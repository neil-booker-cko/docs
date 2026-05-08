# DNS Configuration Standards

DNS infrastructure and resolution standards for Checkout sites. Each site uses a local FortiGate
firewall as the DNS server for network devices, with external forwarders for all other queries.

---

## DNS Architecture

**Standard:** Distributed DNS with local FortiGate as authoritative server for device zone; all
other queries forwarded to external recursive resolvers.

| Component | Standard | Purpose |
| --- | --- | --- |
| Local DNS Server | FortiGate firewall | Authoritative for network devices; recursive forwarder for Internet |
| Local Zone | `<site>.checkout.corp` | Device hostname resolution (switches, routers, firewalls) |
| Local Zone Scope | Network devices only | Management IPs, loopbacks, interfaces |
| Forwarding | Conditional (external) | All non-local domains forward to upstream resolvers |
| Recursive Resolution | Enabled on FortiGate | Firewall acts as recursive resolver for clients |
| Listen Interfaces | Internal only | Management VLAN, server interfaces (NOT external/WAN) |
| Listen Port | UDP/53 | Standard DNS port (TCP fallback if needed) |

---

## Local Domain Naming

**Standard:** Each site has a local domain name: `<SITE-ID>.checkout.corp`

| Site | Domain | Example Devices |
| --- | --- | --- |
| Dublin DC (ELD7) | `eld7.checkout.corp` | eld7-csw-01, eld7-csw-02, eld7-con-01 |
| Ashburn DC (EDC4) | `edc4.checkout.corp` | edc4-csw-01, edc4-pfw-01a, edc4-pfw-01b |
| London Office (LON1) | `lon1.checkout.corp` | lon1-asw04-01a, lon1-pfw-01a, lon1-pfw-01b |
| San Francisco (SFO1) | `sfo1.checkout.corp` | sfo1-asw01-01, sfo1-con-01 |

---

## FortiGate DNS Server Configuration

### Local DNS Zone (Authoritative)

Create DNS zone for network devices in the site. Zone contains A records for all managed network
equipment (routers, switches, firewalls, console servers, access points).

**Example — Dublin DC (eld7.checkout.corp):**

```fortios
config system dns-database
    edit "eld7.checkout.corp"
        set type master
        set allow-transfer "0.0.0.0" "255.255.255.255"
        config dns-entry
            edit 1
                set hostname "eld7-csw-01.eld7.checkout.corp"
                set ip 10.0.0.1
            next
            edit 2
                set hostname "eld7-csw-02.eld7.checkout.corp"
                set ip 10.0.0.2
            next
            edit 3
                set hostname "eld7-pfw-01a.eld7.checkout.corp"
                set ip 10.0.1.10
            next
            edit 4
                set hostname "eld7-con-01.eld7.checkout.corp"
                set ip 10.0.1.20
            next
        end
    next
end
```

### DNS Forwarders (Recursive Resolution)

Configure external DNS servers for all non-local queries. FortiGate forwards requests for zones
outside `<site>.checkout.corp` to upstream resolvers.

**Preferred External Resolvers:**

| Priority | Provider | Address | Notes |
| --- | --- | --- | --- |
| 1 | Cloudflare | `1.1.1.1` | Fast, privacy-focused, DNSSEC |
| 2 | Google | `8.8.8.8` | Reliable, global network |
| 3 | ISP | `<ISP-provided>` | Fallback if external unavailable |

```fortios
config system dns
    set primary 1.1.1.1
    set secondary 8.8.8.8
    set tertiary <ISP-DNS-IP>
end
```

### DNS Server Listen Configuration

FortiGate listens for DNS queries on internal interfaces only (management VLAN, server-facing
interfaces). External/WAN interfaces do NOT listen for DNS.

```fortios
config system interface
    edit "mgmt"
        set allowaccess ping https ssh snmp http telnet ftp
        set dns-server-override enable
    next
    edit "port1"
        set vdom "root"
        set ip 10.0.1.1 255.255.255.0
        set allowaccess dns
    next
end

config system global
    set dns-proxy enable
    set dns-filter-proto udp tcp
end
```

**Listening Interfaces (Internal Only):**

- Management VLAN interface (e.g., `vlan10` on port1)
- Server-facing interfaces (e.g., data center management subnets)

**Do NOT enable DNS on:**

- External/WAN interfaces (port2, port3)
- Untrusted zones (guest, public)
- Internet-facing interfaces

### Recursive DNS Service

FortiGate DNS proxy operates as a recursive resolver: it queries upstream servers on behalf of
internal clients and caches results.

```fortios
config system dns
    set cache-notexist enable
    set cache-limit 5000
    set retransmit 0
    set timeout 2
end
```

---

## Client DNS Configuration

### Network Devices (Routers, Switches, Firewalls)

All network devices point to the local FortiGate firewall as their primary DNS server.

**Cisco IOS-XE:**

```ios
ip name-server 10.0.1.1
ip domain-name eld7.checkout.corp
ip domain-lookup
```

**FortiGate (Secondary Site Firewall):**

```fortios
config system dns
    set primary 10.0.1.1
    set secondary 1.1.1.1
    set timeout 2
end
```

### Servers and Workstations (Optional)

Servers may point directly to external DNS or use local FortiGate as forwarder:

```bash
# Option 1: Use local FortiGate (recommended for consistency)
nameserver 10.0.1.1

# Option 2: Use external resolvers directly (if local DNS unavailable)
nameserver 1.1.1.1
nameserver 8.8.8.8
```

---

## DNS Failover Strategy

### Primary Failure

If primary FortiGate DNS fails:

1. **Automatic:** Clients retry on secondary server (if configured)
2. **Manual:** Update network device DNS pointing to backup FortiGate
3. **Emergency:** Point clients directly to external resolvers (1.1.1.1, 8.8.8.8)

### High Availability (FortiGate HA Pair)

In active-passive HA setup, DNS is served from the active unit. On failover, passive becomes
active and continues serving DNS.

```fortios
config system ha
    set mode active-passive
    set priority 250
    set priority-secondary 200
end
```

---

## DNS Security

### DNSSEC (Optional Future)

Currently not enabled. Consider for future hardening:

- Validates DNS responses
- Prevents DNS spoofing
- Supported by Cloudflare and Google resolvers

### DNS Filtering

FortiGate can optionally filter DNS queries:

- Block malicious domains (malware, phishing)
- Block adult content (office networks)
- Logging of all DNS queries for audit

---

## Verification Commands

**FortiGate DNS Status:**

```fortios
get system dns
diagnose dns name-resolution 8.8.8.8
```

**Test DNS from Network Device (Cisco):**

```ios
ping eld7-csw-01.eld7.checkout.corp
nslookup 8.8.8.8 10.0.1.1
```

**Test DNS Resolution (Linux):**

```bash
nslookup eld7-csw-01.eld7.checkout.corp 10.0.1.1
dig @10.0.1.1 eld7-csw-01.eld7.checkout.corp
```

---

## Troubleshooting

### DNS Not Resolving

**Checklist:**

1. **Firewall listening:** Verify DNS enabled on FortiGate internal interfaces
2. **Client pointing:** Check device `show running-config | include name-server` (Cisco)
3. **Zone entries:** Verify hostname exists in local zone: `get system dns-database`
4. **Forwarders:** Test upstream resolvers: `diagnose dns name-resolution 8.8.8.8`
5. **Firewall policy:** Ensure policy allows DNS (UDP/53) from clients to FortiGate
6. **Network connectivity:** Ping FortiGate DNS IP from client

### Slow DNS Resolution

- Increase timeout: `set timeout 3` or `4`
- Check FortiGate CPU: `get system performance`
- Verify upstream resolvers responding: `diagnose dns name-resolution google.com`

---

## Related Standards

- [Security Hardening](security-hardening.md) — DNS configuration on FortiOS
- [Firewall Policy Standards](firewall-standards.md) — DNS in firewall rules
- [Naming Conventions](naming-conventions.md) — Device naming scheme
