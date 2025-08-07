import os
import time
import shutil
import yaml
from slabcli import config
from slabcli.common.fmt import clifmt

server_root = "/srv/daemon-data/"

def run(args, cfg):
    """Syncs Staging <-> Production servers depending on direction.

    This function performs two main steps:
    1. Sync files from source to destination servers based on the given direction ("up" or "down").
    2. Apply config replacements from config.yml to ensure servers are set up correctly post-sync.
    """

    # Determine source and destination servers and their replacement mappings,
    # based on sync direction ("up" = staging → production, "down" = production → staging).
    if args.direction == "up":
        source_servers = cfg["servers"].get("staging", {})
        dest_servers = cfg["servers"].get("prod", {})
        replacements, missing_keys = config.compute_config_replacements(
            cfg["replacements"].get("prod", {}),
            cfg["replacements"].get("staging", {})
        )
    elif args.direction == "down":
        source_servers = cfg["servers"].get("prod", {})
        dest_servers = cfg["servers"].get("staging", {})
        replacements, missing_keys = config.compute_config_replacements(
            cfg["replacements"].get("staging", {}),
            cfg["replacements"].get("prod", {})
        )
    else:
        raise ValueError(f"Unknown direction: {args.direction}")

    # Validate that all necessary replacement keys are present
    if missing_keys:
        raise ValueError("Cannot update servers: missing replacement keys in config.yml")

    # Build list of paths to exclude from processing (e.g. world files or user-specified paths)
    exempt_paths = list(cfg["replacements"].get("exempt_paths", []))
    if not args.sync_worlds:
        # If world syncing is disabled, exclude all known world names from the replacement step
        exempt_paths += list(cfg["replacements"].get("world_names", {}).values())

    # Debug output to verify the setup before proceeding
    print(clifmt.LIGHT_GRAY + "replacements dict =", replacements)
    print(clifmt.LIGHT_GRAY + "args.direction =", args.direction)
    print(clifmt.LIGHT_GRAY + "source_servers =", source_servers)
    print(clifmt.LIGHT_GRAY + "dest_servers =", dest_servers)
    print(clifmt.LIGHT_GRAY + "exempt paths =", exempt_paths)
    print("")

    # Step 1: Sync files from source to destination unless we're in update-only mode
    if not args.update_only:
        sync_server_files(source_servers, dest_servers, exempt_paths, args.dry_run)

    # Step 2: Update server config files with replacements
    if args.dry_run and args.sync_worlds:
        # In dry run mode, no files are actually copied, so update the source instead
        update_config_files(source_servers, replacements, exempt_paths, args.dry_run)
    else:
        update_config_files(dest_servers, replacements, exempt_paths, args.dry_run)

    # Step 3: Log or persist the timestamp of this sync operation
    if not args.dry_run:
        update_sync_timestamps(args, cfg)


def sync_server_files(source_servers, dest_servers, exempt_paths, dry_run):
    """Clear destination dirs and sync files from source."""

    # Loop over each server name in the source server map
    for name in source_servers:
        # Construct full paths for source and destination directories
        source_server_root =  + source_servers[name]
        dest_server_root = "/srv/daemon-data/" + dest_servers.get(name, "")

        if not dest_server_root:
            print(f"Skipping {name}, no matching destination.")
            continue

        if not os.path.exists(dest_server_root):
            raise FileNotFoundError(f"Destination path does not exist: {dest_server_root}")

        # Clear the contents of the destination directory before syncing
        clear_directory_contents(dest_server_root, exempt_paths, dry_run)

        # If dry run, just print what would happen
        if dry_run:
            print(f"[DRY RUN] Would copy {source_server_root} -> {dest_server_root}")
        else:
            print(f"Copying files from {source_server_root} to {dest_server_root}...")

            # Walk through all directories and files in the source server path
            for root, dirs, files in os.walk(source_server_root):
                # Get the path relative to the source root
                rel_path = os.path.relpath(root, source_server_root)
                # Build the equivalent destination path
                dest_path = os.path.join(dest_server_root, rel_path)

                # Skip copying if this path should be excluded
                if is_excluded(exempt_paths, dest_path):
                    if dry_run:
                        print(
                            f"[DRY RUN] Would skip copying {dest_path} as it contains an excluded directory or filetype"
                        )
                    else:
                        print(
                            f"Skipping copy of {dest_path} as it contains an excluded directory or filetype"
                        )
                    continue
                else:
                    # Create the destination directory if it doesn't exist
                    os.makedirs(dest_path, exist_ok=True)

                    # Copy each file from source to destination
                    for file in files:
                        source_file = os.path.join(root, file)
                        dest_file = os.path.join(dest_path, file)
                        print(f"Copying {source_file} -> {dest_file}")
                        shutil.copy2(source_file, dest_file)


def clear_directory_contents(directory, exempt_paths, dry_run):
    """Remove all files/dirs inside `directory`, skipping any path that contains an excluded substring."""

    # Walk the directory tree from bottom to top so files are removed before their parent directories
    for root, dirs, files in os.walk(directory, topdown=False):

        # Process each file in the current directory
        for file in files:
            path = os.path.join(root, file)

            if is_excluded(exempt_paths, path) or file.lower().endswith(".db"):
                if dry_run:
                    print(
                        f"[DRY RUN] Would skip {path} as it contains an excluded directory or filetype"
                    )
                continue

            # If not a dry run, delete the file; otherwise, just print what would happen
            if dry_run:
                print(f"[DRY RUN] Would delete file: {path}")
            else:
                os.remove(path)

        # Process each subdirectory in the current directory
        for dir in dirs:
            dir_path = os.path.join(root, dir)

            # Skip the directory if it's excluded
            if is_excluded(exempt_paths, dir_path):
                continue

            # Attempt to remove the directory (only works if it's empty)
            if dry_run:
                print(f"[DRY RUN] Would delete dir: {dir_path}")
            else:
                try:
                    print(f"Deleting dir: {dir_path}")
                    os.rmdir(dir_path)
                except OSError:
                    print(f"Could not remove non-empty or locked dir: {dir_path}")


def update_config_files(dest_servers, replacements, exempt_paths, dry_run):
    """Apply replacements to config files in destination folders."""

    print(clifmt.WHITE + "Updating config files...")
    count = 0  # Track how many files were (or would be) updated

    # Loop over each server name in the destination server map
    for name in dest_servers:
        # Construct the full path to the server's config files
        server_path = "/srv/daemon-data/" + dest_servers[name]
        print(clifmt.WHITE + "checking server: " + dest_servers[name])

        # Walk through all directories and files within the server path
        for root, dirs, files in os.walk(server_path):
            for filename in files:
                if filename.endswith((".conf", ".txt, .properties", ".yml", "yaml")):
                    path = os.path.join(root, filename)
                    # Attempt to process the file; increment count if it changed
                    if process_config_file(path, replacements, exempt_paths, dry_run):
                        count += 1

    # Summarize how many files were updated or would be updated
    if dry_run:
        print(clifmt.BOLD + "Would have updated " + clifmt.YELLOW + f"{count} files")
    else:
        print(clifmt.BOLD + "Updated " + clifmt.GREEN + f"{count} files")


def process_config_file(path, replacements, exempt_paths, dry_run):
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
        short_path = path.removeprefix("/srv/daemon-data")

        # Check if the file's path should be exempted from processing.
        if is_excluded(exempt_paths, path):
            # If running in dry-run mode, print a message indicating that the file would be skipped.
            if dry_run:
                print(clifmt.NEGATIVE +
                    f"[DRY RUN] Would skip updating {short_path} as it contains an excluded directory or filetype"
                )
            else:
                # In non-dry-run mode, print a message that the file is being skipped.
                print(clifmt.NEGATIVE +
                    f"Skipping {short_path} as it contains an excluded directory or filetype"
                )
        else:
            # If the file is not exempted and it's a dry-run, indicate that changes would be written.
            if dry_run:
                print(clifmt.YELLOW +
                    f"[DRY RUN] Would write new content to {short_path} (changes: {', '.join(changes)})"
                )
            else:
                # Otherwise, write the new content back to the file and print an update message.
                print(clifmt.GREEN +f"Writing new content to {short_path} (changes: {', '.join(changes)})")
                with open(path, "w") as f:
                    f.write(new_content)
            # Return True to indicate that changes were made.
            return True
    # Return False if no changes were made.
    return False


def is_excluded(exclude_substrings, path):
    """Loop through a list of substrings to determine if any substring is found within a directory path"""

    exclude_substrings = exclude_substrings or []  # empty list to avoid errors
    
    for substring in exclude_substrings:
        if substring in path:
            return True

    return False


def update_sync_timestamps(args, cfg):
    """Save timestamp info to our config file after a successful operation"""

    # Update 'meta' array with new timestamps
    cfg["meta"] = cfg.get("meta", {})
    if args.direction == "down":
        if not args.update_only:
            cfg["meta"]["last_pull_files"] = int(time.time())
        cfg["meta"]["last_pull_cfg"] = int(time.time())
        print(
            f"Updating config.yml with last pull timestamp: {cfg['meta']['last_pull_cfg']}"
        )
    elif args.direction == "up":
        if not args.update_only:
            cfg["meta"]["last_push_files"] = int(time.time())
        cfg["meta"]["last_push_cfg"] = int(time.time())
        print(
            f"Updating config.yml with last push timestamp: {cfg['meta']['last_push_cfg']}"
        )
    # Update config file with new 'meta' values
    config_path = config.get_config_path()
    with open(config_path, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False)
