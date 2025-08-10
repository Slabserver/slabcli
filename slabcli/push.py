import time as t
from slabcli import config
from slabcli.common import sync
from slabcli.common.fmt import clifmt
from datetime import datetime, timezone

abort_msg = clifmt.FAIL + "Aborting the SlabCLI 'push' operation"

def add_arguments(parser):
    parser.add_argument('--debug', action='store_true', help='print internal config mappings for Staging and Production')
    parser.add_argument('--dry-run', action='store_true', help='show which files and config changes would be pushed to Production')
    parser.add_argument('--update-only', action='store_true', help='push the config changes only, with no copying of files at all')
    # parser.add_argument('--sync-worlds', action='store_true', help='Pull the Survival/Resource/Passage worlds from Staging to Production')

def run(args):
    cfg = config.load_config()

    print('')
    print(clifmt.HEADER + 'SlabCLI | push')
    print('')

    print_cmd_info(args,cfg)

    y = input("Are you sure you wish to continue? (y/N) ")
    
    if y != "y":
        print(abort_msg)
        return
    if not args.dry_run:
        print(clifmt.WARNING + "Please ensure the SMP servers are powered off prior to running any push operation, to avoid any potential errors")
        print(clifmt.WARNING + "(Running the " + clifmt.WHITE + "/stop server:SMPtNetwork" + clifmt.WARNING + " modbot command in our Discord is typically the fastest way)")
        print('')
        
        y = input(clifmt.WHITE + "Are the Proxy/Survival/Resource/Passage SMP servers powered off? (y/N) ")
        if y != "y":
            print(abort_msg)
            return
    args.sync_worlds = False
    args.direction = "up"
    sync.run(args, cfg)

def print_cmd_info(args, cfg):
    last_push_files = cfg.get("meta", {}).get("last_push_files")
    last_push_config_only = cfg.get("meta", {}).get("last_push_cfg")

    if last_push_files:
        ts_local = datetime.fromtimestamp(last_push_files, tz=timezone.utc)
        ts_readable = ts_local.strftime("%Y-%m-%d %H:%M:%S UTC")
        print(clifmt.OKGREEN + f"Last update of all files/folders from Staging to Production occurred at: {ts_readable}")
    if last_push_config_only:
        ts_local = datetime.fromtimestamp(last_push_config_only, tz=timezone.utc)
        ts_readable = ts_local.strftime("%Y-%m-%d %H:%M:%S UTC")
        print(clifmt.OKCYAN + f"Last update of Production config files from SlabCLI's config.yml occurred at: {ts_readable}")
    print('')

    print(clifmt.WARNING + 'This will push the current files and folders of Staging to Production, updating files with values defined in SlabCLI\'s config.yml')
    print(clifmt.BOLD + 'Please ensure Staging has been thoroughly tested, and that Production has very recent backups')

    if not args.dry_run:
        print('This is a very dangerous command to run accidentally - pausing for 11s to be very certain that this is what you want!')
        t.sleep(11)