# (c) Adam Pridgen adam@praetoriangrp.com adam.pridgen@thecoverofnight.com
# idaBatchAnalyze.py - 
#		Duplicate a directory tree
#		Analyze all Windows EXE, DRV, DLL, ... files
#		Rename the file to File_exe.idb and removes File.idb
#		Recursively analyses these files and removes all others.
#		
# usage: idaBatchAnalyze.py <src_dir> <dest_dir> <idapath> <analysis_script_name>
#

import shutil, sys, os, stat
from subprocess import *
#idaBatchAnalyze.py "C:\Program Files (x86)\Intuit" "C:\analysis\Intuit" "C:\Program Files (x86)\IDA\idag.exe" C:\analysis\analysis_script.py

#idaBatchAnalyze.py "C:\Users\apridgen\Desktop\ICA_Client" "C:\analysis\ICA_Client" "C:\Program Files (x86)\IDA\idag.exe" C:\analysis\analysis_script.py
SCRIPT = '''
import shutil, sys, os
def batch_analyze_function():
	base_output = "%s"
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
'''
def enableWritePerms(path):
	os.chmod(path, stat.S_IWRITE)
	for i in os.listdir(path):
		f = os.path.join(path, i)
		if os.path.isfile(f):
			os.chmod(f, stat.S_IWRITE)
		else:
			enableWritePerms(f)
	
def write_dynamic_script(fname, *args):
	global SCRIPT
	print "Generating script %s."%fname
	a = tuple([i.replace("\\","\\\\") for i in args])
	print "\t\t arguments: %s"%str(a)
	script = SCRIPT%a
	#print "Filename: %s"%fname
	#print script
	f = open(fname, "w")
	f.write(script)
	f.close()
	
	
def run_cmd(cmd_list):
	x = Popen(cmd_list, stdout=PIPE)
	return x.stdout.read()
def clone_tree(src, dest):
	shutil.copytree(src, dest)

def perform_ida_analysis(ida_path, analysis_script, filename):
	cmd_str = ['"%s"'%ida_path, 
				'-A',
				'-OIDAPython:"%s"'%analysis_script, 
				'"%s"'%filename
				]
	#print "Calling the following command: %s"%(" ".join(cmd_str))
	print "Performing analysis on: %s"%(filename)
	return run_cmd(" ".join(cmd_str))

def perform_analysis(ida, analysis_script_name, dir):
	basedir = dir
	subdirlist = []
	print "Entered %s"%(dir)
	write_dynamic_script(analysis_script_name, basedir)
	#print os.listdir(basedir)
	for i in os.listdir(basedir):
		if os.path.isfile(os.path.join(basedir, i)):
			if i[-4:].lower() == ".cat" or i[-4:].lower() == ".drv" or i[-4:].lower() == ".sys" or i[-4:].lower() == ".dll" or i[-4:].lower() == ".exe":
				print "Found: %s"%(os.path.join(basedir, i))
				perform_ida_analysis(ida, analysis_script_name, os.path.join(basedir, i))
				# remove the idb file after analysis
				print "Removing: %s"%os.path.join(basedir, i[:-4]+".idb")
				x = os.path.join(basedir, i[:-4]+".idb")
				if os.path.exists(x):
					os.remove(x)
			elif i[-4:].lower() == ".idb":
				continue
			else:
				os.remove(os.path.join(basedir, i))
		else:
			subdirlist.append(os.path.join(basedir, i))

	os.remove(analysis_script_name)	
	for fq_path in subdirlist:
		perform_analysis(ida, analysis_script_name, fq_path)

usage = "idaBatchAnalyze.py <src_dir> <dest_dir> <idapath> <analysis_script>"
if __name__ == "__main__":
	if len(sys.argv) != 5:
		print usage
	src_dir = sys.argv[1]
	dest_dir = sys.argv[2]
	ida = sys.argv[3]
	script = sys.argv[4]
	print "Cloning Directory:\n\tFrom: %s\n\tTo: %s"%(src_dir, dest_dir)
	print "\n"
	print "IDA Executable: %s"%ida
	print "Dynamic Script Name Used for Analysis: %s"%script
	clone_tree(src_dir, dest_dir)
	print "Finished cloning.."
	#print "Setting Write Perms in the Directory"
	#enableWritePerms(dest_dir)
	#print "Done Setting Perms"
	print "Beginning Recursive Analysis."
	perform_analysis(ida, script, dest_dir)
	print "Completed Recursive Batch Analysis"
