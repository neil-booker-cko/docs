# Checkout Network Engineering Standards

Standards and design decisions for network infrastructure at Checkout. Based on industry
frameworks (CIS, STIG, PCI-DSS) and operational best practices.

---

## Core Configuration Standards

Standard baseline configurations for Cisco IOS-XE, FortiOS, and Meraki cloud-managed devices.

- **[Equipment Configuration](equipment-config.md)** — SSH, AAA, logging, NTP, SNMP baseline
  templates
- **[Security Hardening](security-hardening.md)** — CIS/STIG/PCI-DSS hardening (management,
  control, data planes)
- **[Meraki Cloud Networking](meraki-standards.md)** — Wireless (SSID, RF, security), switches
  (VLAN, ports, OSPF), site-wide settings (admin, alerts, group policies)
- **[Naming Standards](naming-conventions.md)** — Physical devices, interfaces, VRFs, route
  maps, BGP neighbors, ACLs

---

## Routing and Connectivity Standards

BGP, VPN, and datacenter/cloud interconnection design patterns.

- **[Routing Design](routing-design.md)** — BGP AS allocation, VRF cloud separation, RD/RT
  numbering tied to routing processes
- **[BGP Configuration](bgp-standards.md)** — BGP neighbor templates, process configuration,
  timers, authentication, policies
- **[Connectivity Standards](connectivity-standards.md)** — ISP connectivity, AWS DX, VPN
  failover patterns, hub-and-spoke design
- **[VPN Standards](vpn-standards.md)** — Site-to-Site IPsec (IKEv2, AES-256-GCM, PFS, key
  rotation)

---

## Switching and Interface Standards

VLAN configuration, interface management, and physical connectivity.

- **[VLAN Standards](vlan-standards.md)** — VLAN allocation (data/voice/IoT/guest), tagging,
  trunking, spanning tree, access control
- **[Interface Configuration Standards](interface-standards.md)** — Speed/duplex, MTU, flow
  control, spanning tree, LAG, link aggregation
- **[High Availability (HA) Standards](ha-standards.md)** — HSRP/VRRP, FortiGate HA cluster,
  failover timers, BFD, split-brain prevention

---

## Infrastructure and Operations Standards

Equipment selection, software management, addressing, and operational practices.

- **[IP Addressing](ip-addressing.md)** — Cloud provider links (AWS DX, Azure ER, GCP IC),
  datacenter ranges, reserved blocks
- **[Equipment Standards](equipment-standards.md)** — Approved devices (Cisco, Fortinet,
  Meraki) with EOS/EOSWM/EOVS dates, 5-year refresh policy
- **[Software Standards](software-standards.md)** — Firmware selection principles, security
  advisory SLAs (critical 1wk, high 1mo, medium 2mo), upgrade schedule

---

## Operations & Resilience Standards

Monitoring, logging, change management, and disaster recovery procedures.

- **[Firewall Policy Standards](firewall-standards.md)** — FortiGate policy structure, rule
  ordering, naming conventions, logging, DPI, traffic shaping, NAT
- **[Syslog & Monitoring Standards](syslog-monitoring-standards.md)** — Centralized logging,
  SNMP v3, syslog facilities, alert thresholds, integration with PagerDuty
- **[Change Management Standards](change-management-standards.md)** — Pre-change checklists,
  implementation procedures, validation commands, rollback processes, approvals
- **[Disaster Recovery Standards](disaster-recovery-standards.md)** — Backup procedures,
  retention schedules, RTO/RPO targets, recovery procedures, DR testing

---

## Standards by Plane

Use these cross-references to find related controls across management, control, and data planes.

| Plane | Standards |
| --- | --- |
| **Management** | Equipment Configuration, Security Hardening (AAA, SSH, SNMP), Meraki Cloud Networking (site-wide, admin), Naming Standards, Software Standards, Syslog & Monitoring (SNMP v3), Interface Configuration (mgmt interface), HA Standards (monitoring), Disaster Recovery (backup retention) |
| **Control** | BGP Configuration, Routing Design, Connectivity Standards, Meraki Cloud Networking (OSPF, DHCP), Security Hardening (BGP auth, logging), VLAN Standards (inter-VLAN routing), HA Standards (failover), Firewall Policy Standards (rule structure), Interface Configuration (interface features), Syslog & Monitoring (alerts/thresholds) |
| **Data** | Connectivity Standards (forwarding), VPN Standards (IPsec), Meraki Cloud Networking (switch forwarding, traffic shaping), Security Hardening (data plane ACLs), VLAN Standards (VLAN forwarding), Firewall Policy Standards (traffic filtering, NAT), Interface Configuration (physical path), HA Standards (session sync) |
| **Infrastructure** | Equipment Standards, Meraki Cloud Networking (cloud management), IP Addressing, Software Standards, Equipment Configuration, Syslog & Monitoring (infrastructure), Interface Configuration (physical interfaces), Change Management (all changes), Disaster Recovery (RTO/RPO) |

---

## Adding Standards

When making a design decision that affects multiple engineers or becomes a pattern:

1. Document in the appropriate standards file (or create a new one if it doesn't fit existing
   categories)
2. Link to related theory docs for foundational concepts
3. Include configuration examples and exceptions
4. Update `mkdocs.yml` navigation if adding a new file
5. Update this README to reference the new standard in the appropriate category and
   cross-reference table

---

## Related Documentation

**Theory** — Foundational concepts (VRF, BGP, IPsec, etc.):

- [VRF Theory](../theory/vrf.md) — VRF-Lite vs MPLS, RD/RT design patterns
- [BGP Theory](../theory/bgp.md), [IPsec Theory](../theory/ipsec.md) — Protocol deep dives

**Configuration Guides** — Detailed, step-by-step setup for specific scenarios

**Reference** — Quick lookup tables (IP ranges, ports, ICSS, MTU, etc.)
