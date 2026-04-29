# OSPF vs EIGRP — Interior Gateway Protocols

OSPF (Open Shortest Path First, RFC 2328 / RFC 5340 for IPv6) and EIGRP (Enhanced Interior
Gateway Routing Protocol, Cisco proprietary until 2013, now RFC 7868) are the two dominant
interior gateway protocols in modern networks. Both are distance-vector / link-state hybrids
designed for scalable, rapidly converging routing within an Autonomous System. OSPF is open
standard and vendor-neutral; EIGRP is Cisco-optimised but now openly published. The choice
between them depends on vendor ecosystem, scaling requirements, network maturity, and
convergence demands.

For detailed routing protocol comparisons, see also [EIGRP vs OSPF vs RIP](igp_comparison.md)
and [Routing Protocols Overview](../routing/index.md).

---

## At a Glance

| Property | OSPF v2 | EIGRP |
| --- | --- | --- |
| **Standard** | RFC 2328 (open, vendor-neutral) | Cisco proprietary (now RFC 7868, RFC 5310 for OSPF-like authz) |
| **Metric basis** | Cost (bandwidth-based) | Composite (bandwidth, delay, reliability, load, MTU) |
| **Metric formula** | `100,000,000 / bandwidth_bps` | `256 × [(K1 × BW + (K2 × BW / (256 − Load)) + K3 × Delay + (K4 × Reliability / (256 − Load))) / (K5 × Reliability + K6)]` |
| **Default metric** | Cost ~= 100Mbps bandwidth | BW ~1 Gbps, Delay ~100ms in LAN segment |
| **Convergence time** | 30–180 seconds (tunable) | 1–10 seconds (fast re-route DUAL) |
| **Routing approach** | Link-state (SPF tree) | Advanced distance-vector (DUAL algorithm) |
| **Scalability** | ~100s of routers per area; multi-level hierarchy | ~100s of routers per autonomous system; less hierarchy needed |
| **Memory footprint** | Large (full topology DB per area) | Small (route summaries, diffusing computations) |
| **Bandwidth usage** | Efficient (only on topology change) | Efficient (hello + periodic updates) |
| **Hello interval** | 10 seconds (broadcast), 30 (point-to-point) | 5 seconds (multicast), 60 on WAN links |
| **Dead interval** | 40 seconds (broadcast), 120 (point-to-point) | 15 seconds, 180 on WAN links |
| **Authentication** | MD5 (OSPFv2), implicit with IPv6 in OSPFv3 | MD5, HMAC-SHA-256 (RFC 5310) |
| **Load balancing** | ECMP (equal-cost), unequal-cost via policy | ECMP native, unequal-cost via traffic-share |
| **Vendor support** | All vendors (Cisco, Arista, Juniper, Fortinet, etc.) | Mostly Cisco/IOS-XE; limited third-party |

---

## How Each Protocol Works

### OSPF: Link-State Flooding and SPF

OSPF routers maintain a **complete topology database** — every router in the area knows
every link and its cost. Routers advertise themselves and their connected links in Link
State Advertisements (LSAs). These LSAs are flooded across the area to every router.

**OSPF processes:**

1. **Neighbour discovery (Hello):** OSPF hello packets are multicast on every interface.
   Neighbours are elected based on matching subnet and parameters. Designated Router (DR)
   and Backup Designated Router (BDR) are elected on broadcast networks (Ethernet).

1. **Topology exchange:** Each router sends LSAs listing its connections and costs.

1. **SPF computation:** When a topology change is detected (LSA update), every router
   runs Dijkstra's Shortest Path First algorithm to recompute shortest paths to all
   destinations.

1. **Routing table update:** Routes are installed in the RIB and FIB.

**Key advantage:** Link-state topology awareness is **direct and deterministic**. A
router knows exactly why it chose a path (the SPF tree).

**Example:** In a network of 20 routers:

- R1 floods an LSA saying "I have a link to R2 with cost 10"
- Every router in the area receives this LSA
- Every router re-runs SPF to recompute its path to R2
- Convergence: ~10–20 seconds depending on SPF computation and LSA propagation

### EIGRP: Distance-Vector with DUAL Algorithm

EIGRP sends periodic hello packets and **distance-vector updates** (not full topology).
A router tells its neighbours "I can reach destination X with distance D." EIGRP does
not require full topology knowledge; it works with **Feasible Successors** and **Backup
Routes**.

**EIGRP DUAL algorithm:**

1. **Feasible distance:** The best known distance to a destination (lowest metric).

1. **Advertised distance:** The distance a neighbour claims to that destination.

1. **Feasible successor:** A backup next-hop that satisfies the feasibility condition:
   `advertised_distance < feasible_distance`. A feasible successor can be used without
   re-convergence because it is guaranteed to be loop-free.

1. **Diffusing computation:** When the best route fails and no feasible successor exists,
   EIGRP queries neighbours for alternative paths. This is fast but can cause temporary
   black holes if all neighbours also lack feasible successors.

**Key advantage:** **Sub-second convergence** to a feasible successor. EIGRP can switch
to a pre-computed backup route almost instantly, without waiting for full SPF
recomputation.

**Example:** In a network of 20 routers:

- R1 advertises "I can reach 10.0.0.0/24 with distance 2560"
- R2 receives this and compares: advertised_distance (2560) < my_feasible_distance (3072)?
  Yes, so R1 is a feasible successor for the backup path.

- When the primary path fails, R2 switches to R1 without querying anyone else. Convergence:
  < 100ms.

---

## Metric Calculation: The Deep Difference

### OSPF Metric (Cost)

OSPF cost is simple: `cost = 100,000,000 / bandwidth_bps`

- A 10 Mbps link: cost = 10,000
- A 100 Mbps link: cost = 1,000
- A 1 Gbps link: cost = 100
- A 10 Gbps link: cost = 10

Delay, reliability, load, and MTU are **not part of the metric**. OSPF assumes that
bandwidth is the only relevant factor for path selection. This is usually correct
(bandwidth is the constraint) but requires that admins manually tune costs for exceptions.

**Tuning:** Admin can override cost with:

```ios
interface Gi0/0/1
 ip ospf cost 1000
```

### EIGRP Metric (Composite)

EIGRP is composable by default:

```text
Metric = 256 × [(K1 × BW + (K2 × BW / (256 − Load)) + K3 × Delay + (K4 × Reliability / (256 − Load))) / (K5 × Reliability + K6)]
```

Where:

- **K1 (bandwidth):** Default = 1
- **K2 (load):** Default = 0 (disabled, prevents oscillations)
- **K3 (delay):** Default = 1
- **K4, K5, K6:** Advanced options for reliability tuning; rarely used

In practice, EIGRP default metric simplifies to:

```text
Metric = 256 × (Bandwidth + Delay) / (10^7)
```

Which incorporates both **bandwidth and delay** in a single metric. This makes EIGRP more
intuitive for path selection: latency-sensitive traffic naturally prefers lower-delay
paths.

**Example:**

- Path A: 10 Mbps, 10ms delay → metric ≈ 25,600 + 10,240 = 35,840
- Path B: 1 Mbps, 1ms delay → metric ≈ 256,000 + 1,024 = 257,024

Path A is chosen despite being 10× faster in bandwidth, because the delay difference
(10ms vs 1ms) is significant. OSPF would choose Path A purely on bandwidth.

---

## Convergence Speed and Scalability

### OSPF Convergence

OSPF convergence depends on:

1. **Detection time** (hello timeout): 40–120 seconds default, tunable to ~3 seconds
1. **LSA propagation delay:** ~3–5 seconds to flood across an area
1. **SPF computation time:** ~1–5 seconds (depends on number of routers and links)

**Total default convergence:** ~30–180 seconds

**Tuning OSPF for fast convergence:**

- Reduce hello/dead timers: `ip ospf hello-interval 1` (1 second) and `ip ospf dead-interval
  4` (4 seconds)

- Use BFD (Bidirectional Forwarding Detection) for sub-second failure detection
- Precompute unequal-cost paths with local policies to avoid SPF during convergence

### EIGRP Convergence

EIGRP convergence is **two-tier:**

1. **Feasible successor available:** Convergence is sub-second (~100–500ms). No diffusing
   computation needed.
1. **No feasible successor:** EIGRP queries neighbours. Convergence is 1–10 seconds,
   depending on topology and query propagation.

**Tuning EIGRP for sub-second convergence:**

- Configure multiple paths / ensure feasible successors exist
- Use `timers active-time 0` to disable active timeout (but risk permanent queries)
- Use BFD to detect failures in < 300ms

**Advantage:** EIGRP's sub-second convergence (when feasible successors exist) is
superior to OSPF's SPF-dependent model, assuming network design provides redundancy.

---

## Complexity and Operability

### OSPF Complexity

OSPF introduces **hierarchy** as a fundamental concept:

- **Area 0 (backbone):** Core area, all inter-area routes pass through it
- **Stubby areas:** Block external routes, reduce LSDB size
- **Totally stubby areas:** Accept only a default route and intra-area routes
- **NSSA (Not-So-Stubby Area):** Can inject external routes locally via type 7 LSAs

Multi-area OSPF requires careful planning:

- Area boundaries must be between routers (ABRs)
- Hierarchical design is a requirement, not optional
- Misconfigurations are easy: OSPF will work, but inefficiently

**Operators love OSPF because:**

- The SPF tree is deterministic and debuggable
- Link-state updates mean every router knows the full picture
- Troubleshooting is visual: `show ip ospf database` shows exactly why paths were chosen

**Operators dislike OSPF because:**

- Multi-area design is mandatory for scale — too much planning for small networks
- SPF computation and large LSDBs consume CPU on older hardware
- Convergence tuning requires understanding timers, LSA generation delays, and SPF
  parameters

### EIGRP Complexity

EIGRP is simpler at design time but requires understanding the DUAL algorithm:

- **No areas:** EIGRP works autonomously system-wide; no hierarchy needed for small-to-medium
  networks

- **Route summarization:** Automatic or manual; reduces query scope significantly
- **Feasible successors:** Must be understood to predict convergence behaviour

**Operators love EIGRP because:**

- Flat design; no multi-area hierarchy required
- Sub-second convergence with feasible successors
- Lower LSDB size and memory consumption (distance-vector summaries vs link-state flooding)
- Easier initial configuration for branch offices and hub-and-spoke

**Operators dislike EIGRP because:**

- Cisco proprietary (though RFC 7868 exists, third-party support is limited)
- DUAL algorithm is less intuitive; "why did the route go here?" requires understanding
  advertised distance and feasibility

- Query storms (diffusing computations) can bring down networks if designed poorly
- Requires understanding of `metric weights`, `offset-lists`, and manual summarization for
  optimal design

---

## Scaling and Enterprise Use

### OSPF Scaling Model

**Multi-area OSPF scales to thousands of routers:**

- Per-area LSDB grows with the number of routers in that area
- Inter-area routes are summarized at Area Border Routers (ABRs)
- Proper hierarchy prevents LSDB explosion
- Service provider backbone: 100s of routers in the core, split into regions/areas

**ISP and large enterprise standard:** OSPF is the default for large, vendor-diverse,
geographically distributed networks.

### EIGRP Scaling Model

**EIGRP scales to hundreds of routers within a single AS without hierarchy:**

- Routers exchange distance vectors; topology is implicit from metric differences
- Route summarization reduces update traffic and query scope
- Flat design works well for private IP WAN (< 200 routers)
- Rarely used beyond a single AS; no standard for inter-domain EIGRP

**Cisco-centric, smaller-scale deployments:** Branch offices, regional hubs, campus
networks.

---

## Migration Path: EIGRP to OSPF

Many mature Cisco networks run EIGRP and face pressure to migrate to OSPF for
vendor neutrality. Migration strategies:

### 1. Gradual Redistribution

Introduce OSPF on new devices; redistribute between EIGRP and OSPF on boundary routers.

```ios
! On boundary router: redistribute EIGRP into OSPF
router ospf 1
 redistribute eigrp 100 subnets metric-type 1 metric 100

! And vice versa
router eigrp 100
 redistribute ospf 1 metric 1000 100 255 1 1500
```

**Risks:** Routing loops, metric mismatches, asymmetric paths.

### 2. Parallel Operation

Run both protocols on all devices for 3–6 months. OSPF routes via default distance tuning:

```ios
! Prefer OSPF routes (lower AD)
router ospf 1
 distance ospf intra-area 90

router eigrp 100
 ! Leave default AD = 90
```

Gradually de-advertise EIGRP prefixes; once all traffic flows through OSPF, shut down
EIGRP.

### 3. Per-Region Cutover

Split the network into regions. Migrate each region separately:

1. Region A: OSPF only
1. Region B: EIGRP + OSPF (redistribution at region border)
1. Region C: EIGRP only (will migrate next month)

**Advantages:** Limits blast radius if redistribution goes wrong. Allows operational
experience with OSPF before full cutover.

---

## Cisco Configuration Examples

### OSPF Single Area

```ios
router ospf 1
 network 10.0.0.0 0.0.0.255 area 0
 network 192.168.1.0 0.0.0.255 area 0
 default-information originate

interface Gi0/0/1
 ip address 10.0.1.1 255.255.255.0
 ip ospf cost 100
```

### OSPF Multi-Area

```ios
router ospf 1
 area 1 stub  ! Area 1 is stubby; blocks external routes
 network 10.0.0.0 0.0.0.255 area 0  ! Backbone
 network 192.168.1.0 0.0.0.255 area 1

! Border router must summarize into area 0
 area 1 range 192.168.1.0 255.255.255.0 cost 10

! Inject external route
 default-information originate metric 1000 metric-type 1
```

### EIGRP Autonomous System

```ios
router eigrp 100
 network 10.0.0.0 0.0.0.255
 network 192.168.1.0 0.0.0.255
 passive-interface default
 no passive-interface Gi0/0/1
 no passive-interface Gi0/0/2

interface Gi0/0/1
 bandwidth 1000000  ! 1 Mbps (for metric calculation)
 delay 100  ! tens of microseconds
```

### EIGRP with Summarization

```ios
router eigrp 100
 network 10.0.0.0 0.0.0.255

! Summarize 192.168.0.0/22 (192.168.0.0 to 192.168.3.0) at the ABR
interface Gi0/0/10
 ip summary-address eigrp 100 192.168.0.0 255.255.252.0 5

! Verify
show ip eigrp topology | include Summary
```

---

## When to Use Each

### Use OSPF when

- The network includes **non-Cisco devices** (Arista, Juniper, Fortinet, etc.). OSPF is
  vendor-neutral; EIGRP support is rare outside Cisco.

- The network is **large and geographically distributed** (ISP, large enterprise). Multi-
  area OSPF scales well with proper hierarchy.

- **Standards compliance** is required. RFC 2328 is the industry standard for IGPs.

- The organization is **transitioning from EIGRP** or standardizing on open protocols.

- **Design clarity matters more than absolute convergence speed.** OSPF's SPF tree is
  predictable and debuggable.

### Use EIGRP when

- The network is **Cisco-only** (small/medium enterprise, branch offices, regional hubs).
  EIGRP's sub-second convergence and ease of configuration are compelling.

- **Sub-second convergence** is a hard requirement and feasible successors can be
  guaranteed via design (network is highly redundant).

- The organization **already has mature EIGRP expertise** and sees no immediate need to
  migrate.

- The network is **small-to-medium (<100 routers)** and doesn't warrant the design overhead
  of multi-area OSPF.

### Practical Differences That Matter Most

1. **Vendor diversity:** If any device is non-Cisco or you plan to add non-Cisco devices,
   choose OSPF.

1. **Convergence requirements:** EIGRP's sub-second convergence to feasible successors is
   hard to beat, but requires redundancy and design discipline.

1. **Operations and training:** OSPF requires more upfront design but is easier to debug.
   EIGRP is easier to deploy but harder to troubleshoot.

1. **Scale expectations:** OSPF's multi-area model is designed for thousands of routers.
   EIGRP typically maxes out at hundreds.

---

## Notes

- **RFC 7868:** EIGRP was open-sourced in 2013 as RFC 7868. However, only Cisco has a
  complete, mature implementation. Juniper and others have limited EIGRP support.

- **Administrative Distance:** OSPF has AD 110 (lower is better). EIGRP has AD 90. If
  both run simultaneously, EIGRP routes win. This matters during migrations.

- **DUAL algorithm:** The Diffusing Update Algorithm (DUAL) is Cisco's proprietary
  contribution. It ensures loop-free convergence without requiring full topology knowledge
  — an elegant algorithm but not universally adopted.

- **BFD integration:** Both OSPF and EIGRP can integrate with BFD for sub-second failure
  detection, independent of protocol timers.

- For detailed IGP comparison across three protocols, see [EIGRP vs OSPF vs RIP](igp_comparison.md).

---

## See Also

- [IGP Comparison (OSPF, EIGRP, RIP)](../theory/igp_comparison.md) — Three-way IGP comparison
- [OSPF vs IS-ISIS](../theory/ospf_vs_isis.md) — OSPF vs service provider choice
- [Cisco OSPF Configuration](../cisco/cisco_ospf_config.md) — OSPF setup and tuning
- [Cisco EIGRP Configuration](../cisco/cisco_eigrp_config.md) — EIGRP setup and tuning
- [Route Redistribution](../theory/route_redistribution.md) — Running both protocols together
