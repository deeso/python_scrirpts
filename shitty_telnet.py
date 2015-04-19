#!/bin/python

import sys
import telnetlib

HOST = '192.41.96.121'    # The remote host
PORT = 8686              # The same port as used by the server

tn = telnetlib.Telnet(HOST, PORT)

while True:

    try:
        print "output mode"

        while True:
            buf_in = tn.read_some()
            print buf_in.decode('EBCDIC-CP-BE')
    except KeyboardInterrupt:
        print "input mode"
        pass

    buf_out = sys.stdin.readline()
    buf_out = buf_out.encode('EBCDIC-CP-BE')

    tn.write(buf_out)

