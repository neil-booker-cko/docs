# Cisco BFD Minimal Configuration

This template enables BFD (Bidirectional Forwarding Detection) to detect link failures in sub-second
time, integrated with BGP for fast failover.

## Configuration Breakdown

### Step 1: Define a Global BFD Template

```ios
bfd-template single-hop BFD_STANDARD
 interval min-tx 300 min-rx 300 multiplier 3
 no echo
```

Configures BFD parameters for all interfaces:

- **interval min-tx 300**: Send BFD packets every 300ms (3.3 per second)
- **min-rx 300**: Expect to receive packets every 300ms
- **multiplier 3**: Declare link down after 3 missed packets (900ms total)

**Failure detection time:** ~900ms

### Step 2: Apply Template to Interfaces

```ios
interface GigabitEthernet0/0/0
  bfd template BFD_STANDARD
```

**Advantage:** Change BFD timers once in the template, and all interfaces update
automatically. No need to edit each interface individually.

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

Replace `GigabitEthernet0/0/0` with your interface. All interfaces using
`bfd template BFD_STANDARD` will inherit the same timers.

### Change BFD Timers

Modify the template definition to change all interfaces at once:

**For faster detection (aggressive):**

```ios
bfd-template single-hop BFD_STANDARD
 interval min-tx 100 min-rx 100 multiplier 3
! Detects failure in ~300ms
```

**For slower detection (conservative, less CPU):**

```ios
bfd-template single-hop BFD_STANDARD
 interval min-tx 1000 min-rx 1000 multiplier 3
! Detects failure in ~3 seconds
```

All interfaces using this template automatically get the new timers.

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
