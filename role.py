#! /usr/bin/env python3

import asyncio
import logging

logger = logging.getLogger()

class Role:
    def __init__(self, data, conn):
        self.name = data['name']
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

    def remove_drone(self):
        self._drone = None

    @asyncio.coroutine
    def _run(self):
        while self._conn.alive():
            data = yield from self._conn.recv()
            if self._drone:
                self._drone.get_command(data)
            else:
                self._conn.send({"Error":"drone was gone(?)"})

    @asyncio.coroutine
    def close(self):
        if self._drone:
            self._drone.remove_control(self)
        yield from super().close()

class Drone(Role):
    def __init__(self, data, conn):
        super().__init__(data, conn)
        self._ipaddr = data.get('ip', None)
        self._status = False
        self._controls = []

    @asyncio.coroutine
    def _run(self):
        nonecnt = 0
        while self._conn.alive() and nonecnt <= 5:
            data = yield from self._conn.recv()
            if data is None:
                nonecnt += 1
            elif data.get('status', None):
                self._status = data['status']
            logger.debug('receive from {}: {}'.format(self._name, data))

    def get_command(self, command):
        try:
            self._conn.send(command)
        except ConnectionError:
            logger.debug('Drone {} lost connection.'.format(self._name))

    def get_status(self):
        return {'status':self._status, 'ip': self._ipaddr}

    def add_control(self, control):
        self._controls[control.name] = control

    def remove_control(self, control):
        try:
            del self._controls[control.name]
        except KeyError:
            logger.warning("{} doesn't control {}".format(control.name,
                                                          self.name))

    @asyncio.coroutine
    def close(self):
        for c in self._controls.values():
            c.remove_drone()
        yield from super().close()

