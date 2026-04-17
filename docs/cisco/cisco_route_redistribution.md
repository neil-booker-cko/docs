# Cisco IOS-XE Route Redistribution Configuration Guide

Complete reference for redistributing routes between routing protocols on Cisco IOS-XE.

## Quick Start: Basic Redistribution

```ios
configure terminal

! Redistribute OSPF into EIGRP
router eigrp 100
  redistribute ospf 1 metric 1000000 100 255 1 1500
end
```

---

## Redistribution Components

### Source Protocol (Learned Routes)

Routes from this protocol will be imported into destination protocol.

```ios

router eigrp 100
  ! Import routes from OSPF process 1
  redistribute ospf 1 metric 1000000 100 255 1 1500

  ! Import routes from BGP AS 65000
  redistribute bgp 65000 metric 1000000 100 255 1 1500

  ! Import static routes
  redistribute static metric 1000000 100 255 1 1500
```

### Metric Specification

Each protocol has different metric format. Must be specified explicitly.

```ios

! EIGRP metric: bandwidth delay reliability load mtu
redistribute ospf 1 metric 1000000 100 255 1 1500

! OSPF metric (cost)
redistribute eigrp 100 metric 100

! BGP (no metric; assign arbitrary value)
redistribute bgp 65000 metric 100
```

### Route-Map (Filtering & Modification)

Apply conditions to filter or modify redistributed routes.

```ios

route-map REDIS-FILTER permit 10
  match ip address prefix-list ALLOWED-ROUTES
  set metric 1000
  set tag 100

router eigrp 100
  redistribute ospf 1 metric 1000000 100 255 1 1500 route-map REDIS-FILTER
```

---

## Metric Guidelines by Protocol Pair

### OSPF to EIGRP

```ios

! EIGRP metric: bandwidth(Kbps) delay(10s) reliability(0-255) load(0-255) mtu(bytes)
redistribute ospf 1 metric 1000000 100 255 1 1500
! bandwidth=1Gbps, delay=10ms, reliability=100%, load=1/255, mtu=1500
```

### EIGRP to OSPF

```ios

! OSPF cost (0-65535, typically 1-1000)
redistribute eigrp 100 metric 100
! Equivalent to 1 Gbps link
```

### BGP to OSPF

```ios

! OSPF cost
redistribute bgp 65000 metric 100
```

### BGP to EIGRP

```ios

! EIGRP metric
redistribute bgp 65000 metric 1000000 100 255 1 1500
```

### Static Routes

```ios

! To OSPF
redistribute static metric 100

! To EIGRP
redistribute static metric 1000000 100 255 1 1500
```

---

## Filtering Redistributed Routes

### Deny Specific Routes

```ios

ip prefix-list DENY-ROUTES seq 10 permit 10.0.0.0/24

route-map REDIS-FILTER deny 10
  match ip address prefix-list DENY-ROUTES

route-map REDIS-FILTER permit 20
  ! Allow everything else

router eigrp 100
  redistribute ospf 1 metric 1000000 100 255 1 1500 route-map REDIS-FILTER
```

### Filter by Route Tag

```ios

! Tag redistributed routes
route-map TAG-ROUTES permit 10
  set tag 100

! Don't re-redistribute tagged routes
route-map BLOCK-TAGGED deny 10
  match tag 100

route-map BLOCK-TAGGED permit 20

router ospf 1
  redistribute bgp 65000 metric 100 route-map BLOCK-TAGGED
```

### Modify Metric During Redistribution

```ios

route-map MODIFY-METRIC permit 10
  match ip address 10.0.0.0 0.0.0.255
  set metric 1000

router eigrp 100
  redistribute ospf 1 metric 1000000 100 255 1 1500 route-map MODIFY-METRIC
```

---

## Complete Configuration Example

### Scenario: Merge Two Networks (OSPF + EIGRP)

```text

Company A (OSPF):
  Area 0: 10.0.0.0/24
  Area 1: 10.1.0.0/24

Company B (EIGRP AS 100):
  Network: 192.168.0.0/16

Border Router:
  e0/0: Connected to Company A (OSPF)
  e0/1: Connected to Company B (EIGRP)

Requirement:

  - OSPF network learns Company B routes (via EIGRP)
  - EIGRP network learns Company A routes (via OSPF)
  - Prevent loops with route tags
```

**Configuration:**

```ios

configure terminal

! ===== Router A (OSPF to EIGRP) =====
router ospf 1
  network 10.0.0.0 0.0.0.255 area 0
  network 10.1.0.0 0.0.0.255 area 1
  ! Redistribute EIGRP routes into OSPF
  redistribute eigrp 100 metric 100 route-map TAG-EIGRP

! ===== Router B (EIGRP to OSPF) =====
router eigrp 100
  network 192.168.0.0 0.0.0.0
  ! Redistribute OSPF routes into EIGRP
  redistribute ospf 1 metric 1000000 100 255 1 1500 route-map TAG-OSPF

! ===== Prevent Loops: Tag Redistributed Routes =====
route-map TAG-OSPF permit 10
  set tag 200

route-map TAG-EIGRP permit 10
  set tag 100

! ===== Block Re-redistribution =====
! At Router A: Don't redistribute EIGRP routes back into OSPF if they came from OSPF
route-map BLOCK-OSPF-ECHO deny 10
  match tag 100

route-map BLOCK-OSPF-ECHO permit 20

! At Router B: Don't redistribute OSPF routes back into EIGRP if they came from EIGRP
route-map BLOCK-EIGRP-ECHO deny 10
  match tag 200

route-map BLOCK-EIGRP-ECHO permit 20

! === Apply blocking at Router A ===
router eigrp 100
redistribute ospf 1 metric 1000000 100 255 1 1500 route-map TAG-OSPF route-map
BLOCK-EIGRP-ECHO

! === Apply blocking at Router B ===
router ospf 1
  redistribute eigrp 100 metric 100 route-map TAG-EIGRP route-map BLOCK-OSPF-ECHO

end
```

---

## Redistribution with Default Routes

### Inject Default Route During Redistribution

```ios

route-map INJECT-DEFAULT permit 10
  match interface Loopback0

router eigrp 100
  redistribute ospf 1 metric 1000000 100 255 1 1500 route-map INJECT-DEFAULT
  default-information originate metric 1000000 100 255 1 1500
```

### Redistribute Default Route Only

```ios

route-map DEFAULT-ONLY permit 10
  match ip address prefix-list DEFAULT-PREFIX

ip prefix-list DEFAULT-PREFIX seq 10 permit 0.0.0.0/0

router eigrp 100
  redistribute ospf 1 metric 1000000 100 255 1 1500 route-map DEFAULT-ONLY
```

---

## Verification and Monitoring

### Check Redistributed Routes

```ios

show ip route ospf
! Routes learned from OSPF redistribution

show ip route eigrp
! Routes learned from EIGRP redistribution

show ip route 10.0.0.0
! Details of specific route
```

### Verify Route-Map Matches

```ios

show route-map TAG-OSPF

! Output:
! route-map TAG-OSPF, permit, sequence 10
!   Match clauses:
!   Set clauses:
!     tag 200
!   Route map is used for:
!     Redistribution
!   Policy routing matches: 0 packets, 0 bytes
```

### Check Redistribution Configuration

```ios

show running-config | include redistribute
! Shows all redistribution commands

show ip eigrp topology 10.0.0.0 255.255.255.0
! Details of redistributed EIGRP route
```

### Trace Route Origin

```ios

show ip route 10.0.0.0
! Example output:
! O E2 10.0.0.0/24 [110/20] via 192.168.1.1, 00:05:23, GigabitEthernet0/1
! O E2 = OSPF External Type 2
! [110/20] = [AD/Metric]
! Indicates route is redistributed (external)
```

---

## Common Issues and Fixes

### Issue: Redistributed Routes Not Appearing

**Cause:** Source protocol doesn't have route, or redistribution metric not specified.

**Check:**

```ios

show ip route ospf
! Verify route exists in source protocol

show running-config | include redistribute
! Verify redistribution command is configured
```

#### Fix

```ios

router eigrp 100
  redistribute ospf 1 metric 1000000 100 255 1 1500
  ! Must specify metric explicitly
```

### Issue: Routing Loop (Redistributed Route Feeds Back to Source)

**Cause:** Two routers redistribute same route in both directions.

```text

Router A: redistribute OSPF into EIGRP
Router B: redistribute EIGRP into OSPF

OSPF sees route twice (original + redistributed)
```

**Check:**

```ios

show ip route 10.0.0.0
! If multiple paths with similar metrics, possible loop
```

#### Fix: Use Route Tags

```ios

! At Router A
route-map TAG-OSPF permit 10
  set tag 100

router eigrp 100
  redistribute ospf 1 metric 1000000 100 255 1 1500 route-map TAG-OSPF

! At Router B
route-map BLOCK-ECHO deny 10
  match tag 100

route-map BLOCK-ECHO permit 20

router ospf 1
  redistribute eigrp 100 metric 100 route-map BLOCK-ECHO
```

### Issue: Metric Not Applied Correctly

**Cause:** EIGRP metric format incorrect, or values out of range.

**Check:**

```ios

show running-config | include redistribute
```

**Fix:**

```ios

! EIGRP metric: bandwidth delay reliability load mtu
! bandwidth: 1-4294967295 (Kbps)
! delay: 0-4294967295 (10 microsecond units)
! reliability: 1-255
! load: 1-255
! mtu: 68-65535 (bytes)

router eigrp 100
  redistribute ospf 1 metric 1000000 100 255 1 1500
  ! Correct format: bandwidth=1Gbps, delay=10ms, reliability=100%, load=1, mtu=1500
```

### Issue: Asymmetric Routing (Return Path Different)

**Cause:** Return traffic doesn't redistribute; takes default route via different protocol.

**Fix:**

```ios

! Ensure return traffic also redistributed
router ospf 1
  redistribute eigrp 100 metric 100

router eigrp 100
  redistribute ospf 1 metric 1000000 100 255 1 1500
```

---

## Best Practices

| Practice | Reason |
| --- | --- |
| **Always specify metric** | Default may cause route to not be installed |
| **Use route tags** | Prevent loops by marking redistributed routes |
| **Redistribute in both directions carefully** | Prevents loops; use filtering if needed |
| **Test in lab first** | Redistribution can cause unexpected routing |
| **Monitor redistributed route count** | Sudden increase may indicate misconfiguration |
| **Document redistribution** | Complex logic is hard to remember |
| **Use one-way redistribution when possible** | Simpler than bidirectional with filtering |
| **Set lower AD for native routes** | Prefers original source over redistributed |
| **Aggregate routes before redistribution** | Reduces routing table bloat |
| **Disable redistribution after migration** | Remove when no longer needed |

---

## Configuration Checklist

- [ ] Identify source and destination protocols
- [ ] Determine metric for destination protocol
- [ ] Create route-map for filtering (if needed)
- [ ] Add redistribute command with metric
- [ ] Apply route-map to redistribute
- [ ] Verify source routes exist
- [ ] Verify redistributed routes appear
- [ ] Check route metrics are correct
- [ ] Test traffic paths with traceroute
- [ ] Verify no routing loops
- [ ] Monitor route counts
- [ ] Document redistribution logic

---

## Quick Reference

```ios

! Basic redistribution OSPF to EIGRP
router eigrp 100
  redistribute ospf 1 metric 1000000 100 255 1 1500

! Redistribute with filtering
ip prefix-list ALLOWED seq 10 permit 10.0.0.0/16

route-map FILTER permit 10
  match ip address prefix-list ALLOWED

router eigrp 100
  redistribute ospf 1 metric 1000000 100 255 1 1500 route-map FILTER

! Redistribute with tags to prevent loops
route-map TAG permit 10
  set tag 100

route-map BLOCK deny 10
  match tag 100

route-map BLOCK permit 20

router ospf 1
  redistribute eigrp 100 metric 100 route-map BLOCK

! Verify
show running-config | include redistribute
show ip route 10.0.0.0
show route-map
```
