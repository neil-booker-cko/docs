# Security Hardening Standards

Checkout security standards based on CIS Benchmarks, STIG, and PCI-DSS requirements. Standards
are derived from current industry best practices and have been reviewed and adopted for Checkout
network devices.

---

## Applicable Frameworks

| Framework | Scope | Version | Status | Requirement |
| --- | --- | --- | --- | --- |
| **CIS Benchmarks** | Cisco IOS-XE, FortiGate | v2.2.1 (Cisco), v1.0.1 (FortiGate) | Adopted | Best practice baseline |
| **DISA STIG** | Network device hardening | Current | Reference | Additional hardening guidance |
| **PCI DSS** | Payment card data security | 3.2.1 / 4.0 | **Mandatory** | **Required for compliance** |

---

## Cisco IOS-XE Hardening

Based on CIS Cisco IOS-XE 17.x Benchmark v2.2.1, the standards below cover three primary areas:

### Management Plane: Authentication and Authorization

| Configuration | CIS Control | STIG ID | PCI-DSS | Adoption Status | Notes |
| --- | --- | --- | --- | --- | --- |
| Enable AAA with TACACS+ primary, local fallback | 1.1 Enable Password Encryption | V-224297 | 8.1 | **Adopted** | Primary authentication via TACACS+; local users for failover |
| AAA login authentication on console, VTY, HTTP | 1.2 Manage AAA Local User Accounts | V-224298 | 8.1.1 | **Adopted** | All access methods require AAA login |
| AAA accounting for privileged commands/EXEC | 1.3 Ensure Accounting is Enabled | V-224300 | 8.2 | **Adopted** | Command and session accounting to centralized server |
| Local users with privilege level 1 requirement | 1.4 Use "enable secret" for elevated access | V-224299 | 8.2.1 | **Adopted** | Enable password required for level 15 access |

### Management Plane: Access Control

| Configuration | CIS Control | STIG ID | PCI-DSS | Adoption Status | Notes |
| --- | --- | --- | --- | --- | --- |
| SSH-only VTY access (disable Telnet) | 2.1.1 Disable telnet | V-224301 | 2.3 | **Adopted** | SSH v2 mandatory; Telnet explicitly disabled |
| VTY access restricted to approved subnets | 2.1.2 Restrict access by VTY ACL | V-224302 | 8.1 | **Adopted** | Management ACL applied; all non-approved sources denied |
| Console/VTY exec-timeout ≤10 minutes | 2.1.3 Set exec-timeout | V-224303 | 8.1.2 | **Adopted** | 10 minutes max idle time on management interfaces |
| Password encryption (scrypt algorithm) | 2.2 Encrypt all passwords | V-224304 | 8.2.3 | **Adopted** | Enable secret uses scrypt; local users encrypted |

### Management Plane: SNMP

| Configuration | CIS Control | STIG ID | PCI-DSS | Adoption Status | Notes |
| --- | --- | --- | --- | --- | --- |
| Remove default SNMP community strings | 2.3.1 Disable SNMP v1/v2c | V-224305 | 2.2.4 | **Adopted** | Public/private strings removed from all devices |
| SNMPv3 with authentication (SHA) & privacy (AES) | 2.3.2 Configure SNMPv3 | V-224306 | 8.2 | **Adopted** | Auth: SHA, Privacy: AES-128 minimum |
| SNMP source address ACL restriction | 2.3.3 Restrict SNMP sources | V-224307 | 8.1 | **Adopted** | Only NMS hosts permitted to query |
| SNMP traps for critical events | 2.3.4 Enable SNMP traps | V-224308 | 6.2 | **Adopted** | Trap destination: centralized syslog server |

### Management Plane: NTP

| Configuration | CIS Control | STIG ID | PCI-DSS | Adoption Status | Notes |
| --- | --- | --- | --- | --- | --- |
| Minimum 3 NTP servers with redundancy | 2.4.1 Configure NTP | V-224309 | 8.4 | **Adopted** | Primary + 2 secondary; geographically diverse |
| NTP authentication with MD5 keys | 2.4.2 Enable NTP authentication | V-224310 | 6.2 | **Adopted** | MD5 keys for all NTP peers; annual rotation |
| NTP source from loopback/mgmt interface | 2.4.3 NTP source interface | V-224311 | 8.4.1 | **Adopted** | Uses mgmt loopback; prevents traffic from data plane |
| NTP access-groups restrict NTP operations | 2.4.4 NTP access control | V-224311 | 8.4.1 | **Adopted** | peer/serve/serve-only/query-only restricted via ACLs |

### Management Plane: Banners

| Configuration | CIS Control | STIG ID | PCI-DSS | Adoption Status | Notes |
| --- | --- | --- | --- | --- | --- |
| MOTD and EXEC banners with security warning | 2.5 Configure login banners | V-224312 | 12.6 | **Adopted** | Both banners include unauthorized access warnings |

### Control Plane: Global Services

| Configuration | CIS Control | STIG ID | PCI-DSS | Adoption Status | Notes |
| --- | --- | --- | --- | --- | --- |
| SSH v2 only (disable v1) | 3.1 Configure SSH v2 | V-224313 | 2.2.4 | **Adopted** | SSH version 2 enforced; version 1 disabled |
| RSA 2048-bit minimum (4096 recommended) | 3.1.1 SSH key length | V-224314 | 8.2 | **Adopted** | 4096-bit keys generated for all devices |
| SSH timeout 60s, retry limit 3 | 3.1.2 SSH timeout & retries | V-224315 | 2.2.4 | **Adopted** | Prevents brute force; idle sessions terminated |
| TCP keepalives enabled (inbound/outbound) | 3.1.3 TCP keepalives | V-224316 | 2.2.4 | **Adopted** | Detects dead connections; removes stale sessions |
| Legacy services disabled (PAD, BootP, DHCP) | 3.2 Disable unnecessary services | V-224317 | 2.2.2 | **Adopted** | All unnecessary services explicitly disabled |

### Control Plane: Logging

| Configuration | CIS Control | STIG ID | PCI-DSS | Adoption Status | Notes |
| --- | --- | --- | --- | --- | --- |
| Syslog to centralized server | 4.1 Configure logging | V-224318 | 10.5 | **Adopted** | TCP/601 reliable transport (RFC 5426) |
| Console logging level: critical | 4.1.1 Console logging | V-224319 | 10.2 | **Adopted** | Reduces console noise; critical only |
| Syslog level: informational | 4.1.2 Syslog level | V-224320 | 10.2 | **Adopted** | Captures AAA events, config changes, errors |
| Debug timestamps (localtime + ms) | 4.1.3 Logging timestamps | V-224321 | 10.7 | **Adopted** | Enables event correlation across devices |
| Successful and failed login attempts logged | 4.1.4 Login logging | V-224322 | 10.2.1 | **Adopted** | AAA accounting captures both pass/fail |

**Access Control:**

- Configure SSH as the only transport for VTY access (disable Telnet)
- Restrict VTY access to approved management subnets using ACLs
- Configure exec-timeout to maximum 10 minutes on console and VTY lines
- Implement password encryption and enable secret (scrypt algorithm recommended)

**NTP Access Control:**

- Restrict NTP operations using access-groups to prevent unauthorized synchronization and queries
- `peer` (sync sources): `ACL_NTP_SERVERS` (allow approved NTP servers only)
- `serve`, `serve-only`, `query-only`: `ACL_DENY_ALL` (deny all clients)

```ios
ip access-list standard ACL_NTP_SERVERS
 permit 10.0.1.200
 permit 10.0.1.201
 permit 10.0.1.202
!
ntp access-group peer ACL_NTP_SERVERS
ntp access-group serve ACL_DENY_ALL
ntp access-group serve-only ACL_DENY_ALL
ntp access-group query-only ACL_DENY_ALL
!
```

**SNMP Hardening:**

- Remove default SNMP community strings (public/private)
- Configure SNMPv3 with authentication (SHA) and privacy (AES-128+)
- Restrict SNMP source addresses using ACLs
- Configure SNMP traps for critical events

**NTP Synchronization:**

- Configure minimum 3 NTP servers (with redundancy)
- Enable NTP authentication with MD5 keys
- Use loopback interface or dedicated management interface as NTP source

**Banners:**

- Configure MOTD banner (displayed before login)
- Configure EXEC banner (displayed after login)
- Banners must include unauthorized access warnings and device identification

### Control Plane

**Global Services:**

- Set hostname and domain name (prerequisites for SSH key generation)
- Generate RSA key pairs with minimum 2048-bit modulus (4096 recommended)
- Configure SSH version 2 only (disable SSH version 1)
- Configure SSH timeout and retry limits (60s timeout, 3 retries recommended)
- Enable TCP keepalives for inbound and outbound sessions
- Disable legacy services: PAD, BootP, DHCP

**Logging:**

- Enable syslog logging with centralized server destination
- Configure console logging level to "critical"
- Configure syslog level to "informational"
- Enable debug message timestamps (localtime with milliseconds)
- Log both successful and failed login attempts

---

## FortiOS Security Hardening

Based on CIS FortiGate Benchmark v1.0.1, the standards below cover system administration and
security profiles:

### System Administration: DNS & Zones

| Configuration | CIS Control | Adoption Status | Notes |
| --- | --- | --- | --- |
| Primary and secondary DNS configured | 1.1 Configure DNS | **Adopted** | Provides redundancy; both internal and external DNS |
| Intra-zone traffic disabled (enforce policy) | 1.2 Disable intra-zone traffic | **Adopted** | Forces all inter-zone traffic through policies; applies inspection |
| WAN management disabled | 1.3 Disable WAN management | **Adopted** | Management only via management interface; reduces attack surface |

### System Administration: System Settings

| Configuration | CIS Control | Adoption Status | Notes |
| --- | --- | --- | --- |
| Pre-login banner configured (not post-login) | 1.4 Configure login banners | **Adopted** | Pre-login only; post-login breaks config export |
| Timezone set to local | 1.5 Set timezone | **Adopted** | Enables proper log timestamp correlation |
| NTP configured with redundancy | 1.6 Configure NTP | **Adopted** | Minimum 1 NTP server; 2+ recommended for redundancy |
| Hostname configured | 1.7 Set hostname | **Adopted** | Device identification in logs and management |
| USB firmware/config auto-install disabled | 1.8 Disable USB auto-install | **Adopted** | Prevents unauthorized firmware injection |
| Static TLS keys disabled | 1.9 Disable static TLS keys | **Adopted** | Enforces unique certificates per device |
| Strong encryption globally enabled | 1.10 Enable strong encryption | **Adopted** | AES-256 default for all encrypted communications |
| TLS 1.3 for GUI management | 1.11 Configure TLS 1.3 | **Adopted** | GUI access only via TLS 1.3; HTTP disabled |
| Hostname hidden from login GUI | 1.12 Hide hostname from login | **Adopted** | Reduces information disclosure in login banner |

### System Administration: Password Policy

| Configuration | CIS Control | Adoption Status | Notes |
| --- | --- | --- | --- |
| Minimum 12 characters (mixed case, numeric, special) | 2.1 Password length & complexity | **Adopted** | Enforced for all admin accounts |
| Password expiration: 90 days | 2.2 Password expiration | **Adopted** | Aligns with PCI-DSS requirement; 90-day rotation |
| Password reuse disabled | 2.3 Password history | **Adopted** | Users cannot reuse previous passwords |
| Failed login lockout: 3 attempts × 60 seconds | 2.4 Account lockout | **Adopted** | Prevents brute force attacks; 1-hour lockout |

### Administrator Access: Admin Accounts

| Configuration | CIS Control | Adoption Status | Notes |
| --- | --- | --- | --- |
| Default "admin" account removed/renamed | 3.1 Remove default accounts | **Adopted** | Default admin disabled; admin_checkout created |
| Trusted host IP restrictions per account | 3.2 Restrict admin by IP | **Adopted** | Each admin limited to specific management subnet |
| Specific privilege profiles per user | 3.3 Role-based access control | **Adopted** | Network/Security admins; no superuser except emergencies |
| SSH and HTTPS only (Telnet/HTTP disabled) | 3.4 Disable insecure protocols | **Adopted** | HTTPS port 8443; SSH on default; Telnet/HTTP blocked |
| Admin idle timeout ≤5 minutes | 3.5 Session timeout | **Adopted** | 5-minute idle timeout; prevents unattended sessions |
| Default admin port changed (8443 recommended) | 3.6 Change default ports | **Adopted** | HTTPS moved to 8443; reduces trivial scanning |

### Administrator Access: Local-In Policies

| Configuration | CIS Control | Adoption Status | Notes |
| --- | --- | --- | --- |
| Local-in policies control mgmt traffic | 3.7 Local-in policies | **Adopted** | Restricts which sources reach FortiGate management |
| IPS inspection on mgmt interfaces | 3.8 IPS on mgmt traffic | **Adopted** | Virtual patch for mgmt protocols; blocks known exploits |

### SNMP Configuration

| Configuration | CIS Control | Adoption Status | Notes |
| --- | --- | --- | --- |
| SNMPv1/v2c disabled | 4.1 Disable SNMPv1/v2c | **Adopted** | Only SNMPv3 permitted; v1/v2c not accessible |
| SNMPv3 with SHA & AES encryption | 4.2 Configure SNMPv3 | **Adopted** | Auth: SHA, Privacy: AES; 128-bit minimum |
| Query disabled for trap-only users | 4.3 Trap-only users | **Adopted** | Monitoring accounts: trap-only, no query permission |
| SNMP sources restricted to NMS hosts | 4.4 Restrict SNMP sources | **Adopted** | ACL limits queries to approved management networks |
| SNMP traps for memory usage | 4.5 Enable SNMP traps | **Adopted** | CPU/memory alerts sent to centralized server |

### High Availability: HA Configuration

| Configuration | CIS Control | Adoption Status | Notes |
| --- | --- | --- | --- |
| Active-Passive mode (not Active-Active) | 5.1 HA deployment mode | **Adopted** | Single active device reduces split-brain risk |
| Device priority: 250 (primary), 200 (secondary) | 5.2 HA priority | **Adopted** | Clear failover hierarchy; preemption enabled |
| Group-ID in appropriate range (DC: 100-199) | 5.3 HA Group-ID | **Adopted** | Unique per site; prevents accidental grouping |
| Session pickup enabled | 5.4 Session pickup | **Adopted** | Active sessions transferred to secondary on failover |
| Monitor critical interfaces | 5.5 Monitor critical interfaces | **Adopted** | Primary & internal interfaces monitored |
| Two heartbeat links (dedicated + copper) | 5.6 Heartbeat redundancy | **Adopted** | Prevents single heartbeat link failure |
| Heartbeat priority: 100 (primary), 50 (secondary) | 5.7 Heartbeat priority | **Adopted** | Prevents flapping during network issues |
| HA Direct disabled (allow individual mgmt) | 5.8 Disable HA Direct | **Adopted** | Secondary device manageable independently |

### Security Policies: Firewall Rules

| Configuration | CIS Control | Adoption Status | Notes |
| --- | --- | --- | --- |
| Logging enabled on all policies | 6.1 Policy logging | **Adopted** | All policies (including implicit deny) logged |
| "ALL" service never used | 6.2 Explicit services | **Adopted** | Each policy specifies exact protocols (TCP 443, etc.) |
| Unused policies reviewed & removed | 6.3 Policy audit | **Adopted** | Quarterly review; removes technical debt |
| IPS sensor on WAN-facing policies | 6.4 WAN IPS protection | **Adopted** | WAN→Internal policies include IPS inspection |

### Security Policies: Threat Detection

| Configuration | CIS Control | Adoption Status | Notes |
| --- | --- | --- | --- |
| IPS security profile on inter-network traffic | 6.5 IPS on inter-zone | **Adopted** | Protects internal network-to-network flows |
| Botnet detection configured (monitor or block) | 6.6 Botnet protection | **Adopted** | Monitor mode active; escalates to block on findings |
| Anti-virus enabled on applicable policies | 6.7 Anti-virus | **Adopted** | Enabled on HTTP/SMTP/FTP policies |

### Logging and Reporting

| Configuration | CIS Control | Adoption Status | Notes |
| --- | --- | --- | --- |
| Event logging enabled | 7.1 Enable event logging | **Adopted** | All system events logged (login, config, failures) |
| Centralized syslog (reliable transport) | 7.2 Syslog to server | **Adopted** | TCP/601 reliable delivery (RFC 5426) |
| Syslog source interface specified | 7.3 Syslog source | **Adopted** | Uses dedicated management IP; consistent in logs |
| Syslog port (TCP/601) | 7.4 Syslog port | **Adopted** | Port 601 TCP reliable syslog; guaranteed delivery |

---

---

## SSH Hardening

Both Cisco and FortiGate require strong SSH configuration. These are derived from CIS
recommendations and NIST SP 800-53 cryptographic standards.

### Cisco IOS-XE SSH Standards

```ios
crypto key generate rsa modulus 4096
ip ssh version 2
ip ssh server algorithm authentication keyboard
ip ssh server algorithm kex ecdh-sha2-nistp521 ecdh-sha2-nistp384
ip ssh server algorithm hostkey rsa-sha2-512 rsa-sha2-256
ip ssh server algorithm encryption aes256-gcm aes256-ctr
ip ssh server algorithm mac hmac-sha2-512 hmac-sha2-256
ip ssh server algorithm publickey ecdsa-sha2-nistp521 ecdsa-sha2-nistp384
ip ssh timeout 60
ip ssh authentication-retries 3
```

### FortiOS SSH Standards

```fortios
config system global
    set ssh-enc-algo chacha20-poly1305@openssh.com aes256-ctr aes256-gcm@openssh.com
    set ssh-kex-algo diffie-hellman-group-exchange-sha256 curve25519-sha256@libssh.org ecdh-sha2-nistp256 ecdh-sha2-nistp384 ecdh-sha2-nistp521
    set ssh-mac-algo hmac-sha2-256 hmac-sha2-256-etm@openssh.com hmac-sha2-512 hmac-sha2-512-etm@openssh.com
end
```

---

## Network Access Control (NAC)

**Status:** Not implemented. NAC is not currently in use at Checkout. Future evaluation may be
considered for guest network access control or compliance with enhanced security frameworks.

---

## Implementation Guides

The standards above are implemented through detailed configuration guides for each platform:

### Cisco IOS-XE Configuration

- [AAA Configuration & TACACS+](../cisco/cisco_aaa_config.md) — Implements Management Plane AAA
- [SNMP Configuration](../cisco/cisco_snmp_config.md) — Implements SNMP hardening standards
- [Syslog Configuration](../cisco/cisco_syslog_config.md) — Implements centralized logging
- [SSH Hardening](../application/ssh.md) — Implements SSH algorithm hardening
- [AAA Minimal](../cisco/aaa-minimal.md) — Quick reference for AAA setup

### FortiOS Configuration

- [FortiGate Admin Access](../fortigate/aaa-minimal.md) — Implements administrator access controls
- [FortiGate Firewall Policies](../fortigate/fortigate_firewall_policies.md) — Implements security policies
- [FortiGate HA Configuration](../fortigate/fortigate_ha.md) — Implements high availability standards
- [FortiGate Security Hardening](../fortigate/security-hardening-minimal.md) — Quick reference for hardening
- [FortiGate SSH Hardening](../fortigate/ssh-minimal.md) — Implements SSH standards

### Standards and Protocols

- [SNMP Monitoring Standards](../checkout-standards/snmp-standards.md) — SNMPv3 implementation details
- [Syslog & Monitoring Standards](../checkout-standards/syslog-monitoring-standards.md) — Logging
- [Naming Conventions](../checkout-standards/naming-conventions.md) — ACL naming standards
- [BGP Standards](../checkout-standards/bgp-standards.md) — BGP authentication and route filtering

---

## Adoption Status Summary

All Checkout standards documented above are marked with adoption status:

- **Adopted:** Configuration is implemented and enforced across all devices of that type
- **Partially Adopted:** Configuration exists but with exceptions or inconsistent deployment
- **Not Adopted:** Configuration not yet implemented; requires deployment planning
- **N/A:** Control does not apply to Checkout environment

### Cisco IOS-XE Adoption

| Area | Status | Notes |
| --- | --- | --- |
| Management Plane (AAA, SSH, SNMP, NTP, Banners) | **Fully Adopted** | All controls per CIS v2.2.1 |
| Control Plane (SSH hardening, Logging, Services) | **Fully Adopted** | SSH v2, debug logging, legacy disabled |
| Data Plane (BGP auth, route filtering) | **Fully Adopted** | BGP MD5 + prefix-lists on all peers |

### FortiOS Adoption

| Area | Status | Notes |
| --- | --- | --- |
| System Administration (DNS, NTP, Password Policy) | **Fully Adopted** | All controls implemented per CIS v1.0.1 |
| Administrator Access (SSH/HTTPS only, IP restrictions) | **Fully Adopted** | Default admin disabled; trusted hosts per account |
| SNMP Configuration (SNMPv3 only) | **Fully Adopted** | v1/v2c disabled; SHA+AES encryption |
| High Availability (Active-Passive, Session pickup) | **Fully Adopted** | HA configured per Checkout standards |
| Security Policies (IPS, Logging, Botnet detection) | **Fully Adopted** | All policies logged; WAN-facing has IPS |
| Logging and Reporting (Centralized syslog) | **Fully Adopted** | TCP/601 reliable delivery (RFC 5426) |

### Compliance Verification Checklist

**CIS Benchmark Compliance (Cisco):**

- [x] Management Plane: AAA enabled, SSH restricted, SNMP hardened, NTP configured
- [x] Control Plane: SSH v2 hardened, logging centralized, NTP authentication enabled
- [x] Data Plane: BGP authentication configured, route filtering applied
- [x] Banners: MOTD and EXEC banners with security warnings

**CIS Benchmark Compliance (FortiGate):**

- [x] System Administration: DNS, NTP, hostname, encryption configured
- [x] Administrator Access: Default admin removed, trusted host restrictions, idle timeout
- [x] SNMP: SNMPv3 only, authentication and privacy enabled
- [x] Security Policies: All policies logged, no "ALL" services, IPS on WAN

**STIG Compliance:**

- [x] DISA STIG alignment verified for applicable controls (V-224297 through V-224322)
- [x] Configuration changes logged and change control documented
- [x] Annual review of STIG applicability and compliance status scheduled

**PCI-DSS Compliance:**

- [x] Access controls (8.1, 8.2, 8.2.1): AAA, SSH, password policy
- [x] Logging and monitoring (10.2, 10.5, 10.7): Syslog, timestamps, event logging
- [x] Network segmentation (2.2.2, 2.3): Unused services disabled, SNMP hardened
- [x] Encryption (2.2.4): TLS 1.3, SSH v2, AES-256 encryption

---

## Disaster Recovery

**Configuration Backup Strategy:**

Checkout implements multi-layered configuration backup for resilience:

1. **Centralized Backup (LogicMonitor)** — Primary backup mechanism for all network devices
   - Automated daily backup to LogicMonitor monitoring platform
   - Retained for extended retention period (90+ days)
   - Enables quick comparison and change tracking across devices

2. **Local Archive (Cisco IOS-XE)** — Redundant on-device backup
   - Cisco devices configured with archive feature for local startup config retention
   - Multiple versions stored locally; enables quick restore without external access
   - Fallback if centralized backup access is unavailable

**Data Center Failover:**

- DCs are taken out of action via **application-level traffic shifting**, not device failover
- Applications route to alternate DCs during maintenance or disaster
- Network provides stable routing; application layer handles failover logic
- Avoids complex failover automation; simplifies operational procedures

**Out-of-Band (OOB) Access:**

- **Perle/Vertiv Cyclades console servers** provide OOB access to all network devices
- Enables management access during network outage (management network unavailable)
- Independent network path; does not depend on primary management infrastructure
- Used for emergency recovery, initial configuration, and troubleshooting

---

## Related Standards and Implementation Guides

**Checkout Standards:**

- [Equipment Configuration](equipment-config.md) — Hardware standards and lifecycle
- [Naming Conventions](naming-conventions.md) — ACL and object naming for security
- [BGP Standards](bgp-standards.md) — BGP authentication and secure routing
- [SNMP Standards](snmp-standards.md) — SNMPv3 configuration and monitoring access
- [Syslog Standards](syslog-monitoring-standards.md) — Centralized logging

**Cisco IOS-XE Implementation:**

- [AAA/TACACS+ Configuration](../cisco/cisco_aaa_config.md)
- [SNMP Configuration](../cisco/cisco_snmp_config.md)
- [Syslog Configuration](../cisco/cisco_syslog_config.md)
- [SSH Hardening](../application/ssh.md)

**FortiOS Implementation:**

- [FortiGate Admin Access & Hardening](../fortigate/aaa-minimal.md)
- [FortiGate Firewall Policies & IPS](../fortigate/fortigate_firewall_policies.md)
- [FortiGate High Availability](../fortigate/fortigate_ha.md)
- [FortiGate SSH Standards](../fortigate/ssh-minimal.md)

**Application Protocols:**

- [SSH](../application/ssh.md)
- [SNMP](../application/snmp.md)
- [Syslog](../application/syslog.md)
