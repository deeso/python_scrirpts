# (c) Adam Pridgen <adam.pridgen@thecoverofnight.com>
# collection of ida functions created as i learn ida
# 


import idc
import idaapi
import idautils

def reverse_map(dict_):
    rdict_ = {}
    for k,v in dict_.items():
        rdict_[v] = k
    return rdict_

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
    '''
    searches for all names in the addr range
    returns a mapping (dict) addr --> name
    '''
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
    '''
    include all names in the filter in the result
    returns a mapping (dict) addr --> name
    '''
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
    '''
    exclude all names in the filter in the result
    returns a mapping (dict) addr --> name
    '''
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
    '''
    search all segments in IDA for named items
    returns a mapping (dict) addr --> name
    '''

    
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
    name = idc.SegName(addr)
    if not name is None:
        return name+":%08x"%addr
    return idc.BADADDR

def find_first_instr(addr,instr):
    caddr = addr
    # should break us out of a loop, but atm we will
    # just break and return
    seen_addrs = set()
    while caddr != idc.BADADDR and not caddr in seen_addrs:
        seen_addrs.add(caddr)
        disasm = idc.GetDisasm(caddr)
        if disasm is None:
            return None
        if disasm.find(instr) > -1:
            return caddr
        caddr = idc.RfirstB(caddr)
    return None
