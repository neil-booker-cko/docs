# FortiGate BGP Route Aggregation and Summarization Guide

Complete reference for summarizing routes in BGP on Fortinet FortiGate.

## Quick Start: Aggregate Routes

```text
config router bgp
  config aggregate-address
    edit 1
      set prefix 10.0.0.0 255.255.252.0
      set summary-only enable
    next
  end
end
```

---

## BGP Aggregation Overview

### Why Aggregate?

Reduces routing table size and BGP update frequency.

```text

Without aggregation (4 routes advertised):
  10.0.0.0/24  Metric: 100
  10.0.1.0/24  Metric: 100
  10.0.2.0/24  Metric: 100
  10.0.3.0/24  Metric: 100

With aggregation (1 route advertised):
  10.0.0.0/22  Metric: 100

Result: 4x smaller routing table, faster convergence
```

### Aggregation Requirements

Subnets must be:

1. **Contiguous** — No gaps
1. **Aligned** — Start address on power-of-2 boundary

**Example (aggregatable):**

```text

10.0.0.0/24  ✓
10.0.1.0/24  ✓
10.0.2.0/24  ✓
10.0.3.0/24  ✓
→ Aggregate to 10.0.0.0/22
```

**Example (NOT aggregatable):**

```text

10.0.0.0/24  ✓
10.0.1.0/24  ✓
10.0.3.0/24  ✗ (gap at 10.0.2.0/24)
→ Cannot aggregate all three
```

---

## Basic Aggregate Configuration

### Simple Aggregation with summary-only

```text

config router bgp
  set as 65000
  set router-id 10.0.0.1

  config aggregate-address
    edit 1
      ! Aggregate address and mask
      set prefix 10.0.0.0 255.255.252.0

      ! Do NOT advertise component /24 routes individually
      set summary-only enable
    next
  end
end
```

**Result:**

- FortiGate advertises 10.0.0.0/22 to BGP neighbors
- Component routes (10.0.0.0/24, 10.0.1.0/24, etc.) used internally but NOT advertised

### Aggregation WITHOUT summary-only

```text

config router bgp
  config aggregate-address
    edit 1
      set prefix 10.0.0.0 255.255.252.0
      set summary-only disable  ! Advertise aggregate AND component routes
    next
  end
end
```

**Result:**

- Advertises both 10.0.0.0/22 AND individual /24 routes
- Useful when components need specific policies

---

## Aggregation with AS-SET

### Include All ASNs from Component Routes

```text

config router bgp
  config aggregate-address
    edit 1
      set prefix 10.0.0.0 255.255.252.0
      set summary-only enable

      ! Include all ASNs from component routes
      set as-set enable
    next
  end
end
```

**Without as-set:**

```text

Advertised: 10.0.0.0/22  AS Path: 65000
(loses info about which ASes own component routes)
```

**With as-set:**

```text

Advertised: 10.0.0.0/22  AS Path: 65000 {65001, 65002, 65003}
(preserves info about component ASes)
```

---

## Complete Configuration Example

### Scenario: HQ Aggregates Four Branch Subnets

```text

HQ (aggregator): 10.0.0.0/22 = 10.0.0.0/24 + 10.0.1.0/24 + 10.0.2.0/24 + 10.0.3.0/24

Branch 1: 10.0.0.0/24
Branch 2: 10.0.1.0/24
Branch 3: 10.0.2.0/24
Branch 4: 10.0.3.0/24

HQ announces to ISP: 10.0.0.0/22 (single aggregate)
```

**HQ FortiGate Configuration:**

```text

config router settings
  set router-id 10.0.0.1
end

config router bgp
  set as 65000
  set router-id 10.0.0.1

  ! === Announce local subnets (each branch's /24) ===
  config network
    edit 1
      set prefix 10.0.0.0 255.255.255.0  ! Branch 1
    next
    edit 2
      set prefix 10.0.1.0 255.255.255.0  ! Branch 2
    next
    edit 3
      set prefix 10.0.2.0 255.255.255.0  ! Branch 3
    next
    edit 4
      set prefix 10.0.3.0 255.255.255.0  ! Branch 4
    next
  end

  ! === Aggregate address for ISP ===
  config aggregate-address
    edit 1
      set prefix 10.0.0.0 255.255.252.0
      set summary-only enable
      set as-set enable
    next
  end

  ! === BGP Neighbor: ISP ===
  config neighbor
    edit "200.1.1.1"
      set remote-as 65001
      set description "ISP-1"
    next
  end
end
```

**Result:**

- Internal (HQ ↔ Branch): Routes on /24 (granular control)
- External (to ISP): Advertises /22 aggregate only
- ISP routing table: 1 route instead of 4

---

## Filtering and Policy with Aggregation

### Export Different Routes to Different Neighbors

```text

config router bgp
  ! To ISP: advertise aggregate only
  config neighbor
    edit "200.1.1.1"
      set remote-as 65001
      set route-map-out "EXPORT-TO-ISP"
    next
  end

  ! To branches: advertise component routes
  config neighbor
    edit "192.168.1.2"  ! Branch 1
      set remote-as 65000
      set route-map-out "EXPORT-TO-BRANCH"
    next
  end
end

! === Route maps ===
config router route-map
  edit "EXPORT-TO-ISP"
    config rule
      edit 1
        ! Export only the aggregate
        set match-ip-address "PL-AGGREGATE"
        set action permit
      next
      edit 2
        ! Block component routes
        set match-ip-address "PL-COMPONENTS"
        set action deny
      next
    end
  next

  edit "EXPORT-TO-BRANCH"
    config rule
      edit 1
        ! Export component routes and other networks
        set action permit
      next
    end
  next
end

! === Prefix lists ===
config router prefix-list
  edit "PL-AGGREGATE"
    config rule
      edit 1
        set prefix 10.0.0.0 255.255.252.0
        set le 22
      next
    end
  next

  edit "PL-COMPONENTS"
    config rule
      edit 1
        set prefix 10.0.0.0 255.255.255.0
        set le 24
      next
      edit 2
        set prefix 10.0.1.0 255.255.255.0
        set le 24
      next
      edit 3
        set prefix 10.0.2.0 255.255.255.0
        set le 24
      next
      edit 4
        set prefix 10.0.3.0 255.255.255.0
        set le 24
      next
    end
  next
end
```

---

## Multi-Level Aggregation (Hierarchical)

### Regional Aggregation

```text

Organization: 10.0.0.0/8

Region 1 (Americas): 10.0.0.0/10
  Site 1 (HQ): 10.0.0.0/16
    Subnet A: 10.0.1.0/24
    Subnet B: 10.0.2.0/24
  Site 2: 10.1.0.0/16
    Subnet A: 10.1.1.0/24
    Subnet B: 10.1.2.0/24

Region 2 (Europe): 10.64.0.0/10
  Site 3: 10.64.0.0/16
  Site 4: 10.65.0.0/16

BGP Aggregation:
  Site 1 announces: 10.0.0.0/16 (aggregate of 10.0.1.0/24, 10.0.2.0/24)
  Site 2 announces: 10.1.0.0/16 (aggregate of 10.1.1.0/24, 10.1.2.0/24)
  Region 1 announces: 10.0.0.0/10 (aggregate of 10.0.0.0/16, 10.1.0.0/16)

  Organization announces: 10.0.0.0/8 (aggregate of all regions)
```

### Region 1 HQ Router Configuration

```text

config router bgp
  set as 65000

  ! === Advertise site aggregates ===
  config aggregate-address
    edit 1
      set prefix 10.0.0.0 255.255.0.0  ! Site 1: 10.0.0.0/16
      set summary-only enable
    next
    edit 2
      set prefix 10.1.0.0 255.255.0.0  ! Site 2: 10.1.0.0/16
      set summary-only enable
    next
  end

  ! === Advertise regional aggregate ===
  config aggregate-address
    edit 3
      set prefix 10.0.0.0 255.192.0.0  ! Region: 10.0.0.0/10
      set summary-only enable
    next
  end
end
```

---

## Verification and Monitoring

### Check Advertised Routes

```text

get router info bgp neighbors 200.1.1.1 advertised-routes

! Output:
! BGP table version is 1, local router ID is 10.0.0.1
! Status codes: s suppressed, d damped, h history, * valid, > best, i - internal
!
! Prefixes: 1
! Network           Next Hop     Metric  LocPrf  Weight  Path
! 10.0.0.0/22      0.0.0.0         0             32768  i
!
! (Only aggregate advertised, /24s suppressed by summary-only)
```

### Check BGP Routing Table

```text

get router info bgp network

! Shows all routes in BGP, including aggregates and components
```

### Check Aggregate Status

```text

get router bgp aggregate-address

! Shows configured aggregates and their status
```

### Detailed BGP Info

```text

get router info bgp 10.0.0.0/22

! Detailed information about specific aggregate
```

---

## Common Issues and Fixes

### Issue: Aggregate Not Being Advertised

**Cause:** Component routes don't exist in BGP; aggregate disabled.

**Check:**

```text

get router info bgp network | grep 10.0

! Verify component /24 routes are in BGP table
! Verify aggregate entry exists
```

**Troubleshoot:**

```text

get router bgp summary

! Check BGP is enabled and has neighbors

get router info bgp neighbors 200.1.1.1

! Verify neighbor is established
```

**Fix:**

```text

config router bgp
  ! Ensure component networks are advertised
  config network
    edit 1
      set prefix 10.0.0.0 255.255.255.0
    next
    edit 2
      set prefix 10.0.1.0 255.255.255.0
    next
  end

  ! Enable aggregate
  config aggregate-address
    edit 1
      set prefix 10.0.0.0 255.255.252.0
      set summary-only enable
    next
  end
end
```

### Issue: Both Aggregate AND Component Routes Advertised

**Cause:** `summary-only` not enabled.

**Check:**

```text

get router info bgp neighbors 200.1.1.1 advertised-routes

! If you see:
! 10.0.0.0/22
! 10.0.0.0/24
! 10.0.1.0/24
! → summary-only is disabled
```

**Fix:**

```text

config router bgp
  config aggregate-address
    edit 1
      set prefix 10.0.0.0 255.255.252.0
      set summary-only enable
    next
  end
end
```

### Issue: Wrong AS Path in Aggregate

**Cause:** as-set not enabled; component ASNs lost.

**Check:**

```text

get router info bgp 10.0.0.0/22

! Look at AS Path; should include component ASNs if as-set enabled
```

**Fix:**

```text

config router bgp
  config aggregate-address
    edit 1
      set prefix 10.0.0.0 255.255.252.0
      set as-set enable
    next
  end
end
```

### Issue: Routes Not Being Aggregated

**Cause:** Routes not contiguous or not aligned; cannot aggregate.

**Check:**

```text

! Verify routes are contiguous
10.0.0.0/24  ✓
10.0.1.0/24  ✓
10.0.2.0/24  ✓
10.0.3.0/24  ✓
→ Should aggregate to 10.0.0.0/22

! But if you have:
10.0.0.0/24  ✓
10.0.2.0/24  ✓
→ Cannot aggregate (gap at 10.0.1.0)
```

**Fix:** Redesign IP plan to ensure routes are contiguous and aligned.

---

## Best Practices

| Practice | Reason |
| --- | --------- |
| **Design for aggregation** | Plan subnets contiguously and aligned |
| **Use summary-only** | Prevent duplicate advertisements |
| **Enable as-set for multi-AS** | Preserve AS path information |
| **Monitor advertised routes** | Verify aggregation is working |
| **Document boundaries** | Facilitate future changes |
| **Use route-maps** | Different aggregation policy per neighbor |
| **Test failover** | Verify aggregate is withdrawn if all components fail |
| **Use hierarchical aggregation** | Multi-level reduces routing table growth |

---

## Configuration Checklist

- [ ] Design IP plan with aggregation in mind
- [ ] Configure component networks (network statements)
- [ ] Verify component routes are in BGP table
- [ ] Add aggregate-address with summary-only enable
- [ ] Enable as-set if needed
- [ ] Verify aggregate is advertised to neighbors
- [ ] Verify component routes are suppressed (if summary-only)
- [ ] Test failover (withdraw component route, verify aggregate withdrawn)
- [ ] Monitor BGP table size
- [ ] Save configuration

---

## Quick Reference

```text

! Simple aggregation
config router bgp
  config aggregate-address
    edit 1
      set prefix 10.0.0.0 255.255.252.0
      set summary-only enable
    next
  end
end

! Aggregation with as-set
config router bgp
  config aggregate-address
    edit 1
      set prefix 10.0.0.0 255.255.252.0
      set summary-only enable
      set as-set enable
    next
  end
end

! Verify
get router info bgp neighbors 200.1.1.1 advertised-routes
get router info bgp network
get router bgp aggregate-address
```
