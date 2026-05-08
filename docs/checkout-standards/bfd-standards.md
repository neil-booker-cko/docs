# BFD (Bidirectional Forwarding Detection) Standards

Mandatory BFD configuration for sub-second failover detection on critical routing and HA
links.

---

## BFD Overview

**Standard:** BFD is **mandatory** on all:

- BGP neighbor links (routing protocol detection)
- OSPF links (routing protocol detection)
- HA heartbeat links (failover detection)
- Static routing failover links

BFD provides sub-second failure detection independent of routing protocol timers, enabling
failover in <1 second.

---

## BFD Mandatory Scenarios

| Scenario | BFD Required | Purpose | Failover Time |
| --- | --- | --- | --- |
| BGP neighbor (any VRF) | Yes | Immediate neighbor down detection | 300-900ms |
| OSPF adjacency | Yes | Link failure before hello timeout | 300-900ms |
| HA heartbeat (VSS/vPC) | Yes | Primary/standby link failure | <100ms |
| Static route failover | Yes | Detect primary path down | <1 second |
| Redundant uplink (ISP) | Yes | Detect ISP path failure | <1 second |

---

## BFD Timers (Standard Configuration)

**Standard Timers for All Links:**

| Parameter | Value | Notes |
| --- | --- | --- |
| Transmit Interval | 300ms | Send BFD packets every 300ms |
| Receive Interval | 300ms | Expect BFD packets every 300ms |
| Multiplier | 3 | Detect down after 3 missed packets (900ms) |
| **Effective Detection Time** | **900ms** | 300ms × 3 = down after 900ms |

**Rationale:** 300ms interval with 3x multiplier provides ~900ms detection time
(sub-second), suitable for all Checkout datacenters and offices. More aggressive timers
(100ms) risk false positives on congested links.

---

## Cisco IOS-XE BFD Configuration

### Interface-Level BFD (All Links)

**Mandatory on all routing interfaces:**

```ios
interface GigabitEthernet0/0
 description BGP-Link-to-AWS-TGW
 ip address 169.254.1.1 255.255.255.252
 bfd interval 300 min_rx 300 multiplier 3
 no shutdown
!
```

### BGP BFD Configuration (Mandatory)

**Per-neighbor BFD enablement:**

```ios
router bgp 65000
 neighbor 169.254.1.2 remote-as 65300
 neighbor 169.254.1.2 timers 60 180
 neighbor 169.254.1.2 fall-over bfd
!
```

**BFD timers with BGP:**

- BGP keepalive: 60 seconds (BFD detects failures, BGP holds connection longer)
- BGP hold time: 180 seconds (allows BFD time to recover from transients)
- BFD detection: 300ms interval, 900ms down time

### OSPF BFD Configuration (Mandatory)

**Per-interface BFD enablement:**

```ios
interface GigabitEthernet0/0
 ip address 10.0.0.1 255.255.255.252
 ip ospf 1 area 0
 bfd interval 300 min_rx 300 multiplier 3
 ip ospf fall-over bfd
!
```

**OSPF timers with BFD:**

- OSPF hello: 30 seconds (BFD handles fast detection)
- OSPF dead: 120 seconds (longer dead interval with BFD)
- BFD detection: 300ms interval, 900ms down time

### HA Heartbeat BFD (VSS/vPC)

**VSS heartbeat link BFD:**

```ios
interface GigabitEthernet0/1
 description VSS-Heartbeat
 no ip address
 bfd interval 100 min_rx 100 multiplier 3
 no shutdown
!

switch virtual domain 1
 switch 1
  priority 110
  preempt delay 180
  sync enabled
 exit
 peer switch
  ip address 10.0.0.2
 exit
!
```

**HA BFD timers (more aggressive):**

- Transmit: 100ms
- Receive: 100ms
- Multiplier: 3
- Detection time: 300ms (faster failover for HA)

### Static Route Failover BFD

**BFD tracking for static route failover:**

```ios
ip route 10.1.0.0 255.255.0.0 10.0.0.2 20 track 1

track 1 rtr 1 reachability
 rtr 1 type echo protocol ipIcmpEcho 10.0.0.2
  timeout 1000
  frequency 3
!
```

---

## FortiGate BFD Configuration

### Interface BFD (All Uplinks)

```fortios
config system interface
    edit "port1"
        set ip 169.254.1.1 255.255.255.252
        set allowaccess ping https ssh snmp http telnet
        set type physical
        set bfd enable
        set bfd desired-min-tx 300
        set bfd required-min-rx 300
        set bfd detect-mult 3
    next
end
```

### BGP BFD (FortiOS)

```fortios
config router bgp
    set as 65000
    set router-id 10.0.0.1
    config neighbor
        edit "169.254.1.2"
            set remote-as 65300
            set bfd enable
            set timers-connect 10
            set timers-hold 30
            set timers-keepalive 10
        next
    end
end
```

### OSPF BFD (FortiOS)

```fortios
config router ospf
    set router-id 10.0.0.1
    config ospf interface
        edit "port1"
            set interface "port1"
            set bfd enable
            set hello-interval 30
            set dead-interval 120
        next
    end
end
```

---

## BFD Verification

### Cisco IOS-XE Verification

```ios
show bfd neighbors
show bfd neighbors details
show bfd interface GigabitEthernet0/0
debug bfd packet
```

**Expected output:**

```text
NeighAddr       LD/RD       RH/RS       State     Int
169.254.1.2     1/1         Up/Up       Up        Gi0/0
10.0.0.2        2/2         Up/Up       Up        Gi0/1
```

### FortiGate Verification

```fortios
diagnose ip neighbor list
diagnose routing bgp neighbors
get router bgp neighbor
```

---

## BFD Best Practices

### Configuration Checklist

- ✅ Enable BFD on all routing interfaces (BGP, OSPF)
- ✅ Enable BFD on all HA heartbeat links
- ✅ Use standard 300ms interval (100ms only for HA heartbeats)
- ✅ Use multiplier 3 (900ms detection time)
- ✅ Configure on both ends of link
- ✅ Test failover after deployment
- ✅ Monitor BFD state transitions in syslog

---

### Tuning BFD Timers

**Conservative (production datacenters):**

- Interval: 300ms
- Multiplier: 3
- Detection: 900ms

**Aggressive (HA heartbeats):**

- Interval: 100ms
- Multiplier: 3
- Detection: 300ms

**Do NOT use:**

- Interval < 100ms (CPU intensive)
- Multiplier < 3 (false positives on congested links)
- Different timers on different ends (must match)

---

### Troubleshooting

| Issue | Cause | Resolution |
| --- | --- | --- |
| BFD session down | Interface down, no connectivity | Check physical link; verify IP connectivity |
| BFD flapping | Congestion, timing mismatch | Increase interval; verify timers match both ends |
| High CPU | Too many BFD sessions or aggressive timers | Increase interval or reduce number of BFD sessions |
| Routing instability | BFD down while routing alive | Increase multiplier; add redundant links |

---

## Related Standards

- [BGP Standards](bgp-standards.md) — BGP BFD configuration
- [OSPF Standards](ospf-standards.md) — OSPF BFD configuration
- [HA Standards](ha-standards.md) — HA heartbeat BFD
- [Interface Configuration](interface-standards.md) — Interface-level BFD
