# VRRP (Virtual Router Redundancy Protocol)

Virtual Router Redundancy Protocol provides gateway redundancy by allowing multiple routers
to share a virtual IP address. VRRP automatically elects a Master router; if it fails, a Backup
takes over with minimal traffic loss.

## Overview

- **Layer:** Network (Layer 3)
- **IP Protocol Number:** 112
- **Destination IP:** 224.0.0.18 (all VRRP routers)
- **Purpose:** Gateway redundancy and failover
- **Versions:** VRRPv2 (IPv4, RFC 3768), VRRPv3 (IPv4/IPv6, RFC 5798)
- **Advertisement interval:** 1 second (default)

---

## VRRPv2 Packet Format

```text
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Version| Type  |   Virtual Rtr ID   |  Priority    | Count IP |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|       Auth Type        |   Adver Int    |   Checksum        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    IP Address (VRRP VIP)                     |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    IP Address (Optional, repeat)             |
|                                                                 |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|   Authentication Data (optional, 8 bytes, deprecated)        |
|                                                                 |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### Field Descriptions

| Field | Bits | Purpose |
| --- | --- | --- |
| **Version** | 4 | VRRP version (2 for VRRPv2, 3 for VRRPv3) |
| **Type** | 4 | 1=Advertisement |
| **VRID** | 8 | Virtual Router ID (1-255); identifies group |
| **Priority** | 8 | Election priority: 0-254 (0=stop, 255=owner); higher=preferred |
| **Count IP** | 8 | Number of IP addresses in packet |
| **Auth Type** | 8 | Deprecated (should be 0) |
| **Adver Int** | 8 | Advertisement interval in seconds |
| **Checksum** | 16 | VRRP packet checksum |
| **IP Address** | 32 | Virtual IP (VRRP VIP) or secondary addresses |

---

## VRRP Election Process

```mermaid
sequenceDiagram
    participant RouterA as Router A<br/>(Priority 100)
    participant RouterB as Router B<br/>(Priority 50)
    RouterA->>RouterB: VRRP Advertisement<br/>(Priority 100)
    Note over RouterB: Compare priorities<br/>50 < 100
    RouterB->>RouterA: VRRP Advertisement<br/>(Priority 50)
    Note over RouterA: A elected MASTER
    Note over RouterB: B becomes BACKUP
    Note over RouterA,RouterB: All hosts use VRRP VIP<br/>as gateway (Router A)
```

---

## Priority Values

| Priority | Role | Meaning |
| --- | --- | --- |
| **255** | Owner | Router owns the VRRP VIP; highest priority always |
| **200-254** | Master candidate | Will win election among non-owners |
| **1-199** | Backup candidate | Lower priority in election |
| **0** | Disabled | Router stops participating in VRRP group |

**Owner:** A router configured with the VRRP VIP as a real interface IP is the "owner" (priority 255).

---

## VRRP Timers

| Timer | Default | Meaning |
| --- | --- | --- |
| **Advertisement Interval** | 1 second | Master sends VRRP advertisements every 1s |
| **Master Down Interval** | 3 × adver int = 3s | Backup waits 3 seconds for Master advert before taking over |
| **Skew Time** | (256 - Priority) / 256 seconds | Prevents thundering herd on failover |

**Failover scenario:**

```text
T=0s: Master fails
T=1s: Backup misses 1st advertisement
T=2s: Backup misses 2nd advertisement
T=3s: Master Down Interval expires → Backup becomes MASTER
      All hosts now use Backup's MAC for VRRP VIP
      Traffic flows resume
```

---

## VRRP MAC Address

Virtual MAC derived from VRID:

```text
VRRP MAC: 00:00:5E:00:01:VRID

Example: VRRP group ID 10
MAC: 00:00:5E:00:01:0A

All routers in group use same MAC; ARP resolves VRRP VIP to this MAC.
Master router "owns" the MAC (responds to ARP).
Backup ignores ARP for VRRP VIP.
```

---

## VRRP State Machine

```mermaid
stateDiagram-v2
    [*] --> INITIALIZE
    INITIALIZE --> ELECTION: Start
    ELECTION: Compare Priority & VRID<br/>Higher = MASTER<br/>Lower = BACKUP
    ELECTION --> MASTER
    ELECTION --> BACKUP

    MASTER: Send adv every 1s
    BACKUP: Wait for adv / 3s

    MASTER --> BACKUP: Failure detected<br/>(priority < advertised)<br/>(no adv for 3s)
    BACKUP --> MASTER: Recovery<br/>(higher priority advertised)
```

---

## VRRP VIP Ownership

```mermaid
graph TD
    subgraph Scenario1["Scenario 1: Non-Owner Router (Backup)"]
        A["eth0: 10.1.1.2/24<br/>(Real IP)"]
        B["VRRP VIP: 10.1.1.1<br/>(Configured, not on real interface)"]
        C["Role: Potential MASTER<br/>Priority: 200"]
    end

    subgraph Scenario2["Scenario 2: Owner Router (MASTER)"]
        D["eth0: 10.1.1.1/24<br/>(Real IP = VRRP VIP)"]
        E["VRRP VIP: 10.1.1.1<br/>(Same as interface)"]
        F["Role: Always MASTER<br/>Priority: 255 (automatic)"]
    end

    A --> B --> C
    D --> E --> F
```

**Owner always wins:** A router with VRRP VIP as a real interface IP cannot lose the MASTER role.

---

## Common Deployment Patterns

### Active-Backup (Single VRRP Group)

```mermaid
graph TD
    A["Router A: Priority 200"]
    B["Router B: Priority 100"]
    A -->|Initially| MASTER["MASTER"]
    B -->|Initially| BACKUP["BACKUP"]
    MASTER -->|If A fails| X["B becomes MASTER"]
    X -->|If A recovers| Y["A becomes MASTER<br/>(preempt enabled)"]
    MASTER -.-> Y
```

### Active-Active (Multiple VRRP Groups)

```mermaid
graph TD
    RA["Router A"]
    RB["Router B"]

    RA --> G1A["VRRP Group 1<br/>Priority 200<br/>= MASTER"]
    RA --> G2A["VRRP Group 2<br/>Priority 100<br/>= BACKUP"]

    RB --> G1B["VRRP Group 1<br/>Priority 100<br/>= BACKUP"]
    RB --> G2B["VRRP Group 2<br/>Priority 200<br/>= MASTER"]

    G1A -.->|Load balancing| SPLIT["Traffic split between<br/>A Group 1 & B Group 2"]
    G2B -.->|Failover| SPLIT
```

---

## VRRP vs HSRP vs GLBP

| Feature | VRRP | HSRP | GLBP |
| --- | --- | --- | --- |
| **Standard** | Open (IEEE) | Proprietary (Cisco) | Proprietary (Cisco) |
| **Load balancing** | No | No | Yes (all routers active) |
| **VIP ownership** | Can be shared | Cannot | Can be shared |
| **Failover time** | ~3 seconds | ~3 seconds | ~3 seconds |
| **IPv6 support** | VRRPv3 yes | No | No |
| **Complexity** | Low | Low | Higher |

---

## Common Issues

| Issue | Cause | Fix |
| --- | --- | --- |
| **Both routers MASTER** | Different VRID numbers; different groups | Verify VRID matches on both routers |
| **Slow failover** | Advertisement interval too long | Reduce to 1 second |
| **Rapid flapping** | Preempt enabled; priorities keep changing | Disable preempt or stabilize priorities |
| **VRRP VIP unreachable** | Master's MAC not responding to ARP | Verify VRRP enabled and running |

---

## References

- RFC 5798: Virtual Router Redundancy Protocol (VRRPv3)
- RFC 3768: Virtual Router Redundancy Protocol (VRRPv2)

---

## Next Steps

- See [HSRP vs VRRP Theory](../theory/hsrp_vs_vrrp.md) comparison
- Configure VRRP: [Cisco HSRP & VRRP](../cisco/cisco_hsrp_vrrp.md), [FortiGate VRRP](../fortigate/fortigate_vrrp.md)
