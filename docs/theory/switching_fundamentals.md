# Switching Fundamentals: MAC, Domains, and Forwarding

Layer 2 (Data Link Layer) switching is the foundation of modern networks. Understanding MAC
addresses, broadcast domains, collision domains, and how switches forward frames is critical
for network design and troubleshooting.

## MAC (Media Access Control) Addresses

### Structure

A MAC address is a 48-bit hardware address (6 octets) written in hexadecimal:

```text
Format: XX:XX:XX:XX:XX:XX

Example: 00:1A:2B:3C:4D:5E

Breakdown:
  00:1A:2B      = OUI (Organizationally Unique Identifier, vendor)
  3C:4D:5E      = Device serial number (assigned by vendor)
```

### OUI (Vendor Identifier)

The first 3 octets identify the manufacturer:

- `00:1A:2B` = Intel
- `00:0A:95` = Apple
- `00:09:B7` = Cisco
- `08:00:27` = PCI (Virtual Machines)

**Tools to lookup OUI:**

```bash
# Linux/Mac
oui-lookup 00:1A:2B

# Online
https://maclookup.app/
```

### Unicast vs Multicast vs Broadcast

| Type | MAC Address | Purpose |
| --- | --- | --- |
| **Unicast** | 00:1A:2B:3C:4D:5E | One device to one device |
| **Multicast** | First octet odd (01, 03, 05...) | One device to many devices |
| **Broadcast** | FF:FF:FF:FF:FF:FF | One device to **all devices** on segment |

**Least significant bit of first octet:**

- **0** = Unicast
- **1** = Multicast

Example:

- `00:1A:2B:...` = Unicast (0 = even)
- `01:1A:2B:...` = Multicast (1 = odd)

### MAC Addresses on Different Media

Each network segment has its own MAC addresses:

```text
Internet (WAN):
  Device A (192.0.2.1)  ↔  Router (192.0.2.254)
  └─ Layer 3 (IP) communication

Local Segment (LAN):
  PC (192.168.1.100)  ↔  Router (192.168.1.1)
  └─ Layer 2 (MAC) communication

When PC sends to 192.0.2.100 (Internet):
  1. PC → Router: uses Router's MAC (via ARP lookup)
  2. Router receives frame (destination MAC = Router's interface)
  3. Router strips MAC header, checks IP header
  4. Router sends to next hop with NEW MAC header (router's src, next-hop's dst)
```

---

## Collision Domains vs Broadcast Domains

### Collision Domain

A collision domain is a network segment where **frames can collide** (only one device can transmit
at a time).

**Half-Duplex (collisions possible):**

```text
  Bus topology (legacy):
    PC1 ──┬── PC2 ──┬── PC3
          │         │
          └─ Shared medium ─┘

  Only ONE can transmit at a time.
  If both transmit simultaneously → collision
  Collision domain = all 3 devices
```

**Full-Duplex (no collisions):**

```text
  Star topology (modern):
    PC1 ─┐
         ├─ Switch ─ PC2
    PC3 ─┘

  Each link is independent.
  PC1 and PC2 can transmit simultaneously (different wires).
  No collisions.
  Collision domain = 1 (each port/device)
```

**Devices that expand collision domain:**

- **Hub:** Creates larger shared medium (bad)
- **Repeater:** Extends single collision domain

**Devices that separate collision domains:**

- **Bridge:** Separate domains per port (2 ports = 2 domains)
- **Switch:** Separate domain per port (48 ports = 48 domains)
- **Router:** Separate at Layer 3 (IP), not Layer 2

### Broadcast Domain

A broadcast domain is a network segment where **broadcast frames are forwarded**.

**Broadcast is flooded:**

```text
  Layer 2 broadcast (MAC = FF:FF:FF:FF:FF:FF):

    PC1 (VLAN 10) ─┐
                    ├─ Switch
    PC2 (VLAN 10) ─┤
                    │
    PC3 (VLAN 20) ──┤

  When PC1 sends broadcast → forwarded to PC2 (same VLAN)
  NOT forwarded to PC3 (different VLAN)

  Broadcast domain = VLAN (PC1 + PC2)
```

**VLANs separate broadcast domains:**

- VLAN 10: PC1, PC2
- VLAN 20: PC3, PC4

**Devices that separate broadcast domains:**

- **VLAN (802.1Q tag):** Multiple broadcast domains per switch
- **Router:** Each interface = different broadcast domain

### Key Difference

| Aspect | Collision Domain | Broadcast Domain |
| --- | --- | --- |
| **Defined at** | Layer 1 (physical) | Layer 2 (data link) |
| **Scope** | Shared medium (half-duplex) | VLAN (layer 2 segment) |
| **Separated by** | Switch port (star topology) | Router, VLAN tag |
| **Modern value** | Low (full-duplex everywhere) | HIGH (VLANs for segmentation) |

---

## MAC Learning and Forwarding

### MAC Address Table

Switches learn MAC addresses from received frames and build a table:

```text
Source: PC1 (00:1A:2B:3C:4D:5E)
Destination: Server (00:09:B7:AA:BB:CC)

Switch port 1 ← receives frame from PC1

Switch learns:
  MAC Address      | Port | VLAN | Age
  ─────────────────┼──────┼──────┼────
  00:1A:2B:3C:4D:5E| 1    | 10   | 0s
```

### Forwarding Decision

```text
Frame arrives on port 1 with:
  Src MAC: 00:1A:2B:3C:4D:5E (PC1)
  Dst MAC: 00:09:B7:AA:BB:CC (Server)

1. LEARN: Add source MAC to table (port 1, VLAN 10)
2. LOOKUP: Find destination MAC in table
   - If found on port 3 → forward to port 3 ONLY
   - If NOT found → FLOOD to all ports in VLAN (except incoming)
   - If destination is broadcast (FF:FF:FF:FF:FF:FF) → FLOOD
3. FORWARD: Send frame out port 3
```

### MAC Table Aging

MAC entries age out to handle device moves:

```text
If PC1 moves from port 1 to port 5:
  Time 0s:    PC1 sends frame from port 5
              Switch learns: MAC 00:1A:2B on port 5
  Time 5s:    Old entry (port 1) still in table
              New frame arrives for PC1:
                - MAC table has TWO entries for same MAC (bad!)
                - Flooding occurs until old entry ages out
  Time 300s:  Old entry expires (default = 300 seconds / 5 minutes)
              Table now correct: 00:1A:2B on port 5 only
```

**Typical aging time:** 300 seconds (5 minutes); configurable per switch.

---

## Forwarding Methods

### Store-and-Forward

**Traditional method (safe, higher latency):**

```text
Frame arrives on port 1:
  1. Receive entire frame (buffer it)
  2. Check FCS (Frame Check Sequence) for errors
  3. Look up destination MAC
  4. Forward to destination port

Latency: Full frame time (varies by speed)
  - 10 Mbps: ~1.2 ms (1500-byte frame)
  - 100 Mbps: ~0.12 ms
  - 1000 Mbps: ~0.012 ms (12 microseconds)

Advantage: Detects bad frames (CRC errors), prevents propagation
Disadvantage: Higher latency
```

### Cut-Through

**Modern method (lower latency, less error detection):**

```text
Frame arrives on port 1:
  1. Read destination MAC (first 14 bytes)
  2. Look up destination port
  3. Forward immediately (before entire frame received)

Latency: Only MAC header time (~1.2 microseconds at 1000 Mbps)

Advantage: Minimal latency
Disadvantage: Doesn't check FCS; bad frames propagated
```

**Note:** At Gigabit speeds, latency difference is negligible (microseconds).
Modern switches use cut-through for speed.

### Fragment-Free

**Hybrid method (detect bad frames, lower latency):**

```text
Frame arrives:
  1. Receive minimum frame (64 bytes)
  2. Check FCS on fragment
  3. Forward rest

Catches many errors (runt frames, collisions) without full store-and-forward latency.
Rarely used today.
```

---

## VLAN (802.1Q) Basics

### Purpose

VLANs logically separate ports into multiple broadcast domains:

```text
Physical ports: 1, 2, 3, 4, 5, 6
VLAN assignment:
  Ports 1-2: VLAN 10 (Engineering)
  Ports 3-4: VLAN 20 (Sales)
  Ports 5-6: VLAN 30 (Guest)

Broadcast domains:
  - VLAN 10: Can reach ports 1-2
  - VLAN 20: Can reach ports 3-4
  - VLAN 30: Can reach ports 5-6
  - Cross-VLAN: Requires router

Frame from port 1 → broadcast → received by port 2 only
NOT received by ports 3-6
```

### 802.1Q Tag Format

When a frame travels between switches, it's tagged with the VLAN:

```text
Standard Ethernet:
  [Dst MAC][Src MAC][EtherType][Payload]...

802.1Q Tagged:
  [Dst MAC][Src MAC][VLAN Tag: 0x8100][VLAN ID (12-bit)][EtherType][Payload]...

Example:
  Dst MAC:  00:09:B7:AA:BB:CC
  Src MAC:  00:1A:2B:3C:4D:5E
  Tag:      0x8100 (means "this is 802.1Q")
  VLAN ID:  0x00A (VLAN 10 in decimal)
  EtherType: 0x0800 (IPv4)
```

---

## Switch Types and Capabilities

### Unmanaged Switch

```text
Plug-and-play; no configuration.
  - All ports in same VLAN
  - Broadcasts flooded to all ports
  - No VLAN support
  - No management interface

Use: Small offices, home networks
```

### Managed Switch

```text
Full configuration; VLAN support.
  - Configure VLAN membership
  - Set port speeds/duplex
  - Monitor via SNMP
  - Manage via CLI/GUI

Commands:
  show vlan
  show mac-address-table
  show interfaces
```

### Layer 3 Switch (Multilayer Switch)

```text
Combines Layer 2 (switching) + Layer 3 (routing).
  - Fast switching within VLANs
  - Inter-VLAN routing via internal router
  - No external router needed for VLAN-to-VLAN traffic

Performance: 1 Tbps+ internal switching fabric
  - Can route millions of packets/sec between VLANs
  - Still cheaper than separate router + switch

Example:
  PC1 (VLAN 10) → Switch L3 → PC2 (VLAN 20)
  No external router needed
```

---

## Spanning Tree Protocol (STP)

### Problem: Loops

Multiple switches connected create loops:

```text
    ┌─ Switch 1 ─┐
    │             │
   PC1      Switch 2 ─ Link 2
    │             │
    └─ Switch 3 ─┘

  Broadcast from PC1:
    1. Switch 1 → Switch 2, Switch 3
    2. Switch 2 → Switch 1 (loop!), Switch 3
    3. Switch 3 → Switch 1 (loop!), Switch 2
    4. Infinite loop → broadcast storm → network down
```

### STP Solution

**Spanning Tree Protocol** disables redundant links:

```text
  ┌─ Switch 1 ─┐
  │             │
 PC1      Switch 2 ── Link 2 (BLOCKED)
  │             │
  └─ Switch 3 ─┘

  Broadcast from PC1:
    1. Switch 1 → Switch 2, Switch 3 (no loop)
    2. Redundant link via Switch 2 is BLOCKED

  If Link 1 fails → STP unblocks Link 2 (30-50 second convergence)
```

**See:** [STP/RSTP Configuration](../cisco/cisco_stp_rstp_config.md)

---

## MAC Table Best Practices

✅ **Do:**

- Verify MAC table size (100k+ entries on modern switches)
- Monitor for flapping (same MAC appearing on different ports rapidly)
  → Indicates device moving or cable plugged into wrong port
- Set aging timer appropriately (300 seconds standard)
- Clear MAC table only for troubleshooting (not routine)

❌ **Don't:**

- Leave static entries in MAC table (except for known devices)
- Ignore MAC table growth (may indicate device discovery issues)
- Disable MAC learning (breaks switching)

### Clearing MAC Table (Cisco)

```ios
! Clear entire MAC table
clear mac-address-table

! Clear specific VLAN
clear mac-address-table vlan 10

! Clear specific port
clear mac-address-table interface GigabitEthernet0/1

! Verify clearing worked
show mac-address-table
```

---

## Common Switching Issues

### Broadcast Storm

```text
Symptom: Network becomes unresponsive; interfaces dropping packets

Cause: Loop or disabled spanning tree

Fix:
  1. Physically trace cabling for loops
  2. Verify STP is enabled
     show spanning-tree
  3. Look for high broadcast traffic
     show interfaces counters
  4. If loop found, disconnect one cable immediately
  5. Re-enable STP, let it converge (30-50 seconds)
```

### Flapping MAC Addresses

```text
Symptom: MAC table shows same MAC on different ports

Causes:
  1. Device moving (PC unplugged from port 1, plugged into port 2)
  2. Cable in wrong port
  3. Port mirroring loop

Debug:
  show mac-address-table dynamic
  ! Look for rapidly changing entries

  Monitor per-port:
  show mac-address-table interface GigabitEthernet0/1
```

### VLAN Not Reachable

```text
Symptom: Two devices in same VLAN can't reach each other

Causes:
  1. Wrong VLAN assignment
     show vlan | include VLAN_NAME
     show interfaces GigabitEthernet0/1 switchport | include VLAN

  2. Port not in active VLAN
     interface GigabitEthernet0/1
       switchport access vlan 10  # Assign to VLAN

  3. Spanning tree blocking port
     show spanning-tree interface GigabitEthernet0/1
     # Should show "forwarding" not "blocking"

  4. No trunk link between switches
     show interfaces trunk
     # Should list intermediate switches
```

---

## Switch Performance Metrics

| Metric | Typical Value | What It Means |
| --- | --- | --- |
| **Switching Fabric** | 1.28 Tbps (per device) | Total throughput; can handle all ports at full speed simultaneously |
| **Forwarding Rate** | 100 Mbps/port | Packets per second the switch can process |
| **MAC Table Size** | 128k-1M entries | How many unique MAC addresses switch can learn |
| **VLAN Support** | 4000-4094 VLANs | Max VLANs (4094 = 12-bit field size) |
| **STP Convergence** | 30-50 seconds (STP), <10 sec (RSTP) | Time to recover from topology change |
| **Latency** | <5 microseconds | Time from ingress to egress |

---

## Next Steps

- Learn [Physical Layer](physical_layer.md) for cabling details
- Study [Ethernet Evolution](ethernet_evolution.md) for speed/standard progression
- Configure [VLANs](vlans.md) on your network
- Understand [Spanning Tree](../theory/spanning_tree.md) for resilient networks
- Review [STP/RSTP Configuration](../cisco/cisco_stp_rstp_config.md) for implementation
