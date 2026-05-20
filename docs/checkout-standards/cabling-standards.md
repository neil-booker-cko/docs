# Cabling & Rack Standards

Physical cabling and rack standards for Checkout datacenters. Consistent colour coding
and labelling allow cables to be identified by purpose without tracing them end-to-end,
reducing risk during maintenance and troubleshooting.

---

## Cable Colour Coding

All structured cabling installations must follow this colour scheme. Deviations require
approval and must be documented in the site's cabling records.

| Purpose | Colour |
| --- | --- |
| Internet / Network | Red |
| Management | Yellow |
| Storage | Blue |
| Server / HSM | Green |

**Internet / Network (Red):** All uplinks, cross-connects, and data-plane network cables.
This includes ISP handoffs, inter-switch links, and firewall data interfaces.

**Management (Yellow):** Out-of-band management connections — console servers, IPMI/iDRAC,
management switch ports, and any interface on the management VLAN (VLAN 701).

**Storage (Blue):** Storage area network (SAN) cabling — iSCSI, Fibre Channel, and NFS
paths between servers and storage arrays.

**Server / HSM (Green):** Server data connections and Hardware Security Module (HSM)
links.

---

## Related Standards

- [Equipment Standards](equipment-standards.md) — Device hardware selection and rack unit allocation
- [Naming Conventions](naming-conventions.md) — Device and port labelling conventions
- [Interface Configuration](interface-standards.md) — Interface naming and VLAN assignment
- [VLAN Configuration](vlan-standards.md) — Management VLAN (701) definition
