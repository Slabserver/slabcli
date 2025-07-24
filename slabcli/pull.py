from datetime import datetime, timezone
from slabcli import config
from slabcli.common import sync
from slabcli.common.colors import clicolors

def add_arguments(parser):
    parser.add_argument('--dry-run', action='store_true', help='show what would be pulled')
    parser.add_argument('--sync-worlds', action='store_true', help='pull the Survival/Resource/Passage worlds (disabled by default)')
    parser.add_argument('--update-only', action='store_true', help='pull the config changes only, with no copying of files at all')

def run(args):
    cfg = config.load_config()
    
    print('')
    if args.update_only & args.sync_worlds:
        print(clicolors.FAIL + 'Error: --update-only and --sync-worlds are incompatible flags\n')
        return
    
    print(clicolors.HEADER + 'SlabCLI | pull')
    print('')
    
    last_pull_files = cfg.get("meta", {}).get("last_pull_files")
    last_pull_config_only = cfg.get("meta", {}).get("last_pull_cfg")

    if last_pull_files:
        ts_local = datetime.fromtimestamp(last_pull_files, tz=timezone.utc)
        ts_readable = ts_local.strftime("%Y-%m-%d %H:%M:%S UTC")
        print(clicolors.OKGREEN + f"Last pull of all files/folders from Production to Staging occurred at: {ts_readable}")
    if last_pull_config_only:
        ts_local = datetime.fromtimestamp(last_pull_config_only, tz=timezone.utc)
        ts_readable = ts_local.strftime("%Y-%m-%d %H:%M:%S UTC")
        print(clicolors.OKCYAN + f"Last update of Staging config files from SlabCLI's config.yml occurred at: {ts_readable}")
    print('')

    if not args.update_only:
        print(clicolors.WARNING + 'This will pull the Slabserver files and folders from Production to Staging')
        print(clicolors.BOLD + 'Please ensure you are ready for any Staging changes to be reset by Production')
    else:
        print(clicolors.WARNING + 'This will only update existing config files with values defined in SlabCLI\'s config.yml, as --update-only is set')
        print(clicolors.BOLD + 'Are you certain that Staging has all required config files from Production?')
    print('')

    if args.sync_worlds:
        print(clicolors.WARNING + 'This will pull the Survival/Resource/Passage worlds, as --sync-worlds is set')
    else:
        print(clicolors.WARNING + 'This will NOT pull the Survival/Resource/Passage world files, as --sync-worlds isn\'t set')
    print('')
    
    y = input(clicolors.WHITE + "Are you sure you wish to continue? (y/N) ")
    if y == "y":
        y = input(clicolors.WHITE + "Are the Proxy/Survival/Resource/Passage test servers powered off? (y/N) ")
        if y == "y":
            args.direction = "down"
            sync.run(args, cfg)
    else:
        print(clicolors.FAIL + "Aborting the SlabCLI 'pull' operation")
