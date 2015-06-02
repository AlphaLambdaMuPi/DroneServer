#! /usr/bin/env python3

import asyncio
import logging

logger = logging.getLogger()

class Role:
    def __init__(self, data, conn):
        self._name = data['name']
        self._conn = conn

    @asyncio.coroutine
    def run(self):
        yield from self._run()
        yield from self.close()

    @asyncio.coroutine
    def _run(self):
        pass

    @asyncio.coroutine
    def close(self):
        yield from self._conn.close()


class Control(Role):
    def __init__(self, data, conn):
        super().__init__(data, conn)
        self._drone = None
    
    def set_drone(self, drone):
        self._drone = drone

    @asyncio.coroutine
    def _run(self):
        while self._conn.alive():
            data = yield from self._conn.recv()
            self._drone.get_command(data)

class Drone(Role):
    def __init__(self, data, conn):
        super().__init__(data, conn)

    @asyncio.coroutine
    def _run(self):
        nonecnt = 0
        while self._conn.alive() and nonecnt >= 5:
            data = yield from self._conn.recv()
            if data is None:
                nonecnt += 1
            logger.debug('receive from {}: {}'.format(self._name, data))

    def get_command(self, command):
        try:
            self._conn.send(command)
        except ConnectionError:
            logger.debug('Drone {} lost connection.'.format(self._name))
