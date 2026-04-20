# FortiGate BGP Minimal Configuration

This template establishes a single EBGP peering session. Replace CAPITALIZED values.

## Configuration Breakdown

```fortios
config router bgp
  set as 65000
```

Enables BGP with **local ASN 65000**. Replace with your autonomous system number.

```fortios
  set router-id 10.0.0.1
```

Sets the BGP router ID to **10.0.0.1**. Must be unique. Replace with a loopback or unique IP.

```fortios
  config neighbor
    edit "10.0.0.2"
      set remote-as 65001
    next
  end
```

Declares a neighbor:

- **10.0.0.2** = neighbor's IP (must be reachable)
- **65001** = neighbor's ASN

```fortios
  config network
    edit 1
      set prefix 10.1.0.0 255.255.0.0
    next
    edit 2
      set prefix 10.2.0.0 255.255.0.0
    next
  end
```

Advertises two networks:

- **10.1.0.0/16** (replace with your first subnet)
- **10.2.0.0/16** (replace with your second subnet)

## Customization

### Change ASN

Replace `65000` (your ASN) and `65001` (neighbor ASN).

### Change Neighbor IP

Replace `10.0.0.2` with neighbor's IP.

### Change Router ID

Replace `10.0.0.1` with your unique ID (loopback preferred).

### Add More Networks

```fortios
edit 3
  set prefix 10.3.0.0 255.255.0.0
next
edit 4
  set prefix 10.4.0.0 255.255.0.0
next
```

### Convert to iBGP

Change `remote-as 65001` to `remote-as 65000` (same ASN).

## Verification

After applying:

```fortios
get router info bgp summary
! Check: Neighbor state = "Established"

get router info routing-table bgp
! Check: BGP-learned routes

diagnose ip route list
! Detailed routing table
```

## Next Steps

- Add BFD for faster failure detection (see [BFD minimal](bfd-minimal.md))
- Review [FortiGate BGP guide](../../fortigate/fortigate_bgp_config.md)
