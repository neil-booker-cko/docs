# PTP (Precision Time Protocol)

Precision Time Protocol provides sub-microsecond clock synchronization for time-sensitive
applications
in local networks. PTP is used in data centers, high-frequency trading, telecom, and industrial
automation
where nanosecond-level accuracy is critical.

## Quick Reference

| Property | Value |
| --- | --- |
| **OSI Layer** | Application (Layer 7), with L2/L1 hardware timestamps |
| **Transport Protocol** | UDP ports 319 (events), 320 (general); Ethernet 0x88F7 |
| **RFC/Standard** | IEEE 1588-2008 (PTPv2), IEEE 1588-2002 (PTPv1) |
| **Typical Accuracy** | 1-100 nanoseconds (with hardware support) |
| **Common Use Cases** | High-frequency trading, telecom, data centers, industrial automation |

## Packet Structure

### PTPv2 Sync Message (Master → Slave)

```mermaid

---
title: "PTPv2 Sync Message Header"

---
packet-beta
0-3: "transportSpecific"
4-7: "messageType"
8-15: "reserved"
16-23: "versionPTP"
24-39: "messageLength"
40-47: "domainNumber"
48-55: "reserved"
56-63: "flags"
64-127: "correctionField"
128-159: "reserved32"
160-223: "clockIdentity"
224-239: "sourcePortNumber"
240-255: "sequenceId"
256-271: "controlField"
272-279: "logMessageInterval"
280-343: "originTimestamp"
```

### Follow_Up Message (Master → Slave, after Sync)

Contains precise timestamp of the Sync message transmission (hardware-captured).

### Delay_Req Message (Slave → Master)

Slave requests round-trip delay measurement.

### Delay_Resp Message (Master → Slave)

Master responds with receive timestamp of Delay_Req.

## Field Reference (Common Header)

| Field | Bits | Description |
| --- | --- | --- |
| **transportSpecific** | 4 | PTP transport specification |
| **messageType** | 4 | Message type (0=Sync, 1=Delay_Req, 2=Pdelay_Req, etc.) |
| **versionPTP** | 4 | PTP version (2 for PTPv2) |
| **messageLength** | 16 | Total message length in bytes |
| **domainNumber** | 8 | PTP domain (0-127) |
| **flags** | 8 | Control flags (leap second, frequency traceable, etc.) |
| **correctionField** | 64 | Cumulative correction for residence time |
| **clockIdentity** | 64 | Originating clock's unique identity |
| **sourcePortNumber** | 16 | Port number on source device |
| **sequenceId** | 16 | Sequence number for this message |
| **controlField** | 8 | Control field (0=Sync, 1=Delay_Resp, 2=Follow_Up, etc.) |
| **logMessageInterval** | 8 | Log2 of mean time between messages |

## PTPv2 Message Types

| Type | Direction | Purpose |
| --- | --- | --- |
| **Sync (0x00)** | Master → Slave | Send time; slave adjusts clock |
| **Delay_Req (0x01)** | Slave → Master | Request round-trip delay |
| **Pdelay_Req (0x02)** | Peer → Peer | Peer delay measurement (P2P mode) |
| **Pdelay_Resp (0x03)** | Peer → Peer | Respond to peer delay request |
| **Follow_Up (0x08)** | Master → Slave | Precise Sync transmit timestamp |
| **Delay_Resp (0x09)** | Master → Slave | Respond to Delay_Req with RX time |
| **Pdelay_Resp_FollowUp (0x0A)** | Peer → Peer | Peer delay follow-up |
| **Announce (0x0B)** | Master → All | Master availability; priority |
| **Signaling (0x12)** | Both directions | Request/grant subscriptions |
| **Management (0x0D)** | Both directions | Administrative queries |

## PTP Synchronization Process (Slave Perspective)

```mermaid
sequenceDiagram
    participant Master
    participant Slave
    Master->>Slave: Sync (T1)<br/>Software timestamp
    Note over Slave: Received at T2
    Slave->>Master: Delay_Req (T3)<br/>Request RTT measurement
    Note over Master: Received at T4
    Master->>Slave: Follow_Up<br/>Precise T1' (hardware TX)
    Master->>Slave: Delay_Resp<br/>T4' (hardware RX)
    Note over Slave: Calculate:<br/>Offset = ((T2-T1')+(T4'-T3))/2<br/>Delay = (T4-T3)-(T2-T1')<br/>Adjust clock by offset
```

**Key advantage:** Hardware timestamps on Follow_Up and Delay_Resp provide
picosecond precision.

## PTP Modes

### Master-Slave (E2E — End-to-End)

Traditional mode: slave requests delay from master.

```mermaid
graph TD
    GrandMaster["Master<br/>(Grandmaster)"]
    Slave["Slave"]
    GrandMaster -->|Sync/Follow_Up| Slave
    GrandMaster -->|Delay_Resp| Slave
    Slave -->|"(Adjusts clock)"| Slave
```

### Peer-to-Peer (P2P)

Direct peer measurement; reduces hop latency; useful for daisy-chained networks.

```mermaid
graph LR
    DeviceA["Device A"]
    DeviceB["Device B"]
    DeviceC["Device C"]
    DeviceA <-->|Pdelay<br/>measurement| DeviceB
    DeviceB <-->|Pdelay<br/>measurement| DeviceC
    DeviceA -.->|Peer delay| DeviceC
```

## PTP Clock Classes & Grandmaster Selection

| Class | Accuracy | Source | Example |
| --- | --- | --- | --- |
| **6** | ±100 ns | PTP master | Precision time server |
| **7** | ±250 ns | GPS/Cesium-backed | Primary clock |
| **13** | ±10 µs | Filtered NTP | Secondary clock |
| **52** | ±1 ms | NTP (application) | Fallback timing |
| **187** | ±100 ms | No synchronization | Local free-running clock |
| **255** | Unknown | Undetermined | Clock not ready |

**Grandmaster Selection:** Grandmasters (masters) are elected based on best clock
class, accuracy, and priority.

## PTP Hardware Support

To achieve nanosecond accuracy, PTP requires:

1. **Hardware Timestamp Registers:** Network interface captures exact TX/RX times
1. **Sync Pulse:** Often outputs PPS (pulse-per-second) signal for external devices
1. **Oscillator Quality:** Local oscillator must be stable (GPS-disciplined preferred)

Modern enterprise switches and NICs include PTP support:

- Cisco switches: `ptp server` / `ptp client`
- Mellanox NICs: DPDK integration for PTP
- Intel/Broadcom NICs: Firmware support for hardware timestamps

## Ethernet-Based PTP (Layer 2)

PTP can run directly over Ethernet (EtherType 0x88F7) without UDP/IP overhead for
even lower latency.

```text
Ethernet Frame:
| DA | SA | EtherType (0x88F7) | PTP Message | FCS |
                                  ← Direct encapsulation
```

Advantages:

- Lower latency (no IP/UDP stack processing)
- Deterministic timestamps (no ARP, DHCP, etc.)
- Can synchronize network infrastructure itself

## Notes & Common Issues

| Issue | Cause | Fix |
| --- | --- | --- |
| **Poor accuracy** | No hardware timestamps | Enable PTP hardware assist in NIC firmware |
| **Master not elected** | Announce messages blocked | Check firewall rules for UDP 319/320 |
| **Slave won't sync** | Clock class mismatch or priority | Verify Grandmaster election and domain |
| **Asymmetric delay** | Network switch without PTP support | Deploy PTP-aware switches (transparent clock) |

## References

- IEEE 1588-2008: Precision Clock Synchronization Protocol

## Next Steps

- Read [NTP](ntp.md) for wide-area clock synchronization
- See [NTP vs PTP](../theory/ntp_vs_ptp.md) comparison for deployment decisions
- Configure PTP on enterprise switches and routers (vendor-specific guides)
