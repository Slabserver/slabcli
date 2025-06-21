def add_arguments(parser):
    parser.add_argument('--overwrite', action='store_true', help='Overwrite local changes')
    parser.add_argument('--xyz', type=str, help='Custom XYZ option for pull')

def run(args):
    if args.overwrite:
        print("Overwriting local changes with server state...")
    print(f"Pulling with xyz = {args.xyz}")