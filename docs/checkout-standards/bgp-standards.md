# BGP Configuration Standards

BGP configuration and operational standards for Checkout. All BGP configuration must use the
modern address-family approach for neighbor activation, route filtering, and policy application.
Network statements are deprecated; all VLAN/VRF routing must be explicitly configured within
address families.

---

## BGP Process Configuration

**Standard:** Single BGP process (AS 65000) for all VRFs.

```ios
router bgp 65000
 bgp router-id 10.0.0.1
 bgp log-neighbor-changes
 bgp graceful-restart
```

**Important:** Do NOT use network statements. All route advertisements and neighbor activation
must occur within address-family configuration blocks (see Address Families section below).

---

## BGP Timers & BFD (Recommended)

**Standard:** Use BFD for fast failure detection on all BGP neighbors. BFD enables sub-second
convergence and is strongly recommended for critical cloud connectivity links.

### Standard Timers (without BFD)

| Timer | Value | Use Case |
| --- | --- | --- |
| Keepalive | 10 seconds | Normal operation (fallback only) |
| Hold time | 30 seconds | Detection timeout (3x keepalive) |

### Recommended: Fast Failure (with BFD)

| Timer | Value | Use Case |
| --- | --- | --- |
| Keepalive | 60 seconds | BFD handles fast detection |
| Hold time | 180 seconds | Longer hold (BFD sub-second) |
| BFD interval | 300ms tx/rx | Sub-second failover |

**Configuration (BFD preferred):**

Define a BFD template at the global level, then apply to interfaces:

```ios
bfd-template single-hop BFD_STANDARD
 interval 300 min_rx 300 multiplier 3
!
interface GigabitEthernet0/1
 ip address 169.254.1.1 255.255.255.252
 bfd template BFD_STANDARD
!
router bgp 65000
 neighbor 169.254.1.2 timers 60 180
 neighbor 169.254.1.2 fall-over bfd
!
```

**Configuration (without BFD - fallback only):**

```ios
neighbor 169.254.1.2 timers 10 30
```

---

## BGP Authentication (Recommended)

**Standard:** Enable MD5 authentication on all BGP neighbors to prevent unauthorized route
injection and session hijacking. Use `neighbor password` command per-neighbor or globally.

```ios
router bgp 65000
 neighbor 169.254.1.2 password MyBGPAuth123!
 neighbor 172.16.0.2 password MyBGPAuth456!
!
```

**Key Management:**

- Rotate authentication keys annually
- Use strong, unique passwords per peer
- Document changes in change log
- Coordinate key rotation with peer networks (AWS, Azure, GCP)

---

## Address Families and VRF Configuration (Modern Approach)

**Standard:** Use address-family configuration for ALL neighbor activation, redistribution, route
filtering, and VRF-specific policies. This is the modern, scalable approach and is required for
all new BGP configurations.

**Key Rules:**

- Define each neighbor in address-family block (not in global config)
- Use one address-family per VRF
- Apply prefix-lists and route-maps within address-family
- Do NOT use network statements; use redistribute or explicit neighbor advertisement

```ios
router bgp 65000
 address-family ipv4 vrf AWS
  neighbor 169.254.1.2 activate
  neighbor 169.254.1.2 prefix-list PL_AWS_INTERNAL in
  neighbor 169.254.1.2 route-map RM_AWS_IN in
  neighbor 169.254.1.2 route-map RM_AWS_OUT out
 exit-address-family

 address-family ipv4 vrf Azure
  neighbor 172.16.0.2 activate
  neighbor 172.16.0.2 prefix-list PL_AZURE_INTERNAL in
  neighbor 172.16.0.2 route-map RM_AZURE_IN in
  neighbor 172.16.0.2 route-map RM_AZURE_OUT out
 exit-address-family
```

---

## Route Filtering Standards

### Cloud Provider Routes (Inbound)

Accept all routes from cloud providers without filtering. BGP community filtering may be
applied at the overlay layer (FortiGate).

### Internal Routes (Outbound to Cloud)

Advertise only the transport link subnets to cloud providers. DO NOT advertise internal
prefixes.

---

## FortiGate BGP Configuration

**Standard:** FortiGate BGP configuration uses similar concepts to Cisco but with different syntax.
Configure neighbors at the global level with VRF-specific address families for route filtering
and policy application.

### BGP Process Configuration (FortiGate)

```fortios
config router bgp
    set as 65000
    set router-id 10.0.0.1
    set graceful-restart enable
    set graceful-restart-time 120
!
```

### Address Families and Neighbors (FortiGate)

```fortios
config router bgp
    config neighbor
        edit "169.254.1.2"
            set remote-as 64512
            set description "AWS-TGW-DX-64512-us"
            set keep-alive-timer 60
            set holdtime-timer 180
            set bfd enable
        next
        edit "172.16.0.2"
            set remote-as 12076
            set description "AZURE-MSEE-12076-primary"
            set keep-alive-timer 60
            set holdtime-timer 180
            set bfd enable
        next
    end
    config address-family
        config ipv4
            edit "AWS"
                config neighbor
                    edit "169.254.1.2"
                        set activate enable
                        set prefix-list-in "PL_AWS_INTERNAL"
                        set route-map-in "RM_AWS_IN"
                        set route-map-out "RM_AWS_OUT"
                    next
                end
            next
            edit "Azure"
                config neighbor
                    edit "172.16.0.2"
                        set activate enable
                        set prefix-list-in "PL_AZURE_INTERNAL"
                        set route-map-in "RM_AZURE_IN"
                        set route-map-out "RM_AZURE_OUT"
                    next
                end
            next
        end
    end
end
```

---

## Interface Failure Detection and BGP Failover

**Standard:** Link physical interface state to BGP convergence. When a monitored interface fails,
trigger immediate BGP neighbor reset or attribute manipulation. This ensures sub-second failover
without waiting for BFD timeout.

### Cisco: Track Objects and BFD Fall-Over

#### Option 1: BFD Fall-Over (Recommended)

BFD provides sub-second detection when enabled on BGP neighbors:

```ios
router bgp 65000
 neighbor 169.254.1.2 fall-over bfd
!
```

#### Option 2: Track Objects for Interface State

Use Track objects to monitor interface line-protocol and trigger manual failover:

```ios
track 1 interface GigabitEthernet0/1 line-protocol
 delay down 5 up 5
!
route-map RM_AWS_FAILOVER permit 10
 match track 1
 set local-preference 200
!
router bgp 65000
 address-family ipv4 vrf AWS
  neighbor 169.254.1.2 route-map RM_AWS_FAILOVER in
 exit-address-family
!
```

When GigabitEthernet0/1 goes down, the track object triggers, and the route-map applies lower
local-preference, forcing failover to secondary paths.

### FortiGate: Link-Down Failover and Monitor Objects

#### Option 1: Link-Down Failover (Recommended)

Enable link-down failover on neighbors to trigger graceful BGP shutdown on interface failure:

```fortios
config router bgp
    config neighbor
        edit "169.254.1.2"
            set link-down-failover enable
        next
    end
end
```

When port1 (attached to this neighbor) goes down, BGP immediately removes routes from the peer.

#### Option 2: Monitor Objects for Proactive Health Checks

Create monitor objects to proactively detect link health before interface failure:

```fortios
config system link-monitor
    edit "AWS_PRIMARY_HEALTH"
        set server "169.254.1.2"
        set protocol ping
        set interval 3
        set timeout 5
        set failure-count 3
        set recovery-count 5
        set gateway-ip 169.254.1.1
    next
end

config router bgp
    config neighbor
        edit "169.254.1.2"
            set link-down-failover enable
        next
    end
end
```

When the monitor object detects 3 consecutive failures (9 seconds), BGP routes are withdrawn
immediately, triggering failover to secondary peers before the underlying interface may still be
up.

---

## BGP Communities

TODO: Define standard community values

---

## Graceful Restart

**Standard:** Enable BGP graceful restart for planned maintenance.

```ios
bgp graceful-restart
```

---

## BFD Configuration

See [Cisco BFD Configuration](../cisco/bfd-config.md) for detailed setup.

---

## Troubleshooting Commands

```ios
show bgp vpnv4 unicast all summary
show bgp vpnv4 unicast vrf AWS summary
show bgp vpnv4 unicast vrf AWS neighbors 169.254.1.2
debug bgp keepalives
```

---

## Related Standards

- [Routing Design](routing-design.md)
- [Naming Conventions](naming-conventions.md)
