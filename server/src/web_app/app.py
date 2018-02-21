import aiohttp
from aiohttp import web
import docker

from .handlers import Handler
from .middleware import docker_exceptions_middleware


def create_app():
    """Construct an Application instance.

    It will be configured with middleware, startup, and shutdown handlers.
    """
    app = web.Application()

    async def startup(app):
        app['docker_client'] = docker.from_env()
        app['client_session'] = aiohttp.ClientSession()

    async def cleanup(app):
        await app['client_session'].close()

    app.on_startup.append(startup)
    app.on_cleanup.append(cleanup)
    app.middlewares.append(docker_exceptions_middleware)

    return app


def configure_routes(app):
    "Add routes to the application."
    # TODO: These values need to be passed on somehow
    router = Handler(image_name='cyberdojo/repl_container_python',
                     network_name='cyber-dojo',
                     repl_port=4647)
    app.router.add_post('/repl/{kata}/{animal}', router.create_repl_handler)
    app.router.add_delete('/repl/{kata}/{animal}', router.delete_repl_handler)
    app.router.add_get('/repl/{kata}/{animal}', router.websocket_handler)

    app.on_cleanup.insert(0, Handler.clean_up_containers)


def run(port):
    """Create and run an app.
    """
    app = create_app()
    configure_routes(app)
    web.run_app(app, port=port)
