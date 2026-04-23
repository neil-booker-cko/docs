# BFD (Bidirectional Forwarding Detection) Best Practices

BFD provides sub-millisecond to sub-second failure detection for routing protocols and critical links.
Proper BFD deployment eliminates routing convergence delays, reduces false positives, and integrates
seamlessly with OSPF, BGP, and HSRP. Hardware offload significantly reduces CPU overhead on high-speed
links.

---

## Quick Reference Checklist

| Decision | Best Practice |
| --- | --- |
| **Timer Selection** | 300/900 ms (Rx/Tx) for < 1 sec detection; 1000/3000 ms for cost reduction |
| **Hardware Offload** | Enable on all Cisco routers (ASICs); FortiGate (NPU-assisted); reduces CPU to <1% |
| **Placement** | BGP (always), OSPF (critical links), static routes (WAN failover) |
| **Multiplier** | Default 3 (3 missed hellos = timeout); increase to 5 for flaky links |
| **Asymmetric Timers** | Avoid; match Rx and Tx intervals for predictable behavior |
| **CPU Overhead** | Software BFD 300ms = 10-20% CPU per session; hardware = <1% |
| **Convergence Detection** | BFD 300/900 ms detects failure in <1 sec; combined with OSPF SPF delay gives <3 sec RTO |
| **Common Mistakes** | Over-aggressive timers (300/900 on slow links), no hardware offload, missing BFD on critical paths |

---

## 1. Overview: Sub-Millisecond to Sub-Second Failure Detection

### Why BFD Matters

Traditional routing convergence is slow:

```text
Link down event:
  T=0ms: Interface down
  T=10000ms: BGP detects via hold timer (default 180 seconds)
  T=10180ms: BGP session drops
  T=10200ms: Route withdrawn
  T=10500ms: All routers converge
  Total: 10+ seconds (unacceptable for critical applications)

With BFD:
  T=0ms: Interface down
  T=300ms: BFD detects (first missed detection)
  T=600ms: BFD confirms (second detection)
  T=900ms: BFD times out
  T=950ms: BGP session drops
  T=1000ms: All routers converge
  Total: <1 second (acceptable for VoIP, critical apps)
```

### BFD Operating Principles

```text
BFD packets sent every Tx interval (e.g., 300 ms)
If Rx multiplier (e.g., 3) consecutive packets missed:
  Timeout = Rx interval * multiplier
  Default: 300 ms * 3 = 900 ms total timeout

Example: 300/900 ms configuration
  Router A sends hello: 300, 600, 900, 1200 ms
  Router B expects hello by 900, 1200, 1500 ms (900 ms timeout)
  If packet at 900 ms doesn't arrive: Timeout at 1800 ms
  (Wait for 3rd missed packet: 900, 1200, 1500 ms all missed)
```

### BFD Placement Decision Tree

```text
Question 1: Is this a BGP peer link?
  YES -> Enable BFD (critical for convergence)
  NO -> Go to Question 2

Question 2: Is this an OSPF neighbor link?
  YES -> Enable BFD on critical links (datacenter, core)
         Disable on stable links (internal campus LAN)
  NO -> Go to Question 3

Question 3: Is this a static route next-hop?
  YES -> Enable BFD if failover time is critical (<3 seconds)
  NO -> BFD not needed

Question 4: Is there hardware offload available?
  YES -> CPU overhead minimal (<1%); use aggressive timers
  NO -> Use conservative timers (1000/3000 ms) or disable
```

---

## 2. Timer Selection: How to Choose Appropriate Intervals

### Timer Categories

| Timer Profile | Rx/Tx (ms) | Multiplier | Total Timeout | Use Case | CPU Impact |
| --- | --- | --- | --- | --- | --- |
| **Ultra-aggressive** | 100/300 | 3 | 900 ms | Carrier-grade, hardware-only | 50-100% (software) |
| **Aggressive** | 300/900 | 3 | 2700 ms | Critical BGP, VoIP, trading | 10-20% (software) |
| **Moderate** | 500/1500 | 3 | 4500 ms | Regional routing, datacenter | 3-5% (software) |
| **Conservative** | 1000/3000 | 3 | 9000 ms | Branch, WAN links | <1% (software) |
| **Very Conservative** | 3000/9000 | 3 | 27000 ms | High-latency links (satellite) | <0.1% (software) |

### Timer Selection Rules

#### Rule 1 - Match BFD timers to application RTO (Recovery Time Objective)

```text
Application RTO | BFD Timer Config
VoIP (<500ms)   | 300/900 ms (with hardware offload)
Critical apps   | 300/900 ms or 500/1500 ms
Standard BGP    | 500/1500 ms or 1000/3000 ms
WAN branch      | 1000/3000 ms
Satellite links | 3000/9000 ms (or disable BFD)
```

#### Rule 2 - Hardware offload enables aggressive timers; software requires conservative

```text
Device: Cisco ASR1000 (hardware ASICs)
  Option 1: BFD 300/900 ms, multiplier 3
  CPU overhead: <1%
  Timeout: 2.7 seconds
  Good for critical applications

Device: Cisco 2911 router (software-based)
  Option 1: BFD 1000/3000 ms, multiplier 3
  CPU overhead: <1%
  Timeout: 9 seconds
  Acceptable for most routing

  Option 2: BFD 300/900 ms (aggressive)
  CPU overhead: 15-20%
  Not recommended if CPU is constrained
```

#### Rule 3 - Link latency must be less than BFD interval

```text
Link latency: 50 ms (satellite has 250+ ms; do not use BFD)
Chosen timer: 300 ms
Is 50 ms < 300 ms? YES -> OK
Margin: 250 ms for jitter

Link latency: 150 ms (intercontinental WAN)
Chosen timer: 300 ms
Is 150 ms < 300 ms? YES -> OK
Margin: 150 ms for jitter (tight; risky)

Link latency: 250 ms (high-latency satellite)
Chosen timer: 1000 ms
Is 250 ms < 1000 ms? YES -> OK
Margin: 750 ms for jitter (good)
```

### Multiplier Selection

#### Default - 3 (miss 3 packets = timeout)

```text
With timer 300/900 ms, multiplier 3:
  Packets: 0, 300, 600, 900, 1200, 1500 ms
  If packet at 900 ms missed (first miss)
  Wait until 1200 ms (second miss)
  Wait until 1500 ms (third miss)
  Timeout at 1500 ms (actually 1800 ms after last expected packet)
  Total detection time: ~2700 ms for 3 misses
```

#### Increase multiplier for flaky links (4-5)

```text
Link with occasional packet loss (but not systematic failure):
  Multiplier 3: Timeouts too frequent (false positives)
  Multiplier 4: Need 4 misses = longer timeout
  Multiplier 5: Very conservative; slow to detect real failures

Trade-off: Multiplier 4 balances stability and convergence
```

#### Cisco - Configure multiplier

```ios
interface GigabitEthernet0/0
  bfd interval 300 min_rx 300 multiplier 3
  ! interval: Tx interval (300 ms)
  ! min_rx: minimum acceptable Rx interval from peer
  ! multiplier: Number of missed packets before timeout
end
```

#### FortiGate - BFD multiplier

```fortios
config system interface
  edit "port1"
    set bfd transmit-interval 300
    set bfd receive-interval 300
    set bfd detect-multiplier 3
  next
end
```

---

## 3. CPU/Overhead Considerations: Hardware Offload vs Software

### Software BFD Overhead

#### BFD runs in router CPU; processes each hello packet

```text
BFD 300/900 ms = 3 hellos per second (1000 ms / 300 ms)
Router CPU must:
  1. Receive packet from interface (interrupt)
  2. Check sequence number
  3. Update peer state
  4. Generate response packet
  5. Transmit packet

Per-session CPU: 0.5-2 ms per packet
Total: 3 packets/sec * 2 ms = 6 ms/sec = 0.6% per session

With 20 BFD sessions:
  Total CPU: 20 * 0.6% = 12% CPU overhead

If router CPU is already 80% utilized:
  Adding 20 BFD sessions = 92% (dangerous; overload risk)
```

### Hardware Offload Overhead

#### Hardware ASICs/NPUs process BFD independently

```text
Device: Cisco ASR1000 (hardware ASICs)
  BFD processing: Dedicated hardware forwarding engine
  CPU overhead: <0.1% per session
  Capacity: 1000+ concurrent BFD sessions possible

Device: FortiGate (NPU-assisted)
  BFD processing: Network Processor Unit
  CPU overhead: <0.1% per session
  Capacity: 500+ concurrent BFD sessions possible
```

### Determining Hardware Support

#### Cisco - Check ASIC support

```ios
show platform hardware chassis throughput
  Platform Throughput Information
  ...
  BFD Fast Detection: Supported (hardware offload enabled)

show platform software forwarding-manager hal ...
  Shows if BFD is handled by ASICs vs CPU
```

#### FortiGate - Check NP/CP offload

```fortios
diag npu np6 spe-vfr-info | grep "bfd"
diagnose debug enable
diagnose debug service dataplane 5
  (Monitor for BFD processing in dataplane/offload engine)
```

### Overhead Estimation

| Timer | Sessions | Software CPU | Hardware CPU |
| --- | --- | --- | --- |
| 300/900 ms | 1 | 0.6% | <0.1% |
| 300/900 ms | 20 | 12% | <2% |
| 1000/3000 ms | 1 | 0.2% | <0.1% |
| 1000/3000 ms | 100 | 20% | <5% |

#### Rule - If CPU > 80% baseline, use conservative timers or hardware offload

---

## 4. Placement: BGP, OSPF, Static Routes

### BGP + BFD (Mandatory)

#### Why - BGP default hold timer is 180 seconds; BFD enables sub-second convergence

```text
Without BFD:
  BGP peer down: 180 second detection = 3+ minute failover
  Unacceptable for any production network

With BFD:
  BGP peer down: BFD detects in <3 seconds
  BGP session drops immediately
  All routes withdrawn
  Convergence in <5 seconds total
```

#### Cisco - Enable BFD on BGP neighbors

```ios
router bgp 65000
  neighbor 203.0.113.1 remote-as 65100
  neighbor 203.0.113.1 fall-over bfd single-hop
  ! single-hop: BFD expects peer is 1 hop away
end

! Or enable on interface:
interface GigabitEthernet0/0
  bfd interval 300 min_rx 300 multiplier 3
  ip ospf bfd
  ! BGP automatically uses BFD if enabled on interface
end
```

#### FortiGate - BFD on BGP

```fortios
config router bgp
  set as 65000
  config neighbor
    edit "203.0.113.1"
      set remote-as 65100
      set bfd enable          ! Enable BFD for this neighbor
    next
  end
end
```

### OSPF + BFD (Critical Links)

#### Why - OSPF hello dead timer (default 40 seconds) is slow for critical links

```text
Critical links (datacenter interconnect):
  With BFD: Detect link failure in <1 second
  Convergence: <3 seconds

Non-critical links (branch access):
  BFD overhead not justified
  Standard OSPF timers sufficient
```

#### Cisco - OSPF + BFD on critical interfaces

```ios
interface GigabitEthernet0/0
  ip ospf network point-to-point
  ip ospf hello-interval 10      ! Standard hello
  ip ospf dead-interval 40       ! Standard dead timer
  bfd interval 300 min_rx 300 multiplier 3
  ip ospf bfd                    ! OSPF uses BFD for neighbor detection
end

interface GigabitEthernet0/1      ! Non-critical branch link
  ip ospf hello-interval 30
  ip ospf dead-interval 120
  ! No BFD (not needed)
end
```

#### FortiGate - OSPF + BFD

```fortios
config router ospf
  config area
    edit 0.0.0.0
      config interface
        edit "port1"
          set bfd enable
          set hello-interval 10
          set retransmit-interval 5
          set dead-interval 40
        next
      end
    next
  end
end
```

### Static Routes + BFD (WAN Failover)

#### Why - Static routes don't have dynamic detection; BFD enables failover

```text
Scenario: Static route to ISP1 with BFD
  next-hop 203.0.113.1 (ISP1 gateway)

If BFD times out:
  Route withdrawn
  Traffic fails over to secondary static route (ISP2)
  Convergence: <1 second

Without BFD: Manual intervention required (not failover)
```

#### Cisco - BFD on static route

```ios
track 1 bfd interface GigabitEthernet0/0 destination 203.0.113.1

ip route 0.0.0.0 0.0.0.0 203.0.113.1 1 track 1
! Route is valid only if track 1 (BFD) is up
! If BFD times out, route is removed

ip route 0.0.0.0 0.0.0.0 210.0.113.1 2
! Secondary route (higher metric) takes over
```

#### FortiGate - Static route with health check

```fortios
config system interface
  edit "port1"
    set bfd enable
    set bfd transmit-interval 300
    set bfd receive-interval 300
  next
end

config router static
  edit 1
    set destination 0.0.0.0 0.0.0.0
    set gateway 203.0.113.1
    set device "port1"
    set comment "Primary ISP with BFD"
  next
  edit 2
    set destination 0.0.0.0 0.0.0.0
    set gateway 210.0.113.1
    set device "port2"
    set comment "Secondary ISP (backup)"
  next
end
```

---

## 5. Hardware Offload: Cisco ASICs & FortiGate NPU

### Cisco ASR/ISR Hardware ASIC Support

#### ASR1000 (Edge Services Router)

```text
Platform: Cisco ASR 1000 / 1002
CPU: Intel dual-core (~2 GHz)
ASIC: Quantum Flow Processor (QFP)
BFD: Native hardware offload

Configuration advantage:
  Can run 300/900 ms timers with minimal CPU impact
  Supports 1000+ concurrent BFD sessions
  Recommended for SP/enterprise edge
```

#### ISR4000 (Integrated Services Router)

```text
Platform: Cisco ISR 4000 / 4300 / 4400
CPU: Intel multi-core
ASIC: Not standard (depends on ISR variant)
BFD: Partial hardware support (varies)

Configuration guidance:
  ISR4331: Software-based BFD (~5-10% CPU per 20 sessions)
           Use 1000/3000 ms timers

  ISR4451: Hardware-assisted BFD (~2% CPU per 20 sessions)
           Use 500/1500 ms timers

  Check: show platform hardware inventory
         Look for "ASIC" or "NPU" in output
```

### FortiGate NPU Offload

#### FortiGate 3100D / 3200D / 5240C (NPU-enabled)

```text
Architecture: Dedicated Network Processing Unit (NPU)
Performance: 100+ Gbps throughput with offload
BFD: Handled by NPU; CPU impact <0.1%

Configuration:
  BFD timers: 300/900 ms (safe; NPU handles it)
  Concurrent sessions: 500+ without CPU constraint
  Recommended for ISP/datacenter gateways
```

#### FortiGate FortiASIC integration

```text
Device: FortiGate 3100D-POE (with FortiASIC SP4)
BFD offload: Full hardware offload
Benefit: Lowest latency (wire-speed BFD)
         Highest reliability (independent from main CPU)
```

#### Verify NPU/hardware support

```fortios
diagnose hardware device list
  (Look for NPU, SPE, or FortiASIC in output)

diagnose system top-asic
  (Check if ASICs are active and healthy)

show system performance stat
  (Monitor NPU utilization vs CPU utilization)

! If BFD is processed by NPU, CPU usage stays flat
! If processed by CPU, you'll see CPU spikes
```

### Cisco Hardware Verification

#### Check for ASIC/hardware support

```ios
show platform hardware chassis throughput
  BFD Fast Detection: Supported
  ! Indicates ASIC offload available

show platform software forwarding-manager fp-npu info | grep -i bfd
  ! Shows BFD handling (ASIC vs CPU)

show interfaces GigabitEthernet0/0 | grep "BFD"
  ! Verify BFD enabled on interface
```

---

## 6. Interoperability: BFD with OSPF, BGP, HSRP

### BGP + BFD Session Behavior

#### Scenario - BGP neighbor with BFD enabled

```text
Timeline of events:
  T=0ms: Link down (cable pulled)
  T=300ms: BFD detects first hello miss
  T=600ms: BFD detects second hello miss
  T=900ms: BFD detects third hello miss
  T=950ms: BFD notifies BGP of peer down
  T=960ms: BGP session transitions to Idle
  T=970ms: All routes from peer marked as invalid
  T=1000ms: Best path recalculation (SPF if OSPF involved)
  T=1100ms: RIB updated; traffic reroutes

Total RTO: ~1 second
Without BFD: 180+ seconds
```

#### BGP + BFD configuration (both routers)

```ios
! Router A
router bgp 65000
  neighbor 203.0.113.2 remote-as 65000
  neighbor 203.0.113.2 fall-over bfd single-hop
end

interface GigabitEthernet0/0
  ip address 203.0.113.1 255.255.255.252
  bfd interval 300 min_rx 300 multiplier 3
end

! Router B (identical config)
router bgp 65000
  neighbor 203.0.113.1 remote-as 65000
  neighbor 203.0.113.1 fall-over bfd single-hop
end

interface GigabitEthernet0/0
  ip address 203.0.113.2 255.255.255.252
  bfd interval 300 min_rx 300 multiplier 3
end
```

### OSPF + BFD Session Behavior

#### Scenario - OSPF neighbor with BFD enabled

```text
Timeline:
  T=0ms: Link down
  T=900ms: BFD times out
  T=950ms: OSPF neighbor state transitions to Down
  T=1000ms: LSA flooded (neighbor state down)
  T=1050ms: SPF calculation starts
  T=1100ms: SPF completes (all routers converge)
  T=1150ms: RIB updated

Total RTO: ~1.2 seconds (with aggressive SPF timers)
Without BFD: 40 second OSPF hold timer
```

#### OSPF + BFD configuration

```ios
interface GigabitEthernet0/0
  ip ospf network point-to-point
  ip ospf hello-interval 10
  ip ospf dead-interval 40
  ip ospf cost 1
  bfd interval 300 min_rx 300 multiplier 3
  ip ospf bfd
end

router ospf 1
  timers throttle spf 50 100 5000
  ! SPF delay 50ms to ensure fast convergence
end
```

### HSRP + BFD Integration

#### Scenario - HSRP gateway with BFD health check

```text
Topology:
  Client -> HSRP VIP (10.0.1.254)
  Router1 (Active) -> ISP link
  Router2 (Standby)

With BFD on ISP link:
  T=0ms: ISP link down
  T=900ms: BFD times out on Router1
  T=950ms: Router1 lowers HSRP priority (via tracking)
  T=1000ms: Router2 becomes active
  T=1050ms: Clients reroute to Router2

Total failover: ~1.2 seconds
Without BFD: HSRP hello timer (default 10 seconds)
```

#### HSRP + BFD configuration

```ios
! Track external link via BFD
track 1 bfd interface GigabitEthernet0/0 destination 203.0.113.1

! HSRP group
interface GigabitEthernet0/2
  ip address 10.0.1.1 255.255.255.0
  standby 1 ip 10.0.1.254
  standby 1 priority 255
  standby 1 track 1 decrement 50
  ! If track 1 (BFD) fails, priority drops from 255 to 205
  ! Standby (priority 200) takes over
end

! Enable BFD on ISP interface
interface GigabitEthernet0/0
  ip address 203.0.113.1 255.255.255.252
  bfd interval 300 min_rx 300 multiplier 3
end
```

---

## 7. Monitoring & Troubleshooting: BFD Session State Verification

### BFD State Machine

```text
Admin Down:
  BFD session administratively disabled

Down:
  BFD session inactive; waiting for peer hello

Init:
  BFD session transitioning to Up

Up:
  BFD session healthy; hellos being exchanged
```

### Monitoring Commands

#### Cisco - Check BFD session state

```ios
show bfd summary
  Interface        Peer             State
  Gi0/0            203.0.113.2      Up
  Gi0/1            210.0.113.2      Down

show bfd neighbor detail
  NeighAddr         Local         Interface         State
  203.0.113.2       203.0.113.1    GigabitEthernet0/0  Up
    Local Diag: 0, Demand mode: 0, Poll bit: 0
    MinTxInt: 300 ms, MinRxInt: 300 ms, Multiplier: 3
    Received MinRxInt: 300 ms, Received Multiplier: 3
    Holdown (hits): 900 (0), Hello: 300 ms, Conf helo: 300
    Detect Multiplier: 3, Transmit interval: 300 (usec)
```

#### Cisco - Monitor BFD convergence

```ios
debug bfd session
  *Mar 1 10:00:00.000 UTC: BFD: SH: IP: 203.0.113.2 Interface: Gi0/0
  *Mar 1 10:00:00.050 UTC: BFD: Session Up for neighbor 203.0.113.2

! Observe timestamps; BFD should come up within 300-900 ms
```

#### Cisco - BFD statistics

```ios
show bfd all-sessions counters
  BFD Session Summary:
    Total sessions: 5
    Up sessions: 5
    Down sessions: 0
    Admin Down sessions: 0
```

#### FortiGate - Check BFD status

```fortios
diagnose ip bfd list
  Peer            RxState TxState MsgsRx MsgsTx
  203.0.113.2     Up      Up      45000  45000

diagnose ip bfd session-state
  (More detailed state information)
```

### Troubleshooting False Positives

#### Problem - BFD session flapping (up/down/up/down)

```text
Symptoms:
  show bfd summary: State changes every few seconds
  show bfd session counters: High "Transitions" count

Causes:
  1. Link jitter/packet loss -> occasional missed hellos
  2. Asymmetric delays -> hellos arrive late
  3. CPU overload -> delayed BFD processing

Diagnosis:
  show interfaces counters | grep "drops\|errors"
  (Check for packet loss on interface)

  show processes cpu | grep bfd
  (Check if BFD processing is delayed)
```

#### Mitigation

```text
1. Increase BFD multiplier (3 -> 4 or 5)
   Requires more misses before timeout; tolerates occasional loss

2. Increase BFD intervals (300 -> 500 or 1000 ms)
   Fewer hellos/sec; lower CPU overhead; slower detection

3. Check link quality
   Replace cable, upgrade interface, check for duplex mismatch

4. If CPU issue: reduce other processes
   Or enable hardware offload (upgrade to ASR/FortiGate with NPU)
```

### Convergence Time Measurement

#### Test - Measure actual BFD + routing convergence time

```text
Step 1: Setup baseline
  Router A: show ip route | grep "203.0.113.0/24"
  Router B: show ip route | grep "203.0.113.0/24"
  (Both should have route via primary path)

Step 2: Enable timestamp logging
  Cisco: service timestamps debug datetime msec

Step 3: Trigger failure
  Router A# interface GigabitEthernet0/0
  Router A# shutdown

Step 4: Monitor convergence
  Router B# show ip route | grep "203.0.113.0/24"
  (Watch for route to change to backup path)

Step 5: Calculate RTO
  Measure time from "shutdown" command to route change
  BFD 300/900 ms: ~1-2 seconds expected
  Standard hello: ~40-180 seconds expected
```

---

## 8. Common Pitfalls & How to Avoid Them

### Pitfall 1: Over-Aggressive Timers on Slow/Lossy Links

#### Problem

```text
Configuration: BFD 300/900 ms on intercontinental WAN link
Link latency: 150 ms (expected variability: 10 ms)
Jitter: 50 ms (occasional spike to 200 ms)

When jitter hits 200 ms:
  BFD hello at 300 ms arrives at 500 ms (late)
  Peer waits until 900 ms (timeout)
  BFD session flaps (false positive)

Result: Frequent false positives; routing instability
```

#### Prevention

```text
Rule: BFD interval > (link latency + jitter margin)
Intercontinental WAN (150 ms latency, 50 ms jitter):
  Chosen interval: 1000 ms (1 second)
  Margin: 800 ms for spikes (safe)

High-speed LAN (1 ms latency, 1 ms jitter):
  Chosen interval: 300 ms
  Margin: 298 ms (safe)
```

### Pitfall 2: No Hardware Offload on CPU-Constrained Router

#### Problem

```text
Router: Cisco 2911 (low-end, software-based BFD)
Configuration: BFD 300/900 ms on 10 BGP neighbors
CPU baseline: 70%
After enabling BFD: CPU jumps to 90%+
Risk: CPU overload causes keepalive loss; BGP flaps

With 20 BFD sessions:
  CPU overhead: 20 * 0.6% = 12% (on low-end router)
```

#### Prevention

```text
1. Check CPU baseline before adding BFD
   show processes cpu sorted
   If > 60%, do not add aggressive BFD

2. If CPU high, upgrade hardware
   OR: Use conservative timers (1000/3000 ms)

3. Monitor after enabling BFD
   show processes cpu | grep -i bfd
   BFD CPU should be <10% total
```

### Pitfall 3: Asymmetric BFD Timers (Mismatch Between Peers)

#### Problem

```text
Router A: bfd interval 300 min_rx 300
Router B: bfd interval 1000 min_rx 1000

Negotiation result:
  Router A sends hellos every 300 ms
  Router B configured to accept min 1000 ms
  Router B waits until 1000 ms to expect hello

When Router A sends hello at 300 ms:
  Router B is not yet listening (early)
  Packet may be dropped
  Potential for mismatch
```

#### Prevention

```text
Rule: Both peers must have identical timer configuration
Router A: interval 300, min_rx 300
Router B: interval 300, min_rx 300 (exactly the same)

Or: Use negotiation (routers agree on parameters)
Cisco auto-negotiation: Typically works
FortiGate: Requires explicit matching
```

### Pitfall 4: BFD on Paths with Shared Fate (Same Risk as Primary Path)

#### Problem

```text
Scenario: Primary path Router A -> Router B -> ISP
BFD monitors Router A <-> Router B link (good)
But both routers are in same rack; same power supply
Risk: Power loss affects both routers; no failover

BFD correctly detects failure
But backup path (Router C) can't help
Because Router A (next-hop) is also down
```

#### Prevention

```text
Rule: Backup path must be completely independent from primary
Primary path: Router A (rack 1) -> ISP1
Backup path: Router C (rack 2) -> ISP2
Different racks, different power, different circuits

With this design:
  BFD detects Router A failure
  Traffic reroutes to Router C
  Failover is meaningful
```

### Pitfall 5: BFD Enabled But Routing Doesn't Use It

#### Problem

```text
Configuration: BFD enabled on interface
BGP neighbors: 2 neighbors (203.0.113.1 and 203.0.113.2)
But: Only one neighbor has "fall-over bfd" configured

Result:
  203.0.113.1: Uses BFD (converges in <1 second)
  203.0.113.2: Ignores BFD (uses default 180 second hold timer)
  Asymmetric convergence; confusing behavior
```

#### Prevention

```text
1. Enable BFD on interface (platform level)
2. Enable BFD on EACH routing neighbor
   BGP: "fall-over bfd single-hop"
   OSPF: "ip ospf bfd"

3. Verify:
   show bfd neighbors (BFD is up)
   show ip bgp neighbors | grep "BFD"
   show ip ospf interface | grep "BFD"
```

---

## 9. Convergence Time Calculations

### Formula: Total Convergence Time

```text
RTO (Recovery Time Objective) = BFD timeout + BGP/OSPF timers + SPF + RIB update

RTO = (BFD Rx * Multiplier) + BGP session setup + SPF delay + FIB update
```

### Example Calculations

#### Scenario 1 - BGP + BFD (aggressive timers)

```text
BFD: 300 ms interval, multiplier 3
Timeout: 300 * 3 = 900 ms
BGP fallover: 100 ms (time to detect BFD down + notify BGP)
Best path calculation: 50 ms
Route propagation: 50 ms
RIB/FIB update: 50 ms

Total RTO: 900 + 100 + 50 + 50 + 50 = 1150 ms (~1.2 seconds)
```

#### Scenario 2 - OSPF + BFD (with SPF optimization)

```text
BFD: 300 ms interval, multiplier 3
Timeout: 300 * 3 = 900 ms
OSPF neighbor down: 50 ms
SPF delay: 50 ms (minimum; then 100 ms, 5 sec throttle)
SPF computation: 50 ms (small network)
RIB update: 50 ms

Total RTO: 900 + 50 + 50 + 50 + 50 = 1100 ms (~1.1 seconds)
```

#### Scenario 3 - BGP without BFD (standard timers)

```text
BFD: Disabled
BGP hold timer: 180 seconds (default)
BGP detection: 180 seconds (miss 1 keepalive interval = 60 seconds + margin)
BGP session drop: 180 seconds
Best path recalculation: 50 ms
RIB update: 50 ms

Total RTO: 180000 + 50 + 50 = 180100 ms (~180+ seconds)
```

---

## 10. Verification & Testing

### Pre-Deployment Checklist

- [ ] Hardware offload verified (Cisco ASIC, FortiGate NPU)
- [ ] Timer values chosen based on link latency (interval > latency + jitter margin)
- [ ] Multiplier set to 3 (or 4-5 for flaky links)
- [ ] BFD enabled on interface (all peers using same timers)
- [ ] BGP: "fall-over bfd single-hop" configured on all neighbors
- [ ] OSPF: "ip ospf bfd" enabled on critical links
- [ ] Static routes: Tracking via BFD configured for failover
- [ ] CPU baseline <60% (before adding BFD)
- [ ] BFD state is "Up" on all sessions
- [ ] Convergence test passes (<5 seconds expected)

### Post-Deployment Testing

#### BFD session verification

```text
Step 1: Baseline
  show bfd summary (all sessions Up)
  show bfd neighbor detail (verify timers match)

Step 2: BGP neighbor state
  show ip bgp summary (all neighbors Established)
  show ip bgp neighbors | grep BFD (confirm BFD enabled)

Step 3: CPU impact
  show processes cpu | grep bfd
  (Should be <5% CPU overhead)
```

#### Convergence test

```text
Step 1: Establish baseline routes
  show ip route | grep "203.0.113"
  All routes present

Step 2: Trigger failure
  Interface shutdown (or physical cable pull)

Step 3: Monitor recovery time
  Measure from failure to route convergence
  With BFD 300/900 ms: <2 seconds expected

Step 4: Verify all routes converged
  show ip bgp summary (all neighbors Established)
  show ip route (all routes present via new paths)
```

---

## References

- [BFD Packet Format](../packets/bfd.md)
- [BGP Troubleshooting](bgp_troubleshooting.md)
- [OSPF Troubleshooting](ospf_troubleshooting.md)
- [Gateway Redundancy Design](gateway_redundancy_design.md)
- [Cisco BFD Configuration Guide](../cisco/cisco_bfd_config_guide.md)
- [FortiGate BFD Configuration](../fortigate/fortigate_bfd_config_guide.md)
