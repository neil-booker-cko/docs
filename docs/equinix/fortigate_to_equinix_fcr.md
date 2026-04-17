# FortiGate to Equinix FCR Integration Guide

Complete reference for connecting Fortinet FortiGate firewalls to Equinix Fabric Cloud Router for
secure cloud and datacenter interconnection.

## Quick Start: FortiGate to FCR (Single Cloud)

```fortios
config system interface
  edit "port1"
    set ip 10.255.1.1 255.255.255.252
    set description "Equinix vConnection #1"
  next
end

config router bgp
  set as 65000
  set router-id 10.0.0.1

  config neighbor
    edit "10.255.1.2"
      set remote-as 65001
      set description "Equinix FCR (SJC)"
    next
  end

  config network
    edit 1
      set prefix 10.0.0.0 255.0.0.0
      set description "Local DC subnet"
    next
  end
end
```text

**Verify:**
```text
get router bgp summary
! Expect: neighbor 10.255.1.2 status ESTABLISHED
```text

---

## Detailed Integration Scenarios

## Scenario 1: Single FortiGate to FCR (Hub-and-Spoke Cloud)

### Network Diagram

```text
FortiGate Firewall (DC)
  10.0.0.1 (internal IP)
  10.255.1.1 (BGP peer to FCR)
  10.0.0.0/8 (protected networks)
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
```text

### FortiGate Configuration

```fortios
! System configuration
config system interface
  edit "port1"
    set alias "WAN-to-Equinix"
    set ip 10.255.1.1 255.255.255.252
    set mtu 1500
  next

  edit "port2"
    set alias "LAN-to-DC"
    set ip 10.0.0.1 255.255.255.0
  next
end

! BGP routing
config router bgp
  set as 65000
  set router-id 10.0.0.1
  set ebgp-multipath enable
  set log-neighbour-changes enable

  ! FCR neighbor
  config neighbor
    edit "10.255.1.2"
      set remote-as 65001
      set description "Equinix FCR Primary"
      set timers-connect 10
      set timers-hold 30
      set timers-keepalive 10
    next
  end

  ! Advertise local networks
  config network
    edit 1
      set prefix 10.0.0.0 255.0.0.0
      set description "DC Subnets"
    next
    edit 2
      set prefix 10.1.0.0 255.255.0.0
      set description "DC Servers"
    next
  end

  ! Receive all routes from FCR
  config aggregate-address
    ! Optional: Aggregate routes before sending
  end

end

! Create firewall policies for cloud traffic
config firewall policy
  edit 1
    set name "DC-to-Cloud"
    set srcintf "port2"      ! Local DC interface
    set dstintf "port1"      ! WAN-to-Equinix
    set action accept
    set srcaddr "all"
    set dstaddr "all"
    set service "ALL"
    set logtraffic all
  next
end
```text

### Verification

```text
FortiGate CLI:

get router bgp summary
! Output should show:
! neighbor 10.255.1.2: state ESTABLISHED

get router bgp neighbors 10.255.1.2
! Details: uptime, messages sent/received

diagnose ip route list
! Check if routes from AWS/Azure/GCP present in routing table

diagnose debug flow show-summary
! Monitor traffic flowing through port1 (to FCR)
```text

---

## Scenario 2: Dual FortiGate (HA) to FCR (Redundancy)

### Network Diagram

```text
FortiGate-A (primary)      FortiGate-B (secondary)
  10.0.0.1                   10.0.0.2
  HA Sync (heartbeat)

  Port1: 10.255.1.1         Port1: 10.255.1.5
  BGP AS 65000              BGP AS 65000
        |                          |
        └──────── VRRP ────────────┘ (Virtual IP: 10.255.1.3)

        BGP eBGP (to FCR)

  Equinix FCR-A
    10.255.1.2 (peered with active FortiGate)
    AS 65001
```text

### FortiGate-A Configuration (Primary)

```fortios
config system ha
  set mode active-passive
  set hbdev "ha" 4
  set ha-mgmt-status enable
  set ha-mgmt-interfaces
    edit 1
      set interface "mgmt"
    next
  end
  set priority 200  ! Higher = more likely to be primary
  set unicast enable
  set unicast-peer "10.0.0.2"  ! Partner FortiGate IP
end

! Floating/Virtual IP for BGP peering (uses VRRP)
config system vrrp
  edit 1
    set interface "port1"
    set vip 10.255.1.3  ! Virtual IP that FCR peers with
    set priority 200
  next
end

config router bgp
  set as 65000
  set router-id 10.0.0.1

  ! Peer with FCR using virtual IP
  config neighbor
    edit "10.255.1.2"
      set remote-as 65001
      set description "Equinix FCR"
      set timers-hold 30
      set timers-keepalive 10
    next
  end

  config network
    edit 1
      set prefix 10.0.0.0 255.0.0.0
    next
  end
end
```text

### FortiGate-B Configuration (Secondary)

```fortios
config system ha
  set mode active-passive
  set hbdev "ha" 4
  set ha-mgmt-status enable
  set priority 100  ! Lower priority = secondary
  set unicast enable
  set unicast-peer "10.0.0.1"  ! Partner FortiGate IP
end

config system vrrp
  edit 1
    set interface "port1"
    set vip 10.255.1.3  ! Same virtual IP as FortiGate-A
    set priority 100
  next
end

config router bgp
  set as 65000
  set router-id 10.0.0.2

  config neighbor
    edit "10.255.1.2"
      set remote-as 65001
      set description "Equinix FCR"
      set timers-hold 30
      set timers-keepalive 10
    next
  end

  config network
    edit 1
      set prefix 10.0.0.0 255.0.0.0
    next
  end
end
```text

### Failover Behavior

```text
Normal operation:
  FortiGate-A (primary) owns Virtual IP 10.255.1.3
  FCR peers with 10.255.1.3 (FortiGate-A)
  BGP routes flow via FortiGate-A

FortiGate-A failure:
  HA heartbeat times out (3 seconds)
  FortiGate-B takes over Virtual IP (VRRP transition)
  FCR detects BGP status (BGP session may flap briefly)
  Traffic redirects through FortiGate-B
  Convergence: 3–15 seconds
```text

---

## Scenario 3: Multi-Metro FCR with FortiGate Cluster (Maximum Redundancy)

### Network Diagram

```text
Primary DC (SJC)          Secondary DC (LAX)
  FortiGate-A              FortiGate-C
  10.0.0.1                 10.0.0.3
  HA pair (FG-B backup)    HA pair (FG-D backup)

  BGP AS 65000             BGP AS 65000

  ├─ Peer: FCR-A (SJC)     ├─ Peer: FCR-B (LAX)
  │                        │
  └─ iBGP with FG-C ───────┘

  Equinix FCR-A (SJC)      Equinix FCR-B (LAX)
    10.255.1.2              10.255.2.2
    AS 65001                AS 65001

    ├─iBGP with FCR-B
    │
    AWS (dual peering)
```text

### FortiGate-A Configuration (Primary DC)

```fortios
config router bgp
  set as 65000
  set router-id 10.0.0.1

  ! Peer with local FCR (SJC)
  config neighbor
    edit "10.255.1.2"
      set remote-as 65001
      set description "FCR-A (SJC, primary)"
      set timers-hold 30
      set timers-keepalive 10
    next

    ! iBGP peer with secondary DC FortiGate
    edit "10.0.0.3"
      set remote-as 65000
      set description "FortiGate-C (LAX, secondary DC)"
      set timers-hold 30
      set timers-keepalive 10
      set keep-alive-timer 10
      set hold-timer 30
    next

    ! Optional: Peer with secondary FCR for redundancy
    edit "10.255.2.2"
      set remote-as 65001
      set description "FCR-B (LAX, secondary)"
      set timers-hold 30
      set timers-keepalive 10
    next
  end

  ! Local subnets
  config network
    edit 1
      set prefix 10.0.0.0 255.0.0.0
      set description "DC-A (SJC)"
    next
  end

  ! Path preference
  config redistribute-static
    set status enable
  end

end
```text

### Failover Test

```text
Scenario: FCR-A (SJC) failure

Before failure:
  FortiGate-A → FCR-A (SJC) → AWS
  Traffic via primary, secondary available

After failure (FCR-A down):
  BGP detects (30s hold time expires)
  Routes withdraw from FCR-A
  Traffic shifts to FCR-B (LAX) via iBGP route
  Convergence: ~30–40 seconds

After failure (FCR-A recovers):
  BGP re-establishes
  Preferred path (SJC) restored
  Traffic reconverges (may cause brief flap)
```text

---

## Scenario 4: FortiGate with SD-WAN + FCR (Hybrid Cloud)

Combine SD-WAN (for multiple ISP links) with FCR (for cloud).

### Network Diagram

```text
FortiGate SD-WAN
  Port1: ISP-1 (primary) →  ISP backbone → AWS (direct)
  Port2: ISP-2 (backup)  →  ISP backbone → AWS (direct)
  Port3: Equinix vConn   →  Equinix FCR → AWS/Azure/GCP

  Policy: Route sensitive cloud traffic via FCR (port3)
```text

### Configuration

```fortios
! Interface configuration
config system interface
  edit "port1"
    set alias "ISP-1"
    set ip 203.0.113.1 255.255.255.0
  next
  edit "port2"
    set alias "ISP-2"
    set ip 198.51.100.1 255.255.255.0
  next
  edit "port3"
    set alias "Equinix-FCR"
    set ip 10.255.1.1 255.255.255.252
  next
end

! SD-WAN configuration (ISP failover)
config system sdwan
  set status enable

  config zone
    edit "internet"
    next
    edit "fcr"
    next
  end

  config members
    edit 1
      set interface "port1"
      set zone "internet"
      set priority 10  ! Higher priority = preferred
    next
    edit 2
      set interface "port2"
      set zone "internet"
      set priority 20  ! Backup ISP
    next
    edit 3
      set interface "port3"
      set zone "fcr"
    next
  end

  config health-check
    edit "AWS-Check"
      set server "8.8.8.8"  ! Google DNS (check internet uptime)
      set probe-count 5
      set members 1 2
    next
  end
end

! BGP on Equinix FCR link
config router bgp
  set as 65000

  config neighbor
    edit "10.255.1.2"
      set remote-as 65001
      set description "Equinix FCR"
    next
  end

  config network
    edit 1
      set prefix 10.0.0.0 255.0.0.0
    next
  end
end

! Firewall policies (route based on traffic type)
config firewall policy
  edit 1
    set name "DC-to-AWS-via-FCR"
    set srcintf "port2"      ! LAN
    set dstintf "port3"      ! Equinix FCR
    set srcaddr "AWS-Apps"   ! Tag for AWS apps
    set dstaddr "AWS-VPC"
    set action accept
    set comments "Use FCR for AWS (lower latency, dedicated)"
  next

  edit 2
    set name "DC-to-Internet-via-ISP"
    set srcintf "port2"
    set dstintf "port1"      ! ISP-1 (primary)
    set srcaddr "Internet"   ! Tag for internet destinations
    set action accept
    set comments "Use ISP for internet destinations"
  next
end
```text

---

## Advanced Configurations

### BGP Community-Based Routing

Tag routes to control path selection.

```fortios
config router route-map
  edit "PREFER_FCR_SJC"
    config rule
      edit 1
        set match-ip-address "AWS-ROUTES"
        set set-community "65000:1"
        set set-local-preference 200
      next
    end
  next

  edit "BACKUP_FCR_LAX"
    config rule
      edit 1
        set match-ip-address "AWS-ROUTES"
        set set-community "65000:2"
        set set-local-preference 100
      next
    end
  next
end

config router bgp
  config neighbor
    edit "10.255.1.2"      ! FCR-SJC
      set route-map-out "PREFER_FCR_SJC"
    next
    edit "10.255.2.2"      ! FCR-LAX
      set route-map-out "BACKUP_FCR_LAX"
    next
  end
end
```text

### Route Aggregation (Reduce BGP Updates)

Summarize internal subnets before advertising to FCR.

```fortios
config router bgp
  ! Instead of advertising each subnet:
  ! 10.1.0.0/16, 10.2.0.0/16, 10.3.0.0/16, ...

  ! Aggregate to single summary:
  config aggregate-address
    edit 1
      set prefix 10.0.0.0 255.0.0.0
      set summary-only enable  ! Suppress specific routes
    next
  end
end
```text

### Access Control for BGP

Limit which routes FCR advertises to FortiGate.

```fortios
config router prefix-list
  edit "ACCEPT_AWS_AZURE_GCP"
    config rule
      edit 1
        set prefix 172.31.0.0 255.255.0.0  ! AWS
        set le 24
      next
      edit 2
        set prefix 192.168.0.0 255.255.0.0  ! Azure
        set le 24
      next
      edit 3
        set prefix 10.128.0.0 255.128.0.0  ! GCP
        set le 24
      next
    end
  next
end

config router bgp
  config neighbor
    edit "10.255.1.2"
      set route-map-in "FILTER_CLOUD"
    next
  end
end

config router route-map
  edit "FILTER_CLOUD"
    config rule
      edit 1
        set match-ip-address "ACCEPT_AWS_AZURE_GCP"
        set action accept
      next
      edit 2
        set action deny  ! Deny all others
      next
    end
  next
end
```text

---

## Monitoring and Troubleshooting

### Check BGP Neighbor Status

```text
diagnose router bgp summary
! Output:
! neighbor 10.255.1.2: state ESTABLISHED

diagnose router bgp neighbors 10.255.1.2
! Details: uptime, hello/hold timers, routes exchanged
```text

### View Learned Routes

```text
diagnose ip route list | grep -E "10.255.1.2|AWS|Azure|GCP"
! Show routes learned from FCR

show router bgp network
! BGP-advertised networks
```text

### Monitor BGP Events

```text
diagnose debug enable
diagnose debug application bgpd -1

! Perform BGP action (e.g., flap neighbor)
! Watch for debug output showing BGP events

diagnose debug disable
```text

### Trace BGP Path Selection

```text
diagnose router bgp paths 172.31.0.0/16
! Show why specific route was chosen

diagnose router bgp route-map-stats
! BGP route map statistics
```text

### Check Firewall Policy Logs

```text
diagnose sniffer packet any "host 10.255.1.2" 4
! Capture traffic to/from FCR peer
! Verify traffic flowing through BGP peer

diagnose debug flow show summary
! Monitor active traffic flows
```text

---

## Failover Test Procedure

### Simulate BGP Flap

```text
FortiGate CLI:

! View current BGP status
diagnose router bgp summary

! Disable BGP neighbor (simulates failure)
execute router bgp neighbor 10.255.1.2 disable

! Expected:
! - BGP status changes from ESTABLISHED to IDLE
! - Routes from FCR disappear
! - Firewall policies may fail (if no backup route)

! Re-enable to test failover
execute router bgp neighbor 10.255.1.2 enable

! Expected:
! - BGP re-establishes
! - Routes reappear
! - Traffic normalizes
```text

### Monitor Convergence Time

```text
1. Disable BGP neighbor
2. Check timestamp: T=0
3. Monitor: diagnose debug flow show summary
4. Watch for traffic resuming via backup path
5. Check timestamp: T=X seconds
6. Calculate convergence = X seconds (should be < 30s)
```text

---

## FortiGate Logging Best Practices

### Enable BGP Logging

```fortios
config log memory
  set status enable
end

config router bgp
  set log-neighbour-changes enable
end

! View logs
execute log display memory
```text

### Enable Traffic Logging

```fortios
config firewall policy
  edit 1
    set logtraffic all  ! Log all traffic matching policy
    set logtraffic-start enable  ! Log session initiation
  next
end
```text

---

## Best Practices

| Practice | Reason |
| --- | --- |
| **Use BGP timers 10s/30s** | Conservative (slower failover ~30s) but stable |
| **Use HA for production FortiGates** | Active-passive provides redundancy |
| **Enable BGP logging** | Simplify troubleshooting |
| **Use route-maps for policy** | Fine-grained control over path selection |
| **Monitor BGP neighbor uptime** | Track stability (target: 99.9%+) |
| **Test failover quarterly** | Ensure backup paths operational |
| **Document BGP topology** | Complex setups need clear mapping |
| **Use prefix-lists for filtering** | Prevent accidental route acceptance |
| **Enable soft-reconfiguration inbound** | Allow inbound policy changes without flap |

---

## Configuration Checklist

- [ ] Configure port1 with FCR vConnection IP (10.255.1.1/30)
- [ ] Configure port2 (or internal interface) with local DC IP
- [ ] Set BGP AS 65000
- [ ] Set router-id explicitly (e.g., 10.0.0.1)
- [ ] Add FCR neighbor (10.255.1.2, AS 65001)
- [ ] Configure BGP timers (10/30 recommended)
- [ ] Add local network announcements
- [ ] Verify BGP neighbor status (ESTABLISHED)
- [ ] Check routes learned from AWS/Azure/GCP
- [ ] Create firewall policies for cloud traffic
- [ ] Enable BGP logging for troubleshooting
- [ ] Test failover (disable/enable neighbor)
- [ ] Document topology and configuration

---

## Summary

- **Single FortiGate setup:** Simple BGP peering with FCR, routes to multi-cloud
- **HA setup:** FortiGate active-passive with VRRP for high availability
- **Multi-metro setup:** Multiple DCs with iBGP between FortiGates, peering with dual FCRs
- **Hybrid setup:** SD-WAN + FCR for combined internet and cloud connectivity

---

## Next Steps

- [Cisco to Equinix FCR](cisco_to_equinix_fcr.md) — Cisco integration guide
- [IP WAN Best Practices](equinix_ip_wan_best_practices.md) — Design and operations guide
