import sys,getopt,struct,signal
from mod_debuggee_procedure_call import *
from pydbg import *
from pydbg.defines import *
from pydbg.pydbg_core import *
from pydbg_stack_dmp import *
from IPython.Shell import IPShellEmbed
import time
from subprocess import *
from mypdbg_hooks import *



LOGFILE = "C:\\bp_hit_log_dmps.log"
LF_SD = open(LOGFILE, "a")



first_breakpoint  = True
err = lambda msg: sys.stderr.write("ERR>   " + msg + "\n") or sys.exit(1)
cwrite = lambda msg: sys.stdout.write(msg + "\n")
fwrite = lambda msg: LF_SD.write( msg + "\n")


def log(msg):
   cwrite(msg)
   fwrite(msg)


def set_bp_list(dbg, interesting_bps):
	for i in interesting_bps:
		try:
			dbg.bp_set(i)
		except pdx:
			print pdx.message


EVP_EncryptUpdate = 0x478AAF, # EVP_EncryptUpdate
EVP_EncryptFinal  = 0x478BE8, # EVP_EncryptFinal
EVP_DecryptUpdate_end = 0x478C83+0xDF, # EVP_DecryptUpdate, end
EVP_DecryptFinal_end = 0x478D64+0xEE # EVP_DecryptFinal, end

my_bps = [    0x408AEC, # sub_routine that concatenates string for "a="+encrypted str 
0x408D07, # Mozilla & POST string used here
0x43D0F6, # POST string used here
0x4514DA, # POST string used here
#0x4089F5, # Mozilla string used here
#0x408CD0, # Mozilla string used here
#0x4089F5, # Mozilla string used here
0x4510D0,
0x452210, # Bp on function that uses POST
#0x48E980, # Hooked instead of bp'ed
0x401EEB
 ]

def read_evp_buffer(dbg, context, offset=0x0C):
	ebp = context.Ebp
	buf_addr = dbg.read_process_memory(ebp+offset, 4)
	buf_len = dbg.read_process_memory(ebp+offset+4, 4)
	log("Reading %u bytes from buffer at 0x%x"%(int(buf_len, 16), 
										dbg.flip_endian_dword((buf_addr))))
	buffer = dbg.read_process_memory(dbg.flip_endian_dword(buf_addr), 
									int(buf_len, 16))
	log("Read the following buffer:\n %s"%repr(buffer))

def handler_breakpoint(dbg):
	global first_breakpoint, EVP_DecryptUpdate_end, EVP_DecryptFinal_end, hooks
	bp_list = [EVP_EncryptUpdate,
			EVP_EncryptFinal,
			EVP_DecryptUpdate_end,
			EVP_DecryptFinal_end]
	if not dbg.bp_is_ours(EVP_EncryptUpdate):
		set_bp_list(dbg, bp_list)
	# ignore the first windows driven break point.
	#log("breakpoint handler hit from thread %08x" % dbg.dbg.dwThreadId)
	#log("Hit break point at ")
	if (first_breakpoint):
		first_breakpoint = False
		hooks.add(dbg,0x48e980, 3, abstract_function_entry, None)#memcpy_exit)
		hooks.add(dbg,0x48eaC0, 3, memcpy_entry, None)
		dbg.hide_debugger()
		return DBG_CONTINUE
	#log("breakpoint handler hit from thread %08x" % dbg.dbg.dwThreadId)
	# dump the context for each thread
	tlist = dbg.enumerate_threads()
	contexts = dbg.update_threads_contexts()
	#for tid in dbg.contexts:
	#   special_treatment(dbg, dbg.contexts[tid], tid)
	hTid = dbg.dbg.dwThreadId
	context = dbg.contexts[hTid]
	log("LOG> ThreadId: %d ThreadEip: 0x%x\n"%(hTid, context.Eip))
	if context.Eip == EVP_DecryptUpdate_end:
		read_evp_buffer(dbg, context, 0x0C)
	if context.Eip == EVP_DecryptFinal_end:
		read_evp_buffer(dbg, context, 0x08)
	if context.Eip == 0x408AEC:
		#log("Context Dump: %s"%dbg.dump_context(context, hTid))
		dbg.enable_ss(hTid)
		#dbg.give_shell()
	if context.Eip == 0x401EEB:
		#log("Context Dump: %s"%dbg.dump_context(context, hTid))
		dbg.enable_ss(hTid)
		#dbg.give_shell()
	# log("Dumping context for %s.\n\n"%hTid)
	# stack_dump = stack_dump_table(dbg, contexts[hTid])
	# if stack_dump != "":
	#	 log("STACK DUMP:\n %s\n************"%stack_dump)
	#	 dbg.give_shell()
	# else:
	#	 log("%s"%dbg.dump_context(dbg.contexts[hTid], hTid))
	return DBG_CONTINUE

def handler_single_step(dbg):
	cTid = dbg.dbg.dwThreadId
	context = dbg.contexts[cTid]
	log("LOG> SS TID: x%08x\n"%cTid)
	log("LOG> Dump Context:\n %s\n\n"%dbg.dump_context())
	return DBG_CONTINUE
