# Routing Design Standards

Checkout's routing architecture standards and design patterns.

---

## BGP Autonomous System (AS) Numbers

| ASN Range | Purpose | Network |
| --- | --- | --- |
| `65000` | Checkout core network | Internal |
| `65100–65199` | Data Center | On-premises datacenters |
| `65200–65299` | AWS CNE (Customer Network Edge) | AWS customer-managed routers |
| `65300–65399` | AWS TGW (Transit Gateway) | AWS TGW BGP adjacency |

---

## VRF Strategy: Cloud Provider Separation

**Standard:** Use VRF-Lite with one VRF per cloud provider and management.

| VRF | Purpose | RT (Export/Import) | RD |
| --- | --- | --- | --- |
| Mgmt-vrf | Management plane isolation | `1` | `65000:1` |
| AWS | Amazon Web Services | `100` | `65000:100` |
| Azure | Microsoft Azure | `110` | `65000:110` |
| GCP | Google Cloud Platform | `120` | `65000:120` |

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

| Setting | Value | Notes |
| --- | --- | --- |
| Keepalive | 10 seconds | Fast failure detection |
| Hold time | 30 seconds | 3x keepalive |
| BFD interval | 300ms tx/rx, multiplier 3 | Sub-second failover |

### Route Filtering

**Standard:** Use BGP Prefix-Lists for route filtering.

Prefix-Lists provide efficient, object-based route filtering with sequence numbers for easy
editing. Apply to BGP neighbors or within route-maps for granular control.

**Example:**

```ios
ip prefix-list PL_AWS_INTERNAL seq 10 permit 10.0.0.0/8 ge 16 le 24
ip prefix-list PL_AWS_INTERNAL seq 20 permit 172.16.0.0/12 ge 20 le 24
!
router bgp 65000
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

```ios
route-map RM_AWS_IN permit 10
 match ip address prefix-list PL_AWS_INTERNAL
 set local-preference 300
!
router bgp 65000
 address-family ipv4
  neighbor 169.254.1.2 route-map RM_AWS_IN in
 exit-address-family
!
```

**AS Path Prepending** — steer inbound traffic from preferred ISP:

```ios
route-map RM_AZURE_OUT permit 10
 set as-path prepend 65000 65000 65000
!
router bgp 65000
 address-family ipv4
  neighbor 172.16.0.2 route-map RM_AZURE_OUT out
 exit-address-family
!
```

See [Naming Standards](naming-conventions.md) for route-map naming conventions.

---

## MPLS and Label Distribution

TODO: Add MPLS standards if applicable (LDP, segment routing)

---

## Multi-Cloud Failover Design

TODO: Add active-active vs active-passive patterns

---

## Security Standards

See [Security Hardening](security-hardening.md) for CIS/STIG/PCI-DSS requirements.
