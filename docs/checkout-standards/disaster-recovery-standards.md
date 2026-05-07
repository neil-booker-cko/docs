# Disaster Recovery Standards

Backup procedures, recovery objectives, and testing schedules for network equipment.

---

## Recovery Objectives

### RTO & RPO by Device Type

| Device Type | RTO (Recovery Time) | RPO (Recovery Point) | Rationale |
| --- | --- | --- | --- |
| Core router | 30 minutes | 15 minutes | Critical path; HA failover covers RTO |
| Firewall | 30 minutes | 15 minutes | HA pair; automated failover |
| Access switch | 2 hours | 4 hours | Non-critical; config is static |
| Wireless AP | 4 hours | 8 hours | Client can roam; can be replaced |
| Meraki cloud | N/A | Real-time (cloud-backed) | Cloud-managed; automatic backup |

**Definition:**

- **RTO (Recovery Time Objective):** Maximum acceptable downtime before recovery
- **RPO (Recovery Point Objective):** Maximum acceptable data loss (time between backups)

---

## Configuration Backup Standards

### Backup Frequency

| Device | Frequency | Trigger | Storage |
| --- | --- | --- | --- |
| Cisco core routers | Daily (02:00 UTC) + after any change | Automated script | Vault + Git |
| Cisco switches | Weekly (Sunday 02:00 UTC) + after any change | Automated script | Vault + Git |
| FortiGate firewalls | Daily (02:00 UTC) + after any change | Automated script + manual | Vault + Git |
| Meraki cloud devices | Real-time | Cloud-automatic | Meraki dashboard (30-day default) |

### Backup Storage Locations

**Primary:** Encrypted vault (HashiCorp Vault) at 10.0.1.200

**Secondary:** Git repository (version control) at [GitHub checkout/network-configs](https://github.com/checkout/network-configs)

**Tertiary:** Cold storage (AWS S3 Glacier) for annual backups

### Cisco IOS-XE Backup Process

```bash
#!/bin/bash
# Daily backup script for Cisco devices

DEVICES=("10.0.0.1" "10.0.0.2" "10.0.0.3")
BACKUP_DIR="/mnt/backups/cisco"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

for device in "${DEVICES[@]}"; do
    hostname=$(getent hosts $device | awk '{print $2}')

    # Backup running config via SFTP
    expect <<EOF
    spawn sftp admin@$device
    expect "password:"
    send "MyPassword123\n"
    expect "sftp>"
    send "get running-config $BACKUP_DIR/$hostname-$TIMESTAMP.txt\n"
    expect "sftp>"
    send "quit\n"
EOF

    # Encrypt and upload to vault
    gpg --encrypt $BACKUP_DIR/$hostname-$TIMESTAMP.txt
    vault kv put secret/network/cisco/$hostname config=@$BACKUP_DIR/$hostname-$TIMESTAMP.txt.gpg

    # Commit to Git
    cd /mnt/git-configs
    cp $BACKUP_DIR/$hostname-$TIMESTAMP.txt cisco/$hostname/config-$TIMESTAMP.txt
    git add cisco/$hostname/config-$TIMESTAMP.txt
    git commit -m "Backup: $hostname - $TIMESTAMP"
    git push origin main
done
```

### FortiGate Backup Process

```fortios
! Manual backup command
execute backup config ftp network-backup-210526 10.0.1.200 admin password

! Automated (via script)
config system scheduled-script
    edit "daily-backup"
        set interval 1440  # Every 24 hours
        set start-time 02:00
        set repeat-days every-day
        set script "
            execute backup config ftp fortigate-daily 10.0.1.200 admin password
        "
    next
end
```

### Meraki Cloud Backup

Meraki does **not** require manual backup (cloud-managed).

**Automatic features:**

- Configuration versioning (20+ versions retained)
- Organization settings synced in real-time
- Snapshot available per device (Dashboard → Device Detail → Backup/Restore)

**Manual export (recommended quarterly):**

```text
Dashboard → Organization → Settings → Backup & Restore
- Export organization configuration (JSON)
- Export per-network configuration (JSON)
```

---

## Backup Retention

### Retention Schedule

| Backup Type | Retention Period | Frequency | Storage |
| --- | --- | --- | --- |
| Daily backup (encrypted) | 14 days | Daily | Vault + Git |
| Weekly snapshot | 12 weeks (3 months) | Weekly (Sunday) | Vault + S3 |
| Monthly backup | 12 months | Monthly | Cold storage (Glacier) |
| Annual backup | 7 years | Yearly | Offline (archive) |

### Backup Size Planning

**Per device estimates:**

| Device Type | Config Size | Backup Size (compressed) | Annual Storage |
| --- | --- | --- | --- |
| Cisco router | 2-5 MB | 100-200 KB | ~24 MB/year |
| Cisco switch | 1-2 MB | 50-100 KB | ~12 MB/year |
| FortiGate firewall | 10-50 MB | 1-5 MB | ~60 MB/year |
| Total (all devices) | N/A | ~10-20 MB/day | ~400 MB/year |

**Total storage allocation:** 500 GB (sufficient for 100+ years at current scale)

---

## Recovery Procedures

### Cisco IOS-XE Recovery

#### Scenario: Device lost running config (RAM corruption)

Recovery steps:

1. Access device via console or SSH
2. Reload to startup config (which was synchronized daily)

```ios
reload

! Device reboots with startup-config (previously backed up daily)
```

3. If startup config lost, restore from backup

```ios
configure terminal
copy ftp://admin@10.0.1.200/ELD7-CSW-01-20260515.txt running-config
! Or: copy scp://admin@10.0.1.200/ELD7-CSW-01-20260515.txt running-config
write memory
```

4. Verify config loaded correctly

```ios
show running-config | include router bgp
show ip bgp summary
show ip route
```

### FortiGate Recovery

#### Scenario: Device lost configuration

Recovery steps:

1. Access via console (if available) or SSH
2. Check for available local backups

```fortios
execute backup list
```

3. Restore from backup

```fortios
execute restore config ftp fortigate-backup-20260515 10.0.1.200 admin password
! Device reboots with restored config
```

4. Verify config and HA state

```fortios
get system status
get system ha status
show firewall policy
```

### Meraki Recovery

#### Scenario: Need to restore network configuration

Recovery steps:

1. Dashboard → Network → Devices → Device Detail
2. Click **Backup & Restore**
3. Select previous configuration version from dropdown
4. Click **Restore**
5. Device automatically syncs with Meraki cloud

---

## Physical Recovery (Disaster)

### Site Recovery (Complete Site Failure)

#### Example: Dublin datacenter destroyed by fire

Recovery objectives:

- RTO: 4 hours (activate Ashburn datacenter as primary)
- RPO: 15 minutes (config backup from 02:00 UTC today)

**Recovery steps:**

1. **Activate standby site** (Ashburn/EDC4)
   - Spin up replacement router from template
   - Restore config from backup
   - Point DNS to Ashburn IP

2. **Restore configuration**

   ```ios
   copy ftp://admin@10.0.1.50/ELD7-CSW-01-LATEST.txt running-config
   write memory
   reload
   ```

3. **Verify critical paths**
   - BGP neighbors establish from AWS/Azure/GCP
   - VPN tunnels come up
   - Dataplane validation (ping tests)

4. **Manual recovery (if needed)**
   - Order replacement hardware
   - Rebuild from config backup (estimated 2 hours)

### Individual Device Recovery

#### Scenario: Core router hardware failed (disk/memory)

Recovery:

1. **HA failover triggered automatically** (within 30 seconds)
   - Standby router becomes active
   - No data loss (session sync enabled)

2. **Order replacement hardware** (lead time: 3-7 days)

3. **Once replaced, restore config**
   ```ios
   copy ftp://admin@10.0.1.50/ELD7-CSW-01-LATEST.txt startup-config
   reload
   ```

4. **Join HA pair** (config sync automatic)

---

## Recovery Testing Schedule

### Quarterly DR Test

**Frequency:** Every 3 months (Q1, Q2, Q3, Q4)

**Duration:** 2 hours (after-hours)

**Scope:** Single device recovery (rotate devices)

**Test procedure:**

1. Announce maintenance window (send notifications)
2. Retrieve backup file for target device
3. Simulate config loss (remove config from device)
4. Restore from backup
5. Validate device operational
6. Test critical traffic paths (ping, traceroute)
7. Document results

**Success criteria:**

- Config restored correctly
- All interfaces UP
- BGP neighbors established
- Routing table populated
- No errors in syslog

### Annual Full DR Test

**Frequency:** Once per year (Q1, typically February)

**Duration:** 4-8 hours (all-hands, planned downtime)

**Scope:** Entire network recovery simulation

**Test procedure:**

1. Inform all stakeholders (major maintenance)
2. Backup all device configs (pre-test snapshot)
3. Simulate site-wide failure:
   - Take core router offline
   - Take primary firewall offline
   - Disable all uplinks
4. Attempt recovery:
   - Restore each device from backup
   - Verify HA failover
   - Test cloud connectivity
5. Restore to normal operation
6. Validate no data loss, no routes lost
7. Document recovery time and issues

**Success criteria:**

- All devices recovered within RTO
- All services operational
- BGP and routing converged
- No permanent data loss

---

## Backup Verification

### Monthly Backup Integrity Check

**Frequency:** Monthly (1st Monday of month)

**Steps:**

1. Pick random device from backup list
2. Attempt to restore to lab device (if available)
3. Boot device with restored config
4. Verify all interfaces present
5. Verify all commands in place
6. Document any restoration issues

### Automated Backup Monitoring

**Alert triggers:**

- Backup script failed to run
- Backup file size anomaly (< 10 KB or > 100 MB)
- Backup upload to Vault failed
- Backup not seen in 24 hours

**Monitoring commands:**

```bash
# Check last 5 backups
vault kv list secret/network/cisco

# Monitor backup script logs
tail -f /var/log/backup-network.log

# Verify Git commits
git log --oneline | head -20
```

---

## Disaster Recovery Contacts

### Escalation List

| Role | Contact | Phone | Email |
| --- | --- | --- | --- |
| Network Lead | John Smith | +44-20-XXXX | jsmith (at) checkout.com |
| Senior Engineer | Alice White | +44-20-YYYY | awhite (at) checkout.com |
| Infrastructure Manager | Bob Johnson | +44-20-ZZZZ | bjohnson (at) checkout.com |
| Incident Commander | Sarah Lee | +44-20-WWWW | slee (at) checkout.com |

### External Vendor Contacts

| Vendor | Issue Type | Contact | Response SLA |
| --- | --- | --- | --- |
| Cisco TAC | Hardware failure | 1-800-553-6387 | 4 hours (premier) |
| Fortinet FortiCare | Firmware/bug issue | 1-408-943-4949 | 1 hour (24x7) |
| Meraki Support | Cloud connectivity | 1-888-MERAKI-1 | 1 hour (enterprise) |
| AWS Support | Direct Connect failure | AWS Console | 1 hour (business) |

---

## Troubleshooting Recovery Failures

### Backup File Corruption

**Symptom:** Restore fails; config incomplete

**Solution:**

1. Check previous backup version
2. Compare file size to baseline
3. Attempt restore from earlier backup
4. If all corrupted, rebuild from change log

### Restoration Timeout

**Symptom:** SFTP/FTP copy hangs during restore

**Solution:**

```ios
! Increase timeout
config term
event manager applet INCREASE-TIMEOUT
  event timer countdown time 300
exit
! Re-attempt copy with explicit timeout
copy /allow-overwrite ftp://admin@10.0.1.50/config.txt running-config timeout 300
```

### Config Mismatch After Restore

**Symptom:** Some commands missing after restore (partial config)

**Solution:**

1. Compare restored config to backup file
2. Identify missing sections
3. Manually apply missing commands
4. Update backup process (potential script issue)

---

## Related Standards

- [Change Management Standards](change-management-standards.md) — Backup before/after changes
- [Equipment Configuration](equipment-config.md) — Base configs used for recovery baseline
- [Syslog & Monitoring](syslog-monitoring-standards.md) — Log critical recovery events
