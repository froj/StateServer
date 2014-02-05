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
        self.sockets = set(sockets)
        self.msgtypes = dict(msgtypes)  # input should be {UID:CallBack}
        self.poll = select.poll()
        for s in self.sockets:
            self.poll.register(s.fileno(), socket.POLLIN | socket.POLLPRI)



    def addSocket(self, sock):
        # add socket to list and register to poll
        if sock not in self.sockets:
            self.sockets.add(sock)
            self.poll.register(sock.fileno(), socket.POLLIN | socket.POLLPRI)


    def rmSocket(self, sock):
        # remove socket from list and unregister from poll
        try:
            self.sockets.remove(sock)
            self.poll.unregister(sock.fileno())
        finally:
            pass


    def addMsgType(self, msgtype, callback):
        # add message type (UID) and the corresponding callback function pointer
        self.msgtypes[msgtype] = callback


    def rmMsgType(self, msgtype):
        # remove message type (UID)
        try:
            del self.msgtypes[msgtype]
        finally:
            pass


    def handle(self):
        # poll sockets, deserialize, callback
        pass


