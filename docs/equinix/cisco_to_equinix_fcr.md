# Cisco to Equinix FCR Integration Guide

Complete reference for connecting Cisco IOS-XE routers to Equinix Fabric Cloud Router for cloud
and datacenter interconnection.

## Quick Start: Cisco to FCR (Single Cloud)

```ios
configure terminal

! BGP configuration
router bgp 65000
  bgp router-id 10.0.0.1

  ! Peer with FCR
  neighbor 10.255.1.2 remote-as 65001
  neighbor 10.255.1.2 timers 3 9 0

  address-family ipv4
    neighbor 10.255.1.2 activate
    network 10.0.0.0 mask 255.0.0.0
  exit-address-family

end
```

**Verify:**

```text
show bgp ipv4 unicast summary
! Expect: Established status
```

---

## Detailed Integration Scenarios

## Scenario 1: Single Cisco Router to FCR (Hub-and-Spoke Cloud)

### Network Diagram

```text
Cisco Router (DC)
  10.0.0.1 (iBGP peer)
  10.0.0.0/8 (local subnets)
        |
    BGP eBGP (AS 65000 ↔ AS 65001)
        |
  Equinix FCR-A (SJC metro)
    10.255.1.2 (BGP peer)
    AS 65001
        |
    Multi-cloud routing
        |
    ┌─────┴─────┬──────────┐
    |           |          |
  AWS        Azure      GCP
  16509      8075      15169
```

### Cisco Configuration

```ios
configure terminal

router bgp 65000
  bgp router-id 10.0.0.1
  bgp log-neighbor-changes

  ! Primary FCR peering
  neighbor 10.255.1.2 remote-as 65001
  neighbor 10.255.1.2 description "Equinix FCR Primary (SJC)"
  neighbor 10.255.1.2 timers 3 9 0
  neighbor 10.255.1.2 password encrypted [ENCRYPTED_PASSWORD]

  address-family ipv4
    neighbor 10.255.1.2 activate
    neighbor 10.255.1.2 soft-reconfiguration inbound

    ! Advertise local DC subnets
    network 10.0.0.0 mask 255.0.0.0
    network 10.1.0.0 mask 255.255.0.0
    network 10.2.0.0 mask 255.255.0.0

    ! Optional: Aggregate routes before advertising to FCR
    aggregate-address 10.0.0.0 255.0.0.0

  exit-address-family

end
```

### Verification

```text
show bgp ipv4 unicast summary
! Status should show: Established

show bgp ipv4 unicast neighbors 10.255.1.2
! Details: uptime, messages sent/received, timers

show bgp ipv4 unicast
! Show all routes learned (from AWS, Azure, GCP via FCR)
```

---

## Scenario 2: Dual Cisco Router (iBGP) to FCR (Redundancy)

### Network Diagram

```text
Cisco Router-A (primary)        Cisco Router-B (backup)
  10.0.0.1                        10.0.0.2
  iBGP (AS 65000)                 iBGP (AS 65000)
        |                                |
        └────────iBGP────────────────────┘

        BGP eBGP (to FCR)

  Equinix FCR-A
    10.255.1.2 (peered with Router-A and Router-B)
    AS 65001
        |
    AWS/Azure/GCP
```

### Router-A Configuration

```ios
configure terminal

router bgp 65000
  bgp router-id 10.0.0.1

  ! Internal peering (Router-B)
  neighbor 10.0.0.2 remote-as 65000
  neighbor 10.0.0.2 description "Router-B (internal)"
  neighbor 10.0.0.2 timers 1 3 0  ! Fast convergence for internal

  ! External peering (FCR)
  neighbor 10.255.1.2 remote-as 65001
  neighbor 10.255.1.2 description "Equinix FCR"
  neighbor 10.255.1.2 timers 3 9 0

  address-family ipv4
    neighbor 10.0.0.2 activate
    neighbor 10.255.1.2 activate
    neighbor 10.255.1.2 soft-reconfiguration inbound

    ! Local routes
    network 10.0.0.0 mask 255.0.0.0

  exit-address-family

end
```

### Router-B Configuration

```ios
configure terminal

router bgp 65000
  bgp router-id 10.0.0.2

  ! Internal peering (Router-A)
  neighbor 10.0.0.1 remote-as 65000
  neighbor 10.0.0.1 description "Router-A (internal)"
  neighbor 10.0.0.1 timers 1 3 0

  ! External peering (FCR)
  neighbor 10.255.1.2 remote-as 65001
  neighbor 10.255.1.2 description "Equinix FCR"
  neighbor 10.255.1.2 timers 3 9 0

  address-family ipv4
    neighbor 10.0.0.1 activate
    neighbor 10.255.1.2 activate
    neighbor 10.255.1.2 soft-reconfiguration inbound

    ! Same local routes on both
    network 10.0.0.0 mask 255.0.0.0

  exit-address-family

end
```

### Verification

```text
Router-A:
  show bgp ipv4 unicast summary
  ! Should see both neighbors: 10.0.0.2 (iBGP) and 10.255.1.2 (eBGP)

  show bgp ipv4 unicast
  ! Routes from AWS/Azure/GCP received via FCR
  ! Best path chosen (Router-A or Router-B based on distance)
```

---

## Scenario 3: Multi-Metro FCR with Dual Routers (Maximum Redundancy)

### Network Diagram

```text
Router-A (DC-A)      Router-B (DC-B)
  10.0.0.1             10.0.0.2
        |                    |
        └─iBGP ─────────────┘

  eBGP (AS 65000)      eBGP (AS 65000)
        |                    |
        |                    |
    ┌───▼────┐          ┌────▼───┐
    │ FCR-A  │←iBGP────→│ FCR-B  │
    │(SJC)   │          │(LAX)   │
    └────────┘          └────────┘
        |                    |
        |                    |
    AWS (dual peering)
```

### Router-A Configuration

```ios
configure terminal

router bgp 65000
  bgp router-id 10.0.0.1

  ! Internal iBGP
  neighbor 10.0.0.2 remote-as 65000
  neighbor 10.0.0.2 description "Router-B"
  neighbor 10.0.0.2 timers 1 3 0

  ! Primary FCR (SJC)
  neighbor 10.255.1.2 remote-as 65001
  neighbor 10.255.1.2 description "FCR-A (SJC, primary)"
  neighbor 10.255.1.2 timers 3 9 0

  ! Secondary FCR (LAX) for redundancy
  neighbor 10.255.2.2 remote-as 65001
  neighbor 10.255.2.2 description "FCR-B (LAX, secondary)"
  neighbor 10.255.2.2 timers 3 9 0

  address-family ipv4
    neighbor 10.0.0.2 activate
    neighbor 10.255.1.2 activate
    neighbor 10.255.1.2 soft-reconfiguration inbound
    neighbor 10.255.2.2 activate
    neighbor 10.255.2.2 soft-reconfiguration inbound

    ! Local routes
    network 10.0.0.0 mask 255.0.0.0

    ! Prefer primary FCR (SJC) via local preference
    route-map PRIMARY_FCR permit 10
      set local-preference 200
    route-map SECONDARY_FCR permit 10
      set local-preference 100

    neighbor 10.255.1.2 route-map PRIMARY_FCR in
    neighbor 10.255.2.2 route-map SECONDARY_FCR in

  exit-address-family

end
```

### Failover Behavior

```text
Normal operation:
  Router-A → FCR-A (SJC, primary) → AWS
  Traffic via primary, secondary available

FCR-A failure:
  BGP detects neighbor down (3s + 9s holdtime = ~12s)
  Routes shift to FCR-B (LAX, secondary)
  Full convergence: ~15 seconds
```

---

## Scenario 4: Cisco to FCR + Direct Cloud Connections (Hybrid)

### Network Diagram

```text
Cisco Router (DC)
  10.0.0.1
  AS 65000
        |
      BGP eBGP
        |
    Equinix FCR
      AS 65001
        |
        ├─→ AWS (via vConnection)
        └─→ Azure (via vConnection)

Optional: Direct connection to GCP (AWS Direct Connect, bypassing FCR)
        |
        ├─→ GCP (direct, not via FCR)
```

### Cisco Configuration (FCR + Direct Connection)

```ios
configure terminal

router bgp 65000
  bgp router-id 10.0.0.1

  ! Peer with FCR (for AWS, Azure)
  neighbor 10.255.1.2 remote-as 65001
  neighbor 10.255.1.2 description "Equinix FCR (AWS + Azure)"
  neighbor 10.255.1.2 timers 3 9 0

  ! Direct connection to GCP (different link, e.g., ISP)
  neighbor 203.0.113.1 remote-as 15169
  neighbor 203.0.113.1 description "GCP Direct Connection"
  neighbor 203.0.113.1 timers 10 30 0

  address-family ipv4
    neighbor 10.255.1.2 activate
    neighbor 10.255.1.2 soft-reconfiguration inbound
    neighbor 203.0.113.1 activate

    ! Local routes
    network 10.0.0.0 mask 255.0.0.0

  exit-address-family

end
```

---

## Advanced Configurations

### BGP Community-Based Traffic Steering

Control traffic flow based on communities from FCR.

```ios
router bgp 65000
  address-family ipv4
    ! Tag AWS routes with community 65001:1
    neighbor 10.255.1.2 route-map PREFER_AWS out

    route-map PREFER_AWS permit 10
      match community AWS_ROUTES
      set local-preference 200  ! Prefer AWS routes

    route-map PREFER_AWS permit 20
      ! Other routes unchanged

    ip community-list standard AWS_ROUTES permit 65001:1

  exit-address-family
```

### Route Aggregation (Reduce BGP Load)

Summarize DC subnets before advertising to FCR.

```ios
router bgp 65000
  address-family ipv4
    ! Instead of:
    ! network 10.0.0.0 mask 255.255.0.0
    ! network 10.1.0.0 mask 255.255.0.0
    ! network 10.2.0.0 mask 255.255.0.0

    ! Use aggregate:
    aggregate-address 10.0.0.0 255.0.0.0 summary-only

    ! Advertise single 10.0.0.0/8 to FCR (suppresses specific routes)

  exit-address-family
```

### Conditional Route Advertisement

Only advertise to FCR if AWS is reachable (failover pattern).

```ios
router bgp 65000
  address-family ipv4
    ! Advertise local routes only if AWS routes are present

    neighbor 10.255.1.2 route-map ADVERTISE_IF_AWS_UP out

    route-map ADVERTISE_IF_AWS_UP permit 10
      match as-path AWS_PRESENT
      set local-preference 200

    route-map ADVERTISE_IF_AWS_UP permit 20
      ! Default: don't advertise
      set community no-advertise

    ip as-path access-list AWS_PRESENT permit "16509"

  exit-address-family
```

---

## Interface Configuration (vConnection-facing)

### Layer 2 vLAN Interface

Configure the interface facing FCR vConnection.

```ios
configure terminal

! Physical interface
interface GigabitEthernet0/0/1
  description "Link to Equinix (vConnection #1)"
  no shutdown

  ! Option A: Untagged (simple)
  no ip address

! Option B: Tagged vLAN (multiple vConnections)
interface GigabitEthernet0/0/1.100
  description "vConnection #1 (AWS/Azure via FCR)"
  encapsulation dot1q 100
  ip address 10.255.1.1 255.255.255.252

! Configure default gateway to BGP peer (FCR)
ip route 10.255.1.0 255.255.255.252 10.255.1.2

end
```

### Verify Interface Status

```text
show interface GigabitEthernet0/0/1
! Status: up/up

show ip interface brief
! Verify IP address assigned: 10.255.1.1
```

---

## Monitoring and Troubleshooting

### Check BGP Session Status

```text
show bgp ipv4 unicast summary
BGP router identifier 10.0.0.1, local AS number 65000

Neighbor V AS MsgRcvd MsgSent InQ OutQ Up/Down State
10.255.1.2 4 65001 45 42 0 0 00:15:30 Established

! Status: Established = BGP peering is healthy
```

### View Routes Learned from FCR

```text
show bgp ipv4 unicast
  Network Next Hop Metric LocPrf Weight Path

  * 10.0.0.0/8 0.0.0.0 0 32768 i
  * 172.31.0.0/16 10.255.1.2 0 100 65001 16509 i  (AWS)
  * 192.168.0.0/16 10.255.1.2 0 100 65001 8075 i  (Azure)
  * 10.128.0.0/9 10.255.1.2 0 100 65001 15169 i  (GCP)
```

### Monitor BGP Convergence

```text
debug bgp keepalives
! Watch BGP hello/keepalive exchanges

debug bgp updates
! Track route advertisements/withdrawals

! After 30 seconds:
undebug all
```

### Trace BGP Best Path Selection

```text
show bgp ipv4 unicast 10.0.0.0/24
BGP routing table entry for 10.0.0.0/24, version 10
  Paths: (2 available, best #1, table default)
    Advertised to update-groups:
      1
    65001 16509
      10.255.1.2 from 10.255.1.2 (10.255.1.2)
        Origin IGP, metric 0, localpref 200, valid, external, best

  65001 16509 16509 (duplicate AS)
    10.255.1.6 from 10.255.1.6 (10.255.1.6)
      Origin IGP, metric 0, localpref 100, valid, external

! Best path (16509) preferred via primary FCR
```

---

## Failover Test Procedure

### Simulate vConnection Failure

```text
Equinix Console → Fabric → Virtual Connections → [vConnection]
Disable/disable maintenance mode

Expected on Cisco:
T=0s:  vConnection down (physical link loss)
T=3s:  BGP detects (missed hello)
T=9s:  BGP declares neighbor down (holdtime expired)
T=10s: Routes withdraw from routing table
T=11s: Traffic reroutes (to secondary FCR if configured)
T=12s: Full convergence
```

### Verify Failover

```text
Before failure:
  show bgp ipv4 unicast summary
  ! Both neighbors Established

Simulate failure:
  show bgp ipv4 unicast summary
  ! Primary neighbor Down, secondary Established

  show bgp ipv4 unicast | include 172.31.0.0
  ! Routes now via secondary neighbor
```

---

## Best Practices

| Practice | Reason |
| --- | --- |
| **Use BGP timers 3/9** | Default-aggressive convergence (~10s) |
| **Enable soft-reconfiguration inbound** | Allows inbound policy changes without flap |
| **Aggregate local routes** | Reduces BGP table size and updates |
| **Use communities for path control** | More flexible than AS prepending |
| **Monitor BGP neighbor uptime** | Track stability (target: 99.9%+) |
| **Test failover quarterly** | Ensure secondary paths functional |
| **Document BGP topology** | Multi-peer setups need clear mapping |
| **Use passive-interface for unused neighbors** | Prevent accidental peering |
| **Set router-id explicitly** | Avoid election-based changes |

---

## Configuration Checklist

- [ ] Assign BGP router-id
- [ ] Configure BGP AS 65000 (your ASN)
- [ ] Add FCR neighbor with AS 65001 and IP 10.255.1.2
- [ ] Set BGP timers to 3 9 0
- [ ] Advertise local subnets (network commands)
- [ ] Activate IPv4 address family
- [ ] Enable soft-reconfiguration inbound
- [ ] Verify BGP Established status
- [ ] Check routes learned from AWS/Azure/GCP
- [ ] Test failover to secondary FCR (if configured)
- [ ] Document topology and timers

---

## Summary

- **Single router setup:** Simple, peering with FCR, routes to multi-cloud
- **Dual router setup:** iBGP between routers, eBGP to FCR, resilient
- **Multi-metro setup:** Dual FCR instances, primary/secondary failover
- **Hybrid setup:** FCR + direct cloud connections, cost/latency optimization

---

## Next Steps

- [FortiGate to Equinix FCR](fortigate_to_equinix_fcr.md) — FortiGate integration
- [IP WAN Best Practices](equinix_ip_wan_best_practices.md) — Design and operations guide
