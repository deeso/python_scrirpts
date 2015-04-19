from scapy.all import *


def find_next_handshake(packet_list, pos=0):
	# find next valid TCP/IP Handshake
	cnt = 0
	p = packet_list
    while cnt+pos < len(packet_list)-3:
		if not TCP in p[cnt+pos]: continue
		if p[cnt+pos][TCP].flags == 0x2 and\
			p[cnt+pos+1][TCP].flags == 0x12 and\
        	p[cnt+pos+2][TCP].flags == 0x10: return cnt+pos+3
		cnt += 1
	return None

def get_pkt_payloads(pkt_list, ipaddr, pos=0):
	data_sent = []
	data_rcvd = []
	cnt = 0
	while cnt+pos < len(pkt_list):
		v = cnt+pos
		p = pkt_list[v]
		if not IP in p and not TCP in p: continue
		if p[TCP].flags == 0x14: break
		if p[TCP].flags == 0x10: pass
		elif len(p[TCP].payload)== 0: pass
		elif  p[IP].src == ipaddr:
			data_sent.append(str((p[TCP]).payload))
		elif  p[IP].dst == ipaddr:
			data_rcvd.append(str((p[TCP]).payload))
		cnt+=1
	return pos, data_sent, data_rcvd
		
def get_data_pkts(packet_list, pos=0):
	# find the end of the TCP/IP
	sender_data = []
	rcver_data = []
	cnt = 0 
	p = packet_list
	sender = packet_list[0].src
    reciever = packet_list[0].dst
	# things to consider ports
	# multiple transactions in either direction
    
	while cnt+pos < len(packet_list)-3:
		if not TCP in p[cnt+pos]: continue
		if p[cnt+pos][TCP].flags != 0x14 or\
			break
		if p[cnt+pos][TCP].flags == 0x10:
			# Ack to data ignore
			continue
		if p[cnt+pos].src == sender and\
			len(p[cnt+pos][TCP].payload) > 0:
			sender_data.append(p[cnt+pos][TCP].payload)
		elif p[cnt+pos].src == reciever and\
			len(p[cnt+pos][TCP].payload) > 0:
			rcver_data.append(p[cnt+pos][TCP].payload)
		cnt += 1
	return None

def get_data(packet_list):
   data_to = []
   data_from = []
   
   while True:
      if 

def get_data_from_traffic(packet_list):
  data = {}
  
  while pkt < len( packet_list ):
     if not TCP in pkt: continue
        pkt += 3
        d, pkt = get_data_from_flow(packet_list[pkt:])
     else:
        pkt += 1    


def get_tcp_traffic(pcap, ipaddr):
  sessions = {}
  for i in pcap:
    if not IP in i or not TCP in i:  continue
    if i[IP].src != ipaddr and i[IP].dst != ipaddr: continue
    if i[IP].src == ipaddr:
       if not i[IP].dst in sessions:
          sessions[i[IP].dst] = []
       sessions[i[IP].dst].append(i)
    elif i[IP].dst == ipaddr:
       if not i[IP].src in sessions:
          sessions[i[IP].src] = []
       sessions[i[IP].src].append(i)
  return sessions


f = "FILENAME"
pcap = rdpcap(f)
infected = "172.16.252.132"



# Separate traffic out by host dst/srcs to and from our infected
# host, yay!
sessions = get_tcp_traffic(pcap, infected)

for host in sessions:
   valid_data = get_data_from_traffic(sessions[host])
