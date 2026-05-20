# Routing Design Standards

Checkout's routing architecture standards and design patterns.

---

## BGP Autonomous System (AS) Numbers

| ASN Range | Purpose | Notes |
| --- | --- | --- |
| `65100–65199` | Data Center | On-premises datacenters; one AS per site |
| `65200–65299` | AWS CNE (Customer Network Edge) | AWS customer-managed routers |
| `65300–65399` | AWS TGW (Transit Gateway) | AWS TGW BGP adjacency |

---

## VRF Strategy: Cloud Provider Separation

**Standard:** Use VRF-Lite with one VRF per cloud provider and management.

| VRF | Purpose | RT (Export/Import) | RD |
| --- | --- | --- | --- |
| Mgmt-vrf | Management plane isolation | `1` | `<DC_ASN>:1` |
| AWS | Amazon Web Services | `100` | `<DC_ASN>:100` |
| Azure | Microsoft Azure | `110` | `<DC_ASN>:110` |
| GCP | Google Cloud Platform | `120` | `<DC_ASN>:120` |

**Rationale:**

- Each cloud provider connects via distinct WAN paths (Direct Connect, ExpressRoute, Cloud
  Interconnect). VRF isolation prevents accidental route leaking between clouds.
- RT values (1, 100, 110, 120) are simple and human-readable; RD prepends ASN for BGP
  uniqueness.
- Mgmt VRF isolates management traffic from data plane; uses built-in VRF in IOS-XE.

**Reference:** [VRF Theory](../theory/vrf.md) | [Cloud Separation Config](../cisco/cisco_vrf_config.md)

---

## BGP Design Patterns

### Peer Timers

BFD is the recommended approach for all BGP neighbors — it provides sub-second failure detection
and allows longer BGP timers that reduce unnecessary session resets.

| Setting | With BFD (recommended) | Without BFD (fallback) |
| --- | --- | --- |
| Keepalive | 60 seconds | 10 seconds |
| Hold time | 180 seconds | 30 seconds |
| BFD interval | 300ms tx/rx, multiplier 3 | — |

See [BGP Standards](bgp-standards.md) and [BFD Standards](bfd-standards.md) for full configuration.

### Route Filtering

**Standard:** Use BGP Prefix-Lists for route filtering.

Prefix-Lists provide efficient, object-based route filtering with sequence numbers for easy
editing. Apply to BGP neighbors or within route-maps for granular control.

**Example:**

```ios
ip prefix-list PL_AWS_INTERNAL seq 10 permit 10.0.0.0/8 ge 16 le 24
ip prefix-list PL_AWS_INTERNAL seq 20 permit 172.16.0.0/12 ge 20 le 24
!
router bgp <DC_ASN>
 address-family ipv4
  neighbor 169.254.1.2 prefix-list PL_AWS_INTERNAL in
 exit-address-family
!
```

See [Naming Standards](naming-conventions.md) for prefix-list naming conventions.

### Route Manipulation

**Standard:** Use BGP Route-Maps for route manipulation (Local Preference and AS Path Prepending).

Route-Maps allow conditional modification of BGP attributes to influence path selection and
traffic flow across multiple cloud providers and datacenters.

**Local Preference** — steer outbound traffic via preferred ISP:

Use Local Preference values of **200 for primary links** and **150 for secondary links** to prefer
primary paths while maintaining standby capability.

```ios
route-map RM_AWS_IN permit 10
 match ip address prefix-list PL_AWS_INTERNAL
 set local-preference 200
!
router bgp <DC_ASN>
 address-family ipv4
  neighbor 169.254.1.2 route-map RM_AWS_IN in
 exit-address-family
!
```

**AS Path Prepending** — steer inbound traffic from preferred ISP:

Prepend your own AS number an additional **2 times** on secondary paths to make them appear
less desirable (longer AS Path) to external peers, influencing inbound traffic selection.

```ios
route-map RM_AZURE_OUT permit 10
 set as-path prepend 65100 65100
!
router bgp 65100
 address-family ipv4
  neighbor 172.16.0.2 route-map RM_AZURE_OUT out
 exit-address-family
!
```

See [Naming Standards](naming-conventions.md) for route-map naming conventions.

---

## OSPF

OSPF is used for internal routing within datacenters and offices. BGP handles all cloud
provider and inter-site connectivity.

See [OSPF Standards](ospf-standards.md) for configuration and area design.

---

## Multi-Cloud Failover Design

Active-passive failover using Local Preference (inbound) and AS Path Prepending (outbound).
BFD provides sub-second detection on all cloud provider links.

| Cloud | Primary Path | Secondary Path | Failover Mechanism |
| --- | --- | --- | --- |
| AWS Direct Connect | Local Pref 200 | Local Pref 150 | BFD + BGP fall-over |
| Azure ExpressRoute | Local Pref 200 | Local Pref 150 | BFD + BGP fall-over |
| GCP Interconnect | Local Pref 200 | Local Pref 150 | BFD + BGP fall-over |

Detailed design per provider:

- [AWS BGP Stack](../aws/bgp_stack_vpn_over_dx.md)
- [Azure BGP Stack](../azure/bgp_stack_vpn_over_expressroute.md)
- [GCP BGP Stack](../gcp/bgp_stack_vpn_over_interconnect.md)

---

## Related Standards

- [BGP Standards](bgp-standards.md) — BGP process, timers, communities, address families
- [OSPF Standards](ospf-standards.md) — Internal routing
- [BFD Standards](bfd-standards.md) — Failure detection
- [VPN Standards](vpn-standards.md) — IPsec overlay design
- [Security Hardening](security-hardening.md) — Routing security (BGP auth, prefix limits)
