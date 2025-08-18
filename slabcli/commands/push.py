import time as t
from slabcli import config
from slabcli.core import sync
from slabcli.common.fmt import clifmt
from datetime import datetime, timezone

abort_msg = clifmt.FAIL + "Aborting the SlabCLI 'push' operation"

def add_arguments(parser):
    parser.add_argument('--debug', action='store_true', help='print internal config mappings for Staging and Production')
    parser.add_argument('--dry-run', action='store_true', help='show which files and config changes would be pushed to Production')
    parser.add_argument('--update-only', action='store_true', help='push the config changes only, with no copying of files at all')
    parser.add_argument('--skip-prompts', '-y', action='store_true', help='skips input prompts, but sets --dry-run. Useful for writing to log files.')

def run(args):
    cfg = config.load_config()
    args.direction = sync.PUSH
    args.sync_worlds = False
    args.dry_run = True if args.skip_prompts else False

    print('')
    print(clifmt.HEADER + 'SlabCLI | push')
    print('')

    if args.debug:
        sync.run(args, cfg)
        print(abort_msg)
        return

    print_cmd_info(args,cfg)

    if not args.skip_prompts:
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

    print(clifmt.WARNING + 'This will push files and folders defined in config.yml from Staging to Production, and update files with values defined in SlabCLI\'s config.yml')
    print(clifmt.BOLD + 'Please ensure Staging has been tested, Production has very recent backups, & lockdown is set in the Bouncer/persistent.yml if required.')

    if not args.dry_run:
        print('This is a very dangerous command to run accidentally - pausing for 11s to be very certain that this is what you want!')
        t.sleep(11)