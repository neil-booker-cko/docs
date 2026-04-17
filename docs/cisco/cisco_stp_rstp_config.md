# Cisco IOS-XE STP/RSTP Configuration Guide

Complete reference for configuring STP and RSTP on Cisco IOS-XE platforms.

## Quick Start: Enable RSTP

```ios
configure terminal

! Set global STP mode to RSTP (recommended)
spanning-tree mode rapid-pvst

! Configure primary root (lowest priority = higher preference)
spanning-tree vlan 1 priority 0

! Configure backup root
! (run on a different switch)
spanning-tree vlan 1 priority 4096

! Save configuration
write memory
```

---

## Global STP Configuration

### Set STP Mode

```ios

configure terminal

! Use RSTP (Rapid PVST+) - recommended for all modern deployments
spanning-tree mode rapid-pvst

! Or use legacy STP (PVST+) - slower convergence, avoid if possible
spanning-tree mode pvst

show spanning-tree summary
```

### Configure Root Bridge

Select which switch becomes the root. The root bridge has priority 0 and all other switches reference
it.

```ios

configure terminal

! Make this switch the primary root (priority 0, all VLANs)
spanning-tree vlan 1 root primary

! Or explicitly set priority
spanning-tree vlan 1 priority 0

! For backup root on a different switch
spanning-tree vlan 1 root secondary

! Verify
show spanning-tree vlan 1
```

### BPDU Settings

```ios

configure terminal

! Change BPDU interval (default 2 seconds)
! Lower = faster convergence, more CPU
spanning-tree vlan 1 hello-time 1
spanning-tree vlan 1 forward-time 10
spanning-tree vlan 1 max-age 20

! Note: These are typically left at default unless tuning for specific needs
```

---

## Per-Interface Configuration

### Enable PortFast (Access Ports)

PortFast disables STP listening/learning phases on access ports, speeding up host connectivity.

```ios

configure terminal

! Configure single interface
interface GigabitEthernet0/1
  spanning-tree portfast

! Or configure range
interface range GigabitEthernet0/1 - 24
  spanning-tree portfast

! Verify
show spanning-tree interface GigabitEthernet0/1 detail
```

**Note:** Use ONLY on access ports (connected to hosts). Never on trunk ports between switches.

### BPDU Guard (Protect Access Ports)

Prevents accidental switch-to-switch connections. If a BPDU arrives on a PortFast port, shut it down.

```ios

configure terminal

interface GigabitEthernet0/1
  spanning-tree portfast
  spanning-tree bpduguard enable

! Verify
show spanning-tree inconsistentports
```

#### Optional: Auto-Recovery

```ios

configure terminal

! Automatically re-enable err-disabled port after delay (default 300s)
errdisable recovery cause bpduguard
errdisable recovery interval 60  ! 60 seconds delay

! Verify
show errdisable recovery
```

### Root Guard (Uplink Ports)

Prevents a port from accepting BPDUs from a better bridge (prevents takeover by rogue switch).

```ios

configure terminal

! Configure on uplink ports
interface GigabitEthernet0/48
  spanning-tree guard root

! If a superior BPDU arrives, port blocks and logs alert
! Port unblocks once superior BPDU stops arriving

! Verify
show spanning-tree interface GigabitEthernet0/48 detail
```

### Loop Guard (Blocked Ports)

Prevents loops due to unidirectional link failures. If expected BPDUs stop arriving on a blocked port,
keep it blocked instead of transitioning to forwarding.

```ios

configure terminal

interface GigabitEthernet0/2
  spanning-tree guard loop

! Verify
show spanning-tree interface GigabitEthernet0/2 detail
```

### Adjust Port Priority (Cost)

Manual path engineering. Lower cost = preferred path.

```ios

configure terminal

interface GigabitEthernet0/1
  ! Set cost (1 Gbps = 4, 10 Gbps = 2, 100 Mbps = 19)
  spanning-tree cost 4

  ! Or adjust port priority for tie-breaking
  spanning-tree port-priority 64   ! Default is 128

show spanning-tree interface GigabitEthernet0/1 detail
```

---

## Per-VLAN Configuration (PVST+)

Run separate STP instance per VLAN for load balancing.

```ios

configure terminal

! VLAN 1: Make Core-1 the root
spanning-tree vlan 1 priority 0

! VLAN 2: Make Core-2 the root
spanning-tree vlan 2 priority 0

! On Core-2 switch:
spanning-tree vlan 2 priority 0
spanning-tree vlan 1 priority 4096  ! Backup for VLAN 1

! Result: VLAN 1 traffic prefers Core-1, VLAN 2 prefers Core-2
show spanning-tree vlan 1
show spanning-tree vlan 2
```

---

## Complete Configuration Example

### Scenario: Two-Core Network

```text

        Core-1 (Root)
          / eth0 (primary link)
         /
    Access-1
         \
          \ eth1 (backup link)
        Core-2 (Backup Root)
```

**Core-1 Configuration:**

```ios

configure terminal

! Set as primary root
spanning-tree mode rapid-pvst
spanning-tree vlan 1 priority 0

! Access ports: enable portfast + bpdu guard
interface range GigabitEthernet0/1 - 24
  spanning-tree portfast
  spanning-tree bpduguard enable

! Uplink to Access-1: root guard
interface GigabitEthernet0/48
  spanning-tree guard root

! Auto-recover from BPDU guard
errdisable recovery cause bpduguard
errdisable recovery interval 60

write memory
```

**Core-2 Configuration:**

```ios

configure terminal

! Set as backup root
spanning-tree mode rapid-pvst
spanning-tree vlan 1 priority 4096

! Access ports
interface range GigabitEthernet0/1 - 24
  spanning-tree portfast
  spanning-tree bpduguard enable

! Uplink
interface GigabitEthernet0/48
  spanning-tree guard root

errdisable recovery cause bpduguard
errdisable recovery interval 60

write memory
```

**Access-1 Configuration:**

```ios

configure terminal

spanning-tree mode rapid-pvst

! Access ports
interface range GigabitEthernet0/1 - 23
  spanning-tree portfast
  spanning-tree bpduguard enable

! Uplinks to Core (trunks)
interface GigabitEthernet0/24
  ! This will be the preferred root port (lower cost)
  spanning-tree cost 4
  description Primary link to Core-1

interface GigabitEthernet0/25
  ! Backup link (higher cost, blocked unless primary fails)
  spanning-tree cost 8
  description Backup link to Core-2

errdisable recovery cause bpduguard
errdisable recovery interval 60

write memory
```

---

## Verification and Troubleshooting

### Check STP Status

```ios

! Overall STP summary
show spanning-tree summary

! Details for specific VLAN
show spanning-tree vlan 1

! Interface-level details
show spanning-tree interface GigabitEthernet0/1 detail

! Root bridge information
show spanning-tree root
```

### Identify Root Bridge

```ios

show spanning-tree vlan 1 | include "Root ID"

! Output example:
! Root ID    Priority    4097
!           Address     0000.1111.2222
!           This bridge is the root
```

### Check Port Roles and States

```ios

show spanning-tree interface | include "Port"

! Expected output shows:
! Name      Role  Sts Cost    Prio.Nbr
! Gi0/1     Root FWD 4        128.1    (root port: forwards)
! Gi0/2     Desg FWD 4        128.2    (designated: forwards)
! Gi0/3     Altn BLK 8        128.3    (alternate: blocked, backup)
```

### Monitor BPDU Health

```ios

debug spanning-tree bpdu
undebug all  ! Stop debugging
```

### Verify PortFast Status

```ios

show spanning-tree interface GigabitEthernet0/1 detail | include "PortFast"

! Should show: PortFast Enabled
```

### Check err-disabled Ports

```ios

show errdisable interface

! Shows which ports are disabled and why
```

---

## Common Issues and Fixes

### Issue: Port in err-disabled State After BPDU Guard

**Cause:** BPDU was received on a PortFast port.

**Solution:**

```ios

! Manually bring port back up
configure terminal
interface GigabitEthernet0/10
  no shutdown

! Or configure auto-recovery (recommended)
errdisable recovery cause bpduguard
errdisable recovery interval 60
```

### Issue: Convergence Too Slow (Still Using STP)

**Check mode:**

```ios

show spanning-tree summary

! Should show: Name version STP max age 20 forward delay 15 hello time 2
!             RSTP max age 20 forward delay 15 hello time 2
```

**Enable RSTP:**

```ios

configure terminal
spanning-tree mode rapid-pvst
```

### Issue: Wrong Port Selected as Root Port

**Cause:** Mismatched costs between uplinks.

**Fix:** Explicitly set lower cost on preferred port:

```ios

configure terminal
interface GigabitEthernet0/48
  spanning-tree cost 4  ! Preferred

interface GigabitEthernet0/49
  spanning-tree cost 8  ! Backup
```

### Issue: Unexpected Root Bridge

**Cause:** Priority not explicitly set; lowest MAC becomes root.

**Fix:**

```ios

configure terminal
spanning-tree vlan 1 priority 0  ! Make this switch root
```

---

## Best Practices

1. **Use RSTP** (`spanning-tree mode rapid-pvst`) in all new deployments
2. **Set explicit root priorities** — don't rely on MAC tie-breaking
3. **Enable PortFast + BPDU Guard** on all access ports
4. **Enable Root Guard** on uplink ports to prevent rogue takeover
5. **Enable auto-recovery** from BPDU guard errors
6. **Document port costs** — keep topology predictable
7. **Monitor STP health** — check `show spanning-tree` regularly
8. **Use PVST+** to load-balance across multiple root bridges if multi-VLAN

---

## References

- `show spanning-tree ?` — Interactive help
- `show spanning-tree root` — Root bridge info
- `show spanning-tree interface <port> detail` — Detailed port status
- `debug spanning-tree bpdu` — BPDU logging (use with caution)
