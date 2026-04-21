# EIGRP vs OSPF vs RIP

A comparison of the three most common Interior Gateway Protocols (IGPs) for IPv4/IPv6
enterprise networks. IS-IS is omitted here — it is covered separately and is primarily
used in service provider environments.

---

## Protocol Overview

| Property | RIP v2 | EIGRP | OSPF v2 |
| --- | --- | --- | --- |
| **Type** | Distance-vector | Advanced distance-vector (DUAL) | Link-state |
| **Standard** | RFC 2453 | RFC 7868 (formerly Cisco proprietary) | RFC 2328 |
| **Algorithm** | Bellman-Ford | DUAL (Diffusing Update Algorithm) | Dijkstra (SPF) |
| **Metric** | Hop count (max 15) | Composite (bandwidth + delay by default) | Cost (based on bandwidth) |
| **Convergence** | Slow (180s invalid timer) | Fast (feasible successors instant) | Fast (SPF on topology change) |
| **Scalability** | Small networks only | Medium–large | Large |
| **IP Protocol** | UDP/520 | IP protocol 88 | IP protocol 89 |
| **Multicast** | `224.0.0.9` | `224.0.0.10` | `224.0.0.5` / `224.0.0.6` |
| **IPv6 support** | RIPng (RFC 2080) | Named mode / `ipv6 eigrp` | OSPFv3 (RFC 5340) |
| **Authentication** | MD5 (v2), none (v1) | MD5 / SHA-256 (named mode) | MD5 / SHA (RFC 5709) |
| **VLSM / CIDR** | Yes (v2) | Yes | Yes |
| **Administrative Distance** | `120` | `90` internal / `170` external | `110` |

---

## Metric Comparison

### RIP

Hop count only. Maximum 15 hops; 16 = unreachable. Does not consider bandwidth,
delay, or link quality. A slow 64 Kbps serial link and a 10 Gbps LAN count equally
if they are the same number of hops.

### OSPF

Cost = reference bandwidth / interface bandwidth. Cisco default reference: 100 Mbps.

```text
Cost = 10^8 / interface_bandwidth_bps
```

| Interface | Default Cost |
| --- | --- |
| 10 Mbps Ethernet | 10 |
| 100 Mbps FastEthernet | 1 |
| 1 Gbps GigabitEthernet | 1 |
| 10 Gbps | 1 |

GigabitEthernet and above all default to cost `1` unless the reference bandwidth is
raised (`auto-cost reference-bandwidth 10000` for 10 Gbps). **Always configure
`auto-cost reference-bandwidth` to match the fastest link in the network.**

### EIGRP

Composite metric from K-values applied to bandwidth and delay (default K1=1, K3=1,
K2=K4=K5=0):

```text

Metric = 256 × (10^7 / min_bandwidth_kbps + sum_of_delays_in_tens_of_microseconds)
```

| Interface | Default Delay | Default Bandwidth |
| --- | --- | --- |
| Serial (T1) | 20,000 µs | 1,544 Kbps |
| FastEthernet | 100 µs | 100,000 Kbps |
| GigabitEthernet | 10 µs | 1,000,000 Kbps |

EIGRP considers the **minimum bandwidth** and **cumulative delay** along the entire
path, making it significantly more topology-aware than RIP.

---

## Convergence

### RIP

Convergence is governed by timers:

| Timer | Default | Purpose |
| --- | --- | --- |
| Update | 30s | Periodic full table broadcast |
| Invalid | 180s | Route marked metric 16 if no update |
| Hold-down | 180s | Suppress new routes after invalidation |
| Flush | 240s | Route removed from table |

A network failure can take **3–4 minutes** to fully converge. Triggered updates
(RFC 2453) accelerate partial convergence but the hold-down timer still applies.

### EIGRP

If a **Feasible Successor** exists (a pre-computed loop-free backup path), failover
is instantaneous — the backup is already in the topology table and requires no
additional queries. If no feasible successor exists, EIGRP enters **Active** state
and queries all neighbours; convergence time depends on query scope.

To prevent excessive query propagation, use **route summarisation** at distribution
layer boundaries to limit the Active state to the local area.

### OSPF

OSPF convergence time = detection time + SPF delay + LSA flooding time.

| Component | Typical value | Tuning |
| --- | --- | --- |
| Hello / Dead interval | 10s / 40s (broadcast) | `ip ospf hello-interval` |
| SPF initial delay | 50 ms (IOS default) | `timers throttle spf` |
| SPF hold time | 200 ms | `timers throttle spf` |
| LSA throttle | 50 ms initial | `timers throttle lsa` |
| BFD | < 1s sub-second | `bfd interval` |

With BFD and tuned SPF throttle timers, OSPF can converge in under one second.

---

## Scalability and Design

### RIP

- Maximum 15 hops limits deployment to small, flat networks.
- Full routing table sent every 30 seconds regardless of changes — bandwidth
  inefficient on large tables.

- No concept of areas or summarisation hierarchy.
- Suitable for: small branch offices, lab environments, legacy migrations.

### EIGRP

- Scales well in hub-and-spoke and hierarchical enterprise topologies.
- Partial updates — only changes are sent, not the full table.
- Supports manual and automatic summarisation at any router.
- Query boundary problem: poorly summarised networks can generate excessive Active
  state queries that propagate network-wide ("stuck in active" / SIA).

- Suitable for: Cisco-only enterprise networks, WAN hub-and-spoke, campus.

### OSPF

- Hierarchical area design limits LSA flooding scope. Backbone (area 0) interconnects
  all areas via ABRs.

- Stub, Totally Stubby, and NSSA area types reduce LSA database size in remote areas.
- Full topology database per area — every router in an area has identical LSDB.
- DR/BDR election reduces flooding on multi-access (Ethernet) segments.
- Suitable for: multi-vendor enterprise, large networks, service provider edge,
  any network requiring vendor-agnostic IGP.

---

## Feature Comparison

| Feature | RIP v2 | EIGRP | OSPF v2 |
| --- | --- | --- | --- |
| Unequal-cost load balancing | No | Yes (`variance`) | No |
| Equal-cost load balancing | No | Yes | Yes (`maximum-paths`) |
| Route summarisation | Classful boundaries only | Any boundary (manual) | Area boundary (ABR) |
| Passive interface | Yes | Yes | Yes |
| Default route injection | `default-information originate` | `ip summary-address eigrp 0.0.0.0/0` | `default-information originate` |
| Redistribution complexity | Simple | Simple | Moderate (seed metric required) |
| Fast hello / BFD | No | Yes | Yes |
| Multi-topology routing | No | No | Yes (OSPFv3) |
| Graceful restart | No | Yes (RFC 4811) | Yes (RFC 3623) |

---

## When to Use Each

### RIP

Use only when simplicity is paramount and the network is small (≤ 15 hops). In
practice, OSPF is a better choice even for small networks and should be the default
for new deployments.

### EIGRP

Good choice for **Cisco-only** environments, especially hub-and-spoke WAN topologies
where unequal-cost load balancing (`variance`) provides traffic engineering
flexibility. Named mode (IOS 15.0.1M+) adds SHA-256 authentication and per-AF
configuration. The main constraint is vendor lock-in — EIGRP requires Cisco (or
compatible) on every router in the domain.

### OSPF

The default choice for most enterprise and campus networks. Vendor-neutral, scales
well with proper area design, and has broad tool/monitoring support. OSPFv3 covers
IPv6 with the same operational model. The additional complexity of area design is
offset by predictable convergence and extensive industry familiarity.

---

## Notes

- **Redistribution between EIGRP and OSPF** requires a seed metric in both
  directions. EIGRP redistributed into OSPF defaults to E2 (external type 2) at
  cost 20. OSPF redistributed into EIGRP requires an explicit `default-metric`
  or per-route metric.

- **EIGRP named mode** is the recommended configuration style on IOS-XE. It
  consolidates address-family (IPv4/IPv6) and topology configuration under a single
  `router eigrp <name>` stanza and enables SHA-256 authentication.

- **OSPF `network` vs `ip ospf area`**: the interface-level command
  (`ip ospf <pid> area <area>`) is more explicit and is the recommended style on
  modern IOS-XE and NX-OS.

- See individual protocol pages for full packet formats:
  [OSPF](../routing/ospf.md), [EIGRP](../routing/eigrp.md), [RIP](../routing/rip.md).
