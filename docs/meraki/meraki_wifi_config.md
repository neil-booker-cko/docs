# Cisco Meraki WiFi Configuration Guide

Meraki is a cloud-managed WiFi and networking platform eliminating per-AP configuration. Network
settings, security policies, and monitoring are managed centrally via the Meraki Dashboard (web
UI). All APs in a network inherit settings instantly; no CLI required.

---

## At a Glance

| Task | Location | Key Setting |
| --- | --- | --- |
| **Create SSID** | Dashboard → Configure → Wireless → SSIDs | SSID name, security, VLAN |
| **Enable WPA3** | SSID Settings → Security | WPA3-Personal or WPA3-Enterprise |
| **Configure RADIUS** | SSID Settings → Security → RADIUS | RADIUS server IP, port, secret |
| **Enable 802.11r** | SSID Settings → Advanced → 802.11r Fast Roaming | Toggle enable |
| **Band Steering** | Network-wide Settings → Band Steering | Automatic (default enabled) |
| **Client Limit** | SSID Settings → Advanced → Airtime Fairness | Set max clients per AP |
| **Guest Network** | Configure → Guest Network | Splash page, bandwidth limit |
| **Monitor Clients** | Wireless → Clients | View by AP, SSID, or device |

---

## Dashboard Navigation

### Login and Network Selection

1. Navigate to [https://dashboard.meraki.com](https://dashboard.meraki.com)
1. Sign in with Meraki account (SSO or direct credentials)
1. Select Organization → Network from dropdown
1. All settings now apply to selected network

**Multi-site Management:** Different organizations can manage different networks. Change
organization via account dropdown (top right).

### Key Menu Sections

- **Wireless → Overview:** Real-time network status, AP list, client count
- **Wireless → Clients:** View all connected clients, by SSID or AP
- **Configure → Wireless:** Create/edit SSIDs and global settings
- **Monitor → Events:** Logs of client associations, deauthentications, errors
- **Monitor → Analytics:** Heatmaps, throughput graphs, roaming events

---

## Initial Setup

### Step 1: Add APs to Network

1. **Claim AP hardware:** Unbox AP, power on; AP broadcasts setup SSID
1. **Use Meraki mobile app or Dashboard:**

    - Wireless → Overview → "Add Device" → Claim device
    - Enter AP serial number or scan QR code
1. **AP auto-provisions:** Within 2–5 minutes, AP joins network and downloads settings
1. **Verify:** AP appears in Wireless → Overview with green "online" status

### Step 2: Create Admin Account and MFA

1. Navigate to Organization → Settings → Administrators
1. Invite additional admins (email-based)
1. Enable two-factor authentication (MFA) for security

### Step 3: Configure Time Zone and NTP

1. Organization → Settings → Time Zone: Set local time zone
1. NTP automatically set to Meraki default; change if needed:

    - Wireless → Configure → Network-wide Settings → NTP Servers

---

## SSID Configuration

### Create a New SSID

1. Go to **Configure → Wireless → SSIDs**
1. Click **"Add SSID"** button
1. Fill in settings (see below)
1. Click **"Save"** — setting propagates to all APs instantly

### Basic Settings

| Field | Example | Notes |
| --- | --- | --- |
| **SSID Name** | corp-network | Visible to clients; max 32 chars |
| **Enabled** | Toggle on | Broadcast SSID (off = hidden) |
| **Band** | Dual Band | 2.4 GHz, 5 GHz, or both |
| **VLAN** | 100 | Corporate traffic on VLAN 100 |
| **AP Tags** | building-1 | Optional; apply SSID to subset of APs |

### Security Settings

#### WPA3-Personal (PSK)

```text
Security: WPA3-Personal
PSK: <strong-password>  (min 8 chars, recommend 20+ random)
```

Ideal for small offices, home, or guest networks with shared password.

#### WPA3-Enterprise (802.1X)

```text
Security: WPA3-Enterprise
RADIUS Servers:
  Primary: 192.168.1.10:1812
  Shared Secret: <radius-secret>
  Secondary: 192.168.1.11:1812  (optional redundancy)
```

Requires RADIUS server (FreeRADIUS, Windows NPS, Cisco ISE). Clients authenticate with
username/password or certificate.

#### WPA3-Transition (Mixed)

```text
Security: WPA3-Transition (WPA3-Personal and WPA2-Personal)
PSK: <password>
```

Allows both WPA3-capable and older WPA2-only clients on same SSID. Used during device migration.

#### Open Network (No Encryption)

```text
Security: Open
Splash Page: Optional (portal for guest acceptance)
```

No encryption; traffic in clear. Use only for guest networks with HTTPS requirement.

#### OWE (Opportunistic Wireless Encryption)

```text
Security: OWE (Open with Encryption)
```

Encrypts open-network traffic without pre-shared key. Guests connect without password but
traffic encrypted.

### Advanced Settings

1. **802.11r Fast Roaming:**

    - Enable for sub-100 ms handover (VoIP/video deployments)
    - Requires 802.11r-capable clients

1. **802.11k / 802.11v:**

    - Automatically enabled with WPA3-Enterprise
    - Enables AP-assisted roaming and load balancing

1. **RADIUS Accounting:**

    - Send RADIUS accounting packets (for billing/audit)
    - Toggle: "RADIUS Accounting" → enable

1. **Airtime Fairness:**

    - Limit maximum clients per AP (prevents overcrowding)
    - Example: Set to 30 for 802.11ac; 50 for 802.11ax

1. **Min Bit Rate:**

    - Set minimum data rate (e.g., 24 Mbps minimum)
    - Forces slow devices to disconnect if below threshold

---

## Network-Wide Security Policies

### Access Control Lists (ACL)

1. Configure → Wireless → Network-wide Settings → **Access Control**
1. Create rules by client MAC address or IP range
1. Actions: Allow, Deny, or Required Authentication

**Example:**

```text
Rule 1: Allow all on corp-network SSID
Rule 2: Deny blacklisted MAC addresses on all SSIDs
Rule 3: Require 802.1X for IoT SSID
```

### Firewall and Traffic Management

1. Security → Firewall → Layer 7 Firewall
1. Block or rate-limit applications:

    - Block P2P, torrenting, streaming on corporate SSID
    - Allow all on guest SSID

1. Traffic Shaping (QoS):

    - Configure → Wireless → Network-wide Settings → **QoS**
    - Set bandwidth limits per SSID, client, or application

---

## RADIUS Integration (802.1X)

### Configure RADIUS Server

In SSID Settings → Security → RADIUS Servers:

```text
Primary RADIUS:
  IP: 192.168.1.10
  Port: 1812 (default)
  Shared Secret: <long-random-string>  (min 16 chars)

Secondary RADIUS (optional):
  IP: 192.168.1.11
  Port: 1812
  Shared Secret: <same-as-primary>

RADIUS Accounting (optional):
  IP: 192.168.1.10
  Port: 1813 (default)
  Enable: Yes
```

**Note:** Shared secret must match RADIUS server configuration exactly (case-sensitive, no
spaces).

### VLAN Assignment via RADIUS

RADIUS can assign clients to different VLANs based on authentication:

**RADIUS server configuration (example):**

```text
User: alice@corp.com
Groups: Engineering
Return Attributes:
  Tunnel-Type = VLAN
  Tunnel-Medium-Type = 802
  Tunnel-Private-Group-ID = 100  → Client assigned to VLAN 100
```

Meraki receives VLAN assignment and tags client traffic accordingly.

### Test RADIUS Connectivity

1. SSID Settings → Security → RADIUS Servers
1. Click **"Test"** button
1. Meraki sends test Access-Request packet
1. Verify "Success" message (if fails, check IP, port, shared secret)

---

## Client Management and Monitoring

### View Connected Clients

1. Go to **Wireless → Clients**
1. Filter by:

    - SSID
    - AP
    - Device type (iOS, Android, Windows, etc.)
    - Activity (active, recently connected, etc.)

1. **Client Details:**

    - Signal strength (RSSI), data rate, throughput
    - Roaming events (which AP client moved to)
    - IP address (v4/v6)
    - Connection duration

### Client Policies

1. **Per-Client Bandwidth Limits:**

    - Wireless → Clients → Select client → Edit → Set bandwidth cap

1. **Device Quarantine:**

    - Isolate problematic device to separate VLAN or block

1. **Client Notifications:**

    - Configure email alerts when specific devices connect/disconnect

### Roaming and Mobility

**Automatic Roaming Optimization (Default):**

- 802.11r (FT) enabled on WPA3-Enterprise
- 802.11k (RRM) enabled automatically
- 802.11v (BTM) enabled automatically
- Clients roam between APs with <100 ms disruption

**Band Steering (Automatic):**

- Capable clients automatically steered to 5/6 GHz
- Prevents 2.4 GHz congestion
- Manual override per-client if needed

---

## Guest Networks

### Create Guest SSID

1. Configure → Guest Network → **"Enable Guest Network"**
1. Set SSID name: "Guest" or custom
1. Optionally configure:

    - Bandwidth limit per user (e.g., 10 Mbps)
    - Session duration (e.g., 24 hours)
    - Splash page (login, survey, or accept terms)

### Guest Splash Page Options

1. **Click-through:** Guest accepts terms, clicks "Accept" to connect
1. **Sign-up:** Guest enters email; credentials sent via email
1. **Sponsored:** Admin pre-approves guests (no splash)
1. **Custom URL:** Redirect to external portal (for advanced workflows)

### Guest Bandwidth Limiting

```text
Configure → Wireless → Network-wide Settings → Guest Network
  Per-User Bandwidth Limit: 10 Mbps (example)
```

Ensures guests don't saturate network.

---

## Channel and Power Management

### Automatic Channel Selection (Default)

Meraki automatically selects optimal channels based on interference detection:

- **2.4 GHz:** Channels 1, 6, 11 (non-overlapping)
- **5 GHz:** Channels 36–165 (80 MHz or 20 MHz depending on deployment)
- **6 GHz:** Channels 1–233 (WiFi 6E APs only)

**Manual Override (if needed):**

1. Wireless → Configure → RF Profiles
1. Create custom RF profile with specific channels
1. Assign to SSID or AP tag

### Transmit Power

**Default:** Auto (AP adjusts power based on demand)

**Manual Adjustment (rare):**

1. Wireless → Configure → RF Profiles
1. Set power to 100%, 75%, 50%, 25%, or 10%
1. Lower power reduces overlap; higher power increases range

---

## Monitoring and Troubleshooting

### Real-Time Monitoring

1. **Wireless → Overview:**

    - Network health, AP status, client count
    - "Blips" (brief disconnections) shown on timeline

1. **Wireless → Analytics:**

    - Heatmaps (RSSI coverage)
    - Throughput graphs per SSID
    - Roaming frequency per client

1. **Wireless → Clients:**

    - Filter by SSID or AP
    - Sort by signal strength, roaming events, data rate

### Event Logs

1. **Monitor → Events**
1. Filter by:

    - Type (Association, Deauthentication, 802.1X Auth Failure, etc.)
    - Client or AP
    - Time range

1. **Common Events:**

    - "Client associated to SSID" → client connected
    - "802.1X authentication failed" → credentials wrong or RADIUS unreachable
    - "Client idle timeout" → client inactive, disconnected
    - "Excessive roaming detected" → client unstable, check signal

### Alarms and Notifications

1. **Organization → Alerts → Alerts Settings**
1. Configure email notifications for:

    - AP offline (power loss, internet down)
    - High client count (approaching AP limit)
    - 802.1X failures (authentication issues)
    - Frequent roaming (signal instability)

---

## Common Configuration Examples

### Corporate Network with 802.1X

**SSID Name:** corp-network

```text
Security: WPA3-Enterprise
RADIUS:
  Primary: 192.168.1.10:1812 (Windows NPS or Cisco ISE)
  Shared Secret: <secret>
VLAN: 100 (Corporate)
Advanced:
  802.11r: Enable
  Airtime Fairness: 30 clients per AP
  Min Bit Rate: 12 Mbps
```

**Firewall Rules:**

- Allow all traffic (RADIUS handles user authentication)

---

### Guest Network with Splash Page

**SSID Name:** Guest

```text
Security: Open
Guest Network: Enable
Splash Page: Click-through (terms acceptance)
Bandwidth Limit: 10 Mbps per user
VLAN: 200 (Guest)
```

**Firewall Rules:**

- Block access to corporate VLAN 100
- Allow all internet traffic

---

### IoT Network with MAC Filtering

**SSID Name:** iot-devices

```text
Security: WPA2-Personal
PSK: <strong-password>
VLAN: 300 (IoT)
Access Control: Allow only approved MACs (printers, cameras, sensors)
Advanced:
  Min Bit Rate: 6 Mbps (IoT devices often slow)
  Client Idle Timeout: 24 hours
```

**Firewall Rules:**

- Block IoT access to corporate VLAN
- Limit to local subnet communication only

---

## Best Practices for Meraki WiFi

| Practice | Reason |
| --- | --- |
| **Use WPA3-Enterprise for corporate** | Per-user auth, audit trail, VLAN segmentation |
| **Enable 802.11r for VoIP deployments** | Sub-100 ms roaming required for voice quality |
| **Set reasonable AP client limits** | Prevent overcrowding; balance coverage vs capacity |
| **Monitor event logs weekly** | Catch authentication or stability issues early |
| **Keep dashboard updated** | Security patches, feature releases |
| **Test RADIUS before rollout** | Ensure connectivity before deploying to users |
| **Use AP tags for multi-site deployments** | Apply different settings to different locations |
| **Document SSID/VLAN mapping** | Facilitates future troubleshooting |

---

## Notes / Gotchas

- **Cloud Dependency:** APs require internet connectivity to reach Meraki cloud for management.
  If WAN down, APs continue operating on cached settings but cannot update configuration.

- **Shared Secret Case-Sensitive:** RADIUS shared secret must match exactly on Meraki and RADIUS
  server (spaces, capitalization matter). Mismatch causes silent authentication failures.

- **VLAN Must Exist on Upstream Switch:** If SSID assigned to VLAN 100, that VLAN must be
  configured on wired switch ports where APs connect (trunk port). Otherwise clients get no IP.

- **High Client Density:** Setting airtime fairness to 50+ clients per AP degrades throughput for
  all clients. Default 30–40 is safer for 802.11ac; 50+ for 802.11ax only.

- **Guest Network Splash Page Timeout:** Guests with stale splash page session may not reconnect
  without re-entering details. Session timeout default is usually 1 hour; adjust if needed.

- **Roaming Loops:** If client roams too frequently between APs (every few seconds), check signal
  strength balance. May indicate overlapping coverage with poor SNR in overlap zone.

---

## See Also

- [WiFi Standards Comparison](../theory/wifi_standards_comparison.md)
- [WiFi RF Fundamentals](../theory/wifi_rf_fundamentals.md)
- [802.1X and EAP Authentication](../theory/wifi_authentication_8021x.md)
- [WiFi Roaming (802.11r/k/v)](../theory/wifi_roaming.md)
- [WiFi Security](../theory/wifi_security.md)
- [WiFi Network Design](../theory/wifi_network_design.md)
- [WiFi Troubleshooting](../operations/wifi_troubleshooting.md)
