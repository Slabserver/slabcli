import os
import shutil
from slabcli import config


def run(args):
    cfg = config.load_config()

    if args.direction == "up":
        source_servers = cfg["servers"].get("staging", {})
        dest_servers = cfg["servers"].get("prod", {})
        replacements, missing_keys = config.compute_config_replacements(
            cfg["replacements"].get("prod", {}),cfg["replacements"].get("staging", {})
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

    if missing_keys:
        raise ValueError("Cannot update servers: missing replacement keys in config.yml")
    
    exempt_paths = cfg["replacements"].get("exempt_paths", [])
    
    if not args.sync_worlds:
        exempt_paths += cfg["replacements"].get("world_names", [])
    
    # Debug prints
    print("Derived replacements dict:", replacements)
    print("args.direction =", args.direction)
    print("source_servers =", source_servers)
    print("dest_servers =", dest_servers)

    if args.update_only == False:
        sync_server_files(source_servers, dest_servers, exempt_paths, args.dry_run)
    if args.dry_run and args.sync_worlds:
        # with a dry run the files aren't copied over, so we need to check any replacements against production
        update_config_files(source_servers, replacements, exempt_paths, args.dry_run)
    else:
        update_config_files(dest_servers, replacements, exempt_paths, args.dry_run)
    print("exempt paths =", exempt_paths)

def sync_server_files(source_servers, dest_servers, exempt_paths, dry_run):
    """Clear destination dirs and sync files from source."""
    for name in source_servers:
        src_root = "/srv/daemon-data/" + source_servers[name]
        dst_root = "/srv/daemon-data/" + dest_servers.get(name, "")

        if not dst_root:
            print(f"Skipping {name}, no matching destination.")
            continue

        if not os.path.exists(dst_root):
            raise FileNotFoundError(f"Destination path does not exist: {dst_root}")

        clear_directory_contents(dst_root, exempt_paths, dry_run)
        if dry_run:
            print(f"[DRY RUN] Would copy {src_root} -> {dst_root}")
        else:
            print(f"Copying files from {src_root} to {dst_root}...")
            for root, dirs, files in os.walk(src_root):
                rel_path = os.path.relpath(root, src_root)
                dst_path = os.path.join(dst_root, rel_path)
                
                if is_excluded(exempt_paths, dst_path):
                    if dry_run:
                        print(f"[DRY RUN] Would skip copying {dst_path} as it contains an excluded directory or filetype")
                    else:
                        print(f"Skipping copy of {dst_path} as it contains an excluded directory or filetype")
                    continue
                else:
                    os.makedirs(dst_path, exist_ok=True)
                    for file in files:
                        src_file = os.path.join(root, file)
                        dst_file = os.path.join(dst_path, file)
                        print(f"Copying {src_file} -> {dst_file}")
                        shutil.copy2(src_file, dst_file)

def clear_directory_contents(directory, exempt_paths, dry_run):
    """Remove all files/dirs inside `directory`, skipping any path that contains an excluded substring."""
    for root, dirs, files in os.walk(directory, topdown=False):
        for file in files:
            path = os.path.join(root, file)
            if is_excluded(exempt_paths, path) or file.lower().endswith(".db"):
                if dry_run:
                    print(f"[DRY RUN] Would skip {path} as it contains an excluded directory or filetype")
                continue
            if dry_run:
                print(f"[DRY RUN] Would delete file: {path}")
            else:
                os.remove(path)

        for dir in dirs:
            dir_path = os.path.join(root, dir)
            if is_excluded(exempt_paths, dir_path):
                continue
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
    print("Updating config files...")
    count = 0
    for name in dest_servers:
        server_path = "/srv/daemon-data/" + dest_servers[name]
        print("checking server: " + dest_servers[name])
        for root, dirs, files in os.walk(server_path):
            for filename in files:
                if filename.endswith((".conf", ".txt, .properties", ".yml", "yaml")):
                    path = os.path.join(root, filename)
                    if process_config_file(path, replacements, exempt_paths, dry_run):
                        count += 1

    if dry_run:
        print(f"Would have updated {count} files")
    else:
        print(f"Updated {count} files")
        
def process_config_file(path, replacements, exempt_paths, dry_run):
    """Apply replacements to a config file if changes are needed."""
    
    with open(path) as f:
        content = f.read()

    new_content = content
    changes = []
    
    for key, value in replacements.items():
        if key in new_content:
            changes.append(value)
            new_content = new_content.replace(key, value)

    if new_content != content:
        if is_excluded(exempt_paths, path):
            if dry_run:
                print(f"[DRY RUN] Would skip updating {path} as it contains an excluded directory or filetype")
            else:
                print(f"Skipping {path} as it contains an excluded directory or filetype")
        else:
            if dry_run:
                print(f"[DRY RUN] Would write new content to {path} (changes: {', '.join(changes)})")
            else:
                print(f"Writing new content to {path} (changes: {', '.join(changes)})")
                with open(path, "w") as f:
                    f.write(new_content)
        return True
    return False

def is_excluded(exclude_substrings, path):
    exclude_substrings = exclude_substrings or []
    return any(excl in path for excl in exclude_substrings)