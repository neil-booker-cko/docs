# FortiGate QoS Configuration Guide

Complete reference for configuring Quality of Service on Fortinet FortiGate.

## Quick Start: Enable Basic QoS

```text
config firewall policy
  edit 1
    set name "Web-Traffic-QoS"
    set srcintf "port1"
    set dstintf "port2"
    set srcaddr "Internal-Subnet"
    set dstaddr "any"
    set service "HTTP" "HTTPS"

    ! Apply QoS
    set traffic-shaper "qos-shape-1mbps"
    set traffic-shaper-reverse "qos-shape-2mbps"
  next
end
```

---

## QoS Overview

**Quality of Service (QoS)** prioritizes or limits bandwidth for different types of traffic.

### Why QoS?

```text

Scenario: 100 Mbps link shared by 100 users

Without QoS:
  Video streaming uses 50 Mbps
  VoIP gets 0.1 Mbps → poor quality
  Result: Voice quality degraded

With QoS:
  VoIP priority: guarantees 2 Mbps
  Video allowed: up to 40 Mbps
  Other: up to 58 Mbps
  Result: All services work with acceptable quality
```

### QoS vs Traffic Shaping

| Aspect | QoS/Prioritization | Traffic Shaping/Rate Limiting |
| --- | --------- | --- |
| **Goal** | Prioritize important traffic | Limit bandwidth per flow |
| **Method** | Queue management; serve priority first | Buffer excess; limit rate |
| **Use Case** | Ensure VoIP/video quality | Prevent one user monopolizing link |
| **Impact** | Improves performance of priority traffic | May delay non-priority traffic |

---

## Traffic Shaper Configuration

### Create a Traffic Shaper (Rate Limiter)

```text

config firewall traffic-shaper
  edit "qos-limit-10mbps"
    set guaranteed-bandwidth 10  ! Mbps
    set maximum-bandwidth 10     ! Hard limit
  next

  edit "qos-limit-5mbps"
    set guaranteed-bandwidth 5
    set maximum-bandwidth 5
  next
end
```

### Apply Shaper to Policy

```text

config firewall policy
  edit 1
    set srcintf "port1"
    set dstintf "port2"
    set srcaddr "10.0.0.0/24"
    set dstaddr "any"
    set service "any"

    ! Apply shaper: limit to 10 Mbps
    set traffic-shaper "qos-limit-10mbps"

    ! Optional: different rate for return traffic
    set traffic-shaper-reverse "qos-limit-5mbps"
  next
end
```

---

## Traffic Prioritization (Class-Based QoS)

### Create QoS Classes

```text

config firewall traffic-shaper
  edit "voice-priority"
    set priority high
    set guaranteed-bandwidth 5   ! Reserve 5 Mbps for VoIP
    set maximum-bandwidth 10     ! Allow up to 10 if available
  next

  edit "video-medium"
    set priority medium
    set guaranteed-bandwidth 20
    set maximum-bandwidth 50
  next

  edit "data-low"
    set priority low
    set guaranteed-bandwidth 5
    set maximum-bandwidth 100
  next
end
```

### Assign Traffic to Classes

By Service:

```text

config firewall policy
  edit 1
    set name "VoIP-Priority"
    set srcintf "port1"
    set dstintf "port2"
    set service "SIP" "RTP"
    set traffic-shaper "voice-priority"
  next

  edit 2
    set name "Video-Medium"
    set srcintf "port1"
    set dstintf "port2"
    set service "youtube" "netflix" "Teams"
    set traffic-shaper "video-medium"
  next

  edit 3
    set name "Data-Low"
    set srcintf "port1"
    set dstintf "port2"
    set service "HTTP" "HTTPS" "DNS"
    set traffic-shaper "data-low"
  next
end
```

By Source IP:

```text

config firewall policy
  edit 1
    set srcaddr "10.0.0.0/24"      ! Accounting department
    set traffic-shaper "data-low"  ! Low priority
  next

  edit 2
    set srcaddr "10.1.0.0/24"      ! VoIP endpoints
    set traffic-shaper "voice-priority"  ! High priority
  next
end
```

---

## DSCP Marking and QoS

### Mark Traffic with DSCP Value

```text

config firewall policy
  edit 1
    set srcintf "port1"
    set dstintf "port2"
    set service "SIP"

    ! Mark outgoing traffic with DSCP value
    ! Voice (EF = 46, 0xBA): 101110 in binary
    set dscp-forward enable
    set dscp-forward-value "EF"  ! or numeric: 46

    ! Mark return traffic
    set dscp-reverse enable
    set dscp-reverse-value "EF"
  next
end
```

### DSCP Values Reference

| Class | DSCP Name | Value | Use Case |
| --- | --------- | --- | --------- |
| **Voice** | EF (Expedited Forwarding) | 46 | VoIP, real-time |
| **Video** | AF4x (Assured Forwarding) | 36, 40, 44 | Video, streaming |
| **Important Data** | AF3x | 26, 30, 34 | Critical services |
| **General Data** | AF2x, AF1x | 10–18, 20–26 | Normal traffic |
| **Best Effort** | CS0 (Default) | 0 | Bulk transfers |

---

## Queue Management

### Queue Scheduling Algorithms

```text

config system traffic-shaper
  ! CoDel (Controlled Delay) — recommended for modern networks
  ! CODEL uses: drop packets at tail if delay exceeds threshold

  ! FIFO (First-In-First-Out) — simple, no prioritization
  ! Serves packets in arrival order

  ! Priority Queue — serve high-priority before low
  ! High-priority packets skip ahead in queue
end
```

### Configure Queue Algorithm per Shaper

```text

config firewall traffic-shaper
  edit "voice-priority"
    set per-policy enable
    set scheduler "codel"  ! Use CoDel algorithm
    set diffserv F   ! Mark DSCP = 46 (EF)
  next

  edit "data-low"
    set per-policy enable
    set scheduler "fifo"   ! Simple FIFO for less critical traffic
  next
end
```

---

## Complete Configuration Example

### Scenario: Branch Office QoS Policy

```text

Branch has: 10 Mbps internet link
Traffic types:

  - VoIP: needs minimum 2 Mbps guaranteed
  - Video conferencing: 3–5 Mbps
  - Web browsing: flexible
  - Backups: lowest priority

Goal: Ensure VoIP works; limit video; allow web/backups at lower priority
```

**FortiGate Configuration:**

```text

! === Traffic Shapers ===
config firewall traffic-shaper
  edit "voice-guaranteed"
    set guaranteed-bandwidth 2    ! Reserve 2 Mbps
    set maximum-bandwidth 5       ! Allow up to 5 if available
    set priority high
    set diffserv EF
  next

  edit "video-medium"
    set guaranteed-bandwidth 3
    set maximum-bandwidth 8
    set priority medium
    set diffserv AF41
  next

  edit "web-browse"
    set guaranteed-bandwidth 1
    set maximum-bandwidth 10
    set priority medium
    set diffserv CS0
  next

  edit "backup-low"
    set guaranteed-bandwidth 0.5
    set maximum-bandwidth 10
    set priority low
    set diffserv CS1
  next
end

! === Firewall Policies with QoS ===
config firewall policy
  ! Policy 1: VoIP (highest priority)
  edit 1
    set name "VoIP-Priority"
    set srcintf "vlan100"
    set dstintf "port1"
    set srcaddr "10.0.0.0/24"
    set dstaddr "any"
    set service "SIP" "RTP" "H323"
    set action accept
    set traffic-shaper "voice-guaranteed"
    set traffic-shaper-reverse "voice-guaranteed"
    set logtraffic enable
  next

  ! Policy 2: Video conferencing
  edit 2
    set name "Video-Conference"
    set srcintf "vlan100"
    set dstintf "port1"
    set srcaddr "10.0.0.0/24"
    set dstaddr "any"
    set service "Teams" "Zoom" "WebEx" "YouTube" "NetFlix"
    set action accept
    set traffic-shaper "video-medium"
    set traffic-shaper-reverse "video-medium"
  next

  ! Policy 3: Web browsing
  edit 3
    set name "Web-Browsing"
    set srcintf "vlan100"
    set dstintf "port1"
    set srcaddr "10.0.0.0/24"
    set dstaddr "any"
    set service "HTTP" "HTTPS" "DNS"
    set action accept
    set traffic-shaper "web-browse"
    set traffic-shaper-reverse "web-browse"
  next

  ! Policy 4: Backup traffic (lowest priority)
  edit 4
    set name "Backup-Traffic"
    set srcintf "vlan100"
    set dstintf "port1"
    set srcaddr "10.0.0.0/24"
    set dstaddr "10.1.0.0/16"    ! Backup server subnet
    set service "HTTPS"
    set action accept
    set traffic-shaper "backup-low"
  next

  ! Policy 5: Deny everything else (implicit deny)
  edit 5
    set name "Default-Deny"
    set srcintf "vlan100"
    set dstintf "port1"
    set srcaddr "any"
    set dstaddr "any"
    set service "any"
    set action deny
    set logtraffic enable
  next
end
```

---

## Verification and Monitoring

### Check Traffic Shaper Status

```text

get firewall traffic-shaper

! Shows all configured shapers and their settings
```

### Monitor QoS Counters

```text

diagnose firewall shaper list

! Shows traffic statistics per shaper:
! - bytes/packets forwarded
! - bytes/packets dropped
! - average bandwidth used
```

### Check Policy QoS Configuration

```text

get firewall policy

! Shows which policies have traffic-shaper applied
```

### Real-Time Traffic Monitoring

```text

diagnose firewall shaper top

! Shows real-time bandwidth usage per shaper
! Sorted by current bandwidth consumption
```

### Debug QoS Processing

```text

diagnose debug flow filter addr 10.0.0.5
diagnose debug flow trace start 100

! Sends test traffic, shows which QoS class is applied
diagnose debug flow trace stop
```

---

## Common Issues and Fixes

### Issue: QoS Not Being Applied

**Cause:** Policy not selected for shaping, or shaper not created.

**Check:**

```text

get firewall policy | grep traffic-shaper

! Verify traffic-shaper is set on policy
```

**Fix:**

```text

config firewall policy
  edit 1
    set traffic-shaper "voice-priority"
  next
end
```

### Issue: Traffic Shaped Incorrectly (Too Limited)

**Cause:** Shaper bandwidth set too low; multiple policies sharing same shaper.

**Check:**

```text

get firewall traffic-shaper

! Verify guaranteed-bandwidth and maximum-bandwidth are appropriate

diagnose firewall shaper top

! Check actual bandwidth being used vs configured limits
```

**Fix:**

```text

config firewall traffic-shaper
  edit "voice-priority"
    set maximum-bandwidth 10  ! Increase limit
  next
end
```

### Issue: Low-Priority Traffic Starving

**Cause:** High-priority traffic consuming all bandwidth; low-priority never gets access.

**Check:**

```text

diagnose firewall shaper top

! If high-priority using 100%, low-priority shows 0%
```

**Solution:** Reduce guaranteed-bandwidth for high-priority or add hard maximum.

```text

config firewall traffic-shaper
  edit "voice-priority"
    set maximum-bandwidth 5  ! Hard limit to 5 Mbps, not 10
  next
end
```

### Issue: No DSCP Marking on Outgoing Traffic

**Cause:** `dscp-forward enable` not set on policy.

**Check:**

```text

get firewall policy 1 | grep dscp

! Should show: set dscp-forward enable
!             set dscp-forward-value "EF"
```

**Fix:**

```text

config firewall policy
  edit 1
    set dscp-forward enable
    set dscp-forward-value "EF"
  next
end
```

---

## Best Practices

| Practice | Reason |
| --- | --------- |
| **Guarantee bandwidth for critical services** | Ensures VoIP/video work even under load |
| **Use priorities, not just limits** | Allows flexible use of available bandwidth |
| **Enable DSCP marking** | Downstream routers can prioritize correctly |
| **Monitor shaper stats** | Detect when classes are over-subscribed |
| **Test QoS before production** | Verify traffic is actually shaped as intended |
| **Document shaper configuration** | Facilitate future changes |
| **Use per-service policies** | Easier to manage and troubleshoot |
| **Review QoS monthly** | Adjust as traffic patterns change |
| **Avoid over-subscribing** | Don't guarantee 100%+ of link capacity |

---

## Configuration Checklist

- [ ] Identify traffic classes (VoIP, video, data, backup)
- [ ] Create traffic shapers for each class
- [ ] Set appropriate guaranteed and maximum bandwidth
- [ ] Create firewall policies per traffic class
- [ ] Assign shapers to policies
- [ ] Enable DSCP marking for important traffic
- [ ] Verify policies are evaluated in correct order
- [ ] Test with actual traffic (ping, video call, download)
- [ ] Monitor shaper statistics
- [ ] Adjust bandwidth as needed
- [ ] Document configuration

---

## Quick Reference

```text

! Create traffic shaper
config firewall traffic-shaper
  edit "voice-priority"
    set guaranteed-bandwidth 2
    set maximum-bandwidth 5
    set priority high
    set diffserv EF
  next
end

! Apply to policy
config firewall policy
  edit 1
    set traffic-shaper "voice-priority"
    set traffic-shaper-reverse "voice-priority"
    set dscp-forward enable
    set dscp-forward-value "EF"
  next
end

! Verify
get firewall traffic-shaper
diagnose firewall shaper top
get firewall policy
```
