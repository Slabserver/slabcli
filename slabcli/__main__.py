import sys
import argparse
from .classmodule import MyClass
from .funcmodule import my_function
from slabcli import push, pull, status

def main():
    # Create the parser
    parser = argparse.ArgumentParser(
        prog='slabserver',
        description='Slabserver CLI for managing server state.',
    )

    # Add an argument
    subparsers = parser.add_subparsers(
        title='subcommands',
        dest='command',
        required=True
    )

    # Push command
    push_parser = subparsers.add_parser('push', help='Push local state to the server')
    push.add_arguments(push_parser)
    push_parser.set_defaults(func=push.run)

    # Pull command
    pull_parser = subparsers.add_parser('pull', help='Pull server state locally')
    pull.add_arguments(pull_parser)
    pull_parser.set_defaults(func=pull.run)

    # Status command
    status_parser = subparsers.add_parser('status', help='Show sync status')
    status.add_arguments(status_parser)
    status_parser.set_defaults(func=status.run)

    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()

