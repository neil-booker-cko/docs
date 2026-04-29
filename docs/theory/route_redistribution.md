# Route Redistribution Fundamentals

Complete guide to importing routes from one routing protocol into another.

---

## At a Glance

| Aspect | Static→Dynamic | IGP A→IGP B | IGP→BGP | BGP→IGP |
| --- | --- | --- | --- | --- |
| **Common** | Very (branch defaults) | Sometimes (mergers) | Always (edge) | Rarely (risky) |
| **Metric Translation** | Custom seed required | Requires explicit metric | Requires MED/AS-Path | Requires seed metric |
| **Redistribution Direction** | One-way (always out) | Both ways (both ASes) | One-way (core→edge) | One-way (edge→core) |
| **Loop Prevention** | ACL/distribute-list | Route-tags + filters | AS-Path (implicit) | Dangerous; needs filters |
| **Typical Config** | 2–3 routes | 50–500 routes | 1000s of routes | 100s of routes (filtered) |
| **Risk Level** | Low (few routes) | Medium (accidental loops) | Low (AS-Path) | High (external routes inside) |
| **Best Practice** | Explicit; firewall model | Use mutual redistribution + tags | Summarize before export | Use BGP inside; avoid IGP |

---

## Core Concept

**Route redistribution** imports routes from one protocol and advertises them
through another.

```text
OSPF Network          Redistribution          BGP Network
  10.0.0.0/24    ─────────────────────→    Advertise to ISP
  10.1.0.0/24    (learned via OSPF)        via BGP

ISP Routes         ←─────────────────────   Cisco BGP Router
  0.0.0.0/0       (learned via BGP)        (redistributes BGP
  200.1.1.0/24                             into OSPF)
```

### Why Redistribute?

#### Scenario 1: Merging Networks

```text

Company A uses OSPF internally
Company B uses EIGRP internally
Companies merge → need to learn each other's routes

Solution: Router at boundary redistributes OSPF into EIGRP and vice versa
```

#### Scenario 2: Static Routes into Dynamic Protocol

```text

Branch office has static route to HQ
HQ needs to advertise branch subnets to other branches

Solution: HQ router redistributes static routes into OSPF/BGP
```

#### Scenario 3: Multiple ISPs (Different Protocols)

```text

ISP-1 uses OSPF
ISP-2 uses BGP
Internal network uses EIGRP

Solution: Border router redistributes between all three
```

---

## Metric Translation Problem

Each routing protocol uses different metrics:

- **OSPF**: Cost (bandwidth-based)
- **EIGRP**: Composite (bandwidth, delay, reliability, load)
- **BGP**: None (uses path attributes)
- **RIP**: Hop count
- **Static**: Administrative distance

### The Problem

When redistributing, the originating metric is lost. The receiving protocol
must be told what metric to assign.

```text

OSPF Route: 10.0.0.0/24 with cost 100

Router redistributes into EIGRP:
  EIGRP doesn't understand "cost 100"

Solution: Administrator specifies EIGRP metric:
  redistribute ospf 1 metric 1000 100 255 1 1500
  (bandwidth delay reliability load mtu)
```

### Default Metrics

Different platforms have different defaults when metric not specified.

```text

Cisco:
  OSPF → EIGRP: Default metric (unusable, but accepted)
  EIGRP → OSPF: Default metric 1000
  BGP → OSPF: Default metric 1

FortiGate:
  Uses default metric 0 (may not be redistributed without explicit metric)
```

**Best Practice:** Always specify metric explicitly. Never rely on defaults.

---

## Routing Loops and Prevention

### Loop Scenario

If two routers redistribute the same route, packets could loop indefinitely.

```text

Router A: Learns 10.0.0.0/24 via OSPF, redistributes into BGP
Router B: Learns 10.0.0.0/24 via BGP, redistributes into OSPF

OSPF now knows about 10.0.0.0/24 from two sources:

  1. Original OSPF source
  2. Router B's redistribution

If Router B has longer path via OSPF, it might send traffic back
through Router A, creating a loop.
```

### Prevention Method 1: Route Filtering (Distribute-List)

Block specific routes from being redistributed.

```text

Router A redistributes OSPF into BGP
Router B redistributes BGP into OSPF

At Router B:
  Block 10.0.0.0/24 (learned via BGP) from being redistributed into OSPF
  (because OSPF already learned it from original source)
```

### Prevention Method 2: Route Tags

Mark redistributed routes with a tag; don't redistribute tagged routes.

```text

Router A: redistribute OSPF into BGP, set tag 100
Router B: redistribute BGP into OSPF with condition "if tag != 100"

Result:
  Routes tagged as "came from OSPF" are not re-redistributed back
```

### Prevention Method 3: Metrics

Use administrative distance and metrics to prefer original source.

```text

OSPF route: cost 100, AD 110
Redistributed route (via BGP): cost 1000, AD 120

Router prefers OSPF (lower AD, lower cost)
Prevents loop because original source is preferred
```

### Prevention Method 4: One-Way Redistribution

Only redistribute in one direction, never in both.

```text

OSPF network ──→ BGP network (redistribute OSPF to BGP)
OSPF network ←── BGP network (do NOT redistribute BGP to OSPF)

Result:
  BGP routes reach OSPF via ISP connection
  OSPF doesn't re-advertise them back to BGP
```

---

## Redistribution Filtering

### Deny Specific Routes

```text

route-map REDIS-FILTER deny 10
  match ip address prefix-list DENY-ROUTES

route-map REDIS-FILTER permit 20
  ! Allow everything else

redistribute ospf 1 route-map REDIS-FILTER
```

### Modify Routes During Redistribution

```text

route-map REDIS-MODIFY permit 10
  match ip address 10.0.0.0/8
  set metric 1000  ! Change metric
  set tag 100      ! Tag redistributed routes
  set as-path prepend 65000  ! Add ASN to path

redistribute ospf 1 route-map REDIS-MODIFY
```

### Summarize Routes

Aggregate multiple routes into summary before redistribution.

```text

Instead of advertising:
  10.0.0.0/24
  10.0.1.0/24
  10.0.2.0/24
  10.0.3.0/24

Advertise summary:
  10.0.0.0/22
  (reduces routing table size)
```

---

## Metric Guidelines by Protocol Pair

### OSPF to EIGRP

```text

Use EIGRP metric format:
  redistribute ospf 1 metric <bandwidth> <delay> <reliability> <load> <mtu>

Example:
  redistribute ospf 1 metric 1000000 100 255 1 1500
  (bandwidth=1Gbps, delay=10ms, reliability=100%, load=1/255, mtu=1500)
```

### EIGRP to OSPF

```text

Use OSPF metric (cost):
  redistribute eigrp 100 metric 100
  (cost=100, equivalent to 1 Gbps link)
```

### BGP to Interior Gateway Protocol

```text

BGP has no metric; must be assigned
  redistribute bgp 65000 metric 100  ! OSPF
  redistribute bgp 65000 metric 1000000 100 255 1 1500  ! EIGRP
```

### Static Routes

```text

Static route has no metric; must be assigned
  redistribute static metric 100  ! OSPF
  redistribute static metric 1000000 100 255 1 1500  ! EIGRP
```

---

## Redistribution Design Patterns

### Pattern 1: Hub-and-Spoke Redistribution

```text

HQ (hub):
  Area 0: OSPF internal network
  BGP: ISP connection

  Redistribute BGP into OSPF (import ISP routes)
  Redistribute OSPF into BGP (export HQ routes to ISP)

Branch (spoke):
  EIGRP: Internal
  BGP: ISP connection

  Redistribute BGP into EIGRP (import ISP routes)
  Redistribute EIGRP into BGP (export branch routes to ISP)

Result:
  All sites learn routes from all other sites via ISP BGP
```

### Pattern 2: Gradual Migration

```text

Existing network: OSPF everywhere
New network: BGP everywhere
Migration:

  Year 1: OSPF dominant, add BGP skeleton

    - Redistribute OSPF into BGP at boundaries
    - BGP carries backbone traffic

  Year 2: Mix of OSPF and BGP

    - Redistribute both ways
    - Gradually move sites to BGP

  Year 3: BGP dominant

    - Keep OSPF for backward compat
    - Eventually remove OSPF
```

### Pattern 3: Multi-ISP with Different Protocols

```text

ISP-1: BGP AS 65001
ISP-2: OSPF AS 65002 (unusual but possible)
Internal: EIGRP AS 100

Border Router:
  Redistribute BGP 65001 into EIGRP AS 100
  Redistribute OSPF 65002 into EIGRP AS 100
  Redistribute EIGRP 100 into BGP 65001
  Redistribute EIGRP 100 into OSPF 65002

Result:
  Internal network can reach both ISPs
  ISPs can reach internal routes
```

---

## Verification Techniques

### Verify Redistributed Routes Appear

```text

Show routing table for routes that shouldn't be there natively
Example: OSPF router showing BGP routes

OSPF should NOT normally carry 0.0.0.0/0 (ISP default)
If it appears, redistribution is working
```

### Check Route Source

```text

Look at route attributes to see if redistributed

- Administrative distance changed? (original protocol would have different AD)
- Metric unusual? (redistribution metric may differ)
- Tag set? (indicates redistribution)
- AS path changed? (in BGP)
```

### Trace Route Origin

```text

Use detailed routing commands to see:

- Which routing protocol learned the route
- What metric was assigned
- When it was learned
```

---

## Common Mistakes

### Mistake 1: Not Setting Metric

```text

redistribute ospf 1
! Missing metric - may not work or may use unsafe default
```

### Mistake 2: Allowing Loop

```text

Router A: redistribute OSPF into BGP
Router B: redistribute BGP into OSPF
! Both directions - potential loop

Solution: Redistribute in one direction only,
or use filtering/tags to prevent loop
```

### Mistake 3: Forgetting Administrative Distance

```text

OSPF route: 10.0.0.0/24 via OSPF (AD 110)
Same route: 10.0.0.0/24 via redistributed BGP (AD 200)

If both exist, router prefers OSPF (lower AD)
But if BGP route is more recent, it might be used first
```

### Mistake 4: Redistributing Too Much

```text

redistribute bgp 65000 metric 100

This advertises ALL BGP routes (including ISP's ISP's routes!)
into internal OSPF network, bloating routing table

Solution: Use route-map to filter what gets redistributed
```

---

## Best Practices

| Practice | Reason |
| --- | --------- |
| **Always specify metric** | Default may not work; explicit is safer |
| **Filter what's redistributed** | Don't flood network with unnecessary routes |
| **Use route tags** | Track which routes are redistributed |
| **Prefer one-way redistribution** | Simpler; avoids loops |
| **Test in lab first** | Redistribution can cause loops; validate before prod |
| **Monitor route count** | Explosion of routes may indicate misconfiguration |
| **Document redistribution** | Complex enough to confuse future admins |
| **Use low metrics for redistribution** | Prefer native routes over redistributed |
| **Summarize before redistributing** | Reduces routing table size |
| **Disable unnecessary redistribution** | Remove after migration complete |

---

## Summary

- **Redistribution** imports routes from one protocol into another
- **Metrics must be specified** when redistributing between different protocols
- **Loops can form** if two routers redistribute same route; prevent with filtering/tags
- **Filter what's redistributed** to avoid bloating routing tables
- **One-way redistribution** is simpler than two-way
- **Test thoroughly** before production deployment
- **Use route tags and administrative distance** to prevent and detect loops

---

## See Also

- [IGP Comparison (OSPF, EIGRP, RIP)](../theory/igp_comparison.md) — Metric differences between IGPs
- [Static vs Dynamic Routing](../theory/static_vs_dynamic_routing.md) — When to use static redistribution
- [Cisco Route Redistribution Config](../cisco/cisco_route_redistribution.md) — IOS-XE syntax and examples
- [OSPF vs EIGRP](../theory/ospf_vs_eigrp.md) — Comparing the two most common IGPs
- [eBGP vs iBGP](../theory/ebgp_vs_ibgp.md) — BGP peering and route advertisement
