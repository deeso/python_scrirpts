#!/usr/bin/python

import socket
import sys
HOST = '192.41.96.121'    # The remote host
PORT = 8686              # The same port as used by the server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
#s.send('Hello, world')
while True:
    data = s.recv(1024)
    print repr(data)
    print repr(data.decode('EBCDIC-CP-BE'))

    break
    print data.decode('EBCDIC-CP-BE')
    inp = sys.stdin.readline()
    inp = inp.strip()
    inp= inp.encode('EBCDIC-CP-BE')
    s.send(inp)
