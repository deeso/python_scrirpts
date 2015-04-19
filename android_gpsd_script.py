#!/usr/bin/python
#
from optparse import OptionParser
from socket import *
import android, sys, threading, traceback
from subprocess import *
from time import sleep
from math import *


def set_parse_options():
	parser = OptionParser()
	parser.add_option("-a", "--adb_lport", dest="adb_lport", type="int",
                  help="local port that adb will forward too")
	parser.add_option("-b", "--adb_rport", dest="adb_rport", type="int",
                  help="remote port that adb will forward too")
	parser.add_option("-s", "--socat_port", dest="stcp_port", type="int",
                  help="port socat will recieve and forward the data to the serial port")
	parser.add_option("-t", "--serial_name", dest="serialp_name", type="string",
                  help="port socat will recieve and forward the data to the serial port")
	parser.set_defaults(adb_lport = None, 
			adb_rport = None,
			stcp_port = None,
			serialp_name = None)
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
	
def convert_DMlongitude_to_NMEA(result):
	longitude = result['longitude']
	hemi = "E"
	if longitude < 0:
		hemi = "W"
	return str(abs(longitude)*100)+","+hemi
	
def convert_DMlatitude_to_NMEA(result):
	latitude = result['latitude']
	hemi = "N"
	if latitude < 0:
		hemi = "S"
	return str(abs(latitude)*100)+","+hemi

def create_gpgll_sentence(result):
	gll = "$GPGLL,"
	gll+= convert_DMlatitude_to_NMEA(result)
	gll+= convert_DMlongitude_to_NMEA(result)
	gll+= ","+str(result['time'])
	gll+= ",A,*"
	gll+= get_checksum(gll)
	return gll+"\r\n"

def init_android_instance(port, accuracy="coarse", minUpdateTimeMs=0,minDistanceM=1):
	port = int(port)
	print port
	d = android.Android(("localhost", port))
	print ("Android Scripting Environment initialized..time to start locating")
	d.startLocating(accuracy,minUpdateTimeMs,minDistanceM)
	d.startSensing()
	return d


def deinit_android_instance(d):
	d.stopLocating()
	d.stopSensing()
	return d

PROCESS_STARTED = False
def run_cmd(cmd_str):
	global PROCESS_STARTED
	PROCESS_STARTED = False
	x = Popen(cmd_str.split(), stdout=PIPE)
	#print (x.stdout.read())
	PROCESS_STARTED = True
	print "Process started"
	return x

def get_xy_diff(sensor_ev, x, y):
	mag = get_magnitude_vector(sensor_ev)
	az = event.result['azimuth']
	x_projected = x + mag*cos(az*pi/180)
	y_projected = y + mag*sin(az*pi/180)
	return x_projected, y_projected

def get_new_location(gps_ev, sensor_ev):
	x,y,z = convert_spherical_to_cartesian(gps_ev)
	x_proj,y_proj = get_projected_2D(x,y,z) 
	x_diff, y_diff = get_xy_diff(sensor_ev, x, y)
	x_proj3d, y_proj3d = get_projected_3D(x_proj,y_proj,z)
	
	
def convert_spherical_to_cartesian(result):
	latitude = float(result['latitude']) * pi / 180
	longitude = float(result['longitude']) * pi /180
	x = EARTH_R * cos(longitude) * sin(latitude)
	y = EARTH_R * sin(longitude) * sin(latitude)
	z = EARTH_R * cos(latitude)
	return x,y,z

def convert_cartesian_to_sperical(x,y,z):
	
	latitude = arccos(z/EARTH_R)
	longitude = atan2(y,x)
	return longitude,latitude

def get_projected_3D(x_proj,y_proj,z,focal_length=117):
	x = (x_proj * (focal_length + z))/focal_length
	y = (y_proj * (focal_length + z))/focal_length
	return x, y

	
def get_projected_2D(x,y,z,focal_length=117):
	projected_x = x * focal_length / (focal_length + z)
	projected_y = y * focal_length / (focal_length + z)
	return projected_x, projected_y
	

def get_magnitude_vector(event):
	x = float(event.result['xforce'])
	y = float(event.result['yforce'])
	return sqrt(x**2+y**2+z**2)

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
	adb_cmd = "adb forward tcp:%u tcp:%u"%(options.adb_lport, options.adb_rport)
	#init adb
	print ("Setting up adb for Python and ASE interation: %s"%adb_cmd)
	run_cmd(adb_cmd)
	
	# bind our command socket for the socat serial port forwarding
	#socat_server_socket.bind(("localhost",options.stcp_port))
	#socat_server_socket.listen(1)		
	
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

	# init the android ASE interface, and
	# init location facade manager
	droid = init_android_instance(options.adb_lport)
	
	# Now lets rock and roll
	while 1:
		try:
			event = droid.receiveEvent()
			while event.result is None or\
				event.result['name'] != "location":
				event = droid.readSensors()
				if not event.result is None:
					print event
					a = get_acceleration(event)
					print "Acceleration Vector: %f"%a,event.result['xforce']
				event = droid.receiveEvent()
				
			#event = droid.readLocation()
			if not event.result is None:
				nmea_sentence = create_gpgll_sentence(event.result)
				print("Event: %u Posting the following NMEA Sentence: %s"%(event.id, nmea_sentence))
				socat_socket.send(nmea_sentence)
			sleep(1)
		except KeyboardInterrupt:
			print("Exitting the loop.")
			break
		except:
			print ("The following Exception Occurred:")
			traceback.print_exc(file=sys.stdout)
			sys.exc_clear()
			pass
	run_cmd("pkill socat")
	# dont bother stopping socat
	# when the script dies the thread will terminate
