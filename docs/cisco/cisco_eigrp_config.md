# Cisco IOS-XE EIGRP Configuration Guide

Complete reference for configuring Enhanced Interior Gateway Routing Protocol (EIGRP) on
Cisco IOS-XE.

## Quick Start: Enable EIGRP

```ios
configure terminal

router eigrp 100
  eigrp router-id 10.0.0.1
  network 192.168.1.0 0.0.0.255
  network 10.0.0.0 0.0.255.255

end
show ip eigrp neighbors
```

---

## Global EIGRP Configuration

### Basic Setup

```ios

configure terminal

! Create EIGRP process (AS number: 1-65535, typically 1-100 for enterprise)
router eigrp 100

  ! Router ID (should match loopback IP)
  eigrp router-id 10.0.0.1

  ! Enable classic/named mode (named mode recommended for modern IOS-XE)
  ! Legacy: use "router eigrp 100" alone
  ! Modern: use "router eigrp VRF default" for named mode

end
```

### EIGRP AS Number

| Range | Use Case |
| --- | --------- |
| 1–65535 | Valid AS numbers |
| Typically 1–100 | Enterprise internal EIGRP |
| 65000–65535 | Usually reserved for BGP private use, but works for EIGRP |

**Best practice:** Use single AS number for entire network; match across all routers.

---

## Network Advertisement

Tell EIGRP which interfaces to enable and which networks to advertise.

### Enable EIGRP on Interfaces

```ios

configure terminal

router eigrp 100
  ! Advertise networks connected to these interfaces
  network 192.168.1.0 0.0.0.255  ! Port1: 192.168.1.1/24
  network 10.0.0.0 0.0.255.255   ! Loopback & VLANs: 10.x.x.x/16

end
```

### Wildcard Mask Explained

EIGRP uses wildcard mask (inverse subnet mask) to match networks.

| Subnet Mask | Wildcard Mask | Meaning |
| --- | --------- | --- |
| 255.255.255.0 (/24) | 0.0.0.255 | Match 192.168.1.0–255 |
| 255.255.0.0 (/16) | 0.0.255.255 | Match 10.0.0.0–10.0.255.255 |
| 255.0.0.0 (/8) | 0.255.255.255 | Match 10.0.0.0–10.255.255.255 |
| 0.0.0.0 | 255.255.255.255 | Match any network (use with caution) |

**Calculation:** Wildcard = 255.255.255.255 - Subnet Mask

### Enable EIGRP on Specific Interface

```ios

configure terminal

interface GigabitEthernet0/1
  ! Directly enable EIGRP on this interface (IOS-XE 16.9+)
  ip eigrp 100

end
```

---

## Passive Interfaces

Prevent EIGRP from sending hello/update packets on specific interfaces (e.g., access ports).

```ios

configure terminal

router eigrp 100
  ! Don't send EIGRP packets on access ports
  passive-interface GigabitEthernet0/10
  passive-interface GigabitEthernet0/11

  ! Or set all interfaces passive, then enable only trunk ports
  passive-interface default
  no passive-interface GigabitEthernet0/48  ! Trunk to neighbor
  no passive-interface GigabitEthernet0/49  ! Trunk to neighbor

end
```

**Effect:** Advertise networks on passive interface, but don't send hello/updates (no neighbors formed
on that interface).

---

## EIGRP Neighbors and Adjacency

### Verify Neighbors

```ios

show ip eigrp neighbors

! Output:
! EIGRP-IPv4 Neighbors for AS(100)
! H   Address         Interface       Hold Uptime   SRTT   RTO  Q Seq Type
! 1   192.168.1.2     Gi0/1           13   00:05:22  45    270  0  25  R   U

! Look for:
! - H: neighbor handle
! - Hold: seconds until neighbor timeout (usually 15 for LAN, 180 for WAN)
! - Uptime: how long neighbor has been up
! - Seq: sequence number of last update
```

### Neighbor Requirements

For EIGRP neighbors to form, they must have:

1. **Same AS number** — Both routers running EIGRP 100
2. **Same K-values** — Default K1=1, K3=1 (usually matches automatically)
3. **IP connectivity** — Can ping each other
4. **Not passive interface** — Interface must actively send/receive EIGRP packets

---

## Route Metrics and Costs

EIGRP uses a composite metric based on bandwidth and delay (by default).

### Metric Calculation

```text

Metric = [(K1 × bandwidth) + (K3 × delay)] × 256
```

**Default K-values:**

- K1 = 1 (bandwidth)
- K2 = 0 (unused)
- K3 = 1 (delay)
- K4 = 0 (unused)
- K5 = 0 (unused)

### Bandwidth Configuration

EIGRP uses interface bandwidth for metric calculation (not actual throughput).

```ios

configure terminal

interface GigabitEthernet0/1
  ! Set interface bandwidth (in kbps)
  bandwidth 1000000  ! 1 Gbps

  ! Or for serial link
  bandwidth 1544     ! T1 line (1.544 Mbps)

end

! Verify
show interface GigabitEthernet0/1 | include BW
```

### Delay Configuration

```ios

configure terminal

interface GigabitEthernet0/1
  ! Set delay (in tens of microseconds)
  delay 10  ! Default for Gbps = 10

end
```

---

## Route Redistribution

Import routes from other sources (static, OSPF, BGP) into EIGRP.

### Redistribute Static Routes

```ios

configure terminal

router eigrp 100
  redistribute static metric 1000000 100 255 1 1500

end
```

**Metric parameters:** bandwidth delay reliability load mtu

- `1000000` = bandwidth (1 Gbps in kbps)
- `100` = delay (tens of microseconds)
- `255` = reliability (255 = 100%)
- `1` = load (1 = 1/255 utilization)
- `1500` = MTU (bytes)

### Redistribute Connected Routes

```ios

configure terminal

router eigrp 100
  redistribute connected metric 1000000 100 255 1 1500

end
```

---

## EIGRP Timers

Control convergence speed and hello frequency.

### Hello and Hold Timers

```ios

configure terminal

interface GigabitEthernet0/1
  ! Hello interval: send hello every 5 seconds
  ip hello-interval eigrp 100 5

  ! Hold interval: consider neighbor down if no hello in 15 seconds
  ip hold-time eigrp 100 15

end
```

**Timing relationship:**

```text

Hello: 5 seconds (send greeting to neighbors)
Hold: 15 seconds (wait before marking neighbor as down)

If no hello received for 15 seconds → neighbor marked as down → recompute routes
```

### Default Timers (by link type)

| Link Type | Hello | Hold |
| --- | --------- | --- |
| LAN (Ethernet) | 5 sec | 15 sec |
| WAN (serial, leased line) | 60 sec | 180 sec |

---

## Complete Configuration Example

### Scenario: Multi-Site EIGRP Network

```text

HQ Router (10.0.0.1, AS 100)
   |
   | 192.168.1.0/24
   |
Branch Router (10.0.0.2, AS 100)
```

**HQ Router Configuration:**

```ios

configure terminal

! === Loopback ===
interface Loopback0
  ip address 10.0.0.1 255.255.255.255

! === Uplink to Branch ===
interface GigabitEthernet0/1
  description "Link to Branch"
  ip address 192.168.1.1 255.255.255.0
  bandwidth 1000000
  no shutdown

! === LAN Interface ===
interface Vlan100
  ip address 10.100.0.1 255.255.255.0
  no shutdown

! === EIGRP Configuration ===
router eigrp 100
  eigrp router-id 10.0.0.1

  ! Advertise loopback
  network 10.0.0.0 0.0.255.255

  ! Advertise LAN
  network 10.100.0.0 0.0.0.255

  ! Advertise uplink
  network 192.168.1.0 0.0.0.255

  ! Make access ports passive (don't send EIGRP packets)
  passive-interface default
  no passive-interface GigabitEthernet0/1

  ! Optional: redistribute static routes
  redistribute static metric 1000000 100 255 1 1500

end
```

**Branch Router Configuration:**

```ios

configure terminal

interface Loopback0
  ip address 10.0.0.2 255.255.255.255

interface GigabitEthernet0/1
  description "Link to HQ"
  ip address 192.168.1.2 255.255.255.0
  bandwidth 1000000
  no shutdown

interface Vlan100
  ip address 10.100.0.2 255.255.255.0
  no shutdown

router eigrp 100
  eigrp router-id 10.0.0.2

  network 10.0.0.0 0.0.255.255
  network 10.100.0.0 0.0.0.255
  network 192.168.1.0 0.0.0.255

  passive-interface default
  no passive-interface GigabitEthernet0/1

end
```

---

## Verification and Monitoring

### Check EIGRP Status

```ios

show ip eigrp summary

! Output shows process ID, router ID, and interface count
```

### Check EIGRP Neighbors

```ios

show ip eigrp neighbors detail

! Shows full neighbor details: IP, interface, hold time, uptime, sequence numbers
```

### Check EIGRP Routing Table

```ios

show ip route eigrp

! Shows all routes learned via EIGRP
! Format: D 10.0.0.0/24 [90/409600] via 192.168.1.2, 00:05:22, GigabitEthernet0/1

! Breakdown:
! D = EIGRP route
! 10.0.0.0/24 = destination
! [90/409600] = [Administrative Distance / Metric]
! 192.168.1.2 = next-hop router
! GigabitEthernet0/1 = egress interface
```

### Check EIGRP Topology

```ios

show ip eigrp topology

! Shows all networks known to EIGRP and their metrics
! Including feasible successors (backup routes ready if primary fails)
```

### Debug EIGRP Packets

```ios

debug ip eigrp packets

! Shows EIGRP hello, update, query, reply packets in real-time
! Warning: generates lots of output; use carefully

undebug all  ! Turn off debugging
```

---

## Common Issues and Fixes

### Issue: Neighbors Not Forming

**Cause:** AS number mismatch, IP connectivity issue, or interface shutdown.

**Check:**

```ios

show ip eigrp neighbors
! Should show at least one neighbor; if empty, check below

show ip eigrp summary
! Verify process exists and router ID is set

show interface GigabitEthernet0/1 | include up
! Ensure interface is "up, line protocol is up"

ping 192.168.1.2
! Verify IP connectivity
```

**Fix:**

```ios

configure terminal

router eigrp 100
  ! Verify AS number matches neighbor (show ip eigrp summary)

  ! Verify network statement includes neighbor IP
  network 192.168.1.0 0.0.0.255

  ! Verify interface is not passive
  no passive-interface GigabitEthernet0/1

end
```

### Issue: Routes Not Learned

**Cause:** Neighbor down, network not advertised, or no feasible path.

**Check:**

```ios

show ip eigrp neighbors
! Verify neighbor is "up"

show ip eigrp topology
! Check if destination is in topology table

show ip route eigrp
! Verify routes appear in routing table
```

**Fix:**

```ios

configure terminal

router eigrp 100
  ! Ensure destination network is advertised on neighbor
  network 10.0.0.0 0.0.255.255  ! Must match neighbor's networks

end
```

### Issue: Suboptimal Path Selected

**Cause:** Bandwidth or delay incorrectly configured on interfaces.

**Check:**

```ios

show interface GigabitEthernet0/1 | include BW
! Verify bandwidth is correct (should be actual link speed)

show ip eigrp topology <destination>
! Check metric calculations
```

**Fix:**

```ios

configure terminal

interface GigabitEthernet0/1
  ! Set correct bandwidth (in kbps)
  bandwidth 1000000  ! 1 Gbps

end
```

### Issue: EIGRP Neighbor Flapping (Repeatedly Up/Down)

**Cause:** Network instability, hold time too short, or MTU mismatch.

**Check:**

```ios

debug ip eigrp packets
! Look for hello timeout messages

show interface GigabitEthernet0/1
! Check for errors, drops, or MTU mismatch
```

**Fix:**

```ios

configure terminal

interface GigabitEthernet0/1
  ! Increase hold time for unstable WAN links
  ip hold-time eigrp 100 45  ! Default 15, increase to 45

  ! Ensure MTU is same on both sides
  ip mtu 1500

end
```

---

## Best Practices

| Practice | Reason |
| --- | --------- |
| Use single AS number across network | Simplifies design and troubleshooting |
| Set explicit router ID | Stable identifier instead of relying on interface IPs |
| Configure bandwidth on WAN links | Ensures correct metric calculation |
| Use passive-interface on access ports | Prevents unnecessary EIGRP traffic |
| Monitor EIGRP neighbors regularly | Early warning of topology instability |
| Test connectivity before EIGRP | Ensures underlying IP connectivity works |
| Document network design | Facilitates future changes and troubleshooting |
| Set appropriate hello/hold timers | Balance convergence speed vs network stability |
| Verify K-values match across network | Prevents unexpected metric mismatches |

---

## Configuration Checklist

- [ ] Set unique router ID on each router
- [ ] Create loopback interface for router ID
- [ ] Configure EIGRP AS number (same on all routers)
- [ ] Add network statements for all subnets
- [ ] Configure bandwidth on WAN interfaces
- [ ] Set passive-interface on access ports
- [ ] Verify neighbor state with `show ip eigrp neighbors`
- [ ] Check learned routes with `show ip route eigrp`
- [ ] Test connectivity via EIGRP routes
- [ ] Monitor neighbor stability
- [ ] Save configuration (`write memory`)

---

## Quick Reference

```ios

! Enable EIGRP
router eigrp 100
  eigrp router-id 10.0.0.1
  network 192.168.1.0 0.0.0.255
  network 10.0.0.0 0.0.255.255
  passive-interface default
  no passive-interface GigabitEthernet0/1
end

! Check neighbors
show ip eigrp neighbors

! Check routes
show ip route eigrp

! Check topology
show ip eigrp topology

! Debug
debug ip eigrp packets
undebug all
```
