# Network Software Standards

Guidelines for firmware and software selection, upgrade schedules, and security advisory response
for network devices.

---

## Software Selection Principles

### Initial Build Requirements

When deploying a new device, the selected firmware should meet ALL of:

1. Recommended by the vendor
2. Contains all required features
3. Supports all underlying hardware
4. Long-term supported (LTS) version
5. Free of known security advisories
6. Free of major known bugs

If all criteria cannot be met, prioritize security and support over features.

### Upgrade Drivers

Firmware upgrades should be driven by compelling business reasons, NOT by artificial N-1
policies. Valid upgrade drivers include:

- **Security Advisories** — Critical motivation for upgrade
- **Bug Fixes** — Address issues affecting operations
- **Support Maintenance** — Approaching end-of-life dates
- **Vendor Recommendations** — Stability/maturity indicators
- **Software Age** — Avoid overly outdated releases

**Avoid upgrading for:** feature parity with latest version, arbitrary N-1 compliance, or vendor
release schedules unrelated to your environment.

---

## Security Advisory Response SLAs

Firmware patches for security vulnerabilities must be applied within these timelines:

| Severity | CVSS Score | SLA | Source |
| --- | --- | --- | --- |
| Critical | 9.0-10.0 | 1 week | EBA/internal policy |
| High | 7.0-8.9 | 1 month | PCI DSS |
| Medium | 4.0-6.9 | 2 months | PCI DSS |
| Low | 0-3.9 | No timeline | Internal discretion |

**Notes:**

- SLA begins at public advisory announcement (not discovery)
- Only apply if the vulnerability affects enabled/active services on your equipment
- Mitigated or disabled features may not require immediate patching

---

## Software Review Schedule

Review firmware status on this schedule:

- **Immediately:** Discovery of security advisory affecting deployed devices
- **Immediately:** Bug identified via vendor support case
- **Monthly:** Check vendor security bulletins and release notes
- **Quarterly:** Audit firmware versions across all devices

---

## Software Upgrade Schedule

Execute firmware upgrades on this schedule:

- **Per SLA:** All security advisories per severity timelines (above)
- **Per Impact:** Bug fixes based on issue severity
- **Annually:** Minimum one upgrade per device to avoid stale releases
- **Before EOL:** Plan upgrade before vendor end-of-support dates

---

## Vendor-Specific Guidelines

### Cisco IOS-XE

**Recommended Train Approach:**

- Avoid following every minor release
- Align with Cisco's designated LTS trains (typically every 3rd minor version)
- Monitor release schedules; Cisco publishes expected cadence

**Example:** If Cisco releases 17.6 LTS, 17.7, 17.8, then 17.9 LTS:

- Adopt: 17.6 LTS (stable, recommended)
- Track: 17.9 LTS (next stable candidate)
- Avoid: 17.7, 17.8 (intermediate, not recommended)

**Security Bulletins:**

- Monitor Cisco Security Advisories
- Check CVRF feeds for CVSS scores
- Validate that your device runs the affected service

### Fortinet FortiOS

**Recommended Approach:**

- Fortinet publishes recommended firmware per model
- Follow current recommended; consider N-1 for stability if needed
- Monitor Fortinet Security Advisories for firmware updates

**Security Response:**

- Fortinet releases hotfixes for critical vulnerabilities
- Check release notes for vulnerability fixes
- Apply hotfixes within SLA timelines

### Cisco Meraki

**Recommended Approach:**

- Meraki cloud-manages firmware; automatic updates possible
- Set update windows during maintenance windows
- Monitor Meraki Security Advisories
- Review EOL dates for managed devices

---

## Pre-Upgrade Validation

Before upgrading firmware in production:

1. **Review Release Notes:** Identify breaking changes, known issues
2. **Test in Lab:** Deploy firmware to test device first (if available)
3. **Backup Configuration:** Create backup before upgrade
4. **Plan Maintenance Window:** Schedule during approved change window
5. **Document Rollback:** Know how to revert if upgrade fails
6. **Monitor Post-Upgrade:** Watch device health for 24-48 hours after upgrade

---

## Firmware Inventory

Track firmware versions across all devices:

- Maintain a current device inventory with firmware versions
- Flag devices approaching EOL or on unsupported firmware
- Plan upgrade campaigns for groups approaching EOL dates
- Document firmware releases applied and dates

---

## Deprecation and EOL Management

### End-of-Sale (EOS)

- Last date to order the product
- Plan replacement purchases before this date

### End of Software Maintenance (EOSWM)

- Last date vendor releases bug fixes or patches
- Plan upgrade to newer firmware branch before this date

### End of Vulnerability Support (EOVS)

- Last date vendor releases security patches
- All critical/high security advisories after this date will not be patched
- Plan retirement or upgrade before this date

### Last Date of Support (LDOS)

- Final day of vendor technical support
- Plan complete retirement/replacement after this date

---

## Related Standards

- [Security Hardening Standards](security-hardening.md)
- [Equipment Standards](equipment-standards.md)
- [Network Equipment Standards](equipment-standards.md)
