from slabcli.common import sync
from slabcli.common.colors import clicolors

def add_arguments(parser):
    parser.add_argument('--dry-run', action='store_true', help='show what would be pulled')
    parser.add_argument('--sync-worlds', action='store_true', help='pull the Survival/Resource/Passage worlds (disabled by default)')
    parser.add_argument('--update-only', action='store_true', help='pull the config changes only, with no copying of files at all')

def run(args):
        
    print('')
    if args.update_only & args.sync_worlds:
        print(clicolors.FAIL + 'Error: --update-only and --sync-worlds are incompatible flags\n')
        return
    
    print(clicolors.HEADER + 'SlabCLI: This will pull the current files and folders from Production to Staging')
    print(clicolors.BOLD + 'Please ensure you are ready for any Staging changes to be reset by Production')
    print('')

    if args.update_only:
        print(clicolors.WARNING + 'This will only update existing Staging config files with values defined in config.yml')
        print(clicolors.WARNING + 'Are you certain that Staging has been updated with all config files from Production?')

    if args.sync_worlds:
        print(clicolors.WARNING + 'This will pull the Survival/Resource/Passage worlds, as --sync-worlds is set')
    else:
        print(clicolors.WARNING + 'This will NOT pull the Survival/Resource/Passage world files, as --sync-worlds isn\'t set')

    print('')
    y = input("Are you sure you wish to continue? (y/N) ")
    
    if y == "y":
        args.direction = "down"
        sync.run(args)
    else:
        print(clicolors.FAIL + "Aborting pull")
