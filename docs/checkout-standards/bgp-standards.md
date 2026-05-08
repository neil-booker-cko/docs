# BGP Configuration Standards

BGP configuration and operational standards for Checkout. All BGP configuration must use the
modern address-family approach for neighbor activation, route filtering, and policy application.
Network statements are deprecated; all VLAN/VRF routing must be explicitly configured within
address families.

---

## BGP Process Configuration

**Standard:** Single BGP process (AS 65000) for all VRFs.

```ios
router bgp 65000
 bgp router-id 10.0.0.1
 bgp log-neighbor-changes
 bgp graceful-restart
```

**Important:** Do NOT use network statements. All route advertisements and neighbor activation
must occur within address-family configuration blocks (see Address Families section below).

---

## BGP Timers & BFD (Recommended)

**Standard:** Use BFD for fast failure detection on all BGP neighbors. BFD enables sub-second
convergence and is strongly recommended for critical cloud connectivity links.

### Standard Timers (without BFD)

| Timer | Value | Use Case |
| --- | --- | --- |
| Keepalive | 10 seconds | Normal operation (fallback only) |
| Hold time | 30 seconds | Detection timeout (3x keepalive) |

### Recommended: Fast Failure (with BFD)

| Timer | Value | Use Case |
| --- | --- | --- |
| Keepalive | 60 seconds | BFD handles fast detection |
| Hold time | 180 seconds | Longer hold (BFD sub-second) |
| BFD interval | 300ms tx/rx | Sub-second failover |

**Configuration (BFD preferred):**

Define a BFD template at the global level, then apply to interfaces:

```ios
bfd-template single-hop BFD_STANDARD
 interval 300 min_rx 300 multiplier 3
!
interface GigabitEthernet0/1
 ip address 169.254.1.1 255.255.255.252
 bfd template BFD_STANDARD
!
router bgp 65000
 neighbor 169.254.1.2 timers 60 180
 neighbor 169.254.1.2 fall-over bfd
!
```

**Configuration (without BFD - fallback only):**

```ios
neighbor 169.254.1.2 timers 10 30
```

---

## BGP Authentication (Recommended)

**Standard:** Enable MD5 authentication on all BGP neighbors to prevent unauthorized route
injection and session hijacking. Use `neighbor password` command per-neighbor or globally.

```ios
router bgp 65000
 neighbor 169.254.1.2 password MyBGPAuth123!
 neighbor 172.16.0.2 password MyBGPAuth456!
!
```

**Key Management:**

- Rotate authentication keys annually
- Use strong, unique passwords per peer
- Document changes in change log
- Coordinate key rotation with peer networks (AWS, Azure, GCP)

---

## Address Families and VRF Configuration (Modern Approach)

**Standard:** Use address-family configuration for ALL neighbor activation, redistribution, route
filtering, and VRF-specific policies. This is the modern, scalable approach and is required for
all new BGP configurations.

**Key Rules:**

- Define each neighbor in address-family block (not in global config)
- Use one address-family per VRF
- Apply prefix-lists and route-maps within address-family
- Do NOT use network statements; use redistribute or explicit neighbor advertisement

```ios
router bgp 65000
 address-family ipv4 vrf AWS
  neighbor 169.254.1.2 activate
  neighbor 169.254.1.2 prefix-list PL_AWS_INTERNAL in
  neighbor 169.254.1.2 route-map RM_AWS_IN in
  neighbor 169.254.1.2 route-map RM_AWS_OUT out
 exit-address-family

 address-family ipv4 vrf AZURE
  neighbor 172.16.0.2 activate
  neighbor 172.16.0.2 prefix-list PL_AZURE_INTERNAL in
  neighbor 172.16.0.2 route-map RM_AZURE_IN in
  neighbor 172.16.0.2 route-map RM_AZURE_OUT out
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
