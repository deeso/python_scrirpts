# (c) Adam Pridgen adam.pridgen@thecoverofnight.com
# this script is released under GPLv3 

from scapy.packet import *
from scapy.fields import *

from scapy.all import *

from urllib import quote, unquote

class HeaderField(StrField):
    def addfield(self, pkt, s, val):
		return s+struct.pack("%s"%(self.i2m(pkt, val)))
    def i2m(self, pkt, val):
		return val+"\r\n"
    def i2len(self,pkt, val):
		return len(self.i2m(pkt,val))
    def getfield(self, pkt, raw):
		x = raw.split("\r\n")
		#print "Called get field: ",x
		return "\r\n".join(x[1:]), x[0]

class HeadersListField(FieldListField):
    def addfield(self, pkt, s, val):
		return s+self.i2m(pkt, val)
    def i2m(self, pkt, hdrs):
		if len(hdrs) == 0:  return "\r\n"
		combine_hdr_val = lambda (x,y): x+": "+y
		hdrs_ = map(combine_hdr_val, hdrs)
		return "\r\n".join(hdrs_)+"\r\n\r\n"
    def i2len(self,pkt, val):
		return len(val)
    def getfield(self, pkt, raw):
		x = raw.split("\r\n\r\n")
		hdrs_ = x[0].split("\r\n")
		for i in hdrs_:
			t = i.replace("-","")
			if t.find(":") > -1 and\
			  t.split(":")[0].isalnum():
				continue
			#print "Failed check: ",hdrs_, i 
			return "\r\n\r\n".join(x), ""
		hdrs = []
		for i in hdrs_:
			if i != "":
				h = i.split(":")[0].strip()
				v = ":".join(i.split(":")[1:]).strip()
				hdrs.append((h,v))
		return "\r\n\r\n".join(x[1:]), hdrs

class PathField(StrField):
	def addfield(self, pkt, s, val):
		return s+" "+self.i2m(pkt, val)
	def i2m(self, pkt, val):
		return quote(val)
	def i2len(self,pkt, val):
		return len(self.i2m(pkt,val))
	def getfield(self, pkt, raw):
		x = raw.split(" ")
		#print "Called get field: ",x
		return " ".join(x[1:]).lstrip(), unquote(x[0])

class VerbField(StrField):
	def addfield(self, pkt, s, val):
		return s+self.i2m(pkt, val)
	def i2m(self, pkt, val):
		return val
	def i2len(self,pkt, val):
		return len(val)
	def getfield(self, pkt, raw):
		x = raw.split(" ")
		#print "Called get field: ",x
		return " ".join(x[1:]).lstrip(), x[0]

class DelimField(StrField):
	def addfield(self, pkt, s, val):
		return s+self.i2m(pkt, val)
	def i2m(self, pkt, val):
		return val
	def i2len(self,pkt, val):
		return len(val)
	def getfield(self, pkt, raw):
		#print "Called get field: ",x
		return "".join(raw[1:]), raw[0]

class ReqDataField(StrField):
	def addfield(self, pkt, s, val):
		return s+self.i2m(pkt, val)
	def i2m(self, pkt, val):
		if pkt.verb == "POST" or len(val) > 0:
			return quote(val)+"\r\n\r\n"
		return ""
	def i2len(self,pkt, val):
		return len(self.i2m(pkt,val))
	def getfield(self, pkt, raw):
		x = unquote(raw)
		#print "Called get field: ",x
		return None, raw

class ReqVersionField(StrField):
	def addfield(self, pkt, s, val):
		return s+" "+self.i2m(pkt, val)+"\r\n"
	def i2m(self, pkt, val):
	    return val
	def i2len(self,pkt, val):
	    return len(self.i2m(pkt,val))
	def getfield(self, pkt, raw):
		x = raw.lstrip().split("\r\n")
		#print "Called get field: ",x
		return "\r\n".join(x[1:]), x[0]

class ResDataField(StrField):
	def addfield(self, pkt, s, val):
		return s+self.i2m(pkt, val)
	def i2m(self, pkt, val):
		return quote(val)
	def i2len(self,pkt, val):
		return len(self.i2m(pkt,val))
	def getfield(self, pkt, raw):
		x = unquote(raw)
		#print "Called get field: ",x
		return None, x

class ResVersionField(StrField):
	def addfield(self, pkt, s, val):
		return s+self.i2m(pkt, val)
	def i2m(self, pkt, val):
	    return val
	def i2len(self,pkt, val):
	    return len(self.i2m(pkt,val))
	def getfield(self, pkt, raw):
		x = raw.split(" ")
		#print "Called ResVersionField getfield: ",x, x[0].find("HTTP")
		if x[0].find("HTTP") == -1:
			return " ".join(x), ""
		return " ".join(x[1:]), x[0]

class ResCodeField(StrField):
	def addfield(self, pkt, s, val):
		return s+" "+self.i2m(pkt, val)
	def i2m(self, pkt, val):
	    return val
	def i2len(self,pkt, val):
	    return len(val)
	def getfield(self, pkt, raw):
		x = raw.split(" ")
		#print "Called ResCodeField getfield: ",x
		if not x[0].strip().isdigit():
			return " ".join(x), ""
		return " ".join(x[1:]).strip(), x[0]

class ResMsgField(StrField):
	def addfield(self, pkt, s, val):
		return s+" "+self.i2m(pkt, val)+"\r\n"
	def i2m(self, pkt, val):
	    return val
	def i2len(self,pkt, val):
	    return len(val)
	def getfield(self, pkt, raw):
		x = raw.split("\r\n")
		t = x[0].replace(" ",'')
		if not t.isalnum():
			return "\r\n".join(x), ""
		#print "Called get field: ",x
		return "\r\n".join(x[1:]), x[0].strip()

class ResTxtField(StrField):
	def addfield(self, pkt, s, val):
		return s+self.i2m(pkt, val)
	def i2m(self, pkt, val):
	    return quote(val)
	def i2len(self,pkt, val):
	    return len(self.i2m(pkt,val))
	def getfield(self, pkt, raw):
		x = raw.split("\r\n")
		#print "Called get field: ",x
		for i in x[0]:
			if i.find(":") > -1 and\
			  i.split(":")[0].isalphanum():
				continue
			return " ".join(x), ""
		return "\r\n".join(x[1:]), x[0]

conf.debug_dissector=1 



class HTTP_Request(Packet):
	name = "HTTP Request"
	fields_desc = [ VerbField("verb", "POST"),
					#DelimField("d1"," "),
					PathField("path", "/"),
					#DelimField("d2"," "),
					ReqVersionField("version", "HTTP/1.1"),
					HeadersListField("headers", [], HeaderField),
					ReqDataField("data","")
					]
	def do_postbuild(self, p, pay):
		if self.verb == "POST":
			clen = len(data)
			cheader = "Content-Length: %u\r\n"%clen
			http_req[0] += cheader
			return "\r\n\r\n".join(http_req)
	def __div__(self, other): 
		if isinstance(other, Packet): 
			cloneA = self.copy() 
			cloneB = other.copy() 
			cloneA.add_payload(cloneB) 
			return cloneA 
		elif type(other) is str: 
			return self/Raw(load=other)

class HTTP_Response(Packet):
	name = "HTTP Response"
	fields_desc = [ ResVersionField("version","HTTP/1.1"),
					#DelimField("delim"," "),
					ResCodeField("code", "999"),
					ResMsgField("msg", "OK"),
					HeadersListField("headers", [], HeaderField),
					ResDataField("data","")
					]
	def __div__(self, other): 
		if isinstance(other, Packet): 
			cloneA = self.copy() 
			cloneB = other.copy() 
			cloneA.add_payload(cloneB) 
			return cloneA 
		elif type(other) is str: 
			return self/Raw(load=other)

bind_layers(TCP, HTTP_Request, dport=80)
bind_layers(TCP, HTTP_Response, sport=80)


#@conf.commands.register
class TCPState:
	flag_vals = {"F":0x1, "S":0x2, "R":0x4, "P":0x8, 
				  "A":0x10,"U":0x20,"E":0x40,"C":0x80 }
	previous = -1
	current = 0
	next = 1
	TCP_STATES = {"CLOSED":["LISTEN", "SYN_SENT"],
				  "LISTEN":["SYN_SENT", "SYN_RCVD"],
				  "SYN_RCVD":["ESTABLISHED", "FIN_WAIT_1"],
				  "SYN_SENT":["SYN_RCVD", "ESTABLISHED"],
				  "ESTABLISED":["FIN_WAIT_1", "CLOSE_WAIT"],
				  "FIN_WAIT_1":["CLOSING", "FIN_WAIT_2"],
				  "FIN_WAIT_2":["TIME_WAIT"],
				  "CLOSE_WAIT":["LAST_ACK"],
				  "CLOSING":["TIME_WAIT"],
				  "LAST_ACK":["CLOSED"],
				  "TIME_WAIT":["CLOSED"]
				}
	
	def __init__(self, dst, dport=None, *args, **kwargs):
		from random import randint
		self.sport = randint(0, 65535)
		self.dport = dport
		if dport is None:
			self.dport = randint(0, 65535)
		self.options = []
		self.seq = randint(0, 65535)
		self.ack = randint(0, 65535)
		self.flags = 0x2
		self.MSS = 1460
		self.WScale = 3
		self.window = 8192
		kwargs["window"] = self.window
		self.options = [('MSS', self.MSS), ("NOP", None), ("WScale", self.WScale) ]
		self.next_seq = len(self.tcp.payload)+1+self.tcp.seq
		self.next_ack = 0

		self.state = "Uninitialized"
		self.dst = dst
		self.ip = IP(dst=self.dst)
		self.kwargs = {}
		for k in self.__dict__:
			if k == "kwargs": continue
			self.kwargs[k] = self.__dict__[k]
		for k in kwargs:
			if k == "kwargs": continue
			self.kwargs[k] = kwargs[k]
			
	def goto_state(self, state): 
		next_states = self.TCP_STATES[self.state]
		if not state in set(next_states):
			# move to the next state until we can get to desired state
			pass
		self.state = state
	
	def send_syn(self, tpkt):
		tpkt.flags = 0x2
		a,b,c = sr1(tpkt)
	
	def active_connect(self, tpkt):
		if self.state != "CLOSED" and\
			self.state != "LISTEN":
			goto_state("CLOSED")
		self.send_syn(tpkt)
	
	def init_connection(self, 
						tcp=None, ip=None, iface=None, 
						iface_hint=None, filter=None, nofilter=0, 
						type=ETH_P_ALL,timeout = 2, inter = 0, 
						verbose=None, chainCC=0, retry=0, multi=0):
		t = None
		self.sent_pkts = []
		if ip is None: t = self.ip
		else: t = ip
		if tcp is None: t = t/self.tcp
		else: t = t/tcp
		self.sock=conf.L3socket(filter=filter, nofilter=nofilter, iface=iface)
		ans,unans,c = sndrcv(self.sock, t, timeout, inter, verbose, chainCC, retry, multi )
		self.next_seq = t[TCP].seq + 1
		if len(ans) == 0 or ans[0][1][TCP].flags != 0x12:
			print "Connection failed to %s!"%t[IP].dst
			return t, self.sent_pkts, unans
		self.sent_pkts.append(ans[0])
		r = ans[0][1][TCP]
		t.show()
		t = self.update_tcp(t, r)
		t.flags = self.flag_vals["A"]
		t.show()
		ans,unans,c = sndrcv(self.sock, t, timeout, inter, verbose, chainCC, retry, multi )
		if len(ans) == 0 or ans[0][1][TCP].flags != 0x12:
			print "Connection failed to %s!"%t[IP].dst
			return t, self.sent_pkts, unans
		self.sent_pkts.append(ans[0])
		return t,self.sent_pkts
	
	def update_tcp(self, t, r):
		p = t.copy()
		p.ack = r.seq
		if len(t.payload) == 0:
			p.seq = (p.seq + 1) % 65535
		else: p.seq = (p.seq + len(t.payload)) % 65535
		return p

def init_tcp_connection(x,*args, **kwargs):
	s = conf.L3socket(*args, **kwargs)
	if not "dport" in kwargs: dport = 80
	if not "dst" in kwargs: return None
	pkt = IP(x[IP])/TCP(x[TCP])
	pkt[TCP].options = 	[ ('MSS', 1460), 
		('NOP', None), 
		('WScale', 3), 
		('NOP', None), 
		('NOP', None), 
		('Timestamp', (1036895075, 0)), 
		('SAckOK', ''), 
		('EOL', None)
	]
	pkt.flags = 0x2
	a,b,c=sndrcv(s,pkt,*args,**kargs)
	return s,a,b,c,pkt

def ack_tcp_pkt(sent, response):
	s = sent.copy()
	s.ack = response.seq           
	s.options = response.options
	s.flags = 0x10
	return s

def synack_tcp_pkt(sent, response):
	s = sent.copy()
	s.ack = response.seq           
	s.options = response.options
	s.flags = 0x10
	return s

def init_tcp_state(*args, **kwargs):
	state = TCPState()
	return state

def syn_tcp_pkt(sent, response):
	s = sent.copy()
	s.ack = response.seq           
	s.options = response.options
	s.flags = 0x10
	return s


values2 = [('NOP', None), 
('NOP', None), 
('Timestamp', (1036895076, 3144216861L))
]

def sr4(x,filter=None, iface=None, nofilter=0, *args,**kargs):
	if not kargs.has_key("timeout"):
		kargs["timeout"] = -1
	#  establish tcp connection
	s, a,b,c = init_tcp_conn(s, base_pkt)
	a,b,c=sndrcv(s,x,*args,**kargs)
	s.close()
	return a,b


def establish_connection(spkt):
	s = get_socket()
	establish_results = []
	result = quick_send(s, spkt)
	if len(result[0]) == 0:
		return None,results
	rpkt = result[0][0][1]
	if TCP not in rpkt or\
		rpkt[TCP].flags != 0x12:
		print "Failed to get the initial SA"
		return None, result
	print "Got the initial SA, sending an ACK"
	establish_results.append(result[0][0])
	spkt2 = update_sa_pkt(spkt, rpkt)
	result = quick_send(s, spkt2)
	if len(result[0]) == 0:
		return None,result
	establish_results.append(result[0][0])
	print "Sent the ACK"
	return s, establish_results
	
	
def update_sa_pkt(spkt, rpkt):
	d = spkt.copy()
	d[TCP].seq += 1
	d[TCP].ack = rpkt[TCP].seq
	d[TCP].flags = 0x10
	d[IP].id += 1
	d[TCP].options = rpkt[TCP].options
	#spkt[TCP].ack = rpkt[TCP].seq
	return d

def get_socket(	iface=None, 
				iface_hint=None, filter=None, nofilter=0, 
				type=ETH_P_ALL,timeout = 2, inter = 0, 
				verbose=None, chainCC=0, retry=0, multi=0):

	return conf.L3socket(filter=filter, nofilter=nofilter, iface=iface)

def quick_send(sock, pkt, tcp=None, ip=None, iface=None, 
				iface_hint=None, filter=None, nofilter=0, 
				type=ETH_P_ALL,timeout = 2, inter = 0, 
				verbose=None, chainCC=0, retry=0, multi=0):
	return sndrcv(sock, pkt, timeout, inter, verbose, chainCC, retry, multi )
