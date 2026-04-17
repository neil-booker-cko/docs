# Spanning Tree Configuration Guide

This guide covers STP/RSTP configuration principles, design patterns, and best practices
across vendors.

## Configuration Fundamentals

### STP vs RSTP: Configuration Differences

| Aspect | STP (802.1D) | RSTP (802.1w) |
| --- | --------- | --- |
| **Protocol mode** | Manually configured as "spanning-tree mode" | Manually configured as "spanning-tree mode" |
| **Convergence** | ~50 seconds | ~6 seconds (theoretical <1s) |
| **Port states** | Disabled, Blocking, Listening, Learning, Forwarding | Discarding, Learning, Forwarding |
| **BPDU exchange** | Every 2 seconds (default) | Every 2 seconds (default) |
| **Backward compatible** | N/A | Yes; falls back to STP on old switches |
| **Configuration effort** | Same as RSTP | Same as STP |

**Recommendation:** Use RSTP (802.1w) in all new deployments. It is backward compatible
with STP and provides much faster convergence.

---

## Core Configuration Concepts

### 1. Bridge Priority (Root Bridge Selection)

Every switch has a **bridge priority** determining its likelihood of becoming root.

**Priority Calculation:**

```text
Bridge ID = Priority (4 bits) + Extended System ID (12 bits: VLAN ID) + MAC
```

**Priority values:** 0, 4096, 8192, 12288, ... 61440 (increments of 4096)
**Default:** 32768

**Best Practice:**

- Set priority to 0 (highest) on primary root candidate
- Set priority to 4096 on secondary root candidate
- Allows clean failover if primary goes down

```text

Primary Root (VLAN 1):   priority 0
Secondary Root (VLAN 1): priority 4096
All other switches: default 32768
```

### 2. Port Cost (Path Selection)

Each port has a **cost** determining its desirability for forwarding. Lower cost = preferred path.

**Standard costs (802.1w RSTP):**

| Link Speed | Cost |
| --- | --------- |
| 10 Gbps | 2 |
| 1 Gbps | 4 |
| 100 Mbps | 19 |
| 10 Mbps | 100 |

**Usage:** Manually override cost to engineer preferred paths.

```text

Example: Prefer path through secondary link
  interface GigabitEthernet0/0
    spanning-tree cost 100  (makes this path less desirable)

  interface GigabitEthernet0/1
    spanning-tree cost 4    (preferred path)
```

### 3. Port Priority

When tie-breaking between ports with equal cost, port priority determines which port forwards.

**Port priority values:** 0, 16, 32, 48, ... 240 (increments of 16)
**Default:** 128

**Usage:** Break ties between equal-cost paths.

```text

Example: Two links to same switch, both 1 Gbps
  interface GigabitEthernet0/0
    spanning-tree port-priority 128  (blocks, if tied)

  interface GigabitEthernet0/1
    spanning-tree port-priority 64   (forwards, higher priority)
```

### 4. BPDU Guard

Protects against accidental connection of switches to access ports (edge ports).

**Concept:** If a BPDU is received on a port configured as edge, put port into err-disabled state.

**Use case:** Prevent accidental loop creation when someone connects a switch to an access port.

```text

Cisco:
  interface GigabitEthernet0/10
    spanning-tree portfast
    spanning-tree bpduguard enable

Result: If a BPDU arrives, port shuts down (err-disabled).
         Must manually bring back up or configure automatic recovery.
```

### 5. PortFast (Edge Ports)

Ports connected to end devices (hosts, printers) are not part of the active topology and don't need
STP processing.

**Effect:** Port goes directly to forwarding state without waiting for STP convergence.

**Configuration:**

```text

Cisco:
  interface GigabitEthernet0/1
    spanning-tree portfast

FortiGate:
  config switch-controller
    config managed-switch
      config ports
        edit port_name
          set edge-port enable
        end
      end
    end
  end
```

**Important:** Use only on access ports; never on switch-to-switch links.

### 6. Root Guard

Prevents a port from becoming a root port. Used to enforce root bridge location.

**Use case:** Ensure a specific switch remains root by preventing any port from accepting superior BPDUs.

```text

Cisco:
  interface GigabitEthernet0/2
    spanning-tree guard root

Effect: If port receives BPDU from a better bridge, it's blocked
        until the better BPDU stops arriving.
```

### 7. Loop Guard

Prevents loop creation due to unidirectional link failures (one direction of link is broken).

**Problem:** If link fails in one direction, a blocked port might not receive BPDUs and might unblock,
creating a loop.

**Solution:** Loop guard monitors BPDU arrival; if expected BPDUs stop, port blocks until they resume.

```text

Cisco:
  interface GigabitEthernet0/3
    spanning-tree guard loop

Effect: If BPDU stops arriving on a blocked port, port remains blocked
        instead of transitioning to forwarding.
```

---

## Design Patterns

### Pattern 1: Core-Access (Two-Tier)

```text

        Core Switch 1 (Root)
              |
         (Primary Link)
              |
    +---------+---------+
    |                   |
  Access 1          Access 2
  (Backup Root)
    |                   |
  Hosts               Hosts
```

**Configuration:**

```text

Core Switch 1:
  spanning-tree vlan 1 priority 0

Core Switch 2:
  spanning-tree vlan 1 priority 4096

Access Switches:
  (default priority 32768)
  spanning-tree portfast (on access ports)
  spanning-tree bpduguard enable (on access ports)
```

### Pattern 2: Redundant Core (Aggregation)

```text

      Core 1 (Root)     Core 2 (Backup Root)
         |   \         /   |
         |    \       /    |
         |     \     /     |
      Agg 1 ----\   /---- Agg 2
         |       \ /       |
         +----+   X   +----+
              |       |
           Access 1  Access 2
```

**Configuration:**

```text

Core 1:
  spanning-tree vlan 1 priority 0

Core 2:
  spanning-tree vlan 1 priority 4096

Aggregation (manual path tuning):
  interface GigabitEthernet0/0 (to Core 1)
    spanning-tree cost 4

  interface GigabitEthernet0/1 (to Core 2)
    spanning-tree cost 19  (less preferred)
```

---

## RSTP-Specific Features

### Rapid Convergence

RSTP converges in milliseconds (vs STP's 50 seconds) through:

1. **Explicit Handshake:** Root sends agreement immediately upon receiving superior BPDU
2. **Alternate/Backup Ports:** Pre-computed backup paths ready to use
3. **Port roles:** Root, Designated, Alternate, Backup (vs STP's Blocking)

### Configuration (No special config needed)

Simply enable RSTP mode, and fast convergence happens automatically:

```text

Cisco:
  spanning-tree mode rapid-pvst

FortiGate:
  config switch-controller
    config managed-switch
      set stp-mode rapid  (vs standard)
    end
  end
```

---

## PVST+ (Per-VLAN STP)

In large networks with multiple VLANs, run separate STP instance per VLAN for load balancing.

**Concept:** Different VLANs can have different root bridges, spreading load across switches.

```text

VLAN 1 Root: Core Switch 1
  ├─ VLAN 1 traffic: Core 1 → Agg 1 → Access 1
  └─ VLAN 1 traffic: Access 2 → Agg 2 → Agg 1 → Core 1

VLAN 2 Root: Core Switch 2
  ├─ VLAN 2 traffic: Core 2 → Agg 2 → Access 2
  └─ VLAN 2 traffic: Access 1 → Agg 1 → Agg 2 → Core 2
```

**Configuration:**

```text

Cisco:
  spanning-tree vlan 1 priority 0      (Core 1 is root for VLAN 1)
  spanning-tree vlan 2 priority 4096   (Core 1 is backup for VLAN 2)

  (on Core Switch 2)
  spanning-tree vlan 1 priority 4096
  spanning-tree vlan 2 priority 0      (Core 2 is root for VLAN 2)
```

**Load Balancing Result:**

- VLAN 1 traffic prefers Core 1
- VLAN 2 traffic prefers Core 2
- Better link utilization

---

## Troubleshooting

### Port Stuck in err-disabled

**Cause:** BPDU guard triggered on edge port.

**Fix:**

```text

Cisco:
  interface GigabitEthernet0/10
    no shutdown
    spanning-tree bpduguard recovery delay 60  (auto-recovery after 60s)
```

### Slower Convergence Than Expected

**Causes:**

1. STP mode is set to "spanning-tree mode stp" instead of RSTP
2. Port not configured as portfast (waiting for STP convergence)
3. Link quality issues causing repeated BPDUs

**Check:**

```text

Cisco:
  show spanning-tree summary
  show spanning-tree interface detail
  show spanning-tree vlan 1
```

### Unexpected Root Bridge

**Cause:** Priority not explicitly set; switch with lowest MAC becomes root.

**Fix:** Set explicit priority on intended root.

```text

Cisco:
  spanning-tree vlan 1 priority 0
```

### Asymmetric Forwarding (One direction blocked)

**Cause:** Unidirectional link failure; loop guard can prevent.

**Fix:**

```text

Cisco:
  interface GigabitEthernet0/5
    spanning-tree guard loop
```

---

## Best Practices Summary

| Best Practice | Reason |
| --- | --------- |
| Use RSTP, not STP | 50x faster convergence |
| Set explicit root priorities | Avoid relying on MAC address tie-breaking |
| Use portfast on access ports | Faster end-host connectivity |
| Use BPDU guard on access ports | Prevent accidental loop creation |
| Use root guard on uplinks | Enforce root bridge location |
| Use loop guard on blocked ports | Protect against unidirectional failures |
| Document port costs and priorities | Make topology predictable and maintainable |
| Use PVST+ for load balancing (multi-VLAN) | Spread traffic across multiple root bridges |
| Monitor BPDU health | Early warning for link quality issues |

---

## Summary

STP/RSTP configuration revolves around **priority, cost, and port role**. Modern
deployments should use RSTP for fast convergence and combine it with portfast + BPDU
guard on access ports and root/loop guard on uplinks for a robust, loop-free topology.
