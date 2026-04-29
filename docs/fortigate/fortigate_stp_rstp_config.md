# FortiGate STP/RSTP Configuration Guide

Configuration reference for Spanning Tree Protocol on Fortinet FortiGate managed
switches.

## Overview

FortiGate's managed switch supports STP (IEEE 802.1D) and RSTP (IEEE 802.1w) on a
per-device basis. This guide covers bridge priority, port configuration, and edge port
settings.

---

## Quick Start

```text
config switch-controller
  config managed-switch
    edit <switch-id>
      set stp-mode rapid              ! Enable RSTP (recommended)
      set stp-priority 32768          ! Bridge priority (default)

      config ports
        edit "port1"
          set edge-port enable        ! PortFast equivalent
          set stp-bpdu-guard enable   ! BPDU guard
        next
      end
    next
  end
end
```

---

## Global STP Configuration

### Set STP Mode

```text

config switch-controller
  config managed-switch
    edit <switch_name>
      ! Enable RSTP (faster convergence)
      set stp-mode rapid

      ! Or use standard STP (slower)
      set stp-mode standard

      ! Disable STP entirely
      set stp-mode disable
    next
  end
end
```

### Configure Bridge Priority

Bridge priority determines root bridge selection. Lower value = higher priority = more likely to be
root.

**Valid values:** 0 to 61440 (increments of 4096)
**Default:** 32768

```text

config switch-controller
  config managed-switch
    edit <switch_name>
      ! Primary root (priority 0)
      set stp-priority 0

      ! Or backup root (priority 4096)
      set stp-priority 4096
    next
  end
end
```

### RSTP Timers

```text

config switch-controller
  config managed-switch
    edit <switch_name>
      set stp-hello-time 2      ! BPDU hello interval (1-10 seconds)
      set stp-max-age 20        ! Max age for received BPDU (6-40 seconds)
      set stp-fwd-delay 15      ! Forward delay (4-30 seconds)
    next
  end
end
```

---

## Per-Port Configuration

### Enable Edge Port (PortFast Equivalent)

Edge ports are connected to end devices (hosts, printers) and don't require STP processing. They
transition
directly to forwarding.

```text

config switch-controller
  config managed-switch
    edit <switch_name>
      config ports
        edit "port1"
          set edge-port enable    ! Enable PortFast behavior
        next
        edit "port2"
          set edge-port disable   ! Trunk port, normal STP processing
        next
      end
    next
  end
end
```

### BPDU Guard (Protect Access Ports)

Shuts down port if a BPDU is received on an edge port (prevents accidental switch connections).

```text

config switch-controller
  config managed-switch
    edit <switch_name>
      config ports
        edit "port1"
          set edge-port enable
          set stp-bpdu-guard enable
        next
      end
    next
  end
end
```

### Root Guard (Uplink Ports)

Prevents port from accepting superior BPDUs (blocks if a better bridge appears).

```text

config switch-controller
  config managed-switch
    edit <switch_name>
      config ports
        edit "port48"
          set stp-root-guard enable
          description "Uplink to core"
        next
      end
    next
  end
end
```

### Configure Port Priority and Cost

Adjusts path selection via port priority (tie-breaking) and STP cost (link preference).

```text

config switch-controller
  config managed-switch
    edit <switch_name>
      config ports
        edit "port1"
          set stp-path-cost 4        ! Set cost for path selection
          set stp-priority 128       ! Port priority (0-240, increments of 16)
        next
        edit "port2"
          set stp-path-cost 8        ! Higher cost = less preferred
        next
      end
    next
  end
end
```

**Standard costs:**

- 10 Gbps: 2
- 1 Gbps: 4
- 100 Mbps: 19
- 10 Mbps: 100

---

## Complete Configuration Example

### Scenario: Two-Switch Redundancy

```text

        FortiSwitch 1 (Root)
             / port48 (primary)
            /
       FortiSwitch 2 (Backup)
             \ port48 (backup)
              \
           Access ports (edge ports)
```

**FortiSwitch 1 (Primary Root):**

```text

config switch-controller
  config managed-switch
    edit "fortiswitch1"
      set stp-mode rapid
      set stp-priority 0              ! Primary root

      ! Access ports (connected to hosts)
      config ports
        edit "port1"
          set edge-port enable
          set stp-bpdu-guard enable
          description "Access: VLAN 100"
        next

        edit "port2"
          set edge-port enable
          set stp-bpdu-guard enable
          description "Access: VLAN 100"
        next

        ! Uplink to FortiSwitch 2
        edit "port48"
          set edge-port disable       ! Trunk, normal STP
          set stp-root-guard enable
          set stp-path-cost 4
          description "Uplink to FS2"
        next
      end
    next
  end
end
```

**FortiSwitch 2 (Backup Root):**

```text

config switch-controller
  config managed-switch
    edit "fortiswitch2"
      set stp-mode rapid
      set stp-priority 4096           ! Backup root

      config ports
        edit "port1"
          set edge-port enable
          set stp-bpdu-guard enable
          description "Access: VLAN 100"
        next

        edit "port2"
          set edge-port enable
          set stp-bpdu-guard enable
          description "Access: VLAN 100"
        next

        ! Uplink to FortiSwitch 1
        edit "port48"
          set edge-port disable       ! Trunk
          set stp-root-guard enable
          set stp-path-cost 4
          description "Uplink to FS1"
        next
      end
    next
  end
end
```

---

## Verification and Monitoring

### Check STP Status

```text

diagnose switch-controller managed-switch <switch-name> stp-status

! Output shows:
! Bridge ID, Root ID, Bridge Priority, Port List with roles
```

### View STP Port Details

```text

diagnose switch-controller managed-switch <switch-name> stp-port

! Shows each port's role (root, designated, alternate), state (forwarding, discarding)
```

### Verify Edge Port Configuration

```text

get switch-controller managed-switch <switch-name>

! Look for port configuration; edge-port should be enabled on access ports
```

### Check BPDU Guard Status

```text

diagnose switch-controller managed-switch <switch-name> stp-status

! Alerts will show if BPDU guard triggered on any port
```

---

## Common Issues and Fixes

### Issue: Port Blocked Unexpectedly

**Cause:** Edge port received a BPDU (rogue switch connected).

**Solution:**

```text

! BPDU guard prevents connectivity. Investigate the attached device.
! Once threat is removed:

config switch-controller
  config managed-switch
    edit <switch-name>
      config ports
        edit <port>
          ! Disable BPDU guard temporarily to troubleshoot
          set stp-bpdu-guard disable
        next
      end
    next
  end
end
```

### Issue: Slow Convergence

**Cause:** STP mode is set to "standard" instead of "rapid".

**Fix:**

```text

config switch-controller
  config managed-switch
    edit <switch-name>
      set stp-mode rapid
    next
  end
end
```

### Issue: Wrong Root Bridge

**Cause:** Priority not explicitly set; lowest MAC becomes root.

**Fix:**

```text

config switch-controller
  config managed-switch
    edit <switch-name>
      set stp-priority 0              ! Make this switch root
    next
  end
end
```

### Issue: Preferred Uplink Not Being Used

**Cause:** Cost not adjusted on preferred port.

**Fix:**

```text

config switch-controller
  config managed-switch
    edit <switch-name>
      config ports
        edit "port48"
          set stp-path-cost 4         ! Preferred uplink (lower cost)
        next
        edit "port49"
          set stp-path-cost 8         ! Backup uplink (higher cost)
        next
      end
    next
  end
end
```

---

## Best Practices

| Practice | Reason |
| --- | --------- |
| Use RSTP (`set stp-mode rapid`) | Converges in milliseconds vs STP's 50 seconds |
| Set explicit bridge priority | Predictable root bridge election |
| Enable edge port on access ports | Faster end-device connectivity |
| Enable BPDU guard on edge ports | Prevent accidental loop creation |
| Enable root guard on uplinks | Prevent rogue switch takeover |
| Document port costs | Maintain predictable topology |
| Monitor STP regularly | Early detection of topology changes |

---

## Configuration Summary Table

| Setting | Command | Default | Typical Value |
| --- | --------- | --- | --------- |
| STP Mode | `set stp-mode` | standard | rapid |
| Bridge Priority | `set stp-priority` | 32768 | 0 (root) or 4096 (backup) |
| Edge Port | `set edge-port enable` | disable | enable (access ports only) |
| BPDU Guard | `set stp-bpdu-guard enable` | disable | enable (edge ports) |
| Root Guard | `set stp-root-guard enable` | disable | enable (uplink ports) |
| Path Cost | `set stp-path-cost` | auto | 4 (1 Gbps) |
| Port Priority | `set stp-priority` | 128 | varies |
| Hello Time | `set stp-hello-time` | 2 | 2 |
| Max Age | `set stp-max-age` | 20 | 20 |
| Forward Delay | `set stp-fwd-delay` | 15 | 15 |
