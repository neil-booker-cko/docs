# Security Hardening Guide

Comprehensive security hardening covering password policies, access control, service restrictions,
logging, and cryptographic best practices for Cisco IOS-XE and FortiGate platforms.

## Overview

Network device hardening follows defense-in-depth: strong authentication, restricted access,
disabled unnecessary services, comprehensive logging, and encrypted management channels.

---

## 1. Password Policies

### Cisco Local Password Configuration

#### Password Length and Complexity

Cisco doesn't enforce password complexity natively, but best practice is minimum **12 characters**
with mixed case, numbers, and symbols. Use strong secrets with scrypt hashing:

```ios
! Enable scrypt hashing (recommended)
username admin privilege 15 secret algorithm-type scrypt MyP@ssw0rd123!

! Older MD5 hashing (not recommended)
username admin privilege 15 secret md5 MyPassword123!

! Plaintext enable password (NEVER use)
enable password MyPassword
! Instead use:
enable secret algorithm-type scrypt MyP@ssw0rd123!
```

**Why Scrypt:** Scrypt is memory-hard and slow, making brute-force attacks computationally
expensive. MD5 is fast and vulnerable to rainbow tables.

#### Password Expiration

Cisco does NOT have built-in password expiration for local users. Enforce via:

1. **External AAA (TACACS+/RADIUS):** Server enforces expiration
2. **Manual Policy:** Document and enforce password changes every 90 days
3. **Operational Discipline:** Include in change management procedures

```ios
! Example: Force password change on next login (operational note only)
! No built-in mechanism; use TACACS+ server to enforce

aaa new-model
aaa authentication login default group tacacs+ local
aaa authorization exec default group tacacs+ local

! TACACS+ server enforces password age and complexity
tacacs server PRIMARY
  address ipv4 10.0.0.100
  key SharedSecret123!
```

#### Account Lockout

Cisco does NOT have built-in account lockout. TACACS+/RADIUS servers provide this:

```ios
! With TACACS+, server controls:
! - Max failed login attempts (e.g., 5)
! - Lockout duration (e.g., 15 minutes)
! - Password age (e.g., 90 days)

! Local workaround: Monitor failed login attempts in logs
debug aaa authentication
! Check syslog for repeated failed attempts from admin
```

#### Best Practices: Cisco Passwords

✅ **Do:**

- Use `enable secret` with `algorithm-type scrypt`
- Minimum 12 characters: mixed case + numbers + symbols
- Store passwords in secure vault (LastPass, 1Password, HashiCorp Vault)
- Require SSH key-based auth for automation (no passwords in scripts)
- Use TACACS+/RADIUS for centralized password policies
- Force password change every 90 days (via TACACS+ or operational procedure)
- Document password policy in runbooks

❌ **Don't:**

- Use `enable password` (plaintext, visible in config)
- Use simple passwords (e.g., "Password123")
- Reuse passwords across devices
- Store passwords in email or chat
- Log in with default usernames (admin/admin)
- Use static passwords for service accounts; prefer SSH keys

---

### FortiGate Local Password Configuration

#### Password Length and Complexity

FortiGate enforces password complexity by default. Requirements vary by version:

**FortiOS 7.x+:**

```fortios
! Enable password strength requirements
config system admin
  edit "admin"
    set password MyP@ssw0rd123!
    ! Password must meet complexity: min 8 chars, uppercase + lowercase + digits + symbols
    set force-password-change disable
    set password-expire 2026-12-31
    set wanip 0.0.0.0
    ! Restrict admin login to specific IP
  next
end

! Check password policy
show system admin
```

**Minimum Requirements (FortiOS 7.x):**

- Minimum 8 characters (configurable to 14+)
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 digit
- At least 1 special character (!@#$%^&*)

#### Password Expiration

FortiGate supports password expiration:

```fortios
config system admin
  edit "admin"
    set password MyP@ssw0rd123!
    set password-expire 2026-12-31
    ! Or use days since creation:
    set expire-time 90
    ! Warn user at 7 days before expiry:
    set password-renewal-warning 7
  next
end
```

#### Account Lockout

FortiGate enforces automatic lockout after failed login attempts:

```fortios
config system global
  ! Lock account after 5 failed attempts
  set auth-lockout-threshold 5
  ! Lockout duration in minutes
  set auth-lockout-duration 30
  ! Show login failure in syslog
  set log-auth-failure enable
end
```

#### Two-Factor Authentication (2FA)

FortiGate supports TOTP and FortiToken for admin accounts:

```fortios
config system admin
  edit "admin"
    set password MyP@ssw0rd123!
    ! Require TOTP (Google Authenticator, Microsoft Authenticator)
    set two-factor fortitoken
    ! Or use TOTP
    set two-factor ftk
  next
end

! Generate TOTP token
execute forticlient-tool --action generate_token --user admin
```

#### Best Practices: FortiGate Passwords

✅ **Do:**

- Enforce minimum 14 characters (not default 8)
- Require uppercase + lowercase + digits + special chars
- Set password expiration to 90 days
- Configure account lockout (5 attempts, 30-minute lockout)
- Enable login failure logging
- Use LDAP/RADIUS for centralized policies
- Enable 2FA for admin accounts
- Restrict admin access by source IP

❌ **Don't:**

- Use default passwords (admin/admin)
- Disable password complexity enforcement
- Disable password expiration
- Allow unlimited failed login attempts
- Share admin accounts (use individual logins)
- Store admin passwords in plaintext files

---

## 2. Access Control

### Cisco SSH/Telnet Restrictions

```ios
! Disable telnet (unencrypted)
no ip http server
no ip http secure-server

! Enable SSH v2 only
ip ssh version 2
ip ssh rsa keypair-name SSH-KEY

! Require SSH for VTY access
line vty 0 4
  transport input ssh
  ! No telnet allowed

line console 0
  ! Console can use exec mode only (no transport needed)
  no exec
  ! For OOB access, allow exec on console
end
```

### FortiGate Admin Access Control

```fortios
config system admin
  edit "admin"
    set trusthost1 192.168.1.0 255.255.255.0
    ! Allow login only from 192.168.1.0/24
    set trusthost2 10.0.0.1 255.255.255.255
    ! Also allow from 10.0.0.1/32
    ! Default (0.0.0.0 0.0.0.0) = allow from any IP
  next
end

! Disable HTTP (unencrypted) admin access
config system global
  set admin-sport 443
  ! Force HTTPS on port 443
  set admin-https-redirect disable
  ! Allow direct HTTPS (no HTTP redirect)
end
```

---

## 3. Disable Unnecessary Services

### Cisco Unused Services

```ios
! Disable legacy/dangerous services
no service pad
! Disable PAD (X.25 Packet Assembly/Disassembly)

no service finger
! Disable Finger service (reveals user info)

no service udp-small-servers
no service tcp-small-servers
! Disable Echo, Discard, Daytime, Chargen (amplification attack vectors)

no ip directed-broadcast
! Prevent directed broadcast amplification attacks

no cdp run
! Disable Cisco Discovery Protocol (network reconnaissance risk)

no lldp run
! Disable LLDP if not needed (reveals device info)

no ip source-route
! Prevent source-route spoofing attacks

no ip route-cache
! Slightly impact performance but prevent cache poisoning

ip icmp rate-limit unreachable 100
! Rate-limit ICMP unreachables (prevent ICMP flood attacks)
```

### FortiGate Unused Services

```fortios
config system global
  ! Disable HTTP admin access (HTTPS only)
  set admin-https-redirect enable

  ! Disable Telnet
  set admin-telnet-port 0
  ! Port 0 = disabled

  ! Disable SSH if not needed (use HTTPS)
  set admin-ssh-port 0

  ! Disable SNMP if using different monitoring
  set snmp-status disable
end

config system interface
  edit "port1"
    ! Disable unnecessary protocols on management interface
    set allowaccess ping https ssh
    ! Allow only ping, HTTPS, SSH (not HTTP, Telnet, SNMP)
  next
end
```

---

## 4. Control Plane Protection

### Cisco Control Plane Policing

Protect the device CPU from DoS attacks:

```ios
! Create policy map for control plane
policy-map CONTROL-PLANE-POLICY
  class CRITICAL
    police rate 10000 pps
    ! Rate-limit critical traffic to 10,000 pps

  class MANAGEMENT
    police rate 5000 pps
    ! Rate-limit management to 5,000 pps

! Apply to control plane
control-plane
  service-policy input CONTROL-PLANE-POLICY
end
```

### FortiGate DDoS Protection

```fortios
config system ddos-policy
  edit 1
    set comments "Rate-limit SYN floods"
    set interface port1
    set protocol tcp
    set tcp-halfopen-threshold 1000
    ! Alert when half-open connections exceed 1000
  next
end

config system dos-policy
  edit 1
    set interface port1
    set anomaly.tcp_syn_flood {enable}
    set anomaly.tcp_syn_flood_threshold 100
end
```

---

## 5. Logging and Monitoring

### Cisco Syslog

```ios
! Centralized logging to syslog server
logging host 192.0.2.50
logging trap informational
logging source-interface Loopback0
logging facility local7
logging format rfc5424
logging timestamp milliseconds
logging sequence-numbers

! Log all authentication attempts
aaa new-model
aaa accounting exec default start-stop group syslog
aaa accounting commands 15 default start-stop group syslog

! Log configuration changes
archive
  log config
    logging enable
    logging size 500
    notify syslog
end
```

**Monitor For:**

- Failed authentication attempts (brute-force detection)
- Configuration changes (unauthorized modifications)
- Interface state changes (cable pulls, port bounces)
- BGP neighbor changes (routing instability)
- AAA server timeouts (potential attack or outage)

### FortiGate Logging

```fortios
config log syslogd setting
  set status enable
  set server 192.0.2.50
  set port 601
end

config log syslogd filter
  set admin enable
  set authenticate enable
  set event enable
  set traffic enable
end

! Log all admin logins
config system admin
  edit "admin"
    set login-time "2026-04-20 00:00:00"
    ! Track last successful login
  next
end
```

---

## 6. Cryptographic Best Practices

### Cisco SSH Key Configuration

```ios
! Generate RSA key pair (2048-bit minimum, 4096 recommended)
crypto key generate rsa modulus 4096 label SSH-KEY

! Use ECDSA for newer devices (better performance)
crypto key generate ec keysize 384 label ECDSA-KEY

! Configure SSH to use strongest first
ip ssh server algorithm encryption aes256-ctr aes192-ctr aes128-ctr

! View configured keys
show crypto key pubkey-chain rsa
```

### Cisco TLS/HTTPS Configuration

```ios
! TLS 1.2+ only
ip http secure-server
ip http secure-ciphers 'AES256-SHA256:AES128-SHA256:ECDHE-RSA-AES256-GCM-SHA384'
! High-grade ciphers only, no weak DES/RC4

! Use generated certificate (self-signed for lab)
! For production, use CA-signed certificate
crypto pki trustpoint TP-SELF-SIGNED-CA
  enrollment self
  subject-name CN=router.example.com
end

crypto pki enroll TP-SELF-SIGNED-CA
```

### FortiGate HTTPS Certificate

```fortios
config system certificate local
  edit "HTTPS"
    set password ""
    set comments "FortiGate HTTPS certificate"
    set key-type rsa
    set key-size 2048
    ! Use 4096 for higher security (slower)
  next
end

config system global
  set admin-server-cert "HTTPS"
  set admin-sport 443
  set admin-https-ssl-versions tlsv1-2 tlsv1-3
  ! Force TLS 1.2+ only
end
```

---

## 7. NTP for Time Synchronization

NTP is critical for logging correlation, certificate validation, and cryptographic operations.

### Cisco NTP

```ios
ntp server 169.254.169.123 prefer
! AWS Time Sync Service (always available, no internet needed)

ntp server 0.pool.ntp.org
ntp server 1.pool.ntp.org
! Public NTP servers (for internet-connected devices)

ntp source Loopback0
! Use loopback as source (doesn't change if interface down)

ntp authentication enable
ntp authenticate
ntp trusted-key 1
ntp key 1 md5 NTPSecret123

! Verify NTP status
show ntp status
show ntp associations
```

### FortiGate NTP

```fortios
config system ntp
  set type fortiguard
  ! Use FortiGuard's NTP service
  set server "0.fortinet.pool.ntp.org" "1.fortinet.pool.ntp.org"
  set ntpsync enable
  set interface "port1"
  ! Sync via port1
end

diagnose sys ntp status
! Verify NTP is synchronized
```

---

## 8. SNMP Hardening

### Cisco SNMP v3

```ios
snmp-server group ADMIN v3 priv
snmp-server user admin ADMIN v3 auth sha AdminAuthPass123! priv aes 256 AdminPrivPass456!

snmp-server group MONITOR v3 auth
snmp-server user monitor MONITOR v3 auth sha MonitorAuthPass789!

snmp-server view RESTRICTED iso included
snmp-server group MONITOR v3 auth read RESTRICTED
! Read-only access to limited OID tree

snmp-server host 192.0.2.50 version 3 priv admin
! Send traps to server using SNMPv3
```

### FortiGate SNMP v3

```fortios
config system snmp user
  edit "admin"
    set auth-type sha
    set auth-pwd "AdminAuthPass123!"
    set priv-type aes
    set priv-pwd "AdminPrivPass456!"
  next
  edit "monitor"
    set auth-type sha
    set auth-pwd "MonitorAuthPass789!"
  next
end

config system snmp community
  purge
  ! Delete default "public" and "private" communities
end
```

---

## 9. Configuration Backup and Encryption

### Cisco Configuration Backup

```ios
! Encrypt running configuration
service password-encryption
! Encrypts all passwords (type 7 encryption; reversible but hidden)

! Backup to external server
archive
  path ftp://backup-server/configs/$h-$t.backup
  ! $h = hostname, $t = timestamp
  write-memory
  ! Trigger backup on config save
end

! Manual backup
copy running-config startup-config
copy running-config scp://backupuser@192.0.2.50/router-backup.cfg
```

### FortiGate Configuration Backup

```fortios
! Backup with password encryption
execute backup config sftp backupuser@192.0.2.50:22 backup-fortigate.conf password
! Prompted for SFTP password

! Or via GUI: System → Configuration → Backup
! Automatically encrypted in backup file

! Restore (be careful!)
execute restore config sftp backupuser@192.0.2.50:22 backup-fortigate.conf password
```

---

## Complete Hardening Checklist

| Category | Cisco | FortiGate |
| --- | --- | --- |
| **Passwords** | scrypt hashing, 12+ chars, SSH keys | 14+ chars, 2FA, TACACS+ |
| **Access Control** | SSH only, VTY restrictions, ACLs | HTTPS + SSH, IP whitelisting, RBAC |
| **Services** | Disable finger/pad/cdp, no telnet | Disable HTTP/Telnet, no SNMP v1/v2c |
| **Logging** | Syslog, AAA accounting, archive | Syslog, admin log, traffic log |
| **Crypto** | TLS 1.2+, RSA 4096, AES-256 | TLS 1.2+, SNMPv3, SSH v2 |
| **NTP** | NTP auth enabled, multiple servers | Fortiguard NTP, synchronized |
| **Control Plane** | CoPP policy, rate-limiting | DDoS policy, DoS protection |
| **Monitoring** | SNMP v3 only, read-only access | SNMP v3, restricted communities |

---

## Deployment Order

1. **First:** SSH access, disable telnet
2. **Second:** Strong local passwords, enable TACACS+
3. **Third:** Disable unused services
4. **Fourth:** Configure NTP
5. **Fifth:** Enable syslog
6. **Sixth:** Configure SNMP v3
7. **Seventh:** CoPP / DDoS protection
8. **Eighth:** Certificate management
9. **Ninth:** Backup procedures
10. **Tenth:** Monitoring and alerting

---

## Testing Hardening

```bash
# Test SSH strength from external host
nmap -sV -p 22 DEVICE_IP
# Should show: OpenSSH with strong ciphers

# Test HTTPS certificate
openssl s_client -connect DEVICE_IP:443
# Should show TLS 1.2+, no weak ciphers

# Test for weak services
nmap -sU -p 161,162 DEVICE_IP
# Should show: SNMP closed (if SNMPv1/v2c disabled)

# Test account lockout
# Attempt 6 failed logins, should lock account
```

---

## References

- RFC 5246: TLS 1.2
- RFC 8446: TLS 1.3
- RFC 3195: Reliable Syslog
- RFC 3414: SNMPv3 Authentication
- CIS Controls: Secure Configuration Management
- NIST SP 800-53: Security and Privacy Controls

---

## Next Steps

- Implement this guide in lab environment before production
- Document deviations from baseline with risk justification
- Schedule annual security audits
- Train operations team on password policies
- Monitor failed login attempts for suspicious patterns
