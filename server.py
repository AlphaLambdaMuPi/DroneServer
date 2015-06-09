#! /usr/bin/env python

import asyncio
import logging
import uuid
import hashlib
import hmac
import json
from collections import defaultdict

from connection import JsonConnection
from role import Control, Drone

logger = logging.getLogger()

DRONE = 'DRONE'
CONTROL = 'CONTROL'
ROLES = set([
    DRONE,
    CONTROL,
])

class DroneServer:
    def __init__(self, loop=None):
        if not loop:
            loop = asyncio.get_event_loop()
        self._loop = loop
        self._datas = defaultdict(int)
        self._conns = {DRONE: {}, CONTROL: {}}
        self._controls = self._conns[CONTROL]
        self._drones = self._conns[DRONE]
        self._run_funcs = {
            DRONE: self.run_drone,
            CONTROL: self.run_control
        }

    @asyncio.coroutine
    def __call__(self, sr, sw):
        conn = JsonConnection(sr, sw)
        data = yield from conn.recv()
        if not isinstance(data, dict):
            return
        role = data.get('role', None)
        name = data.get('name', None)
        if role and name and role in ROLES:
            # if name in self._conns[role]:
                # logger.warning('same device connection!')
                # return
            self._conns[role][name] = self.get_role(role, data, conn)
            yield from self._run_funcs[role](name, conn)


    def get_role(self, role, data, conn):
        if role == DRONE:
            return Drone(data, conn)
        if role == CONTROL:
            return Control(data, conn)

    @asyncio.coroutine
    def run_control(self, name, conn):
        targets = {k: v.get_status() for k, v in self._drones.items()}
        conn.send(targets)
        control = self._controls[name]
        data = yield from conn.recv()
        if not isinstance(data, dict):
            return
        target = data.get('target', None)
        if target in self._drones:
            control.set_drone(self._drones[target])
            yield from control.run()
        else:
            conn.send({'ERROR': 'target doesn\'t exist!'})
        del self._controls[name]

    @asyncio.coroutine
    def run_drone(self, name, conn):
        try:
            logger.debug('Drone {} connected.'.format(name))
            drone = self._drones[name]
            yield from drone.run()
            logger.debug('Drone {} lost connection.'.format(name))
            del self._drones[name]
        except KeyError:
            logger.debug('Drone {} doesn\'t exist.'.format(name))

    @asyncio.coroutine
    def stop(self):
        for control in self._controls.values():
            yield from control.close()
        for drone in self._drones.values():
            yield from drone.close()

# global object       
server = DroneServer()

