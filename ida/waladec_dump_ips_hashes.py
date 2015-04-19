#(c) Adam Pridgen adam.pridgen@thecoverofnight.com
# GPL v3
start = AskAddr(0xFFFFFFFF, "Enter start address.")
end = AskAddr(0xFFFFFFFF, "Enter end address.")

if start >= end:
  print "Please enter a valid start and end address start: 0x%08x end: 0x%08x."%(start,end)

hoffset = 4
ipoffset = 10
criteria = {}
while start < end:
  hash = GetString(start,-1,0)
  print hex(start),hash
  base = 0
  if (len(hash) + 1)%4 != 0:
    base = 4 - (len(hash) + 1)%4 
  incr = len(hash) + 1 + base
  ip = GetString(start+incr,-1,0)
  print hex(start+incr-1),ip
  base = 0
  if (len(ip) + 1)%4 != 0:
    base = 4 - (len(ip) + 1)%4 
  start += incr + len(ip) + 1 + base
  criteria[ip] = hash

f = open("C:\\hash_ip_waladec.txt",'w')
for ip in criteria:
  f.write(criteria[ip]+" "+ip+"\n")
f.close()
