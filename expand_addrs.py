from socket import *

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
	add_ip_set = lambda lset,ip: lset.add(inet_ntoa(int_to_str(ip)))
	# this check to make sure all the values are digits and not other
	# stuff.
	f = open(fname,"a")
	
	ip_addrs = set()
	if cidr.find("/") == -1:
		return ip_addrs    
	bits = int(cidr.split("/")[1].strip())
	addr = cidr.split("/")[0].strip()
	mask = build_mask(bits)
	print hex(bits), hex(mask)
	start = current = str_to_int(inet_aton(addr))
	current += 1
	bool = False
	while current & mask != start & mask:
		f.write(inet_ntoa(int_to_str(current))+"\n")
		#print hex(current & mask) , hex(start & mask), hex(current), hex(mask)
		current += 1
		bool = True

def expand_addresses(cidr):
	add_ip_set = lambda lset,ip: lset.add(inet_ntoa(int_to_str(ip)))
	# this check to make sure all the values are digits and not other
	# stuff.
	
	ip_addrs = set()
	if cidr.find("/") == -1:
		return ip_addrs    
	bits = int(cidr.split("/")[1].strip())
	addr = cidr.split("/")[0].strip()
	mask = build_mask(bits)
	print hex(bits), hex(mask)
	start = current = str_to_int(inet_aton(addr))
	add_ip_set(ip_addrs, current)
	current += 1
	while current & mask != start & mask:
		add_ip_set(ip_addrs, current)
		current += 1
		#print hex(current & mask) , hex(start & mask), hex(current), hex(mask)
	return ip_addrs