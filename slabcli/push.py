from datetime import time
from slabcli import config
from slabcli.common import sync
from slabcli.common.fmt import clifmt

abort_msg = clifmt.FAIL + "Aborting the SlabCLI 'push' operation"

def add_arguments(parser):
    # parser.add_argument('--sync-worlds', action='store_true', help='Pull the Survival/Resource/Passage worlds from Staging to Production')
    parser.add_argument('--dry-run', action='store_true', help='show what files and config changes would be pushed to Production')

def run(args):
    cfg = config.load_config()

    print('')
    print(clifmt.HEADER + 'SlabCLI | push')
    print('')

    print_cmd_info(args,cfg)

    y = input("Are you sure you wish to continue? (y/N) ")
    
    if y == "y":
        print("Pushing state...")
        args.direction = "up"
        sync.run(args, cfg)
    else:
        print(abort_msg)

def print_cmd_info(args, cfg):
    print('Warning: This will push the current files and folders of Staging to Production')
    print('Please ensure Staging has been tested, and that Production has recent backups')

    print('This is a very dangerous command to run accidentally - pausing for 11s to be very certain that this is what you want!')

    time.sleep(11)