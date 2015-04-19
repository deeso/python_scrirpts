import threading
import random
import time
#import dns.resolver
import sys
from threading import *
from socket import *
from binascii import *
from random import randint
from optparse import OptionParser

CLEANUP_THREAD = None
THREADS_LOCK = threading.Lock()
THREADS = []

CONNECTED_LOCK = threading.Lock()
CONNECTED = {} #[addr] = [(serial, port), ...] & [serial] = [(addr, port), ...]

HALF_CONNECTED_LOCK = threading.Lock()
HALF_CONNECTED = {} #[addr] = [(serial, port), ...] & [serial] = [(addr, port), ...]

FAILED_LOCK = threading.Lock()
FAILED = {} #[addr] = [(serial, port), ...] & [serial] = [(addr, port), ...]


def set_parse_options():
	parser = OptionParser()
	parser.add_option("-t", "--timeout", dest="timeout", type="float",
                  help="socket connection timeout")
	parser.add_option("-a", "--addresses", dest="addrs", type="string",
                  help="CIDR notation of addresses")
	parser.add_option("-p", "--ports", dest="ports", type="string",
                  help="list of ports to scan DEFAULT: 23, 8080, 3128, 21, 22, 53, 110, 5190, 143, 119, 137, 138, 443, 530, 873, 989, 990")
	parser.add_option("-c", "--ceiling", dest="ceiling", type="int",
                  help="reverse connect port binding for proxy maximum port value to use")
	parser.add_option("-f", "--floor", dest="floor", type="int",
                  help="reverse connect port binding for proxy minimum port value to use")
	parser.add_option("-s", "--static_serial", dest="serial", type="string",
                  help="use a static serial value, must be hexadecimal characters")
	parser.add_option("-b", "--maint_freq", dest="timer", type="float",
                  help="frequency of maintaining threads and writing output")
	parser.add_option("-n", "--threads", dest="threads", type="int",
                  help="number of concurrent threads, DEFAULT: 1")
	parser.add_option("-0", "--failedc_file", dest="ffname", type="string",
                  help="file to write to failed proxy connections DEFAULT: failed_connections.txt")
	parser.add_option("-1", "--halfc_file", dest="hfname", type="string",
                  help="file to write to half proxy connections DEFAULT: half_connections.txt")
	parser.add_option("-2", "--fullc_file", dest="cfname", type="string",
                  help="file to write to full proxy connections DEFAULT: connected_connections.txt")
	iports = [23, 8080, 3128, 21, 22, 53, 110, 5190, 143, 119, 137, 138, 443, 530, 873, 989, 990]
	ports = [str(i) for i in iports]
	parser.set_defaults(ceiling = 19000, 
			floor = 18000,
			timeout = 1.0,
			ports=",".join(ports),
			addrs="",
			threads=1,
			timer=5.0,
			serial=None,
			ffname="failed_connections.txt",
			hfname="half_connections.txt",
			cfname="connected_connections.txt",
			)
	return parser

# 0x9A02 0100 0C04 0600 <-- 8 byte announcement header
# 0xF186 F2BF 640f 5145 8814 A548 A57D 01F0 

build_random_nbyte_str = lambda x: "".join(["%02x"%(randint(0, 255))  for i in xrange(0, x)])
build_random_str = lambda str_len: unhexlify(build_random_nbyte_str(str_len))
build_leading0_str = lambda l,val: unhexlify(("%"+"0%dx"%l)%val)

USED_PORTS = {}
def bind_to_rand_sock(local_addr, floor=19000, ceiling=20000, timeout=1.0):
	#my_addr = gethostbyname(gethostbyaddr(gethostname())[0])
	try:
		while True:
			port = randint(floor, ceiling)
			if port in USED_PORTS:
				continue
			s = socket()
			s.settimeout(timeout)
			USED_PORTS[port] = s
			s.bind((local_addr,port))
			return s
	except:
		print sys.exc_info()
		return  None

def build_v666_header_list(addr, local_addr, serial_no=None, floor=19000, ceiling=20000, timeout=1.0):
	# 0x9A02 0100 0C04 0600 <-- 8 byte announcement header
	s = bind_to_rand_sock(local_addr, floor, ceiling, timeout)
	s.settimeout(timeout)
	if s is None:
		return None
	proto_hdr = unhexlify("9A02 0100 0C04 0600".replace(" ",""))
	
	if serial_no:
		serial_no = unhexlify(serial_no)
	else:
		serial_no = build_random_str(16)
	ip_addr = inet_aton(addr)
	port = build_leading0_str(4,s.getsockname()[1])
	return (s, serial_no, proto_hdr+serial_no+ip_addr+port)


def handle_port(listn_sock, addr, port, pkt, timeout=2.0):
	try:
		sock_v666 = socket()
		sock_v666.settimeout(timeout)
		sock_v666.connect((addr, port))
		sock_v666.send(pkt)
		try:
			listn_sock.recv(1024)
			return 2
		except IOError:
			print "Connected but failed to recieve data from socks v666 connect %s %d"%(addr, port)
			return 1
	except IOError:
		print "Failed to connect to %s %d"%(addr, port)
		return 0


def check_add_set_str(key, dict_, value=None):
	if not key in dict_:
		dict_[key] = set()
	if not value is None:
		dict_[key].add(str(value))
	return dict_

def handle_addr(addr,
				local_addr,
				serial=None,
				port_list=[], 
				floor=19000, 
				ceiling=20000, timeout=2.0):
	
	listn_sock, serial, pkt = build_v666_header_list(addr,local_addr,serial,floor,cieling,timeout)
	connected_flag = False
	for port in addr:
		result = handle_port(listn_sock, addr, port, pkt)
		if result == 2:
			CONNECTED_LOCK.acquire()
			print "******* WINNER: %s %d %s"%(addr, port, hexlify(serial))
			check_add_set_str(addr, CONNECTED, (hexlify(serial),port))
			check_add_set_str(hexlify(serial), CONNECTED, (addr,port))
			CONNECTED_LOCK.release()
			connected_flag = True
		elif result == 1:
			HALF_CONNECTED_LOCK.acquire()
			print "******* WIERD Connect worked but no data: %s %d"%(addr, port, hexlify(serial))
			check_add_set_str(addr, HALF_CONNECTED, (hexlify(serial),port))
			check_add_set_str(hexlify(serial), HALF_CONNECTED, (addr,port))
			HALF_CONNECTED_LOCK.release()
			connected_flag = True
	
	if not connected_flag:
		FAILED_LOCK.acquire()
		check_add_set_str(addr, FAILED, (hexlify(serial),port))
		check_add_set_str(hexlify(serial), FAILED, (addr,port))
		FAILED_LOCK.release()
	return connected_flag

def thread_maintanence(timer_val, cfname=None, hfname=None, ffname=None):
	new_threads = []
	THREADS_LOCK.acquire()
	for thread in THREADS:
		if thread.isAlive():
			new_threads.append(thread)
	THREADS = new_threads
	THREADS_LOCK.release()
	if not cfname:
		cfname = "full_proxy_connections.txt"
	if not hfname:
		hfname = "half_proxy_connections.txt"
	if not ffname:
		ffname = "failed_proxy_connections.txt"
	write_connected_file(cfname)
	write_hconnected_file(hfname)
	write_failed_file(ffname)
	CLEANUP_THREAD = threading.Timer(timer_val, thread_maintanence, args=(timer_val,cfname,hfname,ffname ))
	CLEANUP_THREAD.start()

def write_connected_file(fname):
	keys = CONNECTED.keys()
	output = []
	CONNECTED_LOCK.acquire()
	for key in keys:
		for item in CONNECTED[key]:
			data = key + " " + str(item)
			output.append(data)
	CONNECTED = {}
	CONNECTED_LOCK.release()
	f = open(fname, "a")
	f.write("\n".join(data))

def write_hconnected_file(fname):
	keys = CONNECTED.keys()
	output = []
	HALF_CONNECTED_LOCK.acquire()
	for key in keys:
		for item in CONNECTED[key]:
			data = key + " " + str(item)
			output.append(data)
	HALF_CONNECTED = {}
	HALF_CONNECTED_LOCK.release()
	f = open(fname, "a")
	f.write("\n".join(data))
	
def write_failed_file(fname):
	keys = FAILED.keys()
	output = []
	FAILED_LOCK.acquire()
	for key in keys:
		for item in CONNECTED[key]:
			data = key + " " + str(item)
			output.append(data)
	FAILED = {}
	FAILED_LOCK.release()
	f = open(fname, "a")
	f.write("\n".join(data))

def expand_addrs(cidr_addrs):
	addrs = set()
	for addr in cidr_addrs:
		addrs |= get_ips(addr)
	return addrs

	

def get_ips(IP_RANGE):
    '''
    getips(IPRange)
    
    example usage:
    IP_RANGE = '192.168.1.1-50'

    x = getips(IP_RANGE)
    for ip in x:
        print x
    '''
    
    string_add = lambda l,i: l.add(socket.inet_ntoa(int_to_str(i)))
    # this check to make sure all the values are digits and not other
    # stuff.
    if not IP_RANGE.replace("-",".").replace(".","").isdigit():
        return [IP_RANGE]
    
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


    octets = IP_RANGE.split(".")
    print octets
    if len(octets) != 4:
        return [IP_RANGE]
    
    octet_strs = set()
    x = []
    y = []
    for i in octets:
        if i.find("-") > -1:
            y.append(i.split("-")[1])
            x.append(i.split("-")[0])
        else: 
            y.append(i)
            x.append(i)
     
    x_int = str_to_int(socket.inet_aton(".".join(x)))
    y_int = str_to_int(socket.inet_aton(".".join(y)))
    while x_int <= y_int:
        string_add(octet_strs, x_int)
        x_int += 1
    return octet_strs	

parser = set_parse_options()
if __name__ ==  "__main__":
	print "Not ready for prime time yet"
	addr_list = []
	(options, args) = parser.parse_args()
	addr_list = expand_addrs(options.addr_list.split(","))
	floor = options.floor
	ceiling = options.ceiling
	timeout = options.timeout
	port_list = [int(i) for i in options.ports.split(",")]
	timer = options.timer
	threads_cnt = options.threads
	if threads_cnt < 1:
		parser.print_help()
		sys.exit(-1)

	cfname = options.cfname
	hfname = options.hfname
	ffname = options.ffname
	CLEANUP_THREAD = threading.Timer(timer, thread_maintanence, args=(timer,cfname,hfname,ffname ))
	CLEANUP_THREAD.start()
	while len(addr_list) > 0:
		addr = addr_list.pop()
		while len(threads) >= threads_cnt:
			if not CLEANUP_THREAD or not CLEANUP_THREAD.isAlive():
				CLEANUP_THREAD = threading.Timer(timer, thread_maintanence, args=(timer, ))
				CLEANUP_THREAD.start()
			sleep(2)
			
		# create new thread here
		t = threading.Thread(target=handle_addr, args=(addr, port_list,floor,ceiling, timeout))
		THREADS_LOCK.acquire()
		t.start()
		THREADS.append(t)
		THREADS_LOCK.release()
		


