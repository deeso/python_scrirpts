import idaapi
addr =  AskAddr(0xFFFFFFFF, "Enter start address of the Symbols.")
MARKED_FUNC_COLOR = 0xffd7d7
MARKED_ITEM_COLOR = 0xffd6a9

c_addr = idaapi.get_func(addr).startEA
print "Current Address: 0x%08x"%c_addr

funcs = {}

while c_addr != BADADDR:
	xb = idaapi.xrefblk_t()
	print "Current Address: 0x%08x"%c_addr
	ok = xb.first_to(c_addr,idaapi.XREF_ALL)
	if ok and c_addr != xb.frm:
		t = xb.frm
		if idaapi.get_func(t):
			f = idaapi.get_func(t)
			if not f.startEA in funcs:
				funs[f.startEA] = f
			c_addr = t
			set_item_color(c_addr)
			
		else:
			break
	else:
		break
	print "New Address: 0x%08x"%c_addr
	
	while ok and xb.iscode:
		print str(xb.type)
		ok = xb.next_from()

g = [idc.SetColor(f.startEA, CIC_FUNC, MARKED_FUNC_COLOR) for f in funcs]
Jump(c_addr)