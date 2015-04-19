import idaapi
import idc


def track_register_value(reg_name, start_ea, end_ea=BADADDR):
	bread_crumbs = {}
	fn = idaapi.get_func(ea)
	curr = start_ea
	curr_loc = reg_name
	prev_loc = None
	while start_ea != end_ea:
		# track assignment, moves, loads, modifications
		# get basic block addr and instruction
		# parse the basic block in the instruction
		print GetDisasm(ea)
		if GetDisasm(ea).find(reg_name) == -1:
			continue
		# print the addr, reg, operation
		# add addr and instructions into the bread_crumbs
		# set prev to current
		# assign current, and return to beginning of the loop
		pass
	return bread_crumbs
	
def track_register_value(reg_name, start_ea, end_ea=BADADDR):
	bread_crumbs = {}
	fn = idaapi.get_func(ea)
	curr = start_ea
	curr_loc = reg_name
	prev_loc = None
	while curr != idaapi.BADADDR:
		if curr != end_ea:
		  xb = idaapi.xrefblk_t()
		  ok = xb.first_to(curr, idaapi.XREF_ALL)
		  while ok and xb.iscode:
			if xb.type in [idaapi.fl_JF, idaapi.fl_JN]:
			  done = True
			  break
			ok = xb.next_to()

		if done: break
		mark_ea(curr)
		
		next = idaapi.BADADDR
		xb = idaapi.xrefblk_t()
		ok = xb.first_from(curr, idaapi.XREF_ALL)
		while ok and xb.iscode:
		  if xb.type in [idaapi.fl_JF, idaapi.fl_JN]:
			done = True
			break
		  elif xb.type == idaapi.fl_F:
			next = xb.to
		  ok = xb.next_from()

		if done: break
		curr = next	
		#while start_ea != end_ea:
		# track assignment, moves, loads, modifications
		# get basic block addr and instruction
		# parse the basic block in the instruction
		# print the addr, reg, operation
		# add addr and instructions into the bread_crumbs
		# set prev to current
		# assign current, and return to beginning of the loop
		# pass
		# return bread_crumbs
