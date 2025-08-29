import argparse
from slabcli import config
from slabcli.core.ptero import stop_servers, start_servers, restart_servers

def add_arguments(parser: argparse.ArgumentParser) -> None:
    pass

def stop(args):
    return stop_servers(get_servers(args.target))

def start(args):
    return start_servers(get_servers(args.target))

def restart(args):
    return restart_servers(get_servers(args.target))

def get_servers(server_type):
    cfg = config.load_config()
    return cfg["servers"].get(server_type, {})