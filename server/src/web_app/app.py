"""Create an run the aiohttp Application.
"""

import aiohttp
import docker
import docker.errors
from sanic import Sanic
import sanic.exceptions

from .handlers import Handler


def _create_app(log_config):
    """Construct an Application instance.

    It will be configured with middleware and startup/shutdown handlers.
    """
    app = Sanic(log_config=log_config)

    @app.listener('before_server_start')
    async def startup(app, loop):
        app.config.docker_client = docker.from_env()
        app.config.client_session = aiohttp.ClientSession()

    @app.listener('after_server_stop')
    async def cleanup(app, loop):
        await app.config.client_session.close()

    @app.exception(docker.errors.NotFound)
    def translate_not_found(request, exception):
        raise sanic.exceptions.NotFound(
            message=str(exception))

    @app.exception(docker.errors.NotFound)
    def translate_api_error(request, exception):
        raise sanic.exceptions.SanicException(
            message=str(exception),
            status_code=exception.status_code)

    return app


def _configure_routes(app):
    "Add routes to the application."
    router = Handler(image_name='cyberdojo/repl_container_python',
                     network_name='cyber-dojo',
                     repl_port=4647)
    app.add_route(router.create_repl_handler,
                  '/repl/<kata>/<animal>',
                  methods=['POST'])
    app.add_route(router.delete_repl_handler,
                  '/repl/<kata>/<animal>',
                  methods=['DELETE'])
    app.add_websocket_route(router.websocket_handler, '/repl/<kata>/<animal>')

    app.listener('after_server_stop')(
        lambda app, loop: Handler.clean_up_containers())


def run(host, port, log_config):
    """Create and run an app.
    """
    app = _create_app(log_config)
    _configure_routes(app)
    app.run(host=host, port=port)
