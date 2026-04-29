# STP/RSTP Troubleshooting

Common Spanning Tree Protocol (STP) and Rapid STP (RSTP) issues with diagnostic commands and
remediation steps. Applies to Cisco IOS-XE and FortiGate environments with Layer 2 switching and
redundant links.

---

## Quick Diagnosis

| Symptom | Likely Cause | First Check |
| --- | --- | --- |
| **Unexpected port blocking** | Port in blocking state; wrong bridge priority | Check spanning-tree port role; verify root bridge |
| **Loops after link failure** | STP not converging fast; BPDU Guard not enabled | Enable BPDU Guard on edge ports; verify RSTP enabled |
| **Intermittent connectivity** | Flapping root bridge; topology unstable; BPDUs dropped | Check bridge priority; verify link stability |
| **Slow failover** (>30s) | Using legacy STP (3 states); timers too high | Enable RSTP; reduce forward delay |
| **Unidirectional link problem** | Link down one direction only; BPDUs not flowing back | Test both directions; enable UDLD on switches |
| **BPDU Guard tripping** | Received BPDU on edge port | Verify port shouldn't receive BPDUs; re-enable if needed |
| **Root bridge unexpected** | Bridge priority too high (default 32768) | Lower priority on intended root; verify convergence |
| **Link flapping** | Port in blocked state but should be forwarding | Check port costs; verify no loops in configuration |

---

## Root Bridge Issues

### Symptom: "Wrong Device is Root Bridge"

#### Check 1: Identify current root bridge

```ios
! Cisco
show spanning-tree root

! Example output:
! Root ID    Priority    32768
!            Address     0000.1111.2222
!            This bridge is the root
```

The bridge with the lowest priority (or lowest MAC if priority tied) becomes root.

#### Check 2: Check bridge priority

```ios
! Cisco
show spanning-tree | include Priority
! Default is 32768 (bridge priority 32768 + VLAN priority 0)

! Intended root should have LOWER priority:
spanning-tree vlan 1 priority 4096  ! Lower than 32768, guarantees root
!
```

#### Check 3: On every switch, verify consistent priority configuration

```ios
! All switches should have:
spanning-tree vlan <vlan> priority <value>
! Where intended root has lowest priority

! Example:
! Root: priority 4096
! Backup: priority 8192
! Leaf: priority 16384
```

### Symptom: "Root Bridge Flapping" (Changes Frequently)

**Symptoms:**

- Port roles change frequently

- "Topology Change" messages in logs

- Clients experience brief disconnections

**Cause:** BPDU loss or priority misconfiguration causing multiple devices to claim root.

#### Check 1: Verify bridge priority configuration

If multiple devices have same priority (or default 32768), the one with lowest MAC becomes root.
If any link flaps, a different device may have better BPDU path, causing root to switch.

```ios
! Explicitly set priority to ensure consistency
! On intended root:
spanning-tree vlan 1 priority 4096

! On backup:
spanning-tree vlan 1 priority 8192

! On others:
spanning-tree vlan 1 priority 16384 or higher
```

#### Check 2: Check for BPDU loss

```ios
! Cisco
debug spanning-tree bpdu
! Monitor for missing or delayed BPDUs

! If BPDUs delayed: check link quality, congestion, or MTU mismatch
```

#### Check 3: Verify no manual port cost changes causing topology shifts

If you've manually set port costs (lower cost = higher preference), a link change could shift
the best path to root.

```ios
! Check port costs:
show spanning-tree interface

! Default costs (802.1D): 100 Mbps=100, 1 Gbps=4, 10 Gbps=2
! Manual override:
interface GigabitEthernet0/0/1
 spanning-tree cost 1000  ! Higher cost = lower preference
!
```

---

## Port State Issues

### Symptom: "Port Stuck in Blocking State"

#### Check 1: Verify port role and state

```ios
! Cisco
show spanning-tree interface GigabitEthernet0/0/1 detail
! Shows: Role (Root/Designated/Backup), State (Forwarding/Blocking/Learning)

! Example output:
! Role: Alternate port
! State: Blocked
```

"Alternate" and "Backup" roles are blocked (standby).

#### Check 2: Is blocking intentional?

In a loop-free topology, exactly one port per switch (except root and designated) should be
blocked. If unintentional:

- Check if port is supposed to be root port (closest to root): should be Forwarding

- Check if port is supposed to be designated (segment facing away from root): should be Forwarding

- Check if topology truly requires this port to be blocked: if so, no action needed

#### Check 3: Verify port cost

Port with HIGHEST cost toward root becomes Alternate (blocked):

```ios
! If this port should forward, reduce its cost:
interface GigabitEthernet0/0/1
 spanning-tree cost 100  ! Lower than other ports
!

! Then check:
show spanning-tree interface GigabitEthernet0/0/1 brief
! Role should change to Root or Designated
```

### Symptom: "All Ports Blocking" (Complete Isolation)

**Cause:** This switch is not receiving BPDUs from root; believes it is the root itself; loops
back into blocking state on all ports.

#### Check 1: Verify connectivity to root bridge

Ping root bridge from this switch (if management connectivity exists):

```bash
ping <root-bridge-ip>
```

If unreachable: connectivity broken to root.

#### Check 2: Check for BPDU Guard tripping

```ios
! Cisco
show spanning-tree summary
! May show "BPDU Guard Enabled" and "BPDUs received on edge port (blocked)"

! If BPDU Guard tripped:
interface <interface>
 no spanning-tree bpduguard enable
!
! Then shut/no shut interface to recover
```

#### Check 3: Verify switch is part of VLAN

If switch not in VLAN, it won't participate in STP for that VLAN:

```ios
! Show VLANs on switch
show vlan
! Verify this switch has interfaces in the VLAN

! If not, add interface to VLAN:
interface GigabitEthernet0/0/1
 switchport access vlan 10
!
```

---

## Convergence and Failover Issues

### Symptom: "Failover Slow After Link Failure" (>30 seconds)

#### Check 1: Verify RSTP enabled (not legacy STP)

```ios
! Cisco
show spanning-tree | include "Type"
! Should show "Type: Rapid STP" or "Type: RSTP"

! To enable RSTP:
spanning-tree mode rapid-pvst  ! Per-VLAN Rapid STP
! or
spanning-tree mode rstp        ! Single instance
!
```

Legacy STP has 3 port states (Blocking → Listening → Learning → Forwarding) taking ~30–50
seconds. RSTP has 2 (Discarding → Learning → Forwarding), taking ~6–10 seconds.

#### Check 2: Check forward delay timers

```ios
! Cisco
show spanning-tree vlan 1 | include delay
! Default forward delay: 15 seconds

! To reduce (if RSTP):
spanning-tree vlan 1 forward-time 10  ! 10 seconds (RSTP-only)
!
```

RSTP uses forward delay only for edge ports transitioning to forwarding; most ports converge
faster.

#### Check 3: Enable BFD for sub-second detection

```ios
! Cisco (requires RSTP)
interface GigabitEthernet0/0/1
 bfd interval 300 min_rx 300 multiplier 3  ! 300 ms failure detection
!
```

BFD detects link failure sub-second; STP then converges in ~1 second total.

### Symptom: "Topology Changes Frequent" (Many "Topology Change" Messages)

**Cause:** Ports flapping (transitioning up/down repeatedly); each triggers a topology change.

```ios
! Cisco
debug spanning-tree events  ! Shows every topology change
! Look for which interface is flapping
```

**Remediation:**

1. Check physical link stability (cable, port, transceiver issues)

1. Enable BPDU Guard on edge ports (prevents unexpected devices from flapping ports):

```ios
interface GigabitEthernet0/0/1  ! Edge port (connects to end devices, not other switches)
 spanning-tree portfast         ! Transition directly to forwarding
 spanning-tree bpduguard enable ! Block if BPDU received (prevents loops)
!
```

1. Enable UDLD (Unidirectional Link Detection) on switch-to-switch links:

```ios
interface GigabitEthernet0/0/1
 udld port    ! Detects unidirectional links
!
```

---

## Unidirectional Link Problems

### Symptom: "Traffic Asymmetric" or "One-Way Connectivity"

**Cause:** Link down one direction; frames flowing out but not returning.

**Diagnosis:**

1. Physical observation: check cable, both interfaces

1. Check interface statistics:

```ios
! Cisco
show interface GigabitEthernet0/0/1
! Look for "Rx" (receive) vs "Tx" (transmit) counters

! If Tx high but Rx low or zero: likely unidirectional link
```

**Enable UDLD to detect:**

```ios
! On the link:
interface GigabitEthernet0/0/1
 udld port  ! Aggressive mode (shuts port if unidirectional detected)
!

! Check status:
show udld interface GigabitEthernet0/0/1
! Should show "Link State: Bidirectional"
! If unidirectional: "Link State: Undetermined" and port may be errdisabled
```

**Remediation:**

1. Reseat both cable ends

1. Replace cable

1. Try different port on switch (if current port defective)

---

## BPDU Guard and Loop Protection

### Symptom: "BPDU Guard Blocking Legitimate Switch"

**Cause:** BPDU Guard enabled on access port; received BPDU from legitimate switch that should
be allowed.

#### Check 1: Verify port is truly an access port

```ios
show spanning-tree interface <interface> detail
! Should show "Edge Port: Enabled" if this is access port

! If this is a trunk port (switch-to-switch):
interface <interface>
 no spanning-tree portfast  ! Remove portfast (shouldn't be on trunk)
 no spanning-tree bpduguard enable  ! Remove BPDU Guard on trunks
!
```

#### Check 2: Re-enable port after BPDU Guard blocks it

```ios
interface <interface>
 no shutdown  ! May auto-recover
! or
clear spanning-tree detected-protocols  ! Force recovery (IOS-XE only)
```

### Symptom: "Root Guard Blocking Root Bridge"

**Cause:** Root Guard enabled on port; received BPDU with lower priority than current root (new
device claiming root).

```ios
! Check Root Guard status:
show spanning-tree interface <interface> detail
! May show "Root Guard: Enabled" and "Port is blocked by root guard"
```

**Diagnosis:** Legitimate root bridge replacement? Or spurious BPDU?

- If legitimate: you're replacing root, expect temporary blocking

- If spurious: verify who's sending superior BPDU (trace source)

**Remediation:** Remove Root Guard if not needed:

```ios
interface <interface>
 no spanning-tree guard root
!
```

---

## Link Type and Speed Issues

### Symptom: "Port Transitions to Shared Link (Not Point-to-Point)"

STP has different behavior for point-to-point links (fast convergence) vs shared links (slower).
Port-fast is disabled on shared links.

#### Check 1: Verify link detection

```ios
! Cisco
show spanning-tree interface <interface> detail
! Look for "Link Type: P2p (Designated) or "Link Type: Shared"
```

#### Check 2: Set point-to-point manually if needed

```ios
interface <interface>
 spanning-tree link-type point-to-point  ! Force detection
!
```

---

## Best Practices for STP/RSTP

| Practice | Reason |
| --- | --- |
| **Use RSTP (not legacy STP)** | Faster convergence (6–10s vs 30–50s) |
| **Enable PortFast on access ports** | Transitions directly to forwarding; no learning delay |
| **Enable BPDU Guard on edge ports** | Prevents rogue devices from breaking topology |
| **Enable UDLD on switch links** | Detects and blocks unidirectional links |
| **Set root bridge priority explicitly** | Ensures predictable root selection |
| **Verify redundant links** | At least 2 paths to root; no single point of failure |
| **Monitor topology changes** | Frequent changes indicate port flapping |
| **Document bridge priorities** | Ensures consistent design across sites |
| **Use BFD with RSTP** | Sub-second convergence on link failure |

---

## Notes / Gotchas

- **PortFast Breaks STP:** PortFast on non-edge ports can create loops if bridging loop exists.
  Only enable on ports connecting to end devices (no other switches).

- **Priority 0 Wins:** In rare cases, if you set priority to 0 (maximum), that switch becomes
  root regardless. Use priority 4096 or 8192 instead (lower than default 32768).

- **Rapid PVST vs RSTP:** Cisco IOS has "rapid-pvst" (per-VLAN) and "rstp" (single instance).
  Rapid-PVST is more common in enterprise; RSTP is standard but less flexible per-VLAN.

- **Bridge ID Change = Reelection:** If root bridge fails (shutdown), new root elected by lowest
  priority of remaining bridges. Temporary disruption (1–10 seconds with RSTP).

- **Loop Detection After Failure:** If port incorrectly allowed to forward, creating loop, BPDU
  Guard and Root Guard are last-ditch protection. Primary prevention: correct design validation.

---

## See Also

- [Spanning Tree Design](../theory/spanning_tree.md)

- [STP/RSTP Configuration](../theory/stp_rstp_configuration.md)

- [OSPF Troubleshooting](ospf_troubleshooting.md)

- [BGP Troubleshooting](bgp_troubleshooting.md)

- [Link Aggregation Best Practices](link_aggregation_best_practices.md)
