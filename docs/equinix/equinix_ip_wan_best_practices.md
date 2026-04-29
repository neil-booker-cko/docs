# Equinix IP WAN Best Practices

Comprehensive guide to designing, deploying, and operating IP WAN networks using Equinix Fabric
Cloud Router for cloud and datacenter interconnection.

## Core Principles

### 1. Bandwidth Matching

Match provisioned bandwidth to actual usage patterns.

```text
Scenario: Replication between DC and AWS

Expected throughput:
  Peak: 5 Gbps (24-hour average: 2 Gbps)

Decision:
  ✓ Provision 10 Gbps (1.5–2x peak for headroom)
  ✗ Provision 1 Gbps (insufficient for peak)
  ✗ Provision 100 Gbps (expensive, underutilized)
```

### 2. Latency Predictability

Equinix Fabric guarantees consistent latency; public internet does not.

```text
Equinix Fabric:
  Same metro: <1ms (consistent)
  Different metros: Predictable (SJC-LAX: ~15ms)

Public Internet:
  Variable (5–100ms depending on ISP congestion)
  Unpredictable (varies by time of day)
```

**Use case:** Use Fabric for real-time apps (HFT, video), public internet for batch jobs.

### 3. Redundancy Model

Design for single points of failure (SPOF).

```text
Architecture A (SPOF at FCR):
  DC → FCR → Cloud
  Failure of FCR = total outage

Architecture B (No SPOF):
  DC → FCR-A → Cloud
  DC → FCR-B → Cloud
  Or: DC → FCR + Direct AWS Connect (bypass FCR)
```

---

## Design Patterns

## Pattern 1: Single-Cloud Single-DC (Minimal Redundancy)

```text
Topology:
  DC (10 servers)
  ├─ App tier (5 servers)
  └─ DB tier (5 servers)

  AWS (RDS, S3)

  Connectivity: DC ←(1 vConnection)→ FCR ←→ AWS
```

**Bandwidth:** 1 Gbps (sufficient for 10 servers, typical usage 200 Mbps).

**Redundancy:**

- **No redundancy:** Single vConnection failure = full outage
- **Cost:** ~$500–1000/month

**When to use:** Dev/test, non-critical workloads, small organizations.

**Upgrade path:** Add secondary vConnection or secondary FCR for production.

---

## Pattern 2: Multi-Cloud Single-DC (Hub-and-Spoke)

```text
Topology:
  DC (20 servers)

  Connectivity via FCR:
    ├─ AWS (primary databases)
    ├─ Azure (analytics)
    └─ GCP (machine learning)

  Single vConnection → FCR (SJC) → all clouds
```

**Bandwidth:** 10–20 Gbps (multiple clouds, aggregate traffic).

**Redundancy:**

- **Primary:** Single vConnection
- **Backup:** Dual vConnections (active-active) or secondary FCR (active-passive)

**Cost:**

- Single vConnection: ~$5000/month (10 Gbps)
- Dual vConnections: ~$10,000/month

**When to use:** Multi-cloud applications, consolidation onto single FCR.

**Advantages:**

- Single BGP routing table (all clouds via one peer)
- Unified traffic policies (QoS, filtering)

**Disadvantages:**

- FCR becomes single point of failure (mitigated with dual FCR)
- All traffic funnels through one router (bottleneck at scale)

---

## Pattern 3: Multi-DC Multi-Cloud (Full Mesh or Star)

### Mesh Topology (Full redundancy, high complexity)

```text
DC-A (FCR-A)                DC-B (FCR-B)
  ├─ Full mesh iBGP          ├─ Full mesh iBGP
  │  with other DCs          │  with other DCs
  │                          │
  ├─ AWS peering             ├─ AWS peering
  ├─ Azure peering           ├─ Azure peering
  └─ GCP peering             └─ GCP peering
```

**iBGP sessions:**

```text
DC-A ←iBGP→ DC-B
DC-A ←iBGP→ DC-C
DC-B ←iBGP→ DC-C
(Full mesh: 3 DCs = 3 iBGP sessions)
```

**Bandwidth:** 10–50 Gbps per DC (varies by DC size).

**Redundancy:**

- Full mesh: any single DC failure doesn't impact others
- No single point of failure (except cloud provider connection)

**Cost:** Multiple FCR instances (one per DC) + multiple vConnections = expensive.

**BGP complexity:** O(n²) iBGP sessions, hard to debug.

**When to use:** Enterprise, geographic DR, multiple datacenters (3+).

### Star Topology (Simplified, single hub)

```text
Primary DC (FCR-Hub)
  ├─ iBGP with DC-B
  ├─ iBGP with DC-C
  ├─ AWS, Azure, GCP peering

DC-B ←iBGP→ FCR-Hub
DC-C ←iBGP→ FCR-Hub

(DC-B ↔ DC-C traffic via DCHub)
```

**iBGP sessions:**

```text
FCR-Hub ← iBGP → DC-B
FCR-Hub ← iBGP → DC-C
(Star: 3 DCs = 2 iBGP sessions)
```

**Advantages:**

- Simpler BGP (linear sessions, not exponential)
- Centralized routing control
- Cheaper than full mesh

**Disadvantages:**

- Hub (Primary DC) is SPOF for inter-DC traffic
- DC-B ↔ DC-C traffic detours through hub (higher latency)

**When to use:** Simplified multi-DC, primary DC is reliable.

---

## Bandwidth Planning

### Method 1: Utilization-Based

```text
Step 1: Measure current utilization
  Peak outbound to cloud: 2 Gbps
  Peak inbound from cloud: 1.5 Gbps
  Aggregate: 3.5 Gbps peak

Step 2: Apply headroom factor (1.5x – 2x)
  With 1.5x headroom: 3.5 × 1.5 = 5.25 Gbps
  Provision: 10 Gbps (next standard increment)

Step 3: Plan for growth
  Current: 3.5 Gbps
  Projected (2 years): +50% = 5.25 Gbps
  Provision: 10 Gbps (supports growth without upgrade)
```

### Method 2: Per-Application-Based

```text
Applications and bandwidth requirements:

Database replication: 2 Gbps peak
  (How many concurrent snapshots?)

Video streaming (to CDN): 1 Gbps sustained
  (Codec, bitrate, concurrent streams?)

Backup/archive: 500 Mbps off-peak
  (Size of backups, frequency?)

Web app traffic: 500 Mbps peak
  (Concurrent users, session bandwidth?)

Aggregate: 4 Gbps peak
Provision: 10 Gbps (with headroom)
```

### Method 3: Per-Location-Based

```text
Multi-cloud applications across metros:

App serving US-East (AWS N. Virginia): 2 Gbps
App serving EU (Azure W. Europe): 1.5 Gbps
Analytics (GCP US-Central): 1 Gbps
DB replication (multi-region): 1.5 Gbps

Aggregate: 6 Gbps peak
Provision: 10 Gbps per metro (if multi-metro FCR)
```

### Right-Sizing Strategy

```text
Start small, scale on demand:

  Month 1: Provision 1 Gbps vConnection
           (cost: $500–600/month)

  Month 3–6: Monitor utilization
             If trending >70%, upgrade to 10 Gbps
             (upgrade takes 15–30 min, no downtime)

  Month 12–24: Plan for growth
               If aggregate >15 Gbps, scale to dual vConnections
```

---

## Path Selection and Traffic Steering

### BGP Metrics (Precedence)

```text

1. Locally originated routes (highest preference)
1. iBGP routes (lower distance than eBGP)
1. eBGP routes
1. AS path length (shorter preferred)
1. Local preference (Cisco/FortiGate, higher = preferred)
1. Weight (Cisco only, higher = preferred)
1. MED/Metric (multi-exit discriminator, lower = preferred)
```

### Example: Prefer Primary Cloud via Path Length

```text
Network topology:
  DC ←→ FCR (AS 65001) ←→ AWS (AS 16509)
                    ↓
                  Azure (AS 8075)

BGP path advertisement:

AWS route: 172.31.0.0/16
  AS path: 16509 → FCR → DC (selected as best)

Azure route: 192.168.0.0/16
  AS path: 8075 → FCR → DC (selected as best)

Both have same hop count (3 hops), so first-received wins.
To prefer AWS: Add local-preference 200 to AWS neighbor.
```

### Advanced: Communities-Based Steering

```text
FCR advertises routes with communities:
  AWS routes: community 65001:1
  Azure routes: community 65001:2

DC router policy:
  If community 65001:1 (AWS), set local-pref 200
  If community 65001:2 (Azure), set local-pref 100

Result: AWS preferred unless FCR unreachable
```

---

## Convergence and Failover

### BGP Timers and Convergence

```text
Timer Setting          Convergence Time    Use Case
─────────────────────────────────────────────────────
Hello 10s, Hold 30s    ~30–40 seconds      Stable, non-critical
Hello 3s, Hold 9s      ~10–15 seconds      Balanced
Hello 1s, Hold 3s      ~3–5 seconds        Real-time apps (HFT)
```

### Convergence Timeline Example

```text
T=0s: vConnection fails (link down, or BGP peer crashes)
T=1s: Cisco router detects BGP hello timeout (after hello interval)
T=3s: Cisco router misses 3 hellos, triggers holdtime decay
T=9s: BGP holdtime expires, neighbor declared down
T=10s: Routes from neighbor withdraw
T=11s: Traffic shifts to backup path (if available)
T=12s: Full convergence

Total outage: 10–12 seconds (with 3s/9s timers)
```

### Fast Convergence Optimization

If sub-3-second failover required (e.g., HFT trading):

```text
Option A: BFD (Bidirectional Forwarding Detection)

  - Detects link failures in sub-100ms
  - Triggers BGP session reset
  - Convergence: <1 second

Option B: Aggressive BGP timers (1s/3s)

  - Standard BGP, no extra protocol
  - Convergence: ~3–5 seconds
  - Higher CPU overhead on routers

Option C: Dual active vConnections

  - Traffic load-balances across both
  - Failure of one = load shift (50% → 100% on other)
  - No route withdrawal needed (both paths always active)
```

---

## Monitoring and Operations

### Key Metrics to Track

| Metric | Target | Action if Exceeded |
| --- | --- | --- |
| **vConnection Utilization** | <70% | Plan upgrade |
| **BGP Neighbor Uptime** | >99.9% | Investigate stability |
| **Route Convergence Time** | <15s | Tune timers or add BFD |
| **Packet Loss** | <0.01% | Check vConnection health |
| **RTT (Latency)** | Baseline +10% | Investigate congestion |

### Monitoring Tools

#### Equinix Console

```text
Equinix Console → Fabric → Virtual Connections
Monitor:

  - vConnection status (ACTIVE, ALERTING, DOWN)
  - Bandwidth utilization (real-time graph)
  - BGP neighbor status
  - Error counts (CRC, underrun, overrun)
```

#### Router-Based Monitoring

**Cisco:**

```text
show bgp ipv4 unicast summary
show bgp ipv4 unicast neighbors 10.255.1.2
show interface GigabitEthernet0/0/1  (vConnection interface)
show ip bgp rib
```

**FortiGate:**

```text
get router bgp summary
get router bgp neighbors 10.255.1.2
diagnose router bgp paths 172.31.0.0/16  (trace best path)
```

#### External Monitoring (Grafana, Prometheus)

```text
Export metrics:

  - BGP neighbor state (up/down)
  - Route count (detected changes)
  - BGP session duration (uptime)
  - Route convergence time (measured via test routes)
```

---

## Cost Optimization

### vConnection Bandwidth Upgrade/Downgrade

```text
Scenario: Traffic increased from 5 Gbps to 8 Gbps

Option A: Upgrade vConnection 10 → 100 Gbps
  Cost: +$5000/month
  Time: 15–30 minutes (no downtime)

Option B: Add second vConnection (10 Gbps)
  Cost: +$5000/month (same as upgrade)
  Benefit: Active-active redundancy

Recommendation: Choose Option B (redundancy + same cost)
```

### Bandwidth Sharing Across Applications

```text
Scenario: 10 Gbps vConnection, multiple applications

Poor utilization pattern:
  App-1: 4 Gbps (database)
  App-2: 6 Gbps (video)
  Total: 10 Gbps (no headroom)

Problem: Single spike in App-2 blocks App-1

Solution: QoS rate limiting
  App-1: Reserve 5 Gbps (allows burst to 10)
  App-2: Limit to 7 Gbps (allows priority to App-1)

Result: No starvation, both apps get fair share
```

### Off-Peak Usage Optimization

```text
Use case: Backups run 10 PM – 6 AM only

Cost optimization:
  Provision: 5 Gbps (sufficient for daytime + some backup)
  Schedule backups: Stagger (not all at once)
  Result: 5 Gbps vConnection handles both

Alternative: Separate 1 Gbps vConnection for backups
  Cost: Cheaper ($500/month vs. $2500/month upgrade)
  If vConnection #1 fails: Backups queue (acceptable)
```

---

## Troubleshooting Checklist

### BGP Session Down

1. **Check vConnection status**

    ```text
    Equinix Console: vConnection state = ACTIVE?
    If DOWN: Wait for Equinix to restore, or open support ticket
    ```

1. **Check layer 2 link**

    ```text
    Cisco: show interface [port]
    Status: up/up?

    If down: Check physical cabling, cross-connect status
    ```

1. **Check BGP configuration**

    ```text
    Cisco: show bgp ipv4 unicast neighbors 10.255.1.2
    Expected: Remote AS 65001, local AS 65000

    If mismatch: Verify ASN config
    ```

1. **Check BGP timers**

    ```text
    BGP hello received? Check last message time
    If >9s gap: May hit holdtime, trigger neighbor down
    ```

1. **Check firewall/access**

    ```text
    BGP uses port 179 (TCP)
    Cisco: show access-list
    FortiGate: show firewall policy

    Ensure BGP traffic allowed to/from 10.255.1.2
    ```

### Routes Not Received

1. **Check if neighbor is Established**

    ```text
    If neighbor DOWN: Fix BGP session first
    ```

1. **Check what FCR is advertising**

    ```text
    Cisco: show bgp ipv4 unicast neighbors 10.255.1.2 advertised-routes

    If no routes shown: FCR has no routes to advertise (check FCR)
    ```

1. **Check route filters**

    ```text
    Cisco: show bgp ipv4 unicast neighbors 10.255.1.2 received-routes

    If routes shown but not in BGP table: Check route-maps, prefix-lists
    ```

1. **Check cloud provider connectivity**

    ```text
    If expecting AWS routes but none received:

      - Verify AWS Direct Connect is ACTIVE
      - Check AWS BGP session with FCR
      - Verify AWS is advertising VPC CIDRs
    ```

### High Latency / Jitter

1. **Check vConnection utilization**

    ```text
    Equinix Console: Monitor bandwidth utilization

    If >85% utilized: Congestion likely, upgrade needed
    ```

1. **Check for packet loss**

    ```text
    Cisco: ping -c 100 [cloud-destination]

    If loss >0.1%: Investigate congestion or link issues
    ```

1. **Measure baseline latency**

    ```text
    Cisco: ping [cloud-destination]

    Baseline latency should be consistent (±5% variation OK)
    If jumping 10–20ms: May indicate congestion or routing changes
    ```

---

## Disaster Recovery

### Site Failure Scenario

```text
Primary DC fails (power loss, natural disaster)

Before DR:
  All traffic via Primary DC → FCR → Cloud
  Secondary DC: Idle or limited capacity

After Primary failure:
  BGP routes from Primary DC withdraw
  Traffic cannot reach cloud (no routing path)

RTO (Recovery Time Objective): Manual failover (hours to days)
RPO (Recovery Point Objective): Minutes (last backup)
```

### Improved DR Design

```text
Primary DC (FCR-A)          Secondary DC (FCR-B)
  Active applications        Hot standby
  BGP AS 65000              BGP AS 65000

  ├─ iBGP with Secondary    ←─iBGP─→

  FCR-A ←iBGP→ FCR-B

  Both advertise same routes to AWS

Failure scenario:
  Primary DC fails
  Secondary takes over (all routes already advertised)
  RTO: <15 seconds (BGP convergence)
  RPO: Near-zero (hot standby)
```

### Backup Connectivity Pattern

```text
Primary: FCR in primary metro
Backup: Direct AWS DX connection (bypass FCR)

Normal:
  Traffic via FCR (lower cost)

FCR failure:
  Traffic diverts to Direct DX (higher cost, but works)

Cost optimization:
  Use backup connection rarely (pay for standby only)
```

---

## Multi-Cloud Best Practices

### Route Deduplication

```text
Problem: Same route advertised by multiple clouds

Example:
  AWS advertises: 10.0.0.0/8 (customer VPC + shared services)
  Azure advertises: 10.0.0.0/8 (via peering agreement)

BGP selects one (first received, or by local-pref)
Other route ignored

Solution:
  Use longest-prefix-match
  AWS: 10.0.0.0/8 (VPC)
  Azure: 10.128.0.0/10 (don't overlap)

  Or: Use communities to disambiguate
  AWS routes tagged: 65001:1
  Azure routes tagged: 65001:2
```

### Load Balancing Across Clouds

```text
Scenario: App can run on AWS or Azure

Traffic distribution policy:
  70% to AWS (primary, cheaper)
  30% to Azure (secondary, for failover test)

Implementation: Local preference
  AWS neighbor: local-preference 200
  Azure neighbor: local-preference 100

BGP selects 70% of traffic via AWS path, 30% via Azure
```

---

## Best Practices Checklist

| Category | Practice | Benefit |
| --- | --- | --- |
| **Design** | Size bandwidth for 1.5–2x peak | Handles growth, prevents congestion |
| **Redundancy** | Dual vConnections or dual FCR | Survives single failure |
| **BGP** | Set timers 3/9 or 10/30 | Balanced convergence (10–30s) |
| **Monitoring** | Track BGP uptime, vConnection util | Early warning of issues |
| **Cost** | Right-size bandwidth, upgrade gradually | Avoid waste, manage budget |
| **Operations** | Document topology, test failover | Faster troubleshooting and DR |
| **Multi-cloud** | Use communities for traffic control | Fine-grained path selection |
| **DR** | Active-passive or active-active standby | Sub-minute RTO, near-zero RPO |

---

## Summary

- **Design for redundancy:** Dual vConnections or multi-metro FCR
- **Right-size bandwidth:** 1.5–2x peak utilization, plan for growth
- **Use BGP timers appropriately:** 3/9 for balanced, 10/30 for stability
- **Monitor continuously:** vConnection status, BGP uptime, latency trends
- **Optimize costs:** Upgrade on demand, use backup connectivity for DR
- **Document everything:** Topology, policies, runbooks for team

---

## Next Steps

- [Equinix FCR Concepts](equinix_fabric_concepts.md) — Deep dive on Fabric architecture
- [FCR Architecture & Deployment](equinix_fcr_architecture.md) — Deployment patterns
- [Cisco Integration](cisco_to_equinix_fcr.md) — Cisco configuration examples
- [FortiGate Integration](fortigate_to_equinix_fcr.md) — FortiGate configuration examples
