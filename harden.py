#!/usr/bin/env python3

import os
import sys
import subprocess
import logging
import argparse
import json
from datetime import datetime

if os.geteuid() != 0:
    sys.stderr.write("This script must be run with sudo or as root.\n")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def is_btrfs_root():
    try:
        result = subprocess.run(['findmnt', '-n', '-o', 'FSTYPE', '/'], capture_output=True, text=True, check=True)
        return result.stdout.strip().lower() == 'btrfs'
    except Exception:
        return False

def create_btrfs_snapshot():
    if not is_btrfs_root():
        logger.warning("Root filesystem is not Btrfs; skipping snapshot.")
        return None
    snap_dir = '/.snapshots'
    os.makedirs(snap_dir, exist_ok=True)
    snapshot_label = datetime.now().strftime("hardening-pre-%Y%m%d%H%M%S")
    snapshot_path = os.path.join(snap_dir, snapshot_label)
    try:
        subprocess.run(['btrfs', 'subvolume', 'snapshot', '-r', '/', snapshot_path], check=True)
        logger.info(f"Created Btrfs snapshot at {snapshot_path}")
        return snapshot_path
    except subprocess.CalledProcessError:
        logger.error("Failed to create Btrfs snapshot.")
        return None

def rollback_btrfs(snapshot_path):
    if not is_btrfs_root() or not os.path.exists(snapshot_path):
        logger.error("Cannot rollback. Either filesystem is not Btrfs or snapshot does not exist.")
        return False
    try:
        result = subprocess.run(['btrfs', 'subvolume', 'show', snapshot_path], capture_output=True, text=True, check=True)
        for line in result.stdout.splitlines():
            if line.startswith('ID '):
                snap_id = line.split()[1]
                subprocess.run(['btrfs', 'subvolume', 'set-default', snap_id, '/'], check=True)
                logger.info("Rollback completed. Reboot to apply changes.")
                return True
    except subprocess.CalledProcessError:
        logger.error("Rollback failed.")
    return False

def update_system(dry_run):
    if dry_run:
        subprocess.run(['dnf', 'check-update'], check=False)
        logger.info("Dry-run: Checked for updates.")
    else:
        subprocess.run(['dnf', '-y', 'upgrade', '--refresh'], check=False)
        logger.info("System updated.")

def disable_services(mode, dry_run):
    services = ["avahi-daemon", "cups", "postfix", "vsftpd"]
    if mode == "workstation":
        services.extend(["smb", "nmb", "rpcbind", "nfs-server", "bluetooth"])
    elif mode == "server":
        services.extend(["rpcbind", "nfs-server", "gdm", "cups-browsed", "bluetooth"])
    for svc in services:
        if dry_run:
            logger.info(f"Dry-run: Would disable {svc}")
        else:
            subprocess.run(['systemctl', 'disable', '--now', svc], check=False)

def configure_firewall(dry_run):
    if dry_run:
        logger.info("Dry-run: Would configure firewalld.")
    else:
        subprocess.run(['dnf', '-y', 'install', 'firewalld'], check=False)
        subprocess.run(['systemctl', 'enable', '--now', 'firewalld'], check=False)
        subprocess.run(['firewall-cmd', '--permanent', '--add-service=ssh'], check=False)
        subprocess.run(['firewall-cmd', '--reload'], check=False)
        logger.info("Firewalld configured.")

def enforce_selinux(dry_run):
    if dry_run:
        logger.info("Dry-run: Would enforce SELinux.")
    else:
        subprocess.run(['setenforce', '1'], check=False)
        logger.info("SELinux enforced.")

def harden_ssh(dry_run):
    sshd_config = '/etc/ssh/sshd_config'
    new_port = 2022
    if dry_run:
        logger.info(f"Dry-run: Would set SSH Port to {new_port}, disable root login and password auth.")
    else:
        subprocess.run(['cp', sshd_config, f"{sshd_config}.bak"], check=False)
        with open(sshd_config, 'a') as f:
            f.write(f"\nPort {new_port}\nPermitRootLogin no\nPasswordAuthentication no\n")
        subprocess.run(['systemctl', 'restart', 'sshd'], check=False)
        logger.info("SSH hardened.")

def harden_sysctl(dry_run):
    sysctl_conf = "/etc/sysctl.d/99-hardening.conf"
    params = {
        "net.ipv4.ip_forward": 0,
        "kernel.randomize_va_space": 2,
        "fs.suid_dumpable": 0
    }
    if dry_run:
        logger.info("Dry-run: Would apply sysctl hardening parameters.")
    else:
        with open(sysctl_conf, 'w') as f:
            for k, v in params.items():
                f.write(f"{k} = {v}\n")
        subprocess.run(['sysctl', '--system'], check=False)
        logger.info("Sysctl parameters applied.")

def install_fail2ban(dry_run):
    if dry_run:
        logger.info("Dry-run: Would install and configure fail2ban.")
    else:
        subprocess.run(['dnf', '-y', 'install', 'fail2ban'], check=False)
        subprocess.run(['systemctl', 'enable', '--now', 'fail2ban'], check=False)
        logger.info("fail2ban installed and running.")

def main():
    parser = argparse.ArgumentParser(description="Fedora 42 Hardening Script")
    parser.add_argument("--mode", choices=["workstation", "server"], required=False)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--rollback", action="store_true")
    args = parser.parse_args()

    if args.rollback:
        snap_info = "/var/lib/hardening/last_snapshot"
        if os.path.exists(snap_info):
            with open(snap_info, 'r') as f:
                snap_path = f.read().strip()
            rollback_btrfs(snap_path)
        else:
            logger.error("No snapshot information found.")
        sys.exit(0)

    if not args.mode:
        logger.error("Specify --mode as 'workstation' or 'server'.")
        sys.exit(1)

    dry_run = args.dry_run
    if not dry_run and is_btrfs_root():
        snapshot_path = create_btrfs_snapshot()
        if snapshot_path:
            os.makedirs("/var/lib/hardening", exist_ok=True)
            with open("/var/lib/hardening/last_snapshot", "w") as f:
                f.write(snapshot_path)

    update_system(dry_run)
    disable_services(args.mode, dry_run)
    configure_firewall(dry_run)
    enforce_selinux(dry_run)
    harden_ssh(dry_run)
    harden_sysctl(dry_run)
    install_fail2ban(dry_run)

if __name__ == "__main__":
    main()
