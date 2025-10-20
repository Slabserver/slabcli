import http
import os
import time
import shutil
import yaml
from slabcli import config
from slabcli.common.cli import clifmt
from slabcli.core.ptero import stop_servers, restart_servers
from slabcli.common.utils import file_has_extension, file_newer_than, print_directory_contents, substring_in_string

clicolor = clifmt.GREEN
print_prefix = ""
should_sync = True

PUSH = "push"
PULL = "pull"

PTERO_ROOT = "/srv/daemon-data/"
SERVER_TYPE = {PUSH: "SMP ", PULL: "test-"}
SERVER_DIRECTIONS = {PUSH: ("staging", "production"), PULL: ("production", "staging")}

def run(args, cfg):
    """Syncs Staging <-> Production servers depending on direction.

    This function performs two main steps:
    1. Sync files from source to destination servers based on the given direction (PUSH or PULL).
    2. Apply config replacements from config.yml to ensure servers are set up correctly post-sync.
    """

    # Determine source and destination servers and their replacement mappings,
    # based on sync direction (PUSH = staging → production, PULL = production → staging).
    try:
        source, dest = SERVER_DIRECTIONS[args.direction]
    except KeyError:
        raise ValueError(f"Unknown direction: {args.direction}")
    
    # Build list of paths to exclude from processing (e.g. world files or user-specified paths)
    exempt_paths = list(cfg["replacements"].get("exempt_" + args.direction + "_paths", []))

    replacements, missing_keys = config.compute_config_replacements(
        cfg["replacements"].get(source, {}),
        cfg["replacements"].get(dest, {})
    )
    # Validate that all necessary replacement keys are present
    if missing_keys:
        raise ValueError("Cannot update servers: missing replacement keys in config.yml")

    source_servers = cfg["servers"].get(source, {})
    dest_servers = cfg["servers"].get(dest, {})

    # Debug output to verify the setup before proceeding
    print(clifmt.LIGHT_GRAY + "replacements dict =", replacements)
    print(clifmt.LIGHT_GRAY + "source_servers =", source_servers)
    print(clifmt.LIGHT_GRAY + "dest_servers =", dest_servers)
    print(clifmt.LIGHT_GRAY + "exempt paths =", exempt_paths)

    if args.dry_run:
        global clicolor, print_prefix, should_sync
        clicolor = clifmt.YELLOW
        print_prefix = "[DRY RUN] "
        should_sync = False

    if not args.update_only:
    # Step 1: Stop destination servers via Pterodactyl API unless we're in update-only or dry-run mode
        if should_sync:
            stop_servers(dest_servers)

    # Step 2: Sync files from source to destination unless we're in update-only mode
        sync_server_files(args, cfg, source_servers, dest_servers)

    # Step 3: Update server config files with any replacements
    update_config_files(args, source_servers, dest_servers, replacements, exempt_paths)

    # Step 4: Log or persist the timestamp of this sync operation
    if should_sync:
        update_sync_timestamps(args, cfg)

    # Step 5: Optionally restart the servers
    if not args.dry_run:
        y = input(clifmt.WHITE + f"Would you like to restart the {dest.capitalize()} servers? (y/N) ")
        if y == "y":
            restart_servers(dest_servers)

def sync_server_files(args, cfg, source_servers, dest_servers):
    """Dispatch sync by direction (PULL or PUSH)."""
    for name in source_servers:
        source_server_root = PTERO_ROOT + source_servers[name]
        dest_server_root = PTERO_ROOT + dest_servers.get(name, "")

        if not dest_server_root:
            print(f"Skipping {name}, no matching destination.")
            continue
        if not os.path.exists(dest_server_root):
            raise FileNotFoundError(f"Destination path does not exist: {dest_server_root}")

        if args.direction == PULL:
            sync_pull(args, cfg, name, source_server_root, dest_server_root)
        elif args.direction == PUSH:
            sync_push(args, cfg, name, source_server_root, dest_server_root)

def sync_pull(args, cfg, name, source_server_root, dest_server_root):
    """Sync an entire server directory from source to destination for PULL direction."""
    clear_directory_pull(args, dest_server_root, name)

    print(f"{print_prefix}Recursively copying SMP {name} directory to {SERVER_TYPE[args.direction]}{name}: "
          f"{source_server_root.removeprefix(PTERO_ROOT)} -> {dest_server_root.removeprefix(PTERO_ROOT)}")
    if should_sync:
        shutil.copytree(source_server_root, dest_server_root, dirs_exist_ok=True)
    else:
        print_directory_contents(source_server_root)

    stage_icon = os.path.join(dest_server_root, "server-icon-staging.png")
    final_icon = os.path.join(dest_server_root, "server-icon.png")

    if os.path.exists(stage_icon):
        print(f"{print_prefix}Overwriting {final_icon.removeprefix(PTERO_ROOT)} with {stage_icon.removeprefix(PTERO_ROOT)}")
        if should_sync:
            shutil.copy2(stage_icon, final_icon)


def sync_push(args, cfg, name, source_server_root, dest_server_root):
    """Sync selected files from source to destination for PUSH direction."""
    push_paths = list(cfg["replacements"].get("allowed_push_paths", []))
    push_files = list(cfg["replacements"].get("allowed_push_files", []))
    push_filetypes = list(cfg["replacements"].get("allowed_push_filetypes", []))

    print(clifmt.LIGHT_GRAY + f"Allowed paths: {push_paths}") 
    print(clifmt.LIGHT_GRAY + f"Allowed files:", push_files) 
    print(clifmt.LIGHT_GRAY + f"Allowed filetypes:", push_filetypes) 

    clear_directory_push(dest_server_root, push_paths, push_files)

    for root, dirs, files in os.walk(source_server_root):
        rel_path = os.path.relpath(root, source_server_root)
        dest_path = os.path.join(dest_server_root, '' if rel_path == '.' else rel_path)

        last_push_time = cfg["meta"].get("last_push_files", 0)

        for file in files:
            source_file = os.path.join(root, file)
            dest_file = os.path.join(dest_path, file)

            if should_push_file(dest_file, push_paths, push_filetypes, push_files):
                if file_newer_than(file, last_push_time):
                    print(f"{print_prefix}Warning! {dest_file.removeprefix(PTERO_ROOT)} is newer than {source_file.removeprefix(PTERO_ROOT)} that is being pushed. Will not push.")
                else:
                    print(f"{print_prefix}Copying {SERVER_TYPE[args.direction]}{name} {source_file.removeprefix(PTERO_ROOT)} -> {dest_file.removeprefix(PTERO_ROOT)}")
                    if should_sync:
                        os.makedirs(dest_path, exist_ok=True)
                        shutil.copy2(source_file, dest_file)


def should_push_file(file, push_paths, push_filetypes, push_files):
    """Return True if a file should be pushed based on path, extension, and exemption rules."""
    if substring_in_string(push_paths, file) or substring_in_string(push_files, file) or file_has_extension(file, push_filetypes):
            return True
    return False
    
def clear_directory_pull(args, directory, name):
    """Remove all files/dirs inside `directory` when pulling (full wipe)."""
    
    rel_base = directory.removeprefix(PTERO_ROOT)

    print(f"{print_prefix}Deleting entire contents of {SERVER_TYPE[args.direction]}{name}: {rel_base}")
    print_directory_contents(directory)

    if should_sync:
        for item in os.listdir(directory):
            path = os.path.join(directory, item)
            if os.path.isfile(path) or os.path.islink(path):
                os.remove(path)
                pass
            elif os.path.isdir(path):
                shutil.rmtree(path)
                pass

def clear_directory_push(directory, push_paths, push_files):
    """Remove allowed files/dirs inside `directory` when pushing (selective delete)."""

    for root, dirs, files in os.walk(directory, topdown=True):
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            if substring_in_string(push_paths, dir_path):
                print(f"{print_prefix}Deleting dir: {dir_path.removeprefix(PTERO_ROOT)}")
                if should_sync:
                    try:
                        shutil.rmtree(dir_path)
                    except OSError:
                        print(f"Could not remove non-empty or locked dir: {dir_path.removeprefix(PTERO_ROOT)}")
        for file in files:
            path = os.path.join(root, file)
            is_plugins_folder = root.rstrip("/\\").endswith("/plugins")
            if substring_in_string(push_files, path) or (is_plugins_folder and file.lower().endswith(".jar")):
                print(f"{print_prefix}Deleting file: {path.removeprefix(PTERO_ROOT)}")
                if should_sync:
                    os.remove(path)


def update_config_files(args, source_servers, dest_servers, replacements, exempt_paths):
    """Apply replacements to config files in destination folders."""

    print(clifmt.WHITE + "Updating config files...")
    count = 0  # Track how many files were (or would be) updated
    f = "files" if count != 1 else "file" # Setup ternary vars for print

    servers_to_check = servers_to_log = dest_servers
    if args.dry_run and not args.update_only:
        servers_to_check = source_servers # in this case, the files wouldn't be copied yet, so check the source server

    # Loop over each server name in the destination server map
    for server_name in servers_to_check:
        # Construct full path to the server's config files
        print(clifmt.WHITE + f"Checking {SERVER_TYPE[args.direction]}{server_name} server: " + PTERO_ROOT + servers_to_log[server_name])

        # Walk through all directories and files within the server path
        for root, dirs, files in os.walk(PTERO_ROOT + servers_to_check[server_name]):
            for filename in files:
                if filename.endswith((".conf", ".txt, .properties", ".yml", "yaml")):
                    path = os.path.join(root, filename)
                    # Attempt to process the file; increment count if it changed
                    if process_config_file(args, path, replacements, exempt_paths, servers_to_check[server_name], servers_to_log[server_name]):
                        count += 1


    # Summarize number of files updated or that would be updated
    print(f"{clicolor}{print_prefix}Updated " + f"{count} " + f)


def process_config_file(args, path, replacements, exempt_paths, check_server, log_server):
    """Apply replacements to a config file if changes are needed."""

    # Open the file at 'path' and read its entire content.
    with open(path) as f:
        content = f.read()

    # Initialize new_content with the original content and prepare a list to track changes.
    new_content = content
    changes = []

    # Loop through each key-value pair in the replacements dictionary.
    for key, value in replacements.items():
        # If the current key is found in the content, record the change and perform the replacement.
        if key in new_content:
            changes.append(key + " -> " + value)
            new_content = new_content.replace(key, value)

    # Only continue if changes were made.
    if new_content != content:

        # Resolve short path for concise console logging
        print_path = path.removeprefix(PTERO_ROOT).replace(check_server, log_server)

        # Check if the file's path should be exempted from processing.
        if substring_in_string(exempt_paths, path):
                print(clifmt.LIGHT_GRAY +
                    f"{print_prefix}Skipping {print_path} as it contains an excluded directory or filetype"
                )
        else:
            print(clicolor +
                f"{print_prefix}Writing new content to {print_path} (changes: {', '.join(changes)})"
            )
            if should_sync:
                with open(path, "w") as f:
                    f.write(new_content)
            # Return True to indicate that changes were made.
            return True
    # Return False if no changes were made.
    return False


def update_sync_timestamps(args, cfg):
    """Save timestamp info to our config file after a successful operation"""

    sync_time = int(time.time())
    cfg["meta"] = cfg.get("meta", {})

    # Update 'meta' array in config file with new timestamps
    cfg["meta"]["last_" + args.direction + "_cfg"] = sync_time
    if not args.update_only:
        cfg["meta"]["last_" + args.direction + "_files"] = sync_time
    print(
        f"Updating config.yml with last {args.direction} timestamp: {sync_time}"
    )

    # Update config file with new 'meta' values
    config.set_config(cfg)
