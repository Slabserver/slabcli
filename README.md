# SlabCLI

## A simple CLI tool for managing Slabserver server state and more

This repo serves as a simple and basic CLI for the Slabserver Staff Team to
run python tasks for our servers, such as server promotions, external backups,
and potentially even more in the future. 

While this could have simply been a couple of python / shell scripts, that wouldn't
have been _cool_, and so instead we've developed a simple command tool that provides
us with arguments, help flags, good extensibility, and the aforementioned cool factor.

This is very much in early development, and any / all contributions are welcome - so long
as they are cool.

---

## Installation

Simply run `install.sh`, which will setup dependencies and install the `slabcli` in editable mode.

As of the time of writing, this CLI is located on the dedi server in `/tools/slabcli`

## Config

SlabCLI depends on a `config.yml` file within the `/slabcli` subdirectory in order to do most tasks.
This should exist on the dedi server at all times, and if you don't have one, then:
- You've lost yours, and another member of staff should have a copy.
- You never had one, and another member of staff should have a copy.
- You never had one, and you're not staff - oops, go away.
- All the staff have lost it, and we're a bit screwed.

Until such a time that Slabserver is running on Minecraft version 1.21.8 or above, assume that the `config.yml` file
is total bullshit, completely wrong, untested hacky schlock, and will be subject to change at any point.

### Example Config

<details>
<summary>Click to view a sample <code>config.yml</code> file:</summary>
<br>

```
meta:
  last_pull_cfg: 1754321001
  last_pull_files: 1754321000
replacements:
  exempt_paths:
  - example_config_always_up_to_date!.yml
  - PassageWarden/config.yml
  prod:
    address:
      proxy: slabserver.org:25565
      resource: 172.18.0.1:20010
      survival: 172.18.0.1:20000
    advancedban:
      database: s1_advancedban
      host: 172.17.0.1
      password: definitelyrealpassword
      port: 8080
    discordsrv:
      bot_token: psA14OKjL82XoQP.QPKZfzg0IBJ.fAk3
      chat_channel: '1268892101999984650'
      logs_channel: '596920414232510465'
    plan:
      database: s1_plan
      host: 172.18.0.1
      port: 'Port: 25678'
  staging:
    address:
      proxy: slabserver.org:25675
      resource: 172.18.0.1:40010
      survival: 172.18.0.1:40000
    advancedban:
      database: s11_advancedban
      host: 172.18.0.1
      password: evenmorerealpasswordbutitsstaging
      port: 8181
    discordsrv:
      bot_token: r3aL.WStR12IA8oJDVSMZSp0ucAkYx79
      chat_channel: '146702455487463424'
      logs_channel: '146701388234227712'
    plan:
      database: s11_plan
      host: 172.18.0.1
      port: 'Port: 25999'
  world_names:
    resource_world: resource-world
    survival_world: Slabserver
servers:
  prod:
    proxy: dea98676-757f-47b1-8168-97474c906961
    resource: d29b3b02-b673-4ec0-96de-9c163378d476
    survival: c58cb5a9-516c-4d81-b2e2-f70aa2959ee8
  staging:
    proxy: 73480cd8-d9b8-4ddd-ac3d-165fdf9a5b0b
    resource: c2945d68-2eb3-48da-8ba8-3e781657c970
    survival: 12df443e-53c8-43f3-8481-515449461e11
```
</details>



## Limitations

Anything directly outside the file system of the server must be created ahead of time for a new 'Staging' server to work. This includes, but is probably not exclusive to:
 - Databases
 - Domains

### Database Contents
- Any plugin that uses a database will not have its data synced by SlabCLI. We'd like to address this in the future, but at present this will most notably affect any core Slabserver functionality or plugins that utilise databases, such as those described in our [architecture](https://slabserver.org/documentation/minecraft/server-architecture/).
