def get_align(length, align):
	if length%align == 0: 
		return 0
	return (align - length%align)%align

def get_data_chunk(addr, max_length):
	chunk = ""
	pos = 0
	while addr+pos < addr+max_length:
		byte = IdbByte(addr+pos)
		if chr(byte) == '\x00':
			break
		chunk += chr(byte)
		pos += 1
	return chunk

start = AskAddr(ScreenEA(), "Enter start address.")
end = AskAddr(ScreenEA(), "Enter string length.")
align = AskLong(4, "Enter an alignment (4) by default.")
max_str_length = AskLong(100, "Enter an alignment (37) by default.")

if start >= end:
	print "Please enter a valid start and end address start: 0x%08x end: 0x%08x."%(start,end)

while start < end:
	string = get_data_chunk(start, max_str_length)
	if len(string) == 0:
		MakeAlign(start, align, 0)
		start += align
		continue
	print "Making string:", repr(string)
	try:
		MakeStr(start, start+len(string)+1)
		a = get_align(len(string)+1, 4)
		print "String length: %x \nAlignement Info: %d"%(start+len(string)+1, a)
		MakeAlign(start+len(string)+1,a, 0)
		start += a+len(string)+1
	except:
		start += 1

