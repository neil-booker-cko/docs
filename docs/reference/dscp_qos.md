# DSCP and QoS Reference

Quality of Service (QoS) provides differentiated treatment for network traffic by
marking, classifying, and queuing packets according to their priority requirements.
DSCP (Differentiated Services Code Point) is the primary IP-level marking mechanism.
The 6-bit DSCP field occupies the upper 6 bits of the IP ToS byte (IPv4) or Traffic
Class byte (IPv6), allowing 64 possible codepoints.

## Quick Reference

| Property | Value |
| --- | --- |
| **DiffServ architecture** | RFC 2474, RFC 2475 |
| **QoS configuration guidelines** | RFC 4594 |
| **Expedited Forwarding (EF) PHB** | RFC 3246 |
| **Assured Forwarding (AF) PHB** | RFC 2597 |
| **Class Selector (CS) PHB** | RFC 2474 |
| **DSCP field size** | 6 bits (64 codepoints) |
| **Location in IPv4** | ToS byte, bits 7–2 |
| **Location in IPv6** | Traffic Class byte, bits 7–2 |

---

## DSCP Field in the IP Header

The 8-bit ToS (IPv4) / Traffic Class (IPv6) byte is structured as follows:

| Bits 7–2 | Bits 1–0 |
| --- | --- |
| DSCP (6 bits) | ECN (2 bits) |

ECN (Explicit Congestion Notification) values:

| ECN Bits | Meaning |
| --- | --- |
| `00` | Non-ECT — not ECN-capable |
| `01` | ECT(1) — ECN-capable transport |
| `10` | ECT(0) — ECN-capable transport |
| `11` | CE — Congestion Experienced |

---

## DSCP Values and Per-Hop Behaviours

| DSCP (decimal) | DSCP Name | Binary | ToS Hex | PHB | Typical Use |
| --- | --- | --- | --- | --- | --- |
| 0 | CS0 / BE | 000000 | 0x00 | Best Effort | Default; bulk internet traffic. Dropped first under congestion. |
| 8 | CS1 | 001000 | 0x20 | Class Selector 1 | Background, scavenger traffic. |
| 10 | AF11 | 001010 | 0x28 | Assured Forwarding 1-1 | Bulk data, low drop preference. |
| 12 | AF12 | 001100 | 0x30 | Assured Forwarding 1-2 | Bulk data, medium drop preference. |
| 14 | AF13 | 001110 | 0x38 | Assured Forwarding 1-3 | Bulk data, high drop preference. |
| 16 | CS2 | 010000 | 0x40 | Class Selector 2 | OAM, network management traffic. |
| 18 | AF21 | 010010 | 0x48 | Assured Forwarding 2-1 | Transactional data, low drop preference. |
| 20 | AF22 | 010100 | 0x50 | Assured Forwarding 2-2 | Transactional data, medium drop preference. |
| 22 | AF23 | 010110 | 0x58 | Assured Forwarding 2-3 | Transactional data, high drop preference. |
| 24 | CS3 | 011000 | 0x60 | Class Selector 3 | Broadcast video. |
| 26 | AF31 | 011010 | 0x68 | Assured Forwarding 3-1 | Multimedia streaming, low drop preference. |
| 28 | AF32 | 011100 | 0x70 | Assured Forwarding 3-2 | Multimedia streaming, medium drop preference. |
| 30 | AF33 | 011110 | 0x78 | Assured Forwarding 3-3 | Multimedia streaming, high drop preference. |
| 32 | CS4 | 100000 | 0x80 | Class Selector 4 | Real-time interactive. |
| 34 | AF41 | 100010 | 0x88 | Assured Forwarding 4-1 | Interactive video, low drop preference. |
| 36 | AF42 | 100100 | 0x90 | Assured Forwarding 4-2 | Interactive video, medium drop preference. |
| 38 | AF43 | 100110 | 0x98 | Assured Forwarding 4-3 | Interactive video, high drop preference. |
| 40 | CS5 | 101000 | 0xa0 | Class Selector 5 | Broadcast video; telephony signalling. |
| 46 | EF | 101110 | 0xb8 | Expedited Forwarding | VoIP RTP bearer; real-time low-latency traffic. |
| 48 | CS6 | 110000 | 0xc0 | Class Selector 6 | Network control; routing protocols (BGP, OSPF, etc.). |
| 56 | CS7 | 111000 | 0xe0 | Class Selector 7 | Reserved; highest priority. |

---

## Per-Hop Behaviour (PHB) Classes

### Best Effort (BE / CS0)

Default for all traffic that carries no DSCP marking. No guaranteed bandwidth,
delay, or drop behaviour. Traffic is dropped first under congestion.

### Expedited Forwarding (EF — DSCP 46)

Defined in RFC 3246. Provides a low-latency, low-jitter, low-loss forwarding service
with guaranteed bandwidth. Implemented using a strict priority queue. Used for VoIP
RTP audio streams. EF traffic should be policed at ingress to prevent it from
starving other queues.

### Assured Forwarding (AF)

Defined in RFC 2597. Four classes (AF1–AF4), each with three drop precedences:

| Drop Precedence | Meaning | Examples |
| --- | --- | --- |
| 1 (low) | Dropped last under congestion | AF11, AF21, AF31, AF41 |
| 2 (medium) | Dropped second under WRED | AF12, AF22, AF32, AF42 |
| 3 (high) | Dropped first under WRED | AF13, AF23, AF33, AF43 |

Higher drop precedence means more aggressive WRED dropping. Within a class, traffic
at different drop precedences competes for bandwidth — exceeding traffic (e.g. bursts
above committed rate) should be re-marked to a higher drop precedence rather than
dropped immediately.

### Class Selectors (CS0–CS7)

Backwards-compatible with the legacy 3-bit IP Precedence field. CS values set only
the top 3 bits of the DSCP field, leaving the lower 3 bits as zero. CS1 = IP Prec 1,
CS6 = IP Prec 6, and so on.

---

## Cisco DiffServ Trust Boundary

Traffic entering the network should be re-marked at the trust boundary. Markings
from customer or user devices are untrusted and should be reset or re-classified on
ingress.

Mark VoIP traffic EF and all other traffic Best Effort at an ingress interface:

```ios
class-map match-any VOIP-BEARER
 match protocol rtp audio
!
policy-map MARK-INGRESS
 class VOIP-BEARER
  set dscp ef
 class class-default
  set dscp default
!
interface GigabitEthernet0/1
 service-policy input MARK-INGRESS
```

---

## Queuing and Scheduling

### LLQ (Low-Latency Queuing)

LLQ combines CBWFQ (Class-Based Weighted Fair Queuing) with a strict priority queue.
The priority queue (for EF traffic) is serviced first before any bandwidth is
allocated to other classes. Remaining bandwidth is distributed among CBWFQ classes
according to their configured weights or percentages.

```ios

policy-map WAN-QOS
 class VOIP-BEARER
  priority 512           ! Strict priority queue, 512 Kbps maximum
 class CRITICAL-DATA
  bandwidth percent 30   ! 30% of remaining link bandwidth
 class BULK-DATA
  bandwidth percent 20
 class class-default
  fair-queue             ! WFQ for unclassified traffic
!
interface Serial0/0
 service-policy output WAN-QOS
```

### WRED (Weighted Random Early Detection)

WRED probabilistically drops packets before queues fill completely, using the DSCP
drop precedence to determine thresholds. Higher drop precedence (e.g. AF13) begins
dropping at lower queue depths than lower drop precedence (e.g. AF11). This prevents
tail-drop synchronisation and allows TCP flows to back off gradually.

```ios

policy-map WAN-QOS
 class AF1-CLASS
  bandwidth percent 30
  random-detect dscp-based
```

---

## Layer 2 QoS — 802.1p / CoS

The 802.1Q VLAN tag includes a 3-bit **PCP (Priority Code Point)** field, also
called **CoS (Class of Service)**. It carries Layer 2 QoS markings between switches
and must be mapped to DSCP values at Layer 3 boundaries.

| CoS Value | Description | Typical DSCP Mapping |
| --- | --- | --- |
| 0 | Best Effort | CS0 (0) |
| 1 | Background | CS1 (8) |
| 2 | Spare | — |
| 3 | Excellent Effort | AF31 (26) |
| 4 | Controlled Load | AF41 (34) |
| 5 | Video (< 100 ms latency) | CS5 (40) |
| 6 | Voice (< 10 ms latency) | EF (46) |
| 7 | Network Control | CS6 (48) |

CoS and DSCP must be mapped consistently at all trust boundary points. On Cisco IOS,
CoS-to-DSCP mapping tables are applied at trunk interfaces when QoS is enabled.

---

## Notes

- DSCP markings are **advisory** — they express intent, not enforcement. Only

  properly configured queuing and scheduling policies enforce the per-hop behaviour.

- Always **re-mark untrusted ingress traffic**. Customer devices and end-user hosts

  may set arbitrary DSCP values. Reset or re-classify at the access edge.

- **EF traffic must be rate-limited (policed) at ingress.** Without policing, a

  misbehaving EF-marked flow can starve all other traffic classes by monopolising
  the strict priority queue.

- On **FortiGate**, traffic shaping uses DSCP values for classification under

  `config firewall shaper` and `config firewall shaping-policy`. DSCP marking can
  be applied per-policy.

- `show policy-map interface <interface>` on Cisco IOS displays per-class packet and

  byte counts, queue depth, and drop statistics. Use this to verify QoS policy
  operation.

- The **ECN bits** (bits 1–0 of the ToS byte) are independent of DSCP and provide

  end-to-end congestion signalling between ECN-capable endpoints. Do not confuse ECN
  with DSCP when reading packet captures.
