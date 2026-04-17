# Cisco IOS-XE EtherChannel Configuration Guide

Complete reference for configuring EtherChannel (port aggregation) on Cisco IOS-XE
switches.

## Quick Start: Create EtherChannel

```ios
configure terminal

! Configure member ports
interface range GigabitEthernet0/1 - 4
  channel-group 1 mode active  ! LACP mode
  no shutdown

! Configure port channel (logical interface)
interface Port-channel1
  description "LAG to Switch-2"
  switchport mode trunk
  switchport trunk allowed vlan 1,100,200,300
  no shutdown

end

show etherchannel summary
```

---

## EtherChannel Modes

### LACP (Recommended)

Dynamic negotiation using Link Aggregation Control Protocol.

```ios

configure terminal

interface range GigabitEthernet0/1 - 4
  ! Active = sends LACP packets; initiates LAG
  channel-group 1 mode active

  ! Or Passive = responds to LACP, doesn't initiate
  ! channel-group 1 mode passive

end
```

**Mode combinations:**

- **active + active** = LAG forms (normal)
- **active + passive** = LAG forms (normal)
- **passive + passive** = LAG does NOT form (misconfiguration)
- **active + static** = LAG does NOT form (incompatible)

### Static Mode (PAgP — Cisco proprietary, legacy)

Manual configuration; no dynamic negotiation.

```ios

configure terminal

interface range GigabitEthernet0/1 - 4
  ! Static mode (no negotiation)
  channel-group 1 mode on

  ! Or use PAgP (Cisco proprietary, less reliable)
  ! channel-group 1 mode desirable  (initiates negotiation)
  ! channel-group 1 mode auto       (responds to negotiation)

end
```

**Note:** Static mode (`on`) is safer if both sides are manually configured. Avoid PAgP (proprietary).

---

## Member Port Configuration

### Enable Ports in EtherChannel

```ios

configure terminal

interface range GigabitEthernet0/1 - 4
  description "LAG member"

  ! Add to channel group (1-128)
  channel-group 1 mode active

  ! Ensure ports are not in portfast mode (portfast incompatible with LAG)
  no spanning-tree portfast

  ! Enable interface
  no shutdown

end
```

### Port Configuration Rules

**What CAN differ between member ports:**

- Port descriptions
- Speed/duplex (if negotiating)
- Port priority (STP)

**What MUST match across member ports:**

- Allowed VLANs (if trunk)
- Native VLAN (if trunk)
- Spanning Tree mode
- MTU

---

## Port Channel (Logical Interface) Configuration

### Create Port Channel Interface

```ios

configure terminal

interface Port-channel1
  description "EtherChannel to Switch-2"

  ! (Optional) Assign IP address (for Layer 3 EtherChannel)
  ! ip address 192.168.1.1 255.255.255.0

  ! Or configure as switched port (Layer 2 EtherChannel)
  switchport mode trunk
  switchport trunk encapsulation dot1q
  switchport trunk allowed vlan 1,100,200,300

  no shutdown

end
```

### Access Port EtherChannel

```ios

configure terminal

interface Port-channel1
  description "LAG to access switch"

  switchport mode access
  switchport access vlan 100

  ! Enable portfast on the port-channel
  spanning-tree portfast
  spanning-tree bpduguard enable

end
```

### Trunk Port EtherChannel

```ios

configure terminal

interface Port-channel1
  description "LAG to core switch"

  switchport mode trunk
  switchport trunk native vlan 1
  switchport trunk allowed vlan 1,100,200,300

  ! STP configuration on port-channel
  spanning-tree portfast disable
  spanning-tree guard root

end
```

---

## Load Balancing Configuration

Control how traffic is distributed across member ports.

### Set Load Balancing Algorithm

```ios

configure terminal

! Global setting for ALL port-channels
port-channel load-balance <method>

! Methods:
! - src-mac           : hash based on source MAC
! - dst-mac           : hash based on destination MAC
! - src-dst-mac       : hash based on source AND destination MAC (default)
! - src-ip            : hash based on source IP
! - dst-ip            : hash based on destination IP
! - src-dst-ip        : hash based on source AND destination IP
! - src-port          : hash based on source IP + port
! - dst-port          : hash based on destination IP + port
! - src-dst-port      : hash based on source/dest IP + port

end

! Example: Layer 3 load balancing
port-channel load-balance src-dst-ip
```

### Verify Load Balancing

```ios

show etherchannel load-balance

! Output shows selected algorithm and hash buckets
```

---

## Complete Configuration Example

### Scenario: Trunk LAG Between Two Switches

```text

Switch-1                    Switch-2
Gi0/1 ──┐                 ┌─ Gi0/1
Gi0/2 ──┼─ Po1 ──────── Po1 ─┼─ Gi0/2
Gi0/3 ──┘                └─ Gi0/3

VLANs: 1, 100, 200
```

**Switch-1 Configuration:**

```ios

configure terminal

! === Member Ports ===
interface range GigabitEthernet0/1 - 3
  description "LAG member to Switch-2"

  ! Add to EtherChannel 1
  channel-group 1 mode active

  no shutdown

! === Port Channel Interface ===
interface Port-channel1
  description "LAG to Switch-2"

  ! Configure as trunk
  switchport mode trunk
  switchport trunk native vlan 1
  switchport trunk allowed vlan 1,100,200

  no spanning-tree portfast
  no shutdown

end
```

**Switch-2 Configuration (identical):**

```ios

configure terminal

interface range GigabitEthernet0/1 - 3
  description "LAG member to Switch-1"
  channel-group 1 mode active
  no shutdown

interface Port-channel1
  description "LAG to Switch-1"
  switchport mode trunk
  switchport trunk native vlan 1
  switchport trunk allowed vlan 1,100,200
  no shutdown

end
```

---

## Verification and Monitoring

### Check EtherChannel Status

```ios

show etherchannel summary

! Output:
! Channel-group 1:
! ----------
! Group state = L2
! Ports: 3   Maxports = 9
! Port-channels: 1 Max Port-channels = 9
! Load-balance = src-dst-mac
!
! Ports in the group:
! ----------
! Port      Ch#         Status
! Gi0/1     1           U
! Gi0/2     1           U
! Gi0/3     1           U
!
! ! U = Up, S = Suspended
```

### Check Port Channel Details

```ios

show etherchannel 1 detail

! Shows detailed information about Port-channel 1
! Including member ports, load balance info, protocol used
```

### Check Member Ports

```ios

show interface Port-channel 1

! Shows port-channel statistics: bytes in/out, CRC errors, etc.

show interface range GigabitEthernet0/1 - 3

! Shows individual port statistics
```

### Monitor EtherChannel Health

```ios

show etherchannel port-statistics

! Shows per-port statistics (useful to identify uneven load distribution)
```

### Check LACP Status

```ios

show lacp neighbor

! Shows LACP neighbor information
! Verify both sides are sending/receiving LACP packets
```

---

## Common Issues and Fixes

### Issue: EtherChannel Down (No Members Up)

**Cause:** Member ports down, mode mismatch, or misconfiguration.

**Check:**

```ios

show etherchannel summary

! Look for:
! - Port state: D = Down, U = Up, S = Suspended
! - Group state: should be L2 or L3
```

**Troubleshoot:**

```ios

! 1. Check member port status
show interface GigabitEthernet0/1 status

! 2. Check channel-group configuration
show run interface GigabitEthernet0/1 | include channel

! 3. Check LACP mode on both sides
show lacp neighbor
! Should show neighbors; if empty, mode mismatch
```

**Fix:**

```ios

configure terminal

! Verify mode is ACTIVE on at least one side
interface range GigabitEthernet0/1 - 4
  channel-group 1 mode active

end
```

### Issue: Port Suspended (Not Joining LAG)

**Cause:** Configuration mismatch, spanning tree incompatibility, or LACP negotiation failure.

**Status legend:**

- **D** = Down (port is shut down)
- **U** = Up (active in LAG)
- **S** = Suspended (joined LAG but not forwarding)

**Check:**

```ios

show etherchannel 1 summary

! Look for "S" status on ports

show spanning-tree inconsistency
! Check if STP incompatibility is causing suspension
```

**Fix:**

```ios

configure terminal

! Verify spanning-tree is consistent on all ports
interface range GigabitEthernet0/1 - 4
  no spanning-tree portfast
  no spanning-tree guard root

  ! Re-enable LACP
  channel-group 1 mode active

end

! Wait 30 seconds for LACP to renegotiate
show etherchannel summary
```

### Issue: Uneven Load Distribution

**Cause:** Traffic pattern doesn't match hash algorithm, or subset of flows monopolizes one port.

**Check:**

```ios

show etherchannel port-statistics

! Look at per-port byte/packet counts
! If one port >> others, traffic is not distributed
```

**Note:** This is often normal for server-to-client traffic (all packets same source/dest pair).

**Solution:** Verify load-balance algorithm is appropriate

```ios

show port-channel load-balance

! If using src-dst-mac but traffic is Layer 3 flows, switch to src-dst-ip

port-channel load-balance src-dst-ip
```

### Issue: Rapid Failover Not Happening

**Cause:** LACP timers set too long, hello timeout waiting.

**Check:**

```ios

show lacp neighbor

! Look at LACP timer state (fast/slow)
```

**Reduce LACP timeout for faster failover:**

```ios

configure terminal

interface range GigabitEthernet0/1 - 4
  lacp rate fast  ! Send LACP every 1 second (default 30)

end
```

---

## Best Practices

| Practice | Reason |
| --- | --------- |
| Use LACP mode `active` | Ensures negotiation happens |
| Match configuration on both sides | Prevents suspended ports |
| Use same speed/duplex ports | Avoids speed mismatches |
| Configure port-channel, not member ports | Port-channel is the interface to configure |
| Use even number of ports (2, 4) | Load balancing works better |
| Monitor EtherChannel health regularly | Catch port failures early |
| Document LAG mapping | Facilitate troubleshooting |
| Enable portfast on access LAGs | Speed up STP convergence |
| Use load-balance algorithm appropriate for your traffic | Layer 2 = MAC, Layer 3 = IP |

---

## Configuration Checklist

- [ ] Plan which ports will be in LAG
- [ ] Configure member ports with `channel-group` in **active** mode
- [ ] Create corresponding `Port-channel` interface
- [ ] Configure Port-channel as **access** or **trunk**
- [ ] Verify mode on both switches (both active, or one active + one passive)
- [ ] Check `show etherchannel summary` for all ports **Up (U)**
- [ ] Verify Port-channel status is **up** (`show interface Port-channel1`)
- [ ] Test traffic over LAG
- [ ] Enable LACP fast mode if fast failover needed
- [ ] Monitor load distribution (`show etherchannel port-statistics`)
- [ ] Save configuration (`write memory`)

---

## Quick Reference

```ios

! Create EtherChannel (member ports)
interface range Gi0/1 - 4
  channel-group 1 mode active
  no shutdown
end

! Configure Port Channel
interface Port-channel1
  description "LAG to Switch-2"
  switchport mode trunk
  switchport trunk allowed vlan 1,100,200
  no shutdown
end

! Verify
show etherchannel summary
show etherchannel 1 detail
show interface Port-channel1

! Load balance
port-channel load-balance src-dst-ip
```
