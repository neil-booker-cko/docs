# Routing Protocols

Reference pages for the major IP routing protocols used in enterprise and data centre
networks. Each page covers packet formats, message types, timers, and protocol behaviour
— distinct from the vendor configuration guides in the Cisco & FortiGate section.

---

## Interior Gateway Protocols

| Protocol | Type | Algorithm | Metric | RFC |
| --- | --- | --- | --- | --- |
| [OSPF](ospf.md) | Link-state | Dijkstra (SPF) | Cost (bandwidth) | RFC 2328 |
| [EIGRP](eigrp.md) | Advanced distance-vector | DUAL | Composite (BW + delay) | RFC 7868 |
| [RIP](rip.md) | Distance-vector | Bellman-Ford | Hop count (max 15) | RFC 2453 |
| [IGRP](igrp.md) | Distance-vector | Bellman-Ford | Composite (BW + delay) | Cisco proprietary |

## Exterior Gateway Protocols

| Protocol | Type | Algorithm | Metric | RFC |
| --- | --- | --- | --- | --- |
| [BGP](bgp.md) | Path-vector | Best-path selection | AS path + attributes | RFC 4271 |

---

## See Also

- [IGPs vs EGPs](../theory/igp_vs_egp.md) — comparison of interior and exterior routing categories
- [OSPF vs EIGRP](../theory/ospf_vs_eigrp.md) — side-by-side protocol comparison
- [Cisco OSPF Config](../cisco/cisco_ospf_config.md) — vendor implementation
- [FortiGate BGP Config](../fortigate/fortigate_bgp_config.md) — vendor implementation
