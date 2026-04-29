# Equinix Fabric and Fabric Cloud Router Concepts

Comprehensive guide to Equinix Fabric and Fabric Cloud Router (FCR) as a cloud and datacenter
interconnection platform.

## Core Concept

**Equinix Fabric** is a software-defined interconnection platform enabling direct, private connections
between cloud providers, datacenters, and enterprise networks without traversing the public
internet.

**Fabric Cloud Router (FCR)** is the virtual router component that manages BGP routing, traffic
steering, and redundancy across Equinix's global network.

```text
Traditional (Public Internet):
  DC A → ISP → Cloud Provider
  (exposed to internet routing, congestion, variable latency)

Equinix Fabric (Private Interconnect):
  DC A ←(direct private link)→ Equinix Metal → FCR → AWS/Azure/GCP
  (dedicated bandwidth, low latency, consistent performance)
```text

---

## Equinix Fabric Architecture

### Global Metro Presence

Equinix operates **70+ metros worldwide** with consistent interconnection capabilities.

```text
Equinix Metro Structure:
  ├─ Physical datacenters (IBX buildings)
  ├─ Equinix Metal compute availability (bare metal servers)
  ├─ Direct connection points to cloud providers
  └─ Fabric Cloud Router endpoints for routing
```text

### Connection Types

| Connection Type | Use Case | Bandwidth | Latency |
| --- | --- | --- | --- |
| **Metal-to-Cloud** | App servers to cloud databases | 10Gbps – 400Gbps | Sub-ms (same metro) |
| **DC-to-DC** | Datacenter replication | 10Gbps – 400Gbps | Varies (metro-dependent) |
| **DC-to-Cloud** | Hybrid cloud | 10Gbps – 400Gbps | Low (private link) |
| **Enterprise-to-Cloud** | WAN to cloud | 1Gbps – 100Gbps | Consistent (dedicated) |

---

## Fabric Cloud Router (FCR) Overview

### What is FCR?

A **managed, cloud-native virtual router** that handles:

- **BGP routing** between cloud providers, datacenters, and enterprises
- **Path selection** based on policies, latency, or cost
- **Redundancy** across multiple Equinix metros
- **Traffic steering** to preferred paths
- **Multi-cloud routing** (AWS, Azure, GCP simultaneously)

### FCR vs Traditional WAN

| Aspect | Traditional WAN | FCR (Equinix Fabric) |
| --- | --- | --- |
| **Path** | Public internet or MPLS | Private direct links |
| **Control** | Limited (ISP-managed) | Full control (customer-managed BGP) |
| **Performance** | Variable | Predictable |
| **Redundancy** | Manual failover | Automatic (BGP) |
| **Multi-cloud** | Complex (multiple providers) | Native (single BGP peering) |
| **Setup time** | Weeks | Hours/days |

---

## Fabric Deployment Models

### Model 1: Cloud Interconnect (Hub-and-Spoke)

Multiple clouds connected via single FCR instance.

```text
        AWS
         |
         | BGP peering
         |
    ┌────▼────┐
    │   FCR   │
    └────┬────┘
         |
    ┌────┴────┬───────┐
    |          |       |
  Azure      GCP    Enterprise

Use case: Multi-cloud applications, cloud-agnostic failover
```text

**Advantages:**
- Single BGP routing instance for all clouds
- Simplified redundancy (one FCR to fail over)
- Centralized traffic steering policies

**Disadvantages:**
- Single point of failure (mitigated with secondary FCR)
- All traffic flows through one router

### Model 2: Datacenter Interconnect (Full Mesh)

Multiple datacenters with independent FCR instances per location.

```text
  DC-A (FCR-A)  ←private link→  DC-B (FCR-B)
      |                              |
    BGP                            BGP
      |                              |
    AWS                            Azure

Use case: DR, load distribution, geo-redundancy
```text

**Advantages:**
- No single point of failure
- Traffic stays local (DC-A ↔ AWS direct)
- Lower latency for regional traffic

**Disadvantages:**
- More complex BGP configuration
- Multiple FCR instances to manage

### Model 3: Hybrid Cloud + DC (Mixed)

Combination: Primary DC routes through FCR to cloud, secondary DC routes directly.

```text
  Primary DC (FCR) → AWS/Azure/GCP
         |
       BGP
         |
  Secondary DC → On-prem resources
         |
    (optional: secondary link to FCR for failover)
```text

Use case: Gradual cloud migration, cost optimization.

---

## Virtual Connections (vConnections)

### What is a Virtual Connection?

A **logical connection** between:

- Your infrastructure (DC, Equinix Metal, on-prem)
- FCR instance
- Cloud provider (AWS, Azure, GCP)

### vConnection Types

#### 1. Metal-to-FCR
```text
Equinix Metal server → (Layer 2 Link) → FCR instance
```text

**Use case:** Apps on Metal accessing cloud via FCR.
**Bandwidth:** Up to Metal device bandwidth (typically 40Gbps – 100Gbps).

#### 2. DC-to-FCR (Cross-Connect)
```text
Your datacenter → (Dark fiber or wavelength) → Equinix IBX → FCR
```text

**Use case:** On-prem datacenters to cloud via FCR.
**Bandwidth:** 1Gbps, 10Gbps, 100Gbps (depending on carrier agreement).

#### 3. FCR-to-Cloud
```text
FCR → (Private link to AWS/Azure/GCP) → Cloud Provider
```text

**Use case:** Routing from FCR to cloud (BGP-advertised routes).
**Bandwidth:** Up to 400Gbps (varies by cloud provider).

### vConnection States

```text
Provisioning → Configuring → Waiting for BGP → Active
  (creating)    (link up)    (peers coming up)  (routing)
```text

---

## BGP in Equinix Fabric

### BGP Peering Model

FCR acts as a **BGP router** peering with:

- Your on-prem routers (Cisco, FortiGate)
- Cloud provider routers (AWS Transit Gateway, Azure VPN Gateway)
- Other FCR instances (in multi-metro deployments)

```text
Your Cisco Router
        |
      BGP (iBGP or eBGP)
        |
      FCR
        |
      BGP
        |
    AWS TGW
```text

### AS Path and Route Propagation

Equinix assigns:

- **Public ASN** (shared, for simplicity)
- **Private ASN** (dedicated, for complex topologies)

```text
Routes advertised FROM cloud TO your DC:
  AWS (AS 16509) → FCR (AS 64512) → Your router (AS 65000)
  AS Path: 16509 65000

Your routes advertised TO cloud:
  Your router (AS 65000) → FCR (AS 64512) → AWS (AS 16509)
  AS Path: 65000 16509
```text

---

## Fabric vs Direct Cloud Connections

### Equinix Fabric (FCR)

**Pros:**
- Single entry point to multiple clouds
- Consistent routing control
- Unified BGP policies

**Cons:**
- Additional cost (FCR subscription + vConnections)
- One more hop in the path
- Equinix dependency

### Direct Cloud Connections (AWS Direct Connect, Azure ExpressRoute, etc.)

**Pros:**
- Direct connection to cloud
- No additional hop
- Native cloud integration

**Cons:**
- Separate connection per cloud
- Different management for each cloud
- Complex if multi-cloud

### When to Use Fabric vs Direct

| Scenario | Fabric | Direct |
| --- | --- | --- |
| Single cloud, one location | Direct | ✓ |
| Multi-cloud, same metro | **Fabric** ✓ | Multiple connections |
| Multi-cloud, multi-region | **Fabric** ✓ | Complex/expensive |
| DC + 2+ clouds | **Fabric** ✓ | Multiple connections |
| Cloud replication only | Either | Direct acceptable |
| Strict latency SLA | Direct | Consider both |

---

## Key Metrics

### Latency

Typical latency in same Equinix metro:

```text
Equinix Metal to AWS (same IBX): <1ms
Equinix Metal to AWS (different IBX, same metro): 2–5ms
Cross-metro (e.g., SJC to LAX): 10–15ms
Intercontinental (SJC to London): 150–170ms
```text

### Throughput

- **Provisioned bandwidth:** Fixed at connection creation (1Gbps, 10Gbps, etc.)
- **Burst capability:** Some connections allow short bursts (up to 25% over provisioned)
- **No oversubscription:** Unlike public internet

### Availability

- **SLA:** Typically 99.9% (three nines)
- **Redundancy:** Deploy secondary FCR or dual vConnections to avoid single point of failure

---

## Best Practices

| Practice | Reason |
| --- | --- |
| **Deploy secondary FCR in different metro** | Survives datacenter failure |
| **Use BGP communities for traffic steering** | Fine-grained path control |
| **Monitor vConnection status** | Catch failures before customer impact |
| **Set aggressive BGP timers** | Fast convergence on failures (< 3 seconds) |
| **Document BGP topology** | Complex multi-path scenarios need clear mapping |
| **Test failover regularly** | Ensure secondary paths work under load |
| **Use private ASNs in production** | Avoid conflicts if scaling |

---

## Summary

- **Equinix Fabric** provides software-defined interconnection between clouds, datacenters, and enterprises
- **FCR** is the managed BGP router that enables this connectivity
- **vConnections** are logical links between your infrastructure and FCR/clouds
- **BGP** is the control plane for dynamic routing and failover
- **Multi-cloud models** (hub-and-spoke, mesh, hybrid) fit different use cases
- **Key advantage:** Single entry point to multiple cloud providers with consistent routing policies

---

## Next Steps

- [Equinix FCR Architecture & Deployment](equinix_fcr_architecture.md) — Detailed deployment models
- [Cisco to Equinix FCR](cisco_to_equinix_fcr.md) — Integration with Cisco routers
- [FortiGate to Equinix FCR](fortigate_to_equinix_fcr.md) — Integration with FortiGate
