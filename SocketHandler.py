#!/usr/bin/env python

'''*****************************************************************************
TODO: this is incomplete doc!

This manages a list *open* TCP connections.
It shall listen on those sockets and call the corresponding deserializing
function.
The allowed message types are valid for all sockets.
Each allowed message type has a corresponding callback function.
The callback function has to have (uid, object) as parameters as parameters..

handle() will block the thread!
*****************************************************************************'''

import socket       # for TCP connection
import select       # for poll (cross-platform I/O wait)
import struct       # to unpack bytestreams


HEADER_LENGTH_FIELD = 4
HEADER_HASH_FIELD = 8
HEADER_LENGTH = HEADER_LENGTH_FIELD + HEADER_HASH_FIELD
PACK_FORMAT_STRING = '>i'

ACCEPTED_GARBAGE = 1024     # max length of unkown data without socket.close()


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
        except:
            # couldn't remove / doesn't exist
            pass


    def addMsgType(self, msg_uid, msg_class, callback):
        ''' Add message type (UID) and the corresponding callback func pointer.
            Overrides any existing entry.'''
        self.msgtypes[msg_uid] = (msg_class, callback)


    def rmMsgType(self, msgtype):
        '''Remove message type (by UID)'''
        try:
            del self.msgtypes[msgtype]
        except:
            # couldn't remove / doesn't exist
            pask


    def handle(self):
        '''Poll sockets (blocking), deserialize, callback'''
        events = self.poll.poll()    # poll without timeout <=> blocking

        for fileno, event in events:
            if event & select.POLLIN or event & select.POLLPRI:
                # input ready
                recvPackage(self.sockets[fileno])

            elif event & select.POLLHUP:
                # hang up, close dat shiat
                try:
                    self.sockets[fileno].close()
                except:
                    pass
                self.rmSocket(self.sockets[fileno])

            elif event & select.POLLERR:
                # Error, lolwut? Better close dat shit.
                try:
                    self.sockets[fileno].close()
                except:
                    pass
                self.rmSocket(self.sockets[fileno])

            elif event & select.POLLNVAL:
                # Invalid request. Descriptor not open. Remove from list.
                self.rmSocket(self.sockets[fileno])


    def recvPackage(self, sock):
        header = sock.recv(HEADER_LENGTH)       # recv the header of the package
        # extract the length (big-endian) and uid
        length = struct.unpack(PACK_FORMAT_STRING, header[0:HEADER_LENGTH_FIELD])
        uid = header[HEADER_LENGTH_FIELD:HEADER_LENGTH_FIELD + HEADER_HASH_FIELD]
        try:
            msgtype = self.msgtypes[uid]
            msg_class = msgtype[0]  # extract class-pointer of the message type
            callback = msgtype[1]   # extract callback function pointer
            data = sock.recv(length)    # receive data
            # make sure to get it all
            while len(data) < length:
                data += sock.recv(length-data)
            callback(uid, msg_class(data))
        except KeyError:
            # unkown UID! (first line of the try block probably failed)
            if not self.recv_unkown_data or length > ACCEPTED_GARBAGE:
                try:
                    sock.close()
                except:
                    pass
                self.rmSocket(sock])

            else:
                data = sock.recv(length)    # receive data
                # make sure to get it all
                while len(data) < length:
                    data += sock.recv(length-data)
