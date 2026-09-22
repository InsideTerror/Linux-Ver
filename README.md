# Linver 2

A Linux equivalent of `winver.exe`: a small graphical utility that presents the
current Linux distribution and useful system information in one clean dialog.

## Features

- Distribution name, version, codename and build information
- Kernel version and architecture
- CPU model and logical/physical CPU counts
- RAM usage
- Root filesystem usage
- Hostname and current user
- Desktop environment and session type
- Detected package managers
- System uptime
- Remote distro logos (not bundled locally)
- Copy system details to clipboard
- Open the distribution's official website
- `--cli` mode for terminal output
- `--no-network` mode for offline/privacy-conscious use

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python linver.py
```

For terminal mode:

```bash
python linver.py --cli
```

For an offline run without attempting to fetch a logo:

```bash
python linver.py --no-network
```

## Packaging

PyInstaller works well for a single-file Linux build:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name Linver linver.py
```

The resulting executable will be in `dist/`.

Because the distribution logos are remote, the packaged program does not need
an image asset folder. If the network is unavailable, Linver simply falls back
to the penguin placeholder.

## Logo sources

The application uses SVG assets hosted by the Simple Icons CDN. Examples:

- Ubuntu: https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/ubuntu.svg
- Debian: https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/debian.svg
- Fedora: https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/fedora.svg
- Arch Linux: https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/archlinux.svg
- Linux Mint: https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/linuxmint.svg
- openSUSE: https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/opensuse.svg

Official branding/artwork pages should be consulted for trademark/licensing
requirements if the program is distributed publicly.

## Notes

This project deliberately avoids shelling out to `neofetch`, `fastfetch`, etc.
It reads most information directly through Python and `psutil`, making it
self-contained and predictable.
