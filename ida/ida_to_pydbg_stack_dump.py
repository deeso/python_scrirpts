
stack_dump_code = '''
# Code is Written by code written by
# (c) 2009-? Adam Pridgen adam.pridgen@thecoverofnight.com
# except where annotated code is released under GPLv3
#
# dump_stack and get_stack_info are based off of code
# from dump context in pdbg project by Pedram Amini
# with some modifications
#
#

import sys,getopt,struct,signal
from pydbg import *
from pydbg.defines import *
from pydbg.pydbg_core import *
from IPython.Shell import IPShellEmbed
import time
from subprocess import *


def convert_be(buffer):
	i = 0
	i = ord(buffer[0]) & 0x0ff
	i += ord(buffer[1]) << 8 & 0xff00
	i += ord(buffer[2]) << 16 & 0x0FF0000
	i += ord(buffer[3]) << 24 & 0x0FF000000
	return i

def convert_le(buffer):
	i = 0
	i = ord(buffer[3]) & 0x0ff
	i += ord(buffer[2]) << 8 & 0xff00
	i += ord(buffer[1]) << 16 & 0x0FF0000
	i += ord(buffer[0]) << 24 & 0x0FF000000
	return i


	
def get_stack_info(dbg, context, stack_info, print_dots=True, hex_dump = True):
	# make it extensible to any architecture just change out regs here
	# and in the actual dump function
	regs = ["eip", "eax", "ebx", "ecx", "edx", "edi",
		"esi", "ebp", "esp"]
	fupper = lambda x: x[0].upper()+"".join(x[1:])
	sf_list = {}
	for reg in regs:
		 rvalue = context.__getattribute__(fupper(reg))
		 sf_list[reg] = {}
		 sf_list[reg]["value"] = rvalue
		 if reg == "reg":
		   sf_list[reg]["desc"] = dbg.disasm(rvalue)
		 else:
		   sf_list[reg]["desc"] = dbg.smart_dereference(rvalue, print_dots)
	ebp = context.__getattribute__("Ebp")
	#attempt to determine stack object lens
	offset_lens = []
	idx = 1
	while idx < len(stack_info):
		if stack_info[idx-1][1] > 0 and stack_info[idx][1] < 0:
			offset_lens.append(stack_info[idx-1][1] - 0)
		offset_lens.append(stack_info[idx-1][1] - stack_info[idx][1])
		idx += 1
	idx = 0
	while idx < len(stack_info):
		name = stack_info[idx][0]
		offset = stack_info[idx][1]
		desc = ""
		offset_len = 4 
		if idx < len(offset_lens): offset_len = offset_lens[idx]
		val = dbg.read_process_memory(ebp+offset, 4)
		#print "Adding %s offset: %x len: %x to stack_info"%(name, offset, offset_len)
		try:
				
				if offset_len == 4:
					try: 
						addr = convert_be(val)
						#print "Performing smart Dereference Read from 0x%x"%addr
						desc = dbg.smart_dereference(convert_be(addr), print_dots, hex_dump)
					except:
						#print "Failed! setting desc to the read value"
						desc = val
				else:
					try: 
						#print "Performing smart Dereference Read from stack 0x%x "%addr
						desc = dbg.smart_dereference(ebp+offset, print_dots, hex_dump)
					except:
						#print "Failed! setting desc to the read value"
						desc = dbg.read_process_memory(ebp+offset, offset_len)
				sf_list[name] = {}
				sf_list[name]["desc"] = dbg.get_printable_string(desc, True)
				sf_list[name]["value"] = (convert_be(val), convert_le(val))
		except:
				print "Problem adding %s"%name
				sf_list[name] = {}
				sf_list[name]["desc"] = "ERROR: error reading"
				sf_list[name]["disasm"] = ",".join(dbg.disasm_around(convert_be(val),10))
				sf_list[name]["value"] = (convert_be(val), convert_le(val))

		idx+=1
	return sf_list

def dump_stack(dbg, context, stack_info, stack_list):
	# make it extensible to any architecture just change out regs here
	# and in the actual dump function
	regs = ["eip", "eax", "ebx", "ecx", "edx", "edi",
		"esi", "ebp", "esp"]
	stack_dump  = "STACK DUMP\\n"
	for reg in regs:
	    stack_dump += "  %s: %08x %s\\n" % (reg.upper(),\\
	    					stack_list[reg]["value"],\\
						stack_list[reg]["desc"])
	ebp = stack_list["ebp"]["value"]
	for stack_elem in stack_info:
	        stack_dump += "  %s: 0x%08x (BE: 0x%x, LE: 0x%x) (stack buffer?)-> %s\\n" % \\
	        (       stack_elem[0],   \\
	                ebp+stack_elem[1],\\
					stack_list[stack_elem[0]]["value"][0],   \\
	                stack_list[stack_elem[0]]["value"][1],   \\
	                stack_list[stack_elem[0]]["desc"]     \\
	        )
	return stack_dump

'''



def dump_pdydbg_function(addr):
	stack_offset = 0
	vars = []
	offsets = []
        fname = GetFunctionName(addr)
        fstart = GetFunctionAttr(addr,FUNCATTR_START)
        fframe = GetFrame(fstart)
	if fframe is None:
	  return None
        fmembers = []
        idx = 2 # ignore sp and return
        end = GetLastMember(fframe)
        off = GetFirstMember(fframe)
        while off < end+1:
          off = GetStrucNextOff(fframe, off)
          name = GetMemberName(fframe, off)
          if name != None:
            if name.strip() == "s":
              stack_offset = off
            if name.strip() != "s":
              vars.append(name.strip())
              offsets.append(off)
          if GetMemberSize(fframe, off) is None:
            off += 1
          else: off += GetMemberSize(fframe, off)
        correct_offset = lambda x: stack_offset - x
        offsets = map( correct_offset, offsets)
        i = 0
        #print vars
        #print offsets
        while  i < len(vars):
              fmembers.append((vars[i],"P0x%xP"%offsets[i]))
              i+=1


        st_info = "),\n\t\t".join(str(fmembers).replace("L",'').replace("'P",'').replace("P'",'').split("),"))
        def_str = '''
def dump_%s_stack(dbg, context):
\tstack_info = %s'''%(fname, st_info)
        body = '''
\tstack_list = get_stack_info(dbg, context, stack_info)
\tstack_dump = dump_stack(dbg, context, stack_info, stack_list)
\treturn stack_dump '''

        return def_str + body

def create_stack_dump_table_functions(results, bps):
  func_def = """def stack_dump_table(dbg, context):\n\teip = context.Eip\n"""
  if_select_str = "\tif eip == 0x%08x:\n"
  func_call_str = "\t\treturn dump_%s_stack(dbg,  context)\n"
  func_body = ""
  else_stmt = "\telse: return ''"
  for name in results:
    for bp in bps[name]:
       func_body += if_select_str%bp
       func_body += func_call_str%name
  return func_def + func_body + else_stmt


base_dir = "/Users/apridgen/malware_analysis/waladec/saleslist/analysis/"
addresses_to_dump = [0x48F6CA ,0x441F58, 0x4510D0, 0x4510DA,0x043b295, 0x4502DD, 0x040ABBE, 0x499F7E ]
outfile = base_dir+"pydbg_stack_dmp.py"

results = {}
bps = {}
for addr in addresses_to_dump:
  fname = GetFunctionName(addr)
  if fname in results:
    bps[fname].append(addr)
    continue
  print "Processing: ", hex(addr), " %s"%fname
  result = dump_pdydbg_function(addr)
  if not result is None:
    results[fname] = result 
    bps[fname] = [addr,]
  else:
    print "Processing Failed: ", hex(addr), " %s"%fname

out = open(outfile, 'w')
out.write(stack_dump_code+"\n")
func_selector = create_stack_dump_table_functions(results,bps)
out.write(func_selector+"\n")
for name in results:
  out.write(results[name]+"\n\n")

stack_dump_bps = map(hex, addresses_to_dump)
out.write("stack_dump_bps= %s\n\n"%str(stack_dump_bps).replace("'",''))
out.close()

