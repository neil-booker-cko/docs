# Cisco BGP Minimal Configuration

This template establishes a single EBGP (External BGP) peering session. Replace the values in
CAPITALIZED format with your environment.

## Configuration Breakdown

```ios
router bgp 65000
```

Enables BGP with **local ASN 65000**. Replace with your autonomous system number.

```ios
  bgp router-id 10.0.0.1
```

Sets the BGP router ID to **10.0.0.1**. Must be unique within your BGP network. Typically the
router's loopback IP. Replace with your loopback address.

```ios
  neighbor 10.0.0.2 remote-as 65001
```

Declares a neighbor at **10.0.0.2** with ASN **65001**. Replace both values:

- `10.0.0.2` = neighbor's IP (should be reachable from your router)
- `65001` = neighbor's ASN

```ios
  address-family ipv4
    neighbor 10.0.0.2 activate
    network 10.1.0.0 mask 255.255.0.0
    network 10.2.0.0 mask 255.255.0.0
  exit-address-family
```

Activates IPv4 address family and advertises two networks:

- **10.1.0.0/16** (replace with your first subnet)
- **10.2.0.0/16** (replace with your second subnet)

Add more `network` lines if you have additional subnets to advertise.

## Customization

### Change ASN

Replace `65000` (your ASN) and `65001` (neighbor ASN) with your values.

### Change Neighbor IP

Replace `10.0.0.2` with your neighbor's IP address. This must be reachable (route exists to it).

### Change Router ID

Replace `10.0.0.1` with your router's loopback IP (or any unique IP in your BGP domain).

### Add More Networks

For each additional network, add a line:

```ios
network 10.3.0.0 mask 255.255.0.0
network 10.4.0.0 mask 255.255.0.0
```

### Convert to iBGP (Internal BGP)

To peer with another router in the **same** ASN, change:

```ios
neighbor 10.0.0.2 remote-as 65001    ! EBGP (different ASNs)
```

to:

```ios
neighbor 10.0.0.2 remote-as 65000    ! iBGP (same ASN)
```

Note: iBGP requires either a loopback-to-loopback peering or route reflectors for scalability.

## Verification

After applying, verify the configuration:

```ios
show ip bgp summary
! Check: Neighbor state should be "Established"

show ip bgp neighbors 10.0.0.2
! Check: Session state, received/sent prefixes

show ip route bgp
! Check: BGP-learned routes appear in routing table
```

- Add more neighbors as needed
- Implement route filtering (prefix lists, route maps)
- Add BFD for faster failure detection (see `bfd-minimal.md`)
- Review [BGP configuration guide](../cisco/cisco_bgp_ibgp.md) for advanced features
