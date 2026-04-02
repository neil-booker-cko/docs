# Routing Protocol Reference

Packet format and behaviour reference for routing protocols. For convergence timing
and BFD integration see the [Theory](../theory/bgp_bfd_comparison.md) guides; for
Layer 2–4 wire formats see [Packet Headers](../packets/index.md).

---

| Protocol | Transport | Description |
| --- | --- | --- |
| BGP | TCP `179` | Path-vector protocol for inter-AS and data-centre routing |
| OSPF | IP proto `89` | Link-state IGP; areas, LSAs, DR/BDR election |
| EIGRP | IP proto `88` | Cisco enhanced distance-vector; DUAL algorithm |
| RIP v1/v2 | UDP `520` | Classic distance-vector IGP; max 15 hops |
| IGRP | IP proto `9` | Cisco proprietary distance-vector; deprecated |

*Detailed packet format pages coming soon.*
