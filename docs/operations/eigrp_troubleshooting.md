# EIGRP Troubleshooting

Common EIGRP routing, neighbor discovery, convergence, and redistribution issues with
diagnostic commands and remediation steps. Applies to Cisco IOS-XE and FortiGate deployments.

---

## Quick Diagnosis

| Symptom | Likely Cause | First Check |
| --- | --- | --- |
| **No neighbors** | Interface down; passive interface; AS mismatch; MTU mismatch | Verify interface up; check passive config; confirm AS number |
| **Neighbor flapping** (up/down repeatedly) | MTU mismatch; high latency; authentication mismatch | Check frame size; test latency; verify K-values |
| **Routes not learning** | Neighbor not forming; network not advertised; AS mismatch | Verify neighbor up; check network statements; confirm AS |
| **Slow convergence** (>5s) | High hello/hold timers; no BFD; WAN latency high | Reduce timers; enable BFD; check link quality |
| **Unequal cost load balancing (UCMP) not working** | Variance not set; metrics not different; unequal costs | Check variance setting; verify route metrics differ |
| **Routes disappearing (flapping)** | Topology instability; metric changes; restart-time timer | Check for duplicate route sources; verify metrics stable |
| **Stuck in Active (SIA)** | Long convergence time; no response from neighbors | Increase active timer; reduce query scope; enable BFD |
| **Redistribution loops** | Same routes from multiple sources; no filtering | Use route tags; filter redistributed routes |

---

## Neighbor Discovery Issues

### Symptom: "No EIGRP Neighbors"

#### Check 1: Interface up and in routing process

```ios
! Cisco
show ip eigrp interfaces
! Should show all interfaces in EIGRP (either passive or active)

show ip int brief
! Verify interface IP and status is "up"
```

#### Check 2: Verify neighbor interface

From router with no neighbors, check if interface can ping neighbor:

```ios
! Ping neighbor's IP on shared subnet
ping <neighbor-ip>
```

If unreachable: layer 1/2 issue (cable, port, VLAN, subnet mismatch).

#### Check 3: Verify routing process running

```ios
! Cisco
show ip protocols
! Should show "EIGRP <AS-number> Protocol" section

! FortiGate
get router info routing-table details
```

If EIGRP not listed: routing process may not be started or configured incorrectly.

#### Check 4: Check AS number matches

```ios
! Cisco
show run | include eigrp
! Example: "router eigrp 100"

! Both routers must use same AS number (e.g., AS 100)
```

#### Check 5: Check passive interface setting

```ios
! Cisco
show ip eigrp interfaces passive
! If interface listed here, it won't send EIGRP packets (no neighbors possible)

! Remove passive:
router eigrp 100
 no passive-interface GigabitEthernet0/0/0
!
```

#### Check 6: Check MTU mismatch

MTU mismatch causes neighbor to form momentarily then flap continuously.

```ios
! Cisco
show ip mtu <interface>
show ip eigrp interfaces detail <interface>
! Look for "MTU mismatch: <local> vs <neighbor>"

! If mismatch, change MTU to match:
interface GigabitEthernet0/0/0
 mtu 1500
!
```

### Symptom: "Neighbor Up Then Immediately Flaps"

#### Check 1: K-values mismatch

EIGRP uses K-values (metric weights: K1–K5) for metric calculation. Routers with different
K-values cannot form stable neighbor relationship.

```ios
! Cisco
show ip eigrp parameters
! Example: K1=1 K2=0 K3=1 K4=0 K5=0 (default)

! Must match on both routers; if different, change to match
router eigrp 100
 metric weights 0 1 0 1 0 0  ! Set K1=1, K3=1, others 0
!
```

#### Check 2: MTU mismatch (see above)

#### Check 3: Latency or packet loss on link

High latency (>500 ms) or packet loss causes hello timeout:

```ios
! From neighbor router, check latency
ping <neighbor-ip> timeout 10
! Should be <50 ms for LAN; <500 ms for WAN acceptable
```

If latency high: Check link quality, WAN provider issues, or enable BFD for faster detection.

---

## Route Learning Issues

### Symptom: "Routes Not Appearing in Routing Table"

#### Check 1: Verify network statement

EIGRP only advertises networks explicitly listed in network statements:

```ios
! Cisco
show run | include network
! Example output:
!   network 10.0.0.0 0.0.0.255  (classless, /24 network)
!   network 172.16.0.0          (classful, entire 172.16.0.0/12)

! Routes not listed here won't be advertised
```

Verify network statement matches the subnet to be advertised. Common mistake: using classful
network when subnet is different.

#### Check 2: Verify route is learned from neighbor

```ios
! Cisco
show ip eigrp topology <destination>
! Should show the route with metric and neighbor origin

! If not present: neighbor not advertising or route not in neighbor's table
```

#### Check 3: Check for distribute-list filtering

```ios
! Cisco
show ip eigrp filters
! May show inbound/outbound filters blocking the route

! If filtered, remove or adjust:
router eigrp 100
 no distribute-list <list> in <interface>
!
```

#### Check 4: Verify neighbor actually has the route

SSH to neighbor and check:

```ios
! On neighbor router
show ip route eigrp | include <destination>
! If not present on neighbor: neighbor isn't advertising because it doesn't have route either
```

### Symptom: "Routes Show In Topology But Not Routing Table"

**Cause:** Route is in EIGRP topology (feasible routes) but not installed in routing table due to
metric or administrative distance issue.

```ios
! Cisco
show ip eigrp topology <destination>
! Shows all feasible routes

! The first (best metric) is installed in routing table
! Others are backup (feasible successors)

show ip route <destination>
! Shows only the installed route
```

If topology shows route but routing table doesn't: check administrative distance (AD) — another
routing source (static, OSPF) may have lower AD and be installed instead.

---

## Convergence and Stability Issues

### Symptom: "Routes Flapping" (Appearing/Disappearing)

**Causes:**

1. Neighbor flapping (see Neighbor Flapping above)

1. Metric changing constantly due to load-based or delay-based metric

1. Multiple equal-cost paths with different neighbors failing/recovering

**Diagnosis:**

```ios
! Cisco
debug eigrp packets hello  ! Very verbose; use carefully
debug eigrp events        ! Shows route additions/removals

! Monitor for repeated changes in metric or neighbor state
```

**Remediation:**

1. Enable BFD (detects link failure faster, stabilizes routing)

1. Use delay-based metric only (disable load-based): set K2=0

1. Ensure all equal-cost paths stable (check neighbor flapping)

### Symptom: "Convergence Slow" (>5 seconds)

#### Check 1: Hello and hold timers

Default EIGRP timers: hello 5 seconds, hold 15 seconds. For faster convergence, reduce timers:

```ios
! Cisco
interface GigabitEthernet0/0/0
 ip hello-interval eigrp 100 1     ! 1 second hello
 ip hold-interval eigrp 100 3      ! 3 second hold
!
```

#### Check 2: Enable BFD

BFD (Bidirectional Forwarding Detection) detects link failure sub-second:

```ios
! Cisco
interface GigabitEthernet0/0/0
 bfd interval 300 min_rx 300 multiplier 3  ! 300 ms failure detection
!

router eigrp 100
 bfd all-interfaces
!
```

#### Check 3: Check query timeout (Active timer)

If routers stuck in Active state (waiting for query responses), convergence hangs. Default is
3 minutes; can be reduced:

```ios
! Cisco
router eigrp 100
 timers active-time 1  ! 1 minute max active time (instead of 3)
!
```

**Note:** Reducing active-time may cause SIA (Stuck In Active) if network large or slow. Only
reduce if confident in network size.

---

## Metric and Cost Issues

### Symptom: "UCMP (Unequal Cost Load Balancing) Not Working"

EIGRP supports load balancing across routes with different costs using **variance** multiplier.

#### Check 1: Verify variance set

```ios
! Cisco
show ip eigrp parameters
! Look for "Variance: X"  (default 1 = equal cost only)

! To enable UCMP with 2:1 variance:
router eigrp 100
 variance 2  ! Routes with cost up to 2x best cost are used
!
```

#### Check 2: Check route metrics

```ios
! Cisco
show ip eigrp topology <destination>
! Look for metric of each route and whether it's within variance

! Example:
!   Path 1: metric 256000 (successor)
!   Path 2: metric 384000 (feasible successor)
!   Variance = 2: 384000 <= (256000 * 2 = 512000)? YES → Load balanced
```

#### Check 3: Verify feasible successors exist

UCMP requires feasible successors (backup routes with lower AD). If only successor exists, no
load balancing possible.

---

## Redistribution Issues

### Symptom: "Redistributed Routes Not Appearing"

#### Check 1: Redistribution command present

```ios
! Cisco
show run | include redistribute
! Should show: "redistribute ospf 1 metric ..." or similar
```

#### Check 2: Source has the route

If redistributing OSPF, verify OSPF router has the route:

```ios
! On router running OSPF
show ip route ospf | include <destination>
! If not present: OSPF doesn't have route to redistribute
```

#### Check 3: Metric specified

```ios
! Cisco
router eigrp 100
 redistribute ospf 1 metric 10000 100 255 1 1500
!
! Metric format: bandwidth delay reliability load MTU
! If metric too high (e.g., 100000 bandwidth), route may not be preferred
```

#### Check 4: Filtering applied

```ios
! Check for route-maps or distribute-lists blocking redistribution
show ip eigrp filters
show route-map | include redistribute
```

### Symptom: "Routing Loops from Redistribution"

**Cause:** Same route advertised from multiple sources (e.g., OSPF and static route both
redistributed).

**Prevention:**

1. Use route tags to identify source of redistribution

1. Filter redistributed routes at redistribution point

```ios
! Example: Mark all OSPF routes with tag 100
router eigrp 100
 redistribute ospf 1 metric 10000 100 255 1 1500 route-map TAG-OSPF
!

route-map TAG-OSPF permit 10
 set tag 100
!
```

Then, when redistributing EIGRP into OSPF, exclude tag 100:

```ios
router ospf 1
 redistribute eigrp 100 metric-type 2 route-map NO-EIGRP-TAG100
!

route-map NO-EIGRP-TAG100 deny 10
 match tag 100
!

route-map NO-EIGRP-TAG100 permit 20
!
```

---

## Advanced Diagnostics

### Stuck in Active (SIA) — Long Convergence

**Symptom:** Route in "active" state for >3 minutes; neighbors not responding to queries.

```ios
! Cisco
debug eigrp packets query reply
! Watch for routers not responding to query
```

**Common causes:**

1. Slow WAN link (queries timeout before response)

1. Router overloaded (CPU high, can't process queries)

1. MTU mismatch (large query packet fragments, lost)

**Remediation:**

1. Reduce query scope using **stub** configuration (distribute-only router doesn't query):

```ios
! On spoke routers (shouldn't originate queries):
router eigrp 100
 eigrp stub receive-only  ! Only receives routes, doesn't originate or query
!
```

1. Or, increase active timer:

```ios
router eigrp 100
 timers active-time 5  ! 5 minute timeout instead of 3
!
```

1. Or, enable BFD to detect failures faster (avoids prolonged Active state).

---

## Best Practices for EIGRP

| Practice | Reason |
| --- | --- |
| **Use summarization** | Reduces number of routes; limits scope of queries |
| **Enable BFD on all links** | Sub-second convergence; reduces reliance on timers |
| **Set K-values explicitly** | Avoid accidental mismatch; ensures metric consistency |
| **Use passive-interface default** | Prevent neighbor formation on unnecessary interfaces |
| **Set hello/hold timers appropriately** | Balance between detection speed and stability |
| **Implement route filtering** | Reduce topology size; prevent accidental loops |
| **Use distribute-lists or prefix-lists** | More efficient than route-maps for filtering |
| **Monitor EIGRP topology size** | Large topologies (100+ routes) may cause SIA issues |

---

## Notes / Gotchas

- **Classful vs Classless:** Network statements can be classful (just IP) or classless (IP
  netmask). Mixing may cause confusion; use classless format consistently.

- **K-Value Change Triggers Recompute:** Changing K-values causes all metric recalculations and
  potential brief routing disruption. Change during maintenance window.

- **Variance 1 (Default):** Only equal-cost routes load-balanced. If variance not explicitly
  set, UCMP won't work.

- **EIGRP Metric Formula:** metric = (K1 × bandwidth + K3 × delay) / (K2 × load + 256 - reliability)
  with default K-values simplifies to (bandwidth + delay). Don't memorize; use show commands.

- **Neighbor Password (MD5) Mismatch:** If authentication enabled, password must match. Syntax
  error is silent; neighbor just won't form.

---

## See Also

- [EIGRP vs OSPF Comparison](../theory/ospf_vs_eigrp.md)

- [EIGRP vs BFD Comparison](../theory/eigrp_bfd_comparison.md)

- [IGP Comparison](../theory/igp_comparison.md)

- [BGP Troubleshooting](bgp_troubleshooting.md)

- [OSPF Troubleshooting](ospf_troubleshooting.md)

- [BFD Best Practices](bfd_best_practices.md)
