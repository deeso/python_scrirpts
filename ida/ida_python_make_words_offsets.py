end = 0x04D4C20
start = 0x004E0848


def make_n_dwords(ea,num):
  print "Making %u dwords starting at %x"%(num, ea)
  for i in xrange(0,num):
    MakeDword(ea+4*i)
  return num*4

while start < end:
  MakeNameEx(start, GetString(Dfirst(start), -1, 0), 0)
  x = make_n_dwords(start, 6)
  print hex(start)
  print "Make name result ", str(y)
  OpOff(start+x-8, 0, 0x00)
  start += x