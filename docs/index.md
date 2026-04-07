# Network Engineering Reference

A technical reference library covering network protocols from Layer 2 to Layer 7,
routing design, vendor implementation guides, and quick-reference cheat sheets.

---

## Packet Headers

Wire-format reference for protocols at each OSI layer, with annotated diagrams
and field-level descriptions.

### Layer 2 — Data Link

| Protocol | Description |
| --- | --- |
| [Ethernet II](packets/ethernet.md) | Frame structure, EtherTypes, 802.1Q VLAN tagging |
| [ARP](packets/arp.md) | Address Resolution Protocol — IPv4 to MAC mapping |

### Layer 3 — Network

| Protocol | Description |
| --- | --- |
| [IPv4](packets/ipv4.md) | Header fields, fragmentation, DSCP/ECN, options |
| [IPv6](packets/ipv6.md) | Fixed header, extension headers, flow label |
| [ICMP](packets/icmp.md) | Echo, Destination Unreachable, Redirect, Time Exceeded |

### Layer 4 — Transport

| Protocol | Description |
| --- | --- |
| [TCP](packets/tcp.md) | Header, three-way handshake, FIN/RST teardown, flags |
| [UDP](packets/udp.md) | Lightweight datagram header |
| [BFD](packets/bfd.md) | Bidirectional Forwarding Detection — sub-second link failure |

---

## Routing Protocols

Packet formats, state machines, and operational detail for interior and exterior
gateway protocols.

| Protocol | Type | Description |
| --- | --- | --- |
| [BGP](routing/bgp.md) | Path-vector | Inter-AS and data-centre routing; OPEN/UPDATE/KEEPALIVE |
| [OSPF](routing/ospf.md) | Link-state | Areas, LSAs, DR/BDR, neighbour state machine |
| [EIGRP](routing/eigrp.md) | Distance-vector | DUAL algorithm, TLVs, feasible successors |
| [RIP](routing/rip.md) | Distance-vector | Classic IGP; v1/v2/ng comparison |
| [IGRP](routing/igrp.md) | Distance-vector | Deprecated Cisco predecessor to EIGRP |

---

## Application Protocols

Message formats and behaviour for common application and infrastructure protocols.

| Protocol | Description |
| --- | --- |
| [HTTP / HTTPS](application/http.md) | HTTP/1.1 request/response, HTTP/2 binary frame, HTTP/3/QUIC |
| [DNS](application/dns.md) | Message format, record types, resolution flow, DNSSEC, EDNS0 |
| [PTP](application/ptp.md) | IEEE 1588v2 — sub-microsecond clock sync, BMCA, clock types |
| [SSH](application/ssh.md) | Handshake, key exchange, channel multiplexing |
| [SNMP](application/snmp.md) | v1 / v2c / v3 PDU formats, trap vs inform, USM security |
| [Syslog](application/syslog.md) | RFC 5424 message format, severity/facility, transports |

---

## Theory & Comparisons

Protocol behaviour analysis and side-by-side comparisons to inform design decisions.

| Guide | Description |
| --- | --- |
| [EIGRP vs OSPF vs RIP](theory/igp_comparison.md) | Metric, convergence, scalability, and deployment guidance |
| [BGP vs BFD](theory/bgp_bfd_comparison.md) | Hold-timer analysis and BFD integration for BGP |
| [OSPF vs BFD](theory/ospf_bfd_comparison.md) | Dead interval vs BFD hardware triggers |
| [EIGRP vs BFD](theory/eigrp_bfd_comparison.md) | DUAL feasible successor promotion with BFD |
| [NTP vs PTP](theory/ntp_vs_ptp.md) | Accuracy, hierarchy, infrastructure requirements |

---

## Vendor Implementation Guides

### Cisco IOS-XE

| Guide | Description |
| --- | --- |
| [BFD Core Config](cisco/cisco_bfd_config_guide.md) | BFD templates for BGP, OSPF, and EIGRP |
| [Static BFD](cisco/cisco_static_bfd_guide.md) | Monitoring static gateways with BFD and Object Tracking |
| [Multihop BFD](cisco/cisco_multihop_bfd_guide.md) | Sub-second detection for non-directly connected peers |
| [Active/Passive to AWS TGW](cisco/cisco_aws_tgw_dx.md) | DX Transit VIFs and BGP Communities |

### Fortinet FortiGate

| Guide | Description |
| --- | --- |
| [BFD Core Config](fortigate/fortigate_bfd_config_guide.md) | Hardware-offloaded BFD and NPU acceleration |
| [Multihop BFD](fortigate/fortigate_multihop_bfd_guide.md) | `bfd-map` for multi-hop BGP peering |
| [Static BFD & Health Checks](fortigate/fortigate_static_bfd_guide.md) | Static route monitoring and SD-WAN SLAs |

### AWS Architecture

| Guide | Description |
| --- | --- |
| [BGP Stack (Flagship)](aws/bgp_stack_vpn_over_dx.md) | Overlay-over-underlay for AWS Direct Connect |
| [BGP over VPN Optimization](aws/bgp_vpn_optimization.md) | BGP-to-DPD timer relationship and Graceful Restart |
| [FortiGate to TGW (ECMP)](aws/fortigate_bgp_vpn_bfd.md) | Dual-VTI ECMP over TGW with NPU offload |
| [Troubleshooting VPN & BGP Logs](aws/troubleshooting_vpn_bgp_log_analysis_guide.md) | DPD, hold-timer, IKE re-key log analysis |

### Azure Architecture

| Guide | Description |
| --- | --- |
| [BGP Stack (Flagship)](azure/bgp_stack_vpn_over_expressroute.md) | Encrypted VPN overlay over ExpressRoute private peering |
| [Active-Active VPN Optimization](azure/bgp_vpn_optimization.md) | Dual-instance VPN Gateway ECMP with APIPA BGP addressing |
| [Troubleshooting VPN & BGP Logs](azure/troubleshooting_vpn_bgp_log_analysis_guide.md) | IKEv2, DPD, BGP, and ExpressRoute log analysis |

### GCP Architecture

| Guide | Description |
| --- | --- |
| [BGP Stack (Flagship)](gcp/bgp_stack_vpn_over_interconnect.md) | Encrypted HA VPN overlay over Cloud Interconnect |
| [HA VPN Optimization](gcp/bgp_vpn_optimization.md) | Cloud Router BGP tuning, MED path preference, ECMP |
| [Troubleshooting VPN & BGP Logs](gcp/troubleshooting_vpn_bgp_log_analysis_guide.md) | IKEv2, DPD, BGP, and Cloud Interconnect log analysis |

---

## Reference

Quick-lookup tables for common networking values.

| Reference | Description |
| --- | --- |
| [IP Network Ranges](reference/ip_networks.md) | RFC 1918, CGNAT, documentation, multicast, IPv6 special ranges |
| [TCP/UDP Ports](reference/ports.md) | Well-known and registered port numbers by category |
| [BGP Path Selection](reference/bgp_path_selection.md) | Cisco and Junos best-path algorithm, step-by-step |
| [Administrative Distance](reference/admin_distance.md) | Route source preference — Cisco, Junos, NX-OS, Arista |
