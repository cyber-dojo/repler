import asyncio
import logging
import time

import aiohttp
import docker.errors
import sanic.exceptions
import websockets

log = logging.getLogger()


class ReplManager:
    def __init__(self):
        self.websockets = set()

    async def start(self,
                    kata,
                    animal,
                    loop,
                    docker_client,
                    http_session,
                    image_name,
                    network_name,
                    repl_port,
                    file_data):
        name = _container_name(kata, animal)

        # If the container exists, do nothing and return 409 (Conflict).
        try:
            docker_client.containers.get(name)
            raise sanic.exceptions.SanicException(
                'container named {} already exists'.format(name),
                status_code=409)
        except docker.errors.NotFound:
            pass

        self.container = docker_client.containers.run(
            image=image_name,
            name=name,
            network=network_name,
            restart_policy={'Name': 'on-failure'},
            detach=True)

        log.debug('starting container %s', name)
        await _wait_for_container(
            repl_port,
            self.container,
            http_session)

        log.debug('running REPL on container %s', name)
        await http_session.post(
            'http://{}:{}/'.format(self.container.name, repl_port),
            data=file_data)

        url = 'ws://{}:{}'.format(self.container.name, repl_port)
        self.repl_socket = await websockets.connect(url)

        self.websockets = set()

        self.task = loop.create_task(self._pipe_repl_to_clients())

    def close(self):
        self.repl_socket.close(reason='ReplManager closed')

        self.container.stop()
        self.container.wait()
        self.container.remove()

    async def _pipe_repl_to_clients(self):
        async for msg in self.repl_socket:
            for sock in self.websockets:
                await sock.send(msg)

    async def send(self, msg):
        await self.repl_socket.send(msg)


def _container_name(kata, animal):
    """Calculate the name of the container for a given kata/animal pair.
    """

    # Important: this accounts for docker's limitation that container names
    # can only be lower case. The user might (and probably will) include
    # upper-case letters in their kata and animal names. We lower-case
    # those here.
    return 'cyber-dojo-repl-container-python-{}-{}'.format(kata.lower(),
                                                           animal.lower())


async def _wait_for_container(repl_port,
                              container,
                              http_session,
                              timeout=5.0):
    """Wait for REPL container to be running and responding to HTTP traffic.

    Args:
        container: The `Container` instance to wait on.
        http_session: An `aiohttp.ClientSession` to use for HTTP traffic.
        timeout: The amount of time (seconds) to wait for the container to
            respond.

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
                response = await http_session.get(
                    'http://{}:{}/is_alive'.format(container.name,
                                                   repl_port))
                if response.status == 200:
                    break
            except aiohttp.ClientError as exc:
                log.warn('Client warning: %s', exc)

        await asyncio.sleep(0.1)
    else:
        log.warn('timeout while waiting for REPL container to start.')
        raise sanic.exceptions.ServerError(
            'Unable to contact REPL container in {} seconds.'.format(timeout))
