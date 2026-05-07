# Meraki Cloud Networking Standards

Cloud-based network configuration standards for Cisco Meraki managed devices (Wireless, Switches,
Security Appliances).

---

## Site-Wide Settings

### General Settings

| Setting | Standard | Notes |
| --- | --- | --- |
| Network Name | City name (e.g., LON, NYC, DXB) | Readable identifier for multi-site dashboards |
| Country/Region | Primary datacenter/office location | Determines regional compliance defaults |
| Traffic Analysis | Basic (enabled) | Enable for flow visibility without deep packet inspection |
| Client Privacy | Enabled | Mask MAC addresses in data exports (privacy compliance) |
| LED Lights | On | Physical indicator of device health |
| Local Device Status Pages | Enabled | Allow local management if dashboard unavailable |
| Firmware Upgrades - Try Beta | No | Stable releases only; no pre-release firmware |
| Firmware Upgrades - Strategy | Minimize Client Downtime | Use rolling/scheduled upgrades, not immediate |

### Administration

| Role | Standard | Purpose |
| --- | --- | --- |
| Organization Admin | `netadmin` | Network operations team full access |
| Network Admin | Role-based (See Access Policies) | Limit to specific team responsibilities |
| Guest SSID Password | Shared securely via credential manager | Not documented in source control |

### Alerts and Notifications

**Network-Wide Alerts:**

| Alert Type | Setting | Threshold |
| --- | --- | --- |
| Configuration Changes | Enable | All configuration changes logged |
| VPN Connection Status | Enable | Direct Connect / ExpressRoute failover |
| Rogue AP Detection | Disable | Requires RF site survey baseline (manual enablement) |

**Device-Specific Alerts:**

| Device Type | Alert | Threshold |
| --- | --- | --- |
| Wireless (MR) | Gateway offline | Enable with 5-minute threshold |
| Wireless (MR) | Client signal strength | Enable (default thresholds) |
| Switch (MS) | Device offline | Enable with 5-minute threshold |
| Switch (MS) | Power supply down | Enable immediately |
| Security Appliance (MX) | Offline | Enable with 5-minute threshold |
| Security Appliance (MX) | DHCP exhaustion | Enable immediately |

**Notification Destination:**

- **Webhooks:** HTTPS POST to PagerDuty integration endpoint
- **Email:** netadmin (at) checkout.com (organization alerts only, not per-network)

### Group Policies

Group Policies allow per-SSID or per-client firewall rules. Standard policy structure:

| Policy | Purpose | Application |
| --- | --- | --- |
| Corporate | Full access + logging | Employees, BYOD (with MDM) |
| Guest | Restricted (no local access) | Visitor SSID, no internal routing |
| IoT | Restricted (DNS whitelist) | Printers, cameras, controlled access |
| Management | VPN-only + syslog | Administrative access, audited |

### User Access Control

| User Type | Access | VPN Required |
| --- | --- | --- |
| Administrator (netadmin) | Full dashboard + CLI | No |
| Network Manager | Dashboard only, no global settings | No |
| Read-Only | View dashboards, no changes | No |
| Contractor | Limited scope + time-based | Yes (corporate VPN) |

---

## Wireless (MR) Standards

### SSID Configuration

#### Corporate SSID

| Setting | Standard | Notes |
| --- | --- | --- |
| SSID Name | `Checkout-Corp` | Broadcast enabled |
| Authentication | WPA3 (preferred) or WPA2-PSK | Strong encryption, no WEP/Open |
| Password | 20+ characters, alphanumeric + symbols | Managed via credential manager |
| PSK Rotation | Annual | Revoke old keys via dashboard |
| Hidden SSID | No | Broadcast for convenience; security not affected by hiding |
| Broadcast | Enabled | All floor/site coverage |

#### Guest SSID

| Setting | Standard | Notes |
| --- | --- | --- |
| SSID Name | `Checkout-Guest` | Open or optional WPA2 |
| Authentication | Open (no password) or shared key | No access to company resources |
| Bandwidth Limit | Per-client: 10 Mbps | Prevent guest saturation |
| Access Control | Splash page (registration) | Log visitors, terms of service |
| DNS Filtering | Strict (Meraki AMP, Umbrella) | Block malware, adult content |

### Access Control Lists (ACL)

| Rule | Direction | Source | Destination | Action |
| --- | --- | --- | --- |
| Block Local Network | All clients | Any | 10.0.0.0/8 | Deny |
| Allow DNS | All clients | Any | 8.8.8.8, 8.8.4.4 | Allow |
| Allow Internet | All clients | Any | 0.0.0.0/0 except 10.0.0.0/8 | Allow |
| Block P2P | All clients | Any | Torrent, BitTorrent ports | Deny |

### Firewall & Traffic Shaping

| Setting | Standard | Notes |
| --- | --- | --- |
| Inbound Filtering | Enabled (drop all by default) | Whitelist only required services |
| Outbound Filtering | Enabled | Block high-risk protocols (Telnet, FTP) |
| IDS/IPS | Enabled | Detect intrusions and malware |
| Content Filtering | DNS filtering (Umbrella) | Block known-bad domains |
| Bandwidth Allocation | Corporate 80%, Guest 20% | Prevent guest saturation |
| QoS | Priority: VoIP > Data > Guest | Video calls prioritized |

### Splash Page

| Setting | Standard | Notes |
| --- | --- | --- |
| Type | Registration (Guest), None (Corporate) | Capture visitor info for access logs |
| Terms & Conditions | Display before access | Legal compliance |
| Redirect URL | Company security policy page | Educate users on acceptable use |

### SSID Availability Schedule

| Schedule | SSID | Availability |
| --- | --- | --- |
| Business Hours | Corporate | Mon-Fri 06:00-22:00 |
| 24/7 | Guest | Always on (external access) |
| Off-Hours | Corporate | Sat-Sun, disabled outside business hours |

### Radio Settings

| Setting | 2.4 GHz | 5 GHz | Notes |
| --- | --- | --- | --- |
| Channel Width | 20 MHz | 40 MHz or 80 MHz | Avoid interference |
| Transmit Power | 20 dBm (high) | 20 dBm (high) | Maximum coverage |
| Band Steering | Enabled | Enabled | Prefer 5 GHz for compatible clients |
| Airtime Fairness | Enabled | Enabled | Prevent slow clients dragging down network |
| Minimum Bitrate | 6.5 Mbps | 13 Mbps | Disconnect weak signals |

### IoT Radio Settings

| Setting | Standard | Purpose |
| --- | --- | --- |
| Separate SSID | `Checkout-IoT` | Isolate IoT devices |
| Authentication | WPA2-PSK | Required; minimal attack surface |
| Band Steering | Disabled | Force 2.4 GHz (IoT device compatibility) |
| Rate Limiting | 5 Mbps per device | Prevent rogue IoT device saturation |
| Access Control | Whitelist DNS only | No internal network access |

### Hotspot 2.0 (Passpoint)

| Setting | Standard | Notes |
| --- | --- | --- |
| Enable | No (unless regulatory requirement) | Additional complexity; most guest networks use splash page |
| Operator Name | "Checkout" | If enabled, registered with Hotspot 2.0 Alliance |
| Domain Name | checkout.com | Match corporate domain |

---

## Switches (MS) Standards

### Routing & DHCP

| Setting | Standard | Notes |
| --- | --- | --- |
| DHCP Server | Enabled per VLAN | Assign IPs based on network segment |
| DHCP Lease Time | 24 hours | Sufficient for office/datacenter |
| DNS Servers | 8.8.8.8, 8.8.4.4 (primary); 1.1.1.1 (secondary) | Redundancy across multiple providers |
| DHCP Reserved Range | 10% of pool | IPs .1-50 reserved for servers/printers |
| DHCP Exclusion | Gateway, DNS, NTP servers | Prevent IP conflicts |

### Access Control Lists

| Rule | Type | Source | Destination | Action |
| --- | --- | --- | --- |
| Allow VLAN routing | L3 | VLAN 10 (Data) | VLAN 20 (Management) | Deny |
| Allow Management VLAN | L3 | VLAN 20 (Mgmt) | All VLANs | Allow |
| Block P2P | L4 | Any | Any | Deny (BitTorrent, etc.) |
| QoS Marking | L3 | Any | Voice/Video traffic | Mark DSCP EF |

### Port Profiles

| Profile | Speed | PoE | Spanning Tree | Purpose |
| --- | --- | --- | --- | --- |
| Access-Device | Auto | On | BPDU Guard | Cameras, APs, access points |
| Server-Link | 1 Gbps (fixed) | Off | No | Upstream links to core |
| Trunk-Link | 10 Gbps (fixed) | Off | Enabled | Inter-switch/uplink |
| IoT-Device | Auto | On (low power) | BPDU Guard | IoT sensors, low bandwidth |

### Access Policies

| Policy | Ports | VLAN Assignment | Purpose |
| --- | --- | --- | --- |
| Trusted-Device | 1-24 (AS configured) | Native VLAN + tagged vlans | Managed devices, servers |
| Guest-Access | Dedicated guest ports | Guest VLAN only | Visitor devices (isolated) |
| IoT-Access | Dedicated IoT ports | IoT VLAN only | Constrained devices |
| Management | Uplink ports to core | Management VLAN (20) | Out-of-band management |

### Port Schedules

| Schedule | Ports | Status | Time | Purpose |
| --- | --- | --- | --- | --- |
| Business Hours | All | Active | Mon-Fri 06:00-22:00 | Standard operation |
| Off-Hours | Guest, IoT | Disabled | Sat-Sun, after hours | Reduce attack surface |
| Maintenance | Uplink | Scheduled downtime | As-needed | Firmware updates |

### Switch Settings

| Setting | Standard | Notes |
| --- | --- | --- |
| IGMP Snooping | Enabled | Prevent multicast flooding |
| Link Aggregation | Enabled (LAG) for core links | Redundancy and bandwidth |
| Spanning Tree | RSTP | Prevent L2 loops |
| BPDU Guard | Enabled on access ports | Prevent loop attacks |
| Root Guard | Enabled on non-core ports | Ensure core is STP root |
| DHCP Option 82 | Enabled | Circuit-ID tracking for DHCP leases |

### Staged Upgrades

| Phase | Devices | Schedule | Rollback Plan |
| --- | --- | --- | --- |
| Canary | 1-2 switches | Tuesday 00:00 UTC | Have previous firmware available |
| Early Access | 25% of fleet | Wednesday 00:00 UTC | Monitor syslog for errors |
| Gradual Rollout | 50% more | Thursday 00:00 UTC | Stagger by site if issues occur |
| Final | Remaining | Friday 00:00 UTC | All devices current within 1 week |

### OSPF Routing

| Setting | Standard | Notes |
| --- | --- | --- |
| Process ID | 1 (default) | Single OSPF instance across all switches |
| Router ID | 10.x.x.x (management IP) | Unique per switch |
| Cost Calculation | Auto (ref-bw 1000) | Based on link speed |
| Network Type | Broadcast | Default for Ethernet |
| Hello Interval | 10 seconds | Fast convergence |
| Dead Interval | 40 seconds | 4x hello interval |
| Area | 0 (backbone) | Single area for simplicity |

---

## Security Standards

### Device Hardening

| Control | Standard | Verification |
| --- | --- | --- |
| Admin Password | 16+ chars, alphanumeric + symbols | Changed quarterly |
| SSH Only | SSH enabled, HTTP disabled | SSH audit logs reviewed monthly |
| SNMP v3 | Enabled; SNMP v1/v2c disabled | Credentials in vault |
| NTP Sync | Primary: internal NTP; Secondary: public | Time sync verified daily |
| Syslog | Enable to centralized syslog server | 30-day retention minimum |

### Compliance & Monitoring

| Area | Standard | Tools |
| --- | --- | --- |
| Firmware Age | Current or N-1 (within 90 days) | Dashboard firmware dashboard |
| Event Logging | 30-day retention | Meraki dashboard native |
| Anomaly Detection | Enabled (AMP, Intrusion) | Alerts to PagerDuty |
| Security Advisories | Reviewed weekly | Meraki security notifications |
| Backup Config | Export quarterly | Version control repo |

---

## Integration Points

### PagerDuty Webhook

**Endpoint:** `https://events.pagerduty.com/v2/enqueue`

**Events:**

- Device offline (5+ minutes)
- High client disconnection rate (>10% in 5 min)
- Configuration change
- Firmware upgrade failure
- Intrusion detection event

### Syslog Destinations

| Priority | Destination | Protocol |
| --- | --- | --- |
| Critical | 10.0.1.100:514 | UDP (local datacenter) |
| Warning | 10.0.1.101:514 | UDP (backup syslog) |
| Info | Meraki dashboard (30-day) | HTTPS (native) |

### API Access

**Service Account:** `meraki-api@checkout.com`

**Permissions:** Read-only for monitoring; write access for automation (change notifications)

**Rate Limit:** 10 requests/second (burst: 100)

---

## Related Standards

- [Equipment Standards](equipment-standards.md) — Meraki device models and lifecycle
- [Security Hardening](security-hardening.md) — Management plane hardening applied to Meraki
- [Equipment Configuration](equipment-config.md) — Baseline configuration templates
- [Naming Standards](naming-conventions.md) — SSID and network naming conventions
