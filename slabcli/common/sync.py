import os
import shutil
from slabcli import config


def run(args):
    cfg = config.load_config()
    direction = args.direction

    if direction == "up":
        source_servers = cfg["servers"].get("staging", {})
        dest_servers = cfg["servers"].get("prod", {})
        replacements, missing_keys = config.compute_config_replacements(
            cfg["replacements"].get("prod", {}),
            cfg["replacements"].get("staging", {})
        )
    elif direction == "down":
        source_servers = cfg["servers"].get("prod", {})
        dest_servers = cfg["servers"].get("staging", {})
        replacements, missing_keys = config.compute_config_replacements(
            cfg["replacements"].get("staging", {}),
            cfg["replacements"].get("prod", {})
        )
    else:
        raise ValueError(f"Unknown direction: {direction}")

    if missing_keys:
        raise ValueError("Cannot update servers: missing replacement keys in config.yml")
    
    # Debug prints
    # print("Derived replacements dict:", replacements)
    # print("args.direction =", args.direction)
    # print("source_servers =", source_servers)
    # print("dest_servers =", dest_servers)

    sync_server_files(source_servers, dest_servers, args.dry_run)
    update_config_files(dest_servers, replacements, args.dry_run)


def sync_server_files(source_servers, dest_servers, dry_run):
    """Clear destination dirs and sync files from source."""
    for name in source_servers:
        src_root = "/srv/daemon-data/" + source_servers[name]
        dst_root = "/srv/daemon-data/" + dest_servers.get(name, "")

        if not dst_root:
            print(f"Skipping {name}, no matching destination.")
            continue

        if not os.path.exists(dst_root):
            raise FileNotFoundError(f"Destination path does not exist: {dst_root}")

        if dry_run:
            print(f"[DRY RUN] Would clear all files in {dst_root}")
        else:
            clear_directory_contents(dst_root, dry_run=dry_run)

        if dry_run:
            print(f"[DRY RUN] Would copy {src_root} -> {dst_root}")
        else:
            print(f"Copying files from {src_root} to {dst_root}...")
            print(f"[DEVNOTE] Copying disabled during dev")
            for root, dirs, files in os.walk(src_root):
                rel_path = os.path.relpath(root, src_root)
                dst_path = os.path.join(dst_root, rel_path)
                os.makedirs(dst_path, exist_ok=True)

                for file in files:
                    src_file = os.path.join(root, file)
                    dst_file = os.path.join(dst_path, file)
                    print(f"Copying {src_file} -> {dst_file}")
                    # shutil.copy2(src_file, dst_file)  # DISABLED DURING DEV


def update_config_files(dest_servers, replacements, dry_run):
    """Apply replacements to config files in destination folders."""
    print("Updating config files...")
    count = 0
    for name in dest_servers:
        print("checking server: " + dest_servers[name])
        server_path = "/srv/daemon-data/" + dest_servers[name]
        for root, dirs, files in os.walk(server_path):
            for filename in files:
                if filename.endswith((".yml", ".conf", ".txt")):
                    path = os.path.join(root, filename)
                    with open(path) as f:
                        content = f.read()

                    new_content = content
                    for key in replacements:
                        new_content = new_content.replace(key, replacements[key])

                    if new_content != content:
                        if dry_run:
                            print(f"[DRY RUN] Would write new content to {path}")
                        else:
                            print(f"Writing new content to {filename}")
                            print(f"[DEVNOTE] Writing disabled during dev")
                        #     with open(path, "w") as f:  # DISABLED DURING DEV
                        #         f.write(new_content)    # DISABLED DURING DEV
                        count += 1

    if dry_run:
        print(f"Would have updated {count} files")
    else:
        print(f"Updated {count} files")


def clear_directory_contents(directory, dry_run=False):
    """Remove all files/dirs inside `directory` but not the directory itself."""
    for entry in os.listdir(directory):
        path = os.path.join(directory, entry)
        if os.path.isdir(path):
            if dry_run:
                print(f"[DRY RUN] Would delete directory: {path}")
            else:
                shutil.rmtree(path)
        else:
            if dry_run:
                print(f"[DRY RUN] Would delete file: {path}")
            else:
                os.remove(path)
