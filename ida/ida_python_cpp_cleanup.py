start = 0x04EA8A4
end = 0x4EAFF8

if start == 0xFFFFFFF or\
	end == 0xFFFFFFF or\
	start == end:
	print "Please enter a valid address for start and end!"

def get_alignment(length, align = 4):
	if (length % align) == 0:
		return 0
	return align - (length % align) 

def get_end_addr_and_type_desc(ea, end):
	desc_str = ""
	while ea < end:
		incr = 0
		if Dword(ea) == 0x0:
			tea = ea+4
			if not GetString(tea, -1, 0) is None and len(GetString(tea, -1, 0)) > 0:
				print "Found String @ x%x: %s"%(tea, GetString(tea, -1, 0))
				desc_str = GetString(tea, -1, 0)
				incr = len(desc_str) +1 + get_alignment(len(desc_str)+1)
				ea = incr + tea
				if isValidTypeDesc(desc_str):
					break
		ea += 4
	return ea, desc_str
			
def isValidTypeDesc(name):
	return name.find(".?") == 0 or name.find("?$") > 0

def remove_3ats_portion(name):
	if name.find("@@@") > 0:
		return name.split("@@@")[0]
	return name

def get_last_occur_2ats(name):
	if name.find("@@") > 0:
		return name.strip().split("@@")[-2].split("@")[-1]
	elif name.find("@") > 0:
		return name.strip().split("@")[-1]
	return name

def ApproxNamespace_ClassName(desc_name):
	name = desc_name.replace(".?","")
	if name[0:3] == "AVC": 
		name = name[3:]
	elif name[0:4] == "AVTi":
		name = name[4:]
	elif name[0:2] == "AU" or name[0:2] == "AV":
		name = name[2:]
	name_space = get_last_occur_2ats(name)
	if name.find("?$") > 1:
		name = "?$".join(name.split("?$")[1:])
	name = remove_3ats_portion(name)
	#print "Found Namespace: %s"%name_space
	if name.find("@") == -1:
		return name_space, name_space
	name_space = name_space.split("@")[-1]
	class_name = name.split("@")[0]
	#print "Using Class Name: %s"%class_name
	if class_name.find("?$") == 0:
		class_name = class_name[2:]
	return name_space, class_name.replace("?$", "_")

def names_types_desc_classes_from_info(addr_vftable):
	pass


def create_class_name(name):
	ns, cn = ApproxNamespace_ClassName(name)
	name = "ClassTD_"
	name += ns.upper()
	if ns != cn:
		name+= "_"+cn
	return name
		
def name_class_type_desc(ea, name):
	n = create_class_name(name)
	return MakeName(ea, n)

ea = start
while ea <= end:
	print "Getting Type Descriptor Info for Class @ x%x"%ea
	addr, type_str = get_end_addr_and_type_desc(ea, end)
	if not type_str is None and len(type_str) > 0:
		name = create_class_name(type_str)
		#print "Created Name: %s"%name
		#if name_class_type_desc(ea, type_str):
		print "Successfully named the reference: x%x %s"%(ea, name) 
	#print "Found Class Descriptor for name: %s runing from: x%x to: x%x"%(type_str, ea, addr)
	if ea == addr:
		ea += 4
	else:
		ea = addr
