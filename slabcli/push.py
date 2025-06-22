from slabcli.common import sync

def add_arguments(parser):
    # parser.add_argument('--force', action='store_true', help='Force push even if dirty')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be pushed')

def run(args):
    print("Pushing state...")
    args.direction = "up"
    sync.run(args)