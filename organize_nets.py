
def organize_nets(tree, addr):
	a,b,c,d = addr.split(".")
	if not a in tree:
		tree[a] = {}
	a_tree = tree[a]
	if not b in a_tree:
		a_tree[b] = {}
	b_tree = a_tree[b]
	if not c in b_tree:
		b_tree[c] = set()
	c_tree = b_tree[c]
	if not d in c_tree:
		c_tree.add(d)
	return tree

def get_subnets(networks):
	nets = set()
	networks_ = []
	a_nets = networks.keys()
	a_nets.sort()
	for a_net in a_nets:
		b_nets = networks[a_net].keys()
		b_nets.sort()
		for b_net in b_nets:
			c_nets = networks[a_net][b_net].keys()
			c_nets.sort()
			for c_net in c_nets:
				if not a_net+"."+b_net+"."+c_net+".0/24" in nets:
					networks_.append( a_net+"."+b_net+"."+c_net+".0/24")
	return networks_
	
fname = "C:\\Users\\apridgen\\Desktop\\scan_results\\acc_internal_ips_10.txt"
tree = {}
lines = open(fname).readlines()
for line in lines:
	if line.strip() == "":
		continue
	tree = organize_nets(tree, line.strip())

fname = "C:\\Users\\apridgen\\Desktop\\scan_results\\acc_internal_ips_10_nets.txt"
f = open(fname,"a")
networks = get_subnets(tree)

nets = [i for i in networks]
nets.sort()

f.write("\n".join(nets)+"\n")
f.close()
