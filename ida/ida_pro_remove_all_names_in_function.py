# (c) 2010 Adam Pridgen adam@praetoriangrp.com, adam.pridgen@thecoverofnight.com
# ida_pro_remove_all_names_in_function.py:
#		Remove all Data reference names in function

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

start = ScreenEA()
end = NextFchunk(ScreenEA())
addr = start
while addr < end:
	dis_asm = GetDisasm(addr)
	print "Disassembled: 0x%x %s"%(addr, dis_asm)
	data_list = [i for i in DataRefsFrom(addr)]
	if len(data_list) == 0:
		addr = NextHead(addr, NextFchunk(addr))
		continue
	MakeName(data_list[0],"")
	addr = NextHead(addr, NextFchunk(addr))
print "Finished"