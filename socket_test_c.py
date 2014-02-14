#!/usr/bin/env python

import socket
import sockethandler
import serialization


handler = sockethandler.SocketHandlerSender()

s1 = socket.socket()
s1.connect(('127.0.0.1', 6701))
s2 = socket.socket()
s2.connect(('127.0.0.1', 6701))

s1.setblocking(0)
s2.setblocking(0)

m1 = serialization.PIDConfig()
m2 = serialization.PIDConfig()
m1.kp = 42
m1.ki = 42
m1.kd = 42

m2.kp = 41
m2.ki = 41
m2.kd = 41

for i in range(0, 10):
    handler.send_package(s1, m1)
    handler.send_package(s1, m2)
    handler.send_package(s2, m1)
    handler.send_package(s2, m2)
    handler.send_package(s1, m1)
    handler.send_package(s1, m2)
    handler.send_package(s2, m1)
    handler.send_package(s2, m2)

    print("Packages remaining to send:", handler.send())


while handler.send() > 0:
    buffer_len = handler.send()
    print("Packages remaining to send:", handler.send())

s1.close()
s2.close()
