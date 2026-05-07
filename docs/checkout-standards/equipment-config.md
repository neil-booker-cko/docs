# Equipment Configuration Standards

Baseline and standard configurations for Cisco and FortiGate devices.

---

## Cisco IOS-XE

### Baseline Configuration Template

TODO: Add standard baseline config

**Topics:**

- System identification (hostname, domain)
- SSH/HTTPS management access
- Logging configuration
- NTP synchronization
- AAA (RADIUS/TACACS+)
- SNMP (if used)
- Banner and MOTD

### VRF-Lite Configuration

See [Cisco VRF-Lite for Cloud Provider Separation](../cisco/cisco_vrf_config.md)

### BGP Configuration

See [BGP Standards](bgp-standards.md)

### Security Hardening

See [Security Hardening Standards](security-hardening.md)

---

## FortiGate

### Baseline Configuration Template

TODO: Add standard baseline config

**Topics:**

- System identification (hostname, domain)
- Administrative access (SSH, HTTPS)
- Logging configuration (Syslog)
- NTP synchronization
- VDOM configuration (if multi-tenant)
- Firewall policy templates
- Intrusion prevention (IPS) settings

### Multi-VDOM Setup

TODO: Add VDOM configuration for cloud separation

### BGP Neighbor Configuration

TODO: Add FortiGate BGP neighbor templates

### Security Hardening

See [Security Hardening Standards](security-hardening.md)

---

## Network Management

### Out-of-Band Management (OOB)

**Standard:** Dedicated management VLAN with separate routing.

| Device Type | Management IP | VLAN | VRF |
| --- | --- | --- | --- |
| Core Router | `10.x.x.1` | 999 | Mgmt |
| Firewall | `10.x.x.2` | 999 | Mgmt |

### Backup and Recovery

TODO: Add backup standards (full backup interval, retention)

### Firmware Updates

TODO: Add firmware versioning and update procedures

---

## Maintenance Windows

TODO: Add change window guidelines and procedures
