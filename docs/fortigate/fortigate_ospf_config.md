# FortiGate OSPF Configuration Guide

Complete reference for configuring Open Shortest Path First (OSPF) on Fortinet
FortiGate.

## Quick Start: Enable OSPF

```text
config router ospf
  set router-id 10.0.0.1

  config area
    edit 0.0.0.0
    next
  end

  config ospf-interface
    edit "port1"
      set interface "port1"
      set area 0.0.0.0
    next
  end
end
```

---

## Global OSPF Configuration

### Basic Setup

```text

config router ospf
  ! Router ID (should match loopback IP)
  set router-id 10.0.0.1

  ! Log OSPF neighbor changes for visibility
  set log-neighbor-changes enable

  ! Reference bandwidth (for metric calculation)
  ! Default: 100 Mbps; set to 1000 for Gbps networks
  set abr-type standard

  ! SPF throttle timers (milliseconds)
  ! Controls how fast OSPF recalculates on topology changes
  set spf-interval-delay 5000
  set spf-interval-exp-delay 10000
end
```

### Router ID

Every OSPF router needs a unique router ID. FortiGate uses:

1. Explicitly configured router ID (best)
2. Loopback IP address (if configured)
3. Highest interface IP address (if no loopback)

**Best practice:** Set router ID explicitly to loopback address.

```text

config router settings
  set router-id 10.0.0.1
end
```

---

## Area Configuration

OSPF divides the network into **areas**. Every OSPF network must have Area 0 (backbone).

### Create Area

```text

config router ospf
  config area
    ! Area ID (typically 0.0.0.0 for backbone, 0.0.0.1 for other areas)
    edit 0.0.0.0
      set type regular  ! Can also be "nssa", "stub"
    next

    edit 0.0.0.1
      set type regular  ! Another area
    next
  end
end
```

### Area Types

| Type | Use Case | Characteristics |
| --- | --------- | --- |
| **Regular** | General purpose | Full LSA flooding; highest memory/CPU |
| **Stub** | Reduce routing table size | No external routes; default route to ABR |
| **NSSA** | Allow limited external routes | External routes allowed from ASBR; reduces traffic |
| **Totally Stub** | Maximum reduction | No external or inter-area routes |

---

## Interface Configuration

### Enable OSPF on Interface

```text

config router ospf
  config ospf-interface
    edit "port1"
      ! Physical interface to run OSPF on
      set interface "port1"

      ! Area this interface belongs to
      set area 0.0.0.0

      ! Network type (see table below)
      set type broadcast  ! or point-to-point, etc.

      ! Optional: cost/metric (lower = preferred)
      set cost 10

      ! Optional: priority (for DR/BDR election)
      set priority 1

      ! Optional: hello interval
      set hello-interval 10

      ! Optional: dead interval
      set dead-interval 40
    next
  end
end
```

### Network Types

| Type | Best For | Neighbor Discovery |
| --- | --------- | --- |
| **Broadcast** | Ethernet LAN | Multicast hello; DR/BDR elected |
| **Point-to-Point** | Serial links, P2P tunnels | No DR/BDR; direct communication |
| **Non-broadcast** | Frame Relay, legacy networks | Manual neighbor configuration |

---

## OSPF Timers

Control convergence speed and CPU load.

### Hello and Dead Intervals

```text

config router ospf
  config ospf-interface
    edit "port1"
      ! Hello interval: send hello every 10 seconds
      set hello-interval 10

      ! Dead interval: neighbor dead if no hello in 40 seconds
      set dead-interval 40

      ! Dead = 4 × Hello (typical ratio)
    next
  end
end
```

### SPF Calculation Timers

Control how fast OSPF recalculates routes after topology change.

```text

config router ospf
  ! Initial SPF delay: 5000 ms (5 seconds)
  set spf-interval-delay 5000

  ! Exponential SPF delay: max 10000 ms (10 seconds)
  set spf-interval-exp-delay 10000

  ! First topology change: recalculate in 5 seconds
  ! Subsequent changes: recalculate in 10 seconds (exponential backoff)
end
```

---

## Route Redistribution

Import routes from other sources (static, BGP, connected) into OSPF.

### Redistribute Static Routes

```text

config router ospf
  config redistribute-static
    set status enable
    ! Optional: metric for redistributed routes
    set metric 100
  end
end
```

### Redistribute Connected Routes

```text

config router ospf
  config redistribute-connected
    set status enable
  end
end
```

### Redistribute BGP

```text

config router ospf
  config redistribute-bgp
    set status enable
  end
end
```

---

## Complete Configuration Example

### Scenario: OSPF Backbone with Area 0

```text

HQ Router (Router ID 10.0.0.1, Area 0)
   |
   | port1 (192.168.1.1/24)
   |
   +--- Branch Router (Router ID 10.0.0.2, Area 0)
        port1 (192.168.1.2/24)
        Loopback (10.0.0.2/32)
```

**HQ Router Configuration:**

```text

config router settings
  set router-id 10.0.0.1
end

config router ospf
  set router-id 10.0.0.1
  set log-neighbor-changes enable

  ! Area 0 (backbone)
  config area
    edit 0.0.0.0
      set type regular
    next
  end

  ! Loopback interface (for management)
  config ospf-interface
    edit "loopback"
      set interface "loopback"
      set area 0.0.0.0
      set cost 1
      set priority 1
    next

    ! Port to Branch Router (point-to-point link)
    edit "port1"
      set interface "port1"
      set area 0.0.0.0
      set type broadcast
      set cost 10
      set hello-interval 10
      set dead-interval 40
      set priority 64     ! Higher priority = more likely to be DR
    next
  end

  ! Redistribute connected routes (LAN subnets)
  config redistribute-connected
    set status enable
    set metric 100
  end
end
```

**Branch Router Configuration:**

```text

config router settings
  set router-id 10.0.0.2
end

config router ospf
  set router-id 10.0.0.2
  set log-neighbor-changes enable

  config area
    edit 0.0.0.0
      set type regular
    next
  end

  config ospf-interface
    edit "loopback"
      set interface "loopback"
      set area 0.0.0.0
    next

    ! Port to HQ (point-to-point link)
    edit "port1"
      set interface "port1"
      set area 0.0.0.0
      set type broadcast
      set cost 10
      set hello-interval 10
      set dead-interval 40
      set priority 32     ! Lower priority = less likely to be DR
    next
  end

  config redistribute-connected
    set status enable
    set metric 100
  end
end
```

---

## Verification and Monitoring

### Check OSPF Status

```text

get router info ospf summary

! Output:
! OSPF Routing Process, Router ID: 10.0.0.1
!  Neighbors found: 1
!  Number of areas: 1
!  External routes: 0
```

### Check OSPF Neighbors

```text

get router info ospf neighbor

! Output:
! Neighbor ID    Pri   State           Dead Time  Address         Interface
! 10.0.0.2         32  Full/DR         39s        192.168.1.2     port1

! Look for "Full" state; if "Init" or "2-Way", neighbor not fully converged
```

### Check DR/BDR Election

```text

get router info ospf interface

! Output:
! Interface port1
!   DR: 10.0.0.1  (this router)
!   BDR: 10.0.0.2
!   Hello interval: 10, Dead interval: 40
```

### Check OSPF Routing Table

```text

get router info ospf database

! Shows all LSAs (Link State Advertisements) in OSPF database
```

### Check Routes Learned via OSPF

```text

get router info routing-table ospf

! Shows all routes learned via OSPF
! Look for routes from other areas or neighbors
```

---

## Common Issues and Fixes

### Issue: Neighbor Stuck in "Init" or "2-Way"

**Cause:** Network type mismatch, ACL blocking OSPF, or DR/BDR not forming.

**Check:**

```text

get router info ospf neighbor
get router info ospf interface
```

**Troubleshoot:**

```text

! 1. Verify network types match
get router ospf ospf-interface port1

! 2. Verify OSPF is enabled on interface
get router ospf ospf-interface

! 3. Check firewall policy allows OSPF (protocol 89)
get firewall policy
```

**Fix:**

```text

config router ospf
  config ospf-interface
    edit "port1"
      set type broadcast  ! Ensure both sides match
    next
  end
end
```

### Issue: No OSPF Neighbors

**Cause:** Interfaces not in same area, subnet mismatch, or OSPF not enabled on interface.

**Check:**

```text

! 1. Verify OSPF interfaces
get router ospf ospf-interface

! 2. Verify areas match
config router ospf
  show area
end

! 3. Verify interface is up
get system interface port1
```

**Fix:**

```text

config router ospf
  config ospf-interface
    edit "port1"
      set interface "port1"
      set area 0.0.0.0
    next
  end
end
```

### Issue: Routes Not Learned from Neighbor

**Cause:** Redistribution not enabled, or routes not advertised by neighbor.

**Check:**

```text

! 1. Verify neighbor is Full
get router info ospf neighbor

! 2. Check OSPF routing table
get router info ospf database

! 3. Check what neighbor is advertising
get router info ospf database neighbor <neighbor-id>
```

**Fix:** Enable redistribution on neighbor

```text

config router ospf
  config redistribute-connected
    set status enable
  end
end
```

### Issue: Suboptimal Path Selected

**Cause:** Cost incorrectly calculated or not set on interfaces.

**Check:**

```text

get router info ospf interface

! Verify cost values
```

**Fix:** Adjust cost on interfaces

```text

config router ospf
  config ospf-interface
    edit "port1"
      set cost 10   ! Lower cost = preferred path
    next
  end
end
```

---

## Best Practices

| Practice | Reason |
| --- | --------- |
| Set explicit router ID to loopback | Stable, persistent identifier |
| Use Area 0 as backbone | Standard OSPF design |
| Match network types on both sides | Prevents neighbor issues |
| Adjust hello/dead timers for convergence needs | Balance fast reconvergence vs stability |
| Set interface costs intentionally | Predictable path selection |
| Monitor neighbor state regularly | Early warning of topology issues |
| Enable log-neighbor-changes | Track network stability |
| Use redistribute-connected for LAN subnets | Automatic route advertisement |
| Test connectivity before enabling OSPF | Verify IP routing works first |
| Document area structure | Facilitate future scaling |

---

## Configuration Checklist

- [ ] Set router ID on all routers
- [ ] Create Area 0 (backbone)
- [ ] Enable OSPF on all interfaces in same area
- [ ] Verify network type (broadcast/point-to-point) matches on both sides
- [ ] Verify neighbor state is "Full" (`get router info ospf neighbor`)
- [ ] Check that routes are learned (`get router info routing-table ospf`)
- [ ] Adjust interface costs if path selection is wrong
- [ ] Enable redistribution (connected, static) if needed
- [ ] Set appropriate hello/dead intervals for your network
- [ ] Test end-to-end connectivity via OSPF routes

---

## Quick Reference

```text

! Enable OSPF
config router ospf
  set router-id 10.0.0.1

  config area
    edit 0.0.0.0
    next
  end

  config ospf-interface
    edit "port1"
      set interface "port1"
      set area 0.0.0.0
    next
  end
end

! Add another interface
config router ospf
  config ospf-interface
    edit "port2"
      set interface "port2"
      set area 0.0.0.0
    next
  end
end

! Redistribute connected routes
config router ospf
  config redistribute-connected
    set status enable
  end
end

! Verify
get router info ospf summary
get router info ospf neighbor
get router info routing-table ospf
```
