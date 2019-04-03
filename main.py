import base64
import copy
import thread
import socket
import sys
import os
import datetime
import time
import json
import threading
import email.utils as eut
import signal
import struct 
dict = {
    'mxConnections': 10,
    'proxy_port': 20100,
    'bufSize': 100000000,
    'CONNECTION_TIMEOUT': 20
}

file = open('blacklist.txt',"r")
blockList = file.readlines()
blockList_ary = []
    
for cur in blockList:
    print cur
    (ip, cidr) = cur.split('/')
    cidr = int(cidr) 
    host_bits = 32 - cidr
    i = struct.unpack('>I', socket.inet_aton(ip))[0] # note the endianness
    start = (i >> host_bits) << host_bits # clear the host bits
    end = start | ((1 << host_bits) )
    end += 1
    # excludes the first and last address in the subnet
    for i in range(start, end):
        blockList_ary.append(socket.inet_ntoa(struct.pack('>I',i)))


def HandleRequest(clientSocket, clientAddress):
    request = clientSocket.recv(dict['bufSize'])
    firstLine = request.split('\n')[0]
    url = firstLine.split(' ')[1]
    print(url);
    http_pos = url.find("://") # find pos of ://
    if (http_pos==-1):
        temp = url
    else:
        temp = url[(http_pos+3):] # get the rest of url

    port_pos = temp.find(":") # find the port pos (if any)

    # find end of web server
    webserver_pos = temp.find("/")
    if webserver_pos == -1:
        webserver_pos = len(temp)

    webserver = ""
    port = -1
    if (port_pos==-1 or webserver_pos < port_pos): 

         # default port 
        port = 80 
        webserver = temp[:webserver_pos] 

    else: # specific port 
        port = int((temp[(port_pos+1):])[:webserver_pos-port_pos-1])
        webserver = temp[:port_pos] 
    
    ip = socket.gethostbyname(webserver)
    print(ip)
    if(ip in blockList_ary):
        clientSocket.send('page blocked')
        exit(0)
    print(webserver,    port)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    print(s)
    s.settimeout(dict['CONNECTION_TIMEOUT'])
    s.connect((webserver, port))
    s.sendall(request)

    while 1:
        # receive data from web server
        data = s.recv(dict['bufSize'])

        if (len(data) > 0):
            clientSocket.send(data) # send to browser/client
        else:
            break


def shutdown():
    exit(0)


class serverStart:
    
    def __init__(self):
        self.sName = 0
        # Shutdown on Ctrl+C
        signal.signal(signal.SIGINT, shutdown) 

        # Create a TCP socket
        self.proxySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Re-use the socket
        self.proxySocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.proxySocket.bind(('127.0.0.1', dict['proxy_port']))
        self.proxySocket.listen(dict['mxConnections']) # become a server socket


        while True:

            # Establish the connection
            (clientSocket, clientAddress) = self.proxySocket.accept() 
            # clientData = clientSocket.recv(bufSize);


            curThread = threading.Thread(name=self._getClientName(), \
            target = HandleRequest , args=(clientSocket, clientAddress))

            curThread.setDaemon(True)
            curThread.start()

    def _getClientName(self):
        self.sName += 1
        return self.sName

a=serverStart()