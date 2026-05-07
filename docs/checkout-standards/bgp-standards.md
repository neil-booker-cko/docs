# BGP Configuration Standards

BGP configuration and operational standards for Checkout.

---

## BGP Process Configuration

**Standard:** Single BGP process (AS 65000) for all VRFs.

```ios
router bgp 65000
 bgp router-id 10.0.0.1
 bgp log-neighbor-changes
 bgp graceful-restart
```

---

## BGP Timers

### Standard Timers

| Timer | Value | Use Case |
| --- | --- | --- |
| Keepalive | 10 seconds | Normal operation |
| Hold time | 30 seconds | Detection timeout (3x keepalive) |

### Fast Failure (with BFD)

| Timer | Value | Use Case |
| --- | --- | --- |
| Keepalive | 60 seconds | BFD handles fast detection |
| Hold time | 180 seconds | Longer hold (BFD sub-second) |
| BFD interval | 300ms tx/rx | Sub-second failover |

**Configuration:**

```ios
neighbor 169.254.1.2 timers 10 30
neighbor 169.254.1.2 fall-over bfd
```

---

## Address Families and VRF Configuration

**Standard:** One address family per VRF under single BGP process.

```ios
router bgp 65000
 address-family ipv4 vrf AWS
  neighbor 169.254.1.2 activate
  neighbor 10.254.1.2 activate
 exit-address-family

 address-family ipv4 vrf AZURE
  neighbor 172.16.0.2 activate
  neighbor 10.254.2.2 activate
 exit-address-family
```

---

## Route Filtering Standards

### Cloud Provider Routes (Inbound)

Accept all routes from cloud providers without filtering. BGP community filtering may be
applied at the overlay layer (FortiGate).

### Internal Routes (Outbound to Cloud)

Advertise only the transport link subnets to cloud providers. DO NOT advertise internal
prefixes.

---

## BGP Communities

TODO: Define standard community values

---

## Graceful Restart

**Standard:** Enable BGP graceful restart for planned maintenance.

```ios
bgp graceful-restart
```

---

## BFD Configuration

See [Cisco BFD Configuration](../cisco/bfd-config.md) for detailed setup.

---

## Troubleshooting Commands

```ios
show bgp vpnv4 unicast all summary
show bgp vpnv4 unicast vrf AWS summary
show bgp vpnv4 unicast vrf AWS neighbors 169.254.1.2
debug bgp keepalives
```

---

## Related Standards

- [Routing Design](routing-design.md)
- [Naming Conventions](naming-conventions.md)
