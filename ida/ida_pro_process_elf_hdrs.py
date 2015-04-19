# (c) 2010 Adam Pridgen adam@praetoriangrp.com, adam.pridgen@thecoverofnight.com
# ida_pro_process_elf_hdrs.py:
# 		process elf headers and synchronize symbol names, relocations, and manes in the 
#		program linkage jump table.
#
#		1) Load ELF C-header file
#		2) Move ScreenEA() to the begining of the file
#		3) Run the script

# GPLv3 License
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import sys
import idaapi

MN_FLAGS = SN_NOCHECK|SN_NOWARN|SN_AUTO
PT_TYPES = {
0:"PT_NULL",
1:"PT_LOAD",
2:"PT_DYNAMIC",
3:"PT_INTERP",
4:"PT_NOTE",
5:"PT_SHLIB",
6:"PT_PHDR",
0x70000000:"PT_LOPROC",
0x7fffffff:"PT_HIPROC"}



elf32_structs = {"Ehdr":"Elf32_Ehdr", 
				"Phdr":"Elf32_Phdr",
				"Dyn":"Elf32_Dyn",
				"Rel":"Elf32_Rel",
				"Sym":"Elf32_Sym"}
				
elf64_structs = {}
elf = {"elf32":elf32_structs, "elf64":elf64_structs}

elf_structs = elf["elf32"]


def get_data_string(addr, max_length=0xFFFFFFFF):
	chunk = ""
	pos = 0
	while addr+pos < addr+max_length:
		byte = IdbByte(addr+pos)
		if chr(byte) == '\x00':
			return chunk
		chunk += chr(byte)
		pos += 1
	return chunk


	
def get_align(length, align):
	if length%align == 0: 
		return 0
	return (align - length%align)%align
	
def process_ehdr(base_addr):
	global elf_structs
	ehdr_id = GetStrucIdByName(elf_structs["Ehdr"])
	sz =  GetStrucSize(ehdr_id)
	MakeUnknown(base_addr, sz, DOUNK_DELNAMES)
	c = MakeStructEx(file_start, -1, elf_structs["Ehdr"])
	MakeNameEx(file_start, "ELF_Header", MN_FLAGS)
	return ehdr_id

def process_phdrs(phdr_start, phdr_cnt):
	global elf_structs
	# get the phoff and phnum
	phdr_id = GetStrucIdByName(elf_structs["Phdr"])
	p_type = GetMemberOffset(phdr_id, "p_type")
	p_vaddr = GetMemberOffset(phdr_id, "p_vaddr")
	p_filesz = GetMemberOffset(phdr_id, "p_filesz")
	p_memsz = GetMemberOffset(phdr_id, "p_memsz")
	phdr_sz = GetStrucSize(phdr_id)
	c_addr = phdr_start
	cnt = 0
	while cnt < phdr_cnt:
		MakeUnknown(c_addr, phdr_sz, DOUNK_DELNAMES) 
		c = MakeStructEx(c_addr, -1, elf_structs["Phdr"])
		if not c:
			cnt += 1
			continue
		typ = ""
		if Dword(c_addr+p_type) in PT_TYPES:
			typ = PT_TYPES[Dword(c_addr+p_type)]
		if typ == "PT_DYNAMIC":
			print "Found a Dynamic Section: 0x%08x size: %d bytes"%(Dword(c_addr+p_vaddr), Dword(c_addr+p_memsz))
			process_dynamic(Dword(c_addr+p_vaddr), Dword(c_addr+p_memsz))
		elif typ == "PT_INTERP":
			interp_string_addr = Dword(p_vaddr+c_addr)
			print "Found the Interpreter Section: 0x%08x Interpreter: %s"%(Dword(c_addr+p_vaddr), get_data_string(interp_string_addr))
			#print hex(interp_string_addr), hex(len(get_data_string(interp_string_addr))), get_data_string(interp_string_addr)
			MakeStr(Dword(c_addr+p_vaddr), Dword(c_addr+p_vaddr)+len(get_data_string(interp_string_addr))+1)
		else:
			print "Found the %s Section: 0x%08x"%(typ, Dword(c_addr+p_vaddr))
		MakeNameEx(c_addr, "ELF_Phdr_%d_%s"%(cnt,typ), MN_FLAGS)
		c_addr += phdr_sz 
		cnt += 1
DT_TYPES = {0:"DT_NULL",
1:"DT_NEEDED",
2:"DT_PLTRELSZ",
3:"DT_PLTGOT",
4:"DT_HASH",
5:"DT_STRTAB",
6:"DT_SYMTAB",
7:"DT_RELA",
8:"DT_RELASZ",
9:"DT_RELAENT",
10:"DT_STRSZ",
11:"DT_SYMENT",
12:"DT_INIT",
13:"DT_FINI",
14:"DT_SONAME",
15:"DT_RPATH",
16:"DT_SYMBOLIC",
17:"DT_REL",
18:"DT_RELSZ",
19:"DT_RELENT",
20:"DT_PLTREL",
21:"DT_DEBUG",
22:"DT_TEXTREL",
23:"DT_JMPREL",
0x70000000:"DT_LOPROC",
0x7fffffff:"DT_HIPROC"
}

R_TYPES = {0:"NONE",
1:"32",
2:"PC32",
3:"GOT32",
4:"PLT32",
5:"COPY",
6:"GLOB_DAT",
7:"JMP_SLOT",
8:"RELATIVE",
9:"GOTOFF",
10:"GOTPC",
}

SYM_TYPES = {0:"STT_NOTYPE",
1:"STT_OBJECT",
2:"STT_FUNC",
3:"STT_SECTION",
4:"STT_FILE",
13:"STT_LOPROC",
15:"STT_HIPROC",
}


def process_sym(sym_addr, strtab):
	global elf_structs
	r_break_down = lambda x: ((x & 0xff00) >> 8, (x & 0xff)) # sym, type
	s_break_down = lambda x: ((x & 0xf0) >> 4, (x & 0x0f)) # bind, type
	
	sym_id = GetStrucIdByName(elf_structs["Sym"])
	sym_name = GetMemberOffset(sym_id, "st_name")
	sym_value = GetMemberOffset(sym_id, "st_value")
	sym_info = GetMemberOffset(sym_id, "st_info")
	sym_sz = GetStrucSize(sym_id)
	
	MakeUnknown(sym_addr, sym_sz, DOUNK_DELNAMES) 
	MakeStructEx(sym_addr, -1, elf_structs["Sym"])
	
	st_name = ""
	idx = Dword(sym_addr+sym_name)
	if idx != 0:
		st_name = GetString(strtab+idx, -1, 0)
	
	MakeNameEx(sym_addr, "Sym_"+st_name, MN_FLAGS)
	b,t = s_break_down(Byte(sym_addr+sym_info))
	faddr = Dword(sym_addr+sym_value)
	if t == 2 and faddr != 0:
		# name the function
		MakeNameEx(faddr, st_name, MN_FLAGS)
		MakeFunction(faddr, BADADDR)
		return st_name, True
	return st_name, False
	
def process_reloc(rel_addr, strtab, symtab):
	global elf_structs
	r_break_down = lambda x: ((x & 0xff00) >> 8, (x & 0xff)) # sym, type
	
	c_addr = rel_addr
	rel_id = GetStrucIdByName(elf_structs["Rel"])
	r_offset = GetMemberOffset(rel_id, "r_offset")
	r_info = GetMemberOffset(rel_id, "r_info")
	relsz = GetStrucSize(rel_id)
	
	sym_id = GetStrucIdByName(elf_structs["Sym"])
	sym_name = GetMemberOffset(sym_id, "st_name")
	sym_sz = GetStrucSize(sym_id)
	
	MakeUnknown(c_addr, relsz, DOUNK_DELNAMES) 
	MakeStructEx(c_addr, -1, elf_structs["Rel"])
	sym, typ = r_break_down(Dword(c_addr + r_info))
	sym_addr = sym*sym_sz + symtab
	st_name, func_named = process_sym(sym_addr, strtab)
	
	MakeNameEx(c_addr, "Rel_"+st_name, MN_FLAGS)
	reloc_addr = Dword(c_addr+r_offset)
	e = [i for i in DataRefsTo(reloc_addr)]
	if len(e) != 0:
		ref = e[0]
		func_start = FirstFuncFchunk(ref)
		cname = Name(func_start)
		if func_named and cname == "":
			MakeNameEx(func_start, "plt_jmp_"+st_name, MN_FLAGS)
		else:
			MakeNameEx(func_start, st_name, MN_FLAGS)
	MakeNameEx(reloc_addr, "__"+st_name, MN_FLAGS)

def process_rel(rel_addr, rel_sz, strtab, symtab):
	global elf_structs
	r_break_down = lambda x: ((x & 0xff00) >> 8, (x & 0xff)) # sym, type
	
	c_addr = rel_addr
	rel_id = GetStrucIdByName(elf_structs["Rel"])
	r_offset = GetMemberOffset(rel_id, "r_offset")
	r_info = GetMemberOffset(rel_id, "r_info")
	relsz = GetStrucSize(rel_id)
	
	sym_id = GetStrucIdByName(elf_structs["Sym"])
	sym_name = GetMemberOffset(sym_id, "st_name")
	sym_sz = GetStrucSize(sym_id)
	
	while c_addr < rel_sz + rel_addr:
		process_reloc(c_addr, strtab, symtab)
		c_addr += relsz


def process_dynamic(dyn_addr, dyn_size):
	global elf_structs
	c_addr = dyn_addr
	dyn_id = GetStrucIdByName(elf_structs["Dyn"])
	d_tag = GetMemberOffset(dyn_id, "d_tag")
	d_un = GetMemberOffset(dyn_id, "d_un")
	dyn_sz = GetStrucSize(dyn_id)
	DT_VALUES = {}

	needed = []
	print "Processing the Dynamic Section, Addr: x%08x Size: x%08x"%(dyn_addr, dyn_sz)
	while c_addr < dyn_addr + dyn_size:
		MakeUnknown(c_addr, dyn_sz, DOUNK_DELNAMES) 
		c = MakeStructEx(c_addr, -1, elf_structs["Dyn"])
		tag = Dword(c_addr + d_tag)
		val = Dword(c_addr + d_un)
		if not tag in DT_TYPES:
			c_addr += dyn_sz
			continue
		if tag == 0:
			break
		if tag == 1:
			needed.append((c_addr, tag, val))
			c_addr += dyn_sz
			continue
		MakeNameEx(c_addr, DT_TYPES[tag], MN_FLAGS)
		print "Added: %s %s"%(DT_TYPES[tag], str((hex(c_addr), hex(tag), hex(val))))
		DT_VALUES[DT_TYPES[tag]] = (c_addr, tag, val)
		c_addr += dyn_sz
	
	# start with string table
	if "DT_STRTAB" in DT_VALUES and\
		"DT_STRSZ" in DT_VALUES:
		str_addr = DT_VALUES["DT_STRTAB"][2]
		str_sz = DT_VALUES["DT_STRSZ"][2]
		MakeNameEx(str_addr, "STRTAB", MN_FLAGS)
		process_strtab(str_addr, str_sz)
	
	if "DT_RELSZ" in DT_VALUES and\
		"DT_REL" in DT_VALUES and\
		"DT_STRTAB" in DT_VALUES and\
		"DT_SYMTAB" in DT_VALUES:
		
		symtab = DT_VALUES["DT_SYMTAB"][2]
		strtab = DT_VALUES["DT_STRTAB"][2]
		
		rel_addr = DT_VALUES["DT_REL"][2]
		rel_sz = DT_VALUES["DT_RELSZ"][2]
		MakeNameEx(rel_addr, "Relocations", MN_FLAGS)
		process_rel(rel_addr, rel_sz, strtab, symtab)
	

	if "DT_PLTRELSZ" in DT_VALUES and\
		"DT_JMPREL" in DT_VALUES and\
		"DT_STRTAB" in DT_VALUES and\
		"DT_SYMTAB" in DT_VALUES:
		# should check "DT_PLTREL" in DT_VALUES to see
		# relocation type, oh well
		symtab = DT_VALUES["DT_SYMTAB"][2]
		strtab = DT_VALUES["DT_STRTAB"][2]
		
		rel_addr = DT_VALUES["DT_JMPREL"][2]
		rel_sz = DT_VALUES["DT_PLTRELSZ"][2]
		MakeNameEx(rel_addr, "JMPPLT_Relocations", MN_FLAGS)
		process_rel(rel_addr, rel_sz, strtab, symtab)
		
	if "DT_FINI" in DT_VALUES:
		MakeCode(DT_VALUES["DT_INIT"][2])
		MakeNameEx(DT_VALUES["DT_FINI"][2], ".fini", MN_FLAGS)
	if "DT_INIT" in DT_VALUES:
		MakeCode(DT_VALUES["DT_INIT"][2])
		MakeNameEx(DT_VALUES["DT_INIT"][2], ".init", MN_FLAGS)
	if "DT_HASH" in DT_VALUES:
		hash_table = DT_VALUES["DT_HASH"][2]
		nbucket = Dword(hash_table)
		nchain = Dword(hash_table+4)
		MakeNameEx(hash_table, "Elf_Hash_Table", MN_FLAGS)
		addr = hash_table
		end = hash_table + nchain*4 + nbucket*4 + 8
		print "DT_HASH: %u bytes in size"%(nchain*4 + nbucket*4 + 8)
		while addr < end:
			MakeDword(addr)
			addr+=4
		
	if len(needed) > 0:
		str_addr = DT_VALUES["DT_STRTAB"][2]
		for addr, tag, idx in needed:
			name = GetString(str_addr+idx, -1, 0)
			MakeComm(addr, "Needs: %s"%name)
			MakeNameEx(addr, "Needed_%s"%name, MN_FLAGS)
			
def process_strtab(str_addr, str_sz):
	c_addr = str_addr
	MakeUnknown(str_addr, str_sz, DOUNK_DELNAMES) 
	while c_addr < str_sz+str_addr:
		string = get_data_string(c_addr, str_sz+str_addr)
		if len(string) == 0:
			#MakeAlign(c_addr, 4, 0)
			c_addr += 1
			continue
		MakeStr(c_addr, c_addr+len(string)+1)
		#a = get_align(len(string)+1, 4)
		#MakeAlign(c_addr+len(string)+1, a, 0)
		#c_addr += a+len(string)+1
		c_addr += len(string)+1

#elf_file = AskString("C:\\code\\elf.h", "Enter path to the ELF header file.")
start = AskAddr(idaapi.get_imagebase(), "Enter start address of the file.")
if start == 0xFFFFFFFF:
	print "Error, bad address."
	exit(-1)

# elf header structure
file_start = start
print "Processing Ehdr", hex(file_start)
ehdr_id = process_ehdr(file_start)

# phdr structure
phdr_off = Dword(file_start+GetMemberOffset(ehdr_id, "e_phoff"))
phdr_num = Word(file_start+GetMemberOffset(ehdr_id, "e_phnum"))
process_phdrs(file_start+phdr_off, phdr_num)


	

