# Cisco BFD Minimal Configuration

This template enables BFD (Bidirectional Forwarding Detection) to detect link failures in sub-second
time, integrated with BGP for fast failover.

## Configuration Breakdown

```ios
interface GigabitEthernet0/0/0
  bfd interval 300 min_rx 300 multiplier 3
```

Configures BFD on the interface:

- **interval 300**: Send BFD packets every 300ms (3.3 per second)
- **min_rx 300**: Expect to receive packets every 300ms
- **multiplier 3**: Declare link down after 3 missed packets (900ms total)

**Failure detection time:** ~900ms

```ios
router bgp 65000
  neighbor 10.0.0.2 fall-over bfd single-hop
```

Tells BGP to use BFD for faster neighbor failure detection instead of waiting 180+ seconds for BGP
timers.

- **fall-over bfd**: BGP listens to BFD for neighbor status
- **single-hop**: BFD assumes direct link (no hops between)

## Customization

### Change Interface

Replace `GigabitEthernet0/0/0` with your interface.

### Change BFD Timers

For faster detection (aggressive):

```ios
bfd interval 100 min_rx 100 multiplier 3
! Detects failure in ~300ms
```

For slower detection (conservative, less CPU):

```ios
bfd interval 1000 min_rx 1000 multiplier 3
! Detects failure in ~3 seconds
```

### Use with OSPF

```ios
router ospf 1
  neighbor 10.0.0.2 interface GigabitEthernet0/0/0 bfd
```

Or configure BFD on OSPF process:

```ios
router ospf 1
  bfd all-interfaces
```

### Use with EIGRP

```ios
router eigrp 100
  bfd all-interfaces
```

## Verification

After applying:

```ios
show bfd session
! Check: Session state = UP, detection time ~900ms

show bfd neighbors
! Check: BFD peer status

show ip bgp neighbors 10.0.0.2
! Check: BGP using BFD for failure detection
```

- Review [BFD configuration guide](../cisco/cisco_bfd_config_guide.md) for advanced features
- Combine with HSRP for redundant gateways (see [HSRP minimal](hsrp-minimal.md))
