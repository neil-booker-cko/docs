# Cisco IOS-XE Policy-Based Routing Configuration Guide

Complete reference for implementing policy-based routing on Cisco IOS-XE.

## Quick Start: Basic PBR

```ios
configure terminal

! === Route map for PBR policy ===
route-map PBR-POLICY permit 10
  match ip address 101
  set ip next-hop 192.168.1.254

! === ACL defining traffic to match ===
access-list 101 permit ip 10.0.0.0 0.0.0.255 any

! === Apply PBR to interface ===
interface GigabitEthernet0/1
  ip policy route-map PBR-POLICY

end
```

---

## Policy-Based Routing Components

### 1. Access Control List (ACL)

Defines which traffic to match.

```ios

! Match traffic from specific source
access-list 101 permit ip 10.0.0.0 0.0.0.255 any

! Match traffic with specific protocol and port
access-list 102 permit tcp any any eq 443   ! HTTPS

! Match traffic to specific destination
access-list 103 permit ip any 192.168.0.0 0.0.0.255

! Combine multiple ACL numbers in route-map
```

### 2. Route Map

Matches traffic and applies actions.

```ios

route-map PBR-POLICY permit 10
  ! Match traffic defined in ACL 101
  match ip address 101
  ! Route via this next-hop
  set ip next-hop 192.168.1.254

route-map PBR-POLICY permit 20
  match ip address 102
  set ip next-hop 200.1.1.1  ! Different next-hop

route-map PBR-POLICY deny 30
  ! Deny everything else (optional)
```

### 3. Interface Application

Apply route-map to ingress interface.

```ios

interface GigabitEthernet0/1
  ! Apply PBR to incoming traffic
  ip policy route-map PBR-POLICY
```

---

## Matching Criteria

### Match by Source IP

```ios

access-list 101 permit ip 10.0.0.0 0.0.0.255 any
route-map PBR-POLICY permit 10
  match ip address 101
  set ip next-hop 192.168.1.254
```

### Match by Destination IP

```ios

access-list 102 permit ip any 192.168.0.0 0.0.0.255
route-map PBR-POLICY permit 20
  match ip address 102
  set ip next-hop 200.1.1.1
```

### Match by Protocol and Port

```ios

! TCP port 443 (HTTPS)
access-list 103 permit tcp any any eq 443

! TCP port 22 (SSH)
access-list 104 permit tcp any any eq 22

! UDP port 53 (DNS)
access-list 105 permit udp any any eq 53
```

### Match by DSCP

```ios

! Match voice traffic (DSCP EF)
route-map PBR-POLICY permit 10
  match ip dscp ef
  set ip next-hop 192.168.1.254  ! High-quality ISP
```

### Match by Interface

```ios

route-map PBR-POLICY permit 10
  match interface GigabitEthernet0/1  ! Traffic from this interface
  set ip next-hop 192.168.1.254
```

---

## Set Actions

### Set Next-hop

```ios

route-map PBR-POLICY permit 10
  set ip next-hop 192.168.1.254  ! Route via this gateway
```

### Set Outgoing Interface

```ios

route-map PBR-POLICY permit 10
  set ip next-hop 200.1.1.1
  set interface GigabitEthernet0/2  ! Send out this interface
```

### Set DSCP (QoS Marking)

```ios

route-map PBR-POLICY permit 10
  match ip address 101  ! Voice traffic
  set ip dscp ef  ! Mark as expedited forwarding
  set ip next-hop 192.168.1.254
```

### Multiple Next-hops (Load Balancing)

```ios

route-map PBR-POLICY permit 10
  match ip address 101
  set ip next-hop 192.168.1.1 192.168.1.2 192.168.1.3
  ! Traffic distributed across all three next-hops
```

---

## Complete Configuration Example

### Scenario: Multi-ISP Load Balancing

```text

Internal network: 10.0.0.0/24

ISP-1: 200.1.1.0/24 (gateway 200.1.1.1)
ISP-2: 200.2.1.0/24 (gateway 200.2.1.1)

Requirement:

  - Subnet 10.0.1.0/25 → ISP-1
  - Subnet 10.0.1.128/25 → ISP-2
  - VoIP traffic → ISP-1 (quality)
```

**Configuration:**

```ios

configure terminal

! === ACL for subnet 1 ===
access-list 101 permit ip 10.0.1.0 0.0.0.127 any

! === ACL for subnet 2 ===
access-list 102 permit ip 10.0.1.128 0.0.0.127 any

! === ACL for VoIP ===
access-list 103 permit tcp any any eq 5060  ! SIP
access-list 103 permit udp any any range 10000 11000  ! RTP

! === Route Map: subnet 1 → ISP-1 ===
route-map PBR-LOAD-BALANCE permit 10
  match ip address 101
  set ip next-hop 200.1.1.1
  set ip dscp default

! === Route Map: subnet 2 → ISP-2 ===
route-map PBR-LOAD-BALANCE permit 20
  match ip address 102
  set ip next-hop 200.2.1.1

! === Route Map: VoIP → ISP-1 (high priority) ===
route-map PBR-LOAD-BALANCE permit 5
  match ip address 103
  set ip next-hop 200.1.1.1
  set ip dscp ef
  ! Note: permit 5 is earlier, so evaluated first

! === Route Map: Default (normal routing) ===
route-map PBR-LOAD-BALANCE permit 30
  ! If no match, fall through to normal routing
  ! (implicit; no action needed)

! === Apply PBR to ingress interface ===
interface Vlan100
  description "Internal LAN"
  ip address 10.0.0.1 255.255.255.0
  ip policy route-map PBR-LOAD-BALANCE

! === Verify ===
! show route-map PBR-LOAD-BALANCE
! show access-lists

end
```

---

## Verification and Monitoring

### Check Route Map

```ios

show route-map PBR-LOAD-BALANCE

! Output:
! route-map PBR-LOAD-BALANCE, permit, sequence 5
!   Match clauses:
!     ip address (access lists): 103
!   Set clauses:
!     ip next-hop 200.1.1.1
!     ip dscp ef
!   Policy routing matches: 42 packets, 3500 bytes
```

### Check Policy Routing Hit Counts

```ios

show route-map
! Shows "Policy routing matches" count for each policy

show ip policy
! Shows which route-map is applied to which interface
```

### Debug PBR Decisions

```ios

debug ip policy
! Shows real-time PBR processing

! Send test traffic, watch debug output
! Example: ping from 10.0.1.5 to 8.8.8.8
! Debug output: "Policy routing matched for 10.0.1.5"

undebug all  ! Stop debugging
```

### Verify Traffic Takes Correct Path

```ios

traceroute 8.8.8.8
! Should show ISP-1 as next-hop (200.1.1.1)
```

---

## Common Issues and Fixes

### Issue: PBR Not Being Applied

**Cause:** Route-map not applied to interface, or ACL empty.

**Check:**

```ios

show ip policy

! Should show interface with route-map applied
! Example: interface Vlan100: route map PBR-LOAD-BALANCE
```

**Fix:**

```ios

configure terminal

interface Vlan100
  ip policy route-map PBR-LOAD-BALANCE

end
```

### Issue: Traffic Taking Wrong Path

**Cause:** ACL match is too broad, or route-map order incorrect.

**Check:**

```ios

show access-lists 101

! Verify source IPs actually match intended subnets
! Example: 10.0.1.0 0.0.0.127 matches 10.0.1.0 - 10.0.1.127

show route-map PBR-LOAD-BALANCE

! Verify permit order (lower numbers evaluated first)
```

**Fix:** Adjust ACL or reorder route-map permits.

```ios

configure terminal

no access-list 101
access-list 101 permit ip 10.0.1.0 0.0.0.127 any

! Or reorder route-map (delete and recreate)

end
```

### Issue: Asymmetric Routing (Return Traffic Takes Different Path)

**Cause:** Return path doesn't match PBR; takes default route.

```text

Outbound (internal → external):
  PBR routes via ISP-1

Return (external → internal):
  External routers send back to default route
  Default might be ISP-2

Result: Packet loss, asymmetric routing warning
```

**Solution:** Ensure return traffic matches same ISP or use BGP.

```ios

! Option 1: Add reverse PBR policy
access-list 104 permit ip any 10.0.1.0 0.0.0.127
route-map PBR-LOAD-BALANCE permit 40
  match ip address 104
  set ip next-hop 200.1.1.1  ! Same ISP

! Option 2: Use BGP for dynamic routing (better for asymmetric)
```

### Issue: Next-hop Unreachable (Route via unreachable gateway)

**Cause:** Specified next-hop is down or not reachable.

**Check:**

```ios

ping 200.1.1.1
! Verify next-hop is reachable

show ip route 200.1.1.1
! Verify route to next-hop exists
```

**Fix:** Add backup next-hop or health check.

```ios

route-map PBR-LOAD-BALANCE permit 10
  match ip address 101
  set ip next-hop 200.1.1.1 200.1.1.2 200.1.1.3
  ! Multiple next-hops; use first reachable
```

---

## Best Practices

| Practice | Reason |
| --- | --------- |
| **Use for small networks** | Scales better with BGP beyond 10 sites |
| **Document ACLs and route-maps** | Facilitate troubleshooting |
| **Test before production** | Verify return traffic works |
| **Add backup next-hops** | Failover if primary is down |
| **Monitor hit counts** | Verify policies are actually used |
| **Order route-map by specificity** | Most-specific rules first |
| **Enable logging** | `set logging` to track PBR decisions |
| **Use with health checks** | Automatic failover on link failure |
| **Combine with BGP** | BGP for scalability; PBR for specific policies |

---

## Configuration Checklist

- [ ] Design which traffic needs PBR
- [ ] Create ACLs for traffic matching
- [ ] Create route-map with match/set clauses
- [ ] Order route-map by specificity (lowest = highest priority)
- [ ] Apply route-map to ingress interface
- [ ] Verify route-map is applied (`show ip policy`)
- [ ] Test with actual traffic (ping, traceroute)
- [ ] Verify return traffic works (no asymmetry)
- [ ] Monitor hit counts (`show route-map`)
- [ ] Add backup next-hops for failover
- [ ] Document for future changes

---

## Quick Reference

```ios

! Create ACL
access-list 101 permit ip 10.0.0.0 0.0.0.255 any

! Create route-map
route-map PBR-POLICY permit 10
  match ip address 101
  set ip next-hop 192.168.1.254

! Apply to interface
interface Vlan100
  ip policy route-map PBR-POLICY

! Verify
show ip policy
show route-map PBR-POLICY
show access-lists 101
```
