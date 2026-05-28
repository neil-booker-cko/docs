# NTP Configuration Standards

NTP infrastructure and time synchronization standards for Checkout sites. Each site uses a local
FortiGate firewall as the NTP server for network devices, with external NTP pools per region for
upstream time source.

---

## NTP Architecture

**Standard:** Distributed NTP with local FortiGate as the primary time server for all site devices;
firewall synchronizes to region-specific external NTP pools.

| Component | Standard | Purpose |
| --- | --- | --- |
| Local NTP Server | FortiGate firewall | Primary time source for all site devices |
| Local Stratum | 2 or 3 | Derived from external pools (stratum 1) |
| Listen Interfaces | Internal only | Management VLAN, server interfaces (NOT external/WAN) |
| Listen Port | UDP/123 | Standard NTP port |
| External NTP Pools | Country/region pool | Cloud provider NTP or regional public pools |
| Authentication | MD5 (optional) | Can enable for enhanced security |
| Synchronization | 3 servers minimum | Primary + 2 fallback for redundancy |

---

## External NTP Pools by Region

FortiGate synchronizes to region-appropriate NTP pools. Use country-specific or cloud-provider
pools for lower latency and better accuracy.

### Public NTP Pool Servers (by Region)

**Standard:** Use numbered country/region-specific pools for better geographic localization and
load distribution. Avoid generic `pool.ntp.org`.

| Region | Primary Pool | Secondary Pool | Tertiary Pool |
| --- | --- | --- | --- |
| **Europe - Ireland (Dublin)** | `0.ie.pool.ntp.org` | `1.ie.pool.ntp.org` | `2.ie.pool.ntp.org` |
| **Europe - UK (Slough)** | `0.uk.pool.ntp.org` | `1.uk.pool.ntp.org` | `2.uk.pool.ntp.org` |
| **US East (Ashburn)** | `0.us.pool.ntp.org` | `1.us.pool.ntp.org` | `2.us.pool.ntp.org` |
| **US West (San Francisco)** | `0.us.pool.ntp.org` | `1.us.pool.ntp.org` | `2.us.pool.ntp.org` |
| **Asia-Pacific (Singapore)** | `0.sg.pool.ntp.org` | `1.sg.pool.ntp.org` | `0.asia.pool.ntp.org` |

### Cloud Provider NTP Servers (Preferred for Cloud Links)

| Cloud | Region | NTP Server | Notes |
| --- | --- | --- | --- |
| **AWS** | Global | `169.254.169.123` | AWS-specific NTP (only from EC2) |
| **Azure** | Global | `169.254.169.123` | Azure-specific NTP (only from VMs) |
| **GCP** | Global | `metadata.google.internal` | GCP-specific NTP (only from GCP instances) |

**Recommendation:** Use regional public pools (e.g., `pool.ntp.org`) for firewall synchronization;
cloud-specific servers are only accessible from instances within that cloud.

---

## FortiGate NTP Server Configuration

### External NTP Synchronization (Firewall Upstream)

FortiGate synchronizes to external NTP pools. Configure 3 servers for redundancy.

**Example — Dublin DC (Europe):**

```fortios
config system ntp
    set ntpsync enable
    set type pool
    set server "pool.ntp.org"
    set source-ip 10.0.1.1
    set log-sync-interval 1
    set authentication enable
    set key-type SHA256
    set key-id 1
    set authentication-key "MyNTPKey123"
next
end
```

**Example — Ashburn DC (US East):**

```fortios
config system ntp
    set ntpsync enable
    set type pool
    set server "pool.ntp.org"
    set source-ip 10.0.1.1
    set log-sync-interval 1
next
end
```

### Local NTP Service (FortiGate as Server)

Enable NTP service on internal interfaces so network devices can synchronize to the firewall.

```fortios
config system ntp
    set local-ntp enable
    set allow-insecure-ntp enable
end

config system interface
    edit "mgmt"
        set allowaccess ntp
    next
    edit "port1"
        set allowaccess ntp
    next
end
```

**Why `allow-insecure-ntp enable`:** Some DC equipment cannot perform authenticated NTP and must
sync unauthenticated. This setting is required for:

- **Avocent ACS8000 console servers** — no NTP authentication support in any firmware version
    (confirmed against v2.32.1, December 2025). NTP server address is the only configurable
    parameter.
- **Perle IOLAN console servers** — implement SNTP (not full NTP). NTP authentication is supported
    on firmware 6.2 (latest for Checkout's platform) but MD5 only; SHA-256 is not available.
    MD5 does not meet the SHA-256 minimum standard, so Perle devices sync unauthenticated.

**Listening Interfaces (Internal Only):**

- Management VLAN interface (e.g., `vlan10` on port1)
- Server-facing interfaces (e.g., data center management subnets)

**Do NOT enable NTP on:**

- External/WAN interfaces (port2, port3)
- Untrusted zones (guest, public)
- Internet-facing interfaces

---

## NTP Client Configuration

### Network Devices (Routers, Switches, Firewalls)

All network devices point to the local FortiGate firewall as their primary NTP server.

**Cisco IOS-XE:**

```ios
ntp server 10.0.1.1 prefer
ntp server 1.1.1.1
ntp source GigabitEthernet0/0
ntp authentication-key 1 hmac-sha2-256 MyNTPKey123
ntp trusted-key 1
ntp authenticate
```

**FortiGate (Secondary Site Firewall):**

```fortios
config system ntp
    set ntpsync enable
    set type server
    set server "10.0.1.1"
    set source-ip 10.0.1.1
next
end
```

### Perle Console Server (SNTP)

Perle uses SNTP (a subset of NTP). It supports only two servers, which must be pre-registered
in the host table. NTP authentication is supported but requires uploading a key file separately.

```text
set timezone name <TIMEZONE> offset <OFFSET>
set summertime name <SUMMERTIME_ZONE> recurring <SUMMERTIME_DETAILS>

add host <NTP_SERVER_1_NAME> <NTP_SERVER_1_IP>
add host <NTP_SERVER_2_NAME> <NTP_SERVER_2_IP>
add sntp server-1 <NTP_SERVER_1_NAME>
add sntp server-2 <NTP_SERVER_2_NAME>
set sntp mode unicast version 4
```

Verify with: `show time` and `show sntp-info`

**Note:** The `internet address` field in `show sntp-info` output may display incorrectly — use
`show time` to confirm actual synchronisation status.

### Servers and Workstations (Optional)

Servers may synchronize to local FortiGate or directly to external pools:

```bash
# Option 1: Use local FortiGate (recommended for consistency)
server 10.0.1.1 prefer

# Option 2: Use external pool directly (if local NTP unavailable)
pool pool.ntp.org iburst
```

---

## NTP Stratum Hierarchy

**Stratum 0:** Atomic clocks / GPS receivers (reference clocks)
**Stratum 1:** NTP servers with direct reference clock
**Stratum 2:** Our FortiGate firewalls (sync from pool.ntp.org, which are stratum 1)
**Stratum 3+:** Network devices (sync from FortiGate)

Each device increments the stratum by 1 when serving downstream clients.

| Device | Stratum | Source |
| --- | --- | --- |
| pool.ntp.org | 1 | GPS/atomic |
| FortiGate (local) | 2 | pool.ntp.org |
| Router/Switch | 3 | FortiGate |
| Server | 3-4 | Router or FortiGate |

---

## NTP Synchronization Verification

### Check Firewall Time Sync

**FortiGate:**

```fortios
get system ntp status
diagnose sys ntp status
```

### Check Device Time Sync (Cisco)

```ios
show ntp status
show ntp associations
```

### Expected Output (Synchronized)

```text
NTP synchronized to 10.0.1.1 (LOCAL)
Stratum: 3
Reference Clock ID: 10.0.1.1
Root Distance: 0.001000
Root Dispersion: 0.008812
```

---

## NTP Failover Strategy

### Primary Firewall Failure

If primary FortiGate NTP fails:

1. **Secondary server:** Clients should have secondary server configured (e.g., 1.1.1.1)
2. **Automatic retry:** NTP clients retry on next poll interval (typically 64-1024 seconds)
3. **Manual intervention:** Update network device NTP servers to backup FortiGate or external pool

### High Availability (FortiGate HA Pair)

In active-passive HA setup, NTP service is provided by the active unit. On failover, passive
becomes active and continues serving NTP.

```fortios
config system ha
    set mode active-passive
    set priority 250
    set priority-secondary 200
end
```

The passive unit synchronizes to the primary's NTP source during standby.

---

## NTP Security

### NTP Authentication (SHA-256)

**Required** on all devices. MD5 is deprecated per RFC 8573; SHA-256 is the minimum standard.

**Platform requirements:**

- **FortiOS:** SHA-256 requires FortiOS 7.4.4 or later. DC fleet is on 7.6.6 — compliant.
- **Cisco IOS-XE:** `hmac-sha2-256` requires IOS-XE 17.2 or later. DC fleet is on 17.12.6 —
    compliant.

**FortiGate:**

```fortios
config system ntp
    set authentication enable
    set key-type SHA256
    set key-id 1
    set authentication-key "MySecureNTPKey123"
next
end
```

**Cisco IOS-XE:**

```ios
ntp authentication-key 1 hmac-sha2-256 MySecureNTPKey123
ntp trusted-key 1
ntp authenticate
```

### NTP Access Control (Already Covered)

See [Security Hardening Standards](security-hardening.md) for NTP access-group configuration:

- `peer` → ACL_NTP_SERVERS
- `serve`, `serve-only`, `query-only` → ACL_DENY_ALL

---

## Troubleshooting

### Firewall Not Syncing to External Pool

**Checklist:**

1. **External connectivity:** Ping external NTP server from FortiGate

   ```fortios
   execute ping pool.ntp.org
   ```

2. **Firewall policy:** Ensure policy allows outbound UDP/123 to external NTP servers

3. **NTP status:** Check synchronization status

   ```fortios
   get system ntp status
   ```

4. **Network route:** Verify default route to reach external pool

### Devices Not Syncing to Firewall

**Checklist:**

1. **Firewall listening:** Verify NTP enabled on internal interfaces

   ```fortios
   get system interface | grep -A 5 allowaccess
   ```

2. **Client pointing:** Check device NTP configuration

   ```ios
   show run | include ntp
   ```

3. **Firewall policy:** Ensure policy allows inbound UDP/123 from internal networks

4. **Network connectivity:** Ping firewall NTP IP from client

5. **Time offset:** If offset too large (>128ms), device may reject sync

   ```text
   Manual time correction: clock set HH:MM:SS MMM DD YYYY (Cisco)
   ```

---

## Site-by-Site NTP Configuration Summary

| Site | Domain | Firewall IP | External Pool | Region |
| --- | --- | --- | --- | --- |
| Dublin DC | eld7.checkout.corp | 10.0.1.1 | pool.ntp.org / 0.ie.pool.ntp.org | Europe |
| Ashburn DC | edc4.checkout.corp | 10.0.1.1 | pool.ntp.org / 0.us.pool.ntp.org | US East |
| London Office | lon1.checkout.corp | 10.0.1.1 | pool.ntp.org / 0.uk.pool.ntp.org | Europe |
| San Francisco | sfo1.checkout.corp | 10.0.1.1 | pool.ntp.org / 0.us.pool.ntp.org | US West |

---

## Related Standards

- [Security Hardening](security-hardening.md) — NTP access-groups (peer, serve, serve-only, query-only)
- [DNS Standards](dns-standards.md) — Parallel local service approach
- [Naming Conventions](naming-conventions.md) — Device naming scheme
