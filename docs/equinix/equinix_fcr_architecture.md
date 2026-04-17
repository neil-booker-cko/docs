# Equinix FCR Architecture and Deployment Patterns

Complete reference for designing and deploying Fabric Cloud Router for cloud and datacenter
interconnection.

## FCR Deployment Models

### Single-Metro Hub-and-Spoke (Cloud Interconnect)

Primary use case: **Multi-cloud with centralized routing**.

```text
AWS Region (us-east-1)
        |
    AWS DX Connect
        |
    ┌───▼────┐
    │ FCR-A  │  (SJC metro)
    └───┬────┘
        |
    BGP peering
        |
    ┌───┴─────┬──────────┐
    |         |          |
  Azure    GCP      On-Prem DC
  (East)  (us-c1)   (via DX)
```text

**Configuration:**
- Single FCR instance in primary metro
- Multiple vConnections (one per cloud/DC)
- All routes converge at FCR
- Single BGP routing table

**Advantages:**
- Simplest topology
- Single point of management
- Unified traffic steering policies
- Lowest cost (one FCR)

**Disadvantages:**
- Single point of failure (FCR down = all clouds unreachable)
- All traffic traverses single FCR (potential bottleneck at scale)
- Metro failure = complete outage (no failover)

**When to use:** Small deployments, dev/test, single metro presence.

**High-availability variant:**
Add secondary FCR in same metro for redundancy (active-active BGP).

---

### Multi-Metro Hub-and-Spoke (Geographic Redundancy)

Primary use case: **Multi-cloud with geographic failover**.

```text
Primary Metro (SJC)        Secondary Metro (LAX)
┌─────────────┐             ┌─────────────┐
│  FCR-A      │──BGP iBGP──│  FCR-B      │
└─────┬───────┘             └─────┬───────┘
      |                            |
    BGP eBGP                    BGP eBGP
      |                            |
    AWS                          AWS
```text

**Configuration:**
- FCR-A (primary metro), FCR-B (secondary metro)
- iBGP session between FCR-A and FCR-B
- Both FCRs peer with AWS (separate vConnections)
- Both FCRs peer with on-prem DC

**Advantages:**
- Survives metro failure (FCR-A down → traffic via FCR-B)
- Load balancing across metros (BGP tie-breaking)
- Higher resilience

**Disadvantages:**
- Higher cost (two FCR instances)
- More complex BGP (dual peerings per destination)
- Cross-metro latency (10–50ms depending on distance)

**When to use:** Production deployments, SLA > 99.9%, multi-region cloud presence.

---

### Full Mesh (Datacenter Interconnect)

Primary use case: **DC-to-DC replication, no cloud**.

```text
DC-A (FCR-A)       ────iBGP────       DC-B (FCR-B)
   |                                      |
   ├─ Appservers                         ├─ Appservers
   ├─ Databases                          ├─ Databases
   └─ Backup targets                     └─ Backup targets

Traffic: DC-A ↔ DC-B directly (no intermediary)
```text

**Configuration:**
- FCR per datacenter (FCR-A at DC-A, FCR-B at DC-B)
- iBGP between FCR-A and FCR-B
- Each DC advertises its local subnets via FCR
- Optional: secondary link for failover

**Advantages:**
- Traffic locality (DC-A apps talk directly to DC-A data)
- Low latency (no hub routing)
- Scales to many datacenters (partial mesh also works)

**Disadvantages:**
- BGP complexity increases with number of DCs (n DCs = n FCRs)
- Each DC pair needs BGP session (O(n²) relationships at scale)
- More operational overhead

**When to use:** Multiple datacenters, DR/replication, on-prem only (no cloud).

---

### Hybrid (Cloud + DC Interconnect)

Primary use case: **Gradual cloud migration, hybrid cloud**.

```text
Primary DC (FCR-A)
      |
    BGP eBGP
      |
    AWS/Azure (via vConnection)
      |
    BGP eBGP
      |
On-Prem DC or Branch (direct or secondary FCR)
```text

**Configuration:**
- Primary DC routes to cloud via FCR-A
- Secondary DC connects directly to primary DC (IPsec/WAN)
- Optional: secondary FCR for DC-B failover to cloud

**Advantages:**
- Preserves existing DC infrastructure
- Gradual migration to cloud (start with one FCR)
- On-prem + cloud coexistence

**Disadvantages:**
- Mixed routing (some via FCR, some via WAN)
- Operational complexity (manage both FCR and traditional WAN)

**When to use:** Migrations, hybrid deployments.

---

## vConnection Redundancy Patterns

### Single vConnection (No Redundancy)

```text
DC → (single vConnection) → FCR → AWS
Risk: vConnection failure = AWS unreachable
```text

**When acceptable:** Dev/test, non-critical workloads.

### Dual vConnection (Active-Active)

```text
DC → (vConnection #1) → FCR → AWS
  └─ (vConnection #2) ─┘
```text

**Configuration:**
- Two separate vConnections from DC to FCR
- BGP announces same route via both vConnections
- Traffic load-balances across both

**When to use:** Production, requires failover time < 3 seconds.

### Dual vConnection with Preferred Path

```text
DC → (vConnection #1: primary) ──→ FCR → AWS
  └─ (vConnection #2: backup) ──┘
```text

**Configuration:**
- BGP local preference or AS prepend to prefer vConnection #1
- vConnection #2 takes over only on vConnection #1 failure

**When to use:** Cost optimization (vConnection #2 unused in normal operation).

---

## FCR Sizing and Performance

### Throughput Tiers

| FCR Size | Typical Throughput | vConnections | Use Case |
| --- | --- | --- | --- |
| **Small** | 10Gbps aggregate | 4–6 | Single cloud, dev/test |
| **Medium** | 50Gbps aggregate | 8–12 | Multi-cloud, single metro |
| **Large** | 100Gbps+ | 16+ | Enterprise, multi-metro |

### Factors Affecting Throughput

- **vConnection bandwidth:** Each vConnection has provisioned BW (1–400Gbps)
- **FCR processing:** BGP updates, traffic steering policies
- **Connection count:** More vConnections = more BGP state to manage
- **Route count:** Thousands of routes = higher CPU/memory

### Scaling Strategies

**At vConnection level:**
```text
1 FCR × 4 vConnections @ 10Gbps each = 40Gbps total
Scaling: Add 5th vConnection → 50Gbps
```text

**At FCR level:**
```text
1 FCR @ 50Gbps limit reached
Solution: Add 2nd FCR in same/different metro
```text

**At route level:**
```text
Default: FCR advertises/receives ~1000 routes
At scale: Use route aggregation or path filtering
```text

---

## BGP Configuration Patterns

### Simple Hub-and-Spoke (One ASN)

```text
Your network: AS 65000
FCR: AS 64512 (shared Equinix ASN)
AWS: AS 16509
Azure: AS 8075

eBGP peering:
  Your router ↔ FCR (AS 65000 ↔ 64512)
  AWS ↔ FCR (AS 16509 ↔ 64512)
  Azure ↔ FCR (AS 8075 ↔ 64512)
```text

**Simple but less flexible.**

### Multi-Metro with Private ASN

```text
Your network: AS 65000
FCR-A (primary): AS 65001
FCR-B (secondary): AS 65002
AWS: AS 16509

iBGP:
  Your router ↔ FCR-A (AS 65000 ↔ 65001, iBGP)
  Your router ↔ FCR-B (AS 65000 ↔ 65002, iBGP)
  FCR-A ↔ FCR-B (AS 65001 ↔ 65002, eBGP or iBGP confederation)

eBGP:
  AWS ↔ FCR-A (AS 16509 ↔ 65001)
  AWS ↔ FCR-B (AS 16509 ↔ 65002)
```text

**More complex but allows fine-grained traffic steering.**

---

## Multi-Cloud BGP Advertisement Example

### Scenario: 3 Clouds, 1 FCR

```text
Your DC advertises: 10.0.0.0/8 (local subnets)
AWS advertises: 172.31.0.0/16 (AWS VPCs)
Azure advertises: 192.168.0.0/16 (Azure VNets)
GCP advertises: 10.128.0.0/9 (GCP subnets)

FCR routing table:
  10.0.0.0/8 → Your DC (direct)
  172.31.0.0/16 → AWS (via vConnection)
  192.168.0.0/16 → Azure (via vConnection)
  10.128.0.0/9 → GCP (via vConnection)
```text

**Result:** All four networks can ping each other through FCR routing.

---

## Failover and Convergence

### Scenario: vConnection Failure

```text
T=0s:   vConnection drops (AWS unreachable via primary path)
T=0.5s: BGP detects failure (via failed keepalive)
T=1s:   FCR updates routing (routes withdraw)
T=2s:   Your router detects BGP status change
T=3s:   Traffic reroutes (if secondary path available)
T=3.5s: Full convergence
```text

**Key: BGP timers control convergence time.**
- Aggressive timers (1s hello, 3s holdtime) = faster failover (~3s)
- Conservative timers (3s hello, 9s holdtime) = slower (~10s) but more stable

### Recommended FCR Timers

```text
BGP Hello: 3 seconds
BGP Holdtime: 9 seconds
Convergence: ~10 seconds on vConnection failure
```text

For faster failover (< 3s required):
```text
BGP Hello: 1 second
BGP Holdtime: 3 seconds
Convergence: ~3–5 seconds
(Higher CPU overhead; only for critical paths)
```text

---

## Equinix Metal + FCR Integration

### Compute-to-Cloud via Fabric

```text
Equinix Metal server
        |
    Layer 2 (automatic)
        |
    Equinix Fabric gateway
        |
    FCR (BGP routing)
        |
    AWS/Azure/GCP
```text

**Advantages:**
- Metal server has direct path to cloud (< 1ms latency, same metro)
- Scalable (Metal ↔ FCR is Layer 2, metal can add more servers)
- No BGP configuration needed on Metal itself (Layer 2 abstraction)

**Configuration:**
- Request vLAN on Metal (provided by Equinix)
- vLAN connects to FCR automatically
- Configure BGP on FCR for cloud advertised routes
- Metal servers use FCR as gateway (via DHCP or static config)

---

## Disaster Recovery Patterns

### Pattern 1: Active-Passive Failover

```text
Primary DC (active)      Secondary DC (passive)
      |                         |
    FCR-A ←──BGP────────→ FCR-B
      |                         |
    AWS                       AWS
```text

**Normal operation:** FCR-A sends traffic, FCR-B monitors.
**On FCR-A failure:** Manual or automated failover to FCR-B.

### Pattern 2: Active-Active Load Balancing

```text
Primary DC      Secondary DC
   |                  |
FCR-A ←─BGP eBGP─→ FCR-B
   |                  |
AWS (announces same route via both FCRs)
```text

**Normal operation:** Traffic load-balances 50-50 across both FCRs.
**On FCR-A failure:** All traffic via FCR-B (no manual intervention).

---

## Cost Optimization

### Bandwidth vs. Latency Trade-off

```text
Scenario: Cloud app 100km away

Option A: 10Gbps FCR connection
  Cost: ~$5k/month
  Latency: 2–5ms
  Use case: Streaming, real-time apps

Option B: 1Gbps FCR connection
  Cost: ~$500/month
  Latency: Same 2–5ms
  Use case: Batch, analytics (if 1Gbps sufficient)
```text

**Recommendation:** Start with 1Gbps, upgrade on demand.

### Single vs. Dual vConnections

```text
Option A: Single vConnection (active-only)
  Cost: ~$500/month (1Gbps)
  Availability: 99% (vConnection failures unprotected)
  Use case: Dev, non-critical

Option B: Dual vConnections (active-active)
  Cost: ~$1k/month (2× 1Gbps)
  Availability: 99.9%+ (one can fail)
  Use case: Production

Recommendation: 99% availability is NOT "5 nines"; use dual for production.
```text

---

## Best Practices

| Practice | Reason |
| --- | --- |
| **Deploy secondary FCR in different metro** | Survives datacenter failure |
| **Use dual vConnections per cloud** | Single vConnection failure = brief outage |
| **Set BGP timers for <5s convergence** | Minimize traffic loss during failover |
| **Document BGP topology** | Multi-path scenarios need clear mapping |
| **Use BGP communities for traffic steering** | Avoid complex AS prepending |
| **Monitor vConnection utilization** | Upgrade before hitting limits (80%+ = congestion) |
| **Test failover quarterly** | Ensure secondary paths work under load |
| **Use aggregate routes** | Reduces BGP updates and memory usage |

---

## Summary

- **Single-metro hub-and-spoke:** Simplest, lowest cost, single point of failure
- **Multi-metro hub-and-spoke:** Resilient, load-balancing, higher cost
- **Full mesh:** Good for DC-only, scales with operational complexity
- **Hybrid cloud + DC:** Gradual migration strategy
- **vConnection redundancy:** Critical for production (dual vConnections)
- **BGP tuning:** Control failover convergence (3–10 seconds)
- **Equinix Metal integration:** Direct compute-to-cloud with Layer 2 abstraction

---

## Next Steps

- [Cisco to Equinix FCR](cisco_to_equinix_fcr.md) — Cisco router integration
- [FortiGate to Equinix FCR](fortigate_to_equinix_fcr.md) — FortiGate integration
- [Equinix FCR Setup & Provisioning](equinix_fcr_setup.md) — API and provisioning guide
