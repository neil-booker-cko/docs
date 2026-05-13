# Change Management & Validation Standards

Procedures for deploying, validating, and rolling back network configuration changes.

---

## Change Management Workflow

### Change Phases

All changes follow this workflow:

1. **Planning Phase** — Design, testing, risk assessment
2. **Implementation Phase** — Execute change in maintenance window
3. **Validation Phase** — Verify change worked as expected
4. **Rollback Phase** — Emergency procedure if validation fails

---

## Pre-Change Checklist

### Before Implementing Any Change

**Must complete before change window:**

- [ ] **Configuration backup** — Full device backup taken today
- [ ] **Test in lab** — Change tested on identical lab device (if available)
- [ ] **Peer review** — Another engineer reviewed change (critical changes)
- [ ] **Change ticket** — Created with description, expected impact, rollback plan
- [ ] **Maintenance window** — Scheduled during low-traffic time (off-hours if critical)
- [ ] **Notifications** — Informed stakeholders of maintenance window
- [ ] **Rollback plan** — Documented exact commands to revert change
- [ ] **Verification commands** — Listed commands to validate success

### Change Ticket Template

**Ticket title:** Device name, change type, change date

**Description:**

```text
Device: ELD7-CSW-01
Change: Upgrade IOS-XE from 17.3.1 to 17.6.1
Date: 2026-05-15 22:00 UTC
Duration: 30 minutes (estimated)

Rationale: Security advisories 17.3.1 EOL; 17.6.1 addresses CVE-2026-XXXXX

Scope: Core router only; no data plane impact (HSRP standby, no traffic shift)

Pre-Change:
- Backup config (done 2026-05-15 10:00)
- Lab test completed (upgrade successful; interfaces came up)
- Peer review: approved by John Smith

Verification:
- Device boots successfully
- All interfaces UP
- BGP neighbors established
- Routes learned from AWS TGW
- No CPU/memory alarms

Rollback:
If upgrade fails: reload from previous IOS-XE 17.3.1 image (pre-loaded)
Command: request platform software system rollback clean
```

---

## Implementation Checklist

### During Maintenance Window

**Standard execution order:**

1. **Establish out-of-band access** — Connect via console or OOB management network
2. **Enable logging to syslog** — Verify syslog server reachable
3. **Document baseline state** — Collect pre-change snapshots
4. **Implement change** — Apply configuration/firmware update
5. **Validate immediately** — Check device state, interfaces, services
6. **Monitor for 5 minutes** — Watch CPU, memory, error rates

### Commands Before Change

**Cisco IOS-XE:**

```ios
! Create an archive snapshot for quick comparison
copy running-config startup-config

! Document current routes
show ip route
show ip bgp summary

! Document interface state
show interface brief

! Enable syslog (if not already)
terminal monitor
logging on
```

**FortiGate:**

```fortios
! Backup active configuration
execute backup config ftp myconfig-before-change 10.0.1.5 admin password

! Show current status
get system status

! Check HA state
get system ha status
```

---

## Change Types & Approval

### Configuration Changes (Minor)

**Definition:** Interface config, routing redistribution, firewall rule (low risk)

**Approval:** Single engineer review

**Validation:** Pre-defined commands executed post-change

**Rollback:** Configuration command sequence (< 5 minutes)

### Firmware/Software Updates (Major)

**Definition:** IOS-XE upgrade, FortiOS patch, system reboot required

**Approval:** Two engineers review; change control board decision

**Validation:** Device boots, all services operational, interfaces come up

**Rollback:** BIOS/boot loader fallback or reload from golden image

### Maintenance Window Changes

**Configuration:** Off-hours only (22:00-06:00 UTC)

**Firmware:** Off-hours only; HA devices staggered (24 hours apart)

**Critical systems:** Single maintenance window; no back-to-back changes (24hr minimum between)

---

## Validation Commands

### Cisco IOS-XE Validation

**After any configuration change:**

```ios
! Verify running vs startup config matches (should be identical)
show running-config | include <changed-item>
show startup-config | include <changed-item>

! Check for errors or warnings
show diagnostic system status

! Monitor high-priority systems
show ip route
show ip bgp summary
show interface brief
show processes cpu sorted
show memory statistics
```

**Example validation script (verify BGP change):**

```ios
! Change: Added new route map to AWS peer
show running-config router bgp
show ip bgp summary
show ip bgp neighbors 192.0.2.1 routes
show ip bgp neighbors 192.0.2.1 advertised-routes
! Verify AWS TGW received new routes
ping 10.10.1.1  (AWS subnet; should be reachable)
```

### FortiGate Validation

**After any configuration change:**

```fortios
! Verify config was applied
get system status

! Check HA sync status
diagnose high-availability status

! Verify firewall policies
show firewall policy

! Check system resources
diagnose system top

! Verify interfaces UP
diagnose interface list

! Test critical path (ping AWS)
execute ping 10.10.1.1
```

### Meraki Dashboard Validation

**After any configuration change:**

1. **Dashboard → Devices** — Verify all devices online
2. **Dashboard → Network Health** — Check uplink status
3. **Dashboard → Connectivity** — Verify latency/loss normal
4. **Dashboard → Alerts** — Check for new alerts in past 5 min
5. **Dashboard → Wireless** — Verify AP count and connected clients

---

## Verification Time Windows

### Continuous Monitoring (During & Immediately After)

**Duration:** 0-5 minutes post-change

**Actions:**

- Watch syslog for errors
- Monitor interface state (should be stable)
- Check CPU/memory for spikes
- Verify expected routes/neighbors established

### Extended Monitoring (5 minutes - 1 hour)

**Duration:** 5 min - 1 hour post-change

**Actions:**

- Verify no protocol flaps (BGP, OSPF)
- Check throughput/latency from test client
- Monitor for memory creep or CPU drift
- Verify backup/replication working (if applicable)

### Long-term Monitoring (1 hour - 24 hours)

**Duration:** 1 hour - 24 hours post-change

**Actions:**

- Monitor syslog for warnings/errors
- Check interface error counters (should be stable)
- Verify NAT/DPI functionality (if applicable)
- Monitor failover behavior in HA pairs

---

## Rollback Procedures

### Configuration Rollback (Fast)

**Time:** < 2 minutes

#### Example: Revert routing change

```ios
! Method 1: Copy previous running config from startup
no router bgp 65000
copy startup-config running-config

! Method 2: Manual removal of added commands
configure terminal
router bgp 65000
  no route-map RM_AWS_IN in
exit

! Verify reverted
show ip bgp summary
```

### Firmware Rollback (Slower)

**Time:** 5-10 minutes (device reboot required)

#### Example: Revert IOS-XE upgrade

```ios
! Boot from previous IOS image
configure terminal
boot system flash bootflash:cat9k_iosxe.17.03.01.SPA.bin
exit

! Save and reload
write memory
reload

! Device reboots and loads previous IOS version
```

### FortiGate Configuration Rollback

**Time:** < 2 minutes

```fortios
! Restore from backup
execute restore config ftp myconfig-before-change 10.0.1.5 admin password
! Device reboots with previous config
```

---

## Change Communication

### During Change Window

**Notifications to:**

- On-call engineer (PagerDuty)
- Infrastructure team (email/Slack)
- Application owners if affecting services (email)

**Message template:**

```text
MAINTENANCE WINDOW - NETWORK CHANGE

Device: ELD7-CSW-01
Start: 2026-05-15 22:00 UTC
Duration: 30 min
Impact: No expected impact (primary device, HA in place)

Change: IOS-XE upgrade 17.3.1 → 17.6.1

Status: [ONGOING] / [COMPLETED] / [ROLLED BACK]
```

### Post-Change Communication

**Message template:**

```text
MAINTENANCE WINDOW - COMPLETED

Device: ELD7-CSW-01
Status: SUCCESS

Change Result:
- Device booted successfully
- All interfaces UP
- BGP neighbors established
- Routes learned from AWS TGW
- No errors or alarms

Duration: 15 minutes (under estimated 30 min)
Impact: None observed

Rollback: Not required
```

---

## Documentation & Auditing

### Change Log Entry

**File:** `/var/log/network-changes.log` (or equivalent audit system)

**Format:**

```text
2026-05-15 22:15 UTC | ELD7-CSW-01 | IOS upgrade 17.3.1→17.6.1 | SUCCESS | jsmith | CR-2026-5432
2026-05-14 10:30 UTC | LON1-PFW-01A | BGP route-map change | SUCCESS | awhite | CR-2026-5431
```

### Configuration Backup Schedule

**Frequency:** Before every change; daily backup of all devices

**Storage:** Version control (Git) + Encrypted backup (Vault)

**Retention:** 90 days rolling

```bash
# Daily backup example (cron job)
0 2 * * * /usr/local/bin/backup-network-configs.sh
```

---

## Change Impact Assessment Matrix

| Change Type | Data Plane Impact | Control Plane Impact | Management Impact | Outage Risk |
| --- | --- | --- | --- | --- |
| Interface description update | None | None | None | None |
| Static route addition | Yes (if primary) | Yes | None | Low (HA absorbs) |
| BGP timers tuning | Yes | Yes | None | Low |
| Firewall rule addition | Yes | None | None | Low (traffic-dependent) |
| IOS-XE upgrade (HA) | Low (failover) | Low (transition) | Possible (SSH) | Low (HA) |
| Firmware upgrade (single device) | High | High | High | High |

---

## Approval Matrix

| Change Type | Risk | Approval | Window |
| --- | --- | --- | --- |
| Config change (non-critical) | Low | Single review | Anytime (notify team) |
| Config change (critical device) | Medium | Double review | Off-hours only |
| Firmware upgrade | High | Double review + CCB | Off-hours; HA staggered |
| Security hardening | Medium | Double review | Off-hours or immediate (emergency) |

---

## Related Standards

- [Equipment Configuration](equipment-config.md) — Baseline config; use for baseline validation
- [Security Hardening](security-hardening.md) — Security changes require double review
- [Syslog & Monitoring](syslog-monitoring-standards.md) — Monitor syslog during/after changes
