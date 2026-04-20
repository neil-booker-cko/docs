# Cisco OSPF Minimal Configuration

This template establishes OSPF in a single area. Replace CAPITALIZED values with your network.

## Configuration Breakdown

```ios
router ospf 1
```

Enables OSPF with **process ID 1**. This is local significance only; neighbors can have different
IDs. Replace with your preferred process ID (typically 1 for simplicity).

```ios
  router-id 10.0.0.1
```

Sets the OSPF router ID to **10.0.0.1**. Must be unique within the OSPF domain. Typically a
loopback IP. Replace with your loopback address.

```ios
  network 10.0.0.0 0.0.0.255 area 0
  network 10.1.0.0 0.0.255.255 area 0
```

Announces two subnets in **area 0** (backbone area):

- **10.0.0.0/24** (replace with your first subnet)
- **10.1.0.0/16** (replace with your second subnet)

Each `network` statement uses:

- Network address (e.g., `10.0.0.0`)
- Wildcard mask (inverse of subnet mask; e.g., `0.0.0.255` for /24)
- Area (use `0` for single-area OSPF)

Add more `network` lines for additional subnets.

## Customization

### Change Router ID

Replace `10.0.0.1` with your router's unique loopback IP.

### Add More Networks

For each additional network:

```ios
network 10.2.0.0 0.0.255.255 area 0
network 192.168.0.0 0.0.0.255 area 0
```

### Wildcard Mask Conversion

| Subnet Mask | Wildcard Mask |
| --- | --- |
| 255.255.255.0 | 0.0.0.255 |
| 255.255.0.0 | 0.0.255.255 |
| 255.0.0.0 | 0.255.255.255 |
| 255.255.255.128 | 0.0.0.127 |

### Add a Second Area

For multi-area OSPF, add networks to area 1:

```ios
network 10.100.0.0 0.0.255.255 area 1
```

Area 0 is the backbone; all other areas must connect through it.

## Verification

After applying:

```ios
show ip ospf
! Check: OSPF is running, router ID set

show ip ospf neighbors
! Check: Neighbors appear with state "FULL"

show ip ospf database
! Check: LSA database populated

show ip route ospf
! Check: OSPF-learned routes in routing table
```

## Next Steps

- Add BFD for faster failure detection (see `bfd-minimal.md`)
- Implement area design for scalability (see [OSPF configuration guide](../../cisco/cisco_ospf_config.md))
- Configure OSPF authentication for security
