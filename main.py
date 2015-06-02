#!/usr/bin/env python

import asyncio
import logging
import subprocess

from server import server
import logsetting
from settings import settings as SETTINGS

logsetting.log_setup()
logger = logging.getLogger()

def clear_tasks(loop):
    logger.info('clear tasks...')
    for task in asyncio.Task.all_tasks():
        task.cancel()
    try:
        loop.run_until_complete(asyncio.gather(*asyncio.Task.all_tasks()))
    except asyncio.CancelledError:
        logger.info('some tasks failed.')

if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    coro = asyncio.start_server(server, SETTINGS['ip'], SETTINGS['port'])
    s = loop.run_until_complete(coro)

    logger.info('serving on {}'.format(s.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print()
        loop.run_until_complete(server.stop())
        clear_tasks(loop)
    finally:
        loop.stop()
        loop.close()
        print("exit.")

