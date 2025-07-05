from slabcli.common import sync

def add_arguments(parser):
    parser.add_argument('--dry-run', action='store_true', help='show what would be pulled')
    parser.add_argument('--sync-worlds', action='store_true', help='pull the Survival/Resource/Passage worlds (disabled by default)')
    parser.add_argument('--update-only', action='store_true', help='pull the config changes only, with no copying of files at all')
    

def run(args):
    print('')
    print('Warning: This will pull the current files and folders from Production to Staging')
    print('Please ensure you are ready for any Staging changes to be reset by Production')
    if args.update_only:
        print('This will only update the config files, and --sync-worlds will not work')
    else:
        if args.sync_worlds:
            print('This includes the Survival/Resource/Passage worlds, as --sync-worlds is set')
        else:
            print('This excludes the Survival/Resource/Passage worlds, as --sync-worlds isn\'t set')

    print('')
    y = input("Are you sure you wish to continue? (y/N) ")
    
    if y == "y":
        args.direction = "down"
        sync.run(args)
    else:
        print("Aborting pull")
