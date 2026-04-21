# BGP (Border Gateway Protocol)

Border Gateway Protocol is a path-vector exterior gateway protocol used for inter-autonomous system
(AS) routing. BGP exchanges full routing tables and path attributes (AS path, next-hop, local
preference, MED) to allow networks to make informed routing decisions based on policy and path
characteristics, not just shortest distance.

## Overview

- **Layer:** Application/Network (Layer 3-4)
- **Transport:** TCP port 179
- **Purpose:** Inter-AS routing; policy-based path selection; route aggregation
- **Versions:** BGPv4 (RFC 4271); BGP with MPLS VPN (RFC 4364)
- **Typical use:** ISP-to-ISP, datacenter-to-cloud, enterprise edge routing
- **Keepalive interval:** 60 seconds (default); Hold time 180 seconds
- **Message types:** Open, Update, Keepalive, Notification, Route-Refresh

---

## BGP Message Format (TCP Stream)

All BGP messages start with a 19-byte header:

```text
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                                 |
+                                                                 +
|                    Marker (16 bytes, all 1s)                 |
+                                                                 +
|                                                                 |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Length (2)          |     Type (1)    | [Payload]   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### Field Descriptions

| Field | Bytes | Purpose |
| --- | --- | --- |
| **Marker** | 16 | All 1s (0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF); synchronization |
| **Length** | 2 | Total message length (header + payload), 19-65535 bytes |
| **Type** | 1 | Message type: 1=Open, 2=Update, 3=Notification, 4=Keepalive, 5=Route-Refresh |

---

## BGP Message Types

### 1. Open (Type 1)

Initiates BGP session; exchanges AS number, Router ID, capabilities.

```text
My AS: 65001
My Router ID: 10.0.0.1
Hold Time: 180 seconds
BGP Identifier: 10.0.0.1
Optional Parameters: Capabilities (MP-BGP, Route Refresh, 4-Byte ASN, etc.)
```

**Capabilities Advertisement (Optional Parameters):**

- MP-BGP: Multiprotocol (IPv6, VPN)
- 4-Byte ASN: Support for ASN > 65535
- Route Refresh: Dynamic route reannouncement without session restart

### 2. Update (Type 2)

Announces new routes or withdraws previously advertised routes.

```text
Withdrawn Routes (NLRI removal):
  - 10.1.0.0/16
  - 10.2.0.0/16

Path Attributes:
  - ORIGIN: IGP (learned internally) / EGP (from external) / INCOMPLETE
  - AS_PATH: [65001, 65002, 65003] (list of ASes route traversed)
  - NEXT_HOP: 192.0.2.1 (next-hop IP to reach this prefix)
  - LOCAL_PREF: 100 (local preference; higher = preferred within AS)
  - MULTI_EXIT_DISC (MED): 50 (metric for external comparison; lower = preferred)
  - COMMUNITIES: [65001:100] (grouping for policy)
  - EXTENDED COMMUNITIES: [RT:65001:100] (Route Target for VPN)

NLRI (Network Layer Reachability Information):
  - 10.3.0.0/24
  - 10.4.0.0/24
  (prefix length + prefix = route being advertised)
```

**Path Attributes Decision Process:**

1. **Weight** (Cisco only): 0-65535; highest wins (local device only)
1. **Local Preference** (IGP to EBGP): Higher wins (within AS)
1. **Shortest AS_PATH**: Fewer ASes wins (loop prevention + efficiency)
1. **ORIGIN**: IGP > EGP > INCOMPLETE
1. **MED** (MULTI_EXIT_DISC): Lower wins (inter-AS preference)
1. **EBGP vs IBGP**: EBGP preferred (true external)
1. **IGP Metric**: Lowest IGP cost to NEXT_HOP wins
1. **Router ID**: Lowest Router ID wins (tiebreaker)

### 3. Keepalive (Type 4)

Heartbeat; confirms session is alive. Sent every 60 seconds (default).

```text
No payload — just header.

If no keepalive or update received within Hold Time (180s), neighbor declared down.
```

### 4. Notification (Type 3)

Error notification; terminates session.

```text
Error Code: 1 (Message Header Error)
              2 (OPEN Message Error)
              3 (UPDATE Message Error)
              4 (Hold Timer Expired)
              5 (Finite State Machine Error)
              6 (Cease)

Subcode: Specific error (e.g., "Unsupported Capability")
Data: Optional diagnostic data
```

### 5. Route-Refresh (Type 5)

Requests peer to resend all routes (without session restart). Requires Route-Refresh capability.

```text
Address Family: IPv4 Unicast, IPv6 Unicast, VPN, etc.

Peer responds with all routes for that AFI/SAFI without teardown.
```

---

## BGP Session States

```text
IDLE → CONNECT → ACTIVE → OPENSENT → OPENCONFIRM → ESTABLISHED
  |       |         |         |          |             |
  |       |         |         |          |             └─ Full route exchange
  |       |         |         |          └─ Awaiting Keepalive
  |       |         |         └─ Sent Open, waiting for peer Open
  |       |         └─ Retrying connection
  |       └─ TCP connect in progress
  └─ Down; ready to connect
```

**ESTABLISHED:** Only state where routes are exchanged and traffic flows.

---

## BGP Session Types

### External BGP (EBGP)

Peers in different ASes; full routing table exchange; policy-driven.

```text
ISP1 (AS 65001) ←→ ISP2 (AS 65002)
  (EBGP session over direct link or via upstream ISP)

ISP1 advertises: 203.0.113.0/24 with AS_PATH [65001]
ISP2 receives:   203.0.113.0/24 with AS_PATH [65001, 65002] (adds itself)
ISP2 advertises: 203.0.113.0/24 with AS_PATH [65001, 65002] to rest of internet
```

### Internal BGP (IBGP)

Peers within same AS; distributes external routes; must be fully meshed or use route reflectors.

```text
Router A (AS 65000, DC-A)  ←→ Router B (AS 65000, DC-B)
         (IBGP session, shares EBGP-learned routes)

A receives 203.0.113.0/24 from ISP (EBGP).
A advertises to B via IBGP: 203.0.113.0/24 with AS_PATH [ISP_AS]
(B uses A's local-pref, weight, etc. to decide path)
```

---

## Common BGP Attributes Table

| Attribute | Type | Usage | Example |
| --- | --- | --- | --- |
| **LOCAL_PREF** | Well-Known Mandatory | Prefer local paths within AS | 100 (higher = preferred) |
| **MED** | Optional | Prefer external paths to peer ASes | 50 (lower = preferred) |
| **AS_PATH** | Well-Known Mandatory | Prevent loops; prefer shorter paths | [65001, 65002] |
| **NEXT_HOP** | Well-Known Mandatory | Next-hop IP for route | 192.0.2.1 |
| **ORIGIN** | Well-Known Mandatory | Route origin (IGP/EGP/INCOMPLETE) | IGP |
| **COMMUNITIES** | Optional | Policy grouping (COLOR tagging) | 65001:100 |
| **EXTENDED COMMUNITIES** | Optional | VPN route targets, BGP Flowspec | RT:65001:100 |
| **WEIGHT** | Cisco only | Local preference (highest priority) | 100-500 |

---

## BGP Scalability & Design Patterns

### Full Mesh (Small Networks)

Every router peers with every other router (N routers = N*(N-1)/2 sessions).

```text
3 routers: 3 IBGP sessions
4 routers: 6 IBGP sessions
10 routers: 45 IBGP sessions ← Becomes unwieldy
```

### Route Reflector (Hierarchical)

One reflector; other routers peer with it (hub-and-spoke within AS).

```text
Router A (RR)
   |    \    \
   |     \    \
   B      C    D

RR advertises external routes to B, C, D; no need for full mesh.
```

### Confederation (Very Large Networks)

Divide AS into sub-ASes; reduces IBGP sessions further.

```text
AS 65000 = AS 65001 (sub-conf) + AS 65002 (sub-conf) + AS 65003 (sub-conf)

Reduces IBGP sessions by grouping routers into smaller domains.
```

---

## Common BGP Issues

| Issue | Cause | Fix |
| --- | --- | --- |
| **Session not coming up** | TCP 179 blocked; AS/Router ID mismatch | Verify firewall; check `show bgp summary` |
| **Routes not advertised** | Network not in BGP table; no redistribute | Use `network` or `redistribute` commands |
| **Flapping routes** | Unstable adjacency; rapid updates | Check interface stability; use BFD |
| **Suboptimal routing** | LOCAL_PREF not set; MED ignored | Adjust attributes; verify policy |
| **Route loops** | Misconfigured AS_PATH prepending | Review AS_PATH filtering |

---

## References

- RFC 4271: A Border Gateway Protocol 4 (BGPv4)
- RFC 4364: BGP/MPLS IP Virtual Private Networks (L3 VPN)
- RFC 5668: 4-Byte AS Number Space

---

## Next Steps

- Read [BGP Theory & Design](../theory/bgp.md)
- See [Routing Protocols Comparison](../theory/routing_protocols.md)
- Configure BGP: [Cisco BGP](../cisco/cisco_bgp_config.md), [FortiGate BGP](../fortigate/fortigate_bgp_config.md)
