# Routing Protocol Reference

Packet format, state machine, and behaviour reference for routing protocols used in
enterprise and data-centre networks. For convergence timing and BFD integration
see the [Theory](../theory/bgp_bfd_comparison.md) guides; for vendor configuration
see the [Cisco](../cisco/cisco_ospf_config.md) and [FortiGate](../fortigate/fortigate_bfd_config_guide.md)
sections.

---

## Path-Vector

| Protocol | Transport | Description |
| --- | --- | --- |
| [BGP](bgp.md) | TCP `179` | Exterior gateway protocol for inter-AS routing and data-centre spine-leaf underlay. Carries path attributes, communities, and policy. Supports eBGP (between ASes) and iBGP (within an AS with route reflectors). |

## Link-State IGPs

| Protocol | Transport | Description |
| --- | --- | --- |
| [OSPF](ospf.md) | IP proto `89` | Most widely deployed enterprise IGP. Area-based hierarchy (area 0 backbone), LSA flooding, Dijkstra SPF. Supports stub/NSSA areas, DR/BDR election on broadcast segments, and authentication. |

## Distance-Vector IGPs

| Protocol | Transport | Description |
| --- | --- | --- |
| [EIGRP](eigrp.md) | IP proto `88` | Cisco enhanced distance-vector using the DUAL algorithm. Fast convergence, unequal-cost load balancing, and a composite metric (bandwidth + delay). Cisco-proprietary. |
| [RIP v1/v2](rip.md) | UDP `520` | Classic distance-vector IGP. Simple to configure; limited to 15 hops; slow convergence (30 s updates). Suitable only for small or legacy networks. |
| [IGRP](igrp.md) | IP proto `9` | Cisco proprietary distance-vector predecessor to EIGRP. No longer supported in current IOS releases; documented for reference only. |
