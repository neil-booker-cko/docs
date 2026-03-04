# Network Resilience Library

Master index for sub-second failover and hybrid-cloud connectivity guides. This
repository provides a comprehensive collection of technical documentation and configuration
guides for Cisco, Fortinet, and AWS environments.

---

## 1. Core Protocol Comparisons (Theory)

Fundamental analyses of routing protocol convergence timelines and BFD integration.

- [**BGP vs BFD Comparison**](bgp_bfd_comparison.md): Analysis of BGP hold-timers,
    BFD reaction times, and detailed restoration phases (TCP Handshake/Prefix exchange).
- [**OSPF vs BFD Comparison**](ospf_bfd_comparison.md): Comparison of Standard,
    Tuned, and Fast Hellos against BFD hardware triggers.
- [**EIGRP vs BFD Comparison**](eigrp_bfd_comparison.md): Technical look at how
    the DUAL algorithm promotes Feasible Successors using BFD.

## 2. Cisco Implementation Guides

Standard and advanced BFD configurations for Cisco IOS-XE platforms.

- [**Cisco BFD Core Config**](cisco_bfd_config_guide.md): Unified BFD templates
    for BGP, OSPF, and EIGRP on modern IOS-XE.
- [**Cisco Static BFD Guide**](cisco_static_bfd_guide.md): Monitoring static gateways
    for silent failures using direct BFD or Object Tracking.
- [**Cisco Multihop BFD Guide**](cisco_multihop_bfd_guide.md): Sub-second detection
    for non-directly connected peers using UDP Port 4784.
- [**Cisco to AWS TGW (Active/Passive)**](cisco_aws_tgw_dx.md): Deterministic path
    control using DX Transit VIFs and BGP Communities.

## 3. Fortinet Implementation Guides

High-performance BFD and failover settings for FortiGate security appliances.

- [**FortiOS BFD Guide**](fortigate_bfd_config_guide.md): Hardware-offloaded BFD
    implementation, Link-Down failover, and NPU acceleration.
- [**FortiOS Multihop BFD**](fortigate_multihop_bfd_guide.md): Configuring `bfd-map`
    for multi-hop BGP and static peering.
- [**FortiOS Static BFD & Health Checks**](fortigate_static_bfd_guide.md): Static
    route monitoring via BFD and SD-WAN Performance SLAs.

## 4. Architecture & Optimization Guides

Flagship designs and specific audit reports for Hybrid Cloud connectivity.

- [**The BGP Stack (Flagship Architecture)**](bgp_stack_vpn_over_dx.md): Recursive
    Overlay-over-Underlay design for high-resilience AWS Direct Connect.
- [**BGP over VPN Optimization**](bgp_vpn_optimization.md): Resilience strategies
    focusing on the BGP-to-DPD timer relationship and Graceful Restart.

---

## Architectural Principles

1. **Deterministic Path Control:** Use `local-preference` (Outbound) and AS-Path
    Prepending/Communities (Inbound) to ensure symmetric traffic flow.
1. **Layered Detection:** BFD (300ms x 3) for the physical underlay; Optimized DPD
    (5s x 3) and BGP tuning (10s/30s) for the encrypted overlay.
1. **Hardware Acceleration:** Leverage NPU/ASIC offloading for BFD heartbeats to
    prevent false positives during CPU spikes.
1. **Resilient Maintenance:** Enable BGP Graceful Restart to maintain data-plane
    forwarding during control-plane reloads.

---

## Verification Quick-Reference

| Goal | Cisco IOS-XE | Fortinet FortiOS |
| ----- | ----- | ----- |
| **Check BFD Status** | `show bfd neighbors` | `get router info bfd neighbor` |
| **Verify Best Path** | `show ip bgp` | `get router info bgp network` |
| **Monitor BFD Trace** | `debug bfd event` | `diagnose sniffer packet any 'udp port 3784' 4` |
| **Track SLA Metrics** | `show track` | `diagnose sys sdwan health-check status` |

---

## Meta

- [**Documentation Audit Report**](documentation_audit_report.md): Internal tracker
    for consistency, branding, and standardisation.

*Created for Network Engineering Teams specializing in Hybrid Cloud Connectivity.*
