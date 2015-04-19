import sys,getopt,struct,signal
from mod_debuggee_procedure_call import *
from pydbg import *
from pydbg.defines import *
from pydbg.pydbg_core import *
from pydbg_stack_dmp import *
from IPython.Shell import IPShellEmbed
import time
from subprocess import *


cwrite = lambda msg: sys.stdout.write(msg + "\n")
hooks = utils.hook_container()

default_LOGFILE = "C:\\default_hook.log"
DLF_SD = open(default_LOGFILE, "a")
default_fwrite = lambda msg: DLF_SD.write( msg + "\n")
def default_log(msg):
  cwrite(msg)
  default_fwrite(msg)


def default_hook_logger(dbg, args, ret = None):
	dbg.update_threads_contexts()
	tid = dbg.dbg.dwThreadId
	context = dbg.contexts[tid]
	if ret is None:
		default_log("Hooked into TID: %u EIP: %x"%(tid, context.Eip))
		default_log("Default HOOK STACK UNWIND > %s"%str(map(hex, dbg.stack_unwind(context))))
	else:
		default_log("Leaving Hooked TID: %u EIP: %x"%(tid, context.Eip))
		ret = None
	arg_strs = map(hex, args)
	arg_str = ""
	for i in xrange(0, 6):
	   arg_str += "arg[%u]: %s\n"%(i, arg_strs[i])
	default_log("Argument List of 6:\n%s"%arg_str)
	for i in args:
		buf = ""
		buf2 = ""
		try:
			buf = dbg.read_process_memory(i, 10)
		except:
			try:
				buf = dbg.read_process_memory(dbg.convert_int_endianess(i), 10)
			except:
				buf = "Failed to read from address"
		try:
			buf2 = dbg.smart_dereference(i, 10)
		except:
			try:
				buf2 = dbg.smart_dereference(dbg.convert_int_endianess(i), 10)
			except:
				buf2 = "Failed to read from address"
		default_log("Address %x holds buffer: %s\nsmart dereferenced string: %s\n"%(i, repr(buf), repr(buf2)))
	default_log("CONTEXT DUMP: %s\n"%dbg.dump_context(context))


build_node_information_LOGFILE = "C:\\build_node_information.log"
BLF_SD = open(build_node_information_LOGFILE, "a")
build_node_information_fwrite = lambda msg: BLF_SD.write( msg + "\n")
	
def bni_log(msg):
  cwrite(msg)
  default_fwrite(msg)


def bni_hook_logger(dbg, args, ret = None):
	dbg.update_threads_contexts()
	tid = dbg.dbg.dwThreadId
	context = dbg.contexts[tid]
	if ret is None:
		default_log("Hooked into TID: %u EIP: %x"%(tid, context.Eip))
		default_log("Default HOOK STACK UNWIND > %s"%str(map(hex, dbg.stack_unwind(context))))
	else:
		default_log("Leaving Hooked TID: %u EIP: %x"%(tid, context.Eip))
		ret = None
	arg_strs = map(hex, args)
	arg_str = ""
	for i in xrange(0, 6):
	   arg_str += "arg[%u]: %s\n"%(i, arg_strs[i])
	default_log("Argument List of 6:\n%s"%arg_str)
	for i in args:
		buf = ""
		buf2 = ""
		try:
			buf = dbg.read_process_memory(i, 10)
		except:
			try:
				buf = dbg.read_process_memory(dbg.convert_int_endianess(i), 10)
			except:
				buf = "Failed to read from address"
		try:
			buf2 = dbg.smart_dereference(i, 10)
		except:
			try:
				buf2 = dbg.smart_dereference(dbg.convert_int_endianess(i), 10)
			except:
				buf2 = "Failed to read from address"
		default_log("Address %x holds buffer: %s\nsmart dereferenced string: %s\n"%(i, repr(buf), repr(buf2)))
	default_log("CONTEXT DUMP: %s\n"%dbg.dump_context(context))

memcpy_LOGFILE = "C:\\memcpy_hook.log"
MLF_SD = open(memcpy_LOGFILE, "a")
memcpy_fwrite = lambda msg: MLF_SD.write( msg + "\n")

def memcpy_log(msg):
  cwrite(msg)
  memcpy_fwrite(msg)

afunc_LOGFILE = "C:\\abstract_funtion_hook.log"
AFLF_SD = open(afunc_LOGFILE, "a")
afunc_fwrite = lambda msg: AFLF_SD.write( msg + "\n")


def afunc_log(msg):
  cwrite(msg)
  afunc_fwrite(msg)

def memcpy_entry(dbg, args):
	global hooks
	dbg.update_threads_contexts()
	tid = dbg.dbg.dwThreadId
	context = dbg.contexts[tid]
	callers = dbg.stack_unwind(context)
	memcpy_log("Memcpy into TID: %u EIP: %x"%(tid, context.Eip))
	memcpy_log("Memcpy LOG> STACK UNWIND: %s"%str(map(hex, dbg.stack_unwind(context))))
	src = args[0]
	dst = args[1]
	len = args[2]
	for caller in callers:
		try:
			hooks.add(dbg,caller, 6, default_hook_logger, None)#memcpy_exit)
		except:
			print "FAILED TO SET a valid break point at the caller %x"%caller
	memcpy_log("Memcpy LOG > called with the following args:\n\tsrc = %x\n\tdst = %x,\n\tlen = %d (decimal)"%(src,dst,len))
	buf = dbg.smart_dereference(src, print_dots=False)
	buf2 = dbg.read_process_memory(src, len)
	#dbg.give_shell()
	memcpy_log("Memcpy Read the following from src:\n\t%s"%(repr(buf2)))
	memcpy_log("Memcpy Smart Dereferenced buffer from src:\n\t%s"%buf)
	memcpy_log("Memcpy Context Dump>\n %s"%dbg.dump_context(context))


def memcpy_exit(dbg, args, ret):
	dbg.update_threads_contexts()
	tid = dbg.dbg.dwThreadId
	context = dbg.contexts[tid]
	#log("memcpy called with the following args:\n src = %x\ndst = %x, len = %x"%(src,dst,len))
	memcpy_log("memcpy has  a return = %x"%ret)
	memcpy_log("memcpy Context Dump> %s"%dbg.dump_context(context))
	#log("TEST ENTRY LOG> ret = %s"%(repr(ret)))

def abstract_function_entry(dbg, args):
	dbg.update_threads_contexts()
	tid = dbg.dbg.dwThreadId
	context = dbg.contexts[tid]
	arg0 = args[0]
	arg1 = args[1]
	arg2 = args[2]
	afunc_log("abstract function stack  unwind > %s"%str(map(hex, dbg.stack_unwind(context))))
	afunc_log("Abstract function is called with the following args:\n arg[0] = %x\narg[1] = %x, arg[2] = %d (decimal)"%(arg0,arg1,arg2))
	afunc_log("Context Dump:\n%s"%dbg.dump_context(context))
	#afunc_log("Read the following from src:\n%s"%(repr(buf2)))
	#afunc_log("Smart Dereferenced buffer from src:\n%s"%buf)
	#dbg.give_shell()