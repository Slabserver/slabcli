import os
import argparse
import hashlib
from slabcli import config
from slabcli.core import sync
from datetime import datetime, timezone
from slabcli.common.cli import clifmt, abort_cli
from slabcli.core.ptero import restart_servers, are_servers_at_state


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--update-only', action='store_true', help='pull the config changes only, with no copying of files at all')
    parser.add_argument('--force-reset', action='store_true', help='force Staging to be reset by Production even if .jar files differ')
    parser.add_argument('--dry-run', '-y', action='store_true', help='skip prompts, and only show which changes would be pulled to Staging. Useful for writing to log files.')

def run(args):
    cfg = config.load_config()
    args.direction = sync.PULL

    print_cmd_info(args,cfg)
    
    if not args.dry_run:
        y = input(clifmt.WHITE + "Are you sure you wish to continue? (y/N) ")
        if y != "y":
            abort_cli(args.subcommand)
        
    sync.run(args, cfg)

def print_cmd_info(args, cfg):
    last_pull_files = cfg.get("meta", {}).get("last_pull_files")
    last_pull_config_only = cfg.get("meta", {}).get("last_pull_cfg")

    if last_pull_files:
        ts_local = datetime.fromtimestamp(last_pull_files, tz=timezone.utc)
        ts_readable = ts_local.strftime("%Y-%m-%d %H:%M:%S UTC")
        print(clifmt.OKGREEN + f"Last update of all files/folders from Production to Staging occurred at: {ts_readable}")
    if last_pull_config_only:
        ts_local = datetime.fromtimestamp(last_pull_config_only, tz=timezone.utc)
        ts_readable = ts_local.strftime("%Y-%m-%d %H:%M:%S UTC")
        print(clifmt.OKCYAN + f"Last update of Staging config files from SlabCLI's config.yml occurred at: {ts_readable}")
    print('')

    if args.update_only:
        print(clifmt.WARNING + 'This will only update existing config files with values defined in SlabCLI\'s config.yml, as --update-only is set')
        print(clifmt.BOLD + 'Are you certain that Staging has all required config files from Production?')
    else:
        print(clifmt.WARNING + 'This will stop the Staging servers, pull the Slabserver files and folders from Production to Staging, and update files with values defined in SlabCLI\'s config.yml')
        print(clifmt.BOLD + 'Please ensure you are ready for any Staging changes to be reset by Production')
    print('')

    if not jar_files_match(cfg) and not args.update_only and not args.dry_run:
        print(clifmt.FAIL + "Error: Staging and Production are using different server .jar files - Staging is likely being upgraded to a newer Minecraft version")
        print(clifmt.FAIL + "A pull should follow a successful push - unless Staging is being reset, you are likely to override a Staging upgrade by mistake")
        if not args.force_reset:
            print(clifmt.FAIL + "If you are certain that this is what you are trying to do, run 'slabcli pull' with the --force-reset flag to bypass this error")
            abort_cli(args.subcommand)

def jar_files_match(cfg):
    jar_prefix = "/srv/daemon-data/"
    jar_map = {
        "proxy": "/bungeecord.jar",
        "passage": "/server.jar",
        "survival": "/server.jar",
        "resource": "/server.jar"
    }

    for server, jar_name in jar_map.items():
        prod_id = cfg["servers"].get("production", {}).get(server)
        staging_id = cfg["servers"].get("staging", {}).get(server)

        if not prod_id or not staging_id:
            return False

        prod_jar = f"{jar_prefix}{prod_id}{jar_name}"
        staging_jar = f"{jar_prefix}{staging_id}{jar_name}"

        # Check file existence
        if not os.path.exists(prod_jar) or not os.path.exists(staging_jar):
            print(f"Missing jar for {server}: {prod_jar} or {staging_jar}")
            return False

        if not files_match(prod_jar, staging_jar):
            return False
    return True

def files_match(path1, path2):
    return file_checksum(path1) == file_checksum(path2)

def file_checksum(path, algo="sha256", chunk_size=8192):
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()

