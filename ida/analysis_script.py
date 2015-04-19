
import shutil, sys, os
def batch_analyze_function():
	base_output = "C:\\analysis\\ICA_Client\\cpviewer.id0"
	ida_file = GetInputFilePath()
	new_base_fname = os.path.split(ida_file)[1]
	new_base_fname = new_base_fname.replace(".","_")
	new_file = os.path.join(base_output, new_base_fname)
	new_file = new_file+".idb"
	x = SegStart(BeginEA())
	y = SegEnd(BeginEA())
	Wait()
	AnalyseArea(x,y)
	Wait()
	SaveBase(new_file)
	Wait()
	Exit(0)
	
batch_analyze_function()
