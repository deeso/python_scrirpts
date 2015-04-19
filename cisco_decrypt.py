#
#  Author: Adam Pridgen <adam@praetoriangrp.com>
#  (C) 2010 praetorian group 
#  cisco_decrypt.py - yet another cisco decoder
# GPL v3
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#



from binascii import *
from optparse import OptionParser
import sys

V_xlate= "\x64\x73\x66\x64\x3b\x6b\x66\x6f\x41\x2c\x2e"+\
    "\x69\x79\x65\x77\x72\x6b\x6c\x64\x4a\x4b\x44"+\
    "\x48\x53\x55\x42\x73\x67\x76\x63\x61\x36\x39"+\
    "\x38\x33\x34\x6e\x63\x78\x76\x39\x38\x37\x33"+\
    "\x32\x35\x34\x6b\x3b\x66\x67\x38\x37"

def set_parse_options():
	parser = OptionParser()
	parser.add_option("-f", "--cisco_passwds", dest="fname", type="string",
                  help="File containing the cisco passwds, where the last column is the encoded password")
	parser.add_option("-r", "--replace", action="store_true", dest="replace",
                  help="replace the password in the file")
	parser.add_option("-a", "--append", action="store_true", dest="replace",
                  help="append the decoded password to the line in the file")
	parser.add_option("-o", "--outfile", dest="ofname", type="string",
                  help="out file with the decoded strings, DEFAULT: stdout")
	parser.add_option("-s", "--single", dest="single", type="string",
                  help="decode only a single password")
	parser.add_option("-u", "--unique", dest="unique", action="store_true",
                  help="decode only a single password")
	
	parser.set_defaults(fname = None, 
			ofname = None,
			replace = False,
			single = None,
			unique = False
			)
	return parser
	
def decode_cisco(e_str):
	pw = e_str
	c=2;    
	i= (int(pw[0:c],10))
	#print i, i%53
	#print "Initial: ",i
	r=""
	while c<len(pw):
		e = int(ord(unhexlify(pw[c:c+2])))
		v_i = ord(V_xlate[i])
		#print i, hex(e), pw[c:c+2], hex(v_i), hex(e^v_i)
		r += chr(e^v_i)
		c+=2
		i = (i + 1)%53
	return r

if __name__ == "__main__":
	parser = set_parse_options()
	(options, args) = parser.parse_args()
	
	if options.single is None and options.fname is None:
		print "Error did not specify a filename or a single encoded password"
		parser.print_help()
		sys.exit(-1)
	ofname = options.ofname
	out = None
	if options.ofname is None:
		out = sys.stdout
	else:
		out = open(ofname,'w')
	
	result = []
	lines = []
	if not options.single is None:
		lines = [options.single.strip()]
	else:
		lines = [i.strip() for i in open(options.fname).readlines()]
	for i in lines:
		if i == "":
			continue
		result.append(i.strip()+" "+decode_cisco(i.split()[-1]))
	if options.replace:
		result = [" ".join(i.split()[:-2])+" "+i.split()[-1]  for i in result]
	if options.unique:
		result = [i for i in set(result)]
	out.write("\n".join(result))

