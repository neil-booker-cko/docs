# FortiGate VRRP Minimal Configuration

This template enables VRRP (Virtual Router Redundancy Protocol) for gateway failover. Two or more
FortiGates share a virtual IP, and the highest-priority device becomes the active master.

## Configuration Breakdown

```fortios
config system vrrp
  edit 1
    set vrdst 10.0.0.0 255.255.0.0
    set interface "port1"
    set vrtype v2
    set vrid 100
    set priority 150
    set adv-interval 1
    set preempt enable
    set status enable
    set version 2
  next
end
```

Configures a VRRP group:

- **vrdst 10.0.0.0/16** = virtual IP and mask (the shared gateway IP clients use)
- **interface port1** = interface for VRRP advertisements (replace with your port)
- **vrid 100** = VRRP group ID (must be same on all devices in group)
- **priority 150** = VRRP priority (higher wins; range 0-254)
- **adv-interval 1** = advertisement interval in seconds
- **preempt enable** = allow higher-priority device to take over (use `disable` for avoid
  flapping)

- **status enable** = enable VRRP on this group
- **version 2** = VRRPv2 (use `version 3` for VRRPv3 with IPv6 support)

**On backup device:** Set `priority 100` (lower than master).

```fortios
config firewall policy
  edit 1
    set srcintf "port2"
    set dstintf "port1"
    set srcaddr "internal-subnets"
    set dstaddr "all"
    set action accept
    set schedule "always"
    set service "ALL"
  next
end
```

Creates a firewall policy allowing traffic from internal clients to the gateway (replace with your
policy).

## Customization

### Change Virtual IP (Gateway Address)

Replace `10.0.0.0 255.255.0.0` with your virtual gateway address:

```fortios
set vrdst 192.168.1.0 255.255.255.0
```

### Change Interface

Replace `port1` with your LAN-facing interface (port2, port3, VLAN1, etc.).

### Change VRRP Group ID

Replace `vrid 100` with a unique ID per VRRP group (range 1-255):

```fortios
set vrid 1    ! First gateway pair
set vrid 2    ! Second gateway pair (on different subnet)
```

### Configure Backup Device

On a secondary FortiGate, use a lower priority:

```fortios
set priority 100
! Master has 150, so this becomes backup
```

### Change Priority Thresholds

For 3-FortiGate clusters:

```fortios
Master:      priority 150
Backup 1:    priority 100
Backup 2:    priority 50
```

### Disable Preemption (Avoid Flapping)

If master device restarts frequently:

```fortios
set preempt disable
! Backup keeps control even if master comes back online
```

### Use VRRPv3 for IPv6

```fortios
set version 3
set vrtype v3
! VRRPv3 supports both IPv4 and IPv6 addresses
```

### Enable Health Checks

Monitor interface or system status:

```fortios
set http-get-interval 10
! Check HTTP service every 10 seconds (optional)
```

## Verification

After applying on both devices:

```fortios
get system vrrp status
! Check: Master device shows "Master", backup shows "Backup"

get system vrrp interface
! Check: VRRP group status and priority

diagnose ip address list
! Check: Virtual IP present on master interface

get system interface port1
! Verify interface settings
```

On a client, check reachability to virtual IP:

```bash
ping VIRTUAL_IP
# Should respond from the active master
```

- Add BFD to detect link failures (see [BFD minimal](bfd-minimal.md))
- Review [HSRP minimal](../cisco/hsrp-minimal.md) for Cisco equivalent
