import asyncio
import logging
import time

import aiohttp
import sanic.response
import websockets

log = logging.getLogger()


class Handler:
    """HTTP request handlers for the server.

    Args:
        image_name: the name of the docker image to use for REPL containers.
        network_name: The name of the docker network to use for the container.
        repl_port: The port on which the REPL container will handle HTTP
            traffic.
    """

    _containers = set()

    def __init__(self, image_name, network_name, repl_port):
        self.image_name = image_name
        self.network_name = network_name
        self.repl_port = repl_port

    @classmethod
    async def clean_up_containers(cls):
        """Removes any REPL containers that are still open.
        """
        for container in cls._containers:
            log.info('cleaning up container: %s', container.name)
            container.stop()
            container.wait()
            container.remove()

        cls._containers.clear()

    @staticmethod
    def _container_name(kata, animal):
        """Calculate the name of the container for a given kata/animal pair.
        """

        # Important: this accounts for docker's limitation that container names
        # can only be lower case. The user might (and probably will) include
        # upper-case letters in their kata and animal names. We lower-case
        # those here.
        return 'cyber-dojo-repl-container-python-{}-{}'.format(kata.lower(), animal.lower())

    async def _wait_for_container(self, container, client_session, timeout=5.0):
        """Wait for REPL container to be running and responding to HTTP traffic.

        Args:
            container: The `Container` instance to wait on.
            client_session: An `aiohttp.ClientSession` to use for HTTP traffic.
            timeout: The amount of time (seconds) to wait for the container to respond.

        Raises:
            ServerError: if the REPL container can't be reached by the
                timeout.
        """

        start_time = time.time()

        # Wait for the container to be running
        while time.time() - start_time < timeout:
            if container.status != 'running':
                container.reload()
            else:
                try:
                    response = await client_session.get(
                        'http://{}:{}/is_alive'.format(container.name, self.repl_port))
                    if response.status == 200:
                        break
                except aiohttp.ClientError as exc:
                    log.warn('Client warning: %s', exc)

            await asyncio.sleep(0.1)
        else:
            log.warn('timeout while waiting for REPL container to start.')
            raise sanic.exceptions.ServerError(
                'Unable to contact REPL container in {} seconds.'.format(timeout))

    async def create_repl_handler(self, request, kata, animal):
        """Create a new REPL container.

        This will create a new container based on the image `self.image_name`
        and run it. This will also send a request to that container to start a
        new REPL.
        """
        log.info('creating REPL')

        container_name = self._container_name(kata, animal)

        container = request.app.config.docker_client.containers.run(
            image=self.image_name,
            name=container_name,
            network=self.network_name,
            # ports={'{}/tcp'.format(self.repl_port): self.repl_port},
            restart_policy={'Name': 'on-failure'},
            detach=True)

        self._containers.add(container)

        log.info('waiting for container to run')
        await self._wait_for_container(
            container, request.app.config.client_session)

        log.info('asking repl container to start repl')
        # Request that the REPL process is started
        await request.app.config.client_session.post(
            'http://{}:{}/'.format(container_name, self.repl_port))

        log.info('created REPL: %s', container.name)

        return sanic.response.HTTPResponse(status=201)  # created

    async def delete_repl_handler(self, request, kata, animal):
        """Delete a REPL container.

        This will stop and remove an existing REPL container corresponding to
        the specified kata/animal pair.
        """

        container_name = self._container_name(kata, animal)
        container = request.app.config.docker_client.containers.get(
            container_name)

        container.stop()
        container.wait()
        container.remove()

        self._containers.discard(container)

        log.info('deleted repl: %s', container.name)

        return sanic.response.HTTPResponse(status=200)  # OK

    async def websocket_handler(self, request, ws, kata, animal):
        """Create a websocket to the caller, piping it bi-directionally with the
        websocket on the REPL container.
        """

        name = self._container_name(kata, animal)

        log.info('initiating websocket. kata=%s animal=%s', kata, animal)

        url = 'ws://{}:{}'.format(name, self.repl_port)
        async with websockets.connect(url) as repl_socket:

            async def pipe_repl_to_client():
                async for msg in repl_socket:
                    log.info('from repl: %s', msg)
                    await ws.send(msg)

            repl_to_client_task = request.app.loop.create_task(
                pipe_repl_to_client())

            try:
                # Forward messages from the client websocket to the REPL websocket.
                async for msg in ws:
                    log.info('from client ws: %s', msg)
                    await repl_socket.send(msg)

            finally:
                repl_to_client_task.cancel()

            log.info('exiting websocket handler: kata=%s animal=%s', kata, animal)
