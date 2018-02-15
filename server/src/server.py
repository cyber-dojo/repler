import aiohttp
from aiohttp import web

app = web.Application()
session = aiohttp.ClientSession()
loop = asyncio.get_event_loop()


class Router:
    async def create_repl_handler(self, request):
        kata = request.match_info['kata']
        animal = request.match_info['animal']

        # TODO: Start new repl_container and instruct it to start a REPL.

        return web.Response()

    async def delete_repl_handler(self, request):
        kata = request.match_info['kata']
        animal = request.match_info['animal']

        # TODO: Find associated repl_container and instruct it to stop its REPL.

        return web.Response()

    async def websocket_handler(self, request):
        """Create a websocket to the caller, piping it bidirectionally with the
        websocket on the REPL container.
        """
        kata = request.match_info['kata']
        animal = request.match_info['animal']

        caller_socket = web.WebSocketResponse()
        await caller_socket.prepare(request)

        repl_socket = await session.ws_connect('...URL of REPL container...')

        async def pipe_repl_to_client():
            async for msg in repl_socket:
                # TODO: Need to check msg.type? could be CLOSED or ERROR.
                caller_socket.send_str(msg.data)

        repl_to_client_task = request.app.loop.create_task(pipe_repl_to_client())

        async for msg in caller_socket:
            # TODO: Need to check msg.type? could be CLOSED or ERROR.
            repl_socket.send_str(msg.data)

        repl_to_client_task.cancel()
        await asyncio.gather(caller_socket.close(), repl_socket.close())
        return caller_socket

app = web.Application()
router = Router()
app.router.add_post('/repl/{kata}/{animal}', router.create_repl_handler)
app.router.add_delete('/repl/{kata}/{animal}', router.delete_repl_handler)
app.router.add_get('/repl/{kata}/{animal}', router.websocket_handler)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--auto-reload', action='store_true',
                        help='run in auto-reload mode')
    args = parser.parse_args()

    if args.auto_reload:
        import aiohttp_autoreload
        aiohttp_autoreload.start()

    try:
        port = int(os.environ['PORT'])
    except KeyError:
        port = None

    web.run_app(app, port=port)
