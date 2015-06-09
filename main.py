#!/usr/bin/env python

import asyncio
import logging
import subprocess

from server import server
import logsetting
from settings import settings as SETTINGS

logsetting.log_setup()
logger = logging.getLogger()

@asyncio.coroutine
def cleanup(coros):
    logger.info('clean up...')
    for coro in coros:
        yield from coro

if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    coro = asyncio.start_server(server, SETTINGS['ip'], SETTINGS['port'])
    s = loop.run_until_complete(coro)

    logger.info('serving on {}'.format(s.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print()
        coros = [
            server.stop(),
        ]
        loop.run_until_complete(cleanup(coros))

    finally:
        loop.close()
        logger.info("exit.")

