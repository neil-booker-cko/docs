# FortiGate LAG (Link Aggregation) Configuration Guide

Complete reference for configuring Link Aggregation Groups (LAG) on Fortinet FortiGate.

## Quick Start: Create LAG

```text
config system interface
  edit "aggregate1"
    set type aggregate
    set member "port1" "port2" "port3"
    set mode lacp
    set ip 192.168.1.1 255.255.255.0
    set status up
  next
end
```

---

## LAG Overview

FortiGate creates **aggregated interfaces** that bundle multiple physical ports into a single
logical
link.

### Aggregated Interface vs Port Channel

| Aspect | FortiGate Terminology | Cisco Terminology |
| --- | --------- | --- |
| Physical port | port1, port2, port3 | Gi0/1, Gi0/2, Gi0/3 |
| Logical bundle | aggregate1, aggregate2 | Port-channel 1, Port-channel 2 |
| Protocol | LACP or Static | LACP (active/passive) or Static |
| Configuration | `type aggregate` | `channel-group 1 mode active` |

---

## LAG Modes

### LACP Mode (Recommended)

Automatic negotiation using Link Aggregation Control Protocol.

```text

config system interface
  edit "aggregate1"
    set type aggregate
    set mode lacp
    set member "port1" "port2" "port3"

    ! LACP admin key (default 0; typically leave at default)
    set lacp-mode active  ! or passive
  next
end
```

**Mode combinations:**

- **active + active** = LAG forms (normal)
- **active + passive** = LAG forms (normal)
- **passive + passive** = LAG does NOT form (misconfiguration)

### Static Mode (Manual)

Manual configuration; no dynamic negotiation.

```text

config system interface
  edit "aggregate1"
    set type aggregate
    set mode static-lag
    set member "port1" "port2" "port3"

    ! Static LAG always tries to aggregate
    ! No protocol negotiation; both sides must match manually
  next
end
```

---

## Member Port Configuration

### Add Ports to LAG

```text

config system interface
  edit "aggregate1"
    set type aggregate
    set mode lacp

    ! Add member ports (multiple can be listed)
    set member "port1"
    set member "port2"
    set member "port3"

    set status up
  next
end
```

### Member Port Requirements

**What MUST match across member ports:**

- Link speed (negotiate to same speed)
- Duplex (negotiate to full duplex)

**What CAN differ:**

- Port aliases/descriptions
- VLAN configuration (if not using physical port VLAN)

### Physical Port Configuration (Pre-LAG)

Typically, member ports do NOT have IP addresses; only the aggregated interface gets IP.

```text

config system interface
  ! Member ports can be left with default config
  edit "port1"
    ! Leave default or set speed/duplex
    set speed auto   ! Auto-negotiate
    set duplex auto

    ! Do NOT assign IP to member ports
    ! Do NOT enable port individually
  next

  edit "port2"
    set speed auto
    set duplex auto
  next

  edit "port3"
    set speed auto
    set duplex auto
  next

  ! === LAG Interface (gets IP address) ===
  edit "aggregate1"
    set type aggregate
    set mode lacp
    set member "port1" "port2" "port3"

    ! IP address on LAG interface, NOT on member ports
    set ip 192.168.1.1 255.255.255.0

    set status up
  next
end
```

---

## LAG with VLANs

### VLAN on Top of LAG

```text

config system interface
  ! === LAG Interface (no IP) ===
  edit "aggregate1"
    set type aggregate
    set mode lacp
    set member "port1" "port2" "port3"
    set status up
  next

  ! === VLAN on top of LAG ===
  edit "aggregate1.100"
    set type vlan
    set vlanid 100
    set interface "aggregate1"
    set ip 10.100.0.1 255.255.255.0
    set status up
  next

  edit "aggregate1.200"
    set type vlan
    set vlanid 200
    set interface "aggregate1"
    set ip 10.200.0.1 255.255.255.0
    set status up
  next
end
```

**Result:** LAG carries traffic for both VLAN 100 and VLAN 200.

---

## Complete Configuration Example

### Scenario: FortiGate to Switch LAG (Trunk with VLANs)

```text

FortiGate                   Switch
port1 ──┐                 ┌─ Gi0/1
port2 ──┼─ aggregate1 ──── Po1 ─┼─ Gi0/2 (LAG with 4 VLANs)
port3 ──┘                 └─ Gi0/3

VLANs: 1, 100, 200, 300
```

**FortiGate Configuration:**

```text

config system interface
  ! === Physical member ports (minimal config) ===
  edit "port1"
    set speed auto
    set duplex auto
  next

  edit "port2"
    set speed auto
    set duplex auto
  next

  edit "port3"
    set speed auto
    set duplex auto
  next

  ! === LAG Interface (no IP, just aggregation) ===
  edit "aggregate1"
    set type aggregate
    set mode lacp
    set lacp-mode active
    set member "port1" "port2" "port3"
    set description "LAG to Switch-1"
    set status up
  next

  ! === VLAN 1 on LAG ===
  edit "aggregate1.1"
    set type vlan
    set vlanid 1
    set interface "aggregate1"
    set ip 192.168.1.1 255.255.255.0
    set status up
  next

  ! === VLAN 100 ===
  edit "aggregate1.100"
    set type vlan
    set vlanid 100
    set interface "aggregate1"
    set ip 10.100.0.1 255.255.255.0
    set status up
  next

  ! === VLAN 200 ===
  edit "aggregate1.200"
    set type vlan
    set vlanid 200
    set interface "aggregate1"
    set ip 10.200.0.1 255.255.255.0
    set status up
  next

  ! === VLAN 300 ===
  edit "aggregate1.300"
    set type vlan
    set vlanid 300
    set interface "aggregate1"
    set ip 10.300.0.1 255.255.255.0
    set status up
  next
end
```

**Cisco Switch Configuration (for reference):**

```ios

! Identical to Cisco EtherChannel
interface range Gi0/1 - 3
  channel-group 1 mode active
  no shutdown

interface Port-channel1
  switchport mode trunk
  switchport trunk allowed vlan 1,100,200,300
  no shutdown
```

---

## Load Balancing and Traffic Distribution

FortiGate automatically distributes traffic across member ports using a hash of source/destination
MAC
and IP.

### How Traffic Is Distributed

```text

Frame arrives: SRC_IP=10.0.0.1, DST_IP=192.168.1.1, SRC_MAC=AA:AA:AA:AA:AA:AA, DST_MAC=BB:BB:BB:BB:BB:BB

Hash: (SRC_IP + DST_IP + SRC_MAC + DST_MAC) mod 3
Result: Port 2 selected

Frame forwarded on port 2
```

**Key point:** All frames between same source/destination pair use same port (per-flow consistency).

### Verify Traffic Distribution

```text

get system interface aggregate1

! Shows interface status and statistics
! Member ports are listed; check bytes/packets per port
```

---

## Verification and Monitoring

### Check LAG Status

```text

get system interface aggregate1

! Output shows:
! name: aggregate1
! type: aggregate
! member: port1 port2 port3
! status: up
! ip: 192.168.1.1 255.255.255.0
```

### Check LAG Member Ports

```text

diagnose sys interface list | grep -A 5 aggregate1

! Shows physical member port status
```

### Check LACP Status

```text

get system interface aggregate1 | grep lacp

! Shows LACP mode and status
! Should show "lacp-mode: active"
```

### Monitor LAG Counters

```text

diagnose sys netlink addr list | grep aggregate

! Shows interface IP configuration
```

### Detailed Diagnostics

```text

diagnose sys virtual-wire list

! Shows all aggregated interfaces and members
```

---

## Common Issues and Fixes

### Issue: LAG Members Not Aggregating

**Cause:** Mode mismatch, member ports down, or incompatible LACP modes.

**Check:**

```text

get system interface aggregate1

! Verify:
! - member ports are listed
! - status is "up"
! - lacp-mode is correct (active or passive)
```

**Troubleshoot:**

```text

! 1. Check physical port status
get system interface port1
get system interface port2
get system interface port3

! 2. Verify LACP mode on both sides
! FortiGate active + Switch active = should form LAG

! 3. Check for hardware issues
diagnose sys netlink dev list
```

**Fix:**

```text

config system interface
  edit "aggregate1"
    set lacp-mode active  ! Ensure at least one side is active
    set member "port1" "port2" "port3"
  next
end
```

### Issue: LAG Interface Down

**Cause:** No member ports in LAG, all members disconnected, or LAG disabled.

**Check:**

```text

get system interface aggregate1 | grep -E "status|member"

! Verify status is "up" and members are listed
```

**Troubleshoot:**

```text

! 1. Check if any member port is up
get system interface | grep "port[0-9]" | grep "status"

! 2. Verify LAG is configured correctly
show system interface aggregate1
```

**Fix:**

```text

config system interface
  edit "aggregate1"
    set status up
    set member "port1" "port2" "port3"
  next
end
```

### Issue: One Member Port Not Participating

**Cause:** Port speed mismatch, port misconfiguration, or LACP negotiation failure.

**Check:**

```text

diagnose sys interface list | grep port1

! Look for speed mismatch or "down" status
```

**Fix:**

```text

config system interface
  edit "port1"
    ! Force auto-negotiate
    set speed auto
    set duplex auto
  next
end

! Wait 30 seconds, then check
get system interface aggregate1
```

### Issue: Traffic Not Flowing on LAG

**Cause:** Interface down, VLAN misconfiguration, or routing issue.

**Check:**

```text

! 1. Verify LAG is up
get system interface aggregate1 | grep status

! 2. Verify VLAN interfaces are up
get system interface aggregate1.100

! 3. Check routing table
get router info routing-table all

! 4. Verify firewall policies allow traffic
get firewall policy
```

**Fix:**

```text

config system interface
  edit "aggregate1"
    set status up
  next

  edit "aggregate1.100"
    set status up
  next
end
```

---

## Best Practices

| Practice | Reason |
| --- | --------- |
| Use LACP mode `active` | Ensures LAG formation |
| Configure LAG before VLANs | Cleaner, more modular |
| Use 2–4 member ports | Sweet spot for bandwidth/redundancy |
| Ensure both sides match | LACP mode must be compatible |
| Monitor member port health | Early detection of port failures |
| Document LAG configuration | Facilitate troubleshooting |
| Test failover after setup | Verify traffic survives port failure |
| Use consistent speed/duplex | Avoid mismatches and errors |

---

## Configuration Checklist

- [ ] Plan which ports will be members of LAG
- [ ] Verify all member ports are up (`get system interface port1`)
- [ ] Create `aggregate1` interface with `type aggregate`
- [ ] Set `mode lacp` (or static-lag)
- [ ] Set `lacp-mode active`
- [ ] Add member ports: `set member "port1" "port2" "port3"`
- [ ] Set `status up`
- [ ] Create VLAN interfaces on top of LAG (optional)
- [ ] Assign IPs to VLAN interfaces (not to member ports)
- [ ] Verify LAG status: `get system interface aggregate1`
- [ ] Test connectivity via LAG
- [ ] Monitor member ports for errors/failures
- [ ] Save configuration

---

## Quick Reference

```text

! Create LAG
config system interface
  edit "aggregate1"
    set type aggregate
    set mode lacp
    set lacp-mode active
    set member "port1" "port2" "port3"
    set ip 192.168.1.1 255.255.255.0
    set status up
  next
end

! Add VLAN on LAG
config system interface
  edit "aggregate1.100"
    set type vlan
    set vlanid 100
    set interface "aggregate1"
    set ip 10.100.0.1 255.255.255.0
    set status up
  next
end

! Verify
get system interface aggregate1
get system interface aggregate1.100
```
