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
        replacements = config.compute_config_replacements(prod_cfg, staging_cfg)
    elif args.direction == "down":
        source_servers = prod_servers
        dest_servers = staging_servers
        replacements = config.compute_config_replacements(staging_cfg, prod_cfg)
    else:
        raise ValueError(f"Unknown direction: {args.direction}")

    # print("Derived replacements dict:", replacements)
    print("args.direction =", args.direction)
    # print("source_servers =", source_servers)
    # print("dest_servers =", dest_servers)

    # note: this won't delete any files in the dest that don’t exist in the src - we may wish to change that
    print("Copying files from source to destination servers...")
    for name in source_servers:
        src_root = "/srv/daemon-data/" + source_servers[name]
        dst_root = "/srv/daemon-data/" + dest_servers.get(name, "")

        if not dst_root:
            print(f"Skipping {name}, no matching destination.")
            continue

        for root, dirs, files in os.walk(src_root):
            rel_path = os.path.relpath(root, src_root)
            dst_path = os.path.join(dst_root, rel_path)

            os.makedirs(dst_path, exist_ok=True)

            for file in files:
                src_file = os.path.join(root, file)
                dst_file = os.path.join(dst_path, file)
                if args.dry_run:
                    print(f"[DRY RUN] Would copy {src_file} -> {dst_file}")
                # else:
                #     print(f"Copying {src_file} -> {dst_file}")
                #     shutil.copy2(src_file, dst_file)

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
                        print(path)
                        if args.dry_run:
                            print(f"[DRY RUN] Would write new content to {filename}")
                        # else:
                        #     print(f"Writing new content to {filename}")
                        #     with open(path, "w") as f:
                        #         f.write(new_content)
                        count += 1

    if args.dry_run:
        print(f"Would have updated {count} files")
    else:
        print(f"Updated {count} files")
