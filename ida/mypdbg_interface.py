''' Adapted from:


'''

import sys,getopt,struct,signal
from mod_debuggee_procedure_call import *
from pydbg import *
from pydbg.defines import *
from pydbg.pydbg_core import *
from pydbg_stack_dmp import *
from IPython.Shell import IPShellEmbed
import time
from subprocess import *
from mypdbg_bps import *
from mypdbg_hooks import *


'''
following 4 lines taken from script by pedram for trillian bug
'''






class SigHandler:
	'''
	class definition taken from http://www.bintest.com/extending_pydbg.html
	'''
	def __init__(self):
		self.signaled = 0
		self.sn=None
	reset = __init__

	def __call__(self, sn, sf):
		self.sn = sn
		self.signaled += 1
		
class Tdbg(pydbg,pydbg_core):
	'''
		class definition and concept taken from http://www.bintest.com/extending_pydbg.html
	'''
	def __init__(self):
		pydbg.__init__(self)
		self.sh = sh = SigHandler()
		signal.signal(signal.SIGBREAK,sh)
		self.ss_tids = set()

	def convert_bytes_to_int(self, buffer, bytes = 4):
		'''
			convert the bytes to an integer big endian
		'''
		i = 0
		cnt = 0
		while cnt < bytes:
			j = ord(buffer[cnt]) &0xff
			i = j + (i << 8)
			cnt += 1
		return i

	def convert_bytes_to_int_fe(self, buffer, bytes = 4):
		'''
			convert flip the endianness of the bytes and convert to an 
			integer little endian
		'''
		i = 0
		cnt = 0
		buffer = self.convert_rb_endianess(buffer)
		while cnt < bytes:
			j = ord(buffer[cnt]) &0xff
			i = j + (i << 8)
			cnt += 1	
		return i
	
	def convert_rb_endianess(self, buffer):
		'''
			convert the endianess on a set of raw bytes
		'''
		h = [i for i in buffer]
		h.reverse()
		return "".join(h)

	def convert_int_endianess(self, integer):
		'''
			convert the endianess of an integer value
		'''
		i_buf = self.flip_endian(integer)
		return self.convert_bytes_to_int(i_buf)
	
	def convert_to_rb(self, val, bytes = 4):
		'''
			integer value to convert into a set of raw bytes
		'''
		buffer = []
		cnt = 0
		v = val
		while cnt < bytes:
			buffer.append(v & 0xff)
			v >>= 8
			cnt += 1
		buffer.reverse()
		buffer = map(chr, buffer)
		return "".join(buffer)
	
	def convert_int_to_bytes_fe(self, val, bytes = 4):
		'''
			convert integer to raw bytes and flip the endianness
		'''
		buffer = []
		cnt = 0
		v = val
		while cnt < bytes:
			buffer.append(v & 0xff)
			v >>= 8
			cnt += 1
		buffer = map(chr, buffer)
		return "".join(buffer)
	
	def debug_event_iteration(self):
		pydbg.debug_event_iteration(self)
		sh = self.sh
		if sh.signaled and sh.sn:
			if sh.sn==signal.SIGBREAK:
				ipshell = IPShellEmbed()
				ipshell()
			sh.reset()

	def enable_ss(self, tid):
		'''
			Enable Single Stepping on a thread
		'''
		if tid is None:
			tid = self.enumerate_threads()[0]
		try:
			h_thread = self.open_thread(tid)
			self.single_step(True, h_thread)
			self.ss_tids.add(tid)
		except: pass

	def disable_ss(self, tid):
		'''
			Disable single stepping on a thread
		'''
		if not tid in self.ss_tids:
			return
		if tid is None:
			tid = self.enumerate_threads()[0]
		try:
			h_thread = self.open_thread(tid)
			self.single_step(False, h_thread)
			self.ss_tids.remove(tid)
		except: pass

	def enable_all_ss(self):
		'''
			Enable Single Stepping on all threads
		'''
		tid_list = self.enumerate_threads()
		for tid in tid_list:
			enable_ss(tid)

	def disable_all_ss(self):
		'''
			Disable Single Stepping on all threads
		'''
		for tid in self.ss_tids:
			disable_ss(self, tid)
	
	def update_threads_contexts(self):
		'''
			Update the contexts for all the threads running in the process
		'''
		tlist = self.enumerate_threads()
		self.contexts = {}
		for tid in tlist:
			if tid == 0:
				print "Invalid TID %08x"%tid
				continue
			context = self.get_thread_context(None, thread_id=tid)
			retaddr = self.get_arg(0, context)
			self.contexts[tid] = context
		return self.contexts
	
	def give_shell(self):
		'''
			Give an Ipython shell to the user so they can interact with the Debugger
		'''
		print "\n\n****Entering dbg shell"
		ipshell = IPShellEmbed()
		ipshell()
		print "\n\n***Exiting the debug shell\n\n"
	
	# redefine the dump_*context methods with only context here
	def dump_context(self, context, stack_depth=5, print_dots = True):
		'''
			Overrode Pedram's Implementation of dump_context
		'''
		context_list = self.dump_context_list(context, stack_depth, print_dots)

		context_dump  = "CONTEXT DUMP\n"
		context_dump += "  EIP: %08x %s\n" % (context.Eip, context_list["eip"])
		context_dump += "  EAX: %08x (%10d) -> %s\n" % (context.Eax, context.Eax, context_list["eax"])
		context_dump += "  EBX: %08x (%10d) -> %s\n" % (context.Ebx, context.Ebx, context_list["ebx"])
		context_dump += "  ECX: %08x (%10d) -> %s\n" % (context.Ecx, context.Ecx, context_list["ecx"])
		context_dump += "  EDX: %08x (%10d) -> %s\n" % (context.Edx, context.Edx, context_list["edx"])
		context_dump += "  EDI: %08x (%10d) -> %s\n" % (context.Edi, context.Edi, context_list["edi"])
		context_dump += "  ESI: %08x (%10d) -> %s\n" % (context.Esi, context.Esi, context_list["esi"])
		context_dump += "  EBP: %08x (%10d) -> %s\n" % (context.Ebp, context.Ebp, context_list["esi"])
		context_dump += "  ESP: %08x (%10d) -> %s\n" % (context.Esp, context.Esp, context_list["esp"])

		for offset in xrange(0, stack_depth + 1):
			if offset * 4 >= 0x300:
			    break
			context_dump += "  +%02x: %08x (%10d) -> %s\n" %    \
			(                                                   \
				offset * 4,                                     \
				context_list["esp+%02x"%(offset*4)]["value"],   \
				context_list["esp+%02x"%(offset*4)]["value"],   \
				context_list["esp+%02x"%(offset*4)]["desc"]     \
			)
		return context_dump
	def dump_context_list (self, context=None, stack_depth=5, print_dots=True):
		'''
			Overrode Pedram's Implementation of dump_context
		'''
		context_list = {}

		context_list["eip"] = self.disasm(context.Eip)
		context_list["eax"] = self.smart_dereference(context.Eax, print_dots)
		context_list["ebx"] = self.smart_dereference(context.Ebx, print_dots)
		context_list["ecx"] = self.smart_dereference(context.Ecx, print_dots)
		context_list["edx"] = self.smart_dereference(context.Edx, print_dots)
		context_list["edi"] = self.smart_dereference(context.Edi, print_dots)
		context_list["esi"] = self.smart_dereference(context.Esi, print_dots)
		context_list["ebp"] = self.smart_dereference(context.Ebp, print_dots)
		context_list["esp"] = self.smart_dereference(context.Esp, print_dots)

		for offset in xrange(0, stack_depth + 1):
			# no try/except here because ESP *should* always be readable and i'd really like to know if it's not.
			try:
				esp = self.flip_endian_dword(self.read_process_memory(context.Esp + offset * 4, 4))
				context_list["esp+%02x"%(offset*4)]          = {}
				context_list["esp+%02x"%(offset*4)]["value"] = esp
				context_list["esp+%02x"%(offset*4)]["desc"]  = self.smart_dereference(esp, print_dots)
			except:
				#esp = self.flip_endian_dword(self.read_process_memory(context.Esp + offset * 4, 4))
				context_list["esp+%02x"%(offset*4)]          = {}
				context_list["esp+%02x"%(offset*4)]["value"] = "?????"
				context_list["esp+%02x"%(offset*4)]["desc"]  = "ERROR: Failed Read"
		return context_list

	
def get_reg_value(context, register):
	''' Taken from cody pierce mindshaRE post
	'''
	if   register == "eax" or register == 0: return context.Eax
	elif register == "ecx" or register == 1: return context.Ecx
	elif register == "edx" or register == 2: return context.Edx
	elif register == "ebx" or register == 3: return context.Ebx
	elif register == "esp" or register == 4: return context.Esp
	elif register == "ebp" or register == 5: return context.Ebp
	elif register == "esi" or register == 6: return context.Esi
	elif register == "edi" or register == 7: return context.Edi
	elif register == "eip" or register == 8: return context.Eip

	return False
	





def kickstart_process(filename):
    p = Popen(filename, stdin=PIPE, stdout=PIPE)
    return p

def special_treatment(dbg, context, tid):
	if context.Eip == 0x408AEC or context.Eip == 0x00408d0a:
		print "Setting up x%08x for tracing"%tid
		dbg.enable_ss(tid)
   
	


def setup_proc(dbg, malware, wait=0, bp_list=None):
	'''
		Kick start the process specified by malware and then attach to it after (wait) seconds
		then we set the breakpoints in bp_list 
	'''
	p = kickstart_process(malware)
	if wait:
	  time.sleep(wait)
	dbg.attach(p.pid)
	if not bp_list is None:
	  set_bp_list(dbg, bp_list)
	return p


def quick_setup(dbg):
	'''
		Quick start up function for the debugger and the target process.  We let the program run for one second and then attach to it
		
	'''
	global interesting_bps, malware_name, stack_dump_bps, my_bps
	return setup_proc(dbg, malware_name, 1, stack_dump_bps+my_bps)
   

dbg = Tdbg()
dbg.set_callback(EXCEPTION_BREAKPOINT,       handler_breakpoint)
dbg.set_callback(EXCEPTION_SINGLE_STEP,       handler_breakpoint)
malware_name = "saleslist.exe"



if __name__ == "__main__":
   print """Run the following commands to get started:
			quick_setup(dbg)
			dbg.run()"""
   dbg.give_shell()