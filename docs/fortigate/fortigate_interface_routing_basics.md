# FortiGate Interface and Routing Basics

Complete reference for configuring interfaces and basic static routing on Fortinet
FortiGate.

## Quick Start: Configure an Interface

```text
config system interface
  edit "port1"
    set description "Link to Core Router"
    set ip 192.168.1.1 255.255.255.0
    set status up
  next
end
```

---

## Physical Interface Configuration

### Basic Setup

```text

config system interface
  edit "port1"
    ! Interface alias/description
    set alias "Uplink-Core"
    set description "Primary uplink"

    ! IP address configuration
    set ip 192.168.1.1 255.255.255.0

    ! Enable interface
    set status up

    ! Interface role (see interface types below)
    set type physical
  next
end
```

### Interface Types

| Type | Purpose | Example |
| --- | --------- | --- |
| **Physical** | Direct physical port | port1, port2 |
| **Aggregate** | Port channel / LAG | aggregate1 |
| **VLAN** | Virtual interface on VLAN | vlan100, vlan200 |
| **Loopback** | Virtual interface (always up) | loopback |
| **Tunnel** | Tunnel interface (IPsec, GRE) | tunnel1 |
| **VDOM-Link** | Inter-VDOM traffic | vdom-link0 |

### Configure Port Speed/Duplex

```text

config system interface
  edit "port1"
    ! Speed: 'auto', '10full', '10half', '100full', '100half', '1000full'
    set speed 1000full

    ! Duplex: 'auto', 'full', 'half'
    set duplex full
  next
end
```

### MTU Configuration

```text

config system interface
  edit "port1"
    ! Default 1500, jumbo frames 9000
    set mtu 1500

    ! MTU for IP forwarding (different from physical MTU)
    set mtu-override enable
  next
end
```

---

## VLAN Interface Configuration

### Create VLAN Interface

```text

config system interface
  edit "vlan100"
    set vdom "root"
    set type vlan

    ! Physical interface to tag on
    set interface "port1"

    ! VLAN ID
    set vlanid 100

    ! IP address on VLAN
    set ip 10.100.0.1 255.255.255.0

    set status up
  next
end
```

### Assign Physical Port to VLAN (Access Port)

```text

config system interface
  edit "port2"
    set vdom "root"
    set type physical

    ! This port belongs to VLAN 100
    ! (FortiGate uses implicit VLAN assignment)
    set ip 10.100.0.254 255.255.255.0

    set status up
  next
end
```

### Trunk Port (Multiple VLANs)

```text

config system interface
  edit "port1"
    set type physical
    set status up
    ! Tagging configuration is implicit via VLAN interface assignments
    ! Multiple VLAN interfaces can use the same physical port
  next

  edit "vlan100"
    set interface "port1"  ! Uses port1
    set vlanid 100
    set ip 10.100.0.1 255.255.255.0
  next

  edit "vlan200"
    set interface "port1"  ! Same port, different VLAN
    set vlanid 200
    set ip 10.200.0.1 255.255.255.0
  next
end
```

---

## Loopback Interface Configuration

Loopback interfaces never go down and are ideal for router ID.

```text

config system interface
  edit "loopback"
    set vdom "root"
    set type loopback
    set ip 10.0.0.1 255.255.255.255
    set status up
  next
end

! Verify loopback is always up
get system interface loopback
```

### Router ID Configuration

```text

config router settings
  set router-id 10.0.0.1
end
```

---

## Static Routing

### Basic Static Route

```text

config router static
  edit 1
    ! Destination network
    set destination 10.0.0.0 255.255.255.0

    ! Next-hop gateway
    set gateway 192.168.1.254

    ! Egress interface
    set device "port1"

    ! Distance/priority (lower = preferred)
    set distance 1
  next
end
```

### Default Route

```text

config router static
  edit 1
    set destination 0.0.0.0 0.0.0.0
    set gateway 192.168.1.254
    set device "port1"
  next
end
```

### Backup Route (Failover)

```text

config router static
  edit 1
    set destination 0.0.0.0 0.0.0.0
    set gateway 192.168.1.254   ! Primary
    set device "port1"
    set distance 1
  next

  edit 2
    set destination 0.0.0.0 0.0.0.0
    set gateway 192.168.2.254   ! Backup
    set device "port2"
    set distance 10             ! Higher distance (less preferred)
  next
end
```

---

## Complete Configuration Example

### Scenario: Branch FortiGate with Dual Uplinks

```text

ISP-1 (Primary)        ISP-2 (Backup)
   |                        |
port1 (192.168.1.1)   port2 (192.168.2.1)
   |                        |
  [FortiGate]
   |
vlan100 (10.0.0.1)
   |
[LAN Users]
```

**FortiGate Configuration:**

```text

! === System hostname ===
config system settings
  set hostname "FortiGate-Branch"
  set router-id 10.0.100.1
end

! === Loopback (Router ID) ===
config system interface
  edit "loopback"
    set type loopback
    set ip 10.0.100.1 255.255.255.255
    set status up
  next

  ! === Uplink to ISP-1 (Primary) ===
  edit "port1"
    set alias "Primary-ISP"
    set description "Primary uplink to ISP-1"
    set type physical
    set ip 192.168.1.1 255.255.255.0
    set status up
  next

  ! === Uplink to ISP-2 (Backup) ===
  edit "port2"
    set alias "Backup-ISP"
    set description "Backup uplink to ISP-2"
    set type physical
    set ip 192.168.2.1 255.255.255.0
    set status up
  next

  ! === LAN VLAN ===
  edit "vlan100"
    set type vlan
    set interface "port3"
    set vlanid 100
    set alias "Branch-LAN"
    set ip 10.0.0.1 255.255.255.0
    set status up
  next

  ! === LAN Access Ports ===
  edit "port3"
    set description "LAN Access"
    set type physical
    set status up
  next
end

! === Routing ===
config router static
  ! Primary default route via ISP-1
  edit 1
    set destination 0.0.0.0 0.0.0.0
    set gateway 192.168.1.254
    set device "port1"
    set distance 1
  next

  ! Backup default route via ISP-2 (only used if primary fails)
  edit 2
    set destination 0.0.0.0 0.0.0.0
    set gateway 192.168.2.254
    set device "port2"
    set distance 10
  next

  ! Static route to HQ via ISP-1
  edit 3
    set destination 10.1.0.0 255.255.0.0
    set gateway 192.168.1.254
    set device "port1"
    set distance 1
  next
end
```

---

## Verification and Troubleshooting

### Check Interface Status

```text

! Summary of all interfaces
get system interface

! Expected output shows:
! name: port1
! ip: 192.168.1.1 255.255.255.0
! status: up

! Detailed interface info
get system interface port1
```

### Check Interface List

```text

diagnose sys netlink addr list

! Shows all interfaces with IPs
```

### Verify IP Configuration

```text

! Check specific interface
get system interface port1

! Look for:
! - status: up (interface is enabled)
! - ip: X.X.X.X (IP address assigned)
! - adminlink: up (admin status)
```

### Verify Routing Table

```text

! Full routing table
get router info routing-table all

! Static routes only
get router info routing-table static

! Routes to specific destination
get router info routing-table 10.0.0.0

! Output format:
! S    10.0.0.0/24  [1/0] via 192.168.1.254, port1
! Means: Static route, AD=1, metric=0, via 192.168.1.254, egress port1
```

### Test Connectivity

```text

! Ping to test reachability
execute ping 192.168.1.254

! Expected: "5 packets transmitted, 5 packets received"

! Traceroute to see hop-by-hop path
execute traceroute 10.1.1.1

! Shows each hop on path to destination
```

---

## Common Issues and Fixes

### Issue: Interface Down

**Cause:** Interface shutdown, cable disconnected, or hardware issue.

**Check:**

```text

get system interface port1

! Look for status: up or down
```

**Fix:**

```text

config system interface
  edit "port1"
    set status up
  next
end
```

### Issue: No IP Address on Interface

**Cause:** IP not assigned.

**Check:**

```text

get system interface port1

! Verify "ip: X.X.X.X" is set
```

**Fix:**

```text

config system interface
  edit "port1"
    set ip 192.168.1.1 255.255.255.0
    set status up
  next
end
```

### Issue: Can't Ping Next-Hop

**Cause:** Interface down, wrong IP, cable issue, or firewall policy blocking ICMP.

**Troubleshoot:**

```text

! 1. Check interface is up
get system interface port1

! 2. Verify IP address
get system interface | grep -A 5 "port1"

! 3. Check firewall policy allows ICMP
get firewall policy

! 4. Test ping with verbose output
execute ping -c 5 192.168.1.254

! 5. Traceroute to see where traffic fails
execute traceroute 192.168.1.254

! 6. Check ARP to verify MAC resolution
diagnose sys arp list
```

### Issue: Wrong Routing Table Entry

**Cause:** Static route misconfigured or wrong distance.

**Check:**

```text

get router info routing-table static

! Verify destination, gateway, and distance
```

**Fix:**

```text

! Delete wrong route
config router static
  delete 1
end

! Add correct route
config router static
  edit 1
    set destination 10.0.0.0 255.255.255.0
    set gateway 192.168.1.254
    set device "port1"
  next
end
```

### Issue: Traffic Uses Wrong Path (Wrong Uplink)

**Cause:** Distance/priority not tuned correctly; primary route not preferred.

**Check:**

```text

get router info routing-table static

! Verify primary route has lower distance (lower = preferred)
```

**Fix:** Adjust distance

```text

config router static
  edit 1
    set destination 0.0.0.0 0.0.0.0
    set gateway 192.168.1.254  ! Primary ISP
    set device "port1"
    set distance 1              ! Preferred
  next

  edit 2
    set destination 0.0.0.0 0.0.0.0
    set gateway 192.168.2.254  ! Backup ISP
    set device "port2"
    set distance 10             ! Less preferred
  next
end
```

### Issue: Interface Flapping (Up/Down Repeatedly)

**Cause:** Cable issue, port misconfiguration, or hardware failure.

**Check:**

```text

diagnose sys interface list | grep port1

! Watch for rapid state changes
```

**Solution:**

```text

! 1. Check cable is firmly connected
! 2. Try different port
! 3. Check speed/duplex match both sides

config system interface
  edit "port1"
    set speed auto    ! Auto-negotiate
    set duplex auto
  next
end

! 4. If issue persists, hardware may be faulty
```

---

## Best Practices

| Practice | Reason |
| --- | --------- |
| Use descriptive interface aliases | Troubleshooting clarity |
| Set loopback for router ID | Stable identifier |
| Use default route for upstream | Simplifies routing table |
| Set backup route with higher distance | Automatic failover |
| Test connectivity before production | Catch issues early |
| Document IP addressing plan | Prevents conflicts |
| Monitor interface statistics | Early detection of issues |
| Use consistent naming | Easier to manage multi-device networks |

---

## Configuration Checklist

- [ ] Assign IP address to interface
- [ ] Set `status up` to enable
- [ ] Verify `get system interface` shows interface is up
- [ ] Test ping to next-hop gateway
- [ ] Add static route(s) if needed
- [ ] Set backup route with higher distance
- [ ] Verify routing table with `get router info routing-table`
- [ ] Test end-to-end connectivity
- [ ] Save configuration (`execute backup config ftp`)

---

## Quick Reference

```text

! Configure interface
config system interface
  edit "port1"
    set ip 192.168.1.1 255.255.255.0
    set status up
  next
end

! Add static route
config router static
  edit 1
    set destination 10.0.0.0 255.255.255.0
    set gateway 192.168.1.254
    set device "port1"
    set distance 1
  next
end

! Verify
get router info routing-table static
get system interface port1
execute ping 192.168.1.254
execute traceroute 10.0.0.1
```
