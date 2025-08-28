from slabcli import config
from slabcli.core.ptero import stop_servers, start_servers, restart_servers

def stop(args):
    stop_servers(get_servers(args.target))

def start(args):
    start_servers(get_servers(args.target))

def restart(args):
    restart_servers(get_servers(args.target))

def get_servers(server_type):
    cfg = config.load_config()
    return cfg["servers"].get(server_type, {})