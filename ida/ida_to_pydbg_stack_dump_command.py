addr = AskAddr(0xFFFFFFFF, "Enter Function Address")

if addr == 0xFFFFFFFF:
  Exit("Enter a valid address")

fname = GetFunctionName(addr)
fstart = GetFunctionAttr(addr,FUNCATTR_START)
fframe = GetFrame(fstart)

fmembers = []
count = GetMemberQty(fframe)
idx = 2 # ignore sp and return
end = GetLastMember(fframe)
off = GetFirstMember(fframe)
while off < end+1:
  off = GetStrucNextOff(fframe, off)
  name = GetMemberName(fframe, off)
  if name != None:
    if name != "s" and name != "r":
      fmembers.append((name,off))
  if GetMemberSize(fframe, off) is None:
    off += 1
  else: off += GetMemberSize(fframe, off)



def_str = '''
def dump_%s_stack(dbg, context):
  stack_info = %s'''%(fname, "),\n".join(str(fmembers).split("),")))

body = '''
  stack_list = get_stack_info(dbg, context, stack_info)
  stack_dump = dump_stack(dbg, context, stack_info, stack_list)
  log("Stack Dump for %08x"%(dbg.dbg.dwThreadId))
  log("%s"%(stack_dump))
  return stack_dump
'''

print def_str + body 

