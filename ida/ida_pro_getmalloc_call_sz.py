import sys
import idc
import idaapi
import idautils

from ida_pro_collection import *

function_name = '_malloc'
instruction = 'push'

names = get_all_names()

    

x = filter_inclusive_names(names, ['_malloc'])
# reverse the dictionary, make it name --> addr
x = reverse_map(x)

#if not function_name in x:
#    sys.exit()

callers = []

if not x is None and function_name in x:
    for xref in idautils.XrefsTo(x[function_name]):
        caddr = find_first_instr(xref.frm, instruction)
        value = "Could not find the specificed command on the reverse flow path"
        if not caddr is None:
            value = "%s:%s"%(get_name(caddr), idc.GetDisasm(caddr))
        value = "Xref %s: %s"%(get_name(xref.frm),value)
        callers.append(value)
    

reg_push = []
imm_push = []
for i in callers:
    f = i.split(";")[0].split()[-1]
    if f.isdigit() or f.find("h")>-1 and f.find("[") == -1:
        imm_push.append(i)
    else:
        reg_push.append(i)

print "Immediated Pushes before Malloc is Called"
print "\n".join(imm_push)


print "Register Pushes before Malloc is Called"
print "\n".join(reg_push)