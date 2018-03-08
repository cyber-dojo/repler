import asyncio
import logging
import time

import aiohttp
import docker.errors
import sanic.exceptions
import websockets

log = logging.getLogger()


class ReplManager:
    """Manage the connection between a client websocket and a REPL running in a
    container.

    This is a bit of a monster, but it's pure at heart. This knows how to start
    a new container which itself runs a REPL. This can open a websocket to that
    container, receiving REPL output and sending user commands over that
    socket. Moreover, it can take a client websocket and pipe the data of these
    two websockets to each other.

    It's complex because it handles a few tough cases:

    - Client websockets starting and stopping in an interleaved manner
    - Making sure all REPL output gets to a client socket (meaning we buffer
      it)

    It's probably *too* complex right now, but it also seems to work.

    """
    def __init__(self):
        # Contains messages recieved from the REPL
        self._repl_msgs = asyncio.Queue()

        # The docker container with the actual REPL process
        self._container = None

        # The async task to read from the REPL and store in the queue
        self._store_repl_msgs_task = None

        # The async task to relay messages from the queue to the client
        # websocket
        self._relay_repl_msgs_task = None

        # The websocket for sending message to the REPL
        self._repl_socket = None

        # The active client websocket
        self.ws = None

        # The condition/lock for accessing the client websocket
        #
        # TODO: With proper client use of websockets we shouldn't need to guard
        # the websocket. They should fully close one before opening another.
        # See if we can remove this condition. Let the user worry about getting
        # traffic on the right websocket.
        self.ws_cond = asyncio.Condition()

    @property
    def alive(self):
        return self._container is not None

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
        if self.alive:
            raise ValueError('container connection already started.')

        name = _container_name(kata, animal)

        # If the container exists, do nothing and return 409 (Conflict).
        try:
            docker_client.containers.get(name)
            raise sanic.exceptions.SanicException(
                'container named {} already exists'.format(name),
                status_code=409)
        except docker.errors.NotFound:
            pass

        self._container = docker_client.containers.run(
            image=image_name,
            name=name,
            network=network_name,
            restart_policy={'Name': 'on-failure'},
            detach=True)

        log.debug('starting container %s', name)
        await _wait_for_container(
            repl_port,
            self._container,
            http_session)

        log.debug('running REPL on container %s', name)
        await http_session.post(
            'http://{}:{}/'.format(self._container.name, repl_port),
            data=file_data)

        url = 'ws://{}:{}'.format(self._container.name, repl_port)
        self._repl_socket = await websockets.connect(url)

        self._store_repl_msgs_task = loop.create_task(
            self._store_repl_msgs())

        self._relay_repl_msgs_task = loop.create_task(
            self._relay_repl_msgs())

    def kill(self):
        if not self.alive:
            raise ValueError('container connection not started')

        if self._store_repl_msgs_task is not None:
            self._store_repl_msgs_task.cancel()
            self._store_repl_msgs_task = None

        if self._relay_repl_msgs_task is not None:
            self._relay_repl_msgs_task.cancel()
            self._relay_repl_msgs_task = None

        if self._repl_socket is not None:
            self._repl_socket.close(reason='ReplManager closed')
            self._repl_socket = None

        if self._container is not None:
            self._container.stop()
            self._container.wait()
            self._container.remove()
            self._container = None

    async def _store_repl_msgs(self):
        async for msg in self._repl_socket:
            log.info('repl-runner received: %s', msg)
            await self._repl_msgs.put(msg)

    async def _relay_repl_msgs(self):
        while True:
            msg = await self._repl_msgs.get()
            log.info('popped from queue: %s', msg)

            # Acquire the websocket lock
            with await self.ws_cond:
                log.info('unlocked condition: %s', self.ws)

                # Wait until there's a websocket
                while self.ws is None:
                    log.info('waiting...')
                    await self.ws_cond.wait()

                assert self.ws is not None

                log.info('sending from queue to client: %s', msg)
                await self.ws.send(msg)

    async def process_websocket(self, ws):
        with await self.ws_cond:
            self.ws = ws
            self.ws_cond.notify()

        # Forward messages from the client websocket to the REPL websocket.
        async for msg in ws:
            log.debug('from client ws: %s', msg)
            if self._repl_socket is not None:
                await self._repl_socket.send(msg)

        log.info('websocket shutting down')
        with await self.ws_cond:
            if self.ws is ws:
                self.ws = None


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
