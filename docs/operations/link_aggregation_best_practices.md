# Link Aggregation (LAG/EtherChannel) Best Practices

Link aggregation (LAG) combines multiple physical links into a single logical interface, providing
increased bandwidth and redundancy. Proper implementation requires consistent speed/duplex matching,
LACP negotiation tuning, and careful load distribution across member ports.

---

## Quick Reference Checklist

| Decision | Best Practice |
| --- | --- |
| **Mode Selection** | LACP (active/passive) preferred; static mode only if peer doesn't support LACP |
| **Speed/Duplex** | All member ports MUST match exactly (1 Gbps, full-duplex for all) |
| **System Priority** | Lower is preferred; typically 32768 (default) acceptable |
| **Port Priority** | Lower is preferred; no impact with symmetric links (same speed) |
| **Hash Algorithm** | Layer 3 (source/dest IP) for L3; Layer 2 (MAC) for L2 switching |
| **Load Distribution** | Expected: Equal distribution across N members (e.g., 5 ports = 20% each) |
| **STP Interaction** | LAG is single logical link; STP treats as one port; no per-member blocking |
| **Monitoring** | Monitor member port status; alert if port down or mismatched speed |
| **Common Mistakes** | Mixed speeds (1G + 100M), LACP negotiation failures, unequal load distribution |

---

## 1. Overview: When to Aggregate Links

### Why Link Aggregation Matters

```text
Single 1 Gbps link:
  Bandwidth: 1 Gbps
  If fails: No connectivity (single point of failure)

2x 1 Gbps links aggregated (LAG):
  Bandwidth: 2 Gbps (combined)
  If 1 fails: 1 Gbps still available (redundant)
  Load balancing: Traffic distributed across both
```

### LAG Use Cases

| Use Case | Design | Benefit |
| --- | --- | --- |
| **Server uplink** | 4x 10 Gbps LAG | 40 Gbps + redundancy; any link can fail |
| **Data center interconnect** | 8x 100 Gbps LAG | 800 Gbps; fault-tolerant |
| **Campus access** | 2x 1 Gbps LAG | 2 Gbps; if 1 fails, 1 Gbps remains |
| **Backbone link** | 16x 100 Gbps LAG | 1.6 Tbps; carrier-grade redundancy |

### LAG vs Link Bonding vs ECMP

| Feature | LAG | ECMP (BGP) | Port Channel |
| --- | --- | --- | --- |
| **Scope** | Local switching/routing | Inter-router routing | Cisco term for LAG |
| **Bandwidth** | Combined (4x1G = 4G) | Per-flow per-path (1x1G per flow) | Same as LAG |
| **Transparent** | Yes (single MAC) | No (different next-hops) | Yes |
| **STP** | Single logical port | Multiple routes | Single logical port |
| **Common Use** | Access layer | WAN/eBGP | Access/distribution |

---

## 2. LACP vs Static Mode

### LACP (Link Aggregation Control Protocol) - Recommended

#### Characteristics

```text
Dynamic negotiation: Routers agree on LAG membership
Protocol: IEEE 802.3ad (standardized)
Discovery: Automatic; hello packets every 30 seconds (slow mode) or 1 second (fast mode)
Benefit: Detects misconfiguration automatically
Downside: Requires peer support
Recommended: Use LACP for all new deployments
```

#### LACP states

```text
Active: Initiates LACP negotiation (desired)
Passive: Waits for peer to initiate (acceptable)
```

#### Active/Passive combinations

| Local | Peer | Result |
| --- | --- | --- |
| Active | Active | LACP forms (both sides initiating) |
| Active | Passive | LACP forms (one side initiating) |
| Passive | Passive | LACP fails (neither initiates) |
| Static | Static | LAG forms (no negotiation) |
| LACP | Static | Fails (incompatible) |

#### Cisco LACP configuration

```ios
! Channel group with LACP (active mode)
interface GigabitEthernet0/0
  channel-group 1 mode active          ! LACP active
  no shutdown
end

interface GigabitEthernet0/1
  channel-group 1 mode active
  no shutdown
end

interface Port-channel1
  ip address 10.0.1.1 255.255.255.0
  no shutdown
end

! Verify:
show etherchannel 1 summary
  Flags: D - down        P - bundled in port-channel
         I - stand-alone s - suspended
         H - Hot standby (LACP only)
         R - Layer3      S - Layer2
         U - in use      f - failed to allocate aggregator
         M - not in use, minimum links not met
         u - unsuitable for bundling
         w - waiting to be aggregated
         d - default port

  Number of channel-groups in use: 1
  Number of aggregators:           1

  Group  Port-channel  Protocol    Ports

  ------+-------------+-----------+-----------------------------------------------
  1      Po1(RU)          LACP      Gi0/0(P)   Gi0/1(P)

  ! P = bundled in port-channel (active)
```

#### FortiGate LACP configuration

```fortios
config system interface
  edit "port1"
    set aggregate members "port1"
  next
  edit "port2"
    set aggregate members "port1"   ! Both ports to same aggregate
  next
end

config system interface
  edit "port1"
    set type aggregate
    set member "port1" "port2"
    set lacp-mode active
  next
end
```

### Static Mode (Legacy, Not Recommended)

#### Characteristics

```text
Manual configuration: No negotiation; must match on both sides
Discovery: None; if peer has different config, LAG is silent failure
Benefit: Simple; no negotiation overhead (minimal)
Downside: Easy to misconfigure; silent failures
Recommended: Only if peer doesn't support LACP (rare after 2010)
```

#### Cisco static LAG

```ios
interface GigabitEthernet0/0
  channel-group 1 mode on              ! Static mode (no negotiation)
end

interface GigabitEthernet0/1
  channel-group 1 mode on
end

interface Port-channel1
  ip address 10.0.1.1 255.255.255.0
end

! Risk: If peer has different static config or is down,
!       port-channel may be active but non-functional
```

---

## 3. Member Port Speed & Duplex Matching

### The Requirement: All Ports Must Match

#### Rule - All member ports must have identical speed and duplex

```text
Correct:
  Port 1: 1 Gbps, Full-duplex
  Port 2: 1 Gbps, Full-duplex
  Port 3: 1 Gbps, Full-duplex
  LAG operational: All ports active

Incorrect:
  Port 1: 1 Gbps, Full-duplex
  Port 2: 100 Mbps, Full-duplex
  Port 3: 1 Gbps, Full-duplex
  LAG will form, but:

    - Effective bandwidth = slowest port (100 Mbps)
    - Traffic hash may distribute unevenly
    - Risk of congestion on Port 2
```

#### Another incorrect scenario

```text
Port 1: 1 Gbps, Full-duplex
Port 2: 1 Gbps, Half-duplex
LAG forms, but:

  - Half-duplex can only send OR receive at a time (not both)
  - Full-duplex expects simultaneous send/receive
  - Collisions and retransmissions occur
  - Effective throughput drops 50%
```

### Detection: Speed/Duplex Verification

#### Cisco - Check port speeds

```ios
show interface GigabitEthernet0/0
  GigabitEthernet0/0 is up, line protocol is up (connected)
    Hardware is Gigabit Ethernet, address is abcd.ef12.3456 (bia abcd.ef12.3456)
    Internet address is 10.0.1.1/24
    MTU 1500 bytes, BW 1000000 Kbit/sec, DLY 10 usec
    encapsulation ARPA, loopback not set
    Full-duplex, 1000Mb/s, media type is RJ45

show etherchannel 1 port-channel
  Port-channel1 (Primary aggregator)
    Age of the Port-channel = 00d:00h:05m:20s
    Logical slot/port = 16/1 Number of ports = 2
    GigabitEthernet0/0
    GigabitEthernet0/1
```

#### FortiGate - Verify aggregate port status

```fortios
diagnose system interface list
  name=port1 alias=port1 index=3
  status=up speed=1000Mbps/full-duplex mtu=1500

  name=port2 alias=port2 index=4
  status=up speed=1000Mbps/full-duplex mtu=1500

  (Both ports have matching speed/duplex)
```

### Mitigation: Force Speed/Duplex

#### Cisco - Configure explicit speed and duplex

```ios
interface GigabitEthernet0/0
  speed 1000                ! Force 1 Gbps
  duplex full               ! Force full-duplex
  channel-group 1 mode active
end

interface GigabitEthernet0/1
  speed 1000
  duplex full
  channel-group 1 mode active
end

! Avoid: "speed auto" or "duplex auto" (can negotiate to different values)
```

#### FortiGate - Set port speed

```fortios
config system interface
  edit "port1"
    set speed 1000full      ! 1000 Mbps, full-duplex
    set aggregate members "port1"
  next
  edit "port2"
    set speed 1000full
    set aggregate members "port1"
  next
end
```

---

## 4. Load Distribution: Hash Algorithms

### Load Distribution Mechanism

#### LAG distributes traffic across member ports using a hash function

```text
Hash Input Options:

  - Layer 2: Source MAC + Destination MAC
  - Layer 3: Source IP + Destination IP
  - Layer 4: Source Port + Destination Port

Example (Layer 3 hash with 4 ports):
  Flow 1 (10.0.1.1 -> 10.1.1.1) hash(10.0.1.1 + 10.1.1.1) % 4 = Port 0
  Flow 2 (10.0.1.2 -> 10.1.1.1) hash(10.0.1.2 + 10.1.1.1) % 4 = Port 1
  Flow 3 (10.0.1.3 -> 10.1.1.1) hash(10.0.1.3 + 10.1.1.1) % 4 = Port 2
  Flow 4 (10.0.1.4 -> 10.1.1.1) hash(10.0.1.4 + 10.1.1.1) % 4 = Port 3
  Flow 5 (10.0.1.5 -> 10.1.1.1) hash(10.0.1.5 + 10.1.1.1) % 4 = Port 0

  Distribution: 4 flows across 4 ports = 25% each (balanced)

  Problem: If all flows have same destination:
  Flow 1-100 (10.0.1.x -> 10.1.1.1) hash may map all to Port 0
  Result: 100% on Port 0, 0% on Ports 1-3 (unbalanced)
```

### Hash Algorithm Selection

#### Cisco hash options

```ios
! Cisco default: Source/Dest IP or Source/Dest MAC
show etherchannel load-balance
  EtherChannel Load-Balancing Configuration:
      src-mac
  EtherChannel Load-Balancing Oper: src-dst-ip    ! Currently using this

! Change to source/destination IP (recommended for L3):
port-channel load-balance src-dst-ip

! Change to source/destination MAC (for L2 switching):
port-channel load-balance src-dst-mac
```

#### FortiGate hash algorithm

```fortios
config system global
  set aggregation-algorithm "srcportdstport"  ! Layer 4 (port-based)
  ! OR: "srcipdestipc (Layer 3)
  ! OR: "srcmacdestipmac" (Layer 2 + 3 mixed)
end
```

### Monitoring Load Distribution

#### Cisco - View port utilization

```ios
show interfaces port-channel 1 | include "input rate\|output rate"
  5 minute input rate 125000000 bits/sec, 62500 packets/sec
  5 minute output rate 125000000 bits/sec, 62500 packets/sec

show interfaces GigabitEthernet0/0 | include "input rate"
  5 minute input rate 100000000 bits/sec, 50000 packets/sec

show interfaces GigabitEthernet0/1 | include "input rate"
  5 minute input rate 25000000 bits/sec, 12500 packets/sec

! Imbalance: 100M on Gi0/0, 25M on Gi0/1 (uneven distribution)
```

#### Ideal distribution (4-port LAG)

```text
Port 1: 250 Mbps (25%)
Port 2: 250 Mbps (25%)
Port 3: 250 Mbps (25%)
Port 4: 250 Mbps (25%)
Total:  1000 Mbps (optimal)

Acceptable variance: ±10% (due to hash collisions)
```

### Mitigation: Improving Load Distribution

#### Problem - Single large flow uses 1 port; other flows scattered

```text
Example: TCP bulk transfer (10.0.1.1 -> 10.1.1.1) = 900 Mbps
         Multiple small flows = 100 Mbps

Without flow-aware distribution:
  Bulk flow hashed to Port 1: 900 Mbps
  Small flows distributed: Ports 2-4: 33 Mbps each
  Imbalance: Port 1 congested, Ports 2-4 underutilized

Solution: Use Layer 4 hash (source/destination port)
  Most TCP flows have different source port
  Allows better distribution of multiple flows from same source IP
```

#### Cisco - Change hash to include layer 4

```ios
port-channel load-balance src-dst-port
! Uses source IP + destination IP + source port + destination port
! Better distribution for many flows from same source
```

---

## 5. Spanning Tree Interaction

### STP Treats LAG as Single Port

#### Key principle - LAG is a logical interface; STP sees it as one port

```text
Topology: Switch A (2-port LAG) --- Switch B (2-port LAG)
                       |                    |
                  Server 1 (Gi0/2)    Server 2 (Gi0/2)

STP perspective:
  Port-channel 1 (Switch A <-> Switch B): One logical port
  Gi0/2 (Switch A <-> Server 1): One port
  Gi0/2 (Switch B <-> Server 2): One port

If loop would form through Port-channel 1:
  STP blocks Port-channel 1 entirely (not individual members)
  All 4 links (2 from A, 2 from B) are blocked together
```

### STP Behavior with LAG Failure

#### Scenario - One member port fails

```text
Initial state:
  Port-channel 1 (up): Both member ports active
  Data: Load balanced across Gi0/0 and Gi0/1

Gi0/0 fails:
  Port-channel 1 still up (Gi0/1 active)
  Data: All traffic on Gi0/1 (1x bandwidth)
  STP: No change (port-channel still up)
  Recovery time: <1 second (no STP convergence needed)
```

#### Scenario - Port-channel goes down

```text
Both member ports fail:
  Port-channel 1 (down)
  STP: Detects port-channel down
  STP: Recalculation (30-50 seconds with default timers)
  Convergence time: 50+ seconds

Prevention: Do not allow both members to fail simultaneously
  Different ISP circuits (one per port)
  Different cable routes (physical diversity)
```

### STP Configuration with LAG

#### Cisco - RSTP + LAG

```ios
interface Port-channel1
  spanning-tree portfast edge
  ! Reduces convergence if port-channel fails (enters forwarding immediately)

  spanning-tree cost 1
  ! Cost of port-channel (lower = preferred in STP)
end

! Per-port STP should not be configured; STP operates on port-channel
! (not on individual member ports)
```

#### FortiGate - LAG + STP

```fortios
config system interface
  edit "port-channel"
    set type aggregate
    set member "port1" "port2"
    set stp enable           ! STP on aggregated port
    set stp-priority 128
  next
end
```

---

## 6. Failover Testing: What Happens When a Member Fails

### Test 1: Verify Failover on Single Member Failure

```text
Step 1: Baseline
  Port-channel 1: Up
  Member ports: Gi0/0 (up), Gi0/1 (up)
  Bandwidth: 2 Gbps (combined)
  Traffic: Distributed across both ports

Step 2: Fail one port
  Router# interface GigabitEthernet0/0
  Router# shutdown

Step 3: Verify failover
  Port-channel 1: Still up (Gi0/1 active)
  Bandwidth: 1 Gbps (only Gi0/1)
  Traffic: All on Gi0/1 (no packet loss; hash updated)
  Convergence: <1 second (no STP needed)

Step 4: Restore port
  Router# no shutdown
  Port-channel 1: Back to 2 Gbps
  Traffic: Re-distributed (hash recalculates)
```

### Test 2: Verify LACP Negotiation Failure

#### Intentional misconfiguration to test LACP

```text
Router A: channel-group 1 mode active (LACP active)
Router B: channel-group 1 mode off (no aggregation)

Result:
  Router A: Attempting LACP negotiation
  Router B: Not participating
  Port-channel: Down on Router A
  Data: No traffic flows (port-channel down)

Then fix:
  Router B: channel-group 1 mode active
  LACP negotiation succeeds
  Port-channel: Up
  Data: Flows again
```

### Test 3: Verify Speed Mismatch Impact

```text
Step 1: Configuration
  Port 1: speed 1000, duplex full
  Port 2: speed 100, duplex full (misconfiguration)

Step 2: Verify LAG still forms (but impaired)
  show etherchannel 1 summary
  Port-channel 1: Up (both Gi0/0 and Gi0/1 active)

Step 3: Monitor traffic
  Total bandwidth: Limited to 100 Mbps (slowest port)
  Gi0/0 (1G): < 100 Mbps (underutilized; rate-limited by Gi0/1)
  Gi0/1 (100M): ~100 Mbps (bottleneck)

Step 4: Fix
  change Gi0/1 to: speed 1000, duplex full
  Monitor: Bandwidth increases to 2 Gbps
```

---

## 7. Multi-Chassis LAG (MCLAG/vPC)

### Single-Chassis LAG (Standard)

#### All member ports on same router

```text
Router A (2-port LAG):
  Port-channel 1: Gi0/0 + Gi0/1
  Both ports on Router A
  Failure: If Router A fails, entire LAG down
  Limitation: No cross-router redundancy
```

### Multi-Chassis LAG (MCLAG/vPC) - Advanced

#### Member ports on different routers (requires coordination protocol)

```text
Router A (vPC peer):
  Port-channel 1: Gi0/0 (on Router A) + Gi0/1 (on Router B, virtual)

Router B (vPC peer):
  Port-channel 1: Gi0/0 (on Router B) + Gi0/1 (on Router A, virtual)

Benefit: If Router A fails, Router B takes over; LAG remains up
Requirement: Coordination link (vPC peer-link) between routers

Cisco vPC (Virtual Port Channel):
  Primary router: Active; forwards all traffic
  Secondary router: Standby; active for backup
  Convergence: <1 second on primary failure

FortiGate HA + LAG:
  Active-Active mode: Both routers forward simultaneously
  State synchronization: HA pair sync membership
```

### MCLAG Configuration (Cisco vPC)

```ios
! Router A (vPC Peer 1)
feature vpc
vpc domain 1
  peer-switch
  role priority 32667        ! Higher priority = primary
  peer-keepalive destination 10.0.0.2
end

interface port-channel 10
  vpc 10                     ! vPC group 10
end

interface Ethernet 1/1
  channel-group 10 mode active
  no shutdown
end

! Router B (vPC Peer 2)
feature vpc
vpc domain 1
  peer-switch
  role priority 32768        ! Lower priority = secondary
  peer-keepalive destination 10.0.0.1
end

interface port-channel 10
  vpc 10
end

interface Ethernet 1/1
  channel-group 10 mode active
  no shutdown
end
```

---

## 8. Common Mistakes & Mitigation

### Mistake 1: Mixed Link Speeds

#### Problem

```text
Configuration:
  Gi0/0: 1 Gbps
  Gi0/1: 100 Mbps
  Gi0/2: 1 Gbps
  Gi0/3: 1 Gbps

Result:
  LAG forms with all 4 ports
  But effective throughput = 100 Mbps (bottleneck on Gi0/1)
  Hash distributes traffic; Gi0/1 always congested
  Packet loss on flows hashing to Gi0/1
```

#### Mitigation

```text

1. Do NOT mix speeds
   Either: All 1 Gbps
           OR: All 100 Mbps

1. Pre-deployment: Verify all cables/modules
   show interfaces <range> | include "speed"
   Ensure all report same speed

1. Monitor: Create alert for speed mismatch
   If any port speed differs from others, page on-call
```

### Mistake 2: LACP Negotiation Failure (Silent)

#### Problem

```text
Configuration:
  Router A: channel-group 1 mode active
  Router B: channel-group 1 mode off (no aggregation)

Result:
  Port-channel forms on Router A (single port)
  Router B: Individual ports (no channel)
  No error message; looks operational
  But: Load distribution on Router A only; Router B sees individual ports

Traffic path asymmetry:
  A -> B: Load balanced across 2 ports
  B -> A: No load balancing (Router B has individual ports)
  One-way imbalance; hard to troubleshoot
```

#### Mitigation

```text

1. Verify LACP state
   show etherchannel 1 detail
   LACP Neighbor Info:
     Port Gi0/0: flags = U
     Port Gi0/1: flags = U
   (U = in use; should be present)

   If not in use, LACP negotiation failed
   Check peer configuration: Must be mode active or passive

1. Alert on LACP failure
   If etherchannel members != expected count, alert
```

### Mistake 3: Unequal Load Distribution

#### Problem

```text
Configuration: 4-port LAG
Expected: 25% per port

Actual:
  Port 1: 50% (large flows to destination X)
  Port 2: 30%
  Port 3: 15%
  Port 4: 5%

Root cause:
  Large flows from same source -> same destination hash to few ports
  Hash algorithm (src-dst-ip) insufficient for this traffic pattern
```

#### Mitigation

```text

1. Change hash algorithm to include L4 (port numbers)
   port-channel load-balance src-dst-port

1. This only helps if flows have different source/destination ports
   If all flows are same (e.g., massive data transfer),
   hash will still concentrate them

1. Alternative: Accept unequal load if total throughput acceptable
   Example: 50% on Port 1 = 500 Mbps (acceptable if 1 Gbps links)
   Only problematic if approaching link capacity
```

### Mistake 4: Member Port in Suspended State

#### Problem

```text
show etherchannel 1 summary
  Group  Port-channel  Protocol    Ports

  ------+-------------+-----------+-----------------------------------------------
  1      Po1(RU)          LACP      Gi0/0(P)   Gi0/1(s)

  ! s = suspended (not active)
  ! Only Gi0/0 carrying traffic

Reason: LACP negotiation issue or duplex mismatch
```

#### Mitigation

```text

1. Check LACP negotiation
   show lacp neighbor Ethernet 0/1

1. Check speed/duplex
   show interfaces Gigabit 0/1 | include "speed\|duplex"
   Compare with other members

1. If persistent: Try no shutdown
   interface Gi0/1
     shutdown
     no shutdown   ! Force re-negotiation
   end
```

### Mistake 5: LAG on STP Root Bridge (Prevents Optimization)

#### Problem

```text
LAG is root bridge for spanning tree
Port-channel has cost 1 (lowest, becomes root)
STP blocks other links by default (not using LAG for backup)

If LAG fails:
  STP must reconverge (50+ seconds)
  Other links activate (slow)
  Downtime: 50+ seconds (unacceptable)
```

#### Mitigation

```text

1. Configure port-channel cost explicitly
   interface Port-channel 1
     spanning-tree cost 4096   ! Explicitly set higher cost
   end

1. OR: Prefer STP via other topology
   Configure root bridge on dedicated switches (not LAG)

1. OR: Use loop-free topology (no redundant links)
   Eliminates need for STP entirely
```

---

## 9. Verification & Testing

### Pre-Deployment Checklist

- [ ] All member ports confirmed same speed (e.g., 1 Gbps)
- [ ] All member ports confirmed full-duplex
- [ ] LACP mode: Active or Passive (not static or off)
- [ ] Both sides configured identically
- [ ] Channel group number same on both sides
- [ ] Port-channel interface IP configured (if L3)
- [ ] Hash algorithm appropriate (src-dst-ip for L3, src-dst-mac for L2)
- [ ] STP configured on port-channel (if needed)
- [ ] No per-member STP configuration
- [ ] MTU matches on all members (all 1500 or all 9000)
- [ ] First member port brought up; then others
- [ ] Port-channel comes up (all members active)

### Post-Deployment Testing

#### LACP negotiation verification

```text
Step 1: Verify LACP state
  show etherchannel 1 summary
  Group 1: Po1(RU), LACP
  Ports: Gi0/0(P)  Gi0/1(P)
  ! P = bundled; both should be P (active)

Step 2: Verify on peer
  Peer router: show etherchannel 1 summary
  ! Should show identical status

Step 3: If any port not bundled
  Troubleshoot LACP negotiation:
  show etherchannel 1 detail | include "flags"
  ! Flags must be U (in use) for all members
```

#### Load balancing verification

```text
Step 1: Baseline
  show interfaces port-channel 1 | include "input rate"
  Total rate: X Mbps

Step 2: Per-port distribution
  show interfaces Gi0/0 | include "input rate"
  show interfaces Gi0/1 | include "input rate"
  show interfaces Gi0/2 | include "input rate"
  show interfaces Gi0/3 | include "input rate"

Step 3: Verify balance
  Each port should have ~(X / N) Mbps
  Example: 4 ports, 400 Mbps total = 100 Mbps each
  Acceptable variance: ±20%
```

#### Failover test

```text
Step 1: Establish baseline
  Port-channel 1: Up (all members active)
  Bandwidth: N * 1 Gbps

Step 2: Fail one member
  interface Gi0/0
    shutdown
  end

Step 3: Verify failover
  show etherchannel 1 summary
  ! Gi0/0 shows (D) = down; Gi0/1 still (P) = bundled
  Port-channel 1: Still up
  Bandwidth: (N-1) * 1 Gbps
  Traffic: Rerouted to remaining members
  Convergence: <1 second (no STP convergence)

Step 4: Restore
  interface Gi0/0
    no shutdown
  end
  Port-channel 1: Back to N * 1 Gbps
```

---

## References

- [Port Aggregation (LAG) Theory](../theory/port_aggregation.md)
- [LACP Packet Format](../packets/lacp.md)
- [Spanning Tree Design](../theory/spanning_tree.md)
- [Cisco EtherChannel Configuration](../cisco/cisco_etherchannel_config.md)
- [FortiGate LAG Configuration](../fortigate/fortigate_lag_config.md)
