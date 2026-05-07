# High Availability (HA) Standards

High availability configuration for Cisco IOS-XE (HSRP/VRRP) and FortiGate (HA Cluster).

---

## HA Architecture Overview

### Active-Standby Failover

Checkout's standard HA model: two devices in active-standby mode with automatic failover.

| Component | Active | Standby | Failover Time |
| --- | --- | --- | --- |
| Router (Cisco) | Processes traffic | Monitoring | Sub-second (BFD) |
| Firewall (FortiGate) | Enforces policies | Replicating state | 1-3 seconds |
| Switch (Meraki) | N/A | N/A | Cloud-managed (no failover) |

---

## Cisco IOS-XE HA Standards

### Virtual Switching System (VSS) — Catalyst 9500 Series

**Standard:** Use VSS for datacenter core switches (C9500 series) for chassis-level redundancy.

| Parameter | Value | Notes |
| --- | --- | --- |
| VSS Mode | Active-Standby | One switch active; one standby |
| VSS Domain ID | Unique per site (1-255) | ELD7: 1, EDC4: 2, etc. |
| VSS Link | 40 Gbps (preferred) or 10 Gbps | Dedicated inter-chassis link |
| VSS Link Redundancy | Dual links (for critical sites) | 2x40G or 2x10G for fault tolerance |
| Stateful Switchover (SSO) | Enabled | Hitless failover with NSF |
| NSF (Non-Stop Forwarding) | Enabled | BGP, OSPF retain forwarding during failover |
| Failover Detection | BFD on VSS link | Fast detection of VSS link failure |

**VSS Configuration Example:**

```ios
switch 1
  priority 110
  switch virtual domain 1
exit

switch 2
  priority 100
  switch virtual domain 1
exit

interface Port-channel 10
  description VSS-Link
  switch virtual link 1
  no shutdown
!

interface GigabitEthernet2/1/1
  description VSS-Link-Switch1-to-Switch2
  channel-group 10 mode on
  no shutdown
!
```

**Advantages over HSRP:**

- Entire chassis fails over (all interfaces), not just one router interface
- Simpler configuration than per-interface HSRP
- Unified management (single logical switch)

---

### HSRP (Hot Standby Router Protocol) — Older/Branch Equipment

**Standard:** Use HSRP version 2 (HSRPv2) for all deployments.

| Parameter | Value | Notes |
| --- | --- | --- |
| Version | 2 (HSRPv2) | Supports IPv6; better multicast handling |
| Priority | Active: 110, Standby: 100 | Tie-breaker; higher = more preferred |
| Preempt | Enabled | Active router reclaims role if it recovers |
| Preempt Delay | 300 seconds | Allow convergence before preempting |
| Hello Interval | 3 seconds | Fast detection |
| Hold Time | 10 seconds | 3-4x hello interval |
| Virtual MAC | Auto-assigned (0000.0C9F.Fxxx) | Do not override |
| Virtual IP (VIP) | First/Last usable IP in subnet | Consistent across all HA pairs |
| Authentication | MD5 key (16+ chars) | Credential manager; never documented |

### HSRP Configuration Example

```ios
interface GigabitEthernet0/0
 ip address 10.0.1.10 255.255.255.0
 standby version 2
 standby 1 ip 10.0.1.1
 standby 1 priority 110
 standby 1 preempt delay minimum 300
 standby 1 timers 3 10
 standby 1 authentication md5 key-string MySecureKey123!
!
```

### VRRP (Virtual Router Redundancy Protocol)

**Use VRRP when:** Multi-vendor requirement (non-Cisco standby router).

| Parameter | Value | Notes |
| --- | --- | --- |
| VRRP Version | 3 (VRRPv3) | Supports IPv6 and IPv4 |
| Priority | Master: 110, Backup: 100 | Higher priority = preferred master |
| Preempt | Enabled | Recover if priority improves |
| Preempt Delay | 300 seconds | Allow convergence |
| Advertisement Interval | 1 second | Fast detection |
| Hold Time | 3 seconds | 3x advertisement interval |
| Virtual IP (VIP) | First usable IP in subnet | Same as HSRP |
| Authentication | None (disabled) | VRRPv3 uses IPsec if needed |

### VRRP Configuration Example

```ios
interface GigabitEthernet0/0
 ip address 10.0.1.10 255.255.255.0
 vrrp 1 address-family ipv4
  address 10.0.1.1 primary
  priority 110
  preempt delay minimum 300
  advertisement-interval 1
 !
!
```

---

## FortiGate HA Cluster Standards

### HA Configuration

**Model:** Active-Standby cluster (no load-balancing).

| Parameter | Standard | Notes |
| --- | --- | --- |
| HA Mode | Active-Standby | Primary device is active; secondary is standby |
| HA Priority | Primary: 100, Secondary: 50 | Higher = more preferred |
| Monitor Interval | 1 second | Heartbeat check; sub-second failover |
| Failover Hold Time | 0 seconds | Immediate failover on detection |
| Heartbeat Interfaces | Dedicated mgmt port | Out-of-band (not data path) |
| Session Sync | Enabled | Replicate active sessions to standby |
| Configuration Sync | Enabled | Keep standby config in sync with active |
| Override | Disabled | Standby cannot override priority |
| Password | Sync'd via HTTPS | 16+ chars, credential manager |

### FortiGate HA Configuration Example

**Primary (Active):**

```fortios
config system ha
    set mode active-passive
    set group-name "FW-HA-Primary"
    set priority 100
    set password "YourSecureHAPassword123!"
    set monitor-interfaces enable
    set ha-eth-type dedicated
    set ha-eth-port port1
    set hb-interval 1
    set failover-hold-time 0
    set session-sync enable
    set config-sync enable
    set override disable
next
end
```

**Secondary (Standby):**

```fortios
config system ha
    set mode active-passive
    set group-name "FW-HA-Primary"
    set priority 50
    set password "YourSecureHAPassword123!"
    set monitor-interfaces enable
    set ha-eth-type dedicated
    set ha-eth-port port1
    set hb-interval 1
    set failover-hold-time 0
    set session-sync enable
    set config-sync enable
    set override disable
next
end
```

### Monitored Interfaces

**What to monitor:** Each uplink interface (WAN1, WAN2, DX, ER, etc.)

```fortios
config system ha
    edit "port1"
        set monitor-interface enable
    next
    edit "port3"
        set monitor-interface enable
    next
end
```

If monitored interface goes down → failover to standby.

---

## Failover Detection & Timers

### BFD (Bidirectional Forwarding Detection)

**Use BFD when:** Sub-second failover required (< 1 second).

| Parameter | Value | Purpose |
| --- | --- | --- |
| Transmit Interval | 300 ms | Heartbeat frequency |
| Receive Interval | 300 ms | Expected reception rate |
| Multiplier | 3 | Declare peer dead after 3 missed heartbeats (900ms total) |
| Startup Interval | 10 seconds | Slower ramp-up during initial handshake |

### Cisco IOS-XE BFD Configuration

```ios
interface GigabitEthernet0/0
 ip address 10.0.1.10 255.255.255.0
 ip bfd interval 300 min_rx 300 multiplier 3
 standby bfd interface
!
```

### BFD State Tracking

Combine BFD with object tracking to trigger HA failover:

```ios
track 1 rtr 1 reachability
 delay up 1 down 3
!
interface GigabitEthernet0/0
 standby 1 track 1 decrement 20
!
```

If BFD detects neighbor down → Track 1 fires → Priority decrements 20 → Failover occurs.

---

## Split-Brain Prevention

**Problem:** If HA link fails, both devices may go active (split-brain).

**Solution:** Data path monitoring (not just HA heartbeat).

### Quorum-Based Failover

Require at least 50% of monitored interfaces up before allowing active role:

```fortios
config system ha
    set hb-lost-threshold 3
    set hb-interval 1
    set failover-hold-time 0
next
end
```

If majority of monitored WAN links down on "would-be active" device → stay in standby.

### Merge Recovery

When HA link is restored:

1. **Standby device stays standby** (does not preempt)
2. **Configuration sync** occurs automatically
3. **Session state** replicated from active
4. **Devices resync** — no data loss

---

## Testing & Validation

### Pre-Deployment Testing

**Checklist:**

1. **Power-off primary** — Verify standby takes active role within threshold
2. **Interface failure** — Unplug primary's uplink; verify failover triggers
3. **Data path test** — Ping through HA pair during active role switch
4. **Session persistence** — Verify SSH session survives failover
5. **Rollback test** — Restore primary; verify no data loss

### Failover Test Commands

**Cisco IOS-XE:**

```ios
! Force standby to active (for testing)
debug standby
standby 1 preempt

! Check HSRP state
show standby brief
show standby all
```

**FortiGate:**

```fortios
! Check HA status
get system ha status

! Force secondary to primary (for testing)
diagnose high-availability reclaim
```

### Monitoring & Alerts

- **PagerDuty Alert:** Primary-to-standby transition
- **Syslog Alert:** "HA state change" messages
- **Dashboard Alert:** HA cluster status on Meraki/dashboard
- **Regular Testing:** Monthly failover drill (scheduled maintenance window)

---

## HA Pair Examples

### Example 1: Router HA (Cisco IOS-XE)

**Topology:** Two Cisco Catalyst 9200 routers, HSRP v2

| Device | Role | IP | Priority | Notes |
| --- | --- | --- | --- | --- |
| ELD7-CSW-01 | Active | 10.0.1.10 | 110 | Primary (Dublin datacenter) |
| ELD7-CSW-02 | Standby | 10.0.1.11 | 100 | Secondary (same datacenter) |
| Virtual IP | N/A | 10.0.1.1 | N/A | HSRP VIP (default gateway) |

### Example 2: Firewall HA (FortiGate)

**Topology:** Two FortiGate 601F, active-standby cluster

| Device | Role | IP | Priority | Notes |
| --- | --- | --- | --- | --- |
| LON1-PFW-01A | Active | 10.0.2.10 | 100 | Primary (London office) |
| LON1-PFW-01B | Standby | 10.0.2.11 | 50 | Secondary (same office) |
| Cluster IP | N/A | 10.0.2.1 | N/A | Admin/management IP |

---

## Troubleshooting

### Common Issues

| Problem | Symptom | Solution |
| --- | --- | --- |
| Continuous failover | Alternates active-standby | Check for timing conflicts; increase hold time; verify BFD |
| Standby never active | Primary always active | Check priority; disable preempt if testing; check heartbeat link |
| Split-brain | Both devices claim active | Check HA link; enable data path monitoring; test quorum |
| No failover on failure | Primary fails, no switch | Check tracked objects; verify BFD state; check firewall rules (HA heartbeat) |

---

## Related Standards

- [Equipment Configuration](equipment-config.md) — SSH/AAA for remote access during failover
- [Security Hardening](security-hardening.md) — SNMP monitoring of HA state
- [Interface Configuration Standards](interface-standards.md) — HA heartbeat link configuration
