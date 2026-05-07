# Syslog & Monitoring Standards

Centralized logging, SNMP monitoring, and observability standards for all network devices.

---

## Syslog Infrastructure

### Syslog Server Configuration

**Requirement:** Centralized syslog collection (minimum 2 servers for redundancy).

| Component | Standard | Notes |
| --- | --- | --- |
| Primary Syslog | 10.0.1.100:514 | Local datacenter (Dublin/ELD7) |
| Secondary Syslog | 10.0.1.101:514 | Backup datacenter (Ashburn/EDC4) |
| Protocol | UDP (RFC 3164) | Fast; no TCP overhead |
| Facility | LOCAL0-LOCAL7 | Per-device facility for filtering |
| Retention | 30 days (rolling) | Purge logs older than 30 days |
| Storage | 500 GB per syslog server | ~100 devices × 5MB/day = 15GB/month |

### Syslog Message Format

**Format:** `<PRI>TIMESTAMP HOSTNAME TAG[PID]: MESSAGE`

**Example:**

```text
<134>May  7 12:34:56 ELD7-CSW-01 %LINEPROTO-5-UPDOWN: Line protocol on Interface GigabitEthernet0/1, changed state to up
```

---

## Syslog Severity Levels

All devices must log at **INFO level (6)** or above. Per-facility severity settings:

| Severity | Level | Usage | Example |
| --- | --- | --- | --- |
| Emergency | 0 | System unusable | System reboot imminent |
| Alert | 1 | Immediate action | Unauthorized access attempt |
| Critical | 2 | Critical condition | Device offline, HA failover |
| Error | 3 | Error condition | Configuration error, link down |
| Warning | 4 | Warning | High CPU, memory threshold |
| Notice | 5 | Normal but significant | Configuration changed, user login |
| Informational | 6 | Informational | Interface up, route added |
| Debug | 7 | Debug info | Packet detail (not in production) |

**Standard:** Log all ERROR (3), WARNING (4), NOTICE (5), and INFORMATIONAL (6) messages.
Do **not** send DEBUG (7) to syslog in production.

---

## Device Syslog Configuration

### Cisco IOS-XE Syslog

```ios
logging facility local0
logging host 10.0.1.100 transport udp port 514
logging host 10.0.1.101 transport udp port 514
logging trap informational
logging source-interface GigabitEthernet0/0
!
```

### FortiGate Syslog

```fortios
config log syslogd setting
    set status enable
    set server "10.0.1.100"
    set port 514
    set certificate "Fortinet_Factory"
    set facility local0
    set source-ip 10.0.2.1
next
end
```

### Meraki Cloud Logging

Meraki does **not** support external syslog. Instead:

- **Dashboard native:** 30-day retention (Meraki cloud)
- **Webhooks:** Send events to external systems (PagerDuty, Slack)

---

## SNMP Monitoring Standards

### SNMP Version & Security

**Requirement:** SNMP v3 (no SNMPv1/v2c in production).

| Parameter | Standard | Notes |
| --- | --- | --- |
| Version | SNMPv3 | Authentication & encryption required |
| Authentication | HMAC-SHA | Strong hash algorithm |
| Encryption | AES-128 | Minimum 128-bit encryption |
| Read Community | Disabled (v1/v2c) | v3 only; no plain-text community strings |
| Trap Destination | 10.0.1.50:162 | NMS (Network Management System) |

### SNMP v3 User Configuration

**Cisco IOS-XE:**

```ios
snmp-server group netmon v3 auth
snmp-server user nms_monitor netmon v3 auth sha MyAuthPass123 priv aes 128 MyPrivPass456
snmp-server host 10.0.1.50 traps version 3 auth nms_monitor
snmp-server source-interface all 10.0.1.10
!
```

**FortiGate:**

```fortios
config system snmp user
    edit "nms_monitor"
        set security-level auth-priv
        set auth-proto sha
        set auth-pwd MyAuthPass123
        set priv-proto aes
        set priv-pwd MyPrivPass456
    next
end
config system snmp community
    edit 1
        set name "netmon"
        set status enable
    next
end
```

---

## Syslog Filtering & Routing

### Device-Specific Logging

Configure facility codes per device type for filtering:

| Facility | Device Type | Devices |
| --- | --- | --- |
| LOCAL0 | Core routers | ELD7-CSW-01, ELD7-CSW-02 |
| LOCAL1 | Access switches | LON1-ASW04-01A, LON1-ASW04-01B |
| LOCAL2 | Firewalls | LON1-PFW-01A, LON1-PFW-01B |
| LOCAL3 | VPN appliances | ELD7-CON-01, AWS TGW |
| LOCAL4 | Wireless | Meraki MRs (if capable) |
| LOCAL5 | Servers | NMS, syslog servers |

### Syslog Server Filtering Rules

**Example rsyslog configuration:**

```text
# Route facility LOCAL0 (routers) to file
:facility local0 /var/log/routers.log

# Route facility LOCAL2 (firewalls) to file
:facility local2 /var/log/firewalls.log

# Route errors and above (severity 0-3) to alerts
:severity err /var/log/alerts.log

# Route HA state changes (NOTICE) to ha.log
:msg contains "state change" /var/log/ha.log
```

---

## Log Retention & Archival

### Retention Policy

| Log Type | Retention | Archive | Backup |
| --- | --- | --- | --- |
| Syslog (all devices) | 30 days (rolling) | 90 days (compressed) | 1 year (cold storage) |
| Device config backups | 7 versions | Every weekly backup | Monthly snapshot |
| Audit logs (AAA) | 90 days | 1 year | 2 years |

### Archival Process

1. **Weekly:** Compress logs older than 7 days → archive storage
2. **Monthly:** Move monthly archives to long-term cold storage
3. **Quarterly:** Verify integrity of archived logs; test restore process

---

## SNMP v3 Walk Testing

### Verify SNMP Community

**From NMS (10.0.1.50):**

```bash
# Test SNMPv3 connectivity (from NMS)
snmpwalk -v3 -u nms_monitor -l authPriv -a SHA -A MyAuthPass123 -x AES -X MyPrivPass456 10.0.1.10 .1.3.6.1.2.1.1

# Expected output (sysDescr):
SNMPv3-User: nms_monitor
Engine ID: 8000070903...
System Description: Cisco IOS XE 17.x...
```

---

## Alert Thresholds & Actions

### Critical Thresholds (Immediate PagerDuty Alert)

| Metric | Threshold | Action |
| --- | --- | --- |
| Interface down | Any downtime | Page oncall |
| HA failover | Active-to-standby switch | Page oncall |
| BGP neighbor down | Unexpected | Page oncall |
| Disk usage | >90% | Page oncall |
| Memory | >85% | Page oncall |

### Warning Thresholds (Email Alert Only)

| Metric | Threshold | Action |
| --- | --- | --- |
| CPU | >75% | Email netadmin (at) checkout.com |
| Temperature | >80°C | Email netadmin (at) checkout.com |
| Power supply | >50% power usage | Email netadmin (at) checkout.com |
| BGP route count | Unusual spike | Email netadmin (at) checkout.com |

---

## Monitoring Integration Points

### PagerDuty Integration

**Endpoint:** `https://events.pagerduty.com/v2/enqueue`

**Syslog trigger:** Severity ERROR or above from critical devices

```fortios
# FortiGate example: send syslog to PagerDuty via webhook
config log eventfilter
    set system enable
    set event-log enable
next
end
```

---

## Troubleshooting

### Syslog Not Arriving

**Checklist:**

1. **Connectivity:** Ping syslog server from device

   ```ios
   ping 10.0.1.100
   ```

2. **Source IP:** Verify syslog source interface is reachable

   ```ios
   show logging
   show ip interface brief | include 10.0.1.10
   ```

3. **Firewall rules:** Confirm UDP 514 not blocked

   ```fortios
   diag firewall ipdb list
   ```

4. **Device config:** Verify logging commands were applied

   ```ios
   show run | include logging
   ```

### SNMP Not Responding

**Checklist:**

1. **SNMP enabled:** Verify service is running

   ```ios
   show snmp
   ```

2. **User exists:** Check SNMPv3 user configuration

   ```ios
   show snmp user
   ```

3. **Access list:** Verify NMS IP allowed

   ```ios
   show access-list | include snmp
   ```

4. **Test walk:** Walk the device MIB from NMS

   ```bash
   snmpwalk -v3 -u nms_monitor -l authPriv ... 10.0.1.10
   ```

---

## Related Standards

- [Equipment Configuration](equipment-config.md) — Base SNMP/syslog setup
- [Security Hardening](security-hardening.md) — Access control for monitoring systems
- [Interface Configuration Standards](interface-standards.md) — Management interface source address
