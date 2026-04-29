# Equinix Cloud-to-Cloud Interconnection Guide

Complete reference for connecting cloud providers directly via Equinix Fabric Cloud Router,
enabling private, high-performance inter-cloud communication.

## Overview

### Cloud-to-Cloud Scenarios

Cloud-to-cloud interconnection via Equinix FCR eliminates the public internet for
inter-cloud communication:

```text
Traditional (Public Internet):
  AWS (US-East)
        |
    Internet backbone (unpredictable latency, public routing)
        |
  Azure (US-West)

Equinix Fabric (Private Interconnect):
  AWS (US-East)
        |
    Equinix FCR (SJC)
    BGP routing / private links
        |
  Azure (US-West)

Benefits: <5ms latency, zero bandwidth cost, predictable performance
```

---

## Core Concepts

### Why Cloud-to-Cloud via Equinix?

| Aspect | Internet Path | Equinix FCR |
| --- | --- | --- |
| **Latency** | 30–100ms (variable) | 1–50ms (predictable) |
| **Data Cost** | $0.02–0.04/GB egress | $0 inter-cloud cost* |
| **Privacy** | Public internet path | Private dedicated link |
| **Control** | ISP-managed | Customer-managed BGP |
| **Performance** | Variable (congestion) | Consistent SLA |
| **Setup Time** | Hours (just BGP) | Hours (vConnections) |

*Note: You pay vConnection bandwidth cost, not per-GB data transfer.

### Multi-Cloud Architecture Pattern

```text
┌──────────────┐         ┌──────────────┐
│    AWS       │         │    Azure     │
│  VPC1 (App)  │         │  VNet (DB)   │
│  172.31.0/16 │         │  192.168.0/16│
└───────┬──────┘         └──────┬───────┘
        │                       │
    DX Connect              ExpressRoute
        │                       │
     eBGP (16509)           eBGP (8075)
        │                       │
        └────── Equinix FCR ────┘
              (AS 65001)
              BGP Hub
```

**Routes advertised:**

- AWS advertises: 172.31.0.0/16 → FCR → Azure
- Azure advertises: 192.168.0.0/16 → FCR → AWS

**Result:** AWS app connects directly to Azure database via FCR.

---

## Deployment Models

### Model 1: Single FCR (Simple, Single Metro)

```text
         Equinix FCR
        (SJC Metro)
       /    |    \
      /     |     \
    AWS   Azure   GCP
   (16509)(8075) (15169)
```

**Configuration:**

- One FCR instance in primary metro (e.g., SJC)
- Direct connections to AWS, Azure, GCP in same metro
- All inter-cloud traffic routes through FCR

**Advantages:**

- Simplest topology
- Lowest cost (one FCR, 3 vConnections)
- Single BGP routing table
- Easy to manage

**Disadvantages:**

- Single point of failure (FCR down = all clouds disconnected)
- Single metro means latency for out-of-region clouds
- Limited geographic redundancy

**Use case:** Dev/test multi-cloud, non-critical workloads, single-region deployments.

### Model 2: Dual FCR (Redundant)

```text
Primary Metro (SJC)      Secondary Metro (LAX)
    FCR-A                    FCR-B
   /  |  \                  /  |  \
  /   |   \                /   |   \
AWS Azure GCP          AWS Azure GCP
```

**Configuration:**

- FCR-A in primary metro (SJC)
- FCR-B in secondary metro (LAX)
- iBGP session between FCR-A and FCR-B
- Each cloud peers with both FCRs

**Advantages:**

- Survives single FCR failure (traffic reroutes to FCR-B)
- Geographic redundancy (failover between metros)
- Load balancing possible (split traffic across metros)

**Disadvantages:**

- Higher cost (two FCR instances, 6 vConnections)
- More complex BGP (dual peerings per cloud)
- Cross-metro latency (10–50ms between metros)

**Use case:** Production multi-cloud, SLA > 99.9%, geographic redundancy required.

### Model 3: Multi-Region Cloud-to-Cloud

```text
AWS US-East         Azure EU-West        GCP AP-South
  |                    |                     |
Direct Connect     ExpressRoute         Cloud Interconnect
  |                    |                     |
  └──── Equinix FCR ───┴────── iBGP ────────┘
       (SJC Metro)      Cloud-to-Cloud BGP peering
```

**Configuration:**

- One or more FCRs in central location
- Each cloud region connects via DX/ExpressRoute/Interconnect
- Inter-cloud communication routed through FCR
- Optional: Multi-metro FCR for failover

**Advantages:**

- Global multi-cloud connectivity
- Consistent path for all inter-cloud traffic
- Unified BGP policies across clouds

**Disadvantages:**

- All traffic traverses central FCR (potential bottleneck)
- Increased latency for geographically distant clouds
- Complex BGP (many routes from multiple regions)

**Use case:** Global applications, multi-region failover, centralized routing policy.

---

## Design Patterns

### Pattern 1: Active-Active Multi-Cloud Load Balancing

Distribute traffic equally across multiple clouds based on application workload.

```text
Application Layer (Client)
        |
  (DNS load balancing)
        |
    ┌───┴───┬───────┐
    |       |       |
  AWS     Azure   GCP
(App-1) (App-2) (App-3)

All apps reachable via FCR with equal priority
```

**BGP Configuration:**

- All clouds advertise same prefix with same local preference
- BGP selects one as best path (first-received or IGP metric)
- Alternative: Use equal-cost multipath (ECMP) if available

**Use case:** Distribute workload across clouds for cost optimization, load balancing.

### Pattern 2: Primary-Secondary Failover

One cloud is primary; other is standby for failover.

```text
Primary (AWS)
  |
  ├─ Local Preference 200
  |
FCR BGP
  |
  ├─ Local Preference 100
  |
Secondary (Azure)
```

**BGP Configuration:**

- AWS routes: local-preference 200 (preferred)
- Azure routes: local-preference 100 (backup only)
- On AWS failure: Routes withdraw, traffic shifts to Azure

**Use case:** Cloud migration (old cloud primary, new cloud secondary), disaster recovery.

### Pattern 3: Application-Specific Routing

Different apps route to different clouds based on policy.

```text
Database workload → Azure (SQL Server)
  |
  └─ Route-map: destination match, set next-hop Azure vConnection

Analytics workload → GCP (BigQuery)
  |
  └─ Route-map: destination match, set next-hop GCP vConnection

Cache/Session → AWS (ElastiCache)
  |
  └─ Route-map: destination match, set next-hop AWS vConnection
```

**BGP Configuration:**

- Use BGP communities or route-maps to tag routes by cloud
- Local preference, weight, or MED to steer traffic by application

**Use case:** Multi-cloud architecture where each cloud specializes in specific workloads.

### Pattern 4: Cost-Optimized Hybrid (Internet + FCR)

Use FCR for latency-sensitive traffic; internet for others.

```text
High-bandwidth, low-latency (DB replication)
  → Equinix FCR (expensive, ~$5–10k/month per 10Gbps)

Low-latency, variable (APIs, user requests)
  → Public Internet (cheaper, already exists)

Batch, archival (backups, logs)
  → Public Internet (lowest cost)
```

**Configuration:**

- Size FCR vConnection based on critical workload only
- Less-critical traffic uses existing internet connectivity
- Use BGP communities or route filtering to control which traffic uses FCR

**Use case:** Cost-conscious deployments, gradual FCR adoption.

---

## Cloud-to-Cloud BGP Configuration

### AWS ↔ Azure via FCR

#### Prerequisites

- AWS Direct Connect (DX) connection to Equinix
- Azure ExpressRoute (ER) connection to Equinix
- Equinix FCR instance in same metro as both DX/ER

#### BGP Setup

```text
Topology:
  AWS VPC (10.0.0.0/16)
      |
    DX ASN 16509
      |
    Equinix FCR (ASN 65001)
      |
    ER ASN 8075
      |
  Azure VNet (192.168.0.0/16)
```

**AWS Side (BGP session with DX):**

- Advertises: 10.0.0.0/16 (VPC CIDR)
- Receives: Routes from FCR (including Azure VNet)
- BGP session: AWS DX router (16509) ↔ Equinix FCR (65001)

**Azure Side (BGP session with ER):**

- Advertises: 192.168.0.0/16 (VNet CIDR)
- Receives: Routes from FCR (including AWS VPC)
- BGP session: Azure ER router (8075) ↔ Equinix FCR (65001)

**Equinix FCR (BGP hub):**

- Receives 10.0.0.0/16 from AWS, advertises to Azure
- Receives 192.168.0.0/16 from Azure, advertises to AWS

#### Verification

```text
AWS side:
  Route table should show: 192.168.0.0/16 via DX → Equinix FCR

Azure side:
  Route table should show: 10.0.0.0/16 via ER → Equinix FCR

Connectivity test:
  AWS EC2 → ping Azure VM (192.168.1.10)
  Should work with ~5–15ms latency (same metro)
```

### AWS ↔ GCP via FCR

#### Prerequisites

- AWS Direct Connect (or use standard AWS public peering)
- GCP Cloud Interconnect (or Dedicated Interconnect at Equinix)
- Equinix FCR

#### BGP Setup

```text
AWS (ASN 16509, advertises VPC CIDRs)
    |
  Equinix FCR (ASN 65001)
    |
GCP (ASN 15169, advertises subnet ranges)

AWS routes: 172.31.0.0/16
GCP routes: 10.128.0.0/9
```

#### Notes

- GCP BGP sessions typically use different ASNs per region
- Cloud Interconnect provides Layer 2 connectivity; BGP runs over that
- Route priorities: Use local preference or MED to influence path selection

### Multi-Cloud (AWS + Azure + GCP)

```text
        Equinix FCR
       /    |    \
      /     |     \
    AWS   Azure   GCP
  (16509)(8075) (15169)

Routing table at FCR:
  10.0.0.0/16 (AWS) → Advertise to Azure + GCP
  192.168.0.0/16 (Azure) → Advertise to AWS + GCP
  10.128.0.0/9 (GCP) → Advertise to AWS + Azure
```

**Each cloud sees routes from other clouds via FCR.**

---

## Cisco Router Configuration Example

### Scenario: Cisco Router in AWS Peering with Azure via FCR

```ios
configure terminal

router bgp 65000
  bgp router-id 10.0.0.1

  ! Peer with Equinix FCR
  neighbor 10.255.1.2 remote-as 65001
  neighbor 10.255.1.2 description "Equinix FCR to Azure"
  neighbor 10.255.1.2 timers 3 9

  address-family ipv4
    neighbor 10.255.1.2 activate
    neighbor 10.255.1.2 soft-reconfiguration inbound

    ! Advertise AWS VPC subnets
    network 10.0.0.0 mask 255.0.0.0
    network 10.1.0.0 mask 255.255.0.0

    ! Receive Azure VNet routes from FCR
    ! (default: receive all routes)

  exit-address-family

end
```

**Verification:**

```ios
show bgp ipv4 unicast
! Should show:
!   10.0.0.0/8 (local, weight 32768)
!   192.168.0.0/16 (from FCR, path: 65001 8075)

show ip route bgp
! Should show Azure routes via BGP
```

---

## FortiGate Configuration Example

### Scenario: FortiGate in AWS Peering with Azure via FCR

```fortios
config system interface
  edit "WAN"
    set ip 10.255.1.1 255.255.255.252
    set description "Equinix FCR Link"
  next
end

config router bgp
  set as 65000
  set router-id 10.0.0.1

  config neighbor
    edit "10.255.1.2"
      set remote-as 65001
      set description "Equinix FCR (to Azure)"
      set timers-hold 30
      set timers-keepalive 10
    next
  end

  config network
    edit 1
      set prefix 10.0.0.0 255.0.0.0
      set description "AWS VPC"
    next
  end

end

config firewall policy
  edit 1
    set name "AWS-to-Azure"
    set srcintf "LAN"
    set dstintf "WAN"
    set action accept
    set srcaddr "AWS-Subnets"
    set dstaddr "all"  ! Will match Azure routes learned via BGP
  next
end
```

**Verification:**

```text
get router bgp summary
! Should show neighbor 10.255.1.2 ESTABLISHED

diagnose ip route list | grep 192.168
! Should show Azure routes learned via BGP
```

---

## Use Cases and Benefits

### Use Case 1: Application Migration (AWS → Azure)

```text
Phase 1: Dual-running
  AWS (old): Primary
  Azure (new): Secondary, receiving replicated data
  Connection: Equinix FCR

Phase 2: Gradual cutover
  Lower AWS priority, raise Azure priority
  DNS switches to point to Azure

Phase 3: Sunset
  AWS decommissioned
  All traffic on Azure + Equinix FCR
```

**Benefit:** Zero-downtime migration with test failover capability.

### Use Case 2: Multi-Region Disaster Recovery

```text
Primary region (AWS US-East)
  Application + Database

Secondary region (Azure US-West)
  Standby database (hot standby)

Real-time sync via Equinix FCR:
  AWS → Azure: ~2–5ms latency

On AWS failure:
  DNS points to Azure
  Failover time: <30 seconds (BGP + DNS)
```

**Benefit:** Fast RTO/RPO, proven inter-cloud link.

### Use Case 3: Cost Optimization

```text
Database tier (expensive): Azure SQL (specialized)
Cache tier: AWS ElastiCache (cheaper)
App tier: GCP (good pricing for this workload)

All connected via Equinix FCR
Zero egress charges between clouds (only vConnection cost)
```

**Benefit:** Use each cloud for its strengths, without cost penalty.

### Use Case 4: Multi-Cloud Load Balancing

```text
Service X: Run on AWS, Azure, GCP simultaneously
Load balancer sends traffic to all three
Equinix FCR ensures all clouds reachable with <20ms latency
```

**Benefit:** Better availability, cost arbitrage, vendor negotiation.

---

## Monitoring and Troubleshooting

### Monitor Inter-Cloud Connectivity

```text
Equinix Console:
  Fabric → Virtual Connections
  Monitor: AWS DX status, Azure ER status, FCR health

BGP Sessions:
  show bgp ipv4 unicast summary
  ! All cloud peers should show Established

Routing:
  show ip route bgp
  ! Routes from all connected clouds present

Latency:
  traceroute (AWS → Azure)
  ! Should show ~3–5 hops through FCR
  ! Latency: 1–20ms (same metro)
```

### Troubleshooting Common Issues

#### Issue: Azure routes not received at AWS

```text
Check:

  1. Azure ER connection status (Equinix Console)
  2. FCR BGP session with Azure (status: Established?)
  3. Azure routes advertised by ER partner

Fix:

  - Verify Azure side advertising routes to ER

  - Check BGP session timers (may be too aggressive)

  - Verify no access lists blocking Azure routes
```

#### Issue: High latency between clouds (>50ms)

```text
Possible causes:

  1. Traffic not routing through FCR (taking internet path)
  2. FCR in different metro than expected
  3. BGP suboptimal path selection

Check:

  - Verify BGP best path (show ip bgp [destination] detail)

  - Traceroute to confirm path (should go through FCR IP)

  - Check latency by metro (SJC-LAX ~15ms, SJC-LHR ~170ms)

Fix:

  - Adjust local preference/weight if path suboptimal

  - Consider secondary FCR in different metro if latency critical
```

---

## Best Practices

| Practice | Reason |
| --- | --- |
| **Use dual FCR for production** | Survives single FCR failure |
| **BGP timers 3s/9s** | Fast convergence (~10s) |
| **Advertise only necessary routes** | Reduce BGP table, improve stability |
| **Use communities for policy** | Fine-grained traffic steering |
| **Monitor BGP uptime** | Target: 99.9%+ (< 43 minutes/month downtime) |
| **Test failover quarterly** | Verify secondary cloud path works |
| **Document BGP topology** | Multi-cloud is complex; clear mapping essential |
| **Size vConnections correctly** | Based on peak inter-cloud traffic, not total |
| **Use consistent AS numbering** | Private ASNs (65000–65534) to avoid conflicts |
| **Plan for growth** | Upgrade vConnection bandwidth 6–12 months before capacity |

---

## Cost Considerations

### Bandwidth Cost Comparison

| Path | Cost per GB | Typical Use |
| --- | --- | --- |
| **Public Internet (egress)** | $0.02–0.10 | Most traffic |
| **Equinix FCR (vConnection)** | $0 per GB* | Critical inter-cloud |
| **AWS DX** | $0.02/hr + data | AWS-specific |
| **Azure ER** | Varies | Azure-specific |

*Equinix FCR cost is vConnection subscription (~$500–5000/month per 1–10 Gbps), not per-byte.

### Financial Decision: FCR vs. Internet

```text
Scenario: 1TB/month of critical AWS-Azure traffic

Option A: Internet path
  Cost: 1000 GB × $0.05 = $50/month
  Latency: 30–100ms (unpredictable)

Option B: Equinix FCR (10 Gbps)
  Cost: $3000/month (vConnection) + $500 (FCR) = $3500/month
  Latency: 5–15ms (predictable)

Break-even: ~70TB/month (not just data cost, but latency/SLA value)
```

**Use FCR when:**

- Latency SLA required
- High-throughput critical workload
- Willing to pay for consistency

---

## Summary

**Cloud-to-Cloud via Equinix FCR enables:**

- Sub-20ms latency between any clouds (private path)
- Zero inter-cloud data transfer costs (bandwidth-based pricing only)
- Automatic failover via BGP (no manual intervention)
- Single BGP routing table for all clouds
- Application-specific traffic steering

**Best for:**

- Multi-cloud applications
- Cloud migrations with failover
- Disaster recovery between clouds
- Cost-optimized multi-cloud (use each cloud's strengths)

**Not needed for:**

- Single cloud deployments
- Occasional inter-cloud communication
- Budget-conscious low-bandwidth scenarios

---

## Next Steps

- [Equinix FCR Setup & Provisioning](equinix_fcr_setup.md) — Create FCR and vConnections
- [IP WAN Best Practices](equinix_ip_wan_best_practices.md) — Design and monitoring
- [Cisco to Equinix FCR](cisco_to_equinix_fcr.md) — Detailed Cisco configs
- [FortiGate to Equinix FCR](fortigate_to_equinix_fcr.md) — Detailed FortiGate configs
