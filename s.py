
data = '''bool rebase_cli(std::string args);
bool rebase_rsp(Buffer &buf);


bool get_regs_cli(std::string args);
bool get_regs_rsp(Buffer &buf);
bool get_regs_req(Buffer &buf);

bool set_regs_rsp(Buffer &buf);
bool set_regs_cli(std::string args);

bool set_bps_cli(std::string args);
bool set_bps_req(Buffer &b);

bool resume_req(Buffer &b);
bool break_req(Buffer &b);

bool get_bps_cli(Buffer &b);
bool get_bps_req(Buffer &b);
bool get_bps_rsp(Buffer &buf);

bool rebase_cli(std::string args);
bool rebase_req(Buffer &b);

bool add_alias_cli(std::string args);'''

cleanup = [" ".join(i.split()[1:]).split("(")[0] for i in data.splitlines() if i != ""]
cleanup.sort()


funcs = {}

for i in cleanup:
    n = "".join(i.split("_")[:-1])
    funcs[n] = ["default_net_handler","default_net_handler","default_cli_handler"]


for i in cleanup:
    x = i.split("_")[-1]
    n = "".join(i.split("_")[:-1])
    if x == 'cli':
        funcs[n][2] = i
    elif x == 'rsp':
        funcs[n][1] = i
    elif x == 'req':
        funcs[n][1] = i

cmd_handler = "register_cmd_handler(%s, %s);"
cli_handler = "register_cli_handler(%s, %s);"
for k in funcs:
    a,b,c = funcs[k]
    n = '"'+"".join(k.split("_")[:2])+'"'
    print "\n\n// %s cmd and cli handler registration"%(n)
    print cmd_handler%(n,a)
    print cmd_handler%(n,b)
    print cli_handler%(n,c)










