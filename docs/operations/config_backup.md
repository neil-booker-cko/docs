# Configuration Backup and Restore

The configuration is the most critical asset on a network device. Hardware can be
replaced; configuration cannot be recovered without a backup. Back up before every
change, and automate regular scheduled backups so that a device can be restored to a
known-good state independent of any individual change process.

---

## Cisco IOS-XE Backup Methods

### Manual Backup

Copy the running configuration to a remote server or to local flash:

```ios
copy running-config tftp:
copy running-config scp:
copy running-config flash:backup-2026-04-07.cfg
```

For TFTP and SCP, the router prompts for the destination address and filename. Use a
consistent naming convention that includes the hostname and date.

### Archive (Automated Scheduled Backup)

The `archive` feature writes timestamped copies of the configuration to local flash on a
configurable interval and on every `copy running-config startup-config`.

```ios
archive
 path flash:backup/$h-$t    ! $h = hostname, $t = timestamp
 maximum 14
 time-period 1440          ! Archive every 24 hours (minutes)
 write-memory
```

`write-memory` in the archive block triggers an additional archive write each time
`copy run start` is executed — useful for ensuring every deliberate change is
captured.

The `maximum` value controls how many archive files are retained on local flash before
older files are overwritten. Plan space accordingly: `maximum 14` retains ~2 weeks of
daily backups.

**Note on storage:** Local archive is fast and reliable, but provides no protection against
hardware failure. Regularly copy archived backups to an off-box location (TFTP, SCP, or git)
to meet compliance and disaster recovery requirements. See
[Off-Box Storage](#off-box-storage) below.

### EEM — Event-Driven Backup on Config Change

For additional event-driven backups on every configuration change:

```ios
event manager applet BACKUP-ON-CHANGE
 event syslog pattern "SYS-5-CONFIG_I"
 action 1.0 cli command "enable"
 action 2.0 cli command "copy running-config flash:backup/emergency-$(time)"
```

The `SYS-5-CONFIG_I` syslog message is generated any time the running configuration
is modified. This applet fires on every configuration change.

!!! note
    The `archive` method (above) is recommended over EEM for regular backups as it
    provides built-in timestamp support and maximum retention management. Use EEM for
    event-driven emergency captures that supplement the regular archive schedule.

### NETCONF / RESTCONF API Export

On platforms running IOS-XE 16.6 or later with RESTCONF enabled, the full device
configuration can be retrieved programmatically:

```text
GET /restconf/data/Cisco-IOS-XE-native:native
```

This returns the full running configuration as structured JSON or XML, suitable for
storage in version control or a network management system. See
[NETCONF / RESTCONF](../application/netconf.md) for setup and authentication details.

---

## Cisco IOS-XE Restore

### Restore from Flash (Local Archive)

List available backups and restore from local archive:

```ios
dir flash:backup/
copy flash:backup/router-20260428.180000 startup-config
reload
```

`copy ... startup-config` replaces the startup configuration. Reload applies the restored
configuration cleanly. For a non-disruptive merge into the running config:

```ios
copy flash:backup/router-20260428.180000 running-config
```

!!! warning
    Merging a backup into the running configuration (`copy ... running-config`) is
    non-disruptive but can leave stale configuration in place — interfaces, ACLs, or
    routing statements that were deleted in the backup file will remain. For a clean
    restore, copy to startup-config and reload.

### Restore from TFTP or SCP

If the local backup is corrupted or unavailable, restore from an off-box copy:

```ios
copy tftp: startup-config
copy scp: startup-config
reload
```

---

## FortiGate Backup Methods

### CLI Backup

```fortios
execute backup config tftp <filename> <server-ip>
```

This produces a full configuration file in FortiOS `.conf` format.

**Encrypted backup** (required to preserve pre-shared keys and local passwords in
recoverable form):

```fortios
execute backup config tftp <filename> <server-ip> <encryption-password>
```

Without the encryption password, sensitive fields such as IKE pre-shared keys are
omitted or masked in the backup file.

#### System > Config > Backup

The GUI offers the same full backup with an optional encryption password. In a
multi-VDOM environment, you can back up a single VDOM or all VDOMs.

### Automation Stitch (Scheduled Backup)

FortiOS automation stitches can trigger a configuration backup on a schedule without
relying on external tools:

```fortios
config system automation-trigger
    edit "daily-backup-trigger"
        set trigger-type scheduled
        set trigger-hour 2
    next
end
config system automation-action
    edit "backup-action"
        set action-type backup-config
        set tftp-server 10.0.0.100
        set filename "fgt-backup-%Y%m%d"
    next
end
config system automation-stitch
    edit "daily-backup"
        set trigger "daily-backup-trigger"
        set action "backup-action"
    next
end
```

The `%Y%m%d` tokens in the filename are expanded at execution time, producing a dated
backup file per run.

---

## FortiGate Restore

### CLI Restore

```fortios
execute restore config tftp <filename> <server-ip>
```

The unit applies the configuration and reboots automatically. There is no interactive
merge — the restore replaces the running configuration entirely.

#### System > Config > Restore

Upload the backup file directly from the browser. The unit reboots after the restore
is applied.

!!! warning
    Restoring a configuration from a different firmware version may partially fail —
    FortiOS does not guarantee backward or forward compatibility of configuration
    syntax across major versions. Always restore to the same firmware version the
    backup was taken on. If a firmware upgrade is required, upgrade first, then
    restore.

---

## What Is Not in a Config Backup

A configuration backup captures the device's configured state — not its operational
state at the time of backup.

| Item | Cisco IOS-XE | FortiGate |
| --- | --- | --- |
| Running configuration | ✓ | ✓ |
| Passwords (type 7 &#124; enable secret) | ✓ (hashed) | ✓ (if encrypted backup) |
| IKE / IPsec pre-shared keys | ✓ | ✓ (if encrypted backup) |
| DHCP leases | ✗ | ✗ |
| MAC address table | ✗ | ✗ |
| BGP / OSPF learned routes | ✗ | ✗ |
| Log data | ✗ | ✗ |
| FortiGuard licenses | ✗ | ✗ |

Operational state — learned routes, ARP/MAC tables, active sessions — is rebuilt
automatically after restore and reload. Log data requires a separate log export
process.

---

## Off-Box Storage

A backup stored only on the device provides no protection against hardware failure.
Backups must be stored off the device on at least one of the following:

- **TFTP or SCP server** — simple and widely supported; suitable for automated
  archive destinations
- **Network management system** — Cisco DNA Center and FortiManager both include
  configuration backup and compliance features with version history
- **Version control** — IOS-XE and FortiGate configurations are text files; storing
  them in git provides a full change history with diffs and commit messages, making
  auditing straightforward

For git-based config management, use a pipeline that pulls the config from the device
on change, commits it to the repository, and stores the repository off-site.

!!! note
    For FortiGate in HA, backing up the primary unit's configuration is sufficient
    — HA synchronises the configuration to the secondary automatically. Before
    relying on this, verify that synchronisation is current with
    `get system ha status` and confirm `Configuration Status: in-sync` in the output.
    If the secondary is out of sync, resolve the HA issue before treating the
    primary-only backup as complete.
