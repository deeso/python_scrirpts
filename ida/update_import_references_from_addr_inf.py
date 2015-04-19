MAX_EA = 0xFFFFFFFF

f = open("C:\\imports.txt").readlines()
f = "".join(f).split("\n")
addr_to_names = {}

for i in f:
  if i == "": continue
  addr, name = i.strip().split()
  addr_to_names[int(addr,16)] = name

start = AskAddr(MAX_EA, "Enter a Start Address.")
end = AskAddr(MAX_EA, "Enter an End Address.")

def fix_name(addr, name, flags):
   cnt = 0
   result = MakeNameEx(addr, name+"_%u"%cnt, flags)
   while not result:
     result = MakeNameEx(addr, name+"_%u"%cnt, flags)
     cnt += 1

def name_addresses(start, end, addr_to_names, align = 8, flags=0x000):
  addr = start
  while addr < end:
     dword = Dword(addr)
     if not dword in addr_to_names: 
        addr += align
        continue
     name = addr_to_names[dword]
     print "Making name %s @ %x for val %x"%(name, addr, dword)
     cnt = 0
     nname = name
     result = MakeNameEx(addr, name+"_%u"%cnt, flags)
     if result is False: fix_name(addr, name, flags)
     addr += align



if start > end and end != MAX_EA:
  print "Please enter a valid addresses."
else:
  print "Updating Import Table References from %x to %x."%(start, end)
  name_addresses(start, end, addr_to_names, flags = SN_NOCHECK|SN_NOWARN|SN_AUTO)  