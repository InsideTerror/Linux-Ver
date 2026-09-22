import argparse
import datetime as dt
import getpass
import os
import platform
import shutil
import socket
import subprocess
import sys
import urllib.request

import distro
import psutil
from PySide6.QtCore import Qt, QThread, Signal, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication, QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QMessageBox, QPushButton, QSizePolicy, QVBoxLayout
)

APP_NAME = "Linver"
APP_VERSION = "2.0.0"

# Remote SVGs. They are intentionally not bundled into the application.
# Simple Icons provides stable, directly downloadable SVG assets.
LOGO_URLS = {
    "ubuntu": "https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/ubuntu.svg",
    "debian": "https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/debian.svg",
    "fedora": "https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/fedora.svg",
    "arch": "https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/archlinux.svg",
    "linux mint": "https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/linuxmint.svg",
    "opensuse": "https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/opensuse.svg",
    "manjaro": "https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/manjaro.svg",
    "elementary": "https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/elementary.svg",
    "pop!_os": "https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/popos.svg",
    "kali": "https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/kalilinux.svg",
    "alpine": "https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/alpinelinux.svg",
    "gentoo": "https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/gentoo.svg",
    "nixos": "https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/nixos.svg",
    "rocky": "https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/rockylinux.svg",
    "centos": "https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/centos.svg",
    "red hat": "https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/redhat.svg",
}

DISTRO_SITES = {
    "ubuntu": "https://ubuntu.com/",
    "debian": "https://www.debian.org/",
    "fedora": "https://fedoraproject.org/",
    "arch": "https://archlinux.org/",
    "linux mint": "https://linuxmint.com/",
    "opensuse": "https://www.opensuse.org/",
    "manjaro": "https://manjaro.org/",
    "elementary": "https://elementary.io/",
    "pop!_os": "https://system76.com/pop",
    "kali": "https://www.kali.org/",
    "alpine": "https://www.alpinelinux.org/",
    "gentoo": "https://www.gentoo.org/",
    "nixos": "https://nixos.org/",
    "rocky": "https://rockylinux.org/",
    "centos": "https://www.centos.org/",
    "red hat": "https://www.redhat.com/",
}


def human_bytes(value):
    value = float(value)
    units = ("B", "KB", "MB", "GB", "TB", "PB")
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} PB"


def human_uptime(seconds):
    seconds = int(max(0, seconds))
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if not parts:
        parts.append(f"{secs} second{'s' if secs != 1 else ''}")
    return ", ".join(parts)


def run_command(command):
    try:
        return subprocess.check_output(
            command, stderr=subprocess.DEVNULL, text=True, timeout=1.5
        ).strip()
    except Exception:
        return ""


def detect_session():
    desktop = os.environ.get("XDG_CURRENT_DESKTOP") or os.environ.get("XDG_SESSION_DESKTOP")
    session = os.environ.get("XDG_SESSION_TYPE")
    desktop = desktop.replace(":", "; ") if desktop else "Unknown"
    return desktop, session or "Unknown"


def collect_system_info():
    name = distro.name(pretty=True) or platform.system()
    base_name = (distro.name() or "").strip().lower()
    version = distro.version() or "Unknown"
    codename = distro.codename() or ""
    build = distro.build_number() or "N/A"

    kernel = platform.release()
    machine = platform.machine() or "Unknown"
    hostname = socket.gethostname()
    username = getpass.getuser()

    mem = psutil.virtual_memory()
    root_path = os.path.abspath(os.sep)
    try:
        disk = psutil.disk_usage(root_path)
    except OSError:
        disk = None

    boot = psutil.boot_time()
    uptime = dt.datetime.now() - dt.datetime.fromtimestamp(boot)

    cpu = platform.processor() or platform.machine() or "Unknown CPU"
    cpu_count = psutil.cpu_count(logical=True) or 0
    cpu_physical = psutil.cpu_count(logical=False) or 0

    desktop, session = detect_session()

    # Package-manager detection is deliberately informational only.
    managers = []
    for manager in ("apt", "dnf", "yum", "pacman", "zypper", "apk", "emerge", "nix-env"):
        if shutil.which(manager):
            managers.append(manager)
    package_manager = ", ".join(managers) if managers else "Not detected"

    return {
        "name": name,
        "base_name": base_name,
        "version": version,
        "codename": codename,
        "build": build,
        "kernel": kernel,
        "machine": machine,
        "hostname": hostname,
        "username": username,
        "cpu": cpu,
        "cpu_logical": cpu_count,
        "cpu_physical": cpu_physical,
        "ram_used": mem.used,
        "ram_total": mem.total,
        "ram_percent": mem.percent,
        "disk": disk,
        "boot": boot,
        "uptime": human_uptime(uptime.total_seconds()),
        "desktop": desktop,
        "session": session,
        "package_manager": package_manager,
        "python": platform.python_version(),
        "linver": APP_VERSION,
    }


class LogoWorker(QThread):
    loaded = Signal(bytes)
    failed = Signal()

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            req = urllib.request.Request(
                self.url,
                headers={"User-Agent": "Linver/2.0 (+https://github.com/)"},
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                self.loaded.emit(response.read())
        except Exception:
            self.failed.emit()


class InfoRow(QFrame):
    def __init__(self, label, value):
        super().__init__()
        self.setObjectName("InfoRow")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        left = QLabel(label)
        left.setObjectName("RowLabel")
        right = QLabel(value)
        right.setObjectName("RowValue")
        right.setTextInteractionFlags(Qt.TextSelectableByMouse)
        right.setWordWrap(True)
        layout.addWidget(left, 0)
        layout.addWidget(right, 1)
        self.value_label = right


class LinverDialog(QDialog):
    def __init__(self, info, no_network=False):
        super().__init__()
        self.info = info
        self.no_network = no_network
        self.logo_worker = None

        self.setWindowTitle(f"{APP_NAME} — About this system")
        self.setFixedSize(760, 560)
        self.setStyleSheet("""
            QDialog { background: #f7f7f8; color: #202124; }
            QLabel { color: #202124; }
            #Header { background: white; border: 1px solid #dedee2; border-radius: 12px; }
            #DistroName { font-size: 25px; font-weight: 650; }
            #Subtitle { color: #62656b; font-size: 13px; }
            #InfoCard { background: white; border: 1px solid #dedee2; border-radius: 12px; }
            #InfoRow { border-bottom: 1px solid #eeeeef; }
            #RowLabel { color: #6b6e74; font-size: 12px; min-width: 120px; }
            #RowValue { font-size: 13px; }
            QPushButton {
                background: white; border: 1px solid #cfcfd4; border-radius: 7px;
                padding: 7px 15px; color: #25262a;
            }
            QPushButton:hover { background: #f0f1f3; }
            QPushButton:pressed { background: #e5e6e8; }
            #Primary {
                background: #2563eb; color: white; border: 1px solid #2563eb;
            }
            #Primary:hover { background: #1d4ed8; }
            #Footer { color: #777a80; font-size: 11px; }
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(22, 22, 22, 18)
        outer.setSpacing(14)

        header = QFrame()
        header.setObjectName("Header")
        h = QHBoxLayout(header)
        h.setContentsMargins(22, 20, 22, 20)
        self.logo = QLabel()
        self.logo.setFixedSize(92, 92)
        self.logo.setAlignment(Qt.AlignCenter)
        self.logo.setText("🐧")
        self.logo.setStyleSheet("font-size: 55px;")
        h.addWidget(self.logo)

        title_box = QVBoxLayout()
        title = QLabel(self.info["name"])
        title.setObjectName("DistroName")
        subtitle_text = f"Version {self.info['version']}"
        if self.info["codename"]:
            subtitle_text += f"  •  {self.info['codename']}"
        subtitle = QLabel(subtitle_text)
        subtitle.setObjectName("Subtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        title_box.addSpacing(6)
        tagline = QLabel("Linux system information")
        tagline.setObjectName("Subtitle")
        title_box.addWidget(tagline)
        h.addLayout(title_box, 1)
        outer.addWidget(header)

        card = QFrame()
        card.setObjectName("InfoCard")
        grid = QVBoxLayout(card)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)

        rows = [
            ("Kernel", self.info["kernel"]),
            ("Architecture", self.info["machine"]),
            ("CPU", f"{self.info['cpu']}  ({self.info['cpu_logical']} logical / {self.info['cpu_physical']} physical)"),
            ("Memory", f"{human_bytes(self.info['ram_used'])} used of {human_bytes(self.info['ram_total'])} ({self.info['ram_percent']:.0f}%)"),
            ("Root storage", self.disk_text()),
            ("Hostname", self.info["hostname"]),
            ("User", self.info["username"]),
            ("Desktop", self.info["desktop"]),
            ("Session", self.info["session"]),
            ("Package manager", self.info["package_manager"]),
            ("Uptime", self.info["uptime"]),
        ]
        for label, value in rows:
            grid.addWidget(InfoRow(label, value))
        outer.addWidget(card, 1)

        footer = QHBoxLayout()
        footer_label = QLabel(
            f"Linver {APP_VERSION}  •  Free and open source  •  Python {self.info['python']}"
        )
        footer_label.setObjectName("Footer")
        footer.addWidget(footer_label)
        footer.addStretch()

        copy_btn = QPushButton("Copy details")
        copy_btn.clicked.connect(self.copy_details)
        footer.addWidget(copy_btn)

        site_btn = QPushButton("Distribution website")
        site_btn.setObjectName("Primary")
        site_btn.clicked.connect(self.open_distro_site)
        footer.addWidget(site_btn)

        close_btn = QPushButton("OK")
        close_btn.clicked.connect(self.accept)
        footer.addWidget(close_btn)
        outer.addLayout(footer)

        if not self.no_network:
            self.load_logo()

    def disk_text(self):
        disk = self.info["disk"]
        if not disk:
            return "Unavailable"
        return f"{human_bytes(disk.used)} used of {human_bytes(disk.total)} ({disk.percent:.0f}%)"

    def load_logo(self):
        key = self.info["base_name"]
        url = LOGO_URLS.get(key)
        if not url:
            return
        self.logo_worker = LogoWorker(url)
        self.logo_worker.loaded.connect(self.set_logo)
        self.logo_worker.failed.connect(self.logo_failed)
        self.logo_worker.start()

    def set_logo(self, data):
        renderer = QSvgRenderer(data)
        if renderer.isValid():
            pixmap = QPixmap(92, 92)
            pixmap.fill(Qt.transparent)
            from PySide6.QtGui import QPainter
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            self.logo.setPixmap(pixmap)

    def logo_failed(self):
        self.logo.setText("🐧")

    def copy_details(self):
        i = self.info
        text = (
            f"{i['name']} {i['version']}\n"
            f"Kernel: {i['kernel']}\n"
            f"Architecture: {i['machine']}\n"
            f"CPU: {i['cpu']}\n"
            f"RAM: {human_bytes(i['ram_used'])} / {human_bytes(i['ram_total'])}\n"
            f"Root storage: {self.disk_text()}\n"
            f"Hostname: {i['hostname']}\n"
            f"User: {i['username']}\n"
            f"Desktop: {i['desktop']}\n"
            f"Session: {i['session']}\n"
            f"Package manager: {i['package_manager']}\n"
            f"Uptime: {i['uptime']}\n"
        )
        QApplication.clipboard().setText(text)

    def open_distro_site(self):
        key = self.info["base_name"]
        url = DISTRO_SITES.get(key)
        if url:
            QDesktopServices.openUrl(QUrl(url))
        else:
            QDesktopServices.openUrl(QUrl("https://www.google.com/search?q=" + self.info["name"].replace(" ", "+")))


def print_cli(info):
    print(f"{info['name']}")
    print(f"Version {info['version']}" + (f" ({info['codename']})" if info["codename"] else ""))
    print(f"Kernel: {info['kernel']}")
    print(f"Architecture: {info['machine']}")
    print(f"CPU: {info['cpu']}")
    print(f"RAM: {human_bytes(info['ram_used'])} / {human_bytes(info['ram_total'])}")
    disk = info["disk"]
    if disk:
        print(f"Root storage: {human_bytes(disk.used)} / {human_bytes(disk.total)} ({disk.percent:.0f}%)")
    print(f"Hostname: {info['hostname']}")
    print(f"User: {info['username']}")
    print(f"Desktop: {info['desktop']}")
    print(f"Session: {info['session']}")
    print(f"Package manager: {info['package_manager']}")
    print(f"Uptime: {info['uptime']}")
    print(f"Linver: {APP_VERSION}")


def main():
    parser = argparse.ArgumentParser(description="Winver-style system information utility for Linux.")
    parser.add_argument("--cli", action="store_true", help="print information in the terminal")
    parser.add_argument("--no-network", action="store_true", help="do not download the remote distro logo")
    parser.add_argument("--version", action="version", version=f"%(prog)s {APP_VERSION}")
    args = parser.parse_args()

    if platform.system().lower() != "linux":
        print("Linver is designed for Linux.", file=sys.stderr)

    info = collect_system_info()

    if args.cli:
        print_cli(info)
        return

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    dialog = LinverDialog(info, args.no_network)
    dialog.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
