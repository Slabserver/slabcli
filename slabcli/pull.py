from slabcli.common import sync

def add_arguments(parser):
    parser.add_argument('--dry-run', action='store_true', help='Show what would be pushed')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite local changes')
    parser.add_argument('--xyz', type=str, help='Custom XYZ option for pull')


def run(args):
    print(f"Pulling with xyz = {args.xyz}")
    args.direction = "down"
    sync.run(args)