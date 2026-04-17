# Cisco BGP Route Aggregation and Summarization Guide

Complete reference for summarizing routes in BGP on Cisco IOS-XE.

## Quick Start: Aggregate Routes

```ios
configure terminal

router bgp 65000
  ! Advertise 10.0.0.0/22 as summary of four /24 subnets
  aggregate-address 10.0.0.0 255.255.252.0 summary-only

  ! Ensure individual /24 routes are configured to be advertised
  network 10.0.0.0 mask 255.255.255.0
  network 10.0.1.0 mask 255.255.255.0
  network 10.0.2.0 mask 255.255.255.0
  network 10.0.3.0 mask 255.255.255.0

end
show ip bgp neighbors <neighbor-ip> advertised-routes
```

---

## BGP Aggregation Overview

### Why Aggregate?

Aggregation reduces the size of routing tables and BGP updates.

```text

Without aggregation (4 routes advertised):
  10.0.0.0/24  → metrics/path info
  10.0.1.0/24  → metrics/path info
  10.0.2.0/24  → metrics/path info
  10.0.3.0/24  → metrics/path info

With aggregation (1 route advertised):
  10.0.0.0/22  → metrics/path info

Result: BGP table 4x smaller, faster convergence, less memory
```

### When to Aggregate

- **Multi-site networks** — Summarize all site routes
- **Large organizations** — Reduce BGP table explosion
- **ISP routes** — Summarize customer routes
- **MPLS VPN** — Summarize customer VRF routes

### When NOT to Aggregate

- **Single small network** — No benefit to summarizing 1 route
- **Discontiguous subnets** — Cannot summarize gaps
- **Need granular control** — Some routes require different policies

---

## Aggregate Configuration

### Basic Aggregate Address

```ios

configure terminal

router bgp 65000
  ! Advertise aggregate; suppress individual routes
  aggregate-address 10.0.0.0 255.255.252.0 summary-only

end
```

### Aggregate Address Options

```ios

router bgp 65000
  aggregate-address 10.0.0.0 255.255.252.0
    ! summary-only: Do NOT advertise individual component routes
    summary-only

    ! as-set: Include all ASNs from component routes
    ! (Adds AS path length; useful for load balancing)
    as-set

    ! advertise-map: Only advertise aggregate if certain conditions met
    advertise-map RM-Advertise condition-map RM-Condition

    ! suppress-map: Suppress specific component routes
    suppress-map RM-Suppress

end
```

---

## Simple Aggregation Example

### Scenario: Four Sites, Each with Own /24

```text

HQ (site A): 10.0.0.0/24      (254 hosts)
Branch 1 (site B): 10.0.1.0/24 (254 hosts)
Branch 2 (site C): 10.0.2.0/24 (254 hosts)
Branch 3 (site D): 10.0.3.0/24 (254 hosts)

Total: 1,016 hosts
Aggregate: 10.0.0.0/22        (1,022 hosts — fits perfectly!)
```

### BGP Configuration at HQ Router

**HQ announces summary to internet:**

```ios

configure terminal

router bgp 65000
  ! Advertise individual /24 routes to branch sites (internal)
  network 10.0.0.0 mask 255.255.255.0
  network 10.0.1.0 mask 255.255.255.0
  network 10.0.2.0 mask 255.255.255.0
  network 10.0.3.0 mask 255.255.255.0

  ! To internal/branch neighbors: advertise individual /24
  ! (BGP automatically advertises what matches network statements)

  ! To ISP/internet neighbors: advertise aggregate
  neighbor 200.1.1.1 remote-as 65001

  ! Use route-map to advertise summary to ISP
  neighbor 200.1.1.1 route-map EXPORT-TO-ISP out

end

! === Route map: advertise aggregate to ISP, suppress /24s ===
route-map EXPORT-TO-ISP permit 10
  match ip address prefix-list AGGREGATE-ONLY
  set metric 100
exit

route-map EXPORT-TO-ISP deny 20
  match ip address prefix-list COMPONENT-ROUTES

exit

! === Prefix lists ===
ip prefix-list AGGREGATE-ONLY seq 10 permit 10.0.0.0/22
ip prefix-list COMPONENT-ROUTES seq 10 permit 10.0.0.0/24
ip prefix-list COMPONENT-ROUTES seq 20 permit 10.0.1.0/24
ip prefix-list COMPONENT-ROUTES seq 30 permit 10.0.2.0/24
ip prefix-list COMPONENT-ROUTES seq 40 permit 10.0.3.0/24
```

**Result:**

- Internal networks (HQ ↔ Branch) route on /24 (granular)
- Internet receives /22 aggregate (HQ announces summary)
- ISP routing table smaller; faster convergence

---

## Advanced Aggregation with as-set

### Problem: Losing AS Path Information

When aggregating, BGP loses the individual AS paths of component routes.

```text

Without as-set:
  Route to 10.0.1.0/24: 65000 65001 65002 (path via three ASNs)
  Route to 10.0.2.0/24: 65000 65003 65004 (path via three ASNs)

  Aggregate advertised:
  10.0.0.0/22: 65000  ← AS path shortened; loses information

With as-set:
  Aggregate advertised:
  10.0.0.0/22: 65000 {65001, 65002, 65003, 65004}  ← all ASNs preserved
```

### Configuration with as-set

```ios

configure terminal

router bgp 65000
  ! Include all ASNs from component routes in aggregate
  aggregate-address 10.0.0.0 255.255.252.0 as-set summary-only

end
```

**Tradeoff:**

- **Pro:** Preserves AS information; prevents routing loops
- **Con:** Aggregate AS path is longer; may be less preferred for load balancing

---

## Conditional Aggregation

### Advertise Aggregate Only If Component Routes Exist

By default, aggregate is advertised even if no component routes exist. Use conditional aggregation to
advertise only when needed.

```ios

configure terminal

router bgp 65000
  ! Aggregate only if at least one component route exists
  aggregate-address 10.0.0.0 255.255.252.0
    advertise-map RM-ADVERTISE
    suppress-map RM-SUPPRESS

end

! === Route map: when to advertise ===
! Advertise aggregate if 10.0.0.0/24 OR 10.0.1.0/24 exists
route-map RM-ADVERTISE permit 10
  match ip address prefix-list COMPONENT-ROUTES-EXIST
exit

! === Route map: which routes to suppress ===
! When advertising aggregate, suppress individual /24s
route-map RM-SUPPRESS permit 10
  match ip address prefix-list COMPONENT-ROUTES
exit

! === Prefix lists ===
ip prefix-list COMPONENT-ROUTES-EXIST seq 10 permit 10.0.0.0/24
ip prefix-list COMPONENT-ROUTES-EXIST seq 20 permit 10.0.1.0/24

ip prefix-list COMPONENT-ROUTES seq 10 permit 10.0.0.0/24
ip prefix-list COMPONENT-ROUTES seq 20 permit 10.0.1.0/24
ip prefix-list COMPONENT-ROUTES seq 30 permit 10.0.2.0/24
ip prefix-list COMPONENT-ROUTES seq 40 permit 10.0.3.0/24
```

---

## Multi-Level Aggregation (Hierarchical)

### Scenario: Regional Aggregation

```text

Organization: 10.0.0.0/8

Region 1 (Americas): 10.0.0.0/10
  Site 1: 10.0.0.0/16
    Subnet A: 10.0.1.0/24
    Subnet B: 10.0.2.0/24
  Site 2: 10.1.0.0/16
    Subnet A: 10.1.1.0/24
    Subnet B: 10.1.2.0/24

Region 2 (Europe): 10.64.0.0/10
  Site 3: 10.64.0.0/16
    Subnet A: 10.64.1.0/24
    Subnet B: 10.64.2.0/24
  Site 4: 10.65.0.0/16
    Subnet A: 10.65.1.0/24
    Subnet B: 10.65.2.0/24

BGP Advertisements:
  Site 1 announces: 10.0.0.0/16 (aggregates 10.0.1.0/24, 10.0.2.0/24)
  Site 2 announces: 10.1.0.0/16 (aggregates 10.1.1.0/24, 10.1.2.0/24)
  Region 1 (HQ) announces: 10.0.0.0/10 (aggregates 10.0.0.0/16, 10.1.0.0/16)

  Site 3 announces: 10.64.0.0/16
  Site 4 announces: 10.65.0.0/16
  Region 2 announces: 10.64.0.0/10 (aggregates sites 3 & 4)

  Organization announces: 10.0.0.0/8 (aggregates all regions)
```

### Configuration at Organization HQ

```ios

configure terminal

router bgp 65000
  ! Advertise organization aggregate
  aggregate-address 10.0.0.0 255.0.0.0 summary-only

  ! Also accept and aggregate regional summaries from regions
  ! (handled by route redistribution or neighbor policies)

end
```

---

## Verification and Monitoring

### Check Aggregate Configuration

```ios

show ip bgp neighbors 200.1.1.1 advertised-routes

! Look for:
! - 10.0.0.0/22 advertised (aggregate)
! - Component /24 routes NOT advertised (if summary-only set)
```

### Check BGP Table for Aggregates

```ios

show ip bgp 10.0.0.0/22

! Output:
! BGP routing table entry for 10.0.0.0/22, version 123
! Paths: 1 available, best #1, table Default-IP-Routing-Table
! Flag: A
! Advertised to update-groups:
!    1 2
!  Aggregate
```

### Check for Suppressed Routes

```ios

show ip bgp neighbors 200.1.1.1 advertised-routes | include suppress

! If summary-only set, suppressed /24 routes don't appear in advertised list
```

### Debug Aggregation

```ios

debug ip bgp updates

! Shows when aggregates are created/withdrawn
! Be careful; generates lots of output

undebug all
```

---

## Common Issues and Fixes

### Issue: Aggregate Not Being Advertised

**Cause:** Component routes don't exist; aggregate disabled; no BGP neighbors.

**Check:**

```ios

show ip bgp summary

! Verify neighbors are established

show ip bgp 10.0.0.0 10.0.0.0

! Check if any component routes exist in BGP table

show ip bgp | include 10.0
! Look for 10.0.0.0/22, 10.0.1.0/24, etc.
```

**Fix:**

```ios

configure terminal

router bgp 65000
  ! Ensure component routes are configured
  network 10.0.0.0 mask 255.255.255.0
  network 10.0.1.0 mask 255.255.255.0

  ! Enable aggregate
  aggregate-address 10.0.0.0 255.255.252.0 summary-only

end
```

### Issue: Aggregate Advertised BUT So Are Component Routes

**Cause:** `summary-only` not configured; routes being advertised separately.

**Check:**

```ios

show ip bgp neighbors 200.1.1.1 advertised-routes

! If you see both 10.0.0.0/22 AND 10.0.0.0/24, 10.0.1.0/24, etc.
! → summary-only is not working
```

**Fix:**

```ios

configure terminal

router bgp 65000
  aggregate-address 10.0.0.0 255.255.252.0 summary-only
  ! Add summary-only flag

end
```

### Issue: Wrong Routes Being Advertised

**Cause:** Route-map filtering incorrectly suppressing routes.

**Check:**

```ios

show route-map EXPORT-TO-ISP

! Verify match/deny rules are correct
```

**Fix:** Review route-map logic and adjust prefix lists.

---

## Best Practices

| Practice | Reason |
| --- | --------- |
| **Plan subnets for aggregation** | Design must support hierarchical summary |
| **Use summary-only** | Prevents duplicate advertisements |
| **Document aggregation boundaries** | Facilitates future changes |
| **Test before production** | Verify routes are actually advertised |
| **Use as-set for inter-domain** | Preserves AS path information |
| **Monitor aggregate health** | Verify component routes are being summarized |
| **Use conditional aggregation** | Only advertise if component routes exist |
| **Implement hierarchical aggregation** | Multi-level reduces routing table growth |

---

## Configuration Checklist

- [ ] Design IP plan with aggregation in mind (contiguous, aligned)
- [ ] Configure component routes (network statements)
- [ ] Verify component routes are in BGP table
- [ ] Add aggregate-address statement with summary-only
- [ ] Verify aggregate is advertised to neighbors
- [ ] Verify component routes are NOT advertised (if summary-only)
- [ ] Check BGP table size reduction
- [ ] Test failover (remove component route, verify aggregate withdrawn)
- [ ] Monitor with `show ip bgp` periodically
- [ ] Document aggregation boundaries

---

## Quick Reference

```ios

! Simple aggregation
router bgp 65000
  aggregate-address 10.0.0.0 255.255.252.0 summary-only
end

! Aggregation with AS path preservation
router bgp 65000
  aggregate-address 10.0.0.0 255.255.252.0 as-set summary-only
end

! Verify
show ip bgp neighbors <neighbor> advertised-routes
show ip bgp 10.0.0.0/22
show ip bgp | include 10.0
```
