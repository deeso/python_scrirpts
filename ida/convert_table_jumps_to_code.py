#(c) Adam Pridgen adam.pridgen@thecoverofnight.com
# GPL v3
start = AskAddr(0xFFFFFFFF, "Enter start address.")
end = AskAddr(0xFFFFFFFF, "Enter end address.")
addr_sz = AskLong(4, "Size of offset to each entry in bytes?")

def transform_to_code(start, end):
  while start < end:
	if isCode(start):  return
	l = MakeCode(start)
	if l:
	  print "Converted 0x%08x to code."%start
	  start += l
	elif GetOpType(start, 0) == -1:
	  start+=1
	else:
	  break
  return start

if start >= end:
  print "Please enter a valid start and end address start: 0x%08x end: 0x%08x."%(start,end)

while  start < end:
  if Dfirst(start) != 0xFFFFFFFF:
	transform_to_code(Dfirst(start), Dfirst(start)+1)
  start += addr_sz

print "Finished cleaning up the jump table code."
