#!/usr/bin/env python

'''*****************************************************************************
This manages a list *open* TCP connections.
It shall listen on those sockets and call the corresponding deserializing
function.
The allowed message types are valid for all sockets.
Each allowed message type has a corresponding callback function.
*****************************************************************************'''

import socket       # for TCP connection
import select       # for poll (cross-platform I/O wait)

class SocketHandler:

    def __init__(self, sockets = None, msgtypes = None):
        self.sockets = sockets
        self.msgtypes = msgtypes    # this should be a list of tuples (type, cb)


    def addSocket(self, socket):
        # add socket to list and register to poll


    def rmSocket(self, socket):
        # remove socket from list and unregister from poll


    def addMsgType(self, msgtype, callback):
        # add message type (UID) and the corresponding callback function pointer


    def rmMsgType(self, msgtype):
        # remove message type (UID)


    def handle(self):
        # poll sockets, deserialize, callback


