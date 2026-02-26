# EIGRP Convergence: Standard vs. Tuned vs. BFD

This document compares EIGRP convergence behavior. EIGRP is known for being one
of the fastest IGP protocols due to its Diffusing Update Algorithm (DUAL), but its
initial failure detection still relies on Hello/Hold timers unless BFD is utilized.

---

## 1. Failure Detection Timeline (Neighbor Down)

EIGRP uses "Hello" packets to maintain adjacency and a "Hold Timer" to declare a
neighbor down.

```mermaid
timeline
    title EIGRP Failure Detection
    section Standard (5s/15s)
        T=0s : Link/Neighbor Failure
        T=5s : 1st Hello Missed
        T=10s : 2nd Hello Missed
        T=15s : Hold Timer Expires : Neighbor Down : DUAL Active State Triggered
    section Tuned (1s/3s)
        T=0s : Link/Neighbor Failure
        T=1s : 1st Hello Missed
        T=2s : 2nd Hello Missed
        T=3s : Hold Timer Expires : Neighbor Down : DUAL Active State Triggered
    section EIGRP with BFD
        T=0s : Link/Neighbor Failure
        T=300ms : BFD Packet Miss 1
        T=600ms : BFD Packet Miss 2
        T=900ms : BFD Failure Detected : EIGRP Notified : DUAL Active State Triggered
```

---

## 2. Restoration Timeline (Neighbor Up)

EIGRP restoration involves a 3-way handshake and the exchange of the full topology
table via Update packets.

```mermaid
timeline
    title EIGRP Restoration (Adjacency)
    section Standard EIGRP
        T=0s : Link Restored
        T+1s : Hello Sent/Received (Handshake Init)
        T+2s : Null Update (Sequence Sync)
        T+3s : Topology Table Exchange (Update Packets)
        T+4s : Full Adjacency : DUAL Feasible Successors Calculated
    section EIGRP with BFD
        T=0s : Link Restored
        T+0.5s : BFD Session Up
        T+1s : EIGRP Handshake Init
        T+3s : Full Adjacency : Routes Re-installed
```

---

## 3. Comparison Summary

| Metric | Standard EIGRP | Tuned EIGRP | EIGRP + BFD |
| :--- | :--- | :--- | :--- |
| **Hello / Hold** | 5s / 15s | 1s / 3s | 5s / 15s (Backup) |
| **Detection Time** | ~15 Seconds | ~3 Seconds | < 1 Second |
| **CPU Impact** | Low | Medium-High | Low (Offloaded) |
| **Stability** | High | Moderate | High |
| **Recovery Logic** | DUAL Query | DUAL Query | Immediate DUAL Trigger |

### Key Principles

#### 1. DUAL and the "Active" State

When EIGRP loses a route and has no **Feasible Successor** (backup route) in its
topology table, it goes into "Active" state and sends Queries to neighbors. BFD
speeds up the transition to this state by removing the neighbor immediately.

#### 2. The 1s/3s "Aggressive" Limit

While OSPF can be tuned to sub-second "minimal" hellos, EIGRP typically bottoms
out at 1-second Hellos and a 3-second Hold timer. Going faster than this without
BFD significantly risks "stuck-in-active" (SIA) issues if the CPU is busy.

#### 3. BFD Offloading

BFD is particularly effective for EIGRP because it allows the protocol to maintain
high-stability timers (5/15) while still reacting to physical failures at sub-second
speeds.

---

### Engineering Guidance

- **Use BFD** as the primary detection mechanism for all Core and Distribution links.
- **Tuned Timers (1s/3s)** are acceptable for branch offices or lower-speed links
    where sub-second convergence isn't a requirement.
- **Feasible Successors:** Ensure your design provides EIGRP with feasible successors;
    BFD detects the failure faster, but DUAL needs a backup path to achieve "instant"
    convergence.
