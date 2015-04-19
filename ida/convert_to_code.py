#(c) Adam Pridgen adam.pridgen@thecoverofnight.com
# GPL v3
start = AskAddr(0xFFFFFFFF, "Enter start address.")
end = AskAddr(0xFFFFFFFF, "Enter end address.")

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

transform_to_code(start, end)
current = NextHead(start, end)
while NextHead(current, end) != BADADDR:
  prev = current
  current = NextHead(current, end)
  if current - prev > 5:
	current = transform_to_code(current, end)
