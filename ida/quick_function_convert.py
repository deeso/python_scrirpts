end = 0x04CF274
start = ScreenEA()
print "***********************"
while start < end:
  if Dfirst(start) == 0xFFFFFFFF or not isCode(Dfirst(start)): 
    print "Skipping x%x"%start
    start += 4
    continue
  print "Making code start = x%x code ref = x%x funcend = x%x"%(start, Dfirst(start),FindFuncEnd(Dfirst(start))) 
  MakeFunction(Dfirst(start),FindFuncEnd(start))
  start += 4
