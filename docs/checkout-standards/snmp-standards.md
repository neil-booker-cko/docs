# SNMP Monitoring Standards

SNMPv3 configuration standards for network device monitoring. All devices must use SNMPv3 with
authentication and encryption; no traps are configured. SNMP queries are read-only with source
address restrictions via ACLs.

---

## SNMP Version & Security

**Standard:** SNMPv3 only (no SNMPv1 or SNMPv2c in production).

| Parameter | Standard | Notes |
| --- | --- | --- |
| Version | SNMPv3 | Authentication & encryption mandatory |
| Authentication | HMAC-SHA | SHA-256 or SHA-512 preferred |
| Encryption | AES-128 minimum | AES-256 recommended |
| Access Mode | Read-Only | Query-only; no write access |
| Traps | Disabled | No SNMP traps configured |
| Source Restriction | ACL_SNMP_IN (Cisco) | Limit queries to utility servers |
| NMS Servers (Utility) | 10.13.1.147, 10.13.2.116, 10.13.2.147 | Primary, secondary, tertiary (3-server redundancy) |

---

## SNMP View (Read-Only)

**Standard:** Create restricted SNMP view to allow read-only queries on specific MIB subtrees.
Block write access and sensitive system information.

### Allowed MIB Subtrees (Read-Only)

| MIB | OID | Purpose |
| --- | --- | --- |
| System | 1.3.6.1.2.1.1 | Device name, uptime, description |
| Interfaces | 1.3.6.1.2.1.2 | Interface status, counters, traffic |
| IP (unicast) | 1.3.6.1.2.1.4 | IP routing, forwarding table |
| TCP | 1.3.6.1.2.1.6 | TCP connection table |
| UDP | 1.3.6.1.2.1.7 | UDP port table |
| SNMP | 1.3.6.1.2.1.11 | SNMP statistics (read-only) |

### Restricted MIB Subtrees (Denied)

- sysServices (1.3.6.1.2.1.1.7) — exposed services
- ifName (1.3.6.1.2.1.31.1.1.1) — can leak interface naming
- ENTITY-MIB — hardware details
- CONFIG objects — system configuration

---

## SNMPv3 Authentication & Encryption by Platform

SNMPv3 uses two separate keys: an **auth key** (HMAC for message integrity) and a **priv key**
(payload encryption). Both algorithm and key must match exactly between device and NMS — a mismatch
causes silent authentication failure. LogicMonitor (the NMS) must be configured with the same
algorithm and credentials as each polled device.

**SHA naming note:** In IOS-XE CLI, `auth sha` = SHA-1 (HMAC-SHA-96, RFC 3414). Stronger variants
require explicit keywords: `auth sha256`, `auth sha384`, `auth sha512` (IOS-XE 16.6+). In FortiOS,
`set auth-proto sha` = SHA-1; `sha256`/`sha384`/`sha512` are separate values.

| Platform | Auth Options | Priv Options | **Checkout Standard** | Notes |
| --- | --- | --- | --- | --- |
| **Cisco IOS-XE (17.x)** | MD5, SHA-1, SHA-256, SHA-384, SHA-512 | DES, 3DES, AES-128, AES-192, AES-256 | **SHA-256 + AES-256** | `auth sha256 priv aes 256` |
| **Cisco IOS (15.2(7)E)** | MD5, SHA-1 | DES, 3DES, AES-128, AES-192, AES-256 | **SHA-1 + AES-128** | SHA-256 not available in classic IOS |
| **FortiOS** | MD5, SHA-1, SHA-224, SHA-256, SHA-384, SHA-512 | DES, AES-128, AES-256 | **SHA-256 + AES-256** | `auth-proto sha256`, `priv-proto aes256` |
| **LogicMonitor (NMS)** | MD5, SHA-1, SHA-256, SHA-512 | DES, 3DES, AES-128, AES-256 | **Match device profile** | Two profiles required — see below |
| **Vertiv ACS8000 (2.28.3+)** | MD5, SHA-1, SHA-256, SHA-512 | DES, AES-128, AES-192, AES-256 | **SHA-256 + AES-256** | SHA-256/AES-256 added in firmware 2.28.3 |
| **Perle Console Server** | MD5, SHA-1 | DES, AES-128 | **SHA-1 + AES-128** | Platform ceiling; no SHA-256 available |
| **Meraki** | MD5, SHA-1 | DES, AES-128 | **SHA-1 + AES-128** | Platform ceiling; no SHA-256 available |
| **Palo Alto (PAN-OS)** | SHA-1 | AES-128, AES-192, AES-256 | **SHA-1 + AES-256** | SHA-256 auth not confirmed in PAN-OS docs |
| **UniFi** | SHA-1 | AES-128 | **SHA-1 + AES-128** | Single password used for both auth and priv |
| **APC NMC3 (UPS + PDU)** | MD5, SHA-1, SHA-256 | DES, AES-128, AES-256 | **SHA-256 + AES-256** | UPS and PDU use same NMC3 platform. SHA-256/AES-256 confirmed in Sep 2025 firmware docs |

**Do not use:** MD5 (auth), DES or 3DES (priv) on any platform — all are cryptographically broken.

### LogicMonitor Credential Profiles

Because Meraki and Vertiv are capped at SHA-1 + AES-128, LogicMonitor must maintain two SNMP
credential profiles. Assign devices to the appropriate profile:

| LM Profile | Platforms | Auth | Priv |
| --- | --- | --- | --- |
| `SNMP_STRONG` | Cisco IOS-XE, FortiOS, Vertiv ACS8000 (fw 2.28.3+), APC NMC3 | SHA-256 | AES-256 |
| `SNMP_COMPAT` | Cisco IOS (classic), Meraki, Perle | SHA-1 | AES-128 |

Configure profiles under **Settings > Credentials > SNMPv3** in LogicMonitor. Apply via device
properties or device group inheritance.

---

## Cisco IOS-XE SNMP Configuration

### Checkout Standard Configuration

Use the following Checkout-standard configuration for all devices:

```ios
snmp-server view All_MIB_View .1 included
snmp-server location "Equinix DC4"
snmp-server contact "CKO Network Services"
snmp ifindex persist
!
ip access-list standard ACL_SNMP_IN
 permit 10.0.1.50
 deny any
!
snmp-server group SNMP_RO_GRP v3 auth read All_MIB_View access ACL_SNMP_IN
snmp-server user snmp_monitor SNMP_RO_GRP v3 auth sha256 MyAuthPass123 priv aes 256 MyPrivPass456
snmp-server source-interface all 10.0.1.10
!
```

### Step 1: Create SNMP View (All MIBs — Checkout Standard)

Use `All_MIB_View` to allow read-only access to all available MIBs:

```ios
snmp-server view All_MIB_View .1 included
!
```

### Step 2: Create ACL for SNMP Source Restriction

Restrict SNMP queries to the utility servers (primary, secondary, tertiary):

```ios
ip access-list standard ACL_SNMP_IN
 permit 10.13.1.147
 permit 10.13.2.116
 permit 10.13.2.147
 deny any
!
```

### Step 3: Create SNMPv3 Group with Read-Only View

Use group name `SNMP_RO_GRP` (Checkout standard):

```ios
snmp-server group SNMP_RO_GRP v3 auth read All_MIB_View access ACL_SNMP_IN
!
```

### Step 4: Create SNMPv3 User

```ios
snmp-server user snmp_monitor SNMP_RO_GRP v3 auth sha256 MyAuthPass123 priv aes 256 MyPrivPass456
!
```

### Step 5: Set Device Identification (Checkout Standard)

Configure location, contact, and ifindex persistence:

```ios
snmp-server location "Equinix DC4"
snmp-server contact "CKO Network Services"
snmp ifindex persist
!
```

### Step 6: Configure SNMP Source Interface

```ios
snmp-server source-interface all 10.0.1.10
!
```

### Complete Checkout Standard Configuration

```ios
snmp-server view All_MIB_View .1 included
snmp-server location "Equinix DC4"
snmp-server contact "CKO Network Services"
snmp ifindex persist
!
ip access-list standard ACL_SNMP_IN
 permit 10.13.1.147
 permit 10.13.2.116
 permit 10.13.2.147
 deny any
!
snmp-server group SNMP_RO_GRP v3 auth read All_MIB_View access ACL_SNMP_IN
snmp-server user snmp_monitor SNMP_RO_GRP v3 auth sha256 MyAuthPass123 priv aes 256 MyPrivPass456
snmp-server source-interface all 10.0.1.10
!
```

---

## FortiGate SNMP Configuration

### SNMPv3 User (Read-Only)

```fortios
config system snmp user
    edit "nms_monitor"
        set security-level auth-priv
        set auth-proto sha256
        set auth-pwd MyAuthPass123
        set priv-proto aes256
        set priv-pwd MyPrivPass456
        set trap-status disable
        set ha-direct enable
    next
end
```

**Note:** `set auth-proto sha` configures SHA-1 (not SHA-256) — use `sha256` explicitly. `set
priv-proto aes` configures AES-128 — use `aes256` for AES-256.

### SNMP Community (Legacy, if needed)

**Note:** Use SNMPv3 users above. Community strings are deprecated but shown for reference:

```fortios
config system snmp community
    edit 1
        set name "read-only-community"
        set permission read-only
        set events port-topology-change cpu-memory-usage
    next
end
```

---

## Cisco IOS (Classic) SNMP Configuration

Cisco IOS 15.2(7)E (used on Catalyst 2960X and similar fixed-configuration switches) does not
support SHA-256 authentication — SHA-1 and AES-128 are the strongest available options.

```ios
ip access-list standard ACL_SNMP_IN
 permit 10.13.1.147
 permit 10.13.2.116
 permit 10.13.2.147
 deny any
!
snmp-server view All_MIB_View .1 included
snmp-server group SNMP_RO_GRP v3 auth read All_MIB_View access ACL_SNMP_IN
snmp-server user snmp_monitor SNMP_RO_GRP v3 auth sha MyAuthPass123 priv aes 128 MyPrivPass456
snmp-server location "<DC>-<RACK>-<POSITION>"
snmp-server contact "CKO Network Services"
snmp ifindex persist
!
```

Assign this device to the `SNMP_COMPAT` profile in LogicMonitor (SHA-1 + AES-128).

---

## LogicMonitor SNMP Configuration

LogicMonitor polls devices using SNMPv3 credentials set as device properties — either directly on
a device or inherited from a device group. Maintain two credential profiles to match the two
platform capability tiers.

### Device Properties

| LM Property | Purpose | Example Value |
| --- | --- | --- |
| `snmp.security` | SNMPv3 username | `snmp_monitor` |
| `snmp.auth` | Authentication protocol | `SHA256` or `SHA` |
| `snmp.authToken` | Authentication password | `<AUTH_PASSWORD>` |
| `snmp.priv` | Encryption protocol | `AES256` or `AES` |
| `snmp.privToken` | Encryption password | `<PRIV_PASSWORD>` |
| `snmp.version` | SNMP version (auto-detected) | `v3` |
| `snmp.port` | UDP port if non-standard | `161` (default) |

**Version auto-detection:** `snmp.version` is set automatically on first discovery to whichever
version responds. It can be overridden manually; if new credentials fail, LM falls back to the
previous working setting.

**Context properties** (`snmp.contextName`, `snmp.contextEngineID`) are available for SNMPv3
context-aware queries but are not in use — leave unset.

### Credential Profiles

Navigate to **Settings > Credentials > SNMPv3** and create two profiles:

**Profile: SNMP_STRONG** (for Cisco IOS-XE and FortiOS):

| Field | Value |
| --- | --- |
| `snmp.security` | `snmp_monitor` |
| `snmp.auth` | `SHA256` |
| `snmp.authToken` | `<AUTH_PASSWORD>` |
| `snmp.priv` | `AES256` |
| `snmp.privToken` | `<PRIV_PASSWORD>` |

**Profile: SNMP_COMPAT** (for Cisco IOS classic, Meraki, Perle — SHA-256 not available):

| Field | Value |
| --- | --- |
| `snmp.security` | `snmp_monitor` |
| `snmp.auth` | `SHA` |
| `snmp.authToken` | `<AUTH_PASSWORD>` |
| `snmp.priv` | `AES` |
| `snmp.privToken` | `<PRIV_PASSWORD>` |

Assign profiles at the device group level so devices inherit automatically. Override at device
level only where a device uses non-standard credentials.

---

## Vertiv ACS8000 SNMP Configuration

Vertiv ACS8000 running firmware 2.28.3 or later supports SHA-256 and AES-256. Configure via
the web GUI — CLI syntax for SNMPv3 on this firmware has not been verified and should be
confirmed against the device before use.

**Web GUI:** Network > SNMP > SNMPv3 Users > Add

| Field | Value |
| --- | --- |
| Username | `snmp_monitor` |
| Authentication Protocol | SHA-256 |
| Authentication Password | `<AUTH_PASSWORD>` |
| Privacy Protocol | AES-256 |
| Privacy Password | `<PRIV_PASSWORD>` |
| Access | Read Only |

**Restrict SNMP source:** Network > SNMP > Access Control — permit utility server IPs only
(10.13.1.147, 10.13.2.116, 10.13.2.147).

Assign to the `SNMP_STRONG` profile in LogicMonitor.

---

## Perle Console Server SNMP Configuration

Perle console servers are limited to SHA-1 and AES-128 — no SHA-256 available.

```text
set snmp location <LOCATION>
set snmp contact <CONTACT>

set snmp readonly user <USERNAME>
set snmp v3-security type readonly security-level auth/priv
set snmp v3-security type readonly auth-algorithm sha1
set snmp v3-security type readonly privacy-algorithm aes
set snmp v3-security type readonly auth-password
set snmp v3-security type readonly privacy-password
```

Passwords are prompted interactively — not set inline.

Assign to the `SNMP_COMPAT` profile in LogicMonitor.

---

## Meraki SNMP Configuration

Meraki SNMPv3 is configured organisation-wide in the Meraki Dashboard and is limited to SHA-1
and AES-128.

**Dashboard:** Organization > Settings > SNMP

| Field | Value |
| --- | --- |
| SNMP Version | SNMPv3 |
| Username | `snmp_monitor` |
| Auth Mode | SHA |
| Auth Password | `<AUTH_PASSWORD>` |
| Privacy Mode | AES128 |
| Privacy Password | `<PRIV_PASSWORD>` |

**Access restriction:** Meraki does not support SNMP source ACLs at the device level. Restrict
access at the network perimeter — permit UDP/161 only from utility server IPs.

Assign Meraki devices to the `SNMP_COMPAT` profile in LogicMonitor.

---

## Datadog SNMP Agent Configuration

Datadog polls devices via the Datadog Agent running on a utility server. Configuration is in
`/etc/datadog-agent/conf.d/snmp.d/conf.yaml` (permissions: `644`, owner: `dd-agent`).

```bash
instances:
  - ip_address: "<IP_ADDRESS>"
    user: "snmp_monitor"
    authProtocol: SHA256
    authKey: "<AUTH_PASSWORD>"
    privProtocol: AES256
    privKey: "<PRIV_PASSWORD>"
```

**Profile additions:** The `_base.yaml` profile (`/etc/datadog-agent/conf.d/snmp.d/profiles/`) should
include `sysContact` and `sysLocation` metric tags:

```bash
metric_tags:
  - OID: 1.3.6.1.2.1.1.4.0
    symbol: sysContact
    tag: snmp_contact
  - OID: 1.3.6.1.2.1.1.5.0
    symbol: sysName
    tag: snmp_host
  - OID: 1.3.6.1.2.1.1.6.0
    symbol: sysLocation
    tag: snmp_location
```

Restart the Datadog Agent after any config change: `systemctl restart datadog-agent`.

---

## SNMPd (Linux) Configuration

Linux hosts running `snmpd` (net-snmp) are limited to SHA-1 and AES-128 on most distributions.
SHA-256/AES-256 requires net-snmp 5.8+.

**Create SNMPv3 user (run before starting snmpd):**

```bash
net-snmp-config --create-snmpv3-user -ro \
  -A <AUTH_PASSWORD> -a SHA \
  -X <PRIV_PASSWORD> -x AES \
  snmp_monitor
```

**`/etc/snmp/snmpd.conf` — add or update:**

```bash
sysLocation    <LOCATION>
sysContact     <CONTACT>
agentaddress   udp:161,udp6:[::1]:161
```

Restart snmpd after changes: `systemctl restart snmpd`.

Assign Linux hosts to the `SNMP_COMPAT` profile in LogicMonitor.

---

## SNMP Access Control

### NMS Source Restriction (Cisco ACL)

Only utility servers can query SNMP (primary, secondary, tertiary):

```ios
ip access-list standard ACL_SNMP_IN
 permit 10.13.1.147
 permit 10.13.2.116
 permit 10.13.2.147
 deny any
!
```

### Firewall Policy (FortiGate)

Restrict SNMP traffic via firewall policy:

```fortios
config firewall policy
    edit 1
        set name "Allow-SNMP-from-NMS"
        set srcintf "port1"
        set dstintf "port2"
        set srcaddr "NMS-Subnet"
        set dstaddr "all"
        set action accept
        set schedule "always"
        set service "SNMP"
        set logtraffic all
    next
end
```

---

## SNMP Query Testing

### Verify SNMPv3 Configuration

**From NMS (10.0.1.50):**

```bash
# Test SNMPv3 connectivity
snmpwalk -v3 -u nms_monitor -l authPriv -a SHA-256 -A MyAuthPass123 -x AES-256 -X MyPrivPass456 10.0.1.10 .1.3.6.1.2.1.1

# Expected output (sysDescr):
SNMPv3-User: nms_monitor
Engine ID: 8000070903...
System Description: Cisco IOS XE 17.x...
```

### Verify Read-Only Access

```bash
# Should succeed (read)
snmpget -v3 -u nms_monitor -l authPriv -a SHA-256 -A MyAuthPass123 -x AES-256 -X MyPrivPass456 10.0.1.10 1.3.6.1.2.1.1.1.0

# Should fail (write)
snmpset -v3 -u nms_monitor -l authPriv -a SHA-256 -A MyAuthPass123 -x AES-256 -X MyPrivPass456 10.0.1.10 1.3.6.1.2.1.1.5.0 s "New-Name"
```

---

## SNMP Traps (NOT USED)

**Standard:** SNMP traps are **not configured**. All monitoring is pull-based (NMS queries devices).

- ❌ **No trap destinations** configured
- ❌ **No trap events** sent from devices
- ❌ **No trap forwarding** from FortiGate

Monitoring relies on:

- **Polling:** NMS queries devices on intervals (typically 5-minute intervals)
- **Syslog:** Critical events sent to syslog servers (see Syslog Standards)
- **Alerting:** NMS dashboards and alert rules on metrics

---

## SNMP Security Best Practices

### Key Management

- Use strong, unique passwords (minimum 12 characters, mixed case/numbers/special)
- Store credentials in LastPass (not in config files or documentation)
- Rotate credentials after any suspected compromise or significant personnel change
- Document credential changes in the change log

### Authentication & Encryption

- Use SHA-256 minimum for authentication (SHA-1 only where platform cannot support SHA-256 — Tier 2)
- Always use AES (not DES) for encryption; AES-256 preferred, AES-128 minimum for Tier 2 platforms
- Never use SNMPv1 or SNMPv2c plaintext community strings

### Access Control

- Restrict SNMP to NMS subnet only (ACL_SNMP_IN)
- Disable SNMP on untrusted interfaces
- Use read-only views (no write access for operators)
- Monitor SNMP access attempts in syslog

---

## Troubleshooting

### SNMP Query Fails

**Checklist:**

1. **Credentials:** Verify username, auth password, priv password
2. **Source IP:** Confirm NMS IP is allowed in ACL_SNMP_IN
3. **Firewall policy:** Check FortiGate allows UDP/161 from NMS
4. **SNMP enabled:** Verify SNMP service running on device
5. **MIB view:** Confirm OID is in allowed read-only view

### SNMP Slow Queries

- Increase NMS polling interval
- Reduce number of queried OIDs per poll
- Check device CPU (SNMP is CPU-intensive)
- Verify network latency to NMS

---

## Related Standards

- [Syslog & Monitoring Standards](syslog-monitoring-standards.md) — Syslog configuration
- [Security Hardening](security-hardening.md) — SNMPv3 authentication/encryption
- [Naming Conventions](naming-conventions.md) — ACL naming (ACL_SNMP_IN)
