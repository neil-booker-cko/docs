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

---

## Layer 3 — Network

| Protocol | Description |
| --- | --- |
| [IPv4](ipv4.md) | Core Internet Protocol; addressing, fragmentation, routing |
| [IPv6](ipv6.md) | 128-bit addressing, fixed 40-byte header, extension header chaining |
| [ICMP](icmp.md) | Error reporting and diagnostics (ping, traceroute, Path MTU Discovery) |

---

## Layer 4 — Transport

| Protocol | Description |
| --- | --- |
| [TCP](tcp.md) | Reliable, ordered byte-stream delivery; three-way handshake; flow control |
| [UDP](udp.md) | Connectionless, best-effort delivery; minimal overhead |
| [BFD](bfd.md) | Sub-second forwarding path failure detection; runs over UDP |
