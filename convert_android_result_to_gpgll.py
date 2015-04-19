import android, sys, threading, time

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
	return str(abs(longitude)*100)+","+hemi

def create_gpgll_sentence(result):
	gll = "$GPGLL,"
	gll+= convert_latitude_to_NMEA(result)
	gll+= convert_longitude_to_NMEA(result)
	gll+= ","+str(result['time'])
	gll+= ",A,*"
	gll+= get_checksum(gll)
	return gll+"\r\n"

def init_android_instance(port, accuracy="fine", minUpdateTimeMs=3000,minDistanceM=3):
	port = int(port)
	d = android.Android(("localhost", port))
	d.startLocating(accuracy,minUpdateTimeMs,minDistanceM)
	return d

def run_cmd(cmd_str):
	x = Popen(cmd_str.split(), stdout=PIPE )
	return x.stdout.read()

socat_cmd_str = "socat -d -d tcp:localhost:%d pty,link=/dev/%s,raw,echo=0"
if __name__ == "__main__":
	
	parser = set_parser_options()
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
	
	# start socat in a separate thread
	socat_cmd = socat_cmd_str%(options.stcp_port,options.serialp_name)
	print("Starting socat with the following command: %s"%socat_cmd)
	socat_thread = threading.Thread(None, run_cmd, None, (socat_cmd,))
	# connect our socket to the virtual serial port
	socat_socket = socket()
	socat_socket.connect(("localhost",options.stcp_port))
	
	# init the android ASE interface, and
	# init location facade manager
	droid = init_android_instance(options.adb_lport)
	
	# Now lets rock and roll	
	while 1:
		try:
			event = droid.receiveEvent()
			while not event.result is None and\
					  event.result['name'] != "location":
				event = droid.receiveEvent()
			nmea_sentence = create_gpgll_sentence(event.result)
			print("Posting the following NMEA Sentence: %s", nmea_sentence)
			socat_socket.send(nmea_sentence)
		except KeyboardInterrupt:
			print("Exitting the loop.")
			break
		except:
			print ("The following Exception Occurred %s"%str(sys.sys.exc_info()[0]))
			pass
	# dont bother stopping socat
	# when the script dies the thread will terminate