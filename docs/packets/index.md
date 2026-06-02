# Packet Headers

Reference pages for packet and frame header formats across the network stack. Each page
covers field-level detail: bit layout, field meanings, flags, options, and wire format.

---

## Layer 2 — Data Link

| Protocol | Standard | Purpose |
| --- | --- | --- |
| [Ethernet II](ethernet.md) | IEEE 802.3 | Layer 2 framing |
| [ARP](arp.md) | RFC 826 | IPv4 address resolution |
| [STP / RSTP](stp.md) | IEEE 802.1D / 802.1w | Loop prevention |
| [LLDP](lldp.md) | IEEE 802.1AB | Neighbour discovery |
| [CDP](cdp.md) | Cisco proprietary | Cisco neighbour discovery |
| [LACP](lacp.md) | IEEE 802.3ad | Link aggregation control |

## Layer 2.5 — MPLS

| Protocol | Standard | Purpose |
| --- | --- | --- |
| [MPLS](mpls.md) | RFC 3031 | Label-switched forwarding |

## Layer 3 — Network & Routing

| Protocol | Standard | Purpose |
| --- | --- | --- |
| [IPv4](ipv4.md) | RFC 791 | Internet Protocol version 4 |
| [IPv6](ipv6.md) | RFC 8200 | Internet Protocol version 6 |
| [ICMP](icmp.md) | RFC 792 | Error and control messages |
| [GRE](gre.md) | RFC 2784 | Generic encapsulation tunnel |
| [VXLAN](vxlan.md) | RFC 7348 | L2 overlay for L3 networks |
| [OSPF](ospf.md) | RFC 2328 | Link-state routing |
| [BGP](bgp.md) | RFC 4271 | Path-vector routing |
| [IS-IS](isis.md) | ISO 10589 | Link-state routing |
| [IGMP](igmp.md) | RFC 3376 | Multicast group management |
| [VRRP](vrrp.md) | RFC 5798 | Virtual gateway redundancy |
| [HSRP](hsrp.md) | RFC 2281 | Cisco gateway redundancy |

## Layer 4 — Transport

| Protocol | Standard | Purpose |
| --- | --- | --- |
| [TCP](tcp.md) | RFC 9293 | Reliable, ordered transport |
| [UDP](udp.md) | RFC 768 | Connectionless transport |
| [BFD](bfd.md) | RFC 5880 | Bidirectional forwarding detection |

## Layer 7 — Application (Common Network Services)

| Protocol | Standard | Purpose |
| --- | --- | --- |
| [NTP](ntp.md) | RFC 5905 | Network time synchronisation |
| [PTP](ptp.md) | IEEE 1588 | Precision time protocol |
| [DNS](dns.md) | RFC 1035 | Domain name resolution |
| [DHCP](dhcp.md) | RFC 2131 | Dynamic host configuration |

---

## See Also

- [ICMP Types & Codes](../reference/icmp_types.md) — full ICMP type/code reference
- [TCP/UDP Ports](../reference/ports.md) — well-known port numbers
- [MTU & Fragmentation](../reference/mtu.md) — frame and packet size limits
