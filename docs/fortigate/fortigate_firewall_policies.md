# FortiGate Firewall Policies Guide

Complete reference for configuring firewall policies (access control) on Fortinet
FortiGate.

## Overview

FortiGate uses **firewall policies** to control traffic flow between interfaces. Unlike
traditional ACLs (which work on a single device), firewall policies define
**source→destination→action rules** for bidirectional security.

### Policy vs ACL

| Aspect | Firewall Policy | Traditional ACL |
| --- | --------- | --- |
| **Scope** | Bidirectional (in/out) | Unidirectional (inbound) |
| **Inspection** | Deep packet inspection (DPI) | Basic IP/port matching |
| **Actions** | Allow, Deny, with logging | Allow, Deny only |
| **Where** | Between interfaces | On specific interface |
| **Use** | Security zones, inter-zone traffic | Interface-level filtering |

---

## Firewall Policy Fundamentals

### Policy Flow

When a packet arrives:

```text
1. Packet enters ingress interface
2. FortiGate looks up matching policy
3. Policy specifies: source zone, dest zone, services, action
4. If allowed: inspect & forward
5. If denied: drop (optionally log)
6. Send out egress interface
```

### Key Components

Every firewall policy has:

| Component | Example | Meaning |
| --- | --------- | --- |
| **Source Zone** | Internal | Where traffic originates |
| **Destination Zone** | External | Where traffic is destined |
| **Source Address** | 10.0.0.0/24 | Source IP subnet |
| **Destination Address** | 0.0.0.0/0 (any) | Destination IP subnet |
| **Service** | HTTP, HTTPS, SSH | Protocol + Port |
| **Action** | Accept, Deny | Allow or block |

---

## Zones Configuration

Zones logically group interfaces. Traffic flows between zones via policies.

### Create a Zone

```text

config system zone
  edit "Internal"
    set description "Internal LAN"
    ! Add interfaces to zone
    set interface "vlan100"
    set interface "vlan101"
  next

  edit "External"
    set description "Internet/WAN"
    set interface "port1"
  next
end
```

### Built-in Zones

| Zone | Purpose | Typical Interfaces |
| --- | --------- | --- |
| **Internal** | Internal networks | LAN VLANs, local subnets |
| **External** | Untrusted networks | Internet ISP links |
| **DMZ** | Demilitarized zone | Public-facing servers |
| **Management** | Admin access only | Out-of-band management |

---

## Firewall Policy Creation

### Basic Policy: Allow Internal to External

```text

config firewall policy
  edit 1
    ! Ingress interface zone
    set srcintf "Internal"

    ! Egress interface zone
    set dstintf "External"

    ! Source address (who)
    set srcaddr "Internal-Subnet"

    ! Destination address (where)
    set dstaddr "any"

    ! Allowed service (what)
    set service "HTTP" "HTTPS" "DNS"

    ! Action: accept or deny
    set action accept

    ! Enable logging
    set logtraffic enable

    ! Optional: traffic shaping
    set utm-status enable
  next
end
```

### Policy with Multiple Services

```text

config firewall policy
  edit 2
    set srcintf "Internal"
    set dstintf "External"
    set srcaddr "Branch-LAN"
    set dstaddr "any"

    ! Multiple services
    set service "HTTP"
    set service "HTTPS"
    set service "DNS"
    set service "SSH"

    set action accept
  next
end
```

---

## Address Objects

Pre-define IP addresses/subnets for reuse in policies.

### Create Address Object

```text

config firewall address
  edit "Internal-Subnet"
    set comment "Branch LAN"
    set subnet 10.0.0.0 255.255.255.0
  next

  edit "HQ-Network"
    set comment "HQ LAN"
    set subnet 10.1.0.0 255.255.0.0
  next

  edit "DNS-Server"
    set comment "ISP DNS"
    set subnet 8.8.8.8 255.255.255.255
  next
end
```

### Address Groups

Group multiple addresses for easier management.

```text

config firewall addrgrp
  edit "Internal-Networks"
    set member "Internal-Subnet"
    set member "HQ-Network"
  next
end

! Use in policy
config firewall policy
  edit 3
    set srcaddr "Internal-Networks"
    set dstaddr "any"
    set action accept
  next
end
```

---

## Service Objects

Pre-define ports/protocols for reuse.

### Built-in Services

FortiGate includes pre-defined services: HTTP, HTTPS, SSH, DNS, NTP, SNMP, etc.

### Create Custom Service

```text

config firewall service custom
  edit "App-Server-8080"
    set protocol TCP
    set tcp-portrange 8080
  next

  edit "App-Range"
    set protocol TCP
    set tcp-portrange 8000-8100
  next

  edit "Syslog-Service"
    set protocol UDP
    set udp-portrange 514
  next
end

! Use in policy
config firewall policy
  edit 4
    set service "App-Server-8080" "Syslog-Service"
  next
end
```

---

## Complete Configuration Example

### Scenario: Branch FortiGate with Internal & External Zones

```text

Internal Zone (vlan100: 10.0.0.0/24)
   |
   └─ Firewall Policy
        |
        └─ External Zone (port1: ISP link)
```

**Complete Configuration:**

```text

! === Zones ===
config system zone
  edit "Internal"
    set description "Branch LAN"
    set interface "vlan100"
  next

  edit "External"
    set description "ISP Uplink"
    set interface "port1"
  next

  edit "Management"
    set description "Out-of-band access"
    set interface "mgmt"
  next
end

! === Address Objects ===
config firewall address
  edit "Branch-LAN"
    set comment "Branch users"
    set subnet 10.0.0.0 255.255.255.0
  next

  edit "HQ-Network"
    set comment "HQ office"
    set subnet 10.1.0.0 255.255.0.0
  next

  edit "DNS-ISP"
    set comment "ISP DNS resolvers"
    set subnet 8.8.8.8 255.255.255.255
  next
end

! === Service Objects ===
config firewall service custom
  edit "App-Server"
    set protocol TCP
    set tcp-portrange 443 8080
  next
end

! === Policies ===
config firewall policy
  ! Policy 1: Branch users to internet
  edit 1
    set name "Branch-to-Internet"
    set srcintf "Internal"
    set dstintf "External"
    set srcaddr "Branch-LAN"
    set dstaddr "any"
    set service "HTTP" "HTTPS" "DNS"
    set action accept
    set logtraffic enable
    set schedule "always"
  next

  ! Policy 2: Branch to HQ (site-to-site)
  edit 2
    set name "Branch-to-HQ"
    set srcintf "Internal"
    set dstintf "site-to-site"  ! Another interface or zone
    set srcaddr "Branch-LAN"
    set dstaddr "HQ-Network"
    set service "any"
    set action accept
    set logtraffic enable
  next

  ! Policy 3: Management access (restrictive)
  edit 3
    set name "Management-Access"
    set srcintf "Internal"
    set dstintf "External"
    set srcaddr "Admin-Workstation"
    set dstaddr "any"
    set service "SSH" "HTTPS"
    set action accept
    set logtraffic enable
    set schedule "business-hours"
  next

  ! Policy 4: Deny everything else (implicit deny at end)
  edit 4
    set name "Deny-All"
    set srcintf "any"
    set dstintf "any"
    set srcaddr "any"
    set dstaddr "any"
    set service "any"
    set action deny
    set logtraffic enable
  next
end
```

---

## Policy Priority and Ordering

Policies are evaluated **top-to-bottom**. First matching policy wins.

```text

Policy 1: Allow Branch-LAN to DNS servers (port 53)
   ↓ (checked first)

Policy 2: Allow Branch-LAN to anywhere on HTTP/HTTPS
   ↓ (checked if Policy 1 didn't match)

Policy 3: Deny all traffic
   ↓ (checked if no match above; implicit)
```

**Result:** DNS traffic matches Policy 1 → allowed
**Result:** HTTP traffic doesn't match Policy 1, matches Policy 2 → allowed
**Result:** SSH traffic doesn't match Policies 1-2, matches Policy 3 → denied

### Reorder Policies

```text

! Move policy to different position
config firewall policy
  move 3 before 1  ! Move policy 3 to be first
end
```

---

## Verification and Monitoring

### Check Policies

```text

get firewall policy

! Lists all policies with source, destination, service, action
```

### Check Policy Details

```text

get firewall policy 1

! Shows detailed configuration of policy 1
```

### Monitor Policy Hits

```text

get firewall policy summary

! Shows traffic statistics per policy
! Look for "hit count" and "bytes" to see which policies are actually used
```

### View Policy in Specific Zone

```text

show firewall policy filter dstintf External

! Shows all policies where destination interface is External
```

### Check Address/Service Objects

```text

get firewall address
get firewall service custom
get firewall addrgrp
```

### View Implicit Deny

```text

diagnose debug flow trace start 100

! Trace traffic matching and allow/deny decisions
diagnose debug flow trace stop
```

---

## Common Issues and Fixes

### Issue: Traffic Blocked Despite Policy

**Cause:** Policy doesn't match (wrong source/dest/service), or implicit deny hit.

**Troubleshoot:**

```text

! 1. Check if policy exists and matches
get firewall policy | grep -A 10 "source-address"

! 2. Verify address/service objects exist
get firewall address <address-name>
get firewall service custom <service-name>

! 3. Check policy ordering
get firewall policy
! Are more-specific policies before general ones?

! 4. Debug traffic flow
diagnose debug flow trace start 100
! Then send test traffic
! Traffic matching is logged
```

**Fix:**

```text

! Add missing policy
config firewall policy
  edit 5
    set srcintf "Internal"
    set dstintf "External"
    set srcaddr "Branch-LAN"
    set dstaddr "Server"
    set service "MyService"
    set action accept
  next
end
```

### Issue: All Internet Traffic Blocked

**Cause:** "Deny all" policy placed too early, or no allow policy for internet.

**Check:**

```text

get firewall policy

! Look for order of policies; "deny all" should be last
```

**Fix:** Reorder or add allow policy

```text

config firewall policy
  move <deny-policy-id> after <allow-policy-id>

  ! Or add internet allow policy
  edit 100
    set srcintf "Internal"
    set dstintf "External"
    set srcaddr "any"
    set dstaddr "any"
    set service "HTTP" "HTTPS" "DNS"
    set action accept
  next
end
```

### Issue: Logging Not Working

**Cause:** `logtraffic` not enabled on policy, or disk full.

**Check:**

```text

get firewall policy 1 | grep logtraffic

! Should show: set logtraffic enable
```

**Fix:**

```text

config firewall policy
  edit 1
    set logtraffic enable
  next
end
```

### Issue: Too Many Policies; Hard to Manage

**Solution:** Use address groups and service groups

```text

! Instead of 50 policies, group similar sources/destinations
config firewall addrgrp
  edit "Internal-Subnets"
    set member "Branch-LAN"
    set member "HQ-Network"
  next
end

config firewall service group
  edit "Web-Services"
    set member "HTTP"
    set member "HTTPS"
  next
end

! Use groups in single policy
config firewall policy
  edit 1
    set srcaddr "Internal-Subnets"
    set dstaddr "any"
    set service "Web-Services"
    set action accept
  next
end
```

---

## Best Practices

| Practice | Reason |
| --- | --------- |
| Use address/service objects | Reusability, consistency |
| Order policies: specific → general | Prevent general rules from matching before specific |
| Place "deny all" at end | Fail-safe default |
| Enable logging on important policies | Track what's being blocked |
| Name policies descriptively | Easier to understand and troubleshoot |
| Use zones for logical grouping | Scales better than per-interface rules |
| Review policies regularly | Remove unused rules, update for business changes |
| Test policies in pre-prod | Catch mistakes before production |
| Document policy intent | Facilitate future changes |
| Use "schedule" for time-based access | Restrict access to business hours if needed |

---

## Configuration Checklist

- [ ] Create zones (Internal, External, etc.)
- [ ] Define address objects for subnets
- [ ] Define service objects for custom ports
- [ ] Create allow policies for required traffic
- [ ] Order policies: specific first, deny-all last
- [ ] Enable logging on critical policies
- [ ] Test connectivity for allowed traffic
- [ ] Verify blocked traffic is actually blocked
- [ ] Monitor policy hit counts (`get firewall policy summary`)
- [ ] Document policy intent and schedule

---

## Quick Reference

```text

! Create zone
config system zone
  edit "Internal"
    set interface "vlan100"
  next
end

! Create address object
config firewall address
  edit "LAN-Subnet"
    set subnet 10.0.0.0 255.255.255.0
  next
end

! Create policy
config firewall policy
  edit 1
    set srcintf "Internal"
    set dstintf "External"
    set srcaddr "LAN-Subnet"
    set dstaddr "any"
    set service "HTTP" "HTTPS"
    set action accept
    set logtraffic enable
  next
end

! Verify
get firewall policy
get firewall policy summary
get firewall address
```
