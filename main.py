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
from urlparse import urlparse
dict = {
	'mxConnections': 10,
	'proxy_port': 20100,
	'bufSize': 100000000,
	'CONNECTION_TIMEOUT': 200,
	'cacheDir' : './cache',
	'cacheLimit' : 3
}

file = open('blacklist.txt',"r")
blockList = file.readlines()
blockList_ary = []
 
# urlList = []

userList = ["Arnav:1234"]

for cur in blockList:
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


def getCacheList():
	cacheFile = open('./cache/list.txt',"r")
	cacheList = cacheFile.readlines()
	return cacheList

def HandleRequest(clientSocket, clientAddress):

	request = clientSocket.recv(dict['bufSize'])
	strg = urlparse(request.split('\n')[0].split(' ')[1])[2]
	strg2 = request.split('\n')
	strg3 = strg2[0].split(' ')
	strg3[1] = strg
	thirdLine = request.split('\n')[2]
	firstWord = thirdLine.split()[0]
	thirdWord = ""
	decod = ""
	allow = 0 
	curlFlag = 0
	strg4 = ' '
	strg4 = strg4.join(strg3)
	strg2[0] = strg4
	final = '\n'
	final = final.join(strg2)

	if firstWord == "Authorization:" :
		curlFlag = 1
		thirdWord = thirdLine.split()[2]
		thirdWord += "="*((4 - len(thirdWord) % 4 ) % 4)
		decod = str(base64.b64decode(thirdWord).strip())
		if decod in userList :
			allow = 1


	firstLine = request.split('\n')[0]
	url = firstLine.split(' ')[1]
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

	if ip in blockList_ary:
		if curlFlag == 1:
			if allow == 0 :
				clientSocket.send('Authentication failed')
				clientSocket.close()
				exit(0)
		else :
			clientSocket.send('This page is blocked')
			clientSocket.close()
			exit(0)
		

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
	s.settimeout(dict['CONNECTION_TIMEOUT'])
	try :	
		s.connect((webserver, port))
		s.sendall(final)
	except :
		sys.exit()
	# if filename in os.listdir('./.cache/'):
	# 	st = "GET /"
	# 	st = st + filename
	# 	st = st + " HTTP/1.1\r\nIf-Modified-Since: "
	# 	st = st + time.ctime(os.path.getmtime('./.cache/' + filename)) + " \r\n\r\n"
	# 	s.send(st)
	# else:
	# 	s.send("GET "+ filename + " HTTP/1.1\r\n\r\n")

	#200 modify ho gya
	# if reply.find("200") >=0 :
	while 1:
		# receive data from web server
		data = s.recv(dict['bufSize'])

		if (len(data) > 0):
			clientSocket.send(data) # send to browser/client
		else:
			break
	# elif reply.find("304") >= 0 :


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