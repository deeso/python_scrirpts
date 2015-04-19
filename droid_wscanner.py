#
#  Author: Adam Pridgen <adam@praetoriangrp.com>
#  (C) 2010 praetorian group 
#  droid_wscanner.py - wireless scanner using the andoid phone

import android, sys, threading, traceback, time
from optparse import OptionParser

FEED_BACK = True
KEEP_POLLING = True
POLL_TIME = 1.0
POLL_THREAD = None
POLL_THREAD_LOCK = threading.RLock()
ALLAPS_FILE = "allAps.txt"
OPENAPS_FILE = "openAps.txt"

WIFI_RSRC_LOCK = threading.RLock()

ALLAPS = {}
OPENAPS = {}
ALL_AP_CNT = 0
OPEN_AP_CNT = 0

extract_key = lambda key,string: string.split(key+":")[1].split(",")[0].strip()
#extract_wireless_values = lambda ap: (extract_key("BSSID",ap),extract_key("SSID",ap),extract_key("capabilities",ap))
extract_wireless_values = lambda ap_result: (ap_result[u"bssid"],ap_result[u"ssid"],ap_result[u"capabilities"])
extract_location_values = lambda location: (location[u'time'], location[u'longitude'], location[u'latitude'], location[u'speed'])
def get_location_values(droid):
	location = None
	location_result = droid.getLastKnownLocation()
	#print location
	if location_result is None or\
		location_result.result is None:
		return "Unavailable","Unavailable","Unavailable","Unavailable"
	if "gps" in location_result.result:
		location = location_result.result["gps"]
	elif "network" in location_result.result:
		location = location_result.result["gps"]
	if location:
		return location[u'time'], location[u'longitude'], location[u'latitude'], location[u'speed']
	return "Unavailable","Unavailable","Unavailable","Unavailable"
	

build_wireless_string = lambda bssid, ssid, cap:"BSSID: %s, SSID: %s, Capabilities: %s"%(bssid, ssid, cap)
build_location_string = lambda lon, lat, spe:"LONGITUDE: %s, LATITUDE: %s, SPEED: %s"%(lon, lat, spe)

def read_file(fname, collection):
	try:
		f = open(fname).readlines()
		d = [i.strip() for i in f]
		for i in d:
			if i == "":
				continue
			ap = i.split("/")[0].strip()
			locs = i.split("/")[1:]
			if not ap  in collection:
				collection[ap] = set()
			collection[ap] = set(locs) | collection[ap]
	except:
		pass
	return collection

def read_initial_data():
	global ALLAPS_FILE, OPENAPS_FILE, ALLAPS, OPENAPS
	OPENAPS = read_file(OPENAPS_FILE, OPENAPS)
	ALLAPS = read_file(ALLAPS_FILE, ALLAPS)

def parseAPStrings(droid, ap_list):
	IdentifiedWirelessAPs = {}
	OpenWirelessAP_Location = {}
	location_result = droid.readLocation()
	if location_result is None and\
		location_result.result is None:
			time_, long_, lat_, speed_ = ("Unavailable","Unavailable","Unavailable","Unavailable")
	else:
		time_, long_, lat_, speed_ = extract_location_values(droid.readLocation().result)
	loc_str = build_location_string( long_, lat_, speed_)
	print "Current Location String %s"%(loc_str)
	for ap in ap_list:
		if ap == "":
			continue
		bssid_, ssid_, capabilities_ = extract_wireless_values(ap)		
		ap_str = build_wireless_string(bssid_, ssid_, capabilities_)
		if capabilities_.find("[WEP]") > -1 or capabilities_ == "":
			if not ap_str in OpenWirelessAP_Location:
				OpenWirelessAP_Location[ap_str] = set()
			OpenWirelessAP_Location[ap_str].add(loc_str)
		if not ap_str in IdentifiedWirelessAPs:
			IdentifiedWirelessAPs[ap_str] = set()
		IdentifiedWirelessAPs[ap_str].add(loc_str)
	return IdentifiedWirelessAPs, OpenWirelessAP_Location

def parseAPResults(droid, ap_results):
	IdentifiedWirelessAPs = {}
	OpenWirelessAP_Location = {}
	time_, long_, lat_, speed_ = get_location_values(droid)
	loc_str = build_location_string( long_, lat_, speed_)
	print "Current Location String %s"%(loc_str)
	for ap in ap_results:
		if len(ap) == 0:
			continue
		bssid_, ssid_, capabilities_ = extract_wireless_values(ap)		
		ap_str = build_wireless_string(bssid_, ssid_, capabilities_)
		if capabilities_.find("[WEP]") > -1 or capabilities_ == "":
			if not ap_str in OpenWirelessAP_Location:
				OpenWirelessAP_Location[ap_str] = set()
			OpenWirelessAP_Location[ap_str].add(loc_str)
		if not ap_str in IdentifiedWirelessAPs:
			IdentifiedWirelessAPs[ap_str] = set()
		IdentifiedWirelessAPs[ap_str].add(loc_str)
	return IdentifiedWirelessAPs, OpenWirelessAP_Location

def merge_collection(src, dst):
	for key in src:
		if not key in dst:
			dst[key] = set()
		dst[key] = dst[key] | src[key]
	return dst
	
def mergeScanResults(allAps, openAps):
	global ALLAPS, OPENAPS
	ALLAPS = merge_collection(allAps, ALLAPS)
	OPENAPS = merge_collection(openAps, OPENAPS)
	print "Unique APs: %d Open APS %d Access Points"%(len(OPENAPS),len(ALLAPS))
	
def getProcessWriteResults(droid):
	global FEED_BACK
	#results = droid.getScanResultsParseable()
	
	results = droid.wifiGetScanResults()
	#print "processing results:",results
	if results and\
		results.result and\
		len(results.result) > 0:
		#ap_list = results.result['aps'].split("/")
		#allAps, openAps = parseAPStrings(droid, ap_list)
		allAps, openAps = parseAPResults(droid, results.result)
		#print "Found: %d Open APS %d Access Points"%(len(openAps),len(allAps))
		aps_cnt = len(OPENAPS)
		mergeScanResults(allAps, openAps)
		if FEED_BACK and aps_cnt < len(OPENAPS):
			msg = "%d Open access points found."%(len(OPENAPS)-aps_cnt)
			#droid.speak(msg)
			droid.vibrate()
		writeAps(openAps, OPENAPS_FILE)
		writeAps(allAps, ALLAPS_FILE)
	# schedule the next scan and the read
	WIFI_RSRC_LOCK.acquire()
	reset_wifi_scan(droid)
	WIFI_RSRC_LOCK.release()
	#print "Scheduling another read" , POLL_TIME
	scheduleNextRead(droid,POLL_TIME)
	
def writeAps(openAps, fname):
	global OPENAPS_FILE
	f = open(fname, "a")
	aps = openAps.keys()
	aps.sort()
	for ap in aps:
		loc_list = [i for i in openAps[ap]]
		loc_list.sort()
		write_str = ap+"/"+"/".join(loc_list)
		f.write(write_str+"\n")
	
def writeIdentifiedAps(allAps, fname=None):
	global ALLAPS_FILE
	if fname is None:
		fname = ALLAPS_FILE
	f = open(fname, "a")
	aps = [i for i in allAps]
	aps.sort()
	write_str = "\n".join(aps)
	f.write(write_str+"\n")

def scheduleNextRead(droid, time_=1):
	global KEEP_POLLING, POLL_THREAD_LOCK, POLL_THREAD
	if not KEEP_POLLING:
		return
	#print "scheduleNextRead called and execing"
	POLL_THREAD_LOCK.acquire()
	POLL_THREAD = threading.Timer(time_, getProcessWriteResults, (droid,))
	POLL_THREAD.start()
	POLL_THREAD_LOCK.release()

def set_parse_options():
	parser = OptionParser()
	parser.add_option("-o", "--open_aps", dest="openApsFile", type="string",
                  help="file to write open APs too")
	parser.add_option("-c", "--use_cmd",action="store_true", dest="cmdPrompt",
                  help="if not set")
	parser.add_option("-i", "--identified_aps", dest="allApsFile", type="string",
                  help="file to write identified aps too")
	parser.add_option("-t", "--polling_time", dest="polling_time", type="float",
                  help="time to between polling wifi scan results")
	parser.add_option("-p", "--lport_adb", dest="lport", type="int",
                  help="local port adb is listening on for the ASE")

	parser.set_defaults(openApsFile = "openAps.txt", 
			allApsFile = "allAps.txt",
			polling_time = 1.0,
			lport=None,
			cmdPrompt=False)
	return parser
	
	

def init_android(port=None):
	droid = None
	if not isinstance(port, int) or port is None:
		droid = android.Android()
	else:
		droid = android.Android(("localhost",port))
	droid.startLocating(1,1)
	while not droid.getLastKnownLocation().result:
		time.sleep(1)
	droid.toggleWifiState(True)
	while not droid.wifiStartScan().result:
		time.sleep(1)
	return droid

def reset_wifi_scan(droid):
	droid.toggleWifiState(False)
	while droid.checkWifiState().result:
		time.sleep(1)
	droid.toggleWifiState(True)
	while not droid.checkWifiState().result:
		time.sleep(1)
	while not droid.wifiStartScan().result:
		time.sleep(1)
	
def getFloatDialog(droid, TTS, dia, default):
	message = droid.getInput(TTS, dia).result
	data = default
	try:
		data = float(message)
	except:
		pass
	return data

def getStrDialog(droid, TTS, dia, default):
	message = droid.getInput(TTS, dia).result
	if not message is None:
		return message
	return default
	
def getBoolDialog(droid, TTS, msg, default):
	droid.dialogCreateAlert(msg)
	droid.dialogSetPositiveButtonText('Yes')
	droid.dialogSetNegativeButtonText('No')
	droid.dialogShow()
	result = droid.dialogGetResponse()
	if result is None or\
		result.result is None or\
		not 'which' in result.result:
		return default
	return result.result['which'] == 'positive'
	
def run(droid):
	global KEEP_POLLING, POLL_THREAD_LOCK, POLL_THREAD
	scheduleNextRead(droid,POLL_TIME)
	while KEEP_POLLING:
		try:
			POLL_THREAD_LOCK.acquire()
			if not POLL_THREAD.isAlive():
				getProcessWriteResults(droid)
				print "Uh-oh the no longer polling scan results is dead..exitiing"
				break
			POLL_THREAD_LOCK.release()
			time.sleep(3)
		except KeyboardInterrupt:
			print("Exitting the loop.")
			KEEP_POLLING = False
			POLL_THREAD_LOCK.acquire()
			POLL_THREAD.cancel()
			POLL_THREAD_LOCK.release()
			break
		except:
			print ("The following Exception Occurred:")
			traceback.print_exc(file=sys.stdout)
			sys.exc_clear()
			pass	
	POLL_THREAD.join()
	
if __name__ == "__main__":
	#global POLL_TIME, OPENAPS_FILE, ALLAPS_FILE, KEEP_POLLING, POLL_THREAD_LOCK, POLL_THREAD
	parser = set_parse_options()
	(options, args) = parser.parse_args()
	droid = init_android(options.lport)
	if options.cmdPrompt:
		POLL_TIME = options.polling_time
		OPENAPS_FILE = options.openApsFile
		ALLAPS_FILE = options.allApsFile
		FEED_BACK = True
	else:
		TTS = "Wireless Scanner Config"
		POLL_TIME = getFloatDialog(droid, TTS, "Please enter time between wireless polls:", 1.0)
		OPENAPS_FILE = getStrDialog(droid, TTS, "Please enter dst file for the Open APS Identified", OPENAPS_FILE)
		ALLAPS_FILE = getStrDialog(droid, TTS, "Please enter dst file for the All APS Identified", ALLAPS_FILE)
		FEED_BACK = getBoolDialog(droid, TTS, "Vibrate when an Open AP is found?", True)
	KEEP_POLLING = True
	
	read_initial_data()
	run_thread = threading.Thread(target=run,args=(droid,))
	run_thread.start()
	print "Ctrl-C to quit"
	try:
		while 1:
			time.sleep(4)
	except KeyboardInterrupt:
		KEEP_POLLING = False
		print("Exitting scanner.")
	
	run_thread.join()
	openAps_final = OPENAPS_FILE.split('.')[0]+"_final.txt"
	allAps_final = ALLAPS_FILE.split('.')[0]+"_final.txt"
	writeAps(OPENAPS,openAps_final)
	writeAps(ALLAPS,allAps_final)	

	
	