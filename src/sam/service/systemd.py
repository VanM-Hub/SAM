"""
systemd unit file generator.

Menghasilkan file sam.service untuk systemd.
"""

SYSTEMD_UNIT = """[Unit]
Description=SAM — AI Operations Guardian Runtime
After=network.target

[Service]
Type=simple
User=sam
WorkingDirectory=/opt/sam
ExecStart=/usr/bin/python3 -m sam.launcher.desktop
ExecStop=/usr/bin/python3 -m sam.cli.main service stop
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""


def generate_unit_file(path: str = "/etc/systemd/system/sam.service") -> None:
    """Generate systemd unit file.

    Args:
        path: Path untuk menyimpan unit file.
              Default: /etc/systemd/system/sam.service (membutuhkan root).
    """
    with open(path, "w") as f:
        f.write(SYSTEMD_UNIT)
    print(f"systemd unit file written to {path}")
