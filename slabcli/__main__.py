import sys
import argparse
from slabcli.commands import push, pull

def main():
    # Create the parser
    parser = argparse.ArgumentParser(
        prog='slabcli',
        description='Slabserver CLI for managing server state',
    )

    add_subcommands(parser)

    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()

def add_subcommands(parser):
    subparsers = parser.add_subparsers(title='subcommands', dest='subcommand', required=True)

    # Push subcommand
    push_parser = subparsers.add_parser('push', help='Push state of Staging to Production')
    push.add_arguments(push_parser)
    push_parser.set_defaults(func=push.run)

    # Pull subcommand
    pull_parser = subparsers.add_parser('pull', help='Pull state of Production to Staging')
    pull.add_arguments(pull_parser)
    pull_parser.set_defaults(func=pull.run)