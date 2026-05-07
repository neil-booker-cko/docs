# IP Addressing Standards

Checkout's IP address allocation and design standards.

---

## Address Space Allocation

| Block | Purpose | CIDR | Notes |
| --- | --- | --- | --- |
| TODO | Corporate network | | |
| `10.254.0.0/16` | Cloud provider links | | AWS/Azure/GCP interconnects |
| `169.254.0.0/16` | Link-local (BGP) | | Dynamic routing adjacencies |

---

## AWS Direct Connect Links

**Standard:** Use `169.254.x.0/30` per DX virtual interface.

| VRF | Cisco IP | AWS TGW IP | CIDR |
| --- | --- | --- | --- |
| AWS | `169.254.1.1` | `169.254.1.2` | `169.254.1.0/30` |

---

## Azure ExpressRoute Links

**Standard:** Use `172.16.0.0/30` per ER private peering.

| VRF | Cisco IP | MSEE IP | CIDR |
| --- | --- | --- | --- |
| AZURE | `172.16.0.1` | `172.16.0.2` | `172.16.0.0/30` |

---

## GCP Cloud Interconnect Links

**Standard:** Use `169.254.0.0/29` per interconnect circuit.

| VRF | Cisco IP | Cloud Router IP | CIDR |
| --- | --- | --- | --- |
| GCP | `169.254.0.1` | `169.254.0.2` | `169.254.0.0/29` |

---

## Internal Inter-Router Links

TODO: Add internal link addressing scheme

---

## Management Network

TODO: Add management VLAN addressing

---

## Reserved Ranges

| Range | Purpose |
| --- | --- |
| `10.0.0.0/8` | RFC 1918 private (internal) |
| `172.16.0.0/12` | RFC 1918 private (cloud) |
| `169.254.0.0/16` | Link-local / BGP adjacencies |
