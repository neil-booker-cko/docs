# BGP Best Practices

BGP operational best practices encompass route aggregation, filtering, community tagging, local
preference
tuning, and convergence monitoring. Proper implementation dramatically reduces interdomain routing
failures, prevents route leaks, and improves failover speed.

---

## Quick Reference Checklist

| Decision | Best Practice |
| --- | --- |
| **Route Aggregation** | Summarize to classless boundaries; use summarize keyword in Cisco, aggregate-address in FortiGate |
| **AS-Path Filtering** | Inbound: prepend to deprioritize; outbound: deny misconfigured paths (invalid length, loops) |
| **Communities** | Tag all routes in policy group; use RFC 1997 standard (0-65535:0-65535) format |
| **Local Preference** | Primary ISP 200; secondary 100; preferred internal routes 300+ |
| **MED Tuning** | Set on routes entering network; only compared between same peer AS |
| **Graceful Shutdown** | Enable Community 65535:0; tune hold timer and BGP timers for < 3 sec convergence |
| **Convergence Monitoring** | Alert on route count drop >10%; monitor convergence time with BFD timers = 300/900 ms |
| **Common Mistakes** | Missing filters allow bogus routes; suboptimal aggregation wastes space; MED wars from misconfigured timers |

---

## 1. Overview: When & Why to Apply Best Practices

### Why BGP Optimization Matters

BGP is the internet's routing protocol and runs on enterprise WAN edges, data center
interconnects, and cloud gateways. Misconfiguration cascades:

```text
Scenario: Missing outbound filtering

  - Your network advertises 0.0.0.0/0 by mistake
  - ISP accepts and amplifies the route
  - Internet converges to your network for all traffic
  - Your WAN link is overwhelmed
  - Downstream customers lose connectivity

Scenario: Suboptimal aggregation

  - 100 individual /26 subnets advertised instead of 1 /24
  - Peers carry 100 route objects vs 1
  - RIB size grows; CPU and memory increase
  - ISPs may rate-limit or filter you

Scenario: No graceful shutdown

  - Link drops; BGP session crashes without warning
  - Convergence time = hold timer (180 seconds default)
  - Customer traffic blackholed for 3+ minutes
```

### Design Pattern: Layered Filtering

Best practice is to implement 3 layers of filters:

```text
Layer 1: Inbound (from peers)

  - Accept only prefixes that should arrive from this peer
  - Block invalid ASNs, excessive path length, martians

Layer 2: Internal (iBGP policy)

  - Tag routes with community
  - Set local preference based on route source

Layer 3: Outbound (to peers)

  - Advertise only authorized prefixes for this peer
  - Do not leak customer or internal routes to competitors
```

---

## 2. Route Aggregation: Summarization Strategies

### CIDR Optimization Principles

Route aggregation reduces the number of prefixes advertised to peers, saving memory and convergence
time.

#### Rule 1: Aggregate to natural CIDR boundaries

```text
DO NOT advertise:
  203.0.113.0/25  (Bad: arbitrary subnet)
  203.0.113.128/25

DO advertise:
  203.0.113.0/24  (Good: natural /24 boundary)
```

#### Rule 2 - Aggregate only when you own the entire superblock

```text
Scenario: You own 203.0.113.0/24 via assignments:
  203.0.113.0/26 -> Customer A
  203.0.113.64/26 -> Customer B
  203.0.113.128/26 -> Unused
  203.0.113.192/26 -> Unused

Decision: Aggregate to 203.0.113.0/24 only if all 4 /26s are yours
(If Customer A left and you reallocated their space, you can aggregate)
```

#### Rule 3: Do not aggregate routes you don't originate

```text
Bad (route leaking):

  - Peer sends you 10.0.0.0/8
  - You aggregate and re-advertise 10.0.0.0/8 to other peers
  - You become the path to that prefix (not your responsibility)

Good (pass-through):

  - Accept the /8 and advertise exactly as received
  - If you want to summarize internal routes, only do so for routes you originate
```

### Cisco IOS-XE Aggregation

#### Static aggregation (always advertised)

```ios
router bgp 65001
  bgp log-neighbor-changes
  aggregate-address 203.0.113.0 255.255.255.0 summary-only
  ! summary-only suppresses the longer prefixes (210.0.113.0/25, etc.)
end
```

#### Conditional aggregation (only when more specifics exist)

```ios
router bgp 65001
  aggregate-address 203.0.113.0 255.255.255.0 summary-only
  ! Without summary-only, both the /24 and /25 are advertised
  ! Useful if you want to leak longer prefixes to some peers
end
```

#### Aggregate with AS-path prepending (deprioritize)

```ios
router bgp 65001
  aggregate-address 203.0.113.0 255.255.255.0 as-set
  ! as-set: include all ASNs from more-specific routes
  ! Prevents loops if more-specifics are received from multiple peers
end
```

### FortiGate Aggregation

**Static aggregation:**

```fortios
config router bgp
  set as 65001
  config aggregate-address
    edit 1
      set prefix 203.0.113.0 255.255.255.0
      set summary-only enable
    next
  end
end
```

**Aggregate with AS-path modification:**

```fortios
config router bgp
  set as 65001
  config aggregate-address
    edit 1
      set prefix 203.0.113.0 255.255.255.0
      set as-set enable
    next
  end
end
```

### Monitoring Aggregation Effectiveness

#### Cisco Check if aggregates are being advertised

```ios
show ip bgp neighbors <peer-ip> advertised-routes | include 203.0.113.0
```

#### FortiGate Verify aggregate routes

```fortios
diagnose ip bgp network print | grep "203.0.113"
```

#### Rule of thumb You should see 1 /24 advertised per customer block, not 4 /26s

---

## 3. AS-Path Filtering: Inbound & Outbound Patterns

### Inbound AS-Path Filtering

Inbound filtering protects your network from bogus BGP announcements.

#### Pattern 1: Reject routes with too many hops (possible loop or hijack)

```text
Valid path (direct peer): 65000 65001 65002
Valid path (3 hops):     65000 65001 65002 65003

Suspicious (>10 hops):   65000 65001 65002 65003 65004 65005 65006 65007 65008 65009 65010

  - May indicate a loop or an intentional hijack
  - Most legitimate routes have <5 hops
```

#### Cisco Reject AS-path longer than 10

```ios
router bgp 65000
  neighbor 203.0.113.1 remote-as 65001
  neighbor 203.0.113.1 route-map INBOUND-FILTER in
end

route-map INBOUND-FILTER permit 10
  match as-path-length le 10
  set local-preference 100
end

route-map INBOUND-FILTER deny 20
end

ip as-path access-list 1 permit ^65001_
  ! Permits only direct peers from AS 65001
```

#### FortiGate Reject long AS-paths

```fortios
config router bgp
  set as 65000
  config neighbor
    edit "203.0.113.1"
      set remote-as 65001
      set route-map-in "INBOUND-FILTER"
    next
  end
end

config router route-map
  edit "INBOUND-FILTER"
    config rule
      edit 1
        set match-aspath "LONG-PATH"
        set action deny
      next
      edit 2
        set action permit
      next
    end
  next
end

config router aspath-list
  edit "LONG-PATH"
    config rule
      edit 1
        set regexp "^65001.*65001.*65001.*65001.*65001.*65001.*65001.*65001.*65001.*65001"
      next
    end
  next
end
```

#### Pattern 2: Reject routes with your own ASN (loop detection)

```text
Receive: 65000 65001 65000 203.0.113.0/24
Issue: Your AS appears twice (loop)
Action: Reject immediately
```

#### Cisco Reject routes containing your own ASN

```ios
route-map INBOUND-FILTER deny 5
  match as-path 1
end

route-map INBOUND-FILTER permit 10
  match as-path-length le 10
end

ip as-path access-list 1 permit _65000_
  ! Rejects any route with 65000 in the path
```

#### FortiGate Reject self-originated ASNs

```fortios
config router aspath-list
  edit "SELF-LOOP"
    config rule
      edit 1
        set regexp "65000"
      next
    end
  next
end

config router route-map
  edit "INBOUND-FILTER"
    config rule
      edit 1
        set match-aspath "SELF-LOOP"
        set action deny
      next
    end
  next
end
```

### Outbound AS-Path Filtering

Outbound filtering prevents your network from advertising routes you shouldn't own.

#### Pattern: Only advertise routes you originated or learned from appropriate peers

```text
Your AS: 65000
Peers:

  - Upstream ISP (ASN 65100): Accept all their routes, advertise back only customer routes
  - Customer A (ASN 65001): Accept their routes, advertise them to ISP but NOT to other customers

Route: 10.0.0.0/8 from Customer A

  - Advertise to ISP 65100? YES (transit)
  - Advertise to Customer B (ASN 65002)? NO (customer isolation)
```

#### Cisco Advertise only customer routes to upstream ISP

```ios
router bgp 65000
  neighbor 203.0.113.1 remote-as 65100      ! Upstream ISP
  neighbor 203.0.113.1 route-map UPSTREAM-OUT out

  neighbor 203.0.113.5 remote-as 65001      ! Customer A
  neighbor 203.0.113.5 route-map CUSTOMER-A-OUT out
end

route-map UPSTREAM-OUT permit 10
  match community CUSTOMER-ROUTES
end

route-map UPSTREAM-OUT deny 20
end

route-map CUSTOMER-A-OUT permit 10
  match community CUSTOMER-A-ROUTES
  set as-path prepend 65000
end

route-map CUSTOMER-A-OUT deny 20
end

ip community-list 1 permit 65000:1001
  ! Customer route tag
ip community-list 2 permit 65000:1002
  ! Customer A specific tag
```

#### FortiGate Outbound filtering

```fortios
config router bgp
  set as 65000
  config neighbor
    edit "203.0.113.1"
      set remote-as 65100
      set route-map-out "UPSTREAM-OUT"
    next
    edit "203.0.113.5"
      set remote-as 65001
      set route-map-out "CUSTOMER-A-OUT"
    next
  end
end

config router route-map
  edit "UPSTREAM-OUT"
    config rule
      edit 1
        set match-community "CUSTOMER-ROUTES"
        set action permit
      next
      edit 2
        set action deny
      next
    end
  next
  edit "CUSTOMER-A-OUT"
    config rule
      edit 1
        set match-community "CUSTOMER-A-ROUTES"
        set action permit
      next
      edit 2
        set action deny
      next
    end
  next
end

config router community-list
  edit "CUSTOMER-ROUTES"
    config rule
      edit 1
        set action permit
        set match "65000:1001"
      next
    end
  next
end
```

---

## 4. Community Tagging: Standard & Well-Known Communities

### RFC 1997 Standard Communities

Communities are 32-bit values (AS:value) used to tag routes for policy application.

| Community | Meaning | Behavior |
| --- | --- | --- |
| **0:x** | No export (well-known) | Do not advertise to any peer |
| **65535:0** | Graceful shutdown (well-known) | Withdraw route gracefully during maintenance |
| **65535:1** | Blackhole (well-known) | Drop matching traffic (used for DDoS mitigation) |
| **Custom: 65000:1001** | Customer A routes | Allows selective re-advertisement |
| **Custom: 65000:1002** | Customer B routes | Allows selective re-advertisement |
| **Custom: 65000:2001** | Internal routes | High local preference |

### Community Tagging Strategy

#### Step 1: Define your community policy

```text
Community definitions for ASN 65000:
  65000:100  = Low priority (peer-learned routes)
  65000:200  = Medium priority (customer routes)
  65000:300  = High priority (internal routes)
  65000:1001 = Customer A routes (tag for selective advertisement)
  65000:1002 = Customer B routes (tag for selective advertisement)
  65000:2001 = Internal management routes (do not export)
```

#### Step 2: Apply communities to routes as they enter the network

#### Cisco Tag customer routes on ingress

```ios
router bgp 65000
  neighbor 203.0.113.5 remote-as 65001  ! Customer A
  neighbor 203.0.113.5 route-map TAG-CUSTOMER-A in
end

route-map TAG-CUSTOMER-A permit 10
  set community 65000:200 65000:1001 additive
  ! additive: keep existing communities and add these
end
```

#### Cisco Tag internal routes

```ios
router bgp 65000
  bgp log-neighbor-changes
  network 10.0.0.0 mask 255.255.255.0 route-map TAG-INTERNAL
end

route-map TAG-INTERNAL permit 10
  set community 65000:300 65000:2001 additive
end
```

#### FortiGate Tag customer routes

```fortios
config router bgp
  set as 65000
  config neighbor
    edit "203.0.113.5"
      set remote-as 65001
      set route-map-in "TAG-CUSTOMER-A"
    next
  end
end

config router route-map
  edit "TAG-CUSTOMER-A"
    config rule
      edit 1
        set set-community "65000:200 65000:1001"
        set action permit
      next
    end
  next
end
```

#### FortiGate Tag internal routes

```fortios
config router bgp
  set as 65000
  config network
    edit 1
      set prefix 10.0.0.0 255.255.255.0
      set route-map "TAG-INTERNAL"
    next
  end
end

config router route-map
  edit "TAG-INTERNAL"
    config rule
      edit 1
        set set-community "65000:300 65000:2001"
        set action permit
      next
    end
  next
end
```

### Policy Application Using Communities

#### Use communities to control advertisement

```text
Rule: Advertise Customer A routes to ISP, but not to other customers

Outbound to ISP (ASN 65100):

  - Accept routes tagged 65000:200 (customer routes)
  - Advertise them

Outbound to other customers (ASN 65002, etc.):

  - Deny routes tagged 65000:1001 (Customer A specific)
  - Do not advertise Customer A routes to other customers
```

#### Cisco

```ios
route-map ADVERTISE-TO-ISP permit 10
  match community 65000:200
end

route-map ADVERTISE-TO-CUSTOMER-B deny 10
  match community 65000:1001
end

route-map ADVERTISE-TO-CUSTOMER-B permit 20
  match community 65000:200
end
```

#### FortiGate

```fortios
config router route-map
  edit "ADVERTISE-TO-ISP"
    config rule
      edit 1
        set match-community "CUSTOMER-ROUTES"
        set action permit
      next
    end
  next
  edit "ADVERTISE-TO-CUSTOMER-B"
    config rule
      edit 1
        set match-community "CUSTOMER-A"
        set action deny
      next
      edit 2
        set match-community "CUSTOMER-ROUTES"
        set action permit
      next
    end
  next
end

config router community-list
  edit "CUSTOMER-A"
    config rule
      edit 1
        set action permit
        set match "65000:1001"
      next
    end
  next
  edit "CUSTOMER-ROUTES"
    config rule
      edit 1
        set action permit
        set match "65000:200"
      next
    end
  next
end
```

---

## 5. Local Preference Tuning: Primary/Secondary ISP

### Local Preference Design

Local preference (default 100) controls which peer is preferred for routes learned from multiple
peers.
Higher value = preferred.

#### Scenario Dual ISP setup

```text
Network: 65000
ISP1 (Primary): 203.0.113.1 (ASN 65100)
ISP2 (Secondary): 210.0.113.1 (ASN 65101)

Route received from both ISPs: 8.8.8.0/24 (Google DNS)

Desired behavior:

  - Outbound traffic for 8.8.8.0/24 via ISP1 (primary)
  - Failover to ISP2 if ISP1 is unreachable
```

#### Solution Set local preference

| Peer | AS | Local Preference | Role |
| --- | --- | --- | --- |
| ISP1 | 65100 | 200 | Primary (preferred) |
| ISP2 | 65101 | 100 | Secondary (backup) |
| Customer A | 65001 | 250 | Do not use for transit |
| Customer B | 65002 | 250 | Do not use for transit |
| iBGP peer | 65000 | 300 | Local routes highest priority |

#### Cisco Set local preference on inbound route-map

```ios
router bgp 65000
  neighbor 203.0.113.1 remote-as 65100    ! ISP1
  neighbor 203.0.113.1 route-map ISP1-IN in

  neighbor 210.0.113.1 remote-as 65101    ! ISP2
  neighbor 210.0.113.1 route-map ISP2-IN in

  neighbor 10.0.0.2 remote-as 65000       ! iBGP peer
  neighbor 10.0.0.2 route-map IBGP-IN in
end

route-map ISP1-IN permit 10
  set local-preference 200
end

route-map ISP2-IN permit 10
  set local-preference 100
end

route-map IBGP-IN permit 10
  set local-preference 300
end
```

#### FortiGate Set local preference

```fortios
config router bgp
  set as 65000
  config neighbor
    edit "203.0.113.1"
      set remote-as 65100
      set route-map-in "ISP1-IN"
    next
    edit "210.0.113.1"
      set remote-as 65101
      set route-map-in "ISP2-IN"
    next
  end
end

config router route-map
  edit "ISP1-IN"
    config rule
      edit 1
        set set-local-preference 200
        set action permit
      next
    end
  next
  edit "ISP2-IN"
    config rule
      edit 1
        set set-local-preference 100
        set action permit
      next
    end
  next
end
```

### Failover Testing

#### Cisco Verify local preference is applied

```ios
show ip bgp 8.8.8.0/24
  BGP routing table entry for 8.8.8.0/24, version X
  Paths: (2 available, best #1, table default)
    65100 65002
      203.0.113.1 from 203.0.113.1 (203.0.113.1)
        Origin IGP, metric 0, localpref 200, valid, external, best  <-- Highest pref

    65101 65002
      210.0.113.1 from 210.0.113.1 (210.0.113.1)
        Origin IGP, metric 0, localpref 100, valid, external
```

#### FortiGate Check local preference

```fortios
diagnose ip bgp network print | grep "8.8.8.0"
diagnose ip bgp neighbor 203.0.113.1 advertised-routes | grep "pref"
```

---

## 6. MED Manipulation: Controlling Peer Preference

### MED Overview

Multi-Exit Discriminator (MED) influences the peer's choice of entry points to your network. Unlike
local preference, MED is only compared between routes learned from the same peer AS.

#### Scenario Single ISP, dual connections

```text
Network: 65000
ISP: 65100 (ASN)

Connections:

  - Link1 (primary): 203.0.113.1
  - Link2 (backup): 203.0.113.5

ISP perspective:
  ISP learns 10.0.0.0/8 from both links
  Without MED: arbitrary choice (may pick Link2)
  With MED: use Link1 (lower MED value preferred)

Solution: Set MED=100 on Link1, MED=200 on Link2
```

### MED Best Practices

#### Rule 1: Lower MED = preferred entry point

```text
Route: 10.0.0.0/8 from network 65000
Received from ISP 65100 via two paths:

Path 1 (Link1): MED=100 <-- PREFERRED (lower value)
Path 2 (Link2): MED=200
```

#### Rule 2: MED only compares within the same peer AS

```text
Scenario: Routes from ISP1 (65100) vs ISP2 (65101)
  ISP1 advertises 8.8.8.0/24 with MED=50
  ISP2 advertises 8.8.8.0/24 with MED=10

Decision: ISP1 is chosen (local preference takes priority, not MED)
MED only used to compare ISP1-path1 vs ISP1-path2
```

#### Rule 3: Set MED on routes you advertise (outbound), not routes you receive

```text
Correct: Set MED on 10.0.0.0/8 when advertising to ISP

  - ISP learns the route with MED value
  - ISP uses it to decide which of your links to use

Incorrect: Set MED on routes received from ISP

  - Does not affect ISP's behavior
  - Only affects your internal routing (pointless)
```

### Cisco MED Configuration

#### Set MED on outbound routes (advertise to ISP)

```ios
router bgp 65000
  neighbor 203.0.113.1 remote-as 65100       ! Link1 (primary)
  neighbor 203.0.113.1 route-map LINK1-OUT out

  neighbor 203.0.113.5 remote-as 65100       ! Link2 (backup, same ISP)
  neighbor 203.0.113.5 route-map LINK2-OUT out
end

route-map LINK1-OUT permit 10
  match ip address prefix-list OUR-ROUTES
  set metric 100          ! Lower metric = preferred
end

route-map LINK2-OUT permit 10
  match ip address prefix-list OUR-ROUTES
  set metric 200          ! Higher metric = less preferred
end

ip prefix-list OUR-ROUTES seq 10 permit 10.0.0.0/8
ip prefix-list OUR-ROUTES seq 20 permit 10.1.0.0/16
```

#### Verify MED is advertised

```ios
show ip bgp neighbors 203.0.113.1 advertised-routes
  ...10.0.0.0/8    best (metric 100)
```

### FortiGate MED Configuration

#### Set MED on outbound routes

```fortios
config router bgp
  set as 65000
  config neighbor
    edit "203.0.113.1"
      set remote-as 65100
      set route-map-out "LINK1-OUT"
    next
    edit "203.0.113.5"
      set remote-as 65100
      set route-map-out "LINK2-OUT"
    next
  end
end

config router route-map
  edit "LINK1-OUT"
    config rule
      edit 1
        set match-ip-address "OUR-ROUTES"
        set set-metric 100
        set action permit
      next
    end
  next
  edit "LINK2-OUT"
    config rule
      edit 1
        set match-ip-address "OUR-ROUTES"
        set set-metric 200
        set action permit
      next
    end
  next
end

config router prefix-list
  edit "OUR-ROUTES"
    config rule
      edit 1
        set prefix 10.0.0.0/8
        set action permit
      next
      edit 2
        set prefix 10.1.0.0/16
        set action permit
      next
    end
  next
end
```

### MED Wars: Common Pitfall

#### Pitfall: Both sides setting MED aggressively

```text
Scenario: You and ISP both set MED on routes you advertise

Your perspective:
  You advertise 10.0.0.0/8 with MED=100 (Link1 preferred)
  ISP should prefer Link1

ISP perspective:
  ISP advertises 8.8.8.0/24 with MED=10 (via ISP backbone)
  You learn it with MED=10

Problem:
  ISP uses YOUR MED (100) to choose your link (correct)
  You use ISP's MED (10) to choose ISP's link (pointless; ISP is ISP)
  MED is now meaningless for inbound traffic

Solution:
  Only one side sets MED (typically the origin AS, not the transit ISP)
  ISP ignores MED from customers; customers ignore MED from ISP
```

---

## 7. Graceful Shutdown: Shutdown Communities

### RFC 8326 Graceful Shutdown Community

Graceful shutdown allows controlled route withdrawal without flapping the BGP session.

**Without graceful shutdown:**

```text
Event: Planned maintenance on ISP link
Action: Disable BGP on link
Result: BGP session crashes
        Hold timer starts (180 seconds)
        Peers wait 180 seconds before converging to backup link
        Downtime = 180+ seconds
```

**With graceful shutdown:**

```text
Event: Planned maintenance on ISP link
Action: Set community 65535:0 on all advertised routes
        Keep BGP session UP
Result: Peers see community 65535:0 (no export)
        Peers immediately withdraw routes
        Convergence in <1 second
        Planned 30-second maintenance window with <1 second traffic impact
```

### Implementation

#### Cisco Enable graceful shutdown before maintenance

```ios
router bgp 65000
  neighbor 203.0.113.1 remote-as 65100
  neighbor 203.0.113.1 route-map PRE-MAINTENANCE out
end

! Apply during maintenance:
route-map PRE-MAINTENANCE permit 10
  set community 65535:0 additive
end

! Remove after maintenance:
route-map PRE-MAINTENANCE permit 10
  set local-preference 200
end
```

#### FortiGate Graceful shutdown community

```fortios
config router route-map
  edit "PRE-MAINTENANCE"
    config rule
      edit 1
        set set-community "65535:0"
        set action permit
      next
    end
  next
end

config router bgp
  set as 65000
  config neighbor
    edit "203.0.113.1"
      set remote-as 65100
      set route-map-out "PRE-MAINTENANCE"
    next
  end
end
```

### Convergence Tuning for Graceful Shutdown

Reduce hold timer and BGP timers to achieve sub-3-second convergence:

#### Cisco Fast convergence timers

```ios
router bgp 65000
  neighbor 203.0.113.1 remote-as 65100
  neighbor 203.0.113.1 timers 3 9      ! Keepalive 3s, hold 9s
  neighbor 203.0.113.1 timers connect 10
  ! BGP session established in ~15 seconds max
end
```

#### FortiGate BGP timers

```fortios
config router bgp
  set as 65000
  config neighbor
    edit "203.0.113.1"
      set remote-as 65100
      set keepalive-timer 3
      set holdtime-timer 9
    next
  end
end
```

---

## 8. Monitoring: Advertised/Received Routes & Convergence

### Key Metrics to Monitor

| Metric | Alert Threshold | Purpose |
| --- | --- | --- |
| **Advertised route count** | Drop >10% | Detect route leak or withdrawal |
| **Received route count** | Drop >10% or >100 new | Detect peer flapping or leak |
| **BGP session state** | Any state != Established | Detect connectivity loss |
| **Convergence time** | >30 seconds | Detect slow convergence or hold timer issues |
| **Duplicate routes** | Any | Detect routing loops or misconfiguration |

### Monitoring Commands

#### Cisco Check route counts

```ios
show ip bgp neighbors 203.0.113.1 | include "advertised\|received"
  Prefixes advertised 250
  Prefixes received 50000

show ip bgp summary | include "Neighbor"
  Neighbor        V    AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State
  203.0.113.1     4 65100   45000   45001   123456    0    0 2d03h    Established
```

#### Monitor convergence time after failover

```ios
! Enable BGP logging:
router bgp 65000
  bgp log-neighbor-changes
  ! Log shows: BGP-5-ADJCHANGE: neighbor 203.0.113.1 Up/Down events
end

! Check BGP log for timestamps:
show log | include "BGP.*ADJCHANGE"
  Jul 15 10:00:05: %BGP-5-ADJCHANGE: neighbor 203.0.113.1 Down
  Jul 15 10:00:08: %BGP-5-ADJCHANGE: neighbor 203.0.113.1 Up
  ! Convergence time = 3 seconds (good)
```

#### FortiGate Check route counts

```fortios
diagnose ip bgp summary print
diagnose ip bgp network print | wc -l      ! Total routes

! Check route counts from specific neighbor:
diagnose ip bgp neighbor 203.0.113.1 advertised-routes | wc -l
diagnose ip bgp neighbor 203.0.113.1 received-routes | wc -l
```

#### FortiGate Monitor session state

```fortios
diagnose ip bgp neighbors print | grep "203.0.113.1" -A 10
  Neighbor: 203.0.113.1
  Remote AS: 65100
  BGP State: Established
  Uptime: 2d 03h
```

### Automated Monitoring Setup

#### Create alerts in your NMS (Nagios/Zabbix/Prometheus)

```text
Alert Rule: BGP route count drop >10%
  Baseline: 50,000 routes
  Threshold: 45,000 routes (10% drop)
  Action: Page on-call engineer

Alert Rule: BGP session down
  Condition: BGP state != Established
  Duration: 30+ seconds
  Action: Page immediately

Alert Rule: Convergence time >30 seconds
  Condition: Route change detected, new state reached >30s later
  Action: Alert; review timers and check for hold timer issues
```

---

## 9. Common Mistakes & Mitigation

### Mistake 1: Missing Inbound Filters

**Problem:**

```text
Received route: 0.0.0.0/0 (entire internet)
Action: Advertised to upstream ISP
Result: All internet traffic sent to your network
Impact: WAN link overwhelmed; customer network unreachable
```

**Mitigation:**

```text

1. Inbound route-map on ALL external neighbors
1. Match only expected prefixes (use prefix-list)
1. Deny all others explicitly

Cisco:
  route-map INBOUND-FILTER deny 20
  ! Implicit deny, but explicit is safer

FortiGate:
  config rule
    edit 2
      set action deny
    next
  end
```

### Mistake 2: Suboptimal Route Aggregation

**Problem:**

```text
Advertised: 100 individual /26 subnets (instead of 1 /24)
Peer impact: 100x route table entries
ISP response: Rate-limiting or filtering your routes
```

**Mitigation:**

```text

1. Audit all advertised prefixes
1. Identify aggregatable subnets (contiguous, same AS path)
1. Summarize to natural CIDR boundaries
1. Monitor: Routes advertised should be 5-10% of internal routes
```

### Mistake 3: MED Wars (Both Sides Setting MED)

**Problem:**

```text
Your setting: MED=100 on your routes to ISP (correct)
ISP setting: MED=10 on their routes to you (counterproductive)
Result: MED becomes meaningless; route selection arbitrary
```

**Mitigation:**

```text

1. Policy: Only the origin AS sets MED (typically not ISP)
1. Inbound: Ignore MED from peers (do not set on received routes)
1. Outbound: Set MED to influence peer's ingress path selection
1. Document: Which AS is responsible for MED in multi-peer topology
```

### Mistake 4: Missing AS-Path Validation

**Problem:**

```text
Receive: 65001 65002 65003 65003 65003 65003 203.0.113.0/24
Issue: AS 65003 appears 4 times (loop or hijack)
Action: Accept and advertise to other peers
Result: Possible route hijack accepted
```

**Mitigation:**

```text

1. Max AS-path length filter (deny >10 hops)
1. Reject routes with own ASN (self-loop detection)
1. Community-based filtering for known-good peers
1. Outbound: Only advertise routes with reasonable AS-paths
```

### Mistake 5: Flapping Routes (BGP Session Instability)

**Problem:**

```text
Event: BGP session flaps (up/down/up/down) every 30 seconds
Cause: Hold timer too short, network instability, or CPU spike
Result: All routes from peer continuously re-advertised
Impact: CPU spike on all routers; convergence delays
```

**Mitigation:**

```text

1. Check hold timer: show ip bgp neighbors <peer> | grep "Hold time"
   Should be >=90 seconds (default 180 recommended)

1. Monitor for dampening: Some peers use route dampening
   Flapping routes are penalized and suppressed

1. Check interface stability: show interface <intf> | grep "flaps"
   Interface flaps cause BGP flaps

1. Check CPU: show processes cpu sorted
   High CPU can cause keepalive loss and flapping
```

---

## 10. Verification & Testing

### Pre-Deployment Checklist

- [ ] Inbound route-map applied to all external BGP neighbors
- [ ] Outbound route-map applied to all external BGP neighbors
- [ ] Community policy documented (AS:value meanings)
- [ ] Local preference values assigned (primary >secondary)
- [ ] MED values set on outbound routes (if applicable)
- [ ] Route aggregation configured (only natural CIDR boundaries)
- [ ] Graceful shutdown community (65535:0) tested in lab
- [ ] BGP timers optimized for convergence (if <30 sec required)
- [ ] No duplicate routes in RIB (show ip bgp duplicates)
- [ ] No self-loops in advertised routes

### Post-Deployment Testing

**Failover test:**

```text
Step 1: Baseline
  Advertised routes: 250
  Session state: Established
  Convergence test: Withdraw route, measure time to re-advertise

Step 2: Bring down primary ISP link
  Monitor: Route count change, session state
  Measure: Time to failover (should be <30 sec with fast timers)

Step 3: Restore primary ISP link
  Monitor: Route re-advertisement
  Verify: Primary link preferred again (local preference honored)
```

**Community tagging verification:**

```ios
show ip bgp 10.0.0.0/24
  Community: 65000:300 65000:2001
  ! Verify both communities present
```

**Aggregation verification:**

```ios
show ip bgp neighbors 203.0.113.1 advertised-routes | grep "^65000"
  Network        Next Hop      Metric LocPrf Weight Path
  10.0.0.0/8     0.0.0.0            0 100    32768 i
  ! Verify /8 is advertised, not 4 /26s
```

---

## References

- [BGP Path Selection](../reference/bgp_path_selection.md)
- [BGP Communities](../reference/bgp_communities.md)
- [Cisco BGP Configuration](../cisco/cisco_bgp_ibgp.md)
- [FortiGate BGP Configuration](../fortigate/fortigate_bgp_config.md)
- [BGP Troubleshooting](bgp_troubleshooting.md)
- [Routing Protocols: BGP](../routing/bgp.md)
