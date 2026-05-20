# Equinix Fabric Port Standards

Checkout's standard configuration for Equinix Fabric ports used for datacenter
interconnection and cloud provider connectivity.

---

## Standard Configuration Summary

| Setting | Standard |
| --- | --- |
| Port Type | Standard |
| Port Speed | 1 Gbps |
| Port Redundancy | Redundant pair across two metro locations |
| VLAN Tagging | 802.1Q (0x8100) |
| Encapsulation | Dot1Q |
| LAG | Not used |
| MTU | Standard (1500 bytes) |
| Connection Type | Cross-Connect |
| Monitoring SLA | Standard SLA |

---

## Port Settings

### Port Type and Speed

| Setting | Options | Standard |
| --- | --- | --- |
| Port Type | Standard, Private | Standard |
| Port Speed | 1G, 10G, 25G, 100G | 1 Gbps |
| MTU | Standard (1500), Jumbo (9000) | Standard (1500 bytes) |
| Port Billing Model | Flat rate, Pay-as-you-go | Flat rate |

**Standard** port type allows multiple virtual connections from a single physical port
(shared capacity). **Private** is for dedicated single-service links. Standard is used at
1G; note that unlimited bandwidth is capped at 10G on Standard ports.

### Port Redundancy

| Setting | Options | Standard |
| --- | --- | --- |
| Port Redundancy | Single, Redundant Pair | Redundant pair across two metro locations |
| Active-Active | Yes, No | Yes |

Redundancy is achieved using **two physical ports in different Equinix Fabric metro
locations**. Both ports are active simultaneously. If one metro location experiences a
failure, the other continues to carry traffic. This is preferred over LAG (which provides
redundancy within a single location only).

### Connection Type

| Setting | Options | Standard |
| --- | --- | --- |
| Connection Type | Cross-Connect, Remote Port, Virtual Port | Cross-Connect |

**Cross-Connect** provides a direct physical connection from the Checkout cage to the
Equinix Fabric port within the same datacenter. Remote Port and Virtual Port are not
used.

---

## VLAN Tagging and Encapsulation

| Setting | Options | Standard |
| --- | --- | --- |
| VLAN Standard | 802.1Q (0x8100), 802.1ad Q-in-Q (0x88A8) | 802.1Q (0x8100) |
| Encapsulation | Dot1Q, VXLAN, MPLS | Dot1Q |
| TPID | 802.1Q, Q-in-Q | 802.1Q (0x8100) |

Single-tag 802.1Q (Dot1Q) encapsulation is used throughout. Q-in-Q double-tagging is not
required. VXLAN and MPLS encapsulations are not used.

---

## Link Aggregation (LAG)

LAG is **not used** on Equinix Fabric ports. Redundancy is provided by the dual-port,
dual-metro design rather than link aggregation within a single location.

| LAG Setting | Standard |
| --- | --- |
| LAG Support | No |
| Protocol | Not applicable |
| Number of Links | Not applicable |

---

## Port Security and Monitoring

| Feature | Standard |
| --- | --- |
| Port Security (MAC Limiting, BPDU Guard, Storm Control) | Optional — evaluate per site |
| Utilisation Reporting | Optional |
| Service Level Agreement | Standard SLA |

The Standard SLA covers guaranteed uptime and performance across both metro locations.

---

## Related Standards

- [Connectivity Standards](connectivity-standards.md) — ISP and cloud connectivity design principles
- [Equinix FCR Architecture](../equinix/equinix_fcr_architecture.md) — Fabric Cloud Router design
- [Equinix FCR Setup](../equinix/equinix_fcr_setup.md) — FCR provisioning and BGP configuration
- [Equinix Fabric Concepts](../equinix/equinix_fabric_concepts.md) — Fabric port and connection concepts

## Equinix Documentation

- [Equinix Fabric Port Architectures](https://docs.equinix.com/en-us/Content/Interconnection/Fabric/ports/Fabric-Port-Architectures.htm)
  — Equinix reference for port types, redundancy models, and connection options
