#(c) Adam Pridgen adam.pridgen@thecoverofnight.com
# GPL v3

start = ScreenEA()
end = 0x04F1ACD
align = AskLong(4, "Enter an alignment (4) by default.")
if start >= end:
  print "Please enter a valid start and end address start: 0x%08x end: 0x%08x."%(start,end)

def get_align(length, align):
  if length%align == 0: return 0
  return (align - length%align)%align


while start < end:
  string = GetString(start,-1,0)
  incr = align
  if not string is None:
    MakeStr(start, start+len(string)+1)
    print hex(start),string
    base = len(string)+1 + get_align(len(string)+1, align)
  start += base + 1

print "Finished converting to strings."
