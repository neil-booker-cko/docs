# MPLS (Multiprotocol Label Switching)

Multiprotocol Label Switching is a forwarding mechanism that prepends a label stack to packets,
allowing fast label-based switching instead of IP routing table lookup. MPLS enables traffic engineering,
VPNs, and QoS optimization.

## Overview

- **Layer:** Layer 2.5 (between Data Link and Network)
- **Ethertype:** 0x8847 (MPLS unicast), 0x8848 (MPLS multicast)
- **Purpose:** Fast label-based forwarding, traffic engineering, VPN tunneling
- **Label range:** 0-1048575 (20-bit label field)
- **Reserved labels:** 0-15

---

## MPLS Label Stack Entry (Shim Header)

```text
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                Label (20 bits)        |TC |S|      TTL      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### Field Descriptions

| Field | Bits | Purpose |
| --- | --- | --- |
| **Label** | 20 | Label value (16-1048575 for user; 0-15 reserved) |
| **TC (Traffic Class)** | 3 | QoS marking (same as DSCP/CoS) |
| **S (Bottom of Stack)** | 1 | 1=Last label in stack, 0=More labels follow |
| **TTL** | 8 | Time-to-Live; decremented at each hop |

---

## Reserved Labels (0-15)

| Label | Name | Purpose |
| --- | --- | --- |
| **0** | IPv4 Explicit NULL | Pop label; forward as IPv4 (PHP optimization) |
| **1** | Router Alert | Interrupt forwarding; send to control plane |
| **2** | IPv6 Explicit NULL | Pop label; forward as IPv6 (PHP optimization) |
| **3** | Implicit NULL | Penultimate hop pops label (deprecated) |
| **4-13** | Reserved | Reserved for future use |
| **14** | OAM Alert | Operations & Maintenance (ping, traceroute) |
| **15** | Reserved | Reserved |
| **16+** | Available | User labels (LSPs, VPNs, traffic engineering) |

---

## MPLS Label Stack

Packets can have multiple labels (label stack); processed from top to bottom.

```text
Example: L3 VPN with Traffic Engineering

Original IP packet:
+-----+-----+-----+-----+
| IP  | TCP | Data| ... |
+-----+-----+-----+-----+

With MPLS label stack:
+-------+-------+-------+-----+-----+-----+-----+
| TE    | VPN   | Exp   | IP  | TCP | Data| ... |
| Label | Label | NULL  |     |     |     |     |
+-------+-------+-------+-----+-----+-----+-----+
        ^       ^       ^
        |       |       └── S=1 (bottom of stack)
        |       └─────────── TC=5, S=0
        └─────────────────── TC=3, S=0

Forwarding: Router reads TE label → uses it for next hop selection
            PE router pops TE label, reads VPN label
            VPN label lookup → send to Customer VRF
```

---

## MPLS Forwarding Process

### Ingress Router (Ingress Label Edge Router — ILER)

```text
Packet arrives:
  1. Lookup destination IP in routing table
  2. Find matching FEC (Forwarding Equivalence Class)
  3. Determine outgoing label for this FEC
  4. Push label onto packet
  5. Forward to next-hop router

Example:
  IP: 10.1.0.0/16 → FEC1 → Label 100
  All packets to 10.1.0.0/16 get label 100 pushed
```

### Transit Router (Label Switching Router — LSR)

```text
Labeled packet arrives on interface:
  1. Pop top label (MPLS forwarding table lookup)
  2. Find label's outgoing port and next label
  3. Push new label (swap) or pop (if S=1)
  4. Forward to next-hop router

Example:
  In label: 100 → Out label: 200 (label swap)
  In label: 200 → Out label: NONE (pop, IP forwarding)
```

### Egress Router (Egress Label Edge Router — ELER)

```text
Labeled packet arrives:
  1. Pop last label (S=1)
  2. Deliver packet to destination VRF/interface

Example:
  Label 100 → Pop → IP destination lookup → Customer interface
```

---

## MPLS LSP (Label Switched Path)

Pre-computed path from ingress to egress router.

```text
Topology:
    R1 ------- R2 ------- R3 ------- R4
   ILER       LSR        LSR        ELER
    |          |          |          |
    | Label 100| Label 200| Label 300|
    +-----> +-----> +-----> +------>

LSP: R1 → R2 → R3 → R4 (for destination 10.1.0.0/16)
    Label stack at R1: Push 100
    Label stack at R2: Swap 100→200
    Label stack at R3: Swap 200→300
    Label stack at R4: Pop 300, deliver to 10.1.0.0/16
```

---

## MPLS vs Traditional IP Routing

| Aspect | IP Routing | MPLS |
| --- | --- | --- |
| **Lookup** | IP header, every hop | Label table, every hop (faster with ASIC) |
| **Path** | Based on routing protocol (OSPF, BGP) | Can enforce explicit path (traffic engineering) |
| **Forwarding** | Destination-based | FEC-based (group destinations, not just prefix) |
| **VPN** | Overlays (GRE, VxLAN) | Native MPLS VPN (easier, standardized) |
| **QoS** | Per-packet marking | Per-LSP class of service |

---

## MPLS Applications

### 1. Traffic Engineering (TE)

Force traffic down specific path (not shortest path):

```text
Network:      R1
              / \
             /   \
           R2     R3
             \   /
              \ /
              R4

Shortest path R1→R2→R4: 2 hops
Traffic Engineering LSP R1→R3→R4: 2 hops but different links (balanced)

BGP learns best path = R1→R2→R4
MPLS TE forces R1→R3→R4
```

### 2. MPLS L3 VPN

Customer VPN over service provider MPLS backbone:

```text
Customer A ----+
               |
            +--PE--+---LSP---+--PE--+
            |  VPN |         |  VPN  |
            +------+         +------+
               |                |
            Customer B ----+------+
```

### 3. MPLS Pseudowires (L2 VPN)

Tunnel Ethernet/Frame Relay over MPLS:

```text
Customer Ethernet ----+
                      |
                   +--PE--+---LSP---+--PE--+
                   | PW   |         |  PW   |
                   +------+         +------+
                      |                |
                   Customer Ethernet ----+
```

---

## MPLS Label Distribution

### LDP (Label Distribution Protocol)

Exchange labels between adjacent routers automatically:

```text
R1: "For FEC 10.1.0.0/16, I'll use label 100"
    →(LDP advertisement) R2

R2: "I'll use label 200 for that FEC"
    →(LDP advertisement) R1 and R3

R3: "I'll use label 300"
    →(LDP advertisement) R2 and R4
```

### BGP-based (in L3 VPN)

BGP carries both routing and label information:

```text
BGP route: 10.1.0.0/16
BGP label: 500

ISP can advertise: "Route 10.1.0.0/16 with label 500"
Ingress PE pushes label 500 for routes learned via this BGP path
```

---

## Common Issues

| Issue | Cause | Fix |
| --- | --- | --- |
| **LSP not forwarding** | Label distribution failed | Check LDP neighbor status |
| **Poor QoS** | TC field not marked correctly | Enable QoS on ingress PE |
| **Label conflicts** | Two LSPs using same label | Use MPLS label allocation pool |
| **TTL exceeded** | Packet crossed too many hops | Increase TTL or reduce LSP depth |

---

## References

- RFC 3031: Multiprotocol Label Switching Architecture
- RFC 5036: LDP (Label Distribution Protocol)
- RFC 4364: BGP/MPLS IP Virtual Private Networks (L3 VPN)

---

## Next Steps

- Read [MPLS Fundamentals Theory](../theory/mpls.md)
- See [Route Redistribution](../theory/route_redistribution.md) for integration points
