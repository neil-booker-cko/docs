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
| HA Mode | `a-p` (Active-Passive) | Primary device is active; secondary is standby |
| Group ID | Unique per cluster | Distinguishes clusters on the same network segment |
| Group Name | `<SITE>-FW-Cluster` | Matches device naming convention |
| HA Priority | Primary: 200–250, Secondary: 50 | Higher = more preferred |
| Heartbeat Interfaces | Two dedicated interfaces with priorities | Primary path higher priority; secondary path backup |
| Session Pickup | Enabled | Replicate active sessions to standby |
| Configuration Sync | Automatic | Standby mirrors active config; no explicit config required |
| Route TTL / Wait / Hold | 60 seconds each | Allow routing to stabilise after failover |
| Override | Disabled | Standby does not preempt active after recovery |
| Password | 16+ chars, credential manager | Never documented in source control |
| Monitored Interfaces | All uplinks | Failure on any monitored interface triggers failover |

### FortiGate HA Configuration Example

**Primary (Active):**

```fortios
config system ha
    set group-id <CLUSTER_ID>
    set group-name "<SITE>-FW-Cluster"
    set mode a-p
    set hbdev "ha" 150 "port8" 100
    set route-ttl 60
    set route-wait 60
    set route-hold 60
    set session-pickup enable
    set ha-mgmt-status enable
    config ha-mgmt-interfaces
        edit 1
            set interface "mgmt"
            set gateway <MGMT_GATEWAY>
        next
    end
    set override disable
    set priority 250
    set monitor "<UPLINK_1>" "<UPLINK_2>"
    set password "<HA_PASSWORD>"
end
```

**Secondary (Standby):** identical config except `set priority 50`.

### Monitored Interfaces

Include all uplinks — WAN, Direct Connect, ExpressRoute, and any transit interfaces. Failure on
any monitored interface triggers failover to the standby device.

```fortios
config system ha
    set monitor "bond0" "port1" "x1" "x2"
end
```

If a monitored interface goes down → failover to standby.

### FortiGate HA: Management, SNMP, and NetFlow

#### Per-Device Management Interfaces

The cluster IP is served by the active device only — the standby is unreachable via the cluster
IP until failover. For independent management and monitoring of each node, configure a dedicated
management interface with a unique IP per device:

```fortios
config system ha
    set ha-mgmt-status enable
    config ha-mgmt-interfaces
        edit 1
            set interface "mgmt"
            set gateway 10.x.x.1
        next
    end
end
```

The IP on the management interface itself is configured per-unit (not synced between members),
so each device retains its own address regardless of cluster state. Set these IPs individually
on each physical device before joining the cluster.

#### SNMP

**Standard:** Monitor each HA member by its individual management IP, not only the cluster IP.
Querying only the cluster IP gives visibility into the active node only — the standby is
invisible until failover.

- Enable `ha-direct enable` on the SNMP user — without this, queries to a standby node's
  management IP are proxied through the active device rather than answered directly
- Enable `append-index enable` in `system snmp sysinfo` — appends the HA member index to
  `sysName`, allowing the collector to distinguish which node it is talking to
- Add both node management IPs to LogicMonitor as separate device entries using the
  SNMP_STRONG profile
- The cluster IP may also be monitored, but does not substitute for per-node monitoring

```fortios
config system snmp sysinfo
    set status enable
    set description "<DEVICE_MODEL>"
    set contact-info "CKO Network Services"
    set location "<DC>-<RACK>"
    set append-index enable
end

config system snmp user
    edit "<SNMP_USER>"
        set trap-status disable
        set ha-direct enable
        unset events
        set security-level auth-priv
        set auth-proto sha256
        set auth-pwd ENC <AUTH_PASSWORD>
        set priv-proto aes256
        set priv-pwd ENC <PRIV_PASSWORD>
    next
end
```

The SNMP user config in [Equipment Configuration](equipment-config.md) and
[SNMP Standards](snmp-standards.md) also includes `set ha-direct enable`.

#### NetFlow

**Standard:** NetFlow is generated by the active device only. After failover, the newly active
device begins sending flows — source IP changes to the new active device's management IP.

- Set `source-ip` to the device's own management interface IP so flows are identifiable per node
- Configure the NetFlow collector to accept flows from both node management IPs
- There is no cluster-level NetFlow source; do not rely on a single source IP being stable

```fortios
config system netflow
    set active-flow-timeout 60
    set inactive-flow-timeout 10
    set template-tx-timeout 300
    config collectors
        edit 1
            set collector-ip "<NETFLOW_COLLECTOR_IP>"
            set source-ip "<THIS_NODE_MGMT_IP>"
        next
    end
end
```

`source-ip` must be set individually on each node (it is not synced by HA config sync) to the
node's own management interface IP.

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

**Recommended: Use global BFD template (see [BFD Standards](bfd-standards.md)):**

```ios
bfd-template single-hop BFD_STANDARD
 interval min-tx 300 min-rx 300 multiplier 3
 no echo
!

interface GigabitEthernet0/0
 ip address 10.0.1.10 255.255.255.0
 bfd template BFD_STANDARD
 standby bfd interface
!
```

**Note:** BFD timers are centralized in the template, simplifying management across
multiple HA interfaces.

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

### Device Naming Convention

HA pairs use the same base name with an `A` or `B` suffix to identify each member:

- **A** — primary/active member
- **B** — secondary/standby member

Example: `ELD7-CSW-01A` and `ELD7-CSW-01B` form one HA pair.

See [Naming Conventions](naming-conventions.md) for the full device naming standard.

### Example 1: Router HA (Cisco IOS-XE)

**Topology:** Two Cisco Catalyst 9200 routers, HSRP v2

| Device | Role | IP | Priority | Notes |
| --- | --- | --- | --- | --- |
| ELD7-CSW-01A | Active | 10.0.1.10 | 110 | Primary (Dublin datacenter) |
| ELD7-CSW-01B | Standby | 10.0.1.11 | 100 | Secondary (same datacenter) |
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
