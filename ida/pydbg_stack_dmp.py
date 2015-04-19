
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

def get_disasm_str(dbg, addr, number=5):
	disasm = dbg.disasm_around(addr, number)
	if len(disasm) == 0 or disasm[0][0] == 0:
		return ""
	disasm_instrs = []
	for bytes, instr in disasm:
		disasm_instrs.append(instr)
	return "\n".join(disasm_instrs)

	
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
		 if reg == "eip":
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
		if len(offset_lens) <= idx: offset_len = 4
		else:  offset_len = offset_lens[idx]
		val = dbg.read_process_memory(ebp+offset, 4)
		print "Adding %s offset: %x len: %x to stack_info"%(name, offset, offset_len)
		if offset_len == 4:
			try: 
				addr = convert_be(val)
				#log( "Performing smart Dereference Read from 0x%x"%addr)
				desc = dbg.smart_dereference(addr, print_dots, hex_dump)
				sf_list[name] = {}
				sf_list[name]["desc"] = dbg.get_printable_string(desc, True)
				sf_list[name]["disasm"] = get_disasm_str(dbg, convert_be(val),10)
				sf_list[name]["value"] = (convert_be(val), convert_le(val))
			except:
				#log( "Failed! setting desc to the read value\n")
				desc = val
				sf_list[name] = {}
				sf_list[name]["desc"] = "READ ERROR:" + repr(desc)
				sf_list[name]["disasm"] = get_disasm_str(dbg, convert_be(val),10)
				sf_list[name]["value"] = (convert_be(val), convert_le(val))
		else:
			try: 
				print "Performing smart Dereference Read from stack 0x%x "%addr
				desc = dbg.smart_dereference(ebp+offset, print_dots, hex_dump)
				sf_list[name] = {}
				sf_list[name]["desc"] = dbg.get_printable_string(desc, True)
				sf_list[name]["disasm"] = get_disasm_str(dbg, convert_be(val),10)
				sf_list[name]["value"] = (convert_be(val), convert_le(val))
			except:
				#log( "Failed! setting desc to the read value\n" )
				desc = dbg.read_process_memory(ebp+offset, offset_len)
				sf_list[name] = {}
				sf_list[name]["desc"] = "READ ERROR:" + repr(desc)
				sf_list[name]["disasm"] = get_disasm_str(dbg, convert_be(val),10)
				sf_list[name]["value"] = (convert_be(val), convert_le(val))
		idx+=1
	return sf_list

def dump_stack(dbg, context, stack_info, stack_list):
	# make it extensible to any architecture just change out regs here
	# and in the actual dump function
	regs = ["eip", "eax", "ebx", "ecx", "edx", "edi",
		"esi", "ebp", "esp"]
	stack_dump  = "STACK DUMP\n"
	for reg in regs:
	    stack_dump += "  %s: %08x %s\n" % (reg.upper(),\
	    					stack_list[reg]["value"],\
						stack_list[reg]["desc"])
	ebp = stack_list["ebp"]["value"]
	for stack_elem in stack_info:
		desc = stack_list[stack_elem[0]]["desc"]
		if stack_list[stack_elem[0]]["desc"].find("READ ERROR") > -1:
			desc = stack_list[stack_elem[0]]["desc"] +"\n\n" + str(stack_list[stack_elem[0]]["disasm"])
		stack_dump += "  %s: 0x%08x (BE: 0x%x, LE: 0x%x) (stack buffer?)-> %s\n" % \
		(       stack_elem[0],   \
				ebp+stack_elem[1],\
				stack_list[stack_elem[0]]["value"][0],   \
				stack_list[stack_elem[0]]["value"][1],   \
				desc     \
		)
	return stack_dump


def stack_dump_table(dbg, context):
	eip = context.Eip
	if eip == 0x004510d0:
		return dump_sub_4510D0_stack(dbg,  context)
	if eip == 0x004510da:
		return dump_sub_4510D0_stack(dbg,  context)
	if eip == 0x004502dd:
		return dump_sub_4502DD_stack(dbg,  context)
	if eip == 0x0048f6ca:
		return dump_sub_48F6CA_stack(dbg,  context)
	if eip == 0x00441f58:
		return dump_sub_441F58_stack(dbg,  context)
	if eip == 0x0043b295:
		return dump_sub_43B295_stack(dbg,  context)
	if eip == 0x00499f7e:
		return dump_sub_499F7E_stack(dbg,  context)
	else: return ''

def dump_sub_4510D0_stack(dbg, context):
	stack_info = [('var_204', 0x204),
		 ('var_1FD', 0x1fd),
		 ('var_1F8', 0x1f8),
		 ('var_1EC', 0x1ec),
		 ('var_1E4', 0x1e4),
		 ('var_1DC', 0x1dc),
		 ('var_1C0', 0x1c0),
		 ('var_1B8', 0x1b8),
		 ('var_1AC', 0x1ac),
		 ('var_198', 0x198),
		 ('var_194', 0x194),
		 ('var_180', 0x180),
		 ('var_168', 0x168),
		 ('var_160', 0x160),
		 ('var_15C', 0x15c),
		 ('var_148', 0x148),
		 ('var_130', 0x130),
		 ('var_128', 0x128),
		 ('var_120', 0x120),
		 ('var_104', 0x104),
		 ('var_E8', 0xe8),
		 ('var_CC', 0xcc),
		 ('var_B0', 0xb0),
		 ('var_A8', 0xa8),
		 ('var_A0', 0xa0),
		 ('var_5C', 0x5c),
		 ('var_C', 0xc),
		 ('arg_0', 0x-8)]
	stack_list = get_stack_info(dbg, context, stack_info)
	stack_dump = dump_stack(dbg, context, stack_info, stack_list)
	return stack_dump 


def dump_sub_4502DD_stack(dbg, context):
	stack_info = []
	stack_list = get_stack_info(dbg, context, stack_info)
	stack_dump = dump_stack(dbg, context, stack_info, stack_list)
	return stack_dump 


def dump_sub_48F6CA_stack(dbg, context):
	stack_info = [('r', 0x-8),
		 ('arg_4', 0x-10)]
	stack_list = get_stack_info(dbg, context, stack_info)
	stack_dump = dump_stack(dbg, context, stack_info, stack_list)
	return stack_dump 


def dump_sub_441F58_stack(dbg, context):
	stack_info = []
	stack_list = get_stack_info(dbg, context, stack_info)
	stack_dump = dump_stack(dbg, context, stack_info, stack_list)
	return stack_dump 


def dump_sub_43B295_stack(dbg, context):
	stack_info = [('var_310', 0x310),
		 ('var_308', 0x308),
		 ('var_300', 0x300),
		 ('var_2F8', 0x2f8),
		 ('var_2F4', 0x2f4),
		 ('var_2EC', 0x2ec),
		 ('var_2E4', 0x2e4),
		 ('var_2DC', 0x2dc),
		 ('var_2C0', 0x2c0),
		 ('var_2B8', 0x2b8),
		 ('var_2B0', 0x2b0),
		 ('var_299', 0x299),
		 ('var_294', 0x294),
		 ('var_28D', 0x28d),
		 ('var_280', 0x280)]
	stack_list = get_stack_info(dbg, context, stack_info)
	stack_dump = dump_stack(dbg, context, stack_info, stack_list)
	return stack_dump 


def dump_sub_499F7E_stack(dbg, context):
	stack_info = [('var_324', 0x324),
		 ('arg_0', 0x-8)]
	stack_list = get_stack_info(dbg, context, stack_info)
	stack_dump = dump_stack(dbg, context, stack_info, stack_list)
	return stack_dump 

stack_dump_bps= [0x48f6ca, 0x441f58, 0x4510d0, 0x4510da, 0x43b295, 0x4502dd, 0x40abbe, 0x499f7e]

