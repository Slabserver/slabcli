import os
import time
import shutil
import yaml
from slabcli import config
from slabcli.common.fmt import clifmt

PUSH = "push"
PULL = "pull"

ptero_root = "/srv/daemon-data/"
server_type = {PUSH: "SMP ", PULL: "test-"}
server_directions = {PUSH: ("staging", "prod"), PULL: ("prod", "staging")}

def run(args, cfg):
    """Syncs Staging <-> Production servers depending on direction.

    This function performs two main steps:
    1. Sync files from source to destination servers based on the given direction (PUSH or PULL).
    2. Apply config replacements from config.yml to ensure servers are set up correctly post-sync.
    """

    # Determine source and destination servers and their replacement mappings,
    # based on sync direction (PUSH = staging → production, PULL = production → staging).
    try:
        source, dest = server_directions[args.direction]
    except KeyError:
        raise ValueError(f"Unknown direction: {args.direction}")
    
    # Build list of paths to exclude from processing (e.g. world files or user-specified paths)
    exempt_paths = list(cfg["replacements"].get("exempt_" + args.direction + "_paths", []))

    replacements, missing_keys = config.compute_config_replacements(
        cfg["replacements"].get(source, {}),
        cfg["replacements"].get(dest, {})
    )
    source_servers = cfg["servers"].get(source, {})
    dest_servers = cfg["servers"].get(dest, {})

    # Validate that all necessary replacement keys are present
    if missing_keys:
        raise ValueError("Cannot update servers: missing replacement keys in config.yml")

    world_names = list(cfg["replacements"].get("world_names", {}).values())

    # Build list of paths and filetypes to include for push processing (e.g. plugins and datapacks)
    push_paths = list(cfg["replacements"].get("allowed_push_paths", []))
    push_files = list(cfg["replacements"].get("allowed_push_files", []))
    push_filetypes = list(cfg["replacements"].get("allowed_push_filetypes", []))

    # if args.debug:
    # Debug output to verify the setup before proceeding
    print(clifmt.LIGHT_GRAY + "replacements dict =", replacements)
    print(clifmt.LIGHT_GRAY + "args.direction =", args.direction)
    print(clifmt.LIGHT_GRAY + "source_servers =", source_servers)
    print(clifmt.LIGHT_GRAY + "dest_servers =", dest_servers)
    print(clifmt.LIGHT_GRAY + "exempt paths =", exempt_paths)
    print(clifmt.LIGHT_GRAY + "world names =", world_names)
    print(clifmt.LIGHT_GRAY + "allowed push paths =", push_paths) 
    print(clifmt.LIGHT_GRAY + "allowed push files =", push_files) 
    print(clifmt.LIGHT_GRAY + "allowed push filetypes =", push_filetypes) 
        # return

    # Step 1: Sync files from source to destination unless we're in update-only mode
    if not args.update_only:
        sync_server_files(args, cfg, source_servers, dest_servers)

    # Step 2: Update server config files with any replacements
    update_config_files(args, source_servers, dest_servers, replacements, exempt_paths)

    # Step 3: Log or persist the timestamp of this sync operation
    if not args.dry_run:
        update_sync_timestamps(args, cfg)


def sync_pull(args, cfg, name, source_server_root, dest_server_root):
    """Sync an entire server directory from source to destination for PULL direction."""
    clear_directory_pull(args, dest_server_root, name)

    src_rel = source_server_root.removeprefix(ptero_root)
    dst_rel = dest_server_root.removeprefix(ptero_root)

    if args.dry_run:
        print(f"[DRY RUN] Would copy entire {server_type[args.direction]}{name} directory: {src_rel} -> {dst_rel}")
        print_directory_listing(source_server_root)
    else:
        print(f"Copying entire {server_type[args.direction]}{name} directory: {src_rel} -> {dst_rel} (commented out)")
        # shutil.copytree(source_server_root, dest_server_root, dirs_exist_ok=True)


def sync_push(args, cfg, name, source_server_root, dest_server_root):
    """Sync selected files from source to destination for PUSH direction."""
    push_paths = list(cfg["replacements"].get("allowed_push_paths", []))
    push_files = list(cfg["replacements"].get("allowed_push_files", []))
    push_filetypes = list(cfg["replacements"].get("allowed_push_filetypes", []))

    clear_directory_push(args, dest_server_root, push_paths, push_files)

    for root, dirs, files in os.walk(source_server_root):
        rel_path = os.path.relpath(root, source_server_root)
        dest_path = os.path.join(dest_server_root, '' if rel_path == '.' else rel_path)

        for file in files:
            source_file = os.path.join(root, file)
            dest_file = os.path.join(dest_path, file)

            if should_push_file(dest_path, file, push_paths, push_filetypes, push_files):
                if args.dry_run:
                    print(f"[DRY RUN] Would copy {server_type[args.direction]}{name} {source_file.removeprefix(ptero_root)} -> {dest_file.removeprefix(ptero_root)}")
                else:
                    print(f"Copying {server_type[args.direction]}{name} {source_file.removeprefix(ptero_root)} -> {dest_file.removeprefix(ptero_root)} (commented out)")
                    # os.makedirs(dest_path, exist_ok=True)
                    # shutil.copy2(source_file, dest_file)


def should_push_file(path, file, push_paths, push_filetypes, push_files):
    """Return True if a file should be pushed based on path, extension, and exemption rules."""
    if substring_in_path(push_paths, path) or substring_in_path(push_files, file) or has_file_extension(file, push_filetypes):
        return True
    return False


def sync_server_files(args, cfg, source_servers, dest_servers):
    """Dispatch sync by direction (PULL or PUSH)."""
    for name in source_servers:
        source_server_root = ptero_root + source_servers[name]
        dest_server_root = ptero_root + dest_servers.get(name, "")

        if not dest_server_root:
            print(f"Skipping {name}, no matching destination.")
            continue
        if not os.path.exists(dest_server_root):
            raise FileNotFoundError(f"Destination path does not exist: {dest_server_root}")

        if args.direction == PULL:
            sync_pull(args, cfg, name, source_server_root, dest_server_root)
        elif args.direction == PUSH:
            sync_push(args, cfg, name, source_server_root, dest_server_root)


def print_directory_listing(base_dir):
    for item in os.listdir(base_dir):
        full_path = os.path.join(base_dir, item)
        suffix = "/..." if os.path.isdir(full_path) else ""
        print(f"  {full_path.removeprefix(ptero_root)}{suffix}")
    
def clear_directory_pull(args, directory, name):
    """Remove all files/dirs inside `directory` when pulling (full wipe)."""
    rel_base = directory.removeprefix(ptero_root)

    if args.dry_run:
        print(f"[DRY RUN] Would delete entire contents of {server_type[args.direction]}{name}: {rel_base}")
    else:
        print(f"Deleting entire contents of {rel_base} (commented out)")

    print_directory_listing(directory)

    if not args.dry_run:
        for item in os.listdir(directory):
            path = os.path.join(directory, item)
            if os.path.isfile(path) or os.path.islink(path):
                # os.remove(path)
                pass
            elif os.path.isdir(path):
                # shutil.rmtree(path)
                pass

def clear_directory_push(args, directory, push_paths, push_files):
    """Remove allowed files/dirs inside `directory` when pushing (selective delete)."""
    for root, dirs, files in os.walk(directory, topdown=True):
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            if substring_in_path(push_paths, dir_path):
                if args.dry_run:
                    print(f"[DRY RUN] Would delete dir: {dir_path.removeprefix(ptero_root)}")
                else:
                    try:
                        print(f"Deleted directory: {dir_path} (commented out)")
                        # shutil.rmtree(dir_path)
                    except OSError:
                        print(f"Could not remove non-empty or locked dir: {dir_path.removeprefix(ptero_root)}")
        for file in files:
            path = os.path.join(root, file)
            is_plugins_folder = root.rstrip("/\\").endswith("/plugins")
            if substring_in_path(push_files, path) or (is_plugins_folder and file.lower().endswith(".jar")):
                if args.dry_run:
                    print(f"[DRY RUN] Would delete file: {path.removeprefix(ptero_root)}")
                else:
                    print(f"Deleted file: {path.removeprefix(ptero_root)} (commented out)")
                    # os.remove(path)


def update_config_files(args, source_servers, dest_servers, replacements, exempt_paths):
    """Apply replacements to config files in destination folders."""

    print(clifmt.WHITE + "Updating config files...")
    count = 0  # Track how many files were (or would be) updated

    servers_to_check = servers_to_log = dest_servers
    # if we're dry running a full pull, the files aren't actually copied yet, so we need to check the source server
    if args.dry_run and not args.update_only:
        servers_to_check = source_servers

    # Loop over each server name in the destination server map
    for name in servers_to_check:
        # Construct full path to the server's config files
        print(clifmt.WHITE + f"Checking {server_type[args.direction]}{name} server: " + ptero_root + servers_to_log[name])

        # Walk through all directories and files within the server path
        for root, dirs, files in os.walk(ptero_root + servers_to_check[name]):
            for filename in files:
                if filename.endswith((".conf", ".txt, .properties", ".yml", "yaml")):
                    path = os.path.join(root, filename)
                    # Attempt to process the file; increment count if it changed
                    if process_config_file(args, path, replacements, exempt_paths, servers_to_check[name], servers_to_log[name]):
                        count += 1


    f = "files" if count != 1 else "file" # Setup ternary vars for print

    # Summarize how many files were updated or would be updated
    if args.dry_run:
        print(clifmt.YELLOW + "[DRY RUN] Would have updated " + f"{count} " + f)
    else:
        print(clifmt.GREEN + "Updated " + f"{count} " + f)


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
        print_path = path.removeprefix(ptero_root)
        print_path = print_path.replace(check_server, log_server)

        # Check if the file's path should be exempted from processing.
        if substring_in_path(exempt_paths, path):
            # If running in dry-run mode, print a message indicating that the file would be skipped.
            if args.dry_run:
                print(clifmt.LIGHT_GRAY +
                    f"[DRY RUN] Would skip updating {print_path} as it contains an excluded directory or filetype"
                )
            else:
                # In non-dry-run mode, print a message that the file is being skipped.
                print(clifmt.LIGHT_GRAY +
                    f"Skipping {print_path} as it contains an excluded directory or filetype"
                )
        else:
            # If the file is not exempted and it's a dry-run, indicate that changes would be written.
            if args.dry_run:
                print(clifmt.YELLOW +
                    f"[DRY RUN] Would write new content to {print_path} (changes: {', '.join(changes)})"
                )
            else:
                # Otherwise, write the new content back to the file and print an update message.
                print(clifmt.GREEN +f"Writing new content to {print_path} (changes: {', '.join(changes)})")
                with open(path, "w") as f:
                    f.write(new_content)
            # Return True to indicate that changes were made.
            return True
    # Return False if no changes were made.
    return False


def substring_in_path(substrings, path):
    """Loop through a list of substrings to determine if any substring is found within a directory path"""

    substrings_to_check = substrings or []  # empty list to avoid errors
    for substring in substrings_to_check:
        if substring in path:
            return True
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
    config_path = config.get_config_path()
    with open(config_path, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False)

def has_file_extension(filename, file_extensions):
    """Return True if filename ends with one of the given extensions."""
    return filename.lower().endswith(tuple(ext.lower() for ext in file_extensions))