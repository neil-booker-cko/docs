# Cisco EIGRP Minimal Configuration

This template establishes EIGRP routing. Replace CAPITALIZED values with your network.

## Configuration Breakdown

```ios
router eigrp 100
```

Enables EIGRP with **AS (Autonomous System) 100**. All routers in the same EIGRP domain must
have the same AS number. Replace `100` with your AS.

```ios
  eigrp router-id 10.0.0.1
```

Sets the EIGRP router ID to **10.0.0.1**. Must be unique. Replace with your loopback IP.

```ios
  network 10.0.0.0 0.0.0.255
  network 10.1.0.0 0.0.255.255
```

Announces subnets in EIGRP using:

- Network address (e.g., `10.0.0.0`)
- Wildcard mask (e.g., `0.0.0.255` for /24)

Add more `network` lines for additional subnets.

```ios
  no auto-summary
```

Disables automatic route summarization (recommended in modern networks).

## Customization

### Change AS Number

Replace `100` with your EIGRP AS. All routers must use the same number.

### Change Router ID

Replace `10.0.0.1` with your unique loopback IP.

### Add More Networks

```ios
network 10.2.0.0 0.0.255.255
network 192.168.0.0 0.0.0.255
```

### Wildcard Mask Reference

| Subnet | Wildcard |
| --- | --- |
| /24 | 0.0.0.255 |
| /16 | 0.0.255.255 |
| /25 | 0.0.0.127 |

## Verification

After applying:

```ios
show eigrp neighbors
! Check: Neighbors appear with state "UP"

show ip route eigrp
! Check: EIGRP routes in routing table

show ip eigrp topology
! Check: Topology table for alternate routes
```

- Add BFD for faster failure detection (see [BFD minimal](bfd-minimal.md))
- Review [EIGRP configuration guide](../cisco/cisco_eigrp_config.md)
