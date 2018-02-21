import asyncio
import logging

from aiohttp import web

log = logging.getLogger()


class Handler:
    _containers = set()

    def __init__(self, image_name, network_name, repl_port):
        self.image_name = image_name
        self.network_name = network_name
        self.repl_port = repl_port

    @classmethod
    async def clean_up_containers(cls, app):
        for container in cls._containers:
            log.info('cleaning up container: %s', container.name)
            container.stop()
            container.wait()
            container.remove()

        cls._containers.clear()

    @staticmethod
    def _container_name(kata, animal):
        return 'cyberdojo-repl-container-python-{}-{}'.format(kata, animal)

    async def create_repl_handler(self, request):
        kata = request.match_info['kata']
        animal = request.match_info['animal']

        # TODO: Check that a container of this name doesn't already exist!

        # TODO: How do we inject the user's files into the container?

        client = request.app['docker_client']
        name = self._container_name(kata, animal)

        log.info('network: %s, name: %s', self.network_name, name)

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

        # TODO: This is a hack. How can we be sure that the container is
        # running and ready for traffic?
        await asyncio.sleep(2)

        # Request that the REPL process is started
        await request.app['client_session'].post(
            'http://{}:{}/'.format(name, self.repl_port))

        log.info('created REPL: %s', container.name)

        return web.Response(status=web.HTTPCreated.status_code)

    async def delete_repl_handler(self, request):
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
        """Create a websocket to the caller, piping it bidirectionally with the
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
            async for msg in repl_socket:
                # TODO: Need to check msg.type? could be CLOSED or ERROR.
                log.info('from repl: %s', msg.data)
                await caller_socket.send_str(msg.data)

        repl_to_client_task = request.app.loop.create_task(
            pipe_repl_to_client())

        async for msg in caller_socket:
            # TODO: Need to check msg.type? could be CLOSED or ERROR.
            log.info('from client ws: %s', msg.data)
            await repl_socket.send_str(msg.data)

        repl_to_client_task.cancel()

        await asyncio.gather(caller_socket.close(), repl_socket.close())

        log.info('exiting websocket handler: kata=%s animal=%s', kata, animal)

        return caller_socket
