import hashlib
from datetime import datetime, timezone
from slabcli import config
from slabcli.common import sync
from slabcli.common.colors import clicolors

abort_msg = clicolors.FAIL + "Aborting the SlabCLI 'pull' operation"

def add_arguments(parser):
    parser.add_argument('--dry-run', action='store_true', help='show what files and config changes would be pulled to Staging')
    parser.add_argument('--sync-worlds', action='store_true', help='pull the Survival/Resource/Passage worlds (disabled by default)')
    parser.add_argument('--update-only', action='store_true', help='pull the config changes only, with no copying of files at all')
    parser.add_argument('--force-reset', action='store_true', help='force Staging to be reset by Production even if .jar files differ')

def run(args):
    cfg = config.load_config()
    
    print('')
    print(clicolors.HEADER + 'SlabCLI | pull')
    print('')

    print_cmd_info(args,cfg)
    
    y = input(clicolors.WHITE + "Are you sure you wish to continue? (y/N) ")
    if y != "y":
        print(abort_msg)
        return
    if not args.dry_run:
        print(clicolors.WARNING + "Please ensure the test servers are powered off prior to running any pull operation, to avoid any potential errors")
        print(clicolors.WARNING + "(Running the " + clicolors.WHITE + "/stop server:TestNetwork" + clicolors.WARNING + " modbot command in our Discord is typically the fastest way)")
        print('')
        
        y = input(clicolors.WHITE + "Are the Proxy/Survival/Resource/Passage test servers powered off? (y/N) ")
        if y != "y":
            print(abort_msg)
            return
        
    args.direction = "down"
    sync.run(args, cfg)

def print_cmd_info(args, cfg):
    if args.update_only & args.sync_worlds:
        print(clicolors.FAIL + 'Error: --update-only and --sync-worlds are incompatible flags\n')
        print(abort_msg)
        exit()

    last_pull_files = cfg.get("meta", {}).get("last_pull_files")
    last_pull_config_only = cfg.get("meta", {}).get("last_pull_cfg")

    if last_pull_files:
        ts_local = datetime.fromtimestamp(last_pull_files, tz=timezone.utc)
        ts_readable = ts_local.strftime("%Y-%m-%d %H:%M:%S UTC")
        print(clicolors.OKGREEN + f"Last update of all files/folders from Production to Staging occurred at: {ts_readable}")
    if last_pull_config_only:
        ts_local = datetime.fromtimestamp(last_pull_config_only, tz=timezone.utc)
        ts_readable = ts_local.strftime("%Y-%m-%d %H:%M:%S UTC")
        print(clicolors.OKCYAN + f"Last update of Staging config files from SlabCLI's config.yml occurred at: {ts_readable}")
    print('')

    if args.update_only:
        print(clicolors.WARNING + 'This will only update existing config files with values defined in SlabCLI\'s config.yml, as --update-only is set')
        print(clicolors.BOLD + 'Are you certain that Staging has all required config files from Production?')
    else:
        print(clicolors.WARNING + 'This will pull the Slabserver files and folders from Production to Staging, updating files with values defined in SlabCLI\'s config.yml')
        print(clicolors.BOLD + 'Please ensure you are ready for any Staging changes to be reset by Production')
    print('')

    if args.sync_worlds:
        print(clicolors.WARNING + 'This will pull the Survival/Resource/Passage worlds, as --sync-worlds is set')
    else:
        print(clicolors.WARNING + 'This will NOT pull the Survival/Resource/Passage world files, as --sync-worlds isn\'t set')
    print('')

    if not jar_files_match(cfg) and not args.update_only:
        print(clicolors.FAIL + "Error: Staging and Production are using different server .jar files - Staging is likely being upgraded to a newer Minecraft version")
        print(clicolors.FAIL + "A pull should follow a successful push - unless Staging is being reset, you are likely to override a Staging upgrade by mistake")
        if not args.force_reset:
            print(clicolors.FAIL + "If you are certain that this is what you are trying to do, run 'slabcli pull' with the --force-reset flag to bypass this error")
            print(abort_msg)
            exit()

def jar_files_match(cfg):
    jar_prefix = "/srv/daemon-data/"
    jar_map = {
        "proxy": "/bungeecord.jar",
        "passage": "/server.jar",
        "survival": "/server.jar",
        "resource": "/server.jar"
    }

    for server, jar_name in jar_map.items():
        prod_id = cfg["servers"].get("prod", {}).get(server)
        staging_id = cfg["servers"].get("staging", {}).get(server)

        if not prod_id or not staging_id:
            return False

        prod_jar = f"{jar_prefix}{prod_id}{jar_name}"
        staging_jar = f"{jar_prefix}{staging_id}{jar_name}"

        if not files_match(prod_jar, staging_jar):
            return False
    return True

def files_match(path1, path2):
    return file_checksum(path1) == file_checksum(path2)

def file_checksum(path, algo="sha256", chunk_size=8192):
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()

