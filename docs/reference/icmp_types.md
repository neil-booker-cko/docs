# ICMP Type and Code Reference

Complete lookup table for ICMP (RFC 792) Type and Code values. The Type field identifies
the message class; the Code field provides detail within that class. For the ICMP header
format see [ICMP](../packets/icmp.md).

## Quick Reference

| Property | Value |
| --- | --- |
| **IP Protocol** | 1 |
| **ICMPv4 RFC** | RFC 792 |
| **ICMPv6 RFC** | RFC 4443 |
| **Header fields** | Type (8 bits), Code (8 bits), Checksum (16 bits) |
| **Wireshark filter** | `icmp` (v4), `icmpv6` (v6) |

---

## ICMPv4 Types and Codes

| Type | Code | Name | Notes |
| --- | --- | --- | --- |
| **0** | 0 | Echo Reply | Response to Type 8 Echo Request (ping). |
| **3** | 0 | Destination Unreachable — Net Unreachable | No route to the destination network. |
| **3** | 1 | Destination Unreachable — Host Unreachable | Host could not be reached. |
| **3** | 2 | Destination Unreachable — Protocol Unreachable | Destination does not support the protocol. |
| **3** | 3 | Destination Unreachable — Port Unreachable | Destination port is not open. |
| **3** | 4 | Destination Unreachable — Fragmentation Needed and DF Set | Packet exceeds next-hop MTU and DF=1. Used for Path MTU Discovery. Next-Hop MTU is included in the Type-Specific field. |
| **3** | 5 | Destination Unreachable — Source Route Failed | Source routing failed. |
| **3** | 6 | Destination Unreachable — Destination Network Unknown | The destination network is unknown. |
| **3** | 7 | Destination Unreachable — Destination Host Unknown | The destination host is unknown. |
| **3** | 8 | Destination Unreachable — Source Host Isolated | Source host is isolated (obsolete). |
| **3** | 9 | Destination Unreachable — Communication with Destination Network Administratively Prohibited | Network blocked by policy. |
| **3** | 10 | Destination Unreachable — Communication with Destination Host Administratively Prohibited | Host blocked by policy. |
| **3** | 11 | Destination Unreachable — Destination Network Unreachable for Type of Service | No route for the requested ToS to the network. |
| **3** | 12 | Destination Unreachable — Destination Host Unreachable for Type of Service | No route for the requested ToS to the host. |
| **3** | 13 | Destination Unreachable — Communication Administratively Prohibited | Filtered by firewall. |
| **3** | 14 | Destination Unreachable — Host Precedence Violation | Precedence level disallowed for source/destination. |
| **3** | 15 | Destination Unreachable — Precedence Cutoff in Effect | Network operators have imposed a minimum precedence. |
| **4** | 0 | Source Quench | Deprecated (RFC 6633). Formerly used for congestion signalling. Must be ignored by receivers. |
| **5** | 0 | Redirect — Redirect for Network | Router informs host of a better gateway for the destination network. |
| **5** | 1 | Redirect — Redirect for Host | Router informs host of a better gateway for the specific destination host. |
| **5** | 2 | Redirect — Redirect for Type of Service and Network | Better gateway for the destination network and ToS. |
| **5** | 3 | Redirect — Redirect for Type of Service and Host | Better gateway for the destination host and ToS. |
| **8** | 0 | Echo Request | Ping request. Expects a Type 0 Echo Reply. |
| **9** | 0 | Router Advertisement | IRDP (RFC 1256). Router announces its presence and address(es). |
| **10** | 0 | Router Solicitation | IRDP (RFC 1256). Host requests router advertisement. |
| **11** | 0 | Time Exceeded — TTL Expired in Transit | TTL reached zero at an intermediate router. Basis of traceroute. |
| **11** | 1 | Time Exceeded — Fragment Reassembly Time Exceeded | Reassembly timer expired before all fragments arrived. |
| **12** | 0 | Parameter Problem — Pointer Indicates the Error | IP header error; the pointer field identifies the octet. |
| **12** | 1 | Parameter Problem — Missing a Required Option | A required IP option is absent. |
| **12** | 2 | Parameter Problem — Bad Length | IP header length field is invalid. |
| **13** | 0 | Timestamp Request | Requests timestamp from destination. |
| **14** | 0 | Timestamp Reply | Reply to Type 13 Timestamp Request. |
| **17** | 0 | Address Mask Request | Deprecated. Formerly used to discover subnet mask. |
| **18** | 0 | Address Mask Reply | Deprecated. Response to Type 17. |

---

## ICMPv6 Types and Codes (RFC 4443)

ICMPv6 subsumes the functions of both ICMPv4 and ARP. Types 1–127 are error messages;
Types
128–255 are informational messages.

| Type | Code | Name | Notes |
| --- | --- | --- | --- |
| **1** | 0 | Destination Unreachable — No route to destination | No route exists. |
| **1** | 1 | Destination Unreachable — Communication administratively prohibited | Blocked by firewall or policy. |
| **1** | 2 | Destination Unreachable — Beyond scope of source address | Source address scope too small. |
| **1** | 3 | Destination Unreachable — Address unreachable | Address not reachable (e.g. NDP failure). |
| **1** | 4 | Destination Unreachable — Port unreachable | UDP port closed at destination. |
| **1** | 5 | Destination Unreachable — Source address failed ingress/egress policy | Failed source policy check. |
| **1** | 6 | Destination Unreachable — Reject route to destination | Route exists but is a reject/blackhole. |
| **1** | 7 | Destination Unreachable — Error in source routing header | Source routing header processing failed. |
| **2** | 0 | Packet Too Big | IPv6 equivalent of ICMPv4 Type 3 Code 4. Sent when a packet exceeds next-hop MTU. Used for Path MTU Discovery. MTU value included in message body. |
| **3** | 0 | Time Exceeded — Hop limit exceeded in transit | Hop limit reached zero; equivalent to ICMPv4 TTL exceeded. |
| **3** | 1 | Time Exceeded — Fragment reassembly time exceeded | Reassembly timer expired. |
| **4** | 0 | Parameter Problem — Erroneous header field encountered | Pointer field identifies the octet in error. |
| **4** | 1 | Parameter Problem — Unrecognised next header type | Next Header value is unknown. |
| **4** | 2 | Parameter Problem — Unrecognised IPv6 option | Option type in a Destination Options or Hop-by-Hop header is unknown. |
| **128** | 0 | Echo Request | ICMPv6 ping request. |
| **129** | 0 | Echo Reply | ICMPv6 ping reply. |
| **133** | 0 | Router Solicitation (NDP) | Host requests router advertisement. RFC 4861. |
| **134** | 0 | Router Advertisement (NDP) | Router announces presence, prefix, and gateway info. RFC 4861. |
| **135** | 0 | Neighbour Solicitation (NDP) | Resolves IPv6 address to link-layer address; replaces ARP. RFC 4861. |
| **136** | 0 | Neighbour Advertisement (NDP) | Response to Neighbour Solicitation. RFC 4861. |
| **137** | 0 | Redirect (NDP) | Router informs host of a better first-hop for a destination. RFC 4861. |

---

## Notes

- **Never block ICMPv4 Type 3 Code 4** at firewalls. This message carries the next-hop
MTU

MTU

and is required for Path MTU Discovery (PMTUD). Blocking it causes TCP sessions using
large packets to hang silently — small packets succeed but large file transfers stall.

- **Type 11 Code 0 (TTL Expired)** is what traceroute relies on. Blocking it prevents
traceroute

traceroute

    from identifying intermediate hops but does not affect data plane forwarding.

- **ICMPv6 is essential for IPv6 operation.** NDP (Types 133–137) replaces ARP entirely.

Blocking ICMPv6 breaks address resolution, router discovery, and SLAAC — IPv6
connectivity
    will fail. Never apply blanket ICMPv6 block rules.

- **Minimum recommended firewall ICMP permit (inbound and outbound):** Type 0 (Echo
Reply),

Reply),

Type 3 (Destination Unreachable — all codes, especially Code 4), Type 8 (Echo Request),
    Type 11 (Time Exceeded).

- **Source Quench (Type 4)** must not be generated (RFC 6633). Any received Source
Quench

Quench

    messages should be silently discarded.
