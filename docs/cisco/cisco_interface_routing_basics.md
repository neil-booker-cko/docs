# Cisco IOS-XE Interface and Routing Basics

Complete reference for configuring interfaces and basic static routing on Cisco IOS-XE
platforms.

## Quick Start: Configure an Interface

```ios
configure terminal

! Assign IP address and enable
interface GigabitEthernet0/1
  description "Link to Core Router"
  ip address 192.168.1.1 255.255.255.0
  no shutdown

! Verify
end
show interface GigabitEthernet0/1 brief
show ip interface brief
```

---

## Physical Interface Configuration

### Basic Setup

```ios

configure terminal

interface GigabitEthernet0/1
  ! Add description for clarity
  description "Uplink to Core"

  ! Assign IP address (CIDR format: 192.168.1.0/24)
  ip address 192.168.1.1 255.255.255.0

  ! Enable interface (no shutdown)
  no shutdown

  ! Optional: Set bandwidth (for routing metrics)
  bandwidth 1000000  ! 1 Gbps in kbps

end
```

### Interface Speed/Duplex (Gigabit Typically Auto)

```ios

configure terminal

interface FastEthernet0/1
  ! For older FastEthernet interfaces (not needed for Gigabit)
  speed 100
  duplex full

  no shutdown

end
```

### MTU Configuration

```ios

configure terminal

interface GigabitEthernet0/1
  ! Default is 1500 bytes
  ip mtu 1500

  ! For jumbo frames
  ip mtu 9000

end
```

---

## VLAN Interface Configuration

VLAN interfaces allow Layer 3 routing between VLANs.

### Create VLAN Interface (SVI)

```ios

configure terminal

! First, create VLAN
vlan 100
  name "Production"

! Create Layer 3 interface on VLAN 100
interface Vlan100
  description "Production VLAN Gateway"
  ip address 10.100.0.1 255.255.255.0
  no shutdown

end
```

### Assign Physical Ports to VLAN

```ios

configure terminal

interface GigabitEthernet0/1
  ! Access port (single VLAN)
  switchport mode access
  switchport access vlan 100

interface GigabitEthernet0/2
  ! Trunk port (all VLANs)
  switchport mode trunk
  switchport trunk allowed vlan 100,200,300

end
```

---

## Loopback Interface Configuration

Loopback interfaces never go down and are ideal for router ID.

```ios

configure terminal

interface Loopback0
  description "Router ID"
  ip address 10.0.0.1 255.255.255.255

end

! Verify loopback is always up
show interface Loopback0
```

### Router ID Configuration (for BGP/OSPF)

```ios

configure terminal

! For BGP
router bgp 65000
  bgp router-id 10.0.0.1

! For OSPF
router ospf 1
  router-id 10.0.0.1

end
```

---

## Static Routing

### Basic Static Route

Manually specify destination and next-hop for traffic.

```ios

configure terminal

! Route to 10.0.0.0/24 via 192.168.1.254
ip route 10.0.0.0 255.255.255.0 192.168.1.254

end

! Verify
show ip route static
```

### Default Route

Catches all traffic without explicit route.

```ios

configure terminal

! Default route to ISP or core
ip route 0.0.0.0 0.0.0.0 192.168.1.254

end

! Verify
show ip route
! Should show: S* 0.0.0.0/0 [1/0] via 192.168.1.254
```

### Static Route with Metric (Administrative Distance)

Lower distance = higher priority (trusted more).

```ios

configure terminal

! Primary route (AD 1, default)
ip route 10.0.0.0 255.255.255.0 192.168.1.254

! Backup route (AD 10, only used if primary fails)
ip route 10.0.0.0 255.255.255.0 192.168.1.2 10

end
```

### Static Route via Interface

```ios

configure terminal

! Route via specific egress interface
ip route 10.0.0.0 255.255.255.0 GigabitEthernet0/1

end
```

---

## Complete Configuration Example

### Scenario: Branch Router with Dual Uplinks

```text

ISP-1 (Primary)        ISP-2 (Backup)
   |                        |
Gi0/1 (192.168.1.1)   Gi0/2 (192.168.2.1)
   |                        |
  [Branch Router]
   |
Vlan100 (10.0.0.1)
   |
[LAN Users]
```

**Branch Router Configuration:**

```ios

configure terminal

! === Loopback (Router ID) ===
interface Loopback0
  description "Router ID"
  ip address 10.0.100.1 255.255.255.255

! === Uplink to ISP-1 (Primary) ===
interface GigabitEthernet0/1
  description "Primary uplink to ISP-1"
  ip address 192.168.1.1 255.255.255.0
  bandwidth 100000  ! 100 Mbps
  no shutdown

! === Uplink to ISP-2 (Backup) ===
interface GigabitEthernet0/2
  description "Backup uplink to ISP-2"
  ip address 192.168.2.1 255.255.255.0
  bandwidth 100000
  no shutdown

! === LAN VLAN ===
vlan 100
  name "Branch LAN"

interface Vlan100
  description "Branch LAN Gateway"
  ip address 10.0.0.1 255.255.255.0
  no shutdown

! Assign access ports to VLAN 100
interface range GigabitEthernet0/3 - 24
  switchport mode access
  switchport access vlan 100
  spanning-tree portfast
  spanning-tree bpduguard enable

! === Routing ===
! Primary default route via ISP-1
ip route 0.0.0.0 0.0.0.0 192.168.1.254 1

! Backup default route via ISP-2 (AD 10, only if primary fails)
ip route 0.0.0.0 0.0.0.0 192.168.2.254 10

! Static route to HQ via ISP-1
ip route 10.1.0.0 255.255.0.0 192.168.1.254

end

! Verify
show ip route
show interface brief
```

---

## Verification and Troubleshooting

### Check Interface Status

```ios

! Brief summary of all interfaces
show ip interface brief

! Expected output:
! Interface        IP-Address      OK? Method Status
! GigabitEthernet0/1  192.168.1.1  YES manual up
! GigabitEthernet0/2  192.168.2.1  YES manual up
! Vlan100         10.0.0.1       YES manual up
! Loopback0       10.0.100.1     YES manual up
```

### Detailed Interface Information

```ios

! Detailed info on single interface
show interface GigabitEthernet0/1

! Look for:
! - "up, line protocol is up" (both layers working)
! - IP address, subnet mask
! - MTU size
! - Encapsulation type
```

### Check IP Configuration

```ios

! All interfaces with IP addresses
show ip interface brief

! Detailed IP configuration
show ip interface GigabitEthernet0/1
```

### Verify Routing Table

```ios

! Full routing table
show ip route

! Static routes only
show ip route static

! Routes to specific destination
show ip route 10.0.0.0

! Look for:
! - Route destination and mask
! - Next-hop IP
! - Administrative distance and metric
! - [AD/Metric] format
```

### Test Connectivity

```ios

! Ping next-hop router
ping 192.168.1.254

! Expected: "!!!!!  Success rate is 100 percent"

! Traceroute to destination
traceroute 10.1.1.1

! Shows each hop on path to destination
```

---

## Common Issues and Fixes

### Issue: Interface Down

**Cause:** Cable not connected, interface shutdown, or layer 2 issue.

**Check:**

```ios

show interface GigabitEthernet0/1

! Look for:
! - "down, line protocol is down" → Cable disconnected
! - "administratively down" → Someone ran "shutdown"
```

**Fix:**

```ios

configure terminal

interface GigabitEthernet0/1
  no shutdown

end
```

### Issue: No IP Address on Interface

**Cause:** IP not assigned or VLAN doesn't exist.

**Check:**

```ios

show ip interface brief
show ip interface GigabitEthernet0/1
```

**Fix:**

```ios

configure terminal

interface GigabitEthernet0/1
  ip address 192.168.1.1 255.255.255.0
  no shutdown

end
```

### Issue: Can't Ping Next-Hop

**Cause:** Interface down, cable issue, firewall ACL blocking ICMP, or wrong IP.

**Troubleshoot:**

```ios

! 1. Check interface status
show interface GigabitEthernet0/1

! 2. Verify IP address
show ip interface brief

! 3. Check for ACL blocking ICMP
show ip access-list

! 4. Test with verbose ping
ping 192.168.1.254 verbose

! 5. Traceroute to see where it fails
traceroute 192.168.1.254
```

### Issue: Wrong Routing Table Entry

**Cause:** Static route misconfigured or mask incorrect.

**Check:**

```ios

show ip route | include 10.0.0.0

! Verify destination, mask, and next-hop are correct
```

**Fix:**

```ios

configure terminal

! Remove incorrect route
no ip route 10.0.0.0 255.255.255.0 192.168.1.2

! Add correct route
ip route 10.0.0.0 255.255.255.0 192.168.1.254

end
```

### Issue: Traffic Not Routing Correctly (Takes Wrong Path)

**Cause:** Metric/AD not tuned correctly or primary link not preferred.

**Check:**

```ios

show ip route

! Verify the preferred route has lower AD/metric
```

**Fix:** Adjust administrative distance

```ios

configure terminal

! Primary route (preferred)
ip route 0.0.0.0 0.0.0.0 192.168.1.254 1

! Backup route (fallback)
ip route 0.0.0.0 0.0.0.0 192.168.2.254 10

end
```

---

## Best Practices

| Practice | Reason |
| --- | --------- |
| Use descriptive interface descriptions | Troubleshooting clarity |
| Set loopback for router ID | Stable identifier |
| Use default route for ISP/core | Simplifies routing table |
| Set backup route with higher AD | Automatic failover without BGP |
| Assign IP to every interface | Enables management and routing |
| Test connectivity before production | Catch issues early |
| Document IP plan | Prevents conflicts |
| Use CIDR notation in planning | Easier subnet math |
| Enable PortFast on access ports | Faster user connectivity |
| Monitor interface statistics | Early detection of congestion |

---

## Configuration Checklist

- [ ] Assign IP address to interface
- [ ] Run `no shutdown` to enable
- [ ] Verify `show interface` shows "up, line protocol is up"
- [ ] Test ping to next-hop
- [ ] Add static route(s) if needed
- [ ] Set backup route with higher AD
- [ ] Verify routing table with `show ip route`
- [ ] Test end-to-end connectivity
- [ ] Save configuration (`write memory` or `copy running-config startup-config`)

---

## Quick Reference

```ios

! Configure interface
configure terminal
interface GigabitEthernet0/1
  description "description"
  ip address 192.168.1.1 255.255.255.0
  no shutdown
end

! Add static route
configure terminal
ip route <dest-network> <mask> <next-hop> [AD]
end

! Verify
show ip route
show interface brief
ping <IP>
traceroute <IP>
```
