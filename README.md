# SlabCLI

## A simple CLI tool for managing Slabserver server state and more

This repo serves as a simple and basic CLI for the Slabserver Staff Team to
run python tasks for our servers, such as server promotions, external backups,
and potentially even more in the future. 

While this could have simply been a couple of python / shell scripts, that wouldn't
have been _cool_, and so instead we've developed a simple command tool that provides
us with arguments, help flags, good extensibility, and the aforementioned cool factor.

This is very much in early development, and any/all contributions are welcome - so long
as they are cool.

---

## Installation

Simply run `install.sh` to setup dependencies, and install the `slabcli` in editable mode.

## Config

SlabCLI depends on a `config.yml` file within the `/slabcli` directory in order to do most tasks.
This should exist on the dedi server at all times, and if you don't have one, then:
- You've lost yours, and another member of staff should have a copy.
- You never had one, and another member of staff should have a copy.
- You never had one, and you're not staff - oops, go away.
- All the staff have lost it, and we're a bit screwed.

Until such a time that Slabserver is running on Minecraft version 1.21.7 or above, assume that the `config.yml` file
is total bullshit, completely wrong, untested hacky schlock, and will be subject to change at any point.

## Limitations
```
TODO: write something more eloquent and insightful.

Current limitations of push and pull subcommands:
- Anything directly outside the file system of the server must be created
    - Databases
    - Domains
```