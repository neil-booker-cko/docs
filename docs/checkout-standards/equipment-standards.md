# Network Equipment Standards

Approved network devices with lifecycle status and end-of-life dates for capacity planning and
procurement.

**Data Verification:** May 2026. Cisco and Meraki lifecycle dates verified against official vendor
documentation. Fortinet dates require verification (see notes below). MTBF values sourced from
official datasheets.

---

## Status Definitions

### Checkout Status

| Status | Meaning |
| --- | --- |
| Active | Current model approved for new deployments |
| Maintained | Still in service but no new purchases |
| Retired | No longer supported or in use |

### Vendor Lifecycle Dates

| Term | Meaning |
| --- | --- |
| EOS | End of Sale — last date to order |
| EOSWM | End of Software Maintenance — last firmware patches |
| EOVS | End of Vulnerability Support — last security patches |
| LDOS | Last Date of Support — end of all support |

---

## Cisco Systems Switches

**[Cisco End-of-Life Policy](https://www.cisco.com/c/en/us/products/eos-eol-policy.html)**

**MTBF Source:** [Catalyst 9300 Series Datasheet](https://www.cisco.com/c/en/us/products/collateral/switches/catalyst-9300-series-switches/nb-06-cat9300-ser-data-sheet-cte-en.html)

| Model | Status | MTBF | EOS | EOSWM | EOVS | LDOS |
| --- | --- | --- | --- | --- | --- | --- |
| Catalyst C9300-48T | Active | 305,870 hrs | — | — | — | — |
| Catalyst C9300-24T | Active | 314,790 hrs | — | — | — | — |
| Catalyst C9300-24UX | Active | 214,760 hrs | — | — | — | — |
| Catalyst C9300-48P | Active | 277,770 hrs | — | — | — | — |
| Catalyst C9500-24Y4C | Active | 336,780 hrs | — | — | — | — |
| Catalyst C9200CX-12T-2X2G | Active | 569,530 hrs | — | — | — | — |
| Catalyst C1000-8T-2G-L | Maintained | 2,171,669 hrs | 2025-04-30 | 2026-04-30 | 2028-04-30 | 2030-04-30 |
| Catalyst C1000-24T-4X-L | Maintained | 2,026,793 hrs | 2025-04-30 | 2026-04-30 | 2028-04-30 | 2030-04-30 |

---

## Fortinet FortiGate Firewalls

**[Fortinet Product Life Cycle](https://community.fortinet.com/t5/Customer-Service/Technical-Tip-Product-Life-Cycle-Information-on-Fortinet/ta-p/194438)**

**Note:** Fortinet does not publish specific EOL dates for individual hardware models. Contact Fortinet
support for exact End of Order (EOO), Last Service Extension Date (LSED), and End of Engineering
Support dates. Standard FortiGate support lifecycle is typically 7-10 years from release.

| Model | Status | EOO | LSED | EOS |
| --- | --- | --- | --- | --- |
| FortiGate 101F | Active | — | — | — |
| FortiGate 201F | Active | — | — | — |
| FortiGate 601F | Active | — | — | — |
| FortiGate 601E | Maintained | — | — | — |

### Checkout Firewall Deployment

**⚠️ ACTION REQUIRED:** Support expiration dates for FortiGate 601F units (LD8, SG3, DB3) are TBD.
Contact Fortinet support to verify exact End of Support dates for capacity planning.

| Site | Model | Purchase | Support Expires |
| --- | --- | --- | --- |
| LD7 | 2× FortiGate 601E | 2020 | 2027-09-27 |
| LD7 Test Kit | 2× FortiGate 601E | 2021 | 2027-09-27 |
| DC4 | 2× FortiGate 601E | 2021 | 2027-09-27 |
| LD8 | 2× FortiGate 601F | 2023 | **VERIFY** |
| SG3 | 2× FortiGate 601F | 2022 | **VERIFY** |
| DB3 | 2× FortiGate 601F | 2025 | **VERIFY** |

---

## Cisco Meraki

**[Meraki EOL Policy](https://documentation.meraki.com/General_Administration/Other_Topics/Meraki_End-of-Life_(EOL)_Products_and_Dates)**

**Data Last Updated:** May 2026. Dates for MS120-48LP and MS250 series verified against official
Meraki EOL documentation. Wireless APs (MR series) currently have no announced EOL dates.

| Model | Status | End of Sale | End of Support | Replacement |
| --- | --- | --- | --- | --- |
| MS120-48LP | Maintained | 2025-03-28 | 2030-03-28 | C9300-48P, C9300-24UX |
| MS250-48LP | Maintained | 2025-08-08 | 2030-03-08 | — |
| MS250-24P | Maintained | 2025-08-08 | 2030-03-08 | — |
| MR44 | Maintained | — | — | CW9164I |
| MR46 | Maintained | — | — | — |
| MR76 | Active | — | — | — |
| CW9164I | Active | — | — | — |

### Checkout Meraki Deployment

| Site | Model | Purchase | Status |
| --- | --- | --- | --- |
| Multiple | Various MS120/MS250 | 2019-2022 | Planned replacement 2024-2025 |
| Multiple | MR44/MR46 | 2019-2022 | Maintained; upgrade to MR76/CW9164I as needed |

---

## Hardware Refresh Policy

**Standard Refresh Cycle:** 5 years from purchase

Devices reaching 5-year age should be evaluated for:

1. **Active Support Status** — Is vendor still providing patches?
2. **Performance Adequacy** — Does device meet current throughput/feature needs?
3. **Cost of Ownership** — Is ongoing maintenance cost-effective?
4. **Replacement Availability** — Can equivalent/superior models be procured?

**Action Triggers:**

- Devices approaching end-of-support should be replaced within 12 months before LDOS
- Performance bottlenecks should trigger replacement regardless of age
- Security advisory saturation (frequent critical patches) indicates end-of-life

---

## Procurement Guidelines

When procuring new network equipment:

1. **Verify Active Status** — Only procure models marked "Active" in this document
2. **Plan for Support** — Ensure vendor support covers your planned deployment period
3. **Capacity Planning** — Account for growth; avoid purchasing minimum capacity
4. **Software Support** — Confirm firmware/software versions are recommended or LTS
5. **Warranty Terms** — Standard: 3-year hardware, 5-year support recommended

---

## Related Standards

- [Software Standards](software-standards.md)
- [Device Naming Standards](device-naming.md)
- [Equipment Configuration](equipment-config.md)
