#!/usr/bin/env python

'''*****************************************************************************
This manages a list *open* TCP connections.
It shall listen on those sockets and call the corresponding deserializing
function.
The allowed message types are valid for all sockets.
Each allowed message type has a corresponding callback function.

handle() will block the thread!
*****************************************************************************'''

import socket       # for TCP connection
import select       # for poll (cross-platform I/O wait)


class SocketHandlerReceiver:

    def __init__(self, recv_unkown_data=False):
        self.sockets = {}
        self.msgtypes = {}
        self.poll = select.poll()


    def addSocket(self, sock):
        '''Add socket to list and register to poll'''
        if sock.fileno not in self.sockets:
            self.sockets[sock.fileno()] = sock
            self.poll.register(sock.fileno(), socket.POLLIN | socket.POLLPRI)


    def rmSocket(self, sock):
        '''Remove socket from list and unregister from poll'''
        try:
            del self.sockets[sock.fileno()]
            self.poll.unregister(sock.fileno())
        finally:
            pass


    def addMsgType(self, msgtype, callback):
        '''Add message type (UID) and the corresponding callback func pointer'''
        self.msgtypes[msgtype] = callback


    def rmMsgType(self, msgtype):
        '''Remove message type (UID)'''
        try:
            del self.msgtypes[msgtype]
        finally:
            pass


    def handle(self):
        '''Poll sockets (blocking), deserialize, callback'''
        events = self.poll.poll()    # poll without timeout <=> blocking
        
        for fileno, event in events:
            if event & select.POLLIN || event & select.POLLPRI:
                # input ready
                uid, length, data = recvPackage(fileno)
                # XXX waiting for pa!vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
                self.msgtypes[uid](MessagePassing.deserialize(uid, data))

            elif event & select.POLLHUP:
                # hang up, close dat shiat
                # XXX try bloc needed?
                self.sockets[fileno].close()
                self.rmSocket(self.sockets[fileno])

            elif event & select.POLLERR:
                # Error, lolwut? Better close dat shit.
                # XXX try bloc needed?
                self.sockets[fileno].close()
                self.rmSocket(self.sockets[fileno])

            elif event & select.POLLNVAL:
                # Invalid request. Descriptor not open. Remove from list.
                self.rmSocket(self.sockets[fileno])

