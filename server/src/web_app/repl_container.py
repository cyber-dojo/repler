import asyncio
import logging
import time

import aiohttp
import docker.errors
import sanic.exceptions
import websockets

log = logging.getLogger()


class ReplContainer:
    """Create and communicate with a container running a REPL.
    """
    def __init__(self, container, repl_socket, loop):
        self._repl_msgs = asyncio.Queue()
        self._container = container
        self._repl_socket = repl_socket
        self._ws = None
        self._ws_cond = asyncio.Condition()

        self._store_repl_msgs_task = loop.create_task(
            self._store_repl_msgs())
        self._relay_repl_msgs_task = loop.create_task(
            self._relay_repl_msgs())

    @staticmethod
    async def create(kata,
                     loop,
                     docker_client,
                     http_session,
                     image_name,
                     network_name,
                     repl_port,
                     file_data):
        """Start a REPL container and socket to talk with it.
        Args:
            kata: The kata ID for the REPL
            loop: The `asyncio` event loop to use
            docker_client: The `docker.Client` to use for container control
            http_session: The `aiohttp.ClientSession` to use for HTTP
                communication
            image_name: The name of the image to use for the container
            network_name: The name of the network to use for talking with the
                container.
            repl_port: The HTTP port exposed by the container.
            file_data: The user files that should be injected into the
                container.

        Raises:
            sanic.exceptions.SanicException: If a container for the kata
                already exists. (Status=409)

        Returns:
            A `ReplContainer` instance.
        """
        name = _container_name(kata)

        # If the container exists, do nothing and return 409 (Conflict).
        try:
            docker_client.containers.get(name)
            raise sanic.exceptions.SanicException(
                'container named {} already exists'.format(name),
                status_code=409)
        except docker.errors.NotFound:
            pass

        # Start the container
        # https://docker-py.readthedocs.io/en/stable/containers.html
        container = docker_client.containers.run(
            image=image_name,
            name=name,
            network=network_name,
            user='nobody',
            restart_policy={'Name': 'on-failure'},
            detach=True)

        # Wait for the container to be ready to handle HTTP.
        log.debug('starting container %s', name)
        await _wait_for_container(
            repl_port,
            container,
            http_session)

        # Ask the container to start a REPL.
        log.debug('running REPL on container %s', name)
        await http_session.post(
            'http://{}:{}/'.format(container.name, repl_port),
            data=file_data)

        # Start a websocket to talk with the REPL.
        log.debug('connecting websocket to REPL container')
        url = 'ws://{}:{}'.format(container.name, repl_port)
        repl_socket = await websockets.connect(url)

        return ReplContainer(container, repl_socket, loop)

    def kill(self):
        if not self.alive:
            raise ValueError('container connection not started')

        assert self._store_repl_msgs_task is not None
        assert self._relay_repl_msgs_task is not None
        assert self._repl_socket is not None
        assert self._container is not None

        try:
            # Shutdown messages processing tasks
            self._store_repl_msgs_task.cancel()
            self._relay_repl_msgs_task.cancel()

            # Close the REPL websocket
            self._repl_socket.close(reason='ReplManager closed')

            # Destroy the container
            self._container.stop()
            self._container.wait()
            self._container.remove()
        finally:
            self._store_repl_msgs_task = None
            self._relay_repl_msgs_task = None
            self._repl_socket = None
            self._container = None

    @property
    def alive(self):
        """Indicates if there is a running REPL container.
        """
        return self._container is not None

    async def set_websocket(self, ws):
        with await self._ws_cond:
            self._ws = ws
            self._ws_cond.notify()

    async def _store_repl_msgs(self):
        async for msg in self._repl_socket:
            log.info('repler received: %s', msg)
            await self._repl_msgs.put(msg)

    async def send(self, msg):
        await self._repl_socket.send(msg)

    async def _relay_repl_msgs(self):
        while True:
            msg = await self._repl_msgs.get()
            log.info('popped from queue: %s', msg)

            # Acquire the websocket lock
            with await self._ws_cond:

                # Wait until there's a websocket
                while self._ws is None:
                    await self._ws_cond.wait()

                assert self._ws is not None

                log.info('sending from queue to client: %s', msg)
                await self._ws.send(msg)


class ReplPipe:
    """Pipes messages bi-directionally between a client websocket and a REPL
    container.
    """
    def __init__(self, container):
        self._container = container

    def kill(self):
        self._container.kill()

    async def process_websocket(self, ws):
        """Sets the container's client websocket (into which the container will send
        REPL messages) to `ws`, and writes messages from `ws` into the REPL.
        """
        await self._container.set_websocket(ws)

        # Forward messages from the client websocket to the REPL websocket.
        async for msg in ws:
            log.debug('from client ws: %s', msg)
            await self._container.send(msg)

        log.info('websocket shutting down')
        await self._container.set_websocket(None)


def _container_name(kata):
    """Calculate the name of the container for a given kata.
    """
    # Important: this accounts for docker's limitation that container names
    # can only be lower case. The user might (and probably will) include
    # upper-case letters in their kata id. We lower-case those here.
    return 'cyber-dojo-repler-container-python-{}'.format(kata.lower())


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
