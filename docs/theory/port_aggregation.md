# Port Aggregation (LAG/EtherChannel) Fundamentals

Port aggregation combines multiple physical links into a single logical link for higher
bandwidth and redundancy.

## Core Concepts

### What is Port Aggregation?

Multiple physical ports are bundled into a **Link Aggregation Group (LAG)** or **Port
Channel**, appearing as a single interface to routing protocols.

```text
Physical view:
  Port 1: 1 Gbps ─┐
  Port 2: 1 Gbps ─┼─ Combined
  Port 3: 1 Gbps ─┘

Logical view:
  Port Channel 1: 3 Gbps
```

### Benefits

| Benefit | Use Case |
| --- | --------- |
| **Bandwidth aggregation** | 4× 1 Gbps ports = 4 Gbps throughput |
| **Redundancy** | If one port fails, others still carry traffic |
| **Load balancing** | Traffic distributed across member ports |
| **Simplified configuration** | Single IP address, single routing cost |

---

## How It Works

### Member Port Selection

When sending a frame, the LAG algorithm hashes the source/destination MAC (and optionally IP) to select
which member port to use.

```text

Frame arrives: SRC_MAC=AA:AA:AA:AA:AA:AA, DST_MAC=BB:BB:BB:BB:BB:BB

Hash function: (SRC_MAC + DST_MAC) mod (number of members)
Result: Port 2 selected

Frame sent on Port 2
```

**Key point:** All frames between same source and destination use the same port (per-flow consistency).

### Redundancy and Failover

```text

Port 1: ACTIVE (forwarding traffic)
Port 2: ACTIVE (forwarding traffic)
Port 3: ACTIVE (forwarding traffic)

Port 2 fails → traffic on Port 2 is rehashed to Port 1 or 3
Remaining ports continue forwarding
No packet loss (ideally)
```

---

## LAG Protocol Standards

### LACP (Link Aggregation Control Protocol) — IEEE 802.3ad

Automatic negotiation of LAG membership. Both sides must agree to form LAG.

**Advantages:**

- Automatic detection of misconfigurations
- Can form/break LAG dynamically
- Widely supported (recommended)

**Negotiation process:**

```text

Switch A sends LACP BPDU: "I want to aggregate ports 1–4"
   ↓
Switch B receives LACP BPDU: "Agreed, forming LAG"
   ↓
LAG is active; traffic flows across all 4 ports
```

### Static LAG (no protocol)

Manual configuration; no automatic negotiation.

**Disadvantages:**

- No detection if ports are misconfigured
- Both sides must be manually configured identically
- Avoid unless LACP unavailable

---

## Load Balancing Algorithm

How frames are distributed across member ports.

### Hash Types (Varies by Vendor)

| Algorithm | Hashes | Use Case |
| --- | --------- | --- |
| **MAC-based** | Source & dest MAC | Layer 2 switching |
| **IP-based** | Source & dest IP | Layer 3 routing |
| **Port-based** | Source & dest IP + port | Most balanced (default) |

**Implication:** If all traffic is between same source/destination, it uses one port.
LAG does NOT guarantee even traffic distribution.

```text

Example: Server uploading to single client
  All traffic: SRC=Server, DST=Client → always hashes to Port 1
  Result: Port 1 fully utilized (1 Gbps), Ports 2–4 idle

This is normal behavior; LAG balances across many flows, not within a single flow.
```

---

## Configuration Patterns

### Access Link (Single VLAN)

```text

Switch A                    Switch B
Port 1 ──┐                ┌─ Port 1
Port 2 ──┼─ LAG1 ───────── LAG1 ─┼─ Port 2
Port 3 ──┘                └─ Port 3

VLAN 100: 192.168.1.0/24
```

Both switches form LAG on ports 1–3. All traffic on one VLAN carries over LAG.

### Trunk Link (Multiple VLANs)

```text

Switch A                    Switch B
Port 48 ─┐                 ┐─ Port 48
Port 49 ─┼─ LAG1 ──────── LAG1 ─┼─ Port 49
         └─ (Tagged)  (Tagged)─┘

VLANs: 1, 100, 200, 300
```

LAG carries multiple VLANs (802.1Q tagged). All VLANs flow across all member ports.

---

## Failure Scenarios

### Scenario 1: Single Port Fails

```text

Before: Port 1, 2, 3 active (3 Gbps total)
        Traffic distributed: ~1 Gbps each

Port 2 cable unplugged:
        LACP detects port down
        Traffic rehashed: ~1.5 Gbps on Ports 1 & 3
        No packet loss (drops possible during rehash)
```

### Scenario 2: Entire Switch Fails

```text

Before: Switch A ←LAG→ Switch B

Switch B power failure:
        LACP hello timeout (3x hello interval)
        Switch A marks LAG as down
        All traffic reroutes via alternate path (if available)
```

---

## Design Best Practices

| Practice | Reason |
| --- | --------- |
| **Use LACP** | Automatic negotiation, detection of misconfig |
| **Even number of ports** | Simplifies load balancing math |
| **4 ports max** | More than 4 provides diminishing returns; overkill |
| **Same speed ports** | 1 Gbps + 10 Gbps in same LAG causes issues |
| **Same type cables** | Avoid mixing copper/fiber in same LAG |
| **Configure both sides** | If only one side configured, will not form LAG |
| **Monitor LAG health** | Track which ports are active in LAG |
| **Document LAG mapping** | Facilitate troubleshooting |

---

## Vendor Terminology

| Vendor | Term | Standard |
| --- | --------- | --- |
| **Cisco** | EtherChannel | LACP or Static (PAgP) |
| **Arista** | Port Channel | LACP or Static |
| **Juniper** | Aggregated Ethernet | LACP or Static |
| **FortiGate** | Aggregated Interface / Trunk | LACP or Static |

---

## Troubleshooting Checklist

| Check | Command | Look For |
| --- | --------- | --- |
| Is LAG active? | `show port-channel summary` | "Po1 (SU)" = up |
| How many ports active? | `show port-channel 1 detail` | "Active" vs "Suspended" |
| Are protocols enabled? | `show lacp summary` | LACP enabled on both sides |
| Port errors? | `show interface` | CRC errors, runts, collisions |
| VLAN mismatch? | `show vlan` | All VLANs on both ends? |

---

## Summary

- **Port Aggregation (LAG)** combines physical ports into logical bundles
- **LACP** (recommended) provides automatic negotiation and failure detection
- **Load balancing** distributes traffic across member ports based on hash
- **Redundancy** ensures traffic continues if individual ports fail
- **Same speed/type** ports prevent configuration issues
- **Monitor health** regularly to catch port failures early
