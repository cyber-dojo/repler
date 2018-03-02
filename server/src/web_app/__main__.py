"""Main program for the cyber-dojo runner_repl web_app.
"""

import argparse
import logging

from .app import create_app
from .logging import logging_config


parser = argparse.ArgumentParser()
parser.add_argument(
    '-p', '--port', type=int, default=None,
    help='The port on which to serve HTTP.')
parser.add_argument(
    '--host', type=str, default=None,
    help='The host on which to server HTTP.')
parser.add_argument(
    '--repl-port', type=int, default=None,
    help='The port on which the REPL container will server HTTP.')
parser.add_argument(
    '--network', type=str, default=None,
    help='The docker network on which communicate with the REPL container.')
parser.add_argument(
    '--repl-image', type=str, default=None,
    help='The image from which to build REPL containers.')
parser.add_argument(
    '--auto-reload', action='store_true',
    help='run in auto-reload mode')
parser.add_argument(
    '-v', action='store_true',
    help='enable verbose logging mode')
parser.add_argument(
    '-vv', action='store_true',
    help='enable very verbose logging mode')

args = parser.parse_args()

if args.auto_reload:
    import aiohttp_autoreload
    aiohttp_autoreload.start()

level = logging.INFO if args.v else logging.WARNING
level = logging.DEBUG if args.vv else level

app = create_app(
    repl_port=args.repl_port,
    network_name=args.network,
    image_name=args.repl_image,
    log_level=level)

app.run(host=args.host, port=args.port)
