
import idautils
import idc

'''
api usage:
addrs_names_d = get_all_names()
flow_infoz = {}
for addr in addrs_names_d:
    name = addrs_names_d[addr]
    flow_infoz[name] = get_flow_to_name(name)

'''


def merge(d1,d2):
	df = {}
	if len(d2) == 0:
		return d1
	elif len(d1) == 0:
		return d2
	for i in d1:
		df[i] = d1[i]
	for i in d2:
		df[i] = d2[i]
	return df
	
def get_names(start, end):
	names = {}
	for addr in xrange(start, end):
		name = idc.Name(addr)
		if name != "":
			names[addr] = name
	return names

def get_all_segments():
	segments = []
	seg = idc.FirstSeg()
	while seg != idc.BADADDR:
		segments.append((seg, idc.SegEnd(seg)))
		seg = idc.NextSeg(seg)
	return segments
auto_names = set(['sub','loc','unk','dword','qword','byte','word','off',])

def filter_inclusive_names(names, filter=[]):
	notfilered_names = {}
	if isinstance(filter, str):
		filter = [filter,]
	
	for i in names:
		if len(names[i]) == 0:
			continue
		name = names[i]
		filter_this = True
		for f in filter:
			if name.find(f) > -1:
				filter_this = False
				break
		if not filter_this:
			notfilered_names[i] = names[i]
	return notfilered_names
	
def filter_exclusive_names(names, filter=[]):
	notfilered_names = {}
	if isinstance(filter, str):
		filter = [filter,]
	
	for i in names:
		if len(names[i]) == 0:
			continue
		name = names[i]
		filter_this = False
		for f in filter:
			if name.find(f) > -1:
				filter_this = True
				break
			
		if not filter_this:
			notfilered_names[i] = names[i]
	return notfilered_names
	
def get_all_names():
	names = {}
	segments = get_all_segments()
	for i in segments:
		t = get_names(*i)
		names = merge(names, t)
	return names

get_name_to_name = lambda x: x.strip().split('#')[1].strip()
get_addr_to_addr = lambda x: x.strip().split('#')[0].strip()

def get_name(addr):
	'''
    trys to get the named value by function and offset
    other wise return %segment%:addr
    '''

	name = idc.GetFuncOffset(addr)
	if not name is None:
		return name
    name = idc.SegName(name)
    if not name is None:
        return name+"%08x"%addr
    return idc.BADADDR

get_import_flow_information = lambda x: [ '%s ==> %s'%(idc.GetFuncOffset(xref.frm), idc.Name(xref.to), ) for xref in idautils.XrefsTo(LocByName(x)) if xref.iscode]
get_name_flow_info = lambda x: [ '0x%08x ==> 0x%08x # %s ==> %s  '%(xref.frm, xref.to, get_name(xref.frm), idc.Name(xref.to) ) for xref in idautils.XrefsTo(idc.LocByName(x)) if xref.iscode]
get_addr_flow_info = lambda x: [ '0x%08x ==> 0x%08x # %s ==> %s  '%(xref.frm, xref.to, get_name(xref.frm), idc.Name(xref.to) ) for xref in idautils.XrefsTo(x) if xref.iscode]
idx = 0
def get_flow_to_name(name):
	global idx
	mflow_addrs = []
	mflow_names = []
	print "In call %x Name: %s"%(idx,name)
	idx+=1
	for flow in get_name_flow_info(name):
		print flow
		a2a = get_addr_to_addr(flow)
		n2n = get_name_to_name(flow)
		src = a2a.split()[0].strip()
		# arrows at 1
		dst = a2a.split()[2].strip()
		sname = idc.GetFunctionName(int(src,16))
		print "Obtaining flow information for: ", sname
		flow_addrs, flow_names = get_flow_to_name(sname)
		print "Obatained the following flow info for %s: %s"%(sname,str(flow_names))
		if len(flow_addrs) == 0:
			mflow_addrs.append(a2a)
		if len(flow_names) == 0:
			mflow_names.append(n2n)
		for i in flow_addrs:
			mflow_addrs.append(i + " ==> " + a2a)
		for i in flow_names:
			mflow_names.append(i + " ==> " + n2n)
	idx -= 1
	return [i for i in set(mflow_addrs)], [i for i in set(mflow_names)]
	
def merge_flows(flows):
	flows.sort()
	pruned_flows = set()
	for flow in flows:
		if not flow in pruned_flows:
			cnt = 0
			found = False
			pflows = list(pruned_flows)
			while cnt < len(pflows):
				f = pflows[cnt]
				if len(flow) < len(f) and f.find(flow):
					found = True
					break
				elif  len(f) < len(flow) and flow.find(f):
					found = True
					break
				elif f == flow: 
					found = True
					break
				cnt += 1
			if not found:
				pruned_flows.add(flow)
	return list(pruned_flows)
		