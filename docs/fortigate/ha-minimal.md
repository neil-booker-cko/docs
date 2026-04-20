# FortiGate HA Minimal Configuration

This template enables FGCP (FortiGate Clustering Protocol) active-passive HA. Two or more FortiGates
synchronize configuration and sessions, with one device active and others on standby.

## Configuration Breakdown

```fortios
config system ha
  set mode a-p
  set group-name "FGT-GROUP"
  set priority 200
  set interface "port3"
  set ha-mgmt-status enable
```

Configures HA cluster:

- **mode a-p** = active-passive (one active, others standby; use `a-a` for active-active)
- **group-name "FGT-GROUP"** = cluster name (must match on all members)
- **priority 200** = HA priority (higher wins; range 0-255)
- **interface "port3"** = dedicated heartbeat/sync interface (replace with your port)
- **ha-mgmt-status enable** = enable management over HA link

```fortios
  set ha-mgmt-interfaces
    config ha-mgmt-interface
      edit 1
        set interface "port1"
      next
    end
```

Designates management interfaces for HA (port1 here; add more as needed).

```fortios
  set hbdev "port3" 0
  set session-sync enable
  set override disable
  set password "HA_PASSWORD_HERE"
  set heartbeat-interval 2
  set heartbeat-lost-threshold 20
```

HA protocol settings:

- **hbdev "port3" 0** = heartbeat device and priority
- **session-sync enable** = synchronize sessions (needed for stateful failover)
- **override disable** = prevent standby from overriding active (use `enable` to allow active
  restart)
- **password** = cluster authentication (minimum 6 characters)
- **heartbeat-interval 2** = heartbeat period in seconds
- **heartbeat-lost-threshold 20** = declare peer dead after 20 missed heartbeats (~40 seconds
  with 2s interval)

```fortios
config system interface
  edit "port3"
    set vdom "root"
    set ip 192.168.100.1 255.255.255.0
    set type physical
  next
end
```

Configures the heartbeat/sync interface with an IP address (replace with your HA network).

## Customization

### Change HA Mode

For active-active clustering (both devices active):

```fortios
set mode a-a
! Both devices forward traffic simultaneously
! Requires careful policy configuration
```

### Change Priority

On backup device, use lower priority:

```fortios
set priority 100
! Device with 200 is active; device with 100 is standby
```

### Change Heartbeat Interface

Replace `port3` with your dedicated HA/sync interface:

```fortios
set interface "port4"
set hbdev "port4" 0
```

### Change Heartbeat Timers

For faster failure detection:

```fortios
set heartbeat-interval 1
set heartbeat-lost-threshold 10
! Detects failure in ~10 seconds
```

For slower detection (less traffic):

```fortios
set heartbeat-interval 5
set heartbeat-lost-threshold 10
! Detects failure in ~50 seconds
```

### Enable Override (Allow Restart)

Permit active device to take over when standby restarts:

```fortios
set override enable
! If active device reboots, standby becomes active
! If active comes back, it becomes active again
```

### Add More Management Interfaces

For multiple LAN connections:

```fortios
set ha-mgmt-interfaces
  config ha-mgmt-interface
    edit 1
      set interface "port1"
    next
    edit 2
      set interface "port2"
    next
  end
```

### Enable FGCP Keep-Alive on Data Interfaces

To detect link failures on LAN/WAN ports:

```fortios
set ha-member-tags
  edit 1
    set interface "port1"
  next
  edit 2
    set interface "port2"
  next
end
```

## Verification

On active device:

```fortios
get system ha status
! Check: Status = "enabled", Role = "active"

get system ha peer
! Check: Cluster members and sync status

diagnose sys ha status
! Detailed HA status and configuration
```

On standby device:

```fortios
get system ha status
! Check: Role = "backup" or "secondary"
```

Monitor failover:

```fortios
diagnose sys ha transition
! Check: Failover events and transitions
```

- Add BFD for faster detection (see [BFD minimal](bfd-minimal.md))
- Implement session state sync over dedicated link
- Review [VRRP minimal](vrrp-minimal.md) for per-subnet virtual IP failover
