# MTU and Fragmentation Reference

MTU (Maximum Transmission Unit) is the largest Layer 3 packet that can be transmitted
without
fragmentation on a given link. When a packet exceeds the path MTU, IPv4 fragments it (if
DF=0) or returns an ICMP Type 3 Code 4 message (if DF=1). IPv6 never fragments in
transit
 — the source must perform Path MTU Discovery.

## Quick Reference

| Property | Value |
| --- | --- |
| **IPv4 fragmentation** | RFC 791 |
| **IPv4 PMTUD** | RFC 1191 |
| **IPv6 PMTUD** | RFC 8201 |
| **Packetisation Layer PMTUD** | RFC 4821 |
| **Standard Ethernet MTU** | 1500 bytes |
| **IPv6 minimum link MTU** | 1280 bytes (RFC 8200) |

---

## Common MTU Values

| Technology | MTU | Notes |
| --- | --- | --- |
| Ethernet (standard) | 1500 bytes | IEEE 802.3 default; the de facto internet standard. |
| Ethernet (jumbo frames) | 9000 bytes | Common datacentre setting; vendor variants: 9216, 9600. Must be configured end-to-end. |
| PPPoE | 1492 bytes | 8-byte PPPoE header reduces Ethernet payload from 1500. |
| DSL (ATM-based) | 1500 or 1492 | Depends on PPP or PPPoE encapsulation in use. |
| IPv6 minimum | 1280 bytes | RFC 8200 — every IPv6 link must support at least 1280 bytes. |
| GRE tunnel | 1476 bytes | 1500 − 20 (outer IP) − 4 (GRE header) = 1476. |
| GRE + IPsec (ESP, AES) | ~1422 bytes | Adds ~50+ bytes depending on cipher, IV size, and pad. |
| IPsec ESP (AES-256, SHA-256) | ~1422–1446 bytes | ESP header (8) + IV (16) + padding + ICV (16); overhead varies by cipher. |
| VXLAN | 1450 bytes | 1500 − 50 (VXLAN/UDP/outer IP encapsulation) = 1450 inner frame. |
| 802.1Q (VLAN tag) | 1496 bytes | 4-byte VLAN tag reduces available payload by 4 bytes. |
| MPLS (per label) | −4 bytes | Each label stack entry adds 4 bytes of overhead. |
| Loopback (Linux) | 65536 bytes | Software interface; no physical MTU constraint. |

---

## IPv4 Fragmentation

IPv4 fragmentation is performed by routers when a packet exceeds the outgoing link MTU
and
the DF bit is not set. The receiving host reassembles fragments.

### Header Fields

| Field | Size | Description |
| --- | --- | --- |
| **DF (Don't Fragment)** | 1 bit | If set, the router must not fragment the packet. If the packet is too large, the router discards it and sends ICMP Type 3 Code 4 back to the source. |
| **MF (More Fragments)** | 1 bit | Set on all fragments except the last. The final fragment has MF=0. |
| **Fragment Offset** | 13 bits | Offset of this fragment's data from the start of the original datagram, measured in 8-byte units. |

### Fragmentation Example

A 2000-byte datagram forwarded over a 1500-byte MTU link splits into two fragments:

| Fragment | Total Size | IP Header | Data | MF | Offset |
| --- | --- | --- | --- | --- | --- |
| 1 | 1500 bytes | 20 bytes | 1480 bytes | 1 | 0 |
| 2 | 540 bytes | 20 bytes | 520 bytes | 0 | 185 (1480 ÷ 8) |

Each fragment carries a full 20-byte IP header. Fragmentation increases per-packet
overhead and stresses reassembly buffers at the destination.

---

## Path MTU Discovery (PMTUD)

PMTUD (RFC 1191) avoids fragmentation by probing for the smallest MTU across the entire
path before sending large packets.

### How It Works

1. The source sets DF=1 on all outgoing packets.
1. If an intermediate router cannot forward the packet without fragmenting it, the
    router discards the packet and returns **ICMP Type 3 Code 4** (Fragmentation
    Needed) to the source. The message includes the next-hop MTU in the Type-Specific field.1
1. The source reduces its effective packet size to the advertised MTU and retransmits.
1. The process repeats until the packet traverses the full path without triggering a
    Fragmentation Needed response.

### PMTUD Failure

The most common failure mode is **firewalls that block ICMP Type 3 Code 4**. When this
message
is dropped:

- The source never learns that the path cannot support large packets.
- TCP sessions using large packets stall silently.
- Small packets (e.g. ACKs, SYN/SYN-ACK) succeed; large transfers (file downloads, SCP,
    HTTPS with large payloads) hang indefinitely.
- The symptom is sometimes called "black hole routing."

Mitigation: permit ICMP Type 3 (all codes) on all firewall policies, or use TCP MSS
clamping as a workaround.

---

## TCP MSS Clamping

When PMTUD cannot be relied upon — because ICMP is blocked or tunnel endpoints do not
generate ICMP — routers can clamp the **TCP MSS** (Maximum Segment Size) option in SYN and
SYN-ACK packets. This limits the maximum TCP segment size negotiated during the handshake,
preventing oversized packets from entering the network.

### Recommended MSS Values

| Encapsulation | Recommended MSS | Derivation |
| --- | --- | --- |
| Standard Ethernet | 1460 | 1500 − 20 (IP) − 20 (TCP) |
| PPPoE | 1452 | 1492 − 20 (IP) − 20 (TCP) |
| GRE | 1436 | 1476 − 20 (IP) − 20 (TCP) |
| GRE + IPsec | ~1350–1380 | Varies by cipher and padding |
| VXLAN | 1410 | 1450 − 20 (IP) − 20 (TCP) |

### Configuration

Cisco IOS — clamp MSS on a tunnel interface:

```ios

interface Tunnel0
 ip tcp adjust-mss 1380
```

Cisco IOS — clamp MSS on a WAN interface:

```ios

interface GigabitEthernet0/1
 ip tcp adjust-mss 1452
```

FortiGate — MSS override is available per interface or per firewall policy via the CLI:

```fortigate

config system interface
    edit "wan1"
        set tcp-mss 1452
    next
end
```

---

## IPv6 and Fragmentation

IPv6 **never fragments in transit**. Routers do not fragment IPv6 packets — if a packet
is too large for the next-hop link, the router drops it and sends **ICMPv6 Type 2 (Packet
Too Big)** back to the source. The source is then responsible for reducing its packet size.

IPv6 sources may perform their own fragmentation using the Fragment Extension Header (Next
Header 44), but this is the source's responsibility, not a transit router's.

The minimum required link MTU for IPv6 is **1280 bytes** (RFC 8200). Any IPv6-capable interface
must be able to forward packets of at least this size without fragmentation.

---

## Notes

- **Jumbo frames must be configured end-to-end.** Any link in the path that does not support
    jumbo frames will silently drop oversized packets. Confirm MTU on every hop before
    enabling jumbo frames.
- **Always configure MTU symmetrically** on both ends of a tunnel. Asymmetric MTU causes
    one-directional fragmentation issues that are difficult to diagnose.
- **FortiGate VTI MTU** is set in the tunnel interface config: `set mtu 1500`. TCP MSS
    clamping is available per-interface or per-policy.
- **Cisco IOS:** `ip mtu <bytes>` sets the IP MTU on an interface (may differ from the
    interface hardware MTU). `ip tcp adjust-mss <bytes>` clamps TCP MSS on SYN packets
    transiting the interface.
- PMTUD black holes are a common cause of unexplained TCP stalls on VPN and tunnel
    deployments. When troubleshooting, test with progressively smaller ping sizes:
    `ping -s 1400 -M do <destination>` on Linux.
