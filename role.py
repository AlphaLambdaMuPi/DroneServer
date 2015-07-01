#! /usr/bin/env python3

import asyncio
import logging

logger = logging.getLogger()

class Role:
    def __init__(self, data, conn, server):
        self.name = data['name']
        self._conn = conn
        self._server = server

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
    def __init__(self, data, conn, server):
        super().__init__(data, conn, server)
        self._target = None
    
    def set_drone(self, drone):
        self._target = drone

    @asyncio.coroutine
    def _run(self):
        while self._conn.alive():
            data = yield from self._conn.recv()
            if data is None:
                break
            res = self._server.send_command_to_drone(self._target, data)
            if not res:
                self._conn.send({"Error":"drone was gone(?)"})

    @asyncio.coroutine
    def close(self):
        yield from super().close()

class Drone(Role):
    def __init__(self, data, conn, server):
        super().__init__(data, conn, server)
        self._ipaddr = data.get('ip', None)
        self._status = False

    @asyncio.coroutine
    def _run(self):
        nonecnt = 0
        while self._conn.alive() and nonecnt <= 5:
            data = yield from self._conn.recv()
            if data is None:
                nonecnt += 1
            elif data.get('status', None):
                self._status = data['status']
            logger.debug('receive from {}: {}'.format(self.name, data))

    def get_command(self, command):
        if not self._conn.alive():
            return False
        try:
            self._conn.send(command)
            return True
        except ConnectionError:
            logger.debug('Drone {} lost connection.'.format(self.name))
            return False

    def get_status(self):
        return {'status':self._status, 'ip': self._ipaddr}

    @asyncio.coroutine
    def close(self):
        yield from super().close()

