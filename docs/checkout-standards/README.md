# Checkout Network Engineering Standards

Standards and design decisions for network infrastructure at Checkout. Based on industry
frameworks (CIS, STIG, PCI-DSS) and operational best practices.

---

## Standards by Category

- **[Routing Design](routing-design.md)** — BGP, VRF, ASN allocation, RD/RT numbering
- **[IP Addressing](ip-addressing.md)** — Address allocation, cloud links, internal links
- **[Security Hardening](security-hardening.md)** — CIS/STIG/PCI-DSS configuration baselines
- **[Naming Conventions](naming-conventions.md)** — Devices, interfaces, VRFs, routes
- **[BGP Configuration](bgp-standards.md)** — Neighbor templates, policies, timers
- **[Equipment Configuration](equipment-config.md)** — Cisco IOS-XE, FortiOS standard configs

---

## Adding Standards

When making a design decision that affects multiple engineers or becomes a pattern:

1. Document it in the appropriate standards file
2. Link to relevant theory docs for background
3. Include examples and exceptions
4. Update mkdocs.yml navigation if adding a new file

---

## Related Documents

- **Theory** — Foundational concepts (why things work)
- **Configuration Guides** — Step-by-step setup for specific platforms
- **Reference** — Quick lookup tables and checklists
