# FortiGate BGP Configuration Guide

Complete reference for configuring Border Gateway Protocol (BGP) on Fortinet FortiGate.

## Quick Start: Enable BGP

```text
config router bgp
  set as 65000
  set router-id 10.0.0.1

  config neighbor
    edit "192.168.1.254"
      set remote-as 65001
    next
  end
end
```

---

## Global BGP Configuration

### Basic Setup

```text

config router bgp
  ! Autonomous System Number (ASN)
  set as 65000

  ! Router ID (should match loopback IP)
  set router-id 10.0.0.1

  ! Enable BGP graceful restart (faster recovery)
  set graceful-restart enable

  ! BGP log neighbor changes
  set log-neighbor-changes enable
end
```

### ASN Selection

| ASN Range | Purpose |
| --- | --------- |
| 1–64495 | Public ASNs (internet routing) |
| 64512–65534 | Private ASNs (internal networks) |
| 65000–65535 | Reserved private ASNs (common for DC/enterprise) |

**Example:** Use 65000 for your organization, 65001 for ISP.

---

## Neighbor Configuration

### Add BGP Neighbor (Peer)

```text

config router bgp
  config neighbor
    edit "192.168.1.254"
      ! Neighbor's ASN
      set remote-as 65001

      ! Optional: description
      set description "ISP-1 BGP Peer"

      ! Optional: connect timeout
      set connect-timer 30

      ! Optional: keepalive interval
      set keepalive-time 30

      ! Optional: hold time
      set holdtime 90
    next
  end
end
```

### Neighbor States

| State | Meaning |
| --- | --------- |
| **Idle** | BGP session not started; waiting to connect |
| **Connect** | Attempting to establish TCP connection |
| **Active** | Waiting for BGP OPEN message |
| **OpenSent** | Sent OPEN message; waiting for peer's OPEN |
| **OpenConfirm** | Received OPEN; exchanging routes |
| **Established** | Session up; exchanging routes actively |

---

## Network Announcement (Advertising Routes)

Advertise local networks to BGP neighbors.

### Announce Networks

```text

config router bgp
  config network
    ! Announce local subnet 10.0.0.0/24
    edit 1
      set prefix 10.0.0.0 255.255.255.0
    next

    ! Announce another subnet 10.1.0.0/16
    edit 2
      set prefix 10.1.0.0 255.255.0.0
    next
  end
end
```

**Result:** FortiGate will advertise these networks to all BGP neighbors. Neighbors can then reach your
networks via BGP.

---

## Route Import/Redistribution

Import routes from other routing sources (static routes, OSPF, etc.) into BGP.

### Redistribute Static Routes into BGP

```text

config router bgp
  set as 65000

  ! Redistribute static routes into BGP
  config redistribute-static
    set status enable
    set route-map "RM-Static"
  end

  ! Optional: redistribute connected routes
  config redistribute-connected
    set status enable
  end
end
```

### Redistribute OSPF into BGP

```text

config router bgp
  config redistribute-ospf
    set status enable
  end
end
```

---

## Route Maps and Policy

Control which routes are advertised or accepted.

### Create a Route Map

```text

config router route-map
  edit "RM-Export-Local"
    config rule
      edit 1
        ! Match routes in prefix list
        set match-ip-address "PL-Local-Subnets"
        ! Set metric before advertising
        set set-metric 100
        set action permit
      next
    end
  next
end
```

### Apply Route Map to Neighbor

```text

config router bgp
  config neighbor
    edit "192.168.1.254"
      ! Use route-map when exporting (advertising) to this neighbor
      set route-map-out "RM-Export-Local"

      ! Use route-map when importing (receiving) from this neighbor
      set route-map-in "RM-Import-ISP"
    next
  end
end
```

---

## BGP Timers

### Configure Keepalive and Hold Time

```text

config router bgp
  config neighbor
    edit "192.168.1.254"
      ! Keepalive: send KEEPALIVE message every 30 seconds
      set keepalive-time 30

      ! Hold time: disconnect if no message in 90 seconds
      set holdtime 90

      ! Connect timeout: 30 seconds to establish connection
      set connect-timer 30
    next
  end
end
```

**Timing relationship:**

```text

Keepalive interval: 30 seconds
Hold time: 90 seconds (must be 3x keepalive, typically)

Example timeline:
  T=0s:   Receive KEEPALIVE from neighbor
  T=30s:  Send KEEPALIVE to neighbor
  T=60s:  Receive KEEPALIVE from neighbor
  T=90s:  Hold time expires if no message received since T=0
          Connection drops; neighbor marked as down
```

---

## Complete Configuration Example

### Scenario: Branch FortiGate with BGP to ISP and HQ

```text

Branch FortiGate (ASN 65000, 10.0.0.1)
    |
    ├─ ISP-1 (ASN 65001)
    │   Advertise: 10.0.0.0/24 (local LAN)
    │   Receive: 0.0.0.0/0 (default route)
    │
    └─ HQ (ASN 65000, loopback 10.0.100.1)
        Advertise: 10.0.0.0/24, 10.1.0.0/16 (branch + data center)
        Receive: 10.100.0.0/16 (HQ LAN)
```

**Branch FortiGate Configuration:**

```text

! === Router ID ===
config router settings
  set router-id 10.0.0.1
end

! === BGP Global ===
config router bgp
  set as 65000
  set router-id 10.0.0.1
  set log-neighbor-changes enable
  set graceful-restart enable

  ! === Advertise local networks ===
  config network
    edit 1
      set prefix 10.0.0.0 255.255.255.0
    next
    edit 2
      set prefix 10.1.0.0 255.255.0.0
    next
  end

  ! === BGP Neighbor: ISP-1 ===
  config neighbor
    edit "192.168.1.254"
      set remote-as 65001
      set description "ISP-1 Primary"
      set keepalive-time 30
      set holdtime 90

      ! Import only default route from ISP
      set route-map-in "RM-Import-ISP"
    next

    ! === BGP Neighbor: HQ ===
    edit "192.168.1.2"
      set remote-as 65000
      set description "HQ iBGP Peer"
      set keepalive-time 60
      set holdtime 180

      ! No route-maps: full mesh iBGP
    next
  end

  ! === Route map: Import only default from ISP ===
  config router route-map
    edit "RM-Import-ISP"
      config rule
        edit 1
          ! Accept only 0.0.0.0/0
          set match-ip-address "PL-Default-Only"
          set action permit
        next
        edit 2
          ! Deny everything else
          set action deny
        next
      end
    next
  end
end

! === Prefix list: Default route only ===
config router prefix-list
  edit "PL-Default-Only"
    config rule
      edit 1
        set prefix 0.0.0.0 0.0.0.0
        set le 0
      next
    end
  next
end

! === Prefix list: All local subnets ===
config router prefix-list
  edit "PL-Local-Subnets"
    config rule
      edit 1
        set prefix 10.0.0.0 255.255.0.0
        set le 32
      next
    end
  next
end
```

---

## Verification and Monitoring

### Check BGP Status

```text

get router info bgp summary

! Output:
! BGP router identifier 10.0.0.1, local AS number 65000
! Neighbor        V    AS MsgRcvd MsgSent   TblVer  InQ OutQ State/PfxRcd
! 192.168.1.254   4 65001     100     100      50    0    0 Established/1
! 192.168.1.2     4 65000     200     200      50    0    0 Established/5

! Look for "Established" state; if "Active", neighbor connection failed
```

### Check Advertised Routes

```text

get router info bgp neighbors 192.168.1.254 advertised-routes

! Shows which routes FortiGate is advertising to this neighbor
```

### Check Received Routes

```text

get router info bgp neighbors 192.168.1.254 received-routes

! Shows which routes were received from this neighbor
```

### Check BGP Routing Table

```text

get router info bgp network

! Shows all routes known via BGP
```

### Debug BGP Activity

```text

diagnose router bgp level info

! Enable debug logging for BGP events
```

---

## Common Issues and Fixes

### Issue: Neighbor State is "Active" or "Idle"

**Cause:** TCP connection not established or BGP OPEN rejected.

**Troubleshoot:**

```text

! 1. Check neighbor IP is reachable
execute ping 192.168.1.254

! 2. Check BGP neighbor status
get router info bgp summary

! 3. Check if remote AS is correct
get router bgp

! 4. Check logs for BGP errors
diagnose router bgp level debug
```

**Fix:**

```text

config router bgp
  config neighbor
    edit "192.168.1.254"
      set remote-as 65001  ! Verify this matches peer's ASN
    next
  end
end
```

### Issue: Routes Not Advertised to Neighbor

**Cause:** Routes not in `network` section, or route-map blocking them.

**Check:**

```text

! 1. Verify routes are in network section
get router bgp

! 2. Check advertised routes to neighbor
get router info bgp neighbors 192.168.1.254 advertised-routes

! 3. Check route-map is not blocking
get router route-map
```

**Fix:**

```text

config router bgp
  config network
    edit 1
      set prefix 10.0.0.0 255.255.255.0
    next
  end
end
```

### Issue: Routes Received But Not Used

**Cause:** Administrative distance or metric issue; BGP has higher AD than static route.

**Check:**

```text

get router info routing-table bgp

! Verify received routes appear here
```

**BGP Administrative Distances (default):**

- eBGP: 20
- iBGP: 200
- Static: 10 (preferred over iBGP, but not eBGP)

**Solution:** Lower static route AD or use BGP only.

### Issue: BGP Session Keeps Dropping

**Cause:** Hold time expiring; network latency; keepalive not received.

**Check:**

```text

! 1. Verify connectivity
execute ping 192.168.1.254

! 2. Check keepalive/hold time settings
get router bgp neighbor 192.168.1.254

! 3. Monitor BGP timers
diagnose router bgp level debug
```

**Fix:** Increase hold time for unstable networks

```text

config router bgp
  config neighbor
    edit "192.168.1.254"
      set holdtime 180   ! Increase from 90 to 180 seconds
    next
  end
end
```

---

## Best Practices

| Practice | Reason |
| --- | --------- |
| Set explicit router ID to loopback | Stable identifier |
| Use private ASNs (65000–65535) | Reserved for internal use |
| Use route-maps to filter routes | Prevent unwanted routes from spreading |
| Monitor neighbor state regularly | Early warning of peer issues |
| Set appropriate hold time | Balance convergence vs stability |
| Enable graceful restart | Faster recovery on reboot |
| Test connectivity before BGP | Ensure TCP 179 is reachable |
| Document neighbor relationships | Facilitate troubleshooting |
| Use eBGP for external peers, iBGP for internal | Standard practice |
| Advertise only necessary routes | Reduce routing table size |

---

## Configuration Checklist

- [ ] Set ASN and router ID
- [ ] Configure loopback interface for router ID
- [ ] Add BGP neighbors with correct remote ASN
- [ ] Add `network` statements for subnets to advertise
- [ ] Verify neighbor state is "Established" (`get router info bgp summary`)
- [ ] Check advertised routes appear on neighbor (`get router info bgp neighbors <IP> advertised-routes`)
- [ ] Check received routes appear in routing table (`get router info bgp network`)
- [ ] Test end-to-end connectivity via BGP
- [ ] Configure route-maps if filtering needed
- [ ] Enable graceful restart for stability

---

## Quick Reference

```text

! Enable BGP
config router bgp
  set as 65000
  set router-id 10.0.0.1
end

! Add neighbor
config router bgp
  config neighbor
    edit "192.168.1.254"
      set remote-as 65001
    next
  end
end

! Advertise network
config router bgp
  config network
    edit 1
      set prefix 10.0.0.0 255.255.255.0
    next
  end
end

! Verify
get router info bgp summary
get router info bgp neighbors 192.168.1.254 advertised-routes
get router info bgp network
```
