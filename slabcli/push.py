from slabcli.common import sync

def add_arguments(parser):
    # parser.add_argument('--force', action='store_true', help='Force push even if dirty')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be pushed')

def run(args):
    
    print('Warning: This will push the current files and folders of Staging to Production')
    print('Please ensure Staging has been tested, and that Production has recent backups')
    y = input("Are you sure you wish to continue? (y/N) ")
    
    if y == "y":
        print("Pushing state...")
        args.direction = "up"
        sync.run(args)
    else:
        print("Aborting push")
