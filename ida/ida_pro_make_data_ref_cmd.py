# (c) 2010 Adam Pridgen adam@praetorian.com, adam.pridgen@thecoverofnight.com
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
def get_info():
	addr = idc.AskAddr(idc.ScreenEA(), "Enter start address.")
	name = idc.AskStr("","Enter name.")
	return addr,name

def make_data_ref_name(addr, name):
	if name!= "" and idc.Dfirst(addr) != idc.BADADDR:
		idc.MakeName(idc.Dfirst(addr), name)

if __name__ == "__main__":
	make_data_ref_name(*(get_info()))