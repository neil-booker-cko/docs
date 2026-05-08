# TACACS+ Server Setup (tac_plus)

tac_plus is the open-source TACACS+ server implementation (Shrubbery Networks). Checkout runs
tac_plus on utility servers (10.13.1.147, 10.13.2.116, 10.13.2.147) for centralized AAA for
Cisco IOS-XE, FortiGate, and Vertiv Cyclades devices.

---

## Overview

**Server Implementation:** tac_plus running on utility servers (3-server redundancy)

**Supported Clients:**

- Cisco IOS-XE (switches, routers)
- FortiGate firewalls (admin access)
- Vertiv Cyclades console servers (OOB management)

**Authentication Methods:**

- Local user database (on server)
- Active Directory / LDAP integration (future)

---

## Installation

### Prerequisites

- Linux utility server (Ubuntu 20.04+, CentOS 8+)
- Network connectivity to all managed devices
- Root or sudo access

### Install tac_plus

**Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install tacacs+
```

**CentOS/RHEL:**

```bash
sudo yum install tacacs-plus
```

**Verify Installation:**

```bash
tacacs_plus -v
! or
/usr/sbin/tac_plus -v
```

---

## Configuration

### Basic tac_plus Configuration File

TACACS+ is configured in `/etc/tacacs+/tac_plus.conf` (or `/etc/tac_plus.conf` depending on
distro).

**Directory Structure:**

```text
/etc/tacacs+/
├── tac_plus.conf       # Main configuration
├── users.txt           # Local user database (optional)
└── .tac_plus_key       # Shared secret (must be mode 0600)
```

### Main Configuration (tac_plus.conf)

```ini
# Global settings
key = SharedSecret123!
logfile = /var/log/tacacs+/tac_plus.log
debugging = 0
# Set to 1 for detailed debug output during testing
# Set to 0 for production
accounting log = /var/log/tacacs+/acct.log

# Listen on all interfaces on port 49
listen {
  ip = 0.0.0.0
  port = 49
}

# User database
user = * {
  default service = permit
  login = local
}

# Service authentication methods
service = shell {
  # Shell (CLI) service
}

service = ppp {
  # PPP service (not used for network devices)
}

# Groups for authorization
group = network-admins {
  service = shell {
    priv-lvl = 15
    # Can run all commands
  }
}

group = network-operators {
  service = shell {
    priv-lvl = 5
    # Limited command set
  }
}

group = readonly {
  service = shell {
    priv-lvl = 1
    # Read-only access
  }
}

# Local user examples
user = admin {
  password = <encrypted_password>
  group = network-admins
  name = "Full Admin"
}

user = operator {
  password = <encrypted_password>
  group = network-operators
  name = "Network Operator"
}

user = viewer {
  password = <encrypted_password>
  group = readonly
  name = "Read-Only User"
}

# Host-specific client configuration
client = 192.0.2.1 {
  # Cisco switch (ELD7-CSW-01)
  key = SwitchSecret123!
  description = "ELD7-CSW-01"
}

client = 192.0.2.2 {
  # FortiGate firewall (ELD7-PFW-01A)
  key = FortiSecret456!
  description = "ELD7-PFW-01A"
}

client = 192.0.2.3 {
  # Vertiv Cyclades console server (ELD7-CON-01)
  key = CycladesSecret789!
  description = "ELD7-CON-01"
}
```

### Encrypt Passwords

Instead of storing plaintext passwords, use tac_plus's built-in encryption:

```bash
# Interactive password prompt
tac_plus -C /etc/tacacs+/tac_plus.conf -c PASSWORD_TO_ENCRYPT

# Example output:
# Password: (enter password)
# Encrypted: ^7D3D3D3D3D3D3D3D3D3D3D3D
```

Use the encrypted value in tac_plus.conf:

```ini
user = admin {
  password = encrypted ^7D3D3D3D3D3D3D3D3D3D3D3D
  group = network-admins
}
```

### Shared Secrets (per-Device)

Each managed device has a unique shared secret. Configure on the device side (in Cisco/FortiGate
config) and in tac_plus.conf:

```ini
client = 10.0.1.100 {
  # Cisco device
  key = UniqueSecret123!
  description = "ELD7-CSW-01"
}
```

---

## Service Startup and Management

### Start tac_plus Service

```bash
# Start immediately
sudo systemctl start tacacs+

# Enable auto-start on boot
sudo systemctl enable tacacs+

# Check status
sudo systemctl status tacacs+

# View logs
sudo tail -f /var/log/tacacs+/tac_plus.log
```

### Reload Configuration (Without Restart)

```bash
# Send HUP signal to reload config
sudo kill -HUP $(cat /var/run/tac_plus.pid)

# or
sudo systemctl reload tacacs+
```

---

## Logging and Accounting

### Log Levels

```ini
# tac_plus.conf
debugging = 0   # Production (errors only)
debugging = 1   # Warnings
debugging = 2   # Informational (login attempts, auth events)
debugging = 4   # Debug (detailed protocol messages)
```

### Log Rotation

Configure logrotate to prevent log files from consuming disk space:

```bash
# /etc/logrotate.d/tacacs+
/var/log/tacacs+/tac_plus.log {
  daily
  rotate 7
  compress
  notifempty
  create 0600 root root
  postrotate
    systemctl reload tacacs+ >/dev/null 2>&1 || true
  endscript
}
```

Apply logrotate:

```bash
sudo logrotate -f /etc/logrotate.d/tacacs+
```

### Accounting Log Format

Accounting records are written to `/var/log/tacacs+/acct.log`:

```text
Mon May  8 14:32:15 2026 admin TACACS+ server 10.0.0.100:49:admin
  Mon May  8 14:32:10 2026 start TACACS+ login {admin} from (192.0.2.1)
  Mon May  8 14:32:15 2026 stop TACACS+ login {admin} from (192.0.2.1)
```

Parse accounting logs for audit:

```bash
# Grep for failed logins
grep "failed" /var/log/tacacs+/acct.log

# Count logins per user
awk '{print $NF}' /var/log/tacacs+/acct.log | sort | uniq -c
```

---

## Testing and Verification

### Test Server Connectivity

```bash
# From managed device, test TCP connectivity
ping -c 4 10.0.0.100
telnet 10.0.0.100 49
# Should connect; type Ctrl-C to exit
```

### Test Authentication (Cisco)

From a Cisco device configured with TACACS+:

```ios
show aaa servers
! Should show "UP" status for TACACS+ server

debug aaa authentication
! Enable debug, then try login
```

### Test Authentication (Manual)

Use tacacs-client tool (if available):

```bash
# Ubuntu
sudo apt install tacacs+

# Connect to server
tacc -h 10.0.0.100 -k SharedSecret123! -u admin -p password
```

---

## Troubleshooting

### Problem: Server Not Responding to Clients

**Check service running:**

```bash
sudo systemctl status tacacs+
sudo netstat -tlnp | grep 49
# Should show tac_plus listening on 0.0.0.0:49
```

**Check firewall:**

```bash
# Allow port 49 from managed devices
sudo ufw allow from 192.0.2.0/24 to any port 49
# or
sudo firewall-cmd --add-rich-rule='rule family="ipv4" source address="192.0.2.0/24" port protocol="tcp" port="49" accept'
```

**Check logs:**

```bash
sudo tail -f /var/log/tacacs+/tac_plus.log
# Look for connection errors or mismatched secrets
```

### Problem: Authentication Fails

**Verify shared secret matches:**

```bash
# In tac_plus.conf
client = 192.0.2.1 {
  key = SharedSecret123!
}

# On Cisco device, verify:
show running-config | include tacacs
! Must match exactly
```

**Verify user exists and password is correct:**

```bash
# Edit tac_plus.conf and check user entry
sudo grep "user = admin" /etc/tacacs+/tac_plus.conf

# Test password encryption
tac_plus -c MyPassword123!
# Compare with encrypted password in config
```

**Enable debug logging:**

```bash
# Temporarily set debugging = 4 in tac_plus.conf
sudo systemctl reload tacacs+
# Monitor logs while attempting login
sudo tail -f /var/log/tacacs+/tac_plus.log
```

### Problem: Slow Authentication

**Check network latency:**

```bash
ping -c 5 10.0.0.100
# Should be < 10ms

# On server: check CPU and load
top -n 1 | grep Cpu
```

**Increase device timeout:**

```ios
! On Cisco device
tacacs server TAC-PRIMARY
  timeout 15
  ! Increase from default 5 seconds
```

---

## High Availability (3-Server Redundancy)

Deploy tac_plus on three utility servers for redundancy:

**Server 1:** 10.13.1.147
**Server 2:** 10.13.2.116
**Server 3:** 10.13.2.147

Configure managed devices to try servers in order:

```ios
! Cisco configuration
aaa group server tacacs+ TACACS-SERVERS
  server 10.13.1.147
  server 10.13.2.116
  server 10.13.2.147
  ip tacacs source-interface Loopback0
  timeout 10
```

**Failover behavior:**

1. Device connects to Server 1 (10.13.1.147)
2. If Server 1 unreachable (timeout), try Server 2 (10.13.2.116)
3. If Server 2 unreachable, try Server 3 (10.13.2.147)
4. If all servers unreachable, fall back to local authentication

**Configuration Sync:**

Maintain identical tac_plus.conf on all three servers:

```bash
# On server 1, after making config changes
scp /etc/tacacs+/tac_plus.conf user@10.13.2.116:/etc/tacacs+/
scp /etc/tacacs+/tac_plus.conf user@10.13.2.147:/etc/tacacs+/

# Reload all servers
ssh user@10.13.2.116 "sudo systemctl reload tacacs+"
ssh user@10.13.2.147 "sudo systemctl reload tacacs+"
```

---

## Security Best Practices

✅ **Do:**

- Use strong, unique shared secrets per device
- Restrict access to tac_plus config file (mode 0600)
- Limit file permissions on `/etc/tacacs+/`
- Rotate passwords regularly (at least annually)
- Use encrypted passwords in config (not plaintext)
- Enable accounting for audit trail
- Restrict TACACS+ port 49 to management subnet only
- Monitor logs for failed authentication attempts
- Test failover to local auth regularly

❌ **Don't:**

- Use default or simple shared secrets
- Store plaintext passwords in config
- Run tac_plus on production network devices
- Allow unauthenticated access to TACACS+ port
- Disable logging/accounting
- Share secrets across devices (use unique per device)

---

## Related Documentation

- [TACACS+ Protocol Reference](../application/tacacs.md) — Protocol details and packet structure
- [Cisco AAA Configuration](./cisco_aaa_config.md) — Client-side setup on Cisco IOS-XE
- [Security Hardening Standards](../checkout-standards/security-hardening.md) — AAA/TACACS+ architecture
- [Syslog Configuration](./cisco_syslog_config.md) — Centralized logging for authentication events
