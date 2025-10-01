import sys
import argparse
from slabcli.commands import power, push, pull
from slabcli.common.cli import clifmt

def main():
    # Create the parser
    parser = argparse.ArgumentParser(
        prog='slabcli',
        description='Slabserver CLI for managing server state',
    )

    add_subcommands(parser)
    args = parser.parse_args()

    print(clifmt.HEADER + f'\nSlabCLI | {args.subcommand}\n')

    args.func(args)

if __name__ == '__main__':
    main()

def add_subcommands(parser: argparse.ArgumentParser):
    subparsers = parser.add_subparsers(title='subcommands', dest='subcommand', required=True)

    # Push subcommand
    push_parser = subparsers.add_parser('push', help='Push state of Staging to Production')
    push.add_arguments(push_parser)
    push_parser.set_defaults(func=push.run)

    # Pull subcommand
    pull_parser = subparsers.add_parser('pull', help='Pull state of Production to Staging')
    pull.add_arguments(pull_parser)
    pull_parser.set_defaults(func=pull.run)

    # Stop subcommand
    stop_parser = subparsers.add_parser('stop', help='Stop Staging or Production servers')
    stop_parser.add_argument("target", choices=["production", "staging"], help="Servers to stop")
    power.add_arguments(stop_parser)
    stop_parser.set_defaults(func=power.stop)

    # Start subcommand
    start_parser = subparsers.add_parser('start', help='Start Staging or Production servers')
    start_parser.add_argument("target", choices=["production", "staging"], help="Servers to start")
    power.add_arguments(start_parser)
    start_parser.set_defaults(func=power.start)

    # Restart subcommand
    start_parser = subparsers.add_parser('restart', help='Restart Staging or Production servers')
    start_parser.add_argument("target", choices=["production", "staging"], help="Servers to restart")
    power.add_arguments(start_parser)
    start_parser.set_defaults(func=power.restart)

