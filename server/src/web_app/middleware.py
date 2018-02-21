"""Middlewares for the aiohttp app.
"""

import logging

from aiohttp import web
import docker.errors

log = logging.getLogger()


async def docker_exceptions_middleware(app, handler):
    """Middleware for uniform handling of docker exceptions.

    Translate docker erorrs into reasonable HTTP error codes.
    """
    async def middleware_handler(request):
        try:
            response = await handler(request)
            return response
        except docker.errors.NotFound as exc:
            raise web.HTTPNotFound(text=str(exc))
        except docker.errors.APIError as exc:
            log.info(str(exc))
            return web.Response(
                status=exc.status_code,
                text=str(exc))

    return middleware_handler
