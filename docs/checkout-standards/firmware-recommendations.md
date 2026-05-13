# Firmware Version Recommendations

Recommended firmware versions for network equipment based on [Software Standards](software-standards.md)
criteria: vendor-recommended, LTS, free of critical CVEs, and supported for the planned deployment period.

**Last Reviewed:** 2026-05-13
**Next Review:** 2026-06-12 (monthly, second Tuesday of each month at 14:00 UTC)

---

## Current Recommendations (May 2026)

### Cisco Catalyst Switches — IOS-XE

| Model | Series | OS | Current Recommended | LTS Train | Notes |
| --- | --- | --- | --- | --- | --- |
| C9200CX-12T-2X2G | 9200 | IOS-XE | 17.15.5 | 17.15 | Active; modern hardware |
| C9200L-48P-4G | 9200 | IOS-XE | 17.15.5 | 17.15 | Active; 48-port; PoE capable |
| C9300-24T | 9300 | IOS-XE | 17.15.5 | 17.15 | Active; datacenter; highest MTBF |
| C9300-24UX | 9300 | IOS-XE | 17.15.5 | 17.15 | Active; UPoE capable |
| C9300-48T | 9300 | IOS-XE | 17.15.5 | 17.15 | Active; 48-port option |
| C9300-48P | 9300 | IOS-XE | 17.15.5 | 17.15 | Active; PoE capable |
| C9500-24Y4C | 9500 | IOS-XE | 17.15.5 | 17.15 | Active; highest throughput |

**Notes:**

- **Current Recommended:** 17.15.5 (security advisories in 17.12.x range)
- **9200/9300/9500 Series:** Current maintenance; no announced EOL; 5+ year deployment
- **Deprecated:** 17.12.x and earlier have known security vulnerabilities
- **Non-LTS versions (17.13, 17.14, 17.16+):** Should NOT be deployed in production

**Upgrade Path:** All devices should upgrade to 17.15.5 immediately due to security
advisories. Devices on 17.3.x–17.12.x should prioritize this upgrade.

---

### Cisco Catalyst Switches — IOS (Legacy)

| Model | Series | OS | Current Recommended | Support Expires | Notes |
| --- | --- | --- | --- | --- | --- |
| C1000-8T-2G-L | 1000 | IOS | 12.2(7)E14 | 2030-04-30 | Maintained; legacy platform |
| C1000-24T-4X-L | 1000 | IOS | 12.2(7)E14 | 2030-04-30 | Maintained; legacy platform |

**Notes:**

- **1000 Series (C1000):** Runs traditional IOS (not IOS-XE); EOL 2030-04-30
- **Current Recommended:** 12.2(7)E14 (security advisories in earlier 12.2.x versions)
- **Support Timeline:** End of Vulnerability Support 2028-04-30; plan upgrade/replacement
  by mid-2028
- **Upgrade Path:** Consider replacement with 9200 series; 1000 series near EOL

---

### FortiGate Firewalls

| Model | Recommended | Previous | Status | Support Expires | Notes |
| --- | --- | --- | --- | --- | --- |
| FortiGate 70G | 7.6.6 | 7.4.x | Active | TBD | Mid-range; datacenter capable |
| FortiGate 101F | 7.6.6 | 7.4.x | Active | TBD | Entry-level; updated quarterly |
| FortiGate 201F | 7.6.6 | 7.4.x | Active | TBD | Branch firewall; stable release |
| FortiGate 601F | 7.6.6 | 7.4.x | Active | TBD | High throughput; HA capable |
| FortiGate 601E | 7.6.6 | 7.0.x | Maintained | 2027-09-27 | Legacy; no feature updates |

**Notes:**

- **Current Recommended:** 7.6.6 (Fortinet stable; 7.4.x has critical security advisories)
- **Avoid:** 7.4.x range (deprecated due to security vulnerabilities)
- **Security Response:** Multiple CVEs identified in 7.4.x; all deployments should upgrade
- **Security Patches:** Fortinet releases hotfixes weekly; apply within SLA timelines
- **601E Units:** EOL approaching; plan upgrade to 601F+ models by 2027-Q3

**Upgrade Path:** All devices should upgrade from 7.4.x to 7.6.6 immediately. 601E devices
should plan hardware replacement by Q3 2027.

---

### FortiManager (Cloud)

| Model | Recommended | Current | Status | Notes |
| --- | --- | --- | --- | --- |
| FortiManager Cloud | 7.6.6 | 7.6.6 | Active | Cloud-based management platform |

**Notes:**

- **Current Deployed:** 7.6.6 (up-to-date)
- **Target Version:** 7.6.6 (no upgrade required)
- **Status:** In sync with FortiGate firewall version
- **Upgrade Strategy:** Update FortiManager Cloud when FortiOS version advances

**Upgrade Path:** Monitor Fortinet cloud release notes; coordinate FortiManager and FortiGate
version upgrades together for consistency.

---

### Cisco Meraki

#### Wireless Access Points (MR Series)

| Model | Recommended | Previous | Status | Notes |
| --- | --- | --- | --- | --- |
| MR44 | Current/N-1| (auto-update) | Maintained | Cloud-managed; automatic updates |
| MR46 | Current/N-1| (auto-update) | Maintained | Cloud-managed; automatic updates |
| MR76 | Current| (auto-update) | Active | Latest model; no announced EOL |
| CW9164I | Current/N-1| (auto-update) | Active | Cisco Catalyst WiFi; cloud-native |

**Notes:**

- **Meraki Cloud Management:** Dashboard pushes firmware; device reboots during
  configured maintenance window
- **Current Release:** Meraki publishes updates monthly; set windows 22:00-04:00 UTC
  (low-traffic hours)
- **Beta Releases:** Disabled per standards; use stable releases only
- **MR44/MR46:** Plan upgrade to MR76/CW9164I by 2026-Q4 (hardware aging)

#### Switches (MS Series)

| Model | Recommended | Previous | Status | Support Expires | Notes |
| --- | --- | --- | --- | --- | --- |
| MS120-48LP | Current/N-1| (auto-update) | Maintained | 2030-03-28 | Cloud-managed; scheduled updates |
| MS250-48LP | Current/N-1| (auto-update) | Maintained | 2030-03-08 | Managed; 48-port option |
| MS250-24P | Current| (auto-update) | Maintained | 2030-03-08 | Managed; compact form factor |

**Notes:**

- **Cloud Managed:** All MS switches receive firmware updates via Meraki dashboard
- **Update Windows:** Staged rollout (canary → early access → gradual → complete)
  over 1 week
- **Staged Upgrade Schedule:** Tue 00:00 UTC (canary) → Wed 00:00 UTC → Thu 00:00 UTC
  → Fri 00:00 UTC (completion)

---

### Vertiv Console Servers

| Model | Recommended | Current | Status | Notes |
| --- | --- | --- | --- | --- |
| Avocent ACS 8016DAC | 2.32.3 | 2.32.3 | Active | Serial console server |

**Notes:**

- **Current Deployed:** 2.30.2
- **Target Version:** 2.32.3 (minor version update; recommended)
- **Upgrade Impact:** Low risk; minor version bump
- **Support Status:** TBD; check Vertiv support/EOL dates for current and target versions

**Upgrade Path:** Plan upgrade campaign from 2.30.2 to 2.32.3; schedule during maintenance
window with rollback plan documented.

---

## Review Process & Change History

### Monthly Review Checklist

Every second Tuesday of the month (14:00 UTC):

1. **Check Vendor Security Advisories:**
   - Cisco Security Advisories (cisecurity.org)
   - Fortinet Security Advisories (fortinet.com/support)
   - Meraki Security Notifications (dashboard)

2. **Check Vendor Release Notes:**
   - Cisco IOS-XE release calendar
   - Fortinet release schedule (weekly hotfixes)
   - Meraki release notes (monthly updates)

3. **Assess Existing Deployments:**
   - Flag devices approaching EOL/EOSWM/EOVS
   - Identify devices on non-recommended trains
   - Document any critical bugs reported via support cases

4. **Update This Document:**
   - Revise firmware versions if LTS train changes
   - Add new critical CVEs to Notes column
   - Update next-review date
   - Add entry to Change History below

5. **Notify Teams:**
   - Email network-ops@ if upgrades needed
   - Update change calendar if campaign requires scheduling

---

## Change History

### 2026-05-13 (Version Update)

| Category | Change | Reason |
| --- | --- | --- |
| **Vertiv Avocent ACS 8016DAC** | Updated to 2.32.3 (from 2.30.2) | Firmware update |

### 2026-05-13 (Version Update)

| Category | Change | Reason |
| --- | --- | --- |
| **Meraki MR44** | Updated to Current/N-1 (from Current/N-1 ) | Cloud firmware status |
| **Meraki MR46** | Updated to Current/N-1 (from Current/N-1 ) | Cloud firmware status |
| **Meraki MR76** | Updated to Current (from Current ) | Cloud firmware status |
| **Meraki CW9164I** | Updated to Current/N-1 (from Current ) | Cloud firmware status |
| **Meraki MS120-48LP** | Updated to Current/N-1 (from Current/N-1 ) | Cloud firmware status |
| **Meraki MS250-48LP** | Updated to Current/N-1 (from Current/N-1 ) | Cloud firmware status |
| **Meraki MS250-24P** | Updated to Current (from Current/N-1 ) | Cloud firmware status |

### 2026-05-13 (Version Update)

| Category | Change | Reason |
| --- | --- | --- |
| **Cisco IOS-XE** | Updated to 17.15.5 (from 17.12.x) | Security advisories in 17.12.x range |
| **Cisco IOS** | Updated C1000 to 12.2(7)E14 | Security advisories in earlier 12.2.x versions |
| **FortiOS** | Updated to 7.6.6 (from 7.4.2) | Multiple critical CVEs in 7.4.x range |
| **Meraki** | Documented cloud-managed update strategy | No specific versions; rely on dashboard |
| **Vertiv** | Noted research required | No console servers in current inventory |

---

## Related Standards

- [Software Standards](software-standards.md) — Selection principles & security SLAs
- [Equipment Standards](equipment-standards.md) — Device lifecycle and EOL dates
- [Equipment Configuration](equipment-config.md) — Baseline configs for recommended versions
- [Security Hardening](security-hardening.md) — Minimum security requirements
