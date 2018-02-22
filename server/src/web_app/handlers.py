import asyncio
import logging

from aiohttp import web

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
    async def clean_up_containers(cls, app):
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

    async def create_repl_handler(self, request):
        """Create a new REPL container.

        This will create a new container based on the image `self.image_name`
        and run it. This will also send a request to that container to start a
        new REPL.
        """

        kata = request.match_info['kata']
        animal = request.match_info['animal']

        client = request.app['docker_client']
        name = self._container_name(kata, animal)

        container = client.containers.run(
            image=self.image_name,
            name=name,
            network=self.network_name,
            ports={'{}/tcp'.format(self.repl_port): self.repl_port},
            restart_policy={'Name': 'on-failure'},
            detach=True)

        self._containers.add(container)

        # Wait for the container to be running
        while container.status != 'running':
            container.reload()

        await asyncio.sleep(2)

        # Request that the REPL process is started
        await request.app['client_session'].post(
            'http://{}:{}/'.format(name, self.repl_port))

        log.info('created REPL: %s', container.name)

        return web.Response(status=web.HTTPCreated.status_code)

    async def delete_repl_handler(self, request):
        """Delete a REPL container.

        This will stop and remove an existing REPL container corresponding to
        the specified kata/animal pair.
        """

        kata = request.match_info['kata']
        animal = request.match_info['animal']

        name = self._container_name(kata, animal)
        client = request.app['docker_client']
        container = client.containers.get(name)

        container.stop()
        container.wait()
        container.remove()

        self._containers.discard(container)

        log.info('deleted repl: %s', container.name)

        return web.Response(status=web.HTTPOk.status_code)

    async def websocket_handler(self, request):
        """Create a websocket to the caller, piping it bi-directionally with the
        websocket on the REPL container.
        """

        kata = request.match_info['kata']
        animal = request.match_info['animal']
        name = self._container_name(kata, animal)

        log.info('initiating websocket. kata=%s animal=%s', kata, animal)

        caller_socket = web.WebSocketResponse()
        await caller_socket.prepare(request)

        url = 'ws://{}:{}'.format(name, self.repl_port)
        repl_socket = await request.app['client_session'].ws_connect(url)

        async def pipe_repl_to_client():
            "Forward messages from the REPL websocket to the client websocket."
            async for msg in repl_socket:
                log.info('from repl: %s', msg.data)
                await caller_socket.send_str(msg.data)

        repl_to_client_task = request.app.loop.create_task(
            pipe_repl_to_client())

        # Forward messages from the client websocket to the REPL websocket.
        async for msg in caller_socket:
            log.info('from client ws: %s', msg.data)
            await repl_socket.send_str(msg.data)

        repl_to_client_task.cancel()

        await asyncio.gather(caller_socket.close(), repl_socket.close())

        log.info('exiting websocket handler: kata=%s animal=%s', kata, animal)

        return caller_socket
