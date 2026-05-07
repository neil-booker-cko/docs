# Routing Design Standards

Checkout's routing architecture standards and design patterns.

---

## BGP Autonomous System (AS) Numbers

| ASN | Purpose | Network |
| --- | --- | --- |
| `65000` | Checkout core network | Internal |
| (Reserved) | Cloud provider BGP | AWS TGW, Azure MSEE, GCP Cloud Router |

---

## VRF Strategy: Cloud Provider Separation

**Standard:** Use VRF-Lite with one VRF per cloud provider and management.

| VRF | Purpose | RT (Export/Import) | RD |
| --- | --- | --- | --- |
| Mgmt | Management plane isolation | `1` | `65000:1` |
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

TODO: Add route filtering standards (prefix lists, route maps)

---

## MPLS and Label Distribution

TODO: Add MPLS standards if applicable (LDP, segment routing)

---

## Multi-Cloud Failover Design

TODO: Add active-active vs active-passive patterns

---

## Security Standards

See [Security Hardening](security-hardening.md) for CIS/STIG/PCI-DSS requirements.
