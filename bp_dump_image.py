# (c) 2010 Adam Pridgen adam@praetoriangrp.com adam.pridgen@thecoverofnight.com
# bp_dump_image.py:  
#		Immunity Debbuger Command that will set breakpoints on supplied expressions
#		and search the process memory for a set of special strings from a VB process.  
#		If an executable image is found in memory, it will be dumped from memory.
#
#		 Expression Format:  expression1,expression2
#			 decimal address (e.g. 12345678)
#			 hexadecimal address (e.g. 0x1234)
#			 lib.function expressions (e.g. kernel32.CreateProcessA).  
#
#		 Strings Format: string1,string2
#			 Must be ACSII.  For example, \x00 will not be converted to a single char
#			 Strings will be converted to Unicode, upper, and lower derivatives.
#
#		 (optional) Tail:  Tail value that indicates the end of a the exe image.
#
# Command: !bp_dump_image expresion1[,expression2,expression3,...] str1[,str2,str3,...] tail_value
#
# Example: !bp_dump_image kernel32.CreateProcessA,kernel32.CreateProcessW, BitDefender 0xEEFEEEFE

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



import sys,getopt,struct,signal
DEBUGGER = ""
STRINGS = []
import immlib
from immutils import *
from libhook import BpHook
import pelib
#import hidedebug

	
myint2string32 = lambda x: chr((x>>24)&0xff) + chr((x>>16)&0xff) + chr((x>>8)&0xff) + chr((x>>0)&0xff)
usage = '''(c) Adam Pridgen adam@praetoriangrp.com adam.pridgen@thecoverofnight.com
bp_dump_image.py:  
		Immunity Debbuger Command that will set breakpoints on supplied expressions
		and search the process memory for a set of special strings from a VB process.  
		If an executable image is found in memory, it will be dumped from memory.

		Expression Format:  expression1,expression2
			decimal address (e.g. 12345678)
			hexadecimal address (e.g. 0x1234)
			lib.function expressions (e.g. kernel32.CreateProcessA).  

		Strings Format: string1,string2
			Must be ACSII.  For example, \\x00 will not be converted to a single char
			Strings will be converted to Unicode, upper, and lower derivatives.

		(optional) Tail:  Tail value that indicates the end of a the exe image.

Command: !bp_dump_image expresion1[,expression2,expression3,...] str1[,str2,str3,...] tail_value

Example: !bp_dump_image kernel32.CreateProcessA,kernel32.CreateProcessW, BitDefender 0xEEFEEEFE
'''


class BpSearchandDropBinsHook(BpHook):
	def __init__(self, addresses=[], special_strings=[], tail=0xEEFEEEFE):
		global STRINGS
		imm = immlib.Debugger()
		_special = set()
		for i in special_strings:
			_special.add(i)
			_special.add(i.lower())
			_special.add(i.upper())
			_special.add( "\x00".join([j for j in i])) #mb char
			_special.add( "\x00".join([j for j in i.lower()])) #mb char
			_special.add( "\x00".join([j for j in i.upper()])) #mb char
		# change the set to a list for pickling
		self.__dict__["STRINGS"] = str(",".join([i for i in _special]))
		self._exename = imm.getDebuggedName().split(".")[0]
		self._tail = myint2string32(tail)
		BpHook.__init__(self)
		imm = immlib.Debugger()
		for i in addresses:
			desc = i[0]
			addr = i[1]
			self.add(desc, addr)
		# ascii, unicode hack
		imm.Log("STRINGS are %s"%(repr(self.__dict__["STRINGS"])))

	def dump_exes_in_pages(self, pages):
		exes_written = 0
		immlib.Debugger().Log("Dumping exe in pages")
		for base in  pages:
			p = pages[base]
			memory = p.getMemory()
			immlib.Debugger().Log("Page address 0x%08x"%base)
			# returns lists, need to 
			# check them to see if they are
			# valid
			metric = p.search("!This program cannot be run in DOS mode")
			for addy in metric:
				for mz in p.search("MZ"):
					immlib.Debugger().Log("MZ@0x%08x !This...@0x%08x Difference@0x%08x"%(mz, addy, mz-addy))
					pe = self.dump_exe(p.getMemory(), addy-base, mz-base)
					if not pe is None:
						fname = "C:\\dumped_%s_%u.image_dumped"%(self._exename, exes_written)
						immlib.Debugger().Log("Found an image, and writing it as %s"%fname)
						f = open(fname, "wb")
						f.write(pe)
						f.close()
						exes_written+=1
			
	def dump_exe(self, buf, addy, pe_start):
		if addy - pe_start != 0x4d:
			return None
		buf = buf[pe_start:]
		end = buf.find(self._tail)
		immlib.Debugger().Log("Tail was found at position 0x%08x"%end)
		if end == -1:
			return None
		return buf[:end]
		
		

	def _run(self, regs):
		immlib.Debugger().Log(str(type(self)))
		self.main()
	
	def main(self):
		"""This will be executed when hooktype happens"""
		imm = immlib.Debugger()
		r_addrs = []
		imm.Log("Dumping the following strings")
		strings = self.__dict__["STRINGS"].split(",") 
		for i in strings:
			r_addrs += imm.Search(i)
			imm.Log("String %s @ %s"%(repr(i), str([hex(j) for j in imm.Search(i)])))
			
		r_pages = {}
		for i in r_addrs:
			mp = imm.getMemoryPagebyAddress(i)
			r_pages[mp.getBaseAddress()] = mp
		if len(r_pages) < 1:
			return
		self.dump_exes_in_pages(r_pages)

def main(args): 
	global usage
	print_usage = lambda usage: [imm.Log(i) for i in usage.replace("\t","  ").split("\n")]
	imm = immlib.Debugger()
	#k32 = "kernel32"
	#kernel32_names = ["CreateProcessW", "CreateProcessA", "CreateProcessInternalW", "CreateProcessInternalA", "CreateRemoteThread","CreateThread"]
	if len(args) < 2:
		print_usage(usage)
		return "Fail: See log window"
	expressions = [i.strip() for i in args[0].split(",")]

	strings = set()
	for i in args[1].split(","):
		if i == "":
			continue
		strings.add(i)

	addresses = [] # list of tuple (desc, addr)
	desc_count = 0
	tail = 0xEEFEEEFE
	if len(args) == 3 and args[2].isdigit():
		tail = int(args[2])
	elif len(args) == 3:
		try:
			tail = int(args[2],16)
		except:
			print_usage(usage)
			return "Fail: Tail cannot be converted to an int, See log window for usage"

	for i in expressions:
		if i == "":
			continue
		# handle if the supplied expression is an integer
		if i.isdigit(): 
			addr = int(i)
			desc = "Breakpoint %d autoset for BP hooker"%(desc_count)
			desc_count += 1
			addresses.append((desc, addr))
			continue
		# handle if the supplied expression is an hexadecimal
		try: 
			addr = hex(i)
			desc = "Breakpoint %d autoset for BP hooker"%(desc_count)
			desc_count += 1
			addresses.append((desc, addr))
			continue
		except:
			pass
		# handle if the supplied expression is a lib.function
		addr = imm.getAddressOfExpression(i) 
		desc = i
		if addr == -1:
			continue
		addresses.append((desc, addr))
		desc_count += 1

	hook = BpSearchandDropBinsHook(addresses, strings, tail=tail)
	imm.Error("Hook was successfully set" )