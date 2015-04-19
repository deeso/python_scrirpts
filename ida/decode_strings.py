import binascii

test_string = "".join("84 9C A2 8D 8D 8D 8D 8D  8D AD AF AF".split())
test_string_2 = "".join("FD 97 B6 B3 BA BE B9".split())

b_test_string = binascii.a2b_hex(test_string)
b_test_string_2 = binascii.a2b_hex(test_string_2)

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