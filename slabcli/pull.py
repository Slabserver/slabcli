from slabcli.common import sync

def add_arguments(parser):
    parser.add_argument('--dry-run', action='store_true', help='Show what would be pushed')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite local changes')

def run(args):
    
    print('Warning: This will pull the current files and folders from Production to Staging')
    print('Please ensure you are ready for any Staging changes to be reset by Production')
    y = input("Are you sure you wish to continue? (y/N) ")
    
    if y == "y":
        print(f"Pulling with xyz = {args.xyz}")
        args.direction = "down"
        sync.run(args)
    else:
        print("Aborting pull")
