# FortiGate Firmware Upgrade

This guide covers production-safe firmware upgrade procedures for standalone
FortiGate units and high-availability (FGCP) clusters. Firmware upgrades on
FortiGate require following a supported upgrade path and careful sequencing in HA
environments to avoid outages.

---

## Supported Upgrade Paths

FortiGate firmware upgrades must follow a supported path. Skipping major versions is
not always supported and may result in a failed upgrade or configuration loss.

- Supported: 7.0 → 7.2 → 7.4
- May not be supported: 6.4 → 7.4 (direct)

Always verify the upgrade path using the
[Fortinet Upgrade Path Tool](https://docs.fortinet.com/upgrade-tool) before
proceeding. The tool takes your current and target versions and returns the required
intermediate steps.

!!! warning
    Downgrading FortiGate firmware may not restore configuration. Config file format
    changes between major versions are not backward-compatible. Always backup your
    configuration before upgrading and treat downgrade as a last resort.

---

## Pre-Upgrade Checklist

| Step | Command / Action | What to record |
| --- | --- | --- |
| Backup configuration | `execute backup config tftp <filename> <server-ip>` or GUI: System > Config > Backup | Confirm backup file is received and non-zero |
| Check HA status | `get system ha status` | Current primary/secondary roles, sync state |
| Verify disk space | `diagnose sys flash list` | Available partition space for firmware image |
| Review release notes | Fortinet docs portal | Breaking changes, deprecated features, known issues in target version |
| Confirm upgrade path | Fortinet Upgrade Path Tool | Note required intermediate versions |
| Validate rollback plan | — | Confirm backup is accessible; understand config restore process for downgrade scenario |

!!! note
    Review the release notes for every version in the upgrade path, not just the
    target version. Breaking changes introduced in an intermediate version still
    apply.

---

## Standalone Upgrade

For a standalone FortiGate unit, the upgrade can be performed from the CLI or GUI.
The unit reboots automatically after the firmware is applied. Expect approximately
3–5 minutes of downtime.

### CLI upgrade

```fortios
execute restore image tftp <filename> <server-ip>
```

The unit will prompt for confirmation, then download and apply the firmware before
rebooting.

### GUI upgrade

Navigate to **System > Firmware** and upload the firmware file or use the built-in
Fortinet upgrade portal if the unit has internet access.

### Verify after reload

```fortios
get system status
```

Confirm the firmware version matches the expected target version.

---

## HA Cluster Upgrade

Upgrading an FGCP HA cluster requires a specific sequence to avoid a simultaneous
reboot of both units, which would cause a full outage.

!!! warning
    Upgrading both HA units simultaneously causes a complete outage. Always upgrade
    the secondary unit first, wait for it to rejoin the cluster, then upgrade the
    primary.

### Manual HA upgrade sequence

1. Identify the current primary and secondary units.

    ```fortios
    get system ha status
    ```

2. Connect to the **secondary** unit directly (use its management IP, not the
   cluster virtual IP).

3. Upgrade the secondary unit:

    ```fortios
    execute restore image tftp <filename> <server-ip>
    ```

4. The secondary reboots. The primary handles all traffic during this time. Wait for
   the secondary to come back online and rejoin the cluster.

    ```fortios
    get system ha status
    ```

    Confirm the secondary is listed and in sync before proceeding.

5. Force a failover so traffic moves to the upgraded secondary unit:

    ```fortios
    execute ha failover set 1
    ```

6. Upgrade the primary unit (now acting as secondary):

    ```fortios
    execute restore image tftp <filename> <server-ip>
    ```

7. After the original primary reloads and rejoins, clear the forced failover:

    ```fortios
    execute ha failover unset 1
    ```

8. If HA override is enabled, the higher-priority unit will reclaim the primary role
   automatically after syncing.

### Uninterruptible upgrade (automated sequence)

If `set uninterruptible-upgrade enable` is configured in the HA settings, FortiOS
manages the above sequence automatically. The cluster upgrades the secondary first,
fails over, then upgrades the original primary — without manual intervention.

To verify the setting:

```fortios
show system ha | grep uninterruptible
```

---

## Post-Upgrade Verification

Run these checks after the unit or cluster has fully come back online.

| Command | What to verify |
| --- | --- |
| `get system status` | Firmware version matches target; serial number correct |
| `get system ha status` | Both cluster members present; sync state is `in-sync` |
| `diagnose sys session stat` | Session count and rate in expected range |
| `get router info bgp summary` | BGP peers established; prefix counts match baseline |
| `get router info ospf neighbor` | OSPF adjacencies in FULL state |
| `diagnose hardware sysinfo memory` | Memory utilisation within normal range |
| `get system performance status` | CPU utilisation within normal range |

### Pre/Post Checklist

| Check | Pre-change value | Post-change value | Pass? |
| --- | --- | --- | --- |
| Firmware version | | | |
| HA primary unit (serial) | | | |
| HA sync state | | | |
| BGP peers established | | | |
| BGP prefixes received (per peer) | | | |
| OSPF neighbours | | | |
| Active session count | | | |
| Memory utilisation (%) | | | |
| CPU utilisation (%) | | | |

---

## Rollback

FortiGate retains the previously running firmware image on a separate partition. To
boot the previous image:

```fortios
execute restore image {current | previous}
```

Use `previous` to reload the firmware image from before the upgrade.

!!! warning
    If the upgrade crossed a major version boundary, the configuration format may
    have changed. Restoring the previous firmware image does not automatically
    restore the previous configuration. You must restore the configuration from
    backup manually if downgrading across major versions.
