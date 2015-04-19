# (c) 2010 Adam Pridgen adam@praetoriangrp.com, adam.pridgen@thecoverofnight.com
# ida_pro_name_runtime_imports.py:
#		Rename references to runtime imports in a given function

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

start = AskAddr(ScreenEA(), "Enter start address.")
end = NextFchunk(ScreenEA())
addr = start

while addr < end:
	dis_asm = GetDisasm(addr)
	print "Disassembled: 0x%x %s"%(addr, dis_asm)
	if dis_asm.find("push") == -1 or dis_asm.find("offset") == -1:
		addr = NextHead(addr, NextFchunk(addr))
		continue
	data_list = [i for i in DataRefsFrom(addr)]
	if len(data_list) == 0:
		addr = NextHead(addr, NextFchunk(addr))
		continue
	string = GetString(data_list[0],-1,0)
	if string.lower().find("dll") != -1 or string == "":
		addr = NextHead(addr, NextFchunk(addr))
		continue
	print "Found String Data XRef From: 0x%x %s"%(addr, string)
	while addr < end:
		addr = NextHead(addr, NextFchunk(addr))
		dis_asm = GetDisasm(addr)
		print "Disassembled: 0x%x %s"%(addr, dis_asm)
		if dis_asm.find("mov") == -1 or dis_asm.find("eax") == -1:
			addr = NextHead(addr, NextFchunk(addr))
			continue
		data_list2 = [i for i in DataRefsFrom(addr)]
		if len(data_list2) == 0:
			NextHead(addr, NextFchunk(addr))
			continue
		print "Found Data XRef From: 0x%x"%(addr)
		MakeName(data_list2[0],"")
		MakeNameEx(data_list2[0], "_"+string, 0x0)
		break
	addr = NextHead(addr, NextFchunk(addr))
print "Finished"