
# 🛡️ Fedora 42 Hardening Script

This script automates the security hardening of Fedora 42 systems for both **Workstation** and **Server** environments. It applies security best practices following CIS benchmarks, automates system updates, disables unnecessary services, configures SELinux, hardens SSH, applies kernel hardening, and sets up basic intrusion prevention.

---

## ⚠️ **Disclaimer – Use at Your Own Risk!**

This script performs **critical system modifications** that may disrupt normal operations, including:

- Disabling essential services.
- Changing the SSH port to `2022` and disabling root/password SSH logins.
- Enforcing SELinux policies and applying kernel parameter changes.
- Blocking access through the firewall except for explicitly allowed ports.
- Creating/using Btrfs snapshots if available.

**It is highly recommended to run the script in `--dry-run` mode first to review proposed changes. Always have backups and console access before applying hardening.**

---

## 📖 Usage

Ensure the script is executable and run it with `sudo` or as `root`.

```bash
sudo python3 harden.py --mode workstation [--dry-run]
sudo python3 harden.py --mode server [--dry-run]
sudo python3 harden.py --rollback
```

---

### 📌 **Options**

| Option         | Description                                  |
|----------------|----------------------------------------------|
| `--mode`       | Specify `workstation` or `server`.           |
| `--dry-run`    | Preview changes without applying them.       |
| `--rollback`   | Revert to the last Btrfs snapshot (if any).  |

---

### 🚀 **Examples**

- Preview changes for a Server:
    ```bash
    sudo python3 harden.py --mode server --dry-run
    ```

- Apply hardening to a Workstation:
    ```bash
    sudo python3 harden.py --mode workstation
    ```

- Rollback to last snapshot:
    ```bash
    sudo python3 harden.py --rollback
    ```

---

## ✅ **What This Script Does**

- **System Updates**: Updates all packages and enables security auto-updates.
- **Service Management**: Disables unnecessary services based on mode.
- **Firewall Configuration**: Installs and configures `firewalld` to allow only necessary ports.
- **SELinux Enforcement**: Enables SELinux in enforcing mode.
- **SSH Hardening**: 
    - Changes SSH port to `2022`.  
    - Disables root login and password authentication.  
    - Restarts the SSH service.
- **Kernel Hardening**: Applies sysctl settings for additional security.
- **Account Hardening**: Enforces basic password policies.
- **Fail2Ban Installation**: Installs and configures fail2ban to protect against brute force attacks.
- **Rollback Support**: If the root filesystem is Btrfs, creates a snapshot for easy rollback.

---

## 📋 **Important Notes**

- This script modifies **critical configuration files** such as:
    - `/etc/ssh/sshd_config`
    - `/etc/selinux/config`
    - `/etc/sysctl.d/99-hardening.conf`
- The SSH port is changed to `2022`. Ensure firewall and clients are updated accordingly.
- Always test in a non-production environment before deploying system-wide.
- Rollback functionality works **only if your root filesystem is Btrfs**.

---

## 📅 **Changelog**

- **v1.0** – Initial release with workstation and server modes, dry-run support, rollback via Btrfs, and core hardening features.

---

## 📞 **Support**

This script is provided **as-is** with no guarantees.  
Use it at your own risk.  
Issues and suggestions can be submitted via GitHub Issues.

---
