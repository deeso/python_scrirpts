MN_FLAGS = SN_NOWARN|SN_AUTO
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
	st_name, func_named = process_sym(sym_addr, strtab, symtab)
	
	MakeNameEx(c_addr, "Rel_"+st_name, MN_FLAGS)
	reloc_addr = Dword(c_addr+r_offset)
	e = [i for i in DataRefsTo(reloc_addr)]
	if len(e) != 0:
		ref = e[0]
		func_start = FirstFuncFchunk(ref)
		if func_named:
			MakeNameEx(func_start, "plt_jmp_"+st_name, MN_FLAGS)
		else:
			MakeNameEx(func_start, st_name, MN_FLAGS)
	MakeNameEx(reloc_addr, "__"+st_name, MN_FLAGS)

dt_strtab = LocByName("DT_STRTAB")
dt_symtab = LocByName("DT_SYMTAB")


reloc = AskAddr(0xFFFFFFFF, "Enter start address of the relocations.")

dyn_id = GetStrucIdByName(elf_structs["Dyn"])
d_tag = GetMemberOffset(dyn_id, "d_tag")
d_un = GetMemberOffset(dyn_id, "d_un")
dyn_sz = GetStrucSize(dyn_id)

process_reloc(reloc, Dword(d_un+dt_strtab), Dword(d_un+dt_symtab))
process_reloc(reloc, Dword(d_un+dt_strtab), Dword(d_un+dt_symtab))