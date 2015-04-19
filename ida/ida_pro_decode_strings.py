# (c) 2010 Adam Pridgen adam@praetoriangrp.com, adam.pridgen@thecoverofnight.com
# ida_pro_decode_strings.py:
# 		decode strings, rename, and comment on encoded strings in the binary

# GPLv3 License
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import binascii



def get_align(length, align):
	if length%align == 0: 
		return 0
	return (align - length%align)%align

def sign_extend(val, szBit=8, szExtendTo=32):
	shift_or = lambda x: (x << 1) | 1
	sign_bit = 0x1 << (szBit-1)
	mask = 0x0
	for i in xrange((szExtendTo-1) - (szBit-1)):
		mask = shift_or(mask)
	sign_mask = mask << szBit
	if val & sign_bit:
		return sign_mask | val
	return val

ones_complement = lambda x: (~x+0xFFFFFFFF)+1
PAD = "XmA8DdhSADxShdNsd0TTadNSDasdoSDFIFds8"
def decode_string(encoded_str, pad=PAD):
	pos = 0
	decoded_str = ""
	decoded_str_no_not = ""
	for i in encoded_str:
		pad_pos = 0
		enc_chr = ord(i)
		#print "Decoding the following value", i, hex(ord(i))
		for j in pad:
			#print "Current Pad Value", j, ord(j)
			enc_chr = (enc_chr ^ ord(j)) & 0x0FF
			#print "Result of Xor: 0x%x ^ 0x%x = 0x%x"%((enc_chr^ord(j)), ord(j), (enc_chr))
			pad_pos += 1
		enc_chr = sign_extend(enc_chr, 8, 32)
		decoded_str += chr(ones_complement(enc_chr))
		pos += 1
	return decoded_str

def get_data_chunk(addr, max_length):
	chunk = ""
	pos = 0
	while addr+pos < addr+max_length:
		byte = IdbByte(addr+pos)
		chunk += chr(byte)
		if chr(byte) == '\x00':
			return chunk
		pos += 1
	return chunk



start = AskAddr(0xFFFFFFFF, "Enter start address.")
end = AskAddr(0xFFFFFFFF, "Enter string length.")
align = AskLong(4, "Enter an alignment (4) by default.")
max_str_length = AskLong(0, "Enter an alignment (0) by default.")

if start >= end:
	print "Please enter a valid start and end address start: 0x%08x end: 0x%08x."%(start,end)

while start < end:
	string = "\x00"
	if max_str_length == 0:
		string = get_data_chunk(start, 37)
	else:
		string = get_data_chunk(start, max_str_length)
	if len(string) == 1:
		start += 1
		continue
	print "Decoding string:", repr(string)
	try:
		decoded_string = decode_string(string[:-1])
		MakeComm(start, "")
		MakeComm(start, decoded_string)
		MakeNameEx(start, "", 0x0)
		MakeNameEx(start, decoded_string, 0x0)
		MakeStr(start, start+len(string))
		start += len(string)
		print ("Decoded string successfully: %s = %s"%(repr(string[:-1]), decoded_string))
	except:
		start += 1

print "Finished converting and decoding strings to strings."
