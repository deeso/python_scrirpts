#!c:\python\python.exe

#
# PyDbg Debuggee Procedure Call Hack
# Copyright (C) 2006 Pedram Amini <pedram.amini@gmail.com>
#
# $Id: debuggee_procedure_call.py 194 2007-04-05 15:31:53Z cameron $
#
# This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program; if not, write to the Free
# Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#

'''
@author:       Pedram Amini
@license:      GNU General Public License 2.0 or later
@contact:      pedram.amini@gmail.com
@organization: www.openrce.org
'''

import sys
import struct
import utils

from pydbg import *
from pydbg.defines import *

class __global:
    def __repr__ (self):
        rep = ""

        for key, val in self.__dict__.items():
            if type(val) is int:
                rep += "  %s: 0x%08x, %d\n" % (key, val, val)
            else:
                rep += "  %s: %s\n" % (key, val)

        return rep

allocations   = []           # allocated (address, size) tuples.
cmd_num       = 0            # keep track of executed commands.
glob          = __global()   # provide the user with a globally accessible persistent storage space.
saved_context = None         # saved thread context prior to CALL insertion.
dbg           = pydbg()      # globally accessible pydbg instance.
container     = None         # address of memory allocated for instruction container.

# enable / disable logging here.
#log = lambda x: sys.stdout.write("> " + x + "\n")
log = lambda x: None


########################################################################################################################
def alloc (size):
    '''
    Convenience wrapper around pydbg.virtual_alloc() for easily allocation of read/write memory. This routine maintains
    the global "allocations" table.

    @type  size: Long
    @param size: Size of MEM_COMMIT / PAGE_READWRITE memory to allocate.

    @rtype:  DWORD
    @return: Address of allocated memory.
    '''

    global dbg, allocations

    if not size:
        return

    address = dbg.virtual_alloc(None, size, MEM_COMMIT, PAGE_EXECUTE_READWRITE)

    # make a record of the address/size tuple in the global allocations table.
    allocations.append((address, size))

    return address


########################################################################################################################
def handle_av (dbg):
    '''
    As we are mucking around with process state and calling potentially unknown subroutines, it is likely that we may
    cause an access violation. We register this handler to provide some useful information about the cause.
    '''

    crash_bin = utils.crash_binning.crash_binning()
    crash_bin.record_crash(dbg)

    print crash_bin.crash_synopsis()
    dbg.terminate_process()


########################################################################################################################
def handle_bp (dbg):
    '''
    This callback handler is responsible for establishing and maintaining the command-read loop. This handler seizes
    control-flow at the first chance breakpoint.

    At the command prompt, any Python statement can be executed. To store variables persistently across iterations over
    this routine, use the "glob" global object shell. The built in commands include:

        DONE, GO, G

    For continuing the process. And for calling arbitrary procedures:

        dpc(address, *args, **kwargs)

    For more information, see the inline documentation for dpc(). Note: You *can not* directly assign the return value
    from dpc(). You must explicitly assign Eax, example:

        var = dpc(0xdeadbeef, "pedram")     # INCORRECT

        dpc(0xdeadbeef, "pedram")           # CORRECT
        var = dbg.context.Eax

    @see: dpc()
    '''

    global allocations, cmd_num, saved_context, glob

    log("breakpoint hit")

    if not dbg.first_breakpoint:
        # examine the return value.
        ret      = dbg.context.Eax
        byte_ord = ret & 0xFF
        status   = "procedure call returned: %d 0x%08x" % (ret, ret)
        deref    = dbg.smart_dereference(ret, print_dots=False)

        if byte_ord >= 32 and byte_ord <= 126:
            status += " '%c'" % byte_ord

        if deref != "N/A":
            status += " -> %s" % deref

        print status

    # when we first get control, save the context of the thread we are about to muck around with.
    if not saved_context:
        saved_context = dbg.get_thread_context(dbg.h_thread)

    # command loop.
    while 1:
        try:
            command = raw_input("\n[%03d] CMD> " % cmd_num)
        except:
            return DBG_CONTINUE

        if type(command) is str:
            # cleanup and let the process continue execution.
            if command.upper() in ["DONE", "GO", "G"]:
                dbg.set_thread_context(saved_context)
                free_all()
                break

        try:
            exec(command)
            cmd_num += 1
    
            # implicit "GO" after dpc() commands.
            if type(command) is str and command.lower().startswith("dpc"):
                break
        except:
            sys.stderr.write("failed executing: '%s'.\n" % command)

    log("continuing process")
    return DBG_CONTINUE


########################################################################################################################
def free (address_to_free):
    '''
    Convenience wrapper around pydbg.virtual_free() for easily releasing allocated memory. This routine maintains
    the global "allocations" table.

    @type  address: DWORD
    @param address: Address of memory chunk to free.
    '''

    global dbg, allocations

    for address, size in allocations:
        if address == address_to_free:
            dbg.virtual_free(address, size, MEM_DECOMMIT)

            # remove the address/size tuple from the global allocations table.
            allocations.remove((address, size))


########################################################################################################################
def free_all ():
    '''
    Free all entries in the global allocations table. Useful for when you have done a bunch of testing and want to
    release all the allocated memory.
    '''

    global allocations

    while len(allocations):
        for address, size in allocations:
            free(address)


########################################################################################################################
def dpc (address, *args, **kwargs):
    '''
    This routine is the real core of the script. Given an address and arguments it will allocate and initialize space
    in the debuggee for storing the necessary instructions and arguments and then redirect EIP from the current thread
    to the newly created instructions. A breakpoint is written after the assembled instruction set that is caught by
    our breakpoint handler which re-prompts the user for further commands. Note: You *can not* directly assign the
    return value from dpc(). You must explicitly assign Eax, example:

        var = dpc(0xdeadbeef, "pedram")     # INCORRECT

        dpc(0xdeadbeef, "pedram")           # CORRECT
        var = dbg.context.Eax

    @type  address: DWORD
    @param address: Address of procedure to call.
    @type  args:    List
    @param args:    Arguments to pass to procedure.
    @type  kwargs:  Dictionary (Keys can be one of EAX, EBX, ECX, EDX, ESI, EDI, ESP, EBP, EIP)
    @param kwargs:  Register values to set prior to calling procedure.
    '''

    global dbg, allocations, container

    PUSH = "\x68"
    CALL = "\xE8"
    INT3 = "\xCC"

    # XXX - freeing an address that bp_del is later trying to work on.
    if container:
        pass #free(container)

    # allocate some space for our new instructions and update EIP to point into that new space.
    container = eip = alloc(512)
    dbg.context.Eip = eip

    dbg.set_register("EIP", eip)

    log("setting EIP of thread %d to 0x%08x" % (dbg.dbg.dwThreadId, eip))

    # args are pushed in reverse order, make it a list and reverse it.
    args = list(args)
    args.reverse()

    for arg in args:
        log("processing argument: %s" % arg)

        # if the argument is a string. allocate memory for the string, write it and set the arg to point to the string.
        if type(arg) is str:
            string_address = alloc(len(arg))
            log("  allocated %d bytes for string at %08x" % (len(arg), string_address))
            dbg.write(string_address, arg)
            arg = string_address

        # assemble and write the PUSH instruction.
        assembled = PUSH + struct.pack("<L", arg)
        log("  %08x: PUSH 0x%08x" % (eip, arg))
        dbg.write(eip, assembled)
        eip += len(assembled)

    for reg, arg in kwargs.items():
        log("processing register %s argument: %s" % (reg, arg))

        if reg.upper() not in ("EAX", "EBX", "ECX", "EDX", "ESI", "EDI", "ESP", "EBP", "EIP"):
            sys.stderr.write(">   invalid register specified: %s\n" % reg)
            continue

        # if the argument is a string. allocate memory for the string, write it and set the arg to point to the string.
        if type(arg) is str:
            string_address = alloc(len(arg))
            log("  allocated %d bytes for string at %08x" % (len(arg), string_address))
            dbg.write(string_address, arg)
            arg = string_address

        # set the appropriate register to contain the argument value.
        dbg.set_register(reg, arg)

    # assemble and write the CALL instruction.
    relative_address = (address - eip - 5)  # -5 for the length of the CALL instruction
    assembled        = CALL + struct.pack("<L", relative_address)

    log("%08x: CALL 0x%08x" % (eip, relative_address))
    dbg.write(eip, assembled)
    eip += len(assembled)

    # set a breakpoint after the call.
    log("setting breakpoint after CALL at %08x" % eip)
    dbg.bp_set(eip, restore=False)


########################################################################################################################
def show_all ():
    '''
    Print a hex dump for all of the tracked allocations.
    '''

    global dbg, allocations

    for address, size in allocations:
        print dbg.hex_dump(dbg.read(address, size), address)


########################################################################################################################
if len(sys.argv) != 2:
    sys.stderr.write("USAGE: debuggee_procedure_call.py <process name | pid>\n")
    sys.exit(1)

dbg.set_callback(EXCEPTION_BREAKPOINT,       handle_bp)
dbg.set_callback(EXCEPTION_ACCESS_VIOLATION, handle_av)

try:
    pid          = int(sys.argv[1])
    found_target = True
except:
    found_target = False
    for (pid, proc_name) in dbg.enumerate_processes():
        if proc_name.lower() == sys.argv[1]:
            found_target = True
            break

print "attaching to %d" % pid

if found_target:
    dbg.attach(pid)
    dbg.debug_event_loop()
else:
    sys.stderr.write("target '%s' not found.\n" % sys.argv[1])