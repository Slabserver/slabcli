import os
from slabcli import config

def run(args):
    # Load config (from fixed location)
    cfg = config.load_config()
    prod_servers = cfg["servers"].get("prod", {})
    staging_servers = cfg["servers"].get("staging", {})

    prod_cfg = cfg["replacements"].get("prod", {})
    staging_cfg = cfg["replacements"].get("staging", {})
    if args.direction == "up":
        servers = prod_servers
        replacements = config.compute_config_replacements(staging_cfg, prod_cfg)
    elif args.direction == "down":
        servers = staging_servers
        replacements = config.compute_config_replacements(prod_cfg, staging_cfg)
    else:
        raise ValueError(f"Unknown direction: {args.direction}")
    print("Derived replacements dict:", replacements)
    print("args.direction =", args.direction)
    print("servers =", servers)

    print("Updating config files...")
    count = 0
    for key in servers:
        for root, dirs, files in os.walk("/srv/daemon-data/" + servers[key]):
            print("checking server: " + servers[key]) 
            for filename in files:
                if filename.endswith(".yml") or filename.endswith(".conf") or filename.endswith(".txt"):
                    path = os.path.join(root, filename)
                    file = open(path)
                    new_content = content = file.read()
                    file.close()
                    for key in replacements:
                        new_content = new_content.replace(key, replacements[key])
                    if new_content != content:
                        file = open(path, "w")
                        print(path) 
                        if args.dry_run:
                            print("would write new content: " + new_content in filename) 
                        else:
                            print("writing new content: " + new_content) 
                            # file.write(new_content)
                        file.close()
                        count += 1
    if args.dry_run:
        print("Would have updated {} files".format(count))
    else:
        print("Updated {} files".format(count))
