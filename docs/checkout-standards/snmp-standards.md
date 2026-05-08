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

Different platforms support different authentication and encryption algorithms. Use the most secure
option available for each platform. **Preferred: SHA for authentication, AES-128 (minimum) or
AES-256 (recommended) for encryption.**

| Platform | Supported Authentication | Supported Encryption |
| --- | --- | --- |
| **Cisco IOS-XE (17.6, 17.9, 17.12)** | MD5, SHA | DES, 3DES, AES-128, AES-192, AES-256 |
| **Cisco IOS (15.2(7)E)** | MD5, SHA | DES, 3DES, AES-128, AES-192, AES-256 |
| **FortiOS** | MD5, SHA, SHA224, SHA256, SHA384, SHA512 | DES, AES-128, AES-256 |
| **Meraki** | MD5, SHA | DES, AES-128 |
| **APC UPS/PDU** | MD5, SHA | DES, AES-128 |
| **Perle Serial/Console** | MD5, SHA | DES, AES-128 |
| **Palo Alto** | SHA | AES-128 |
| **UniFi** | SHA | AES-128 |
| **Vertiv Avocent** | MD5, SHA | DES, AES-128 |
| **SNMPd (Linux)** | MD5, SHA | DES, AES-128 |
| **Datadog Agent** | MD5, SHA, SHA224, SHA256, SHA384, SHA512 | DES, AES, AES-192, AES-256 |
| **LogicMonitor** | MD5, SHA, SHA224, SHA256, SHA384, SHA512 | DES, 3DES, AES-128, AES-192, AES-256 |

### Selection Guidance

**For Cisco IOS-XE (primary platform):**

- Authentication: **SHA** (recommended over MD5)
- Encryption: **AES-128** (minimum) or **AES-256** (recommended)

**For FortiOS:**

- Authentication: **SHA256** or **SHA512** (if supported by remote SNMP manager)
- Encryption: **AES-256** (recommended over AES-128)

**For other platforms (Meraki, APC, Perle, etc.):**

- Authentication: **SHA** (only secure option; avoid MD5)
- Encryption: **AES-128** (use AES over DES)

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
snmp-server user snmp_monitor SNMP_RO_GRP v3 auth sha MyAuthPass123 priv aes 128 MyPrivPass456
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
snmp-server user snmp_monitor SNMP_RO_GRP v3 auth sha MyAuthPass123 priv aes 128 MyPrivPass456
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
snmp-server user snmp_monitor SNMP_RO_GRP v3 auth sha MyAuthPass123 priv aes 128 MyPrivPass456
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
        set auth-proto sha
        set auth-pwd MyAuthPass123
        set priv-proto aes
        set priv-pwd MyPrivPass456
        set permission read-only
    next
end
```

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
snmpwalk -v3 -u nms_monitor -l authPriv -a SHA -A MyAuthPass123 -x AES -X MyPrivPass456 10.0.1.10 .1.3.6.1.2.1.1

# Expected output (sysDescr):
SNMPv3-User: nms_monitor
Engine ID: 8000070903...
System Description: Cisco IOS XE 17.x...
```

### Verify Read-Only Access

```bash
# Should succeed (read)
snmpget -v3 -u nms_monitor -l authPriv -a SHA -A MyAuthPass123 -x AES -X MyPrivPass456 10.0.1.10 1.3.6.1.2.1.1.1.0

# Should fail (write)
snmpset -v3 -u nms_monitor -l authPriv -a SHA -A MyAuthPass123 -x AES -X MyPrivPass456 10.0.1.10 1.3.6.1.2.1.1.5.0 s "New-Name"
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

- Rotate SNMP credentials annually
- Use strong, unique passwords (minimum 12 characters, mixed case/numbers/special)
- Store credentials securely (not in config files, use encrypted vaults)
- Document credential rotation in change log

### Authentication & Encryption

- Always use SHA (not MD5) for authentication
- Always use AES (not DES) for encryption
- Use AES-256 for additional security if performance permits
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
