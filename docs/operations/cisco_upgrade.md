# Cisco IOS-XE Software Upgrade

This guide covers production-safe software upgrade procedures for Cisco IOS-XE
platforms, including Catalyst 9000 series switches and ISR/ASR routers. It addresses
both Install mode (default on Cat9k) and Bundle mode, as well as StackWise and ISSU
upgrade paths.

---

## IOS-XE Version & Boot Mode Compatibility

### Upgrade Method by IOS-XE Version

| IOS-XE Version | Default Boot Mode | Upgrade Command | Status |
| --- | --- | --- | --- |
| **16.x and earlier** | Bundle mode | `request platform software package install ...` | Legacy (sunset 2023) |
| **17.0 - 17.x** | Install mode | `install add file ... activate commit` | **Current (recommended)** |
| **18.x and later** | Install mode | `install add file ... activate commit` | **Current** |

!!! warning
    The `request platform software package install` command is **deprecated** as of IOS-XE 17.x.
    If you are running IOS-XE 17.x or later, use the modern `install` commands instead.
    Legacy commands may be removed in future releases.

### Boot Modes

Cisco IOS-XE platforms support two boot modes:

| Mode | How it boots | Use case |
| --- | --- | --- |
| Bundle mode | Single monolithic `.bin` file | IOS-XE 16.x; simpler but no ISSU |
| Install mode | Package directory (`packages.conf`) | IOS-XE 17.x+; default on Cat9k; supports ISSU |

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

## Device Prerequisites & Configuration

Before performing an upgrade, configure the device to support secure, high-speed file transfers and
modern authentication practices.

### SCP Account & Privilege Level

**Critical:** The account used for SCP file transfers must have **privilege level 15**. This applies
whether using a local account or TACACS+ authenticated user.

```ios
! Verify account privilege (run after login as the user who will do SCP)
show privilege
```

If the user is at privilege level 1 or 7, SCP operations will fail with "Permission denied". Either:

1. **Local service account (recommended for automated/scripted transfers):**

```ios
username scp_upgrade privilege 15 secret <strong-password>
```

1. **TACACS+ user configuration** — in `/etc/tac_plus.conf`, ensure the user profile returns
privilege 15:

```text
user = <username> {
    login = tacacs
    service = shell {
        set priv-lvl = 15
    }
    enable = tacacs {
        set priv-lvl = 15
    }
}
```

### AAA & SSH Configuration

Modern IOS-XE requires AAA for proper authentication and SSH access:

```ios
aaa new-model

! SSH/SCP authentication (TACACS+ primary, local fallback)
aaa authentication login default tacacs+ local

! Exec authorization (TACACS+ primary, local fallback)
aaa authorization exec default tacacs+ local

! Console access (local only — prevents lockout if TACACS+ is down)
aaa authentication login console local

! Enable SSH for SCP transfers
ip ssh version 2
ip scp server enable
```

### TCP & SSH Tuning for SCP Performance

Optimize TCP and SSH for high-speed file transfers:

```ios
! SSH window size (increase from default 2048)
ip ssh window-size 65536

! TCP window size (for negotiated TCP window scaling)
ip tcp window-size 65536

! Enable TCP Path MTU Discovery (prevents fragmentation)
ip tcp path-mtu-discovery

! TCP keepalives (prevents timeout on large transfers)
service tcp-keepalives-in
service tcp-keepalives-out
```

!!! note
    Window sizes of 65536 balance performance and memory usage. For very high-speed
    networks (10+ Gbps), 131072 is possible but uses more memory. Start with 65536.

---

## File Transfer: TFTP vs SCP

### TFTP (Legacy)

TFTP is simple and widely supported but slow (~1-5 Mbps) and unencrypted:

```ios
copy tftp://10.0.0.1/cat9k_iosxe.17.09.04.SPA.bin flash:
```

**Pros:**

- No authentication required
- Minimal device CPU overhead
- Works on any network with UDP 69

**Cons:**

- Slow (UDP-based, no windowing)
- Unencrypted
- Single-threaded transfer
- Unreliable on lossy networks

### SCP (Recommended)

SCP (Secure Copy Protocol) uses SSH and is faster (~50-200 Mbps with tuning):

```ios
copy scp://username@10.0.0.1/path/to/image.bin flash: vrf management
```

!!! warning

    **Prerequisite:** The user account must have **privilege level 15**. See
    [Device Prerequisites & Configuration](#device-prerequisites--configuration) above
    for setup instructions. If using TACACS+, the account privilege level is the most
    common reason SCP fails even when SSH exec login works.

**Pros:**

- Encrypted (SSH)
- Faster than TFTP (TCP-based with windowing)
- Authenticated
- Better network reliability
- Supports IPv6

**Cons:**

- Requires SSH server on source
- Device must have SSH client (all modern IOS-XE versions)
- SSH window size tuning needed for optimal speed

---

## SCP File Transfer Setup & Optimization

### 1. Enable SSH on Router

Ensure SSH is enabled (required for SCP client):

```ios
! Check if SSH is already enabled
show ip ssh

! If needed, enable SSH (most devices have it enabled by default)
ip ssh version 2
```

### 2. Source Server SSH Configuration

Your Linux/Windows SCP server must have SSH enabled. Verify SSH is listening:

```bash
# Linux: Check SSH daemon
sudo systemctl status ssh
# or
sudo systemctl status sshd

# Verify SSH is listening on port 22
netstat -tuln | grep :22
ss -tuln | grep :22
```

### 3. Copy File via SCP (Basic)

```ios
copy scp://admin@10.0.0.1/images/cat9k_iosxe.17.09.04.SPA.bin flash:
Password: ****
```

The router will prompt for SSH password (or use public key if configured).

### 4. Tune SSH/TCP Window Size for Faster Transfer

By default, SSH uses a small buffer which limits throughput. Tuning TCP window size on the

**source server** dramatically improves transfer speed (10x improvement possible).

#### Linux Server Tuning

Before copying, on the Linux server, increase TCP window size:

```bash
# Check current window size
cat /proc/sys/net/ipv4/tcp_rmem
# Typical output: 4096  87380  6291456 (min, default, max)

# Increase buffer sizes (as root)
sudo sysctl -w net.ipv4.tcp_rmem="4096 87380 16777216"
sudo sysctl -w net.ipv4.tcp_wmem="4096 65536 16777216"

# For SSH specifically, edit /etc/ssh/sshd_config
sudo vi /etc/ssh/sshd_config

# Add or uncomment these lines:
TCPKeepAlive yes
ClientAliveInterval 60
ClientAliveCountMax 10
# Set SSH session timeout to accommodate large files (0 = no timeout)

# Reload SSH daemon
sudo systemctl reload sshd
```

#### Windows Server Tuning (SCP via SSH)

If using Windows with OpenSSH or WinSCP:

```powershell
# PowerShell: Check current TCP window size
Get-NetTCPSetting | Format-Table State, ReceiveBufferSize

# Increase buffer (Admin PowerShell)
Set-NetTCPSetting -SettingName InternetCustom -ReceiveBufferSize 16777216

# Or use netsh (alternative)
netsh int tcp set global autotuninglevel=normal
netsh int tcp set global autotuninglevel=experimental
```

### 5. Tune Router SSH/TCP for Inbound Transfers

On the **Cisco router**, optimize inbound SCP transfer:

```ios
! Increase SSH connection buffer
ip ssh window size 32768

! Set TCP MSS clamping if needed (for fragmentation issues)
ip tcp adjust-mss 1400

! Enable TCP window scaling (RFC 1323)
ip tcp path-mtu-discovery

! Optional: TCP keepalives to prevent timeout on long transfers
service tcp-keepalives-in
service tcp-keepalives-out
```

### 6. Performance Baseline & Verification

Test transfer speed:

```bash
# Linux: Test SCP transfer with timing
time scp admin@10.0.0.1:/path/to/large_file /tmp/test

# Example output:
# real    2m15s  (135 seconds for 1 GB file = 7.4 Mbps, untuned)
# Tuned: ~100+ Mbps typical on 1 Gigabit network
```

On the router, monitor SSH session during transfer:

```ios
! While transfer is in progress (from another terminal)
show ip ssh

! Check TCP window size negotiated
show tcp brief

! Monitor CPU/memory during transfer
show processes cpu sorted
show memory statistics
```

### 7. SCP Command Examples

```ios
! Basic SCP copy
copy scp://admin@10.0.0.1/images/cat9k_iosxe.17.09.04.SPA.bin flash:

! SCP with VRF (if management interface is on separate VRF)
copy scp://admin@10.0.0.1/images/cat9k_iosxe.17.09.04.SPA.bin flash: vrf management

! SCP to alternate location
copy scp://admin@10.0.0.1/images/image.bin bootflash:staging/

! Copy with custom SSH port (if server uses non-standard port)
copy scp://admin@10.0.0.1:2222/images/image.bin flash:
```

### 8. Troubleshooting SCP Failures

| Error | Cause | Fix |
| --- | --- | --- |
| **Authentication failed** | Wrong password or user not authorized | Verify SSH credentials; check server permissions |
| **File not found** | Path incorrect or typo | Verify path on server: `ls -la /images/` |
| **Connection timeout** | Network unreachable or firewall blocking SSH | Check firewall allows TCP 22; ping server |
| **Permission denied** | SSH user lacks read permission on file | Server: `chmod 644 image.bin` |
| **Slow transfer (<5 Mbps)** | TCP window size not tuned | Apply server tuning from step 4 |
| **Transfer hangs mid-way** | SSH timeout or TCP reset | Increase `ClientAliveCountMax` on server; check MTU |

---

## Install Mode Upgrade Procedure (IOS-XE 17.x and later)

Install mode uses a three-phase process: **add**, **activate**, and **commit**. This is the

**recommended method for all current releases** (IOS-XE 17.x+).

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

## Bundle Mode Upgrade (IOS-XE 16.x and earlier)

Bundle mode upgrade applies to **IOS-XE 16.x and earlier** devices. It is simpler but requires
a full reload and does not support in-service upgrades.

!!! note
    If your device is running IOS-XE 17.x or later, use the **Install Mode** procedure instead.

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

### Modern Method (IOS-XE 17.x+)

For Catalyst 9000 StackWise in **IOS-XE 17.x and later**, use the standard `install` commands,
which auto-propagate to all stack members:

```ios

! Single-command upgrade (recommended)
install add file flash:cat9k_iosxe.17.09.04.SPA.bin activate commit prompt-level none
```

The `install add` command automatically copies the image to all stack members that do not have
it before activation.

### Legacy Method (IOS-XE 16.x and earlier - DEPRECATED)

!!! warning
    This method is **deprecated** as of IOS-XE 17.x and may be removed in future releases.
    Do not use on new deployments.

For older IOS-XE 16.x StackWise deployments, the legacy command was:

```ios

request platform software package install switch all file flash:cat9k_iosxe.16.12.04.SPA.bin auto-copy
```

### StackWise Reload Behavior

All stack members reload simultaneously unless StackWise Virtual with SSO is configured.

**For non-SSO stacks:** Plan for a full stack reload (all switches down briefly).

**For StackWise Virtual (SVL) with SSO:** Rolling upgrade minimises downtime. One switch
reloads while the other maintains forwarding.

Verify SSO capability:

```ios
show redundancy
! Look for "Redundancy State" = "SSO" or "HA"
```

---

## ISSU (In-Service Software Upgrade)

### Availability & Platforms

ISSU is available on **Catalyst 9000 and ASR 9000 platforms** running **IOS-XE 17.x or later**
with one of the following redundancy configurations:

- StackWise Virtual (dual-chassis SSO)
- Dual supervisor modules (Active/Standby)

ISSU allows a software upgrade with zero traffic disruption (hitless upgrade).

### ISSU Command Sequence (IOS-XE 17.x+)

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
