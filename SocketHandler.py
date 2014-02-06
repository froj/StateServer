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

class SocketHandler:

    def __init__(self, sockets = None, msgtypes = None, headersize = 8):
        self.sockets = set(sockets)
        self.msgtypes = dict(msgtypes)  # input should be {UID:CallBack}
        self.headersize = headersize
        self.poll = select.poll()
        for s in self.sockets:
            self.poll.register(s.fileno(), socket.POLLIN | socket.POLLPRI)



    def addSocket(self, sock):
        '''Add socket to list and register to poll'''
        if sock not in self.sockets:
            self.sockets.add(sock)
            self.poll.register(sock.fileno(), socket.POLLIN | socket.POLLPRI)


    def rmSocket(self, sock):
        '''Remove socket from list and unregister from poll'''
        try:
            self.sockets.remove(sock)
            self.poll.unregister(sock.fileno())
        finally:
            pass


    def getSocketByFileno(self, fileno):
        '''Return the corresponding socket object to a file descriptor'''
        for sock in self.sockets:
            if fileno == sock.fileno()
                return sock
        return None



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
        # XXX it might help to make a dictionary FileDescriptor:SocketObject
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
                sock = self.getSocketByFileno(fileno)
                sock.close()
                self.rmSocket(sock)
            elif event & select.POLLERR:
                # Error, lolwut? Better close dat shit.
                # XXX try bloc needed?
                sock = self.getSocketByFileno(fileno)
                sock.close()
                self.rmSocket(sock)
            elif event & select.POLLNVAL:
                # Invalid request. Descriptor not open. Remove from list.
                self.rmSocket(self.getSocketByFileno(fileno))

