#
#  Author: Adam Pridgen <adam@praetoriangrp.com>
#  (C) 2010 praetorian group 
#  droid_gps.py - gps bridge for the android phone and GPSd or Kismet


from optparse import OptionParser
from socket import *
import android, sys, threading, traceback, time
from subprocess import *
from time import sleep
from math import *
from datetime import date,timedelta,datetime
from threading import Timer


EARTH_R = 10^6 # really does not matter since the factor is multiplied before its used

POLL_THREAD = None

def set_parse_options():
	parser = OptionParser()
	parser.add_option("-l", "--adb_lport", dest="adb_lport", type="int",
                  help="local port that adb will forward too")
	parser.add_option("-r", "--adb_rport", dest="adb_rport", type="int",
                  help="remote port that adb will forward too")
	parser.add_option("-t", "--timing", dest="timing", type="int",
                  help="how many seconds between polling the phones gps")
	parser.add_option("-p", "--socat_port", dest="stcp_port", type="int",
                  help="port socat will recieve and forward the data to the serial port")
	parser.add_option("-s", "--serial_name", dest="serialp_name", type="string",
                  help="port socat will recieve and forward the data to the serial port")
	parser.set_defaults(adb_lport = None, 
			adb_rport = None,
			stcp_port = None,
			serialp_name = None,
			timing = 3)
	return parser

def get_checksum(sentence):
	Checksum = 0
	for char in sentence:
		if char == '$': continue
		elif char == '*': break
		else:
			if Checksum == 0:
				Checksum = ord(char)
			else:
				Checksum = Checksum ^ ord(char)
	return "%x"%Checksum
	
def convert_DMlongitude_to_NMEA(longitude):
	hemi = "E"
	if longitude < 0:
		hemi = "W"
	return "%.4f"%(convert_value(abs(longitude)))+","+hemi

def convert_value(DMS):
	D = int(DMS)
	M = (DMS - D) * 60
	#S = ((DMS - D )*3600 - M * 60) * 3600
	val = float(D * 100) + M
	return val

def convert_DMlatitude_to_NMEA(latitude):
	hemi = "N"
	if latitude < 0:
		hemi = "S"
	return "%.4f"%(convert_value(abs(latitude)))+","+hemi

def create_gpgll_sentence(lat, long, time_):
	gll = "$GPGLL,"
	gll+= convert_DMlatitude_to_NMEA(lat)
	gll+= convert_DMlongitude_to_NMEA(long)
	d = datetime.fromtimestamp(time_/1000)
	gll+= ","+d.strftime('%H%M%S')
	gll+= ",A,*"
	gll+= get_checksum(gll)
	return gll+"\r\n"

def create_gprmc_sentence(lat, lon, time_,speed_=0.0,course_=0.00):
	rmc = "$GPRMC"
	d = datetime.fromtimestamp(time_/1000)
	rmc+= ","+d.strftime('%H%M%S')+".999"
	rmc+= ","+"A"
	rmc+= ","+convert_DMlatitude_to_NMEA(lat)
	rmc+= ","+convert_DMlongitude_to_NMEA(lon)
	rmc+= ",%.2f"%(speed_*1.943844)
	rmc+= ",%.2f"%(course_)
	rmc+= ","+d.strftime('%D').replace("/","")
	rmc+= ",,*"+get_checksum(rmc)
	return rmc+"\r\n"

def init_android_instance(port, minUpdateTimeMs=1,minUpdateDistance=1):
	port = int(port)
	d = android.Android(("localhost", port))
	print ("Android Scripting Environment initialized..time to start locating")
	d.startLocating(minUpdateTimeMs,minUpdateDistance)
	ev = d.getLastKnownLocation()
	while not ev.result:
		sleep(4)
		print ev.result
	return d

def test_gps(d):
	ev_p = ev = d.readLocation()
	print str(ev_p.result)
	while True:
		ev = d.readLocation()
		if str(ev.result) == str(ev_p.result):
			continue
		ev_p = ev
		print str(ev_p.result)
def same_events(ev, ev_p):
	return str(ev.result) == str(ev_p.result)
		
def deinit_android_instance(d):
	d.stopLocating()
	return d

def pollForLocationEv(droid):
	ev = get_location_values(droid)
	#ev = droid.receiveEvent()
	#print ev
	#while not ev is None or\
	#	not ev.result is None or\
	#	not 'name' in ev.result or\
	#	ev.result['name'] != u"location":
	#	ev = droid.receiveEvent()
	return ev


def run_cmd(cmd_str):
	#global PROCESS_STARTED
	#PROCESS_STARTED = False
	x = Popen(cmd_str.split(), stdout=PIPE)
	#print (x.stdout.read())
	#PROCESS_STARTED = True
	#print "Process started"
	return x

KeepRunning = True
POLL_THREAD_LOCK = threading.RLock()
extract_stuff = lambda result:(float(result['latitude']),float(result['longitude']),int(result['time']),float(result['speed']))

def get_location_values(droid):
	location = None
	location_result = droid.getLastKnownLocation()
	#print location
	default = (0,0.0,0.0,0)
	if location_result is None or\
		location_result.result is None:
		return default
	ida = location_result.id
	if "gps" in location_result.result and\
		not location_result.result["gps"] is None:
		location = location_result.result["gps"]
	elif "network" in location_result.result:
		location = location_result.result["network"]
	if location:
		return ida, float(location[u'latitude']),float(location['longitude']),int(location['time'])
	return ida,0.0,0.0,0

def read_location_xmit_socat(droid, socat_socket, ev_p):
	id,lat_,long_,t_ = get_location_values(droid)
	tnow = date.fromtimestamp(time.time())
	if (id,lat_,long_,t_) != (0,0.0,0.0,0):
		nmea_sentence = ""
		ev_p = (id,lat_,long_,t_)
		nmea_sentence = create_gprmc_sentence(lat_,long_,t_)
		print("Event: %u Posting the following NMEA Sentence: %s"%(id, nmea_sentence))
		socat_socket.send(nmea_sentence)
	else:
		print "Read invalid location information"
	schedule_callback(droid, socat_socket, ev_p)

def schedule_callback(droid, socat_socket, ev_p):
	global POLL_THREAD_LOCK, POLL_THREAD
	POLL_THREAD_LOCK.acquire()
	POLL_THREAD = Timer(TIME, read_location_xmit_socat, args=(droid, socat_socket, ev_p))
	POLL_THREAD.start()
	POLL_THREAD_LOCK.release()

def construct_sent(string):
	return string+get_checksum(string)+"\r\n"

def test_gpsd(sock):
	s = sock.recv(100000)
	print repr(s)

socat_cmd_str = "socat -d TCP4-LISTEN:%u,bind=localhost,reuseaddr pty,link=/dev/%s,raw,echo=0"

	
if __name__ == "__main__":
	parser = set_parse_options()
	(options, args) = parser.parse_args()
	if options.adb_lport is None or\
		options.adb_rport is None or\
		options.stcp_port is None or\
		options.serialp_name is None:
		parser.print_help()
		sys.exit(-1)
	TIME = options.timing
	adb_cmd = "adb forward tcp:%u tcp:%u"%(options.adb_lport, options.adb_rport)
	#init adb
	print ("Setting up adb for Python and ASE interation: %s"%adb_cmd)
	run_cmd(adb_cmd)
	
	# bind our command socket for the socat serial port forwarding
	# start socat in a separate thread
	socat_cmd = socat_cmd_str%(options.stcp_port,options.serialp_name)
	print("Starting socat with the following command: %s"%socat_cmd)
	socat_thread = threading.Thread(target=run_cmd, args=(socat_cmd,))
	# ugh, always need to remember to start 
	# the thread!!! 3 hours lost )-:
	socat_thread.start()	
	sleep(2)
	# connect to the thread
	print ("Connecting to: localhost %u"%options.stcp_port)
	socat_socket = socket()
	socat_socket.connect(("localhost",options.stcp_port))
	pash = "$PASHR,RID*"
	pgrm = "$PGRMC,2,0,,,,,,,,5,,,,*"
	#socat_sock.send(construct_sent(pash))
	# testing out gpsd
	#test_gpsd(socat_socket)
	f = raw_input("Press Enter After you have started gpsd or kismet")
	socat_socket.send(construct_sent(pgrm))
	#print repr(socat_socket.recv(8096))

	# init the android ASE interface, and
	# init location facade manager
	droid = init_android_instance(options.adb_lport)
	# Now lets rock and roll
	long_p = lat_p = 0.0
	t_p = 0
	last_update = date.fromtimestamp(time.time())
	tdelta = timedelta(milliseconds=(1000))
	# poll for the first Location event
	ev_p = pollForLocationEv(droid)
	ev = ev_p
	schedule_callback(droid, socat_socket, ev_p)
	while 1:
		try:
			POLL_THREAD_LOCK.acquire()
			if not POLL_THREAD.isAlive():
				print "Uh-oh polling thread failed )-:"
				POLL_THREAD_LOCK.release()
				break
			POLL_THREAD_LOCK.release()
			sleep(3)
		except KeyboardInterrupt:
			print("Exitting the loop.")
			KeepRunning = False
			POLL_THREAD_LOCK.acquire()
			POLL_THREAD.cancel()
			POLL_THREAD_LOCK.release()
			POLL_THREAD.join()
			break
		except:
			print ("The following Exception Occurred:")
			traceback.print_exc(file=sys.stdout)
			sys.exc_clear()
			pass
	#run_cmd("pkill socat")
	# dont bother stopping socat
	# when the script dies the thread will terminate
