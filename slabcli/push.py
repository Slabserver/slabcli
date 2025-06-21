def add_arguments(parser):
    parser.add_argument('--force', action='store_true', help='Force push even if dirty')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be pushed')

def run(args):
    if args.dry_run:
        print("[dry-run] Would push current state...")
    elif args.force:
        print("Force pushing state...")
    else:
        print("Pushing state...")