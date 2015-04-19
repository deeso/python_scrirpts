from socket import socket
from socket import timeout
from thread import Threading
import Queue
import struct, sys, time 

EA_SZ = 4

CMD_REQ = 0
CMD_RES = 1

BPHIT=0 
GETBPS=1  
SETBPS = 2  
GETREGS = 3 
SETREGS = 4 
READMEM = 5 
WRITEMEM = 6 


IDA_CMD = 7 
IDA_GETNAME=0
IDA_MAKECOMMENT=1
IDA_MAKEBYTE=2
IDA_MAKEWORD=3
IDA_MAKEDWORD=4
IDA_MAKEQWORD=5
IDA_MAKEOWORD=6
IDA_MAKEALIGN=7
IDA_MAKEFLOAT=8
IDA_MAKESTRING=9
IDA_MAKEDOUBLE=10
IDA_MAKECODE=11
IDA_MAKENAME=12
IDA_JUMPTO=13
IDA_SCREENEA=14
IDA_AAREA=15

IDA_CMD_ARGS = {
IDA_GETNAME:["ea"],
IDA_MAKECOMMENT:["ea","str"],
IDA_MAKEBYTE:["ea"],
IDA_MAKEWORD:["ea"], 
IDA_MAKEDWORD:["ea"],
IDA_MAKEQWORD:["ea"],
IDA_MAKEOWORD:["ea"],
IDA_MAKEALIGN:["ea","int","int"],
IDA_MAKEFLOAT:["ea"],
IDA_MAKEOWORD:["ea"],
IDA_MAKEOWORD:["ea"],
IDA_MAKENAME:["ea","str"],
IDA_SCREENEA:["ea"],
IDA_JUMPTO:["ea"],
IDA_AAREA:["ea","ea"],
IDA_MAKEFLOAT:["ea","ea"]
}

class RecvThread(threadng.Thread):
	def __init__(self, cmd_class, recvQ):
		self.queue = recvQ
		self.cmd_class = cmd_class
		self.handle_queue = True
		
	def run(self):
		while self.handle_queue:
			if self.queue.empty():
				time.sleep(.1)
				continue
			# process data as buffer
			d = queue.get()
			data = "" # buffer
			cmd = "" # self.parse_data(data)
			if cmd and cmd == "req":
				self.cmd_class.handle_reqdbg_cmd(cmd)
			elif cmd and cmd == "rsp":
				self.cmd_class.handle_rspdbg_cmd(cmd)
			else:
				print "Invalid Command or Type"
	


class ServerThread(threadng.Thread):
	def __init__(self, cmd_class, address="127.0.0.1", port=8080):
		threading.Thread.__init__(self)
		self.server = (address, port)
		self.client = None
		self.cmd_class = cmd_class
		self.listen = False
		self.sock = socket()
		self.sock.settimeout(2)
		self.sock.bind(self.server)
		self.client = None
		self.connected = False
	
	def run():
		self.listen = True
		self.sock.listen(1)
		self.client = None
		while self.listen:
			try:
				self.client, addr = self.sock.accept()
				self.connected = True
				self.recv_traffic()
			except:
				print "Client Error :("
				self.client = None
	
	def send_traffic(self, data):
		if self.client:
			try:
				self.client.send(data)
				return True
			except:
				print "Exception when trying to send data"
		return False
		
	def recv_traffic(self):
		print "Receiving client: ",str(addr)
		while self.listen and self.client:
			try:
				# need to write a buffer class
				data = client.recv(65535)
				self.handle_recv(data)
			except timeout:
				pass
	
	def handle_recv(self, data):
		self.cmd_class.add_cmd(data)
	
	def stop_listening(self):
		listening = False
	
class Dlistener:
	def __init__(self, vdb, address="127.0.0.1", port=8080):
		self.server = (address, port)
		self.server_thread = None
		self.recvQ = Queue.Queue()
		self.recv_thread = None
		self.vdb = vdb
	
	def handle_local_cmd(self, cmd_str):
		if not self.server_thread:
			print "Not listening for clients"
			return False
		elif self.server_thread.is_connected():
			print "Not connected to any clients"
			return False
		# process cmd str
		# create a buffer
		data = "" # buffer assigned here
		return self.server_thread.send_traffic(data)
		
	
	def handle_remote_request(self, data):
		# add data to Queue
		self.recvQ.put(data)
	
	def start_listener(self, server=None, port=None):
		if host and port:
			self.server = (server, port)
		self.server_thread = ServerThread(self.server)
		self.server_thread.start()
		
class Buffer:
	def __init__(self):
		self.data = ""
		self.rptr = 0
		self.wptr = 0
		
	def append(self, data):
		self.data += data
		self.wptr += len(data)
	
	def read(self, data, length):
		s = None
		if self.rptr+length < self.wptr:
			s = data[self.rptr:self.rptr+length]
			self.rptr += length
		return s
	
	def read_long(self):
		long_val = None
		if self.rptr+8 < self.wptr:
			long_val = struct.unpack(">Q",self.data+self.rptr)[0]
			self.rptr += 8
		return long_val
	
	def read_int(self):
		int_val = None
		if self.rptr+4 < self.wptr:
			int_val = struct.unpack(">I",self.data+self.rptr)[0]
			self.rptr += 4
		return int_val
	
	def read_short(self):
		short_val = None
		if self.rptr+2 < self.wptr:
			short_val = struct.unpack(">H",self.data+self.rptr)[0]
			self.rptr += 2
		return short_val
		
	def read_byte(self):
		byte_val = None
		if self.rptr+1 < self.wptr:
			byte_val = struct.unpack(">B",self.data+self.rptr)[0]
			self.rptr += 1
		return byte_val
	
	def rewind(self, rew):
		# todo make sure this 
		# matches up
		if rew <= self.rptr:
			self.rptr -= rew
			return True
		return False
		
	def reset(self):
		self.data = ""
		self.self.wptr = 0
		self.self.rptr = 0
	
	def write(self, data, length):
		if length <= len(data):
			self.data += data[0:length]
			self.wptr += length
			return True
		return False
	
	def write_long(self, data):
		self.data += struct.pack(">Q",data)
		self.wptr += len(struct.pack(">Q",data))
		return True
	
	def write_int(self, data):
		self.data += struct.pack(">I",data)
		self.wptr += len(struct.pack(">I",data))
		return True
	
	def write_short(self, data):
		self.data += struct.pack(">H",data)
		self.wptr += len(struct.pack(">H",data))
		return True
	
	def write_byte(self, data):
		self.data += struct.pack(">B",data)
		self.wptr += len(struct.pack(">B",data))
		return True
	
	def get_buf(self):
		return data
		
	def get_size(self):
		return len(data)
	

pack_ea = None
unpack_ea =None
if EA_SZ is 8:
	pack_ea = lambda x: struct.pack(">Q",x)
	unpack_ea = lambda x: struct.unpack(">Q",x)[0]
else:	
	pack_ea = lambda x: struct.pack(">I",x)
	unpack_ea = lambda x: struct.unpack_from(">I",x)[0]

pack_dword = lambda x: struct.pack(">I",x)
unpack_dword = lambda x: struct.unpack_from(">I",x)[0]


byte_x = lambda b,p: chr((b>>(p*8))& 0xff)
get_dword = lambda x: byte_x(x,3)+byte_x(x,2)+byte_x(x,1)+byte_x(x,0)

def build_pkt(typ, cmd, len_data,data):
	msg = pack_ea(typ) + pack_ea(cmd) + pack_ea(len_data)+data
	return pack_ea(len(msg)+EA_SZ)+msg


def parse_ida_msg(data):
	cmd_buffer = data
	cmd = unpack_dword(cmd_buffer)
	if not cmd in IDA_CMD_ARGS:
		return None
	template = IDA_CMD_ARGS[cmd]
	cnt = 0
	cmd_args = []
	while cnt < len(template):
		if template[cnt] == "int":
			cmd_args.append(unpack_dword(cmd_buffer))
			cmd_buffer = cmd_buffer[4:]
		elif template[cnt] == "ea":
			cmd_args.append(unpack_dword(cmd_buffer))
			cmd_buffer = cmd_buffer[EA_SZ:]
		elif template[cnt] == "str":
			cmd_args.append(cmd_buffer)
		cnt += 1
	return cmd_args	
	

def create_ida_pkt(cmd_type, *args):
	if not cmd_type in IDA_CMD_ARGS:
		return None
	template = IDA_CMD_ARGS[cmd_type]
	if len(template) != len(args):
		return None
	cnt = 0
	msg = pack_dword(IDA_CMD) + pack_dword(cmd_type)
	while cnt < len(template):
		if template[cnt] == "int" and isinstance(args[cnt],int):
			msg+=pack_dword(args[cnt])
		elif template[cnt] == "ea":
			if isinstance(args[cnt],int) or isinstance(args[cnt],long):
				msg+=pack_ea(args[cnt])
			else:
				print "Arg %d is not of type '%s':%s"%(cnt, template[cnt],str(arg[cnt]))
				return None
		elif template[cnt] == "str":
			msg+=str(args[cnt])
		else:
			print "Arg %d is not of type '%s':%s"%(cnt, template[cnt],str(arg[cnt]))
			return None
		cnt += 1
	return msg

def parse_header(data):
	typ,cmd = struct.unpack_from(">II",data)
	return typ,cmd,data[2*EA_SZ:]
	
def parse_response(data, s=None):
	typ,cmd,rest = parse_header(data)
	print "type: %d cmd: %d rest: %s"%(typ,cmd,repr(rest))
	if typ == 1 and cmd == IDA_CMD:
		return typ,cmd,parse_ida_msg(rest)
	elif cmd == GETREGS and typ == 0:
		if s:
			f = recv_get_regs()
			msg = build_pkt(typ+1, cmd, len(f),f)
			s.send(msg)
			print repr(msg)
		return typ,cmd,recv_get_regs()
	elif cmd == SETREGS and typ == 0:
		return typ,cmd,recv_set_regs(rest)
	elif cmd == GETBPS and typ == 0:
		if s:
			f = recv_get_bps()
			msg = build_pkt(typ+1, cmd, len(f),f)
			s.send(msg)
			print repr(msg)
		return typ,cmd,recv_get_bps()
	elif cmd == SETBPS and typ == 0:
		return typ,cmd,recv_set_bps(rest)
	return typ,cmd,"Could not pares the rest:"+rest
	


def recv_get_regs():
	return "eax:0x1222,ebx:0x28198,ecx:0x89898,edx:0x1222,ebp:0x28198,esp:0x89898,esi:0x1222,edi:0x28198,eflags:0x89898,ei:0x89898"
	
		
def create_regs_rsp():
	regs = get_regs()
	l = len(regs)
	data = pack_dword(CMD_RSP)+pack_dword(GETREGS)+pack_dword(l)+regs
	return regs
	
def recv_get_bps(data=''):
	return "0x1234,0x234,0x56678,0x5678"

def create_regs_rsp():
	bps = get_bps()
	l = len(bps)
	data = pack_dword(CMD_RSP)+pack_dword(GETBP)+pack_dword(l)+bps
	return bps

def set_bps(bps):
	print "Recv'd the following regs"
	for bp in bps:
		print "breakpoint: %s"%(bp)
	
def recv_set_bps(data):
	cmd_len = unpack_ea(data)
	print "Recv'd len:", cmd_len
	data = data[EA_SZ:]
	addrs = data.split(",")
	#print addrs
	set_bps(addrs)
	return addrs
	
def set_regs(regs):
	print "Recv'd the following regs"
	#print regs
	for r,v in regs:
		print "register: %s value %s"%(r,v)

def recv_set_regs(data):
	cmd_len = unpack_ea(data)
	print "Recv'd len:", cmd_len
	data = data[EA_SZ:]
	regs = []
	reg_data = data.split(",")
	for i in reg_data:
		#print i
		r = i.split(":")
		regs.append(r)
	set_regs(regs)
	return regs


s = socket()
s.bind(("127.0.0.1",8088))
s.listen(10)
def handle_client(s):
	while (1):
		t = s.recv(4)
		le = unpack_dword(t)
		print "Expecting %d bytes of data"%(le)
		t = s.recv(le)
		#print "Recv'd: ", repr(t)
		print parse_response(t,s)


def run_server(s):
	while (1):
		try:
			c,a = s.accept()
			print "Client connected",a
			handle_client(c)
		except KeyboardInterrupt:
			return
		except:
			print sys.exc_info()
			

run_server(s)


