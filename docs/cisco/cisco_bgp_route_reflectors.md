# Cisco BGP Route Reflectors and Confederations Guide

Complete reference for scaling iBGP in large networks using route reflectors.

## Quick Start: Configure Route Reflector

```ios
configure terminal

router bgp 65000
  bgp cluster-id 1

  ! This router is a route reflector
  ! It will reflect iBGP routes to other clients

  neighbor 10.0.0.2 remote-as 65000
  neighbor 10.0.0.2 route-reflector-client

  neighbor 10.0.0.3 remote-as 65000
  neighbor 10.0.0.3 route-reflector-client

end
```

---

## The iBGP Full Mesh Problem

### iBGP Split Horizon Rule

iBGP has a critical rule: **iBGP routes learned from one iBGP neighbor are NOT advertised to other
iBGP
neighbors**.

**Reason:** Prevent routing loops in IBGP.

### Problem: Full Mesh Required

In a small network, all routers must be neighbors (full mesh):

```text

Network with 4 routers (A, B, C, D):

Full mesh = 6 eBGP sessions:
  A ↔ B
  A ↔ C
  A ↔ D
  B ↔ C
  B ↔ D
  C ↔ D

Calculation: n(n-1)/2 = 4(3)/2 = 6 sessions

Problem: 100 routers = 4,950 sessions!
Scaling nightmare.
```

### Solution: Route Reflectors

A **route reflector (RR)** breaks the split-horizon rule. It reflects iBGP routes to other clients.

```text

With route reflector:

Route Reflector (RR)
   ↑    ↑    ↑    ↑
   |    |    |    |
  A    B    C    D
(clients)

Clients only need 1 session (to RR)
RR reflects routes between clients
Total sessions: 4 (A-RR, B-RR, C-RR, D-RR)

Benefit: Reduces from n(n-1)/2 to n
100 routers: 4,950 sessions → 100 sessions!
```

---

## Route Reflector Roles

### Route Reflector (RR)

A special iBGP router that reflects routes between clients.

```text

Router RR configuration:
  router bgp 65000
    neighbor 10.0.0.2 remote-as 65000
    neighbor 10.0.0.2 route-reflector-client
    ! Now RR will advertise iBGP routes to this client
```

**Behavior:**

- Receives iBGP route from Client A
- Reflects to Client B (breaks split-horizon)
- Updates reflected route's originator-id and cluster-list

### Route Reflector Client

An iBGP router that peers only with the RR.

```text

Router A (client) configuration:
  router bgp 65000
    neighbor 10.0.0.100 remote-as 65000
    ! Only neighbor is the RR
    ! Does NOT know about other clients
```

**Behavior:**

- Sends iBGP routes to RR
- Receives reflected routes from RR
- Thinks RR is the only iBGP peer

### Non-Client (Peer Routers)

iBGP routers that peer with RR but are NOT clients (full-mesh between themselves).

```text

RR configuration:
  neighbor 10.0.0.2 remote-as 65000
  neighbor 10.0.0.2 route-reflector-client

  neighbor 10.0.0.3 remote-as 65000
  neighbor 10.0.0.3 route-reflector-client

  neighbor 10.0.0.4 remote-as 65000
  ! NO route-reflector-client for this neighbor
  ! This is a peer, not a client
  ! Must maintain full-mesh with other peers

  neighbor 10.0.0.5 remote-as 65000
  ! Also a peer
```

---

## Route Reflector Attributes

### Originator ID

Tracks the origin of the reflected route (prevents loops).

```text

Router A originates: 10.0.0.0/24
  Originator_ID = 10.0.0.1 (Router A's ID)

Route Reflector reflects to Router B
  BGP update includes: Originator_ID = 10.0.0.1
  (not RR's ID, but original source)

If route comes back to Router A:
  Router A sees: Originator_ID = 10.0.0.1 (my own ID)
  Action: IGNORE (don't accept route from yourself)
```

### Cluster List

Tracks which RRs have reflected this route (prevents loops in RR hierarchy).

```text

Cluster ID = identifier for RR (typically RR's router ID)

Primary RR reflects route:
  Cluster_List = [1]

Secondary RR reflects same route:
  Cluster_List = [1, 2]

If route returns to Primary RR:
  RR checks: Is my cluster ID (1) in Cluster_List?
  YES → IGNORE (already reflected by me)
```

---

## Route Reflector Topologies

### Single Route Reflector

Simplest: one RR, all other routers are clients.

```text

        RR
       /  \
      /    \
     A      B      C      D
  (clients)

Peering:
  RR - A
  RR - B
  RR - C
  RR - D
  (no client-to-client peering)

Risk: RR is single point of failure
```

### Redundant Route Reflectors

Two or more RRs, all routers clients to both RRs.

```text

    RR1       RR2
    / \       / \
   /   \     /   \
  A     B   C     D
(all clients to both RRs)

Peering:
  A - RR1, A - RR2
  B - RR1, B - RR2
  C - RR1, C - RR2
  D - RR1, D - RR2

Advantage: RR redundancy
Disadvantage: More connections
```

### Hierarchical Route Reflectors

Cluster of RRs, with each RR as client to parent RR.

```text

        Primary RR
        /         \
      RR1         RR2
      / \         / \
     A   B       C   D
  (clients to RR1)  (clients to RR2)

Peering:
  A - RR1 (client)
  B - RR1 (client)
  RR1 - Primary (client)
  RR2 - Primary (client)
  C - RR2 (client)
  D - RR2 (client)

Benefit: Scales to very large networks
         Each cluster managed independently
```

---

## Complete Route Reflector Configuration

### Scenario: 4-Router Network with Central RR

```text

Central RR (Router ID 10.0.0.100)
   |
   +--RR-Client1 (10.0.0.1)
   +--RR-Client2 (10.0.0.2)
   +--RR-Client3 (10.0.0.3)
```

**Route Reflector Configuration (RR):**

```ios

configure terminal

router bgp 65000
  bgp router-id 10.0.0.100
  bgp cluster-id 1  ! Cluster ID (typically RR's ID)

  ! Client 1
  neighbor 10.0.0.1 remote-as 65000
  neighbor 10.0.0.1 description "Client A"
  neighbor 10.0.0.1 route-reflector-client

  ! Client 2
  neighbor 10.0.0.2 remote-as 65000
  neighbor 10.0.0.2 description "Client B"
  neighbor 10.0.0.2 route-reflector-client

  ! Client 3
  neighbor 10.0.0.3 remote-as 65000
  neighbor 10.0.0.3 description "Client C"
  neighbor 10.0.0.3 route-reflector-client

end
```

**Client A Configuration:**

```ios

configure terminal

router bgp 65000
  bgp router-id 10.0.0.1

  ! Only neighbor is RR
  neighbor 10.0.0.100 remote-as 65000
  neighbor 10.0.0.100 description "Route Reflector"

  ! Advertise local routes
  network 10.1.0.0 mask 255.255.0.0

end
```

#### Client B and C: Similar to Client A

---

## BGP Confederations (Alternative to RR)

**Confederations** divide a single ASN into sub-ASNs with eBGP between them.

```text

Without confederation (full mesh problem):
  ASN 65000 with 100 routers
  Need 4,950 iBGP sessions

With confederation:
  ASN 65000 divided into:
    65000.1 (20 routers)
    65000.2 (20 routers)
    65000.3 (20 routers)
    65000.4 (20 routers)

  Within each sub-ASN: full mesh (20 × 19 / 2 = 190 sessions each)
  Between sub-ASNs: eBGP (mesh of sub-ASNs)

  Total: 4 × 190 + eBGP between 4 sub-ASNs = much less than 4,950
```

### Confederation vs Route Reflector

| Aspect | Route Reflector | Confederation |
| --- | --------- | --- |
| **ASN** | Single ASN | Single external ASN, multiple internal |
| **Internal Sessions** | iBGP (limited by RR) | iBGP within sub-ASNs |
| **External Sessions** | To RR only | eBGP between sub-ASNs |
| **Complexity** | Medium (RR logic) | High (sub-ASN management) |
| **Scalability** | Good (to ~1000 routers) | Excellent (to 10k+) |
| **AS Path Length** | Preserved (originator-id) | Lengthened (looks like eBGP hops) |

**Recommendation:** Use route reflectors for most networks (< 1000 routers). Use confederations for
very large networks (>1000 routers).

---

## Verification and Troubleshooting

### Check Route Reflector Status

```ios

show bgp ipv4 unicast summary

! Output shows neighbors and their state
! RR clients should show as "Established"
```

### Check if Route is Being Reflected

```ios

show ip bgp 10.0.0.0/24

! Look for:
! - Originator ID (original router that originated route)
! - Cluster List (RRs that have reflected)
```

### Check Originator ID

```ios

show ip bgp 10.0.0.0/24 detail

! Output:
! Originator: 10.0.0.1
! Cluster list: 1
! (route originated by 10.0.0.1, reflected by cluster 1)
```

### Verify Client Status

```ios

show ip bgp neighbor 10.0.0.1

! Look for:
! Route Reflector client: True
! (confirms this neighbor is a client)
```

---

## Common Issues and Fixes

### Issue: Route Not Reflected to Clients

**Cause:** Neighbor not configured as route-reflector-client.

**Check:**

```ios

show ip bgp neighbor 10.0.0.1 | include Reflector

! Should show: Route Reflector client: True
```

**Fix:**

```ios

configure terminal

router bgp 65000
  neighbor 10.0.0.1 route-reflector-client

end
```

### Issue: Suboptimal Path Selected

**Cause:** RR choosing less-optimal route due to originator-id or cluster-list.

**Check:**

```ios

show ip bgp 10.0.0.0/24 detail

! Look at:
! - AS Path (should be same for all paths)
! - Originator ID
! - Local Preference
```

**Fix:** Use route-map to set local preference on RR for preferred path.

### Issue: Route Loop (Same Route Advertised Back)

**Cause:** Cluster ID not configured; RR accepting its own reflected routes.

**Check:**

```ios

show ip bgp summary

! Look for high number of route updates
! Or specific routes advertised/withdrawn repeatedly
```

**Fix:**

```ios

configure terminal

router bgp 65000
  bgp cluster-id 1  ! Set cluster ID to break loops

end
```

---

## Best Practices

| Practice | Reason |
| --- | --------- |
| **Use route reflectors for <1000 routers** | Scales well; simpler than confederations |
| **Redundant RRs for production** | Eliminates single point of failure |
| **Set cluster ID explicitly** | Prevents loops; must match across all RRs in cluster |
| **Monitor RR CPU/memory** | RR processes more updates than clients |
| **Document RR topology** | Facilitates troubleshooting and changes |
| **Use hierarchical RRs for very large networks** | Scales to 10,000+ routers |
| **Test RR changes in lab** | Verify routes reflect as expected before production |
| **Verify originator-id** | Confirms route is from expected source |

---

## Configuration Checklist

- [ ] Designate which routers are route reflectors
- [ ] Configure RR with bgp cluster-id
- [ ] Identify which neighbors are clients (route-reflector-client)
- [ ] Identify which neighbors are full-mesh peers (no route-reflector-client)
- [ ] Configure all clients to peer only with RR
- [ ] Maintain full-mesh between non-client peers (if any)
- [ ] Verify neighbors are "Established"
- [ ] Verify routes are reflected (show ip bgp detail)
- [ ] Test failover (remove RR, verify routes still learned)
- [ ] Monitor RR statistics
- [ ] Document RR topology

---

## Quick Reference

```ios

! Route Reflector Configuration
router bgp 65000
  bgp cluster-id 1
  neighbor 10.0.0.2 remote-as 65000
  neighbor 10.0.0.2 route-reflector-client
end

! Client Configuration
router bgp 65000
  neighbor 10.0.0.100 remote-as 65000
  ! That's it — peer only with RR
end

! Verify
show bgp ipv4 unicast summary
show ip bgp 10.0.0.0/24 detail
show ip bgp neighbor 10.0.0.2 | include Reflector
```
