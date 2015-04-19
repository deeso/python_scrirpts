# (c) 2010 Adam Pridgen 
# ida_pro_make_data_ref_name_cmd.py:
# 

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

import idaapi
import idc
import sys

def get_info():
	addr = idc.AskAddr(idc.ScreenEA(), "Enter start address.")
	comment = idc.AskStr("","Enter comment to add after the bp, if any.")
	outfilename = idc.AskStr("","Output file name.")
	command = idc.AskStr("","Vtrace command to use?.")
	return addr,comment,command,outfilename

def get_write_bps_to_file(addr, comments, command="", outfilename=""):
	bp_str_fmt = "bp 0x%08x # %s"
	if command != "":
		bp_str_fmt = 'bp -c "%s" '%(command)+" 0x%08x # %s"
	bp_str_cmt_fmt = " Bp corresponds to Name: %s in function+offset: %s @ 0x%08x %s"+comments
	name = Name(addr)
	outfile = sys.stdout
	if outfilename != "":
		outfile = open(outfilename, 'a')
	bp_addr = idaapi.get_first_cref_to(addr)
	bp_lines = []
	while (bp_addr != idc.BADADDR):
		bp_cmt = bp_str_cmt_fmt%(name, GetFuncOffset(bp_addr), bp_addr, GetDiasm(bp_addr))
		bp_str = bp_str_fmt%(bp_addr, bp_cmt)
		bp_lines.append(bp_str+"\n")
		outfile.write(bp_str+"\n")
		bp_addr = idaapi.get_next_cref_to(addr, bp_addr)
	bp_addr = idaapi.get_first_cref_to(addr)
	while (bp_addr != idc.BADADDR):
		bp_cmt = bp_str_cmt_fmt%(name, GetFuncOffset(bp_addr), bp_addr)
		bp_str = bp_str_fmt%(bp_addr, bp_cmt)
		bp_lines.append(bp_str+"\n")
		outfile.write(bp_str+"\n")
		bp_addr = idaapi.get_next_cref_to(addr, bp_addr)
	return bp_lines


if __name__ == "__main__":
	addr,comment,command,outfilename = get_info()
	get_write_bps_to_file(addr,comment,command,outfilename)