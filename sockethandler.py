#!/usr/bin/env python

'''****************************************************************************

This manages a list *open* TCP connections.
It shall listen on those sockets and call the corresponding deserializing
function.
The allowed message types are valid for all sockets.
Each allowed message type has a corresponding callback function.
The callback function has to have (uid, object) as parameters as parameters..

handle() will block the thread!
sockets have to be nonblocking when they're added! (socket.setnonblocking(0))
****************************************************************************'''

#import socket       # for TCP connection
import select       # for poll (cross-platform I/O wait)
import struct       # to unpack bytestreams
import logging

logging.basicConfig(filename='sockethandler.log', level=logging.DEBUG)

HEADER_LENGTH_FIELD = 4
HEADER_HASH_FIELD = 8
HEADER_LENGTH = HEADER_LENGTH_FIELD + HEADER_HASH_FIELD
PACK_FORMAT_STRING = '>i'

ACCEPTED_GARBAGE = 1024     # max length of unkown data without socket.close()


class SocketHandlerReceiver(object):
    ''' This deserializes incoming messages and does callbacks. '''

    def __init__(self, recv_unkown_data=False):
        self.sockets = {}
        self.msgtypes = {}
        self.poll = select.poll()
        self.recv_unkown_data = recv_unkown_data

    def add_socket(self, sock):
        '''Add socket to list and register to poll'''
        if sock.fileno not in self.sockets:
            self.sockets[sock.fileno()] = sock
            self.poll.register(sock.fileno(), select.POLLIN | select.POLLPRI)

    def rm_socket(self, sock):
        '''Remove socket from list and unregister from poll'''
        try:
            del self.sockets[sock.fileno()]
            self.poll.unregister(sock.fileno())
        except KeyError:
            # couldn't remove / doesn't exist
            pass

    def add_msg_type(self, msg_uid, msg_class, callback):
        ''' Add message type (UID) and the corresponding callback func pointer.
            Overrides any existing entry.
        '''
        self.msgtypes[msg_uid] = (msg_class, callback)

    def rm_msg_type(self, msgtype):
        '''Remove message type (by UID)'''
        try:
            del self.msgtypes[msgtype]
        except KeyError:
            # couldn't remove / doesn't exist
            pass

    def handle(self):
        '''Poll sockets (blocking), deserialize, callback'''
        events = self.poll.poll()    # poll without timeout <=> blocking

        for fileno, event in events:
            if event & select.POLLIN or event & select.POLLPRI:
                # input ready
                self._recv_package(self.sockets[fileno])

            elif event & select.POLLHUP:
                # hang up, close dat shiat
                try:
                    self.sockets[fileno].close()
                    self.rm_socket(self.sockets[fileno])
                except KeyError:
                    pass

            elif event & select.POLLERR:
                # Error, lolwut? Better close dat shit.
                try:
                    self.sockets[fileno].close()
                    self.rm_socket(self.sockets[fileno])
                except KeyError:
                    pass

            elif event & select.POLLNVAL:
                # Invalid request. Descriptor not open. Remove from list.
                self.rm_socket(self.sockets[fileno])

    def _recv_package(self, sock):
        ''' read from TCP socket, deserialize, and callback '''
        header = sock.recv(HEADER_LENGTH)  # recv the header of the package
        # extract the length (big-endian) and uid
        length = struct.unpack(
            PACK_FORMAT_STRING,
            header[0:HEADER_LENGTH_FIELD]
            )
        uid = header[
            HEADER_LENGTH_FIELD:HEADER_LENGTH_FIELD + HEADER_HASH_FIELD
            ]
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
                sock.close()
                self.rm_socket(sock)

            else:
                data = sock.recv(length)    # receive data
                # make sure to get it all
                while len(data) < length:
                    data += sock.recv(length-data)


class SocketHandlerSender(object):
    ''' This serializes and sends messages. '''

    def __init__(self):
        self.send_buffer = []   # entries are (socket, message)
        self.poll = select.poll()
        self.descriptor_count = {}  # fileno:count

    def send(self):
        ''' work the send buffers
            Returns the total packages left to send.
        '''
        events = dict(self.poll.poll())

        for buffer in self.send_buffer:
            if buffer[0].fileno() in events:
                # we've found a socket with an event
                event = events[buffer[0].fileno()]
                if event & select.POLLOUT:
                    # the socket is ready to send
                    sentbytes = buffer[0].send(buffer[1])
                    if sentbytes < len(buffer[1]):
                        # only parts could be send
                        buffer[1] = buffer[1][sentbytes:len(buffer[1])]
                        # we need to prevent getting the messages scrambled up
                        del events[buffer[0].fileno()]
                    else:
                        # all was sent, remove the buffer
                        self._remove_buffer(buffer)

                elif event & select.POLLHUP:
                    # hung up, close the socket, remove all traces
                    self._exterminate_buffer(buffer)

                elif event & select.POLLERR:
                    # error, close the socket, remove all traces
                    self._exterminate_buffer(buffer)

                elif event & select.POLLNVAL:
                    # Invalid request, close the socket, remove all traces
                    self._exterminate_buffer(buffer)

        return len(self.send_buffer)

    def _remove_buffer(self, buffer):
        ''' Remove a buffer from the list and uregister the file descriptor if
            the count is at zero.
        '''
        self.send_buffer.remove(buffer)
        try:
            if self.descriptor_count[buffer[0].fileno()] == 1:
                try:
                    self.poll.unregister(buffer[0].fileno())
                except KeyError:
                    # damnit, not registered
                    pass
            else:
                self.descriptor_count[buffer[0].fileno()] -= 1
        except KeyError:
            # dafuq? not in the dictionary?
            pass

    def _exterminate_buffer(self, buffer):
        ''' If a socket hung up or doesn't exist anymore, we should remove any
            occurrence in the list.
        '''
        buffer[0].close()
        for buf in self.send_buffer:
            if buf[0] is buffer[0]:
                self.send_buffer.remove(buf)

        try:
            del self.descriptor_count[buffer[0].fileno()]
        except KeyError:
            pass

        try:
            self.poll.unregister(buffer[0].fileno())
        except KeyError:
            pass

    def send_package(self, sock, msg):
        ''' Add a message to the list of buffers to send.
            Returns how many packages there are for this socket.

            Might be interesting to send to a list of sockets.
        '''
        message = msg.serialize()   # create bytestream
        # put message header (length + hash/uid) on top
        message = msg.hash + message
        message = struct.pack(PACK_FORMAT_STRING, len(message)) + message

        # append messge to list of packages to send
        self.send_buffer.append((sock, message))
        try:    # count packages per socket
            self.descriptor_count[sock.fileno()] += 1
            return self.descriptor_count[sock.fileno()]
        except KeyError:
            # register to poll if it's first
            self.descriptor_count[sock.fileno()] = 1
            self.poll.register(sock.fileno(), select.POLLOUT)
            return 1
