# FortiGate BFD Minimal Configuration

This template enables BFD (Bidirectional Forwarding Detection) to detect link failures in sub-second
time, integrated with BGP for fast failover.

## Configuration Breakdown

```fortios
config system bfd
  set default-multiplier 3
  set default-min-rx 300
  set default-min-tx 300
end
```

Sets global BFD defaults:

- **default-multiplier 3**: Declare link down after 3 missed packets
- **default-min-rx 300**: Expect to receive packets every 300ms
- **default-min-tx 300**: Send BFD packets every 300ms

**Failure detection time:** ~900ms (3 packets × 300ms)

```fortios
config router bfd
  config neighbor
    edit 1
      set ip 10.0.0.2
      set interface "port1"
      set multiplier 3
      set min-rx 300
      set min-tx 300
    next
  end
end
```

Configures a BFD neighbor:

- **10.0.0.2** = neighbor's IP (must be reachable)
- **port1** = interface name
- **multiplier 3** = failure threshold (3 missed packets)
- **min-rx/min-tx 300** = timer intervals in milliseconds

```fortios
config router bgp
  ...
  config neighbor
    edit "10.0.0.2"
      set bfd enable
    next
  end
end
```

Tells BGP to use BFD for faster neighbor failure detection instead of waiting 180+ seconds for BGP
timers.

## Customization

### Change Interface

Replace `port1` with your interface (port2, port3, etc. or VLAN name).

### Change BFD Neighbor IP

Replace `10.0.0.2` with the neighbor's IP address.

### Change BFD Timers

For faster detection (aggressive):

```fortios
set default-min-rx 100
set default-min-tx 100
! Detects failure in ~300ms
```

For slower detection (conservative, less CPU):

```fortios
set default-min-rx 1000
set default-min-tx 1000
! Detects failure in ~3 seconds
```

### Use with OSPF

Enable BFD for OSPF neighbors:

```fortios
config router ospf
  config ospf-interface
    edit "port1"
      set bfd enable
    next
  end
end
```

### Use with EIGRP

Enable BFD for EIGRP neighbors:

```fortios
config router eigrp
  config network
    edit 1
      set bfd-status enable
    next
  end
end
```

## Verification

After applying:

```fortios
get router info bfd neighbors
! Check: BFD session status = UP

diagnose sys bfd-monitor
! Check: BFD session details and status

get router info bgp neighbors 10.0.0.2
! Check: BGP neighbor using BFD
```

- Combine with VRRP for redundant gateways (see [VRRP minimal](vrrp-minimal.md))
