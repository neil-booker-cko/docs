# HSRP, VRRP, and GLBP — Gateway Redundancy Protocols

HSRP (Hot Standby Router Protocol), VRRP (Virtual Router Redundancy Protocol), and GLBP
(Gateway Load Balancing Protocol) solve the same fundamental problem: a host's single
configured default gateway can fail. All three present a **virtual IP (VIP)** to which
hosts send traffic. The difference lies in how redundancy is handled: HSRP and VRRP use
an **active/standby model** (one router forwards, others monitor); GLBP uses **active/
active load balancing** (multiple routers forward simultaneously). This guide compares
all three and clarifies when to use each.

For detailed protocol packet formats, see [HSRP Packet Format](../packets/hsrp.md) and
[VRRP Packet Format](../packets/vrrp.md). For configuration details, see
[HSRP and VRRP Configuration](../cisco/cisco_hsrp_vrrp.md) and
[GLBP Configuration](../cisco/cisco_glbp_config.md).

---

## At a Glance

| Property | HSRP v2 | VRRP v3 | GLBP v2 |
| --- | --- | --- | --- |
| **Standard** | Cisco proprietary | RFC 5798 (open) | Cisco proprietary |
| **Redundancy model** | Active/Standby (1 active, 1–N standby) | Master/Backup (1 master, 1–N backup) | Active/Active (up to 4 active AVGs) |
| **Load balancing** | No (single active) | No (single master) | Yes (multiple AVGs, 1 AVF per subnet) |
| **Transport** | UDP `1985`, multicast `224.0.0.102` | IP protocol `112`, multicast `224.0.0.18` | UDP `3222`, multicast `224.0.0.102` |
| **Hello interval** | 3 seconds | 1 second | 3 seconds |
| **Failover time** | ~10 seconds (default) | ~3 seconds (default) | ~10 seconds |
| **Priority** | 0–255, default 100 | 1–254, default 100 | 0–255, default 100 |
| **Preemption default** | Disabled | Enabled | Disabled |
| **Virtual MAC count** | 1 per group | 1 per group | 4 (one per AVG) |
| **Max load-sharing routers** | N/A (1 active) | N/A (1 master) | 4 (AVGs) |
| **Tracking support** | Yes (object tracking) | Yes (object tracking) | Yes (weighted tracking) |
| **Bandwidth utilization** | Efficient (periodic hellos) | Efficient (periodic advertisements) | Higher (hello + weighting advertisements) |
| **Complexity** | Low | Low | High (requires tuning for optimal load balance) |
| **IPv6 support** | HSRPv2 (separate config) | VRRPv3 (native dual-stack) | Cisco proprietary extension |
| **Third-party support** | Cisco only | All vendors (Fortinet, Juniper, Arista, etc.) | Cisco only |

---

## How Each Protocol Works

### HSRP: Active/Standby Gateway Redundancy

HSRP routers negotiate to elect one **Active** router and one **Standby** router. The
Active router owns the virtual IP and responds to ARP requests. Standby routers monitor
the Active and take over if it fails. Only the Active and Standby roles matter; additional
routers sit in a **Listen** state, monitoring but not participating unless both Active and
Standby fail.

**Election:** Highest priority wins. If priorities are equal, highest real IP address wins.
By default, preemption is **disabled** — a lower-priority router that becomes Active
stays Active even after the preferred (higher-priority) router recovers.

```mermaid
graph LR
    subgraph Normal
        R1a["R1 (Priority 110)<br/>Active<br/>Owns VIP 10.0.1.1"] -->|Forwards traffic| VIP1["Virtual IP<br/>10.0.1.1"]
        R2a["R2 (Priority 100)<br/>Standby<br/>Monitors R1"] -->|Monitors| VIP1
        R3a["R3 (Priority 90)<br/>Listen"] -.->|Monitors| VIP1
    end
    subgraph Failover
        R1b["R1 FAILED"] -->|Cannot reach| VIP2["Virtual IP<br/>10.0.1.1"]
        R2b["R2 (Priority 100)<br/>Now Active<br/>Takes VIP"] -->|Forwards traffic| VIP2
        R3b["R3 (Priority 90)<br/>Standby"] -->|Monitors| VIP2
    end
```text

### VRRP: Master/Backup Gateway Redundancy

VRRP is similar to HSRP but standardised (RFC 5798). The **Master** router is elected
and forwards traffic. **Backup** routers monitor the Master and take over if the Master
fails. VRRP **preemption is enabled by default** — a higher-priority router will always
become Master.

**Owner concept:** A router whose real IP is the VIP has an implicit priority of 255 and
is always Master. This is unique to VRRP; HSRP requires the VIP to be separate from real
IPs.

```mermaid
graph LR
    subgraph Normal
        R1a["R1 (Priority 110)<br/>Master<br/>Owns VIP 10.0.1.1"] -->|Forwards| VIP1
        R2a["R2 (Priority 100)<br/>Backup"] -->|Monitors| VIP1
    end
    subgraph PreemptRecovery["Preemption on Recovery"]
        R1b["R1 recovers<br/>Priority 110 > 100"] -->|Becomes Master<br/>Preempts R2| VIP2
        R2b["R2 is demoted to Backup"] -->|Monitors| VIP2
    end
```text

### GLBP: Active/Active Load Balancing

GLBP is unique: instead of one active and one standby, GLBP supports up to **4 Active
Virtual Gateways (AVGs)** — each serving a subset of hosts. A **Virtual Forwarder (AVF)**
is elected for each AVG, and the AVF forwards traffic to that gateway. If an AVF fails,
another router becomes the new AVF for that gateway.

**Load balancing:** Hosts are assigned to different gateways via ARP responses. When a
host ARPs for the VIP, the GLBP group returns **different virtual MACs** depending on
which gateway the host should use. This distributes traffic across up to 4 routers.

```mermaid
graph LR
    subgraph GLBP["GLBP Active/Active Load Balancing (4 routers)"]
        AVG1["R1<br/>AVG 1 (Primary)<br/>Forwards for VIP"] -->|Responds: MAC-1| Host1["Host 1<br/>Learns MAC-1<br/>Routes via R1"]
        AVG2["R2<br/>AVG 2<br/>Forwards for VIP"] -->|Responds: MAC-2| Host2["Host 2<br/>Learns MAC-2<br/>Routes via R2"]
        AVG3["R3<br/>AVG 3<br/>Forwards for VIP"] -->|Responds: MAC-3| Host3["Host 3<br/>Learns MAC-3<br/>Routes via R3"]
        AVG4["R4<br/>AVG 4<br/>Forwards for VIP"] -->|Responds: MAC-4| Host4["Host 4<br/>Learns MAC-4<br/>Routes via R4"]
    end
```text

**Key difference:** GLBP requires router **weighting** — administrators assign relative
weights to each router to control how many hosts are directed to each. If R1 has weight
100 and R2 has weight 50, R1 receives 2/3 of ARP requests.

---

## Redundancy Models: Active/Standby vs Active/Active

### Active/Standby (HSRP, VRRP)

- **Simplicity:** One router forwards; others are backups. Debugging is straightforward.
- **Utilization:** Standby routers are idle, wasting capacity. In a 2-router pair, 50% of
  gateway capacity is unused.
- **Convergence:** Depends on hello/failover timers (typically 10–30 seconds).
- **Scalability:** Any number of standby routers, but only one active.

**Design:** Standard for campus and enterprise edge gateways where a single router has
sufficient capacity.

### Active/Active (GLBP)

- **Efficiency:** All routers forward simultaneously. 100% of capacity is utilized in a 4-
  router group.
- **Complexity:** Weighting must be tuned to balance load. Uneven weights result in
  unbalanced load distribution.
- **Convergence:** More complex — failure of one AVG requires reweighting, and hosts
  using that gateway's MAC may experience brief loss.
- **Scalability:** Up to 4 active AVGs (GLBP limit). Beyond 4 routers, some routers must
  be standby.

**Design:** Used when multiple gateway routers exist and load-sharing is desired (e.g.,
distribution layer in a spine-leaf fabric).

---

## Load Balancing Comparison

### HSRP / VRRP: Single Active

Traffic from all hosts is forwarded by a single Active/Master router. The standby router
receives no traffic.

```text
Host 1 → VIP (10.0.1.1) → ARP Resolution → Virtual MAC (00:00:5E:00:01:XX)
Host 2 → VIP (10.0.1.1) → ARP Resolution → Virtual MAC (00:00:5E:00:01:XX)
Host 3 → VIP (10.0.1.1) → ARP Resolution → Virtual MAC (00:00:5E:00:01:XX)

All traffic flows through the single Active router.
```text

**Load balancing workaround:** Run **multiple HSRP/VRRP groups**, each with different
active routers:

```text
Group 1: R1 Active, R2 Standby  (for VLAN 10, VIP 10.0.1.1)
Group 2: R2 Active, R1 Standby  (for VLAN 20, VIP 10.0.2.1)
```text

This requires per-VLAN configuration and careful tuning. Not practical for hundreds of
VLANs.

### GLBP: Multiple Active Forwarders

Each AVG owns a unique virtual MAC. Hosts are distributed across AVGs based on ARP
responses.

```text
Host 1 → VIP (10.0.1.1) → ARP → MAC-1 (R1's virtual MAC) → Traffic via R1
Host 2 → VIP (10.0.1.1) → ARP → MAC-2 (R2's virtual MAC) → Traffic via R2
Host 3 → VIP (10.0.1.1) → ARP → MAC-3 (R3's virtual MAC) → Traffic via R3
Host 4 → VIP (10.0.1.1) → ARP → MAC-4 (R4's virtual MAC) → Traffic via R4
```text

GLBP uses **Round-Robin or Weighted** ARP responses to distribute hosts:

- **Round-Robin:** Host 1 gets MAC-1, Host 2 gets MAC-2, Host 3 gets MAC-3, Host 4 gets
  MAC-4, Host 5 gets MAC-1 again.
- **Weighted:** If R1 has weight 50 and R2 has weight 50, 50% of ARPs are answered with
  MAC-1, 50% with MAC-2.

---

## Failure Scenarios and Recovery

### HSRP Failure

```text
T=0s: Active (R1) fails
T=3-10s: Hold timer expires on Standby (R2)
T=10s: R2 becomes Active, sends gratuitous ARP
T=11s: Hosts update ARP cache with new MAC for VIP
```text

**Result:** ~10 seconds of traffic loss (default timers).

### VRRP Failure

```text
T=0s: Master (R1) fails
T=3s: Master_Down timer expires on Backup (R2)
T=3s: R2 becomes Master, sends VRRP Advertisement
T=4s: Hosts update ARP caches
```text

**Result:** ~3 seconds of traffic loss (faster than HSRP due to default timers).

### GLBP Failure (Single AVF)

```text
T=0s: AVF for AVG-1 (R1) fails
T=3-10s: Hold timer expires on other routers
T=10s: Next router becomes new AVF for AVG-1
       Hosts using MAC-1 see brief loss
       Hosts using MAC-2, MAC-3, MAC-4 unaffected
```text

**Result:** Only hosts using the failed AVG's MAC see loss. Other hosts continue through
other AVGs. More graceful degradation than HSRP/VRRP.

---

## Feature Comparison Table

| Feature | HSRP | VRRP | GLBP |
| --- | --- | --- | --- |
| **Load balancing** | No (single active) | No (single master) | Yes (up to 4 active) |
| **Preemption** | Off by default; manual | On by default | Off by default |
| **IPv4 support** | Yes | Yes | Yes |
| **IPv6 support** | HSRPv2 only | VRRPv3 (native) | Limited |
| **Object tracking** | Yes | Yes | Yes (weighted) |
| **Metric switching** | Yes (with tracking) | Yes (with tracking) | Yes (weighted priority) |
| **Scalability** | Many standby routers | Many backup routers | Max 4 AVGs |
| **Configuration complexity** | Low | Low | High (weighting required) |
| **Convergence to standby** | ~10s | ~3s | ~10s |
| **Vendor support** | Cisco | All vendors | Cisco |
| **Use case** | Cisco-only, redundant gateways | Multi-vendor, standard gateways | Cisco-only, load-sharing gateways |

---

## When to Use Each

### Use HSRP When

- **Cisco-only environment** and existing investment in HSRP expertise.
- **Simple redundancy:** Two routers, one active, one standby. No need for load balancing.
- **Legacy infrastructure:** Existing HSRP deployments are stable; migration cost outweighs
  benefits.

**Example:** A regional branch office with two Cisco 4461 routers acting as a gateway pair.
Traffic volume is low; a single active router is sufficient.

### Use VRRP When

- **Multi-vendor environment** (Cisco, Fortinet, Juniper, Arista gateways).
- **Standards compliance required** — RFC 5798 is the industry standard.
- **IPv6 redundancy** needed — VRRP v3 natively supports dual-stack.
- **Faster failover** desired (default 3 seconds vs HSRP's 10).
- **Greenfield deployment** — choosing a gateway redundancy protocol from scratch.

**Example:** A data center with Cisco and Fortinet firewall pairs. Both support VRRP; a
single protocol manages redundancy across vendors.

### Use GLBP When

- **Cisco-only environment** and **load-sharing is required.**
- **Multiple gateway routers** (3–4) exist and capacity should be fully utilized.
- **No per-VLAN configuration burden:** GLBP distributes load automatically via ARP
  responses, avoiding complex multi-group setups.
- **Graceful degradation** is important — failure of one gateway doesn't impact all
  traffic.

**Example:** A distribution layer in a campus network with 4 distribution switches
acting as gateways. GLBP distributes hosts across all 4, utilising full capacity.
If one switch fails, only hosts assigned to that switch are affected.

---

## Practical Considerations and Limitations

### Single-Active Limitations (HSRP/VRRP)

If two gateways are configured with HSRP/VRRP, one is always idle:

```text
R1 (Active) — 1 Gbps utilised, 0% available
R2 (Standby) — 0 Gbps utilised, 1 Gbps wasted
```text

To use both routers, admins must configure **multiple groups** (one per VLAN). This is
operationally messy for large networks.

### GLBP Weighting Complexity

GLBP's effectiveness depends on correct weighting. Misconfigured weights lead to uneven
load distribution:

```text
R1 weight 50 (but has 1 Gbps capacity)
R2 weight 50 (but has 10 Gbps capacity)

Result: Both routers receive equal traffic despite R2's higher capacity.
Fix: Set R1 weight 50, R2 weight 500 to match capacity ratios.
```text

### BFD Integration

Both HSRP/VRRP and GLBP can integrate with BFD (Bidirectional Forwarding Detection) to
detect failures in < 300ms, independent of protocol timers. This is recommended for
sub-second convergence.

```ios
! Enable BFD on an interface
interface Gi0/0/1
 bfd interval 300 min_rx 300 multiplier 3
```text

---

## Cisco Configuration Examples

### HSRP (Simple Active/Standby)

```ios
interface Gi0/0/1
 ip address 10.0.1.2 255.255.255.0

 ! Configure HSRP group 1
 standby 1 ip 10.0.1.1
 standby 1 priority 110  ! R1 is primary
 standby 1 preempt       ! Enable preemption
 standby 1 preempt delay minimum 30  ! Wait 30s before taking over

 ! Verify
 ! show standby brief
```text

### VRRP (Simple Master/Backup)

```ios
interface Gi0/0/1
 ip address 10.0.1.2 255.255.255.0

 ! Configure VRRP group 1
 vrrp 1 ip 10.0.1.1
 vrrp 1 priority 110
 vrrp 1 preempt  ! Enabled by default, but explicit for clarity
 vrrp 1 timers advertise 1

 ! Verify
 ! show vrrp brief
```text

### GLBP (Active/Active Load Balancing)

```ios
interface Gi0/0/1
 ip address 10.0.1.2 255.255.255.0

 ! Configure GLBP group 1
 glbp 1 ip 10.0.1.1
 glbp 1 priority 110  ! R1 is primary AVG
 glbp 1 preempt       ! Enable preemption

 ! Set weighting (R1 is 1 Gbps, others are 10 Gbps)
 glbp 1 weighting 50  ! R1 gets 50/500 = 10% of traffic

 ! Other routers:
 ! glbp 1 weighting 450  ! Each of R2, R3, R4 gets 90%

 ! Verify
 ! show glbp brief
 ! show glbp 1 forwarders
```text

---

## Notes

- **HSRP vs VRRP in data centres:** Modern data centre fabrics (spine-leaf) have largely
  moved away from HSRP/VRRP in favour of **anycast gateways** on leaf switches, where
  every leaf presents the same gateway MAC/IP. See [Data Centre Topologies](dc_topologies.md).

- **Tracking and failover triggers:** All three protocols support object tracking to detect
  upstream failures and trigger failover even if the gateway interface is still up. This
  is critical in hub-and-spoke designs where a gateway's uplink can fail independent of
  the gateway interface.

- **Multiple groups for load balancing:** If GLBP is not available (non-Cisco environment),
  admins can simulate active/active by configuring multiple VRRP groups with different
  masters. This is complex and not recommended for more than 2–3 groups.

- **Virtual MAC addresses are deterministic:** Both HSRP and VRRP generate the virtual MAC
  from the group number. This means the MAC is predictable and does not change, which is
  why hosts cache it in ARP. GLBP generates 4 MACs (one per AVG) from the same group number.

- **RFC references:** HSRP is Cisco proprietary (no RFC). VRRP is RFC 5798 (v3) / RFC 3768
  (v2). GLBP is Cisco proprietary (no RFC).
