#!/usr/bin/env python

import socket
import sockethandler
import serialization
from time import sleep

def callback(uid, object):
    if object:
        print("Callback OK.")
        print(object.kp)
        print(object.ki)
        print(object.kd)
    else:
        print("No object :(")

handler = sockethandler.SocketHandlerReceiver()

serv_sock = socket.socket()
serv_sock.bind(('127.0.0.1', 6701))

serv_sock.listen(1)
s1, addr = serv_sock.accept()
s1.setblocking(0)
serv_sock.listen(1)
s2, addr = serv_sock.accept()
s2.setblocking(0)

handler.add_socket(s1)
handler.add_socket(s2)

handler.add_msg_type(
    serialization.PIDConfig.hash,
    serialization.PIDConfig,
    callback
    )

try:
    while True:
        handler.handle()
        sleep(0.005)
except:
    print("Interrupted.")
    s1.close()
    s2.close()
