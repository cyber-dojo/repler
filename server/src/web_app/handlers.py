import logging

import sanic.response

from .repl_mgr import ReplManager

log = logging.getLogger()


class Handler:
    """HTTP request handlers for the server.

    Args:
        image_name: the name of the docker image to use for REPL containers.
        network_name: The name of the docker network to use for the container.
        repl_port: The port on which the REPL container will handle HTTP
            traffic.
    """

    def __init__(self, image_name, network_name, repl_port):
        self.image_name = image_name
        self.network_name = network_name
        self.repl_port = repl_port
        self.repl_mgrs = {}

    def close(self):
        """Removes any REPL containers that are still open.
        """
        for repl_mgr in self.repl_mgrs:
            repl_mgr.close()

        self.repl_mgrs.clear()

    async def create_repl_handler(self, request, kata, animal):
        """Create a new REPL container.

        This will create a new container based on the image `self.image_name`
        and run it. This will also send a request to that container to start a
        new REPL.
        """
        log.info('creating REPL')

        key = (kata, animal)
        if key in self.repl_mgrs:
            return sanic.response.HTTPResponse(status=409)

        repl_mgr = ReplManager()

        await repl_mgr.start(
            kata=kata,
            animal=animal,
            loop=request.app.loop,
            docker_client=request.app.config.docker_client,
            http_session=request.app.config.http_session,
            image_name=self.image_name,
            network_name=self.network_name,
            repl_port=self.repl_port,
            file_data=request.body)

        self.repl_mgrs[key] = repl_mgr

        return sanic.response.HTTPResponse(status=201)  # created

    async def delete_repl_handler(self, request, kata, animal):
        """Delete a REPL container.

        This will stop and remove an existing REPL container corresponding to
        the specified kata/animal pair.
        """

        key = (kata, animal)
        try:
            repl_mgr = self.repl_mgrs.pop(key)
        except KeyError:
            return sanic.response.HTTPResponse(status=404)  # NotFound

        repl_mgr.kill()

        return sanic.response.HTTPResponse(status=200)  # OK

    async def websocket_handler(self, request, ws, kata, animal):
        """Create a websocket to the caller, piping it bi-directionally with the
        websocket on the REPL container.
        """

        key = (kata, animal)
        try:
            repl_mgr = self.repl_mgrs[key]
        except KeyError:
            return sanic.response.HTTPResponse(status=404)  # NotFound

        log.info('initiating websocket: kata=%s animal=%s', kata, animal)
        await repl_mgr.process_websocket(ws)
        log.info('terminating websocket: kata=%s animal=%s', kata, animal)
