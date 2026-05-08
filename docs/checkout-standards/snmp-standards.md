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
| Source Restriction | ACL_SNMP_IN (Cisco) | Limit queries to approved NMS hosts |
| NMS Server | 10.0.1.50 | Network Management System (read-only queries only) |

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

## Cisco IOS-XE SNMP Configuration

### Step 1: Create SNMP View (Read-Only)

```ios
snmp-server view RO-View 1.3.6.1.2.1.1 included
snmp-server view RO-View 1.3.6.1.2.1.2 included
snmp-server view RO-View 1.3.6.1.2.1.4 included
snmp-server view RO-View 1.3.6.1.2.1.6 included
snmp-server view RO-View 1.3.6.1.2.1.7 included
snmp-server view RO-View 1.3.6.1.2.1.11 included
!
```

### Step 2: Create ACL for SNMP Source Restriction

```ios
ip access-list standard ACL_SNMP_IN
 permit 10.0.1.50
 deny any
!
```

### Step 3: Create SNMPv3 Group with Read-Only View

```ios
snmp-server group nms-ro v3 auth read RO-View access ACL_SNMP_IN
!
```

### Step 4: Create SNMPv3 User

```ios
snmp-server user nms_monitor nms-ro v3 auth sha MyAuthPass123 priv aes 128 MyPrivPass456
!
```

### Step 5: Configure SNMP Source Interface

```ios
snmp-server source-interface all 10.0.1.10
!
```

### Complete Configuration

```ios
ip access-list standard ACL_SNMP_IN
 permit 10.0.1.50
 deny any
!
snmp-server view RO-View 1.3.6.1.2.1.1 included
snmp-server view RO-View 1.3.6.1.2.1.2 included
snmp-server view RO-View 1.3.6.1.2.1.4 included
snmp-server view RO-View 1.3.6.1.2.1.6 included
snmp-server view RO-View 1.3.6.1.2.1.7 included
snmp-server view RO-View 1.3.6.1.2.1.11 included
!
snmp-server group nms-ro v3 auth read RO-View access ACL_SNMP_IN
snmp-server user nms_monitor nms-ro v3 auth sha MyAuthPass123 priv aes 128 MyPrivPass456
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

Only approved NMS hosts can query SNMP:

```ios
ip access-list standard ACL_SNMP_IN
 permit 10.0.1.50
 permit 10.0.1.51
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
