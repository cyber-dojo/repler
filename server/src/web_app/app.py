"""Create an run the aiohttp Application.
"""

import aiohttp
import docker
import docker.errors
from sanic import Sanic
import sanic.exceptions

from .handlers import Handler
from .logging import logging_config


def _configure_routes(app, repl_port, image_name, network_name):
    "Add routes to the application."
    handler = Handler(image_name=image_name,
                     network_name=network_name,
                     repl_port=repl_port)
    app.add_route(handler.alive,
                  '/alive',
                  methods=['GET'])
    app.add_route(handler.ready,
                  '/ready',
                  methods=['GET'])
    app.add_route(handler.sha,
                  '/sha',
                  methods=['GET'])
    app.add_route(handler.create_repl_handler,
                  '/repl/<kata>/<animal>',
                  methods=['POST'])
    app.add_route(handler.delete_repl_handler,
                  '/repl/<kata>/<animal>',
                  methods=['DELETE'])
    app.add_websocket_route(handler.websocket_handler, '/repl/<kata>/<animal>')

    app.listener('after_server_stop')(
        lambda app, loop: handler.close())


def create_app(repl_port, network_name, image_name, log_level):
    """Construct an Application instance.

    It will be configured with middleware and startup/shutdown handlers.
    """
    app = Sanic(log_config=logging_config(log_level))

    @app.listener('before_server_start')
    async def startup(app, loop):
        app.config.docker_client = docker.from_env()
        app.config.http_session = aiohttp.ClientSession()

    @app.listener('after_server_stop')
    async def cleanup(app, loop):
        await app.config.http_session.close()

    @app.exception(docker.errors.NotFound)
    def translate_not_found(request, exception):
        raise sanic.exceptions.NotFound(
            message=str(exception))

    @app.exception(docker.errors.APIError)
    def translate_api_error(request, exception):
        raise sanic.exceptions.SanicException(
            message=str(exception),
            status_code=exception.status_code)

    _configure_routes(app, repl_port, image_name, network_name)

    return app
