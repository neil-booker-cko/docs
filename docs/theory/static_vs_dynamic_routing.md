# Static vs Dynamic Routing — Routing Fundamentals

Static routing and dynamic routing are two fundamentally different approaches to populating
a router's routing table. **Static routing** means the administrator manually configures
each route; the router does not learn routes from peers. **Dynamic routing** means routers
exchange routing information via protocols like OSPF, EIGRP, or BGP, building the routing
table automatically. Most networks use a **hybrid approach:** dynamic routing for
reachability in the core, static routes for specific purposes (default routes, summaries,
exceptions). Understanding the trade-offs is essential for network design.

For detailed routing protocol comparisons, see [OSPF vs EIGRP](ospf_vs_eigrp.md),
[EIGRP vs OSPF vs RIP](igp_comparison.md), and [Routing Protocols Overview](../routing/index.md).

---

## At a Glance

| Property | Static Routing | Dynamic Routing |
| --- | --- | --- |
| **Configuration** | Manual per router | Automatic via protocol |
| **Scalability** | Poor (O(n) routes per router) | Good (scales to thousands) |
| **Convergence time** | N/A (no convergence) | 1–180 seconds (protocol-dependent) |
| **Failure detection** | None (manual intervention required) | Automatic (hello timers) |
| **CPU overhead** | Minimal (no computation) | Moderate (SPF, diffusing computation) |
| **Bandwidth overhead** | None (no updates) | Low-to-moderate (periodic hellos + updates) |
| **Complexity** | Low (simple to understand) | High (protocol-specific knowledge required) |
| **Route optimisation** | Manual (admin must tune metrics) | Automatic (protocol-driven) |
| **Suitable for** | Small networks, branches, specific routes | Large networks, redundancy, failover |

---

## Static Routing: Manual Configuration

Static routing is the simplest form of routing: the administrator explicitly configures
each route via `ip route` commands. The router makes no decisions — it either knows how
to reach a destination (explicit route exists) or drops the packet.

### How Static Routing Works

A static route entry consists of:

1. **Destination:** Destination IP prefix (CIDR notation)
2. **Next-hop:** The IP address of the next router or the outbound interface
3. **Administrative Distance (AD):** A preference metric (0–255; lower is preferred)
4. **Metric:** Optional metric used for tie-breaking if multiple routes to the same
   destination exist

**Example:**

```text
ip route 10.0.0.0 255.255.0.0 192.168.1.1  ! Send traffic for 10.0.0.0/16 via 192.168.1.1
ip route 172.16.0.0 255.255.0.0 Gi0/0/1    ! Send traffic for 172.16.0.0/16 via Gi0/0/1
ip route 0.0.0.0 0.0.0.0 203.0.113.1       ! Default route: anything not matched → send to ISP
```

### Advantages of Static Routing

1. **Predictability:** Routes are exactly as configured. No surprises; what you see is what
   you get.

2. **CPU efficiency:** No routing protocol computations. Even ancient routers can handle
   static routes.

3. **Security:** Routes are not leaked via protocol advertisements. An attacker cannot
   inject false routes via a routing protocol.

4. **Bandwidth efficiency:** No periodic hello messages or routing updates. Minimal
   overhead.

5. **Debugging simplicity:** A static route either works (next-hop is reachable) or does
   not (next-hop is down). No SPF computations to trace.

### Disadvantages of Static Routing

1. **No failover:** If the next-hop becomes unreachable, the route remains in the table.
   Traffic is still forwarded to the dead next-hop and dropped. The router does not learn
   an alternative path.

2. **Manual updates required:** Any topology change (new site, new link) requires manual
   route configuration. Does not scale.

3. **No redundancy awareness:** Static routes cannot automatically switch to a backup path
   if the primary path fails.

4. **Operator error:** Large static route tables are error-prone. Typos in CIDR notation or
   next-hop IP addresses go undetected until traffic is affected.

5. **Not suitable for complex topologies:** Hundreds of static routes are unmanageable.

### Use Cases for Static Routing

- **Small branches (1–2 routers):** A branch office with a single uplink to HQ uses a
  default static route: `ip route 0.0.0.0 0.0.0.0 <hq_ip>`.

- **Default routes:** Almost all networks use a default static route at the edge:
  `ip route 0.0.0.0 0.0.0.0 <isp_gateway>`.

- **Specific exceptions:** A network might use dynamic routing globally but static routes
  for specific, rarely-changing destinations (e.g., a legacy system reachable via a
  specific next-hop).

- **Network summarisation:** At aggregate points (e.g., a regional hub), static route
  summaries can be used to reduce dynamic routing table size.

- **Firewall rules:** Firewalls often use static routes for internal segmentation,
  complemented by dynamic routing for external traffic.

---

## Dynamic Routing: Automatic Learning and Failover

Dynamic routing protocols (OSPF, EIGRP, BGP) enable routers to **learn routes from peers**
and automatically adapt when topology changes. The protocol exchanges routing information
in a standardised format; each router computes its own routing table independently.

### How Dynamic Routing Works

1. **Neighbour discovery:** Routers periodically send hello packets to discover peers on
   directly connected links.

2. **Topology exchange:** Routers advertise their connected interfaces and learned routes
   in protocol-specific messages (LSAs in OSPF, distance vectors in EIGRP, etc.).

3. **Route computation:** Each router computes shortest paths (or best paths) based on
   received topology information.

4. **Convergence:** Once all routers have exchanged information and recomputed their
   tables, the network is said to have **converged**. Traffic flows along optimal paths.

5. **Adaptation:** When a link fails, routers detect the failure (hello timeout) and
   recompute, potentially choosing a different path.

### Advantages of Dynamic Routing

1. **Automatic failover:** If a primary path fails, routers detect the failure and switch
   to an alternative path, often within seconds.

2. **Scalability:** Routers learn routes from many peers. The number of routes grows
   automatically with network size.

3. **Optimisation:** Routers choose paths based on metrics (cost, delay, bandwidth). The
   "best" path is chosen automatically.

4. **Redundancy-aware:** If multiple paths exist, dynamic routing can load-balance traffic
   across them (ECMP) or pre-compute backup paths (EIGRP).

5. **Minimal manual configuration:** Routes are not manually entered per router. A single
   configuration (e.g., `network 10.0.0.0 0.0.0.255 area 0` in OSPF) enables learning
   for an entire prefix.

### Disadvantages of Dynamic Routing

1. **Complexity:** Understanding routing protocols requires significant effort. Tuning
   metrics, timers, and policies is non-trivial.

2. **Convergence time:** If a link fails, convergence can take seconds to minutes (default
   timers). During convergence, traffic may be black-holed or misrouted.

3. **CPU overhead:** SPF computation (OSPF) or diffusing computations (EIGRP) consume CPU,
   especially during convergence on large networks.

4. **Bandwidth overhead:** Periodic hello messages and routing updates consume bandwidth,
   though typically minimal on modern networks.

5. **Route leakage:** A misconfigured routing protocol can advertise unintended routes to
   peers, causing traffic redirection or loops.

6. **Debugging difficulty:** Troubleshooting routing protocol issues requires understanding
   algorithm details (SPF, DUAL, BGP path selection). Simple `show route` output may not
   explain why a route was or was not chosen.

### Use Cases for Dynamic Routing

- **Large networks (>50 routers):** Manual route configuration is infeasible. Dynamic
  routing is required.

- **Redundant networks:** A network with multiple paths (mesh topology) requires dynamic
  routing to detect failures and converge.

- **Service provider backbones:** ISP networks with hundreds of routers use BGP for inter-
  domain routing and OSPF/ISIS for intra-domain routing.

- **Data centres:** Networks with spine-leaf topologies use OSPF or BGP to automatically
  load-balance traffic across multiple paths.

- **Cloud environments:** Networks connecting to AWS, Azure, or GCP use BGP to advertise
  routes from the cloud provider back to the enterprise.

---

## Hybrid Approaches: The Practical Middle Ground

Most networks use a **combination of static and dynamic routing**, optimising for both
simplicity and resilience.

### Pattern 1: Dynamic Core + Static Edge

```text
        Core (OSPF or BGP)
      /          |          \
   R1 (HQ)    R2 (Hub)    R3 (Regional)
     |            |            |
Branch-A(static)  ISP-1        Branch-B(static)
                  |
               ISP-2
```

- **Core:** OSPF or BGP among core routers
- **Edge:** Static routes at branch offices pointing to HQ
- **ISP links:** Static default routes pointing to each ISP

**Advantage:** Core routers learn about each other dynamically; branches are simple static
configs.

### Pattern 2: Dynamic Routing + Backup Static Route

```text
router ospf 1
 network 10.0.0.0 0.0.0.255 area 0

! Primary route via OSPF (AD 110)
! If OSPF fails, use static backup (AD 200)
ip route 192.168.0.0 255.255.0.0 10.0.0.254 200
```

If the OSPF path to `192.168.0.0/16` fails (peer down, link failure), the static route
with higher AD (200) becomes active.

### Pattern 3: Default Static + Dynamic for Specific Routes

```text
! Default route is static (simple, stable)
ip route 0.0.0.0 0.0.0.0 203.0.113.1

! Internal routes are dynamic (automatically learned)
router ospf 1
 network 10.0.0.0 0.0.0.255 area 0
```

Internal traffic is routed via OSPF; external (Internet) traffic goes via the static
default route.

---

## Convergence: How Fast Is Fast Enough?

**Convergence time** is the time from link failure to traffic flowing on an alternative
path. Different applications have different requirements:

| Use Case | Convergence Requirement | Protocol | Actual Convergence |
| --- | --- | --- | --- |
| **Web browsing** | Seconds OK | OSPF, BGP | 30–180 seconds default |
| **VoIP** | <150ms loss (single packet) | EIGRP + BFD | < 500ms with BFD |
| **Financial trading** | <100ms loss | EIGRP or BGP + BFD | < 300ms with BFD |
| **Carrier-grade SLA** | <50ms loss | BGP + BFD + MPLS FRR | < 50ms |

**BFD (Bidirectional Forwarding Detection)** is a sub-second failure detection protocol
that works alongside OSPF, EIGRP, or BGP:

```ios
! Enable BFD on an interface
interface Gi0/0/1
 bfd interval 300 min_rx 300 multiplier 3  ! Detect failure in 900ms (300ms × 3)

! OSPF uses BFD for immediate failure detection
router ospf 1
 timers throttle spf 50 200 5000  ! SPF computation tuning
```

With BFD, convergence can be < 1 second; without it, default OSPF convergence is 30+ seconds.

---

## Design Patterns for Enterprise Networks

### Hub-and-Spoke (Branch Model)

```text
                  HQ (Core Routers with OSPF)
                 /            |            \
           Branch-A        Branch-B      Branch-C
        (static route     (static route  (static route
         to HQ)            to HQ)         to HQ)
```

- **HQ:** Dynamic routing (OSPF/EIGRP) among core routers
- **Branches:** Static default routes pointing to HQ gateway
- **Advantage:** Simple branch config, no routing protocol overhead
- **Trade-off:** Branch-to-branch traffic must go through HQ (no direct peer routes)

### Mesh Network (Full Redundancy)

```text
     R1 ━━━━ R2
     ┃ ╲    ╱ ┃
     ┃  ╲  ╱  ┃
     R4 ━━━━ R3
```

- All routers run OSPF or EIGRP
- Every router can reach every other router via multiple paths
- Convergence to alternate paths in 1–10 seconds

### Regional Hubs (Partial Mesh)

```text
          Core (OSPF)
          /  |  \
      HUB-A HUB-B HUB-C
       /|\   /|\   /|\
      Branch nodes (static to nearest hub)
```

- Hubs run dynamic routing among themselves
- Branches use static routes to the nearest hub
- Compromise between complexity and redundancy

---

## Cisco Configuration Examples

### Static Routing Only (Branch)

```ios
! Branch office with single uplink to HQ
ip route 0.0.0.0 0.0.0.0 203.0.113.1  ! Default route to ISP/HQ gateway

! Specific route for internal network (if direct link exists)
ip route 10.0.0.0 255.255.0.0 10.0.1.1

! Verify
show ip route static
```

### Dynamic Routing (OSPF)

```ios
router ospf 1
 network 10.0.0.0 0.0.0.255 area 0
 network 192.168.1.0 0.0.0.255 area 0

interface Gi0/0/1
 ip ospf hello-interval 10
 ip ospf dead-interval 40

! Verify
show ip ospf neighbors
show ip ospf database
show ip route ospf
```

### Hybrid: Dynamic + Static

```ios
! Dynamic routing for internal routes
router ospf 1
 network 10.0.0.0 0.0.0.255 area 0

! Static default route to ISP (lower priority than OSPF)
ip route 0.0.0.0 0.0.0.0 203.0.113.1 110  ! AD 110 (same as OSPF); static is backup

! Or use higher AD to make static the true backup
ip route 0.0.0.0 0.0.0.0 203.0.113.1 200  ! AD 200; static is last resort

! Verify
show ip route
show ip route summary
```

### Backup Route (OSPF + Static Failover)

```ios
router ospf 1
 network 10.0.0.0 0.0.0.255 area 0

! If OSPF learns a route to 192.168.0.0/16, it is used (AD 110).
! If OSPF loses the route, the static route (AD 200) takes over.
ip route 192.168.0.0 255.255.0.0 10.0.0.254 200

! Verify: show ip route 192.168.0.0 should show OSPF route first
show ip route 192.168.0.0
```

---

## When to Use Each

### Use Static Routing When

- **Small networks (<10 routers):** Manual route configuration is manageable.

- **Branch offices with single uplink:** No redundancy needed; static default route is
  sufficient.

- **Specific, stable routes:** Exceptional routes that rarely change (e.g., legacy system
  reachable via a specific path).

- **Security is critical:** Routes are not advertised; no routing protocol overhead;
  reduced attack surface.

- **CPU/bandwidth constrained:** Very old routers or extremely low-bandwidth WAN links may
  not support dynamic routing overhead.

### Use Dynamic Routing When

- **Large networks (>20 routers):** Manual route configuration is infeasible.

- **Redundancy required:** Multiple paths must be available for failover.

- **Automatic failover is critical:** Applications cannot tolerate manual intervention
  during outages.

- **Topology changes are frequent:** New routers/links are added regularly.

- **Multi-vendor environment:** BGP is the only choice for inter-AS routing. OSPF is
  standard for intra-AS.

### Use Hybrid Approach When (Most Common)

- **Core is dynamic, edge is static:** Core routers run OSPF/BGP for scalability; branches
  use static routes.

- **Default route is static, internal routes are dynamic:** Everything not explicitly
  known is sent to a default gateway; internal routes are learned.

- **Backup route is static:** Primary route is dynamic; if it fails, a static backup
  activates (higher AD).

---

## Notes

- **Administrative Distance (AD):** When multiple routing protocols offer routes to the same
  destination, AD determines preference. Lower AD wins. Static routes have AD 1 by default
  (highest priority); OSPF is 110; EIGRP is 90. This allows admins to tier routing
  protocols by preference.

- **Floating static routes:** A static route with high AD (e.g., 200) that activates only
  if the primary dynamic route fails is called a "floating static route."

- **Route summarisation:** In large networks, dynamic routing can be combined with manual
  route summarisation to reduce routing table size. See [Route Redistribution](route_redistribution.md).

- **BGP is different:** BGP is a special case — it is primarily used for inter-domain
  routing (between ASes) and can carry hundreds of thousands of routes. Most networks use
  BGP only at the edge (ISP peering, cloud provider connections); internal routing is OSPF
  or EIGRP.
