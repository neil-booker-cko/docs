# OSPF Advanced Concepts

Advanced OSPF topics for complex network designs: area types, virtual links, and
optimization.

---

## At a Glance

| Area Type | Type 3 (Inter-area) | Type 5 (External) | Type 7 (NSSA-external) | Routing Table Size | Use Case |
| --- | --- | --- | --- | --- | --- |
| **Regular** | Flooded | Flooded | Flooded (if ASBR) | Largest (full topology) | Backbone; large networks |
| **Stub** | Flooded | Blocked (→ default) | Blocked | Smaller (no externals) | Remote offices; smaller sites |
| **Totally Stub** | Blocked (→ default) | Blocked (→ default) | Blocked | Smallest (only intra-area) | Leaf areas; minimal routing |
| **NSSA** | Flooded | Blocked (→ default) | Flooded as Type 3 | Medium (local ABR injects) | Sites with local ASBR |

---

## OSPF Area Types

### Regular Area

All LSA types flooded; standard OSPF behavior.

```text
Area 0 (backbone): Regular area
  Receives all LSAs (types 1-5)

Area 1: Regular area
  Receives all LSAs (types 1-5)
```

### Stub Area

Blocks external routes (type 5 LSAs); uses default route to ABR instead.

```text

Advantage: Reduces routing table size; routers don't learn external prefixes
Disadvantage: Cannot distinguish between external routes; all external traffic goes to ABR

Configuration:
  Area 1: Stub

  Router in Area 1 will NOT learn:

    - Type 5 LSAs (external routes from ASBR)
    - Individual external prefixes

  Router in Area 1 WILL learn:

    - Type 3 LSAs (other areas)
    - Default route (0.0.0.0/0) to ABR
```

### Totally Stub Area

Blocks both external routes AND inter-area routes. Uses default route to ABR for everything.

```text

Advantage: Maximum reduction in routing table; simplest routers
Disadvantage: Cannot route to other areas; must go through ABR

Configuration:
  Area 1: Totally Stub

  Router in Area 1:

    - Learns only intra-area routes
    - Uses default route (0.0.0.0/0) for everything else
    - Does NOT learn other areas or external routes
```

### NSSA (Not-So-Stubby Area)

Allows local ASBR to inject external routes (type 7 LSAs) without receiving all external routes.

```text

Use Case: Branch office with local server ASBR

  - Branch ASBR redistributes local server routes
  - Branch does NOT need to learn all external routes from ISP
  - Type 7 LSAs converted to Type 5 at ABR

Advantage: Local ASBR can advertise routes; other areas not flooded
Disadvantage: More complex than stub; type 7 conversion overhead
```

### Totally NSSA

NSSA + no inter-area routes = external routes only via NSSA ASBR.

```text

Rare use case; similar to Totally Stub but NSSA ASBR can inject routes
```

---

## Area Design Patterns

### Pattern 1: Hub and Spoke (Branch Office Network)

```text

Area 0 (backbone) = HQ + core routers

Area 1 = Branch 1
  Stub area (reduces routing table)

Area 2 = Branch 2
  Stub area

Area 3 = Branch 3
  Stub area

Result:
  Branch routers learn intra-area routes
  Branch routers learn HQ area routes via ABR
  Branch routers use default route for other branches (via ABR)
```

### Pattern 2: Multiple Core Locations (Redundancy)

```text

Area 0 (backbone) = spans multiple data centers

Area 1 = DC1 (campus network)
  Regular area (DC1 has many subnets)

Area 2 = DC2 (campus network)
  Regular area

Result:
  All DCs connected via backbone
  If DC1-DC2 link down, traffic via backbone
  Each DC learns other DC's subnets
```

### Pattern 3: ISP/Internet Boundary

```text

Area 0 (backbone) = main network

Area 1 = DMZ
  NSSA area (DMZ ASBR advertises servers)
  ASBR at area 1 border connects to ISP

Result:
  DMZ ASBR can advertise server subnets to rest of network
  Rest of network doesn't flood with all ISP routes
  ASBR converts type 7 to type 5 at ABR
```

---

## Virtual Links

### Problem: Disconnected Backbone

If Area 0 is split by non-backbone routers, traffic between backbone segments must tunnel through non-backbone
area.

```text

Topology:
  Area 0: Segment A ─── Area 1 ─── Area 0: Segment B

  PROBLEM: Area 0 is split!
  Area 0 segments cannot communicate directly
```

### Solution: Virtual Link

Tunnel traffic between backbone segments through non-backbone area.

```text

Virtual link: Segment A ←→ Segment B (through Area 1)

Configuration:
  ABR1 (in Segment A):
    area 1 virtual-link 10.0.0.2

  ABR2 (in Segment B):
    area 1 virtual-link 10.0.0.1

Result:
  Segment A and B communicate via tunnel through Area 1
  Effectively rejoins Area 0
```

### When Virtual Links Are Needed

1. **Temporarily**: Maintenance, adding new area
2. **Permanently**: Design error (Area 0 should be contiguous)

**Best practice:** Redesign to make Area 0 contiguous. Virtual links are temporary fix.

---

## OSPF Optimization

### Metrics and Cost

Default OSPF cost = 100,000,000 / interface bandwidth.

```text

10 Gbps link: 100,000,000 / 10,000,000 = 10
1 Gbps link: 100,000,000 / 1,000,000 = 100
100 Mbps link: 100,000,000 / 100,000 = 1,000
10 Mbps link: 100,000,000 / 10,000 = 10,000
```

### Manual Cost Configuration

Set cost explicitly to influence path selection.

```text

Preferred path: cost 10
Backup path: cost 100

Result: Preferred path selected unless primary fails
```

### Metric Translation Between Areas

Intra-area routes use actual cost. Inter-area routes use distance (cost to ABR + advertised cost).

```text

Area 1:
  Router A → Router B: cost 10

Area 0:
  ABR advertises: "Route to Router B reachable via ABR with cost 50"

Router in Area 2:
  Sees: "Route to Router B via Area 0 with cost 50"
  (Does NOT see intra-area cost of 10)
```

---

## OSPF Convergence Optimization

### SPF Calculation Timers

Control how fast OSPF recalculates routes after topology change.

```text

Initial SPF delay: 50 ms (first calculation)
Exponential SPF delay: 5000 ms (max delay between recalculations)

Effect: Back-to-back topology changes recalculated every 50ms initially,
        then exponentially backed off to 5000ms

Result: Fast convergence for first change, then slows to avoid CPU thrashing
```

### OSPF FastHello (Sub-second Detection)

Detect neighbor failures faster using hello packets.

```text

Default: Hello every 10s, Dead 40s (4 hellos)
Fast: Hello every 1s, Dead 4s (4 hellos)

Result: Neighbor failure detected in ~4 seconds (vs 40 seconds)
```

---

## Scaling OSPF to Large Networks

### Number of Routers per Area

Recommendation: 50-100 routers per area (hard limit ~200).

### Number of Areas

Recommendation: 10-50 areas (can go higher with aggregation).

### Optimization Strategy

For networks with 1000+ routers:

1. **Divide into multiple areas** (~50-100 routers per area)
2. **Use route aggregation** (summarization)
3. **Stub/Totally Stub** for edge areas
4. **Redundant ABRs** in Area 0
5. **Monitor CPU** on ABRs (most CPU-intensive)

---

## OSPF vs ISIS vs BGP

| Aspect | OSPF | ISIS | BGP |
| --- | --------- | --- | --------- |
| **Scaling** | ~1000 routers | ~5000 routers | Unlimited |
| **Area Complexity** | Medium | Medium | High (policy) |
| **Convergence** | Fast (sub-second) | Fast (sub-second) | Slow (seconds) |
| **Use Case** | Enterprise IGP | ISP core | Inter-domain |
| **Design Flexibility** | Good | Good | Excellent |

---

## Common OSPF Design Mistakes

### Mistake 1: Backbone Not Contiguous

OSPF requires Area 0 to be contiguous. If split, use virtual links (temporary).

### Mistake 2: Too Many Areas

Each area adds CPU load on ABRs. Limit to 10-50 areas.

### Mistake 3: Wrong Area Type

Using Regular when Stub would reduce routing table size by 10x.

### Mistake 4: Inconsistent Costs

Manual cost on some links, default on others → unpredictable paths.

### Mistake 5: Summarization Not Aggregated

Advertising 100 /24 routes instead of summarizing to /16.

---

## Summary

- **Regular Area**: All LSAs; full OSPF behavior
- **Stub Area**: No external routes; default route to ABR
- **Totally Stub**: No external or inter-area; only intra-area + default
- **NSSA**: Local ASBR injects routes; other areas don't see individual externals
- **Virtual Links**: Temporary fix for disconnected backbone (redesign for permanent)
- **Scaling**: Use areas to keep per-area router count to 50-100
- **Optimization**: Summarization + stub areas + fast hello for large networks

---

## See Also

- [OSPF Fundamentals](../theory/ospf_fundamentals.md) — Core OSPF concepts and protocol mechanics
- [OSPF vs EIGRP](../theory/ospf_vs_eigrp.md) — Comparing OSPF with EIGRP
- [Cisco OSPF Configuration](../cisco/cisco_ospf_config.md) — Area design and best practices
- [Route Summarization & Aggregation](../theory/route_redistribution.md) — Inter-area route filtering
- [Data Centre Topologies](../theory/dc_topologies.md) — OSPF in modern network designs
