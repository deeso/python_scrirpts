def convert_raw(val, bytes = 4):
	buffer = []
	cnt = 0
	v = val
	while cnt < bytes:
		buffer.append(v & 0xff)
		v >>= 8
		cnt += 1
	buffer = map(chr, buffer)
	return "".join(buffer)

def convert_int(buffer, bytes = 4):
	i = 0
	cnt = 0
	while cnt < bytes:
		j = ord(buffer[cnt]) &0xff
		i = j + (i << 8)
		cnt += 1
	#i = ord(buffer[0]) & 0x0ff
	#i += ord(buffer[1]) << 8 & 0xff00
	#i += ord(buffer[2]) << 16 & 0x0FF0000
	#i += ord(buffer[3]) << 24 & 0x0FF000000
	return i

def convert_int_flip_endianess(buffer, bytes = 4):
	i = 0
	cnt = 0
	h = [i for i in buffer]
	h.reverse()
	buffer = "".join(h)
	while cnt < bytes:
		j = ord(buffer[cnt]) &0xff
		i = j + (i << 8)
		cnt += 1
	#i = ord(buffer[0]) & 0x0ff
	#i += ord(buffer[1]) << 8 & 0xff00
	#i += ord(buffer[2]) << 16 & 0x0FF0000
	#i += ord(buffer[3]) << 24 & 0x0FF000000
	return i