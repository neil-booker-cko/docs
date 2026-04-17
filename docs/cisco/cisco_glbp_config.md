# Cisco GLBP Configuration Guide

Complete reference for configuring Gateway Load Balancing Protocol on Cisco IOS-XE.

## Quick Start: Basic GLBP

```ios
configure terminal

interface GigabitEthernet0/1
  ip address 192.168.1.10 255.255.255.0
  glbp 1 ip 192.168.1.1

end
```

---

## GLBP Configuration Components

### GLBP Interface Configuration

Enable GLBP on an interface and assign virtual IP.

```ios
interface GigabitEthernet0/1
  ! Enable GLBP group 1, virtual IP 192.168.1.1
  glbp 1 ip 192.168.1.1
```

### GLBP Group Number

Groups are numbered 0-1023. Use same group number on all routers in the group.

```ios
interface GigabitEthernet0/1
  glbp 1 ip 192.168.1.1  ! Group 1, VIP 192.168.1.1
  glbp 2 ip 192.168.2.1  ! Group 2, VIP 192.168.2.1
  glbp 3 ip 192.168.3.1  ! Group 3, VIP 192.168.3.1
```

### Priority (AVG Election)

Highest priority router becomes AVG (and primary AVF).

```ios
interface GigabitEthernet0/1
  glbp 1 ip 192.168.1.1
  glbp 1 priority 110  ! Higher number = higher priority
```

### Preemption

Allows higher-priority router to take over if current AVG fails.

```ios
interface GigabitEthernet0/1
  glbp 1 ip 192.168.1.1
  glbp 1 priority 110
  glbp 1 preempt  ! Take over if priority is higher
```

### Timers

Control hello interval and hold time (dead interval).

```ios
interface GigabitEthernet0/1
  glbp 1 ip 192.168.1.1

  ! Default: hello 3 seconds, hold 10 seconds
  glbp 1 timers 3 10

  ! Fast convergence: hello 1 second, hold 4 seconds
  glbp 1 timers 1 4
```

---

## GLBP Load Balancing Configuration

### Host-based Load Balancing (Default)

ARP load balancing: each host gets a different MAC address.

```ios
interface GigabitEthernet0/1
  glbp 1 ip 192.168.1.1
  glbp 1 load-balancing host-dependent  ! Default behavior
```

### Round-robin Load Balancing

Cycle through MAC addresses sequentially.

```ios
interface GigabitEthernet0/1
  glbp 1 ip 192.168.1.1
  glbp 1 load-balancing round-robin  ! Cycle through MACs
```

### Weighted Load Balancing

Assign weight to each forwarder (higher weight = more traffic).

```ios
interface GigabitEthernet0/1
  glbp 1 ip 192.168.1.1

  ! Router A: 70% of traffic
  glbp 1 weighting 70

  ! Enable weighted load balancing
  glbp 1 load-balancing weighted
```

---

## Complete Configuration Example

### Scenario: 4-Router Network with Load Balancing

```text
Virtual IP: 192.168.1.1
Router A (10.0.0.1): AVG, primary AVF, priority 110
Router B (10.0.0.2): Primary AVF 2, priority 100
Router C (10.0.0.3): Primary AVF 3, priority 90
Router D (10.0.0.4): Primary AVF 4, priority 80

Load balancing: Round-robin (equal distribution)
```

**Router A Configuration:**

```ios
configure terminal

interface GigabitEthernet0/1
  ip address 10.0.0.1 255.255.255.0

  ! GLBP group 1
  glbp 1 ip 192.168.1.1
  glbp 1 priority 110  ! Highest priority = AVG
  glbp 1 preempt
  glbp 1 timers 3 10
  glbp 1 load-balancing round-robin

  ! Optional: description
  glbp 1 name "Gateway-Group-1"

end
```

**Router B Configuration:**

```ios
configure terminal

interface GigabitEthernet0/1
  ip address 10.0.0.2 255.255.255.0

  glbp 1 ip 192.168.1.1
  glbp 1 priority 100  ! Lower than Router A
  glbp 1 preempt
  glbp 1 timers 3 10
  glbp 1 load-balancing round-robin

end
```

**Router C & D:** Similar to Router B, with priority 90 and 80 respectively.

---

## Weighted Load Balancing Example

### Scenario: Asymmetric Capacity

```text
Router A: 1 Gbps link, should get 50% traffic
Router B: 100 Mbps link, should get 50% traffic
```

**Router A (1 Gbps):**

```ios
configure terminal

interface GigabitEthernet0/1
  ip address 192.168.1.10 255.255.255.0

  glbp 1 ip 192.168.1.1
  glbp 1 priority 110
  glbp 1 preempt
  glbp 1 weighting 100  ! Full weight (100 Mbps equivalent)
  glbp 1 load-balancing weighted

end
```

**Router B (100 Mbps):**

```ios
configure terminal

interface GigabitEthernet0/1
  ip address 192.168.1.11 255.255.255.0

  glbp 1 ip 192.168.1.1
  glbp 1 priority 100
  glbp 1 preempt
  glbp 1 weighting 100  ! Same weight (100 Mbps equivalent)
  glbp 1 load-balancing weighted

end
```

---

## Verification and Monitoring

### Check GLBP Status

```ios
show glbp

! Output:
! Interface   Group Ver State   Priority   Weighting Timeout Group
! Gi0/1       1     v4  Active  110       100       3       Router A
!                                AVG      Secondary
```

### Detailed GLBP Information

```ios
show glbp 1 detail

! Shows:
! - Group number
! - Virtual IP
! - Priority
! - Timers (hello, hold)
! - Load-balancing method
! - Virtual MAC addresses
! - AVG and AVF status
```

### GLBP Virtual MAC Addresses

```ios
show glbp 1 forwarders

! Output shows:
! State    Pri    MAC Address        Group
! Active   100    0000.0701.0001     Router A
! Active   90     0000.0701.0002     Router B
! Active   80     0000.0701.0003     Router C
! Active   70     0000.0701.0004     Router D
```

### Monitor GLBP Hellos

```ios
debug glbp terse

! Shows GLBP hello exchanges and elections
! Use sparingly on production (generates verbose output)
```

### Check ARP Responses

```ios
show arp 192.168.1.1

! Should show multiple MAC addresses if GLBP is load balancing
```

---

## Common Issues and Fixes

### Issue: All Traffic Goes to One Router

**Cause:** Load balancing not enabled, or host only learned one MAC.

**Check:**

```ios
show glbp 1 detail
! Verify load-balancing method is set

show arp 192.168.1.1
! Check if multiple MACs are in ARP table
```

**Fix:**

```ios
interface GigabitEthernet0/1
  glbp 1 load-balancing round-robin  ! Enable load balancing
  ! Clients must re-ARP to learn new MAC
```

### Issue: Router Keeps Becoming AVG When It Shouldn't

**Cause:** Priority is too high, or preemption is enabled when not desired.

**Check:**

```ios
show glbp 1
! Check priority settings on all routers
```

**Fix:**

```ios
interface GigabitEthernet0/1
  glbp 1 priority 100  ! Lower priority on non-primary router
  ! Consider disabling preemption if not needed
  no glbp 1 preempt
```

### Issue: GLBP Election Keeps Changing (Flapping)

**Cause:** Unstable network, hello/hold timers too aggressive.

**Check:**

```ios
debug glbp terse
! Watch for repeated elections
```

**Fix:**

```ios
interface GigabitEthernet0/1
  ! Use slower timers for stability
  glbp 1 timers 5 15  ! Hello 5s, hold 15s

  ! Check for network issues (flaky interface)
  show interface GigabitEthernet0/1
```

### Issue: Secondary Routers Not Becoming AVF

**Cause:** Only one router configured for GLBP, others not running GLBP.

**Check:**

```ios
show glbp
! Should show status on all routers in the group
```

**Fix:**

Ensure all routers in the group have GLBP configured on the same interface
with the same group number.

---

## Best Practices

| Practice | Reason |
| --- | --- |
| **Use 4 AVFs when possible** | Maximum load balancing benefit |
| **Set staggered priorities** | Clear AVG hierarchy (110, 100, 90, 80) |
| **Enable preemption** | Higher-priority router takes over if recovered |
| **Use round-robin load balancing** | Simplest, most predictable distribution |
| **Test failover regularly** | Verify convergence time is acceptable |
| **Monitor AVG elections** | Flapping indicates instability |
| **Use consistent timers** | All routers in group should match |
| **Enable GLBP authentication (optional)** | Prevent rogue routers from joining |
| **Document group topology** | Multiple groups can be complex |
| **Match priorities to roles** | Primary higher than secondary |

---

## Configuration Checklist

- [ ] Enable GLBP on all routers on same interface
- [ ] Assign same group number on all routers
- [ ] Assign same virtual IP on all routers
- [ ] Set priorities (primary higher than secondary)
- [ ] Enable preemption on primary
- [ ] Configure timers consistently
- [ ] Choose load-balancing method (round-robin recommended)
- [ ] Verify with `show glbp 1 detail`
- [ ] Test failover by shutting down primary
- [ ] Monitor ARP to verify multiple MACs
- [ ] Document GLBP topology and priorities
- [ ] Verify hosts learn multiple MACs for VIP

---

## Quick Reference

```ios
! Basic GLBP configuration
interface GigabitEthernet0/1
  glbp 1 ip 192.168.1.1
  glbp 1 priority 110
  glbp 1 preempt
  glbp 1 timers 3 10
  glbp 1 load-balancing round-robin

! Enable authentication (optional)
interface GigabitEthernet0/1
  glbp 1 authentication md5 key-string MySecureKey123

! Verify configuration
show glbp 1 detail
show glbp 1 forwarders
show arp 192.168.1.1

! Debug GLBP (use cautiously)
debug glbp terse
undebug all
```
