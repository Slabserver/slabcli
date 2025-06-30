import os
import shutil
from slabcli import config


def run(args):
    # Load config (from fixed location)
    cfg = config.load_config()
    prod_servers = cfg["servers"].get("prod", {})
    staging_servers = cfg["servers"].get("staging", {})

    prod_cfg = cfg["replacements"].get("prod", {})
    staging_cfg = cfg["replacements"].get("staging", {})

    if args.direction == "up":
        source_servers = staging_servers
        dest_servers = prod_servers
        replacements, missingKeys = config.compute_config_replacements(prod_cfg, staging_cfg)
    elif args.direction == "down":
        source_servers = prod_servers
        dest_servers = staging_servers
        replacements, missingKeys = config.compute_config_replacements(staging_cfg, prod_cfg)
    else:
        raise ValueError(f"Unknown direction: {args.direction}")

    if missingKeys:
        raise ValueError(f"Cannot update servers: missing replacement keys in config.yml")
    
    # Debug prints
    # print("Derived replacements dict:", replacements)
    # print("args.direction =", args.direction)
    # print("source_servers =", source_servers)
    # print("dest_servers =", dest_servers)

    # TODO: this won't delete any files in the destination that don’t exist in the source
    # TODO: as prod/staging are meant to be exact copies of one another, we should do this.
    for name in source_servers:
        src_root = "/srv/daemon-data/" + source_servers[name]
        dst_root = "/srv/daemon-data/" + dest_servers.get(name, "")

        if not dst_root:
            print(f"Skipping {name}, no matching destination.")
            continue
        
        if not os.path.exists(dst_root):
            raise FileNotFoundError(f"Destination path does not exist: {dst_root}")
            
        if args.dry_run:
            print(f"[DRY RUN] Would clear all files in {dst_root}")
        else:
            # Clear all destination files ahead of copying from source
            clear_directory_contents(dst_root, dry_run=args.dry_run)

        if args.dry_run:
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
                    # shutil.copy2(src_file, dst_file) #DISABLED DURING DEV

    print("Updating config files...")
    count = 0
    for s in dest_servers:
        print("checking server: " + dest_servers[s])
        for root, dirs, files in os.walk("/srv/daemon-data/" + dest_servers[s]):
            for filename in files:
                if filename.endswith((".yml", ".conf", ".txt")):
                    path = os.path.join(root, filename)
                    with open(path) as f:
                        content = f.read()

                    new_content = content
                    for key in replacements:
                        new_content = new_content.replace(key, replacements[key])

                    if new_content != content:
                        if args.dry_run:
                            print(f"[DRY RUN] Would write new content to {path}")
                        else:
                            print(f"Writing new content to {filename}")
                            print(f"[DEVNOTE] Writing disabled during dev")
                        #     with open(path, "w") as f:  #DISABLED DURING DEV
                        #         f.write(new_content)    #DISABLED DURING DEV
                        count += 1

    if args.dry_run:
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