# Firewall Policy Standards

FortiGate security policy configuration, rule structure, logging, and performance tuning.

---

## Firewall Policy Architecture

### Policy Ordering

Policies are evaluated **top-to-bottom**; first match wins. Order policies by:

1. **Deny/Block rules** (most specific to least specific)
2. **Allow rules** (most specific to least specific)
3. **Catch-all rule** (implicit deny at end)

| Rule Priority | Type | Example | Notes |
| --- | --- | --- | --- |
| 1 | Deny | Block known-bad IP ranges (bogons) | Reject earliest; save processing |
| 2 | Deny | Block C2/malware domains | IPS/AMP detection |
| 3 | Deny | Deny RFC1918 (private IPs) inbound | Prevent spoofing |
| 4 | Allow | Allow web traffic (80, 443) | Permit business traffic |
| 5 | Allow | Allow DNS (53) | Essential service |
| 6 | Allow | Allow NTP (123) | Timekeeping |
| 7 | Deny | Deny all other traffic (implicit) | Default-deny posture |

### Example Policy Order

```fortios
config firewall policy
    edit 1
        set name "DENY-Bogon-Inbound"
        set srcintf "any"
        set dstintf "any"
        set action deny
        set logtraffic all
        # ... more config
    next
    edit 2
        set name "ALLOW-Web-Traffic"
        set srcintf "trust"
        set dstintf "untrust"
        set srcaddr "Internal-Subnet"
        set dstaddr "External-Servers"
        set service "HTTP" "HTTPS"
        set action accept
        set logtraffic all
    next
end
```

---

## Policy Naming Convention

**Format:** `[ACTION]-[SOURCE]-[DESTINATION]-[SERVICE]`

### Standard Policy Names

| Policy Name | Action | Source | Destination | Service |
| --- | --- | --- | --- | --- |
| `DENY-Bogon-Inbound` | Deny | Any (external) | Any | All |
| `ALLOW-Corp-to-Internet` | Allow | Corp-VLAN | Internet | HTTP, HTTPS, DNS |
| `ALLOW-Guest-to-Internet` | Allow | Guest-VLAN | Internet | HTTP, HTTPS only |
| `ALLOW-IoT-to-DNS` | Allow | IoT-VLAN | DNS servers | DNS (UDP 53) |
| `DENY-IoT-to-Internal` | Deny | IoT-VLAN | Internal networks | All |
| `ALLOW-AWS-VPN` | Allow | AWS-VPC | Local networks | All |
| `ALLOW-Mgmt-SSH` | Allow | Mgmt-VLAN | Routers/Switches | SSH (TCP 22) |

---

## Policy Configuration Template

### Full Policy Example

```fortios
config firewall policy
    edit 100
        set name "ALLOW-Corp-to-Internet"
        set uuid "550e8400-e29b-41d4-a716-446655440000"

        # Source and Destination
        set srcintf "port1.100"
        set dstintf "port2"
        set srcaddr "Corporate-VLAN"
        set dstaddr "Internet"

        # Services and Action
        set service "HTTP" "HTTPS" "DNS" "NTP"
        set action accept
        set schedule "always"

        # Logging and Visibility
        set logtraffic all
        set log-traffic-start enable
        set logtraffic-start enable

        # Performance and Optimization
        set profile-type single
        set profile-protocol-options "default"
        set av-profile "default"
        set ips-sensor "default"
        set ssl-ssh-profile "default"
        set nattype dynamic
        set nat enable
        set ippool enable
        set poolname "Corp-NAT-Pool"

        # Advanced Options
        set timeout-send-rst enable
        set timeout-tcp-session 86400
        set timeout-udp-session 300
        set timeout-icmp-session 60

        # Comments
        set comments "Allow corporate users to access internet"

    next
end
```

---

## Address Objects & Groups

### Standard Address Object Naming

**Format:** `[PURPOSE]-[TYPE]-[DESCRIPTION]`

| Address Object | Type | Value | Notes |
| --- | --- | --- | --- |
| `AWS-VPC-CIDR` | Subnet | 10.10.0.0/16 | AWS Primary VPC |
| `Azure-VNet-CIDR` | Subnet | 10.20.0.0/16 | Azure virtual network |
| `Corporate-VLAN` | Group | VLAN100 + VLAN200 | Corporate traffic |
| `Internal-DNS` | Host | 10.0.1.10 | Local DNS server |
| `Google-DNS` | Host | 8.8.8.8 | External DNS fallback |
| `RFC1918-Bogon` | Group | 10.0.0.0/8 + 172.16.0.0/12 + 192.168.0.0/16 | Bogon IP ranges |

---

## Service Objects

### Standard Service Groups

| Service Group | Services | Protocol | Port |
| --- | --- | --- | --- |
| `Web-Browsers` | HTTP, HTTPS | TCP | 80, 443 |
| `DNS-Resolution` | DNS | UDP | 53 |
| `Remote-Access` | SSH, RDP | TCP | 22, 3389 |
| `VoIP-Signaling` | SIP | TCP/UDP | 5060, 5061 |
| `NTP-Time` | NTP | UDP | 123 |
| `Syslog-Collection` | Syslog | UDP | 514 |

---

## Traffic Logging Standards

### Logging Policy

All policies must have:

1. **Log all traffic:** `set logtraffic all`
2. **Log session start:** `set logtraffic-start enable`
3. **Log when rule is matched:** Critical and Warning level

### Log Destination

**Primary:** Syslog to centralized logging (10.0.1.100:514)

```fortios
config log syslogd setting
    set status enable
    set server "10.0.1.100"
    set port 514
    set facility local2
    set source-ip 10.0.2.1
next
end
```

**Secondary:** Disk (local logging if syslog unavailable)

```fortios
config log disk setting
    set status enable
    set diskfull overwrite
    set maximum-log-size 1024
next
end
```

---

## Deep Packet Inspection (DPI) Profiles

### IPS/AMP Integration

All outbound policies should apply default IPS/AMP profiles:

| Profile | Setting | Notes |
| --- | --- | --- |
| AV Profile | Default (Fortiguard) | Detect malware/ransomware |
| IPS Sensor | Default (intrusion detection) | Detect exploits, DoS |
| SSL/SSH Profile | Default (certificate inspection) | HTTPS threat detection |
| Application Control | High-risk apps blocked | Block P2P, torrents, mining |
| Antispam | Enable (outbound only) | Prevent spam relay |

```fortios
config firewall policy
    edit 100
        set name "ALLOW-Corp-to-Internet"
        set av-profile "default"
        set ips-sensor "default"
        set ssl-ssh-profile "default"
        set application-list "default"
        set antispam-profile "default"
    next
end
```

---

## Bandwidth Control & QoS

### Per-Policy Traffic Shaping

| Policy | Upstream Limit | Downstream Limit | Priority |
| --- | --- | --- | --- |
| Voice (VoIP) | Unlimited | Unlimited | High |
| Video Call | 10 Mbps | 10 Mbps | High |
| Corporate Web | 100 Mbps | 100 Mbps | Medium |
| Guest Internet | 10 Mbps per user | 10 Mbps per user | Low |
| Backup/Replication | 50 Mbps | 50 Mbps | Low |

```fortios
config firewall policy
    edit 100
        set name "ALLOW-Corp-to-Internet"
        set traffic-shaper "Corporate-Shaper"
        set traffic-shaper-reverse "Corporate-Shaper-Reverse"
    next
end

config traffic-shaper
    edit "Corporate-Shaper"
        set guaranteed-bandwidth 100000
        set maximum-bandwidth 100000
        set priority high
    next
end
```

---

## NAT & PAT Configuration

### Source NAT (Dynamic PAT)

**Requirement:** All outbound traffic from private VLANs must use NAT.

```fortios
config firewall policy
    edit 100
        set srcaddr "Corporate-VLAN"
        set dstaddr "Internet"
        set nat enable
        set nattype dynamic
        set poolname "Corp-NAT-Pool"
    next
end

config firewall ippool
    edit "Corp-NAT-Pool"
        set startip 203.0.113.1
        set endip 203.0.113.10
    next
end
```

### Destination NAT (Port Forwarding)

**Requirement:** Inbound to public-facing services (web, mail).

```fortios
config firewall ippool
    edit "Web-Server-NAT"
        set startip 10.1.0.50
        set endip 10.1.0.50
        set type overload
    next
end

config firewall policy
    edit 200
        set name "ALLOW-Inbound-Web"
        set srcaddr "Internet"
        set dstaddr "Web-Server"
        set dstintf "port2"
        set srcintf "port2"
        set service "HTTP" "HTTPS"
        set action accept
        set nattype static
        set nat enable
        set ippool enable
        set poolname "Web-Server-NAT"
    next
end
```

---

## Policy Performance Tuning

### Hardware Acceleration

Enable hardware acceleration on supported hardware:

```fortios
config system settings
    set asymroute enable
    set tcp-option enable
    set vpn-stats-log enable
    set fec-port 1
next
end

config system npu-vlink
    edit "vlink0"
        set ips-offload enable
    next
end
```

### Connection Optimization

```fortios
config firewall policy
    edit 100
        set timeout-send-rst enable
        set timeout-tcp-session 86400
        set timeout-udp-session 300
        set timeout-icmp-session 60
        set sessions enable
    next
end
```

---

## Rule Recommendations

### Deny Rules (Implicit at End)

```fortios
config firewall policy
    edit 999
        set name "DENY-ALL-CATCH-ALL"
        set action deny
        set srcaddr "all"
        set dstaddr "all"
        set service "all"
        set logtraffic all
        set comments "Implicit deny; all traffic not explicitly allowed"
    next
end
```

### Anti-Spoofing & RFC1918

```fortios
config firewall policy
    edit 1
        set name "DENY-Bogon-Inbound"
        set srcintf "port2"  # WAN interface
        set dstintf "any"
        set action deny
        set srcaddr "RFC1918-Bogon"
        set logtraffic all
        set comments "Block RFC1918 private IPs on WAN (spoofing)"
    next
end
```

---

## Testing & Validation

### Pre-Deployment Policy Testing

1. **Review rule order** — Ensure no shadowing
2. **Test deny rules** — Verify bogon blocking, anti-spoofing
3. **Test allow rules** — Verify business traffic flows
4. **Test logging** — Confirm syslog reception
5. **Test DPI** — Verify AV/IPS/SSL profiles active
6. **Performance test** — Measure throughput after policy applied

### Policy Audit Commands

```fortios
# Show all policies
show firewall policy

# Show specific policy details
get firewall policy 100

# Show policy statistics
diagnose firewall policy list

# Check NAT pool utilization
diagnose firewall ippool list
```

---

## Troubleshooting

| Issue | Cause | Solution |
| --- | --- | --- |
| Traffic blocked unexpectedly | Policy shadowed by earlier rule | Check policy order; review logs |
| Logging not appearing | Syslog server down or unreachable | Check connectivity; verify facility code |
| Performance degradation | DPI profiles consuming CPU | Reduce DPI scope; use hardware acceleration |
| NAT pool exhaustion | Too many concurrent sessions | Increase pool size; use multiple IPs |

---

## Related Standards

- [Security Hardening](security-hardening.md) — Firewall access control, logging
- [Syslog & Monitoring](syslog-monitoring-standards.md) — Policy logging and alerting
- [VLAN Standards](vlan-standards.md) — Source/destination VLAN isolation
