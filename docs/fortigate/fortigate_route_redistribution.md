# FortiGate Route Redistribution Configuration Guide

Complete reference for redistributing routes between routing protocols on Fortinet
FortiGate.

## Quick Start: Basic Redistribution

```text
config router ospf
  config redistribute
    edit 1
      set protocol bgp
      set metric 100
    next
  end
end
```

---

## Redistribution Components

### Source Protocol (Learned Routes)

Routes from this protocol will be imported into destination protocol.

```text

config router bgp
  config redistribute
    ! Redistribute OSPF into BGP
    edit 1
      set protocol ospf
    next

    ! Redistribute static routes
    edit 2
      set protocol static
    next
  end
end
```

### Metric Specification

Assign metric to redistributed routes. Required for protocol pairs with different metrics.

```text

config router ospf
  config redistribute
    edit 1
      set protocol bgp
      set metric 100  ! OSPF cost
    next
  end
end
```

### Route-Map (Filtering & Modification)

Apply conditions to filter or modify redistributed routes.

```text

config router static
  config prefix-list
    edit ALLOWED
      config rule
        edit 1
          set prefix 10.0.0.0 255.255.255.0
        next
      end
    next
  end
end

config router ospf
  config redistribute
    edit 1
      set protocol bgp
      set metric 100
      set routemap FILTER
    next
  end

  config route-map
    edit FILTER
      config rule
        edit 10
          set match-ip-address ALLOWED
          set set-metric 100
          set set-tag 100
        next
      end
    next
  end
end
```

---

## Metric Guidelines by Protocol Pair

### OSPF to BGP

```text

config router bgp
  config redistribute
    edit 1
      set protocol ospf
      ! BGP uses path attributes, not traditional metrics
    next
  end
end
```

### BGP to OSPF

```text

config router ospf
  config redistribute
    edit 1
      set protocol bgp
      set metric 100
    next
  end
end
```

### Static Routes to OSPF

```text

config router ospf
  config redistribute
    edit 1
      set protocol static
      set metric 100
    next
  end
end
```

### Static Routes to BGP

```text

config router bgp
  config redistribute
    edit 1
      set protocol static
    next
  end
end
```

---

## Filtering Redistributed Routes

### Deny Specific Routes

```text

config router static
  config prefix-list
    edit DENY-ROUTES
      config rule
        edit 1
          set prefix 192.168.1.0 255.255.255.0
          set action deny
        next

        edit 2
          set prefix 0.0.0.0 0.0.0.0
          set action permit
        next
      end
    next
  end
end

config router ospf
  config redistribute
    edit 1
      set protocol bgp
      set metric 100
      set routemap FILTER
    next
  end

  config route-map
    edit FILTER
      config rule
        edit 10
          set match-ip-address DENY-ROUTES
          set action deny
        next

        edit 20
          set action permit
        next
      end
    next
  end
end
```

### Filter by Route Tag

```text

config router ospf
  config redistribute
    edit 1
      set protocol bgp
      set metric 100
      set routemap TAG-ROUTES
    next
  end

  config route-map
    edit TAG-ROUTES
      config rule
        edit 10
          set set-tag 100
          set action permit
        next
      end
    next
  end
end

config router bgp
  config redistribute
    edit 1
      set protocol ospf
      set routemap BLOCK-TAGGED
    next
  end

  config route-map
    edit BLOCK-TAGGED
      config rule
        edit 10
          set match-tag 100
          set action deny
        next

        edit 20
          set action permit
        next
      end
    next
  end
end
```

---

## Complete Configuration Example

### Scenario: Multi-Site Network (OSPF + Static Routes)

```text

HQ (OSPF):
  Internal: 10.0.0.0/24
  Area 0: OSPF

Branch (Static Routes):
  Internal: 192.168.1.0/24
  Default route to ISP

Border Router:
  OSPF to HQ
  Static routes for branches
  Must advertise branch routes to HQ via OSPF

Requirement:

  - HQ learns branch routes via OSPF
  - Branches reach HQ via default route to ISP
```

**Configuration:**

```text

config router ospf
  set router-id 172.16.0.1

  config area
    edit 0
    next
  end

  config network
    edit 1
      set prefix 10.0.0.0 255.255.255.0
      set area 0
    next

    edit 2
      set prefix 172.16.0.0 255.255.255.0
      set area 0
    next
  end

  ! Redistribute static routes (branch routes) into OSPF
  config redistribute
    edit 1
      set protocol static
      set metric 100
      set routemap BRANCH-ROUTES
    next
  end

  ! Route-map to filter which static routes to redistribute
  config route-map
    edit BRANCH-ROUTES
      config rule
        edit 10
          set match-ip-address BRANCH-SUBNETS
          set set-tag 200
          set action permit
        next
      end
    next
  end
end

! Define branch subnets that should be redistributed
config router static
  config prefix-list
    edit BRANCH-SUBNETS
      config rule
        edit 1
          set prefix 192.168.1.0 255.255.255.0
        next

        edit 2
          set prefix 192.168.2.0 255.255.255.0
        next
      end
    next
  end

  ! Static routes for each branch
  edit 1
    set destination 192.168.1.0 255.255.255.0
    set gateway 200.1.1.1
    set device port2
  next

  edit 2
    set destination 192.168.2.0 255.255.255.0
    set gateway 200.1.1.2
    set device port2
  next
end
```

---

## Default Route Redistribution

### Advertise Default Route

```text

config router ospf
  set default-metric 100
  set default-metric-type 2

  config redistribute
    edit 1
      set protocol static
      set metric 100
      set routemap REDIS-DEFAULT
    next
  end

  config route-map
    edit REDIS-DEFAULT
      config rule
        edit 10
          set match-ip-address DEFAULT-ONLY
          set action permit
        next
      end
    next
  end
end

config router static
  config prefix-list
    edit DEFAULT-ONLY
      config rule
        edit 1
          set prefix 0.0.0.0 0.0.0.0
        next
      end
    next
  end
end
```

---

## Verification and Monitoring

### Check Redistributed Routes

```text

get router info ospf neighbor
! Shows OSPF neighbors

get router info ospf database
! Shows OSPF database

diagnose ip route list
! Shows all routes in routing table
```

### Verify Route Redistribution Status

```text

get router ospf summary
! Shows OSPF configuration summary

get router bgp summary
! Shows BGP configuration

diagnose debug config-error list
! Check for redistribution errors
```

### Check Specific Route

```text

diagnose ip route list 192.168.1.0 255.255.255.0
! Details of specific route

! Output example:
! S* 192.168.1.0/24 [10/0] via 200.1.1.1, port2, weight 0
! O 192.168.1.0/24 [110/100] via 172.16.0.1, port1
! (route learned via OSPF redistribution)
```

### Check Route Redistribution Configuration

```text

show router ospf
! Shows OSPF config including redistributions

show router bgp
! Shows BGP config including redistributions
```

### Monitor Route Count

```text

diagnose ip route list | grep -c "^S"
! Count static routes

diagnose ip route list | grep -c "^O"
! Count OSPF routes
```

---

## Common Issues and Fixes

### Issue: Redistributed Routes Not Appearing

**Cause:** Metric not specified, or source routes don't exist.

**Check:**

```text

diagnose ip route list
! Verify redistributed routes are in table

show router ospf
! Check redistribution configuration
```

**Fix:**

```text

config router ospf
  config redistribute
    edit 1
      set protocol static
      set metric 100  ! Must specify metric
    next
  end
end
```

### Issue: All Routes Being Redistributed (Too Much)

**Cause:** No filtering; all source protocol routes are redistributed.

```text

show router ospf
! Shows all BGP routes being redistributed into OSPF (may be too many)
```

#### Fix: Add Filtering

```text

config router static
  config prefix-list
    edit ALLOWED-ONLY
      config rule
        edit 1
          set prefix 192.168.0.0 255.255.0.0
        next
      end
    next
  end
end

config router ospf
  config redistribute
    edit 1
      set protocol bgp
      set metric 100
      set routemap FILTER
    next
  end

  config route-map
    edit FILTER
      config rule
        edit 10
          set match-ip-address ALLOWED-ONLY
          set action permit
        next
      end
    next
  end
end
```

### Issue: Routing Loop (Redistributed Route Feeds Back)

**Cause:** Redistributing same route in both directions without filtering.

```text

Router A: redistribute OSPF into BGP
Router B: redistribute BGP into OSPF

OSPF sees route from two sources
```

#### Fix: Use Tags and Filtering

```text

config router ospf
  config redistribute
    edit 1
      set protocol bgp
      set metric 100
      set routemap TAG-BGP
    next
  end

  config route-map
    edit TAG-BGP
      config rule
        edit 10
          set set-tag 100
          set action permit
        next
      end
    next
  end
end

config router bgp
  config redistribute
    edit 1
      set protocol ospf
      set routemap BLOCK-ECHO
    next
  end

  config route-map
    edit BLOCK-ECHO
      config rule
        edit 10
          set match-tag 100
          set action deny
        next

        edit 20
          set action permit
        next
      end
    next
  end
end
```

### Issue: Metric Not Applied Correctly

**Cause:** Metric value incorrect or out of range for destination protocol.

**Check:**

```text

show router ospf
! Verify metric value

diagnose ip route list
! Check if routes are actually installed
```

**Fix:**

```text

config router ospf
  config redistribute
    edit 1
      set protocol bgp
      set metric 100  ! OSPF cost: 1-65535
    next
  end
end
```

### Issue: No Return Path (Asymmetric Routing)

**Cause:** Return traffic doesn't have matching redistribution.

```text

Outbound (internal → external): Redistributed into OSPF
Return (external → internal): Doesn't match any redistribution; takes default
```

#### Fix: Redistribute Return Path

```text

config router ospf
  ! Forward path: static to OSPF
  config redistribute
    edit 1
      set protocol static
      set metric 100
    next
  end
end

config router bgp
  ! Return path: OSPF to BGP
  config redistribute
    edit 1
      set protocol ospf
    next
  end
end
```

---

## Best Practices

| Practice | Reason |
| --- | --- |
| **Always specify metric** | Default may not work or may be unsafe |
| **Filter redistributed routes** | Don't flood network with all source routes |
| **Use route tags** | Prevent loops by marking redistributed routes |
| **Redistribute in one direction when possible** | Simpler than bidirectional with filtering |
| **Test in lab first** | Redistribution can cause unexpected routing |
| **Monitor route counts** | Sudden increase indicates misconfiguration |
| **Document redistribution logic** | Complex logic is easy to forget |
| **Use specific prefix-lists** | Better than accepting all routes |
| **Set appropriate metrics** | Prefer native routes over redistributed |
| **Disable after migration** | Remove redistribution when no longer needed |

---

## Configuration Checklist

- [ ] Identify source and destination routing protocols
- [ ] Determine metric for destination protocol
- [ ] Create prefix-list for filtering (if needed)
- [ ] Create route-map to apply filtering and tags
- [ ] Add redistribute commands with metric
- [ ] Apply route-map to redistribute
- [ ] Verify source routes exist in routing table
- [ ] Verify redistributed routes appear
- [ ] Check route metrics are correct
- [ ] Test with ping/traceroute from different sources
- [ ] Verify no routing loops
- [ ] Monitor route counts regularly
- [ ] Document redistribution configuration

---

## Quick Reference

```text

! Basic redistribution: BGP to OSPF
config router ospf
  config redistribute
    edit 1
      set protocol bgp
      set metric 100
    next
  end
end

! Redistribution with filtering
config router static
  config prefix-list
    edit ALLOWED
      config rule
        edit 1
          set prefix 10.0.0.0 255.255.255.0
        next
      end
    next
  end
end

config router ospf
  config redistribute
    edit 1
      set protocol bgp
      set metric 100
      set routemap FILTER
    next
  end

  config route-map
    edit FILTER
      config rule
        edit 10
          set match-ip-address ALLOWED
          set action permit
        next
      end
    next
  end
end

! Verify
diagnose ip route list
show router ospf
show router bgp
```
