# UDP Header

UDP provides a minimal, connectionless transport for applications that prioritise
low overhead over reliability. There is no handshake, retransmission, or ordering —
delivery is best-effort. The fixed 8-byte header makes UDP well-suited to latency-
sensitive traffic such as DNS, DHCP, SNMP, and real-time media.

## Quick Reference

| Property | Value |
| --- | --- |
| **OSI Layer** | Layer 4 — Transport |
| **TCP/IP Layer** | Transport |
| **RFC** | RFC 768 |
| **Wireshark Filter** | `udp` |
| **IP Protocol** | `17` |

## Header Structure

```mermaid
---
title: "UDP Header"
---
packet-beta
0-15: "Source Port"
16-31: "Destination Port"
32-47: "Length"
48-63: "Checksum"
```

## Field Reference

| Field | Bits | Description |
| --- | --- | --- |
| **Source Port** | 16 | Port number of the sending application. Optional — set to `0` if not used. |
| **Destination Port** | 16 | Port number of the receiving application. |
| **Length** | 16 | Total length of the UDP header and payload in bytes. Minimum value is `8` (header only). |
| **Checksum** | 16 | One's complement checksum over a pseudo-header (source/destination IP, protocol, UDP length), UDP header, and payload. Optional in IPv4 (set to `0` to disable); mandatory in IPv6. |

## Notes

- **No connection state** means UDP has negligible per-flow overhead. Applications
  that need reliability implement it themselves (e.g. QUIC, TFTP, DNS over TCP fallback).
- **BFD** (Bidirectional Forwarding Detection) uses UDP port `3784` for single-hop
  sessions and port `4784` for multi-hop sessions. The lightweight nature of UDP is
  essential for BFD's sub-second hello intervals.
- **QUIC** (HTTP/3) runs over UDP port `443`, implementing its own reliability,
  ordering, and encryption at the application layer.
- The **checksum pseudo-header** includes the source and destination IP addresses,
  ensuring a misdelivered datagram is detected even if the UDP checksum alone passes.
