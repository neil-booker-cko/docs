# Packet Header Reference

Field-level reference for Layer 2–4 protocol headers. For routing protocol formats
see [Routing Protocols](../routing/index.md); for application protocol formats see
[Application Protocols](../application/index.md).

---

## Layer 2 — Data Link

| Protocol | Description |
| --- | --- |
| [Ethernet II](ethernet.md) | Standard Layer 2 frame; carries IPv4, IPv6, ARP |
| [ARP](arp.md) | Resolves IPv4 addresses to MAC addresses on a local segment |
| [STP / RSTP](stp.md) | Spanning tree loop prevention; BPDU format and port roles |
| [LLDP](lldp.md) | IEEE 802.1AB link layer discovery; TLV-based neighbour advertisement |
| [CDP](cdp.md) | Cisco Discovery Protocol; Cisco-proprietary neighbour discovery |

---

## Layer 3 — Network

| Protocol | Description |
| --- | --- |
| [IPv4](ipv4.md) | Core Internet Protocol; addressing, fragmentation, routing |
| [IPv6](ipv6.md) | 128-bit addressing, fixed 40-byte header, extension header chaining |
| [ICMP](icmp.md) | Error reporting and diagnostics (ping, traceroute, Path MTU Discovery) |
| [GRE](gre.md) | Generic Routing Encapsulation; tunnels any network layer protocol over IP |
| [VXLAN](vxlan.md) | Virtual Extensible LAN; Layer 2 overlay over UDP with 24-bit VNI |

---

## Layer 4 — Transport

| Protocol | Description |
| --- | --- |
| [TCP](tcp.md) | Reliable, ordered byte-stream delivery; three-way handshake; flow control |
| [UDP](udp.md) | Connectionless, best-effort delivery; minimal overhead |
| [BFD](bfd.md) | Sub-second forwarding path failure detection; runs over UDP |
