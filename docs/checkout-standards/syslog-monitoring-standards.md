# Syslog & Monitoring Standards

Centralized logging, SNMP monitoring, and observability standards for all network devices.

---

## Syslog Infrastructure

### Syslog Server Configuration

**Requirement:** Centralized syslog collection on utility servers (3 servers for redundancy).

**Note:** These utility servers also function as management servers for SNMP monitoring and NMS
queries.

| Component | Standard | Notes |
| --- | --- | --- |
| Utility Server 1 (Primary) | 10.13.1.147:601 | Syslog + SNMP management |
| Utility Server 2 (Secondary) | 10.13.2.116:601 | Syslog + SNMP management |
| Utility Server 3 (Tertiary) | 10.13.2.147:601 | Syslog + SNMP management |
| Protocol | TCP/601 (RFC 5426 Reliable Syslog) | Preferred; guarantees message delivery |
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

### Cisco IOS-XE Syslog (Multiple Servers)

**Note:** Do NOT modify facility codes; use device defaults.

```ios
logging host 10.13.1.147 transport tcp port 601
logging host 10.13.2.116 transport tcp port 601
logging host 10.13.2.147 transport tcp port 601
logging trap informational
logging source-interface GigabitEthernet0/0
!
```

### FortiGate Syslog (Multiple Servers)

Configure three syslog servers for operational logging (syslogd–syslogd3) and an optional fourth
(syslogd4) in CEF format for InfoSec/SIEM ingestion:

```fortios
config log syslogd setting
    set status enable
    set server "<SYSLOG_SERVER_1>"
    set mode reliable
    set port 601
    set source-ip "<FORTIOS_IP>"
end

config log syslogd2 setting
    set status enable
    set server "<SYSLOG_SERVER_2>"
    set mode reliable
    set port 601
    set source-ip "<FORTIOS_IP>"
end

config log syslogd3 setting
    set status enable
    set server "<SYSLOG_SERVER_3>"
    set mode reliable
    set port 601
    set source-ip "<FORTIOS_IP>"
end

config log syslogd4 setting
    set status enable
    set server "<INFOSEC_SIEM_SERVER>"
    set mode reliable
    set port 601
    set source-ip "<FORTIOS_IP>"
    set format cef
end
```

**syslogd4 (CEF):** Common Event Format for InfoSec SIEM ingestion. Only configure when a
dedicated InfoSec log destination is required.

### Perle Console Server Syslog

```text
add host <SYSLOG_HOSTNAME> <SYSLOG_IP>

set syslog level informational
set syslog primary-host <SYSLOG_HOSTNAME>
set syslog secondary-host <SYSLOG_HOSTNAME>
```

### Meraki Cloud Logging

Meraki does **not** support external syslog. Instead:

- **Dashboard native:** 30-day retention (Meraki cloud)
- **Webhooks:** Send events to external systems (PagerDuty, Slack)

---

## SNMP Monitoring Standards

### SNMP Management Servers

**Requirement:** SNMP NMS queries to utility servers (same 3 servers as syslog).

| Parameter | Standard | Notes |
| --- | --- | --- |
| Primary NMS Server | 10.13.1.147 | Utility server (also primary syslog) |
| Secondary NMS Server | 10.13.2.116 | Utility server (also secondary syslog) |
| Tertiary NMS Server | 10.13.2.147 | Utility server (also tertiary syslog) |
| SNMP Port | 161 (UDP) | Standard SNMP query port |
| Trap Destination | 10.13.1.147:162 | Traps disabled (pull-based monitoring only) |

### SNMP Version & Security

**Requirement:** SNMP v3 (no SNMPv1/v2c in production).

| Parameter | Standard | Notes |
| --- | --- | --- |
| Version | SNMPv3 | Authentication & encryption required |
| Authentication | HMAC-SHA | Strong hash algorithm |
| Encryption | AES-128 | Minimum 128-bit encryption |
| Read Community | Disabled (v1/v2c) | v3 only; no plain-text community strings |
| Trap Destination | Disabled | Pull-based monitoring via NMS servers |

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

## Syslog Server Configuration (rsyslog)

### Facility Code Standard

**Standard:** Do NOT modify or assign device-specific facility codes. All devices use default
facility (LOCAL0 or device default). Filtering and organization is based on source IP address,
not facility codes.

### rsyslog File Logging

Logs are written to per-platform directories, each file named by source IP. Config files live
in `/etc/rsyslog.d/`. Key files:

| File | Platform | Directory |
| --- | --- | --- |
| `10-cisco.conf` | Cisco IOS-XE | `/var/log/cisco-iosxe/` |
| `20-fortios.conf` | FortiOS | `/var/log/fortios/` |
| `22-perle.conf` | Perle | `/var/log/perle/` |

**Example — FortiOS (`20-fortios.conf`):**

```text
if $fromhost-ip=='<FORTIOS_IP>' then /var/log/fortios/<DEVICE_NAME>.log
& stop
```

**Example — Cisco IOS-XE (`10-cisco.conf`):**

```text
if $fromhost-ip=='<CISCO_IP>' then /var/log/cisco-iosxe/<DEVICE_NAME>.log
& stop
```

**rsyslog.conf** — enable TCP and UDP reception:

```text
module(load="imudp")
input(type="imudp" port="514")

module(load="imtcp")
input(type="imtcp" port="514")
```

After editing: `systemctl restart rsyslog && systemctl enable rsyslog`

**File permissions:** `644 syslog:adm` — 644 (not 600) so the Datadog agent can read log files.

### Log File Organization

```text
/var/log/
  ├── cisco-iosxe/          Cisco IOS-XE devices (per-device file by IP or hostname)
  ├── fortios/              FortiOS firewalls
  └── perle/                Perle console servers
```

### Log Rotation

Logrotate config files in `/etc/logrotate.d/`. Retain 7 days locally — Datadog provides
longer-term storage.

```text
/var/log/fortios/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 syslog adm
}
```

Apply the same pattern for `cisco-iosxe` and `perle` directories.

---

## Datadog Log Monitoring & Upload

### Datadog Agent Configuration

Datadog agent monitors rsyslog log files and uploads to Datadog cloud for centralized analysis,
alerting, and long-term retention beyond local syslog retention (30 days).

Config file: `/etc/datadog-agent/conf.d/custom_log_collection.d/conf.yaml`

```yaml
logs:
  - type: file
    path: /var/log/fortios/*.log
    source: fortigate
    tags:
      - "env:datacenter:<SITE>"
  - type: file
    path: /var/log/cisco-iosxe/*.log
    source: cisco-iosxe
    tags:
      - "env:datacenter:<SITE>"
  - type: file
    path: /var/log/perle/*.log
    source: perle
    tags:
      - "env:datacenter:<SITE>"
```

Restart after changes: `systemctl restart datadog-agent`

### Datadog Grok Parsing Patterns

Pipelines in Datadog parse incoming log messages by source. The Grok patterns below are used
for the `cisco-iosxe` and `fortigate` sources. Processors also rename variables and normalise
severity levels.

**Cisco IOS-XE:**

```text
ManualRule1 %{date("MMM dd HH:mm:ss"):syslog_timestamp}\s+%{ip:client}\s+%{integer:seqnum}\:(\s+%{ipOrHost:client}:)?\s+%{date("MMM dd YYYY HH:mm:ss.SSS z"):eventtime}:\s+.%{word:facility}-%{integer:severity}-%{word:mnemonic}:\s+%{data:message}
ManualRule2 %{date("MMM  d HH:mm:ss"):syslog_timestamp}\s+%{ip:client}\s+%{integer:seqnum}\:(\s+%{ipOrHost:client}:)?\s+%{date("MMM dd YYYY HH:mm:ss.SSS z"):eventtime}:\s+.%{word:facility}-%{integer:severity}-%{word:mnemonic}:\s+%{data:message}
```

**FortiGate:**

```text
manualRule1 %{date("MMM dd HH:mm:ss"):syslog_timestamp}\s+_gateway\s+%{data::keyvalue("=", " \"():*\[\]")}
manualRule2 %{date("MMM dd HH:mm:ss"):syslog_timestamp}\s+_gateway\s+%{data::keyvalue("=", " \":*\[\]")}
manualRule3 %{date("MMM dd HH:mm:ss"):syslog_timestamp}\s+_gateway\s+%{data::keyvalue("=", "\":*\[\]")}
manualRule4 %{date("MMM  d HH:mm:ss"):syslog_timestamp}\s+_gateway\s+%{data::keyvalue("=", " \"():*\[\]")}
manualRule5 %{date("MMM  d HH:mm:ss"):syslog_timestamp}\s+_gateway\s+%{data::keyvalue("=", " \":*\[\]")}
manualRule6 %{date("MMM  d HH:mm:ss"):syslog_timestamp}\s+_gateway\s+%{data::keyvalue("=", "\":*\[\]")}
```

Multiple rules cover single-digit day padding (`MMM dd` vs `MMM  d`) and FortiOS key=value
quoting variants.

### Datadog Tags

All logs are tagged with metadata for filtering and alerting:

| Tag | Values | Purpose |
| --- | --- | --- |
| `env` | `datacenter`, `enterprise` | Environment classification |
| `site` | `eld7`, `edc4`, `lon1`, `sfo1`, etc. | Site/location identifier |
| `vendor` | `cisco`, `fortinet`, `meraki` | Device vendor |
| `source` | `cisco-iosxe`, `fortios`, `meraki` | Device OS/platform |

**Example Datadog Query:**

```text
source:cisco-iosxe env:datacenter site:eld7 status:error
```

This finds all ERROR-level events from Cisco IOS-XE devices in the ELD7 datacenter.

### Datadog Features

- **Log Storage:** Unlimited retention in Datadog cloud (vs. 30 days local)
- **Search & Analysis:** Full-text search, faceted analysis, custom dashboards
- **Alerting:** Create alerts on log patterns, anomalies, error rates
- **Metrics:** Extract metrics from logs (e.g., interface down events per device)
- **Integration:** Connect to PagerDuty, Slack, email for incident response

### Datadog Dashboard Example

**Monitor network events:**

- Interface down/up events (count per device)
- Configuration changes (logins, auth failures)
- High CPU/memory alerts
- BGP neighbor state changes
- OSPF adjacency changes

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
