# Cisco IOS-XE Software Upgrade

This guide covers production-safe software upgrade procedures for Cisco IOS-XE
platforms, including Catalyst 9000 series switches and ISR/ASR routers. It addresses
both Install mode (default on Cat9k) and Bundle mode, as well as StackWise and ISSU
upgrade paths.

---

## Bundle Mode vs Install Mode

Cisco IOS-XE platforms support two boot modes:

| Mode | How it boots | Use case |
| --- | --- | --- |
| Bundle mode | Single monolithic `.bin` file | Simpler; no in-service upgrade capability |
| Install mode | Package directory (`packages.conf`) | Default on Cat9k; supports ISSU and StackWise rolling upgrades |

To check the current boot mode:

```ios
show version | include Install
```

If the output shows `INSTALL mode`, the device is running Install mode. If it shows the
`.bin` filename directly, the device is in Bundle mode.

---

## Pre-Upgrade Checklist

Complete all items before beginning the upgrade.

| Step | Command / Action | What to record |
| --- | --- | --- |
| Verify current version | `show version` | IOS-XE version, uptime |
| Check flash space | `dir flash:` / `show platform resources` | Available bytes; ensure sufficient space for new image |
| Copy image to flash | `copy tftp://server/image.bin flash:` or USB | Confirm transfer completes without error |
| Verify image integrity | `verify /md5 flash:image.bin` / `verify /sha512 flash:image.bin` | Compare hash against Cisco download page |
| Backup running config | `copy running-config tftp:` or `archive` | Confirm backup is accessible |
| Record BGP neighbour states | `show ip bgp summary` | Peer addresses, state, prefixes received |
| Record OSPF neighbour states | `show ip ospf neighbor` | Neighbour IDs, state, interface |
| Schedule maintenance window | — | Notify stakeholders; confirm rollback window |

!!! warning
    Do not skip image hash verification. A corrupted image will cause a boot failure.
    Always verify MD5 or SHA512 against the hash published on the Cisco Software
    Download page.

---

## Install Mode Upgrade Procedure

Install mode uses a three-phase process: **add**, **activate**, and **commit**.

### Phase overview

| Phase | Command | Effect |
| --- | --- | --- |
| Add | `install add` | Copies and unpacks the image into the install store; no reload required |
| Activate | `install activate` | Sets the boot variable to the new image and schedules a reload |
| Commit | `install commit` | Marks the new version as the rollback point; removes ability to auto-rollback |

### Single-command upgrade (recommended for maintenance windows)

```ios
install add file flash:cat9k_iosxe.17.09.04.SPA.bin activate commit prompt-level none
```

This completes all three phases in sequence. The device reloads during the activate phase.

### Two-step upgrade (allows review before commit)

```ios
! Step 1: Add the image to the install store
install add file flash:cat9k_iosxe.17.09.04.SPA.bin

! Step 2: Activate — this sets the boot variable and reloads the device
install activate

! Step 3: After reload, commit to make this the new rollback point
install commit
```

!!! note
    After `install activate`, the device reloads. Log back in and verify the new version
    is running before issuing `install commit`. If there is a problem, you can rollback
    before committing.

### Checking install state

```ios
show install summary
show install log
```

---

## Rollback (Install Mode)

If the upgraded device has issues before `install commit` is issued, an automatic
rollback is available.

To manually rollback to the last committed version:

```ios
install rollback to committed
```

This does not require the original `.bin` file to be present on flash. The install
store retains the previous package set until a new commit is made.

!!! warning
    Once `install commit` is issued, the automatic rollback point moves to the new
    version. Rolling back after a commit requires the old image file or a separate
    install procedure.

---

## Bundle Mode Upgrade

Bundle mode upgrade is simpler but requires a full reload and does not support
in-service upgrades.

```ios
! Set the boot variable to the new image
boot system flash:cat9k_iosxe.17.09.04.SPA.bin

! Save the configuration
write memory

! Reload the device
reload
```

Verify after reload:

```ios
show version | include Version
```

---

## StackWise Upgrade

For Catalyst 9000 StackWise stacks, the following command upgrades all stack members
and auto-copies the image to members that do not have it:

```ios
request platform software package install switch all file flash:cat9k_iosxe.17.09.04.SPA.bin auto-copy
```

All stack members reload simultaneously unless StackWise Virtual with SSO is configured.
For non-SSO stacks, plan for a full stack reload.

!!! note
    For StackWise Virtual (SVL) deployments with SSO configured, rolling upgrade
    minimises downtime. One switch reloads while the other maintains forwarding.

---

## ISSU (In-Service Software Upgrade)

ISSU is available on Catalyst 9000 platforms with StackWise Virtual (dual-chassis SSO)
or with dual supervisor modules. It allows a software upgrade with minimal traffic
disruption.

ISSU command sequence:

```ios
! Load the new version on the standby supervisor/switch
issu loadversion <slot> file flash:cat9k_iosxe.17.09.04.SPA.bin

! Activate the new version (standby takes over)
issu runversion

! Accept the new version — traffic is now running on new software
issu acceptversion

! Commit — upgrade the original active unit
issu commitversion
```

!!! warning
    ISSU is not supported on all Cat9k platforms or all upgrade paths. Verify support
    in the target release notes before attempting ISSU. An unsupported ISSU attempt
    may fall back to a standard reload.

---

## Post-Upgrade Verification

Run these checks immediately after the device comes back online and compare against the
pre-upgrade baseline.

| Command | What to verify |
| --- | --- |
| `show version` | New IOS-XE version is active; uptime reset |
| `show ip bgp summary` | All BGP peers re-established; prefix counts match baseline |
| `show ip ospf neighbor` | All OSPF adjacencies in FULL state |
| `show interfaces status` | All expected interfaces up; no new err-disabled ports |
| `show platform resources` | CPU and memory within normal range |
| `show install summary` | Version shown as committed |
| `show log` | No unexpected error messages post-reload |

### Pre/Post Checklist

| Check | Pre-change value | Post-change value | Pass? |
| --- | --- | --- | --- |
| IOS-XE version | | | |
| BGP peers established | | | |
| BGP prefixes received (per peer) | | | |
| OSPF neighbours in FULL | | | |
| Interface error counters | | | |
| CPU utilisation (%) | | | |
| Memory utilisation (%) | | | |
