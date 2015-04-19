#(c) Adam Pridgen adam.pridgen@thecoverofnight.com
# GPL v3
start = AskAddr(0xFFFFFFFF, "Enter start address.")
end = AskAddr(0xFFFFFFFF, "Enter end address.")
incr = AskLong(4, "What is the offset from one table entry to the next?")

def transform_to_code(start, end):
  while start < end:
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
  start += 4

print "Finished cleaning up the jump table code."
