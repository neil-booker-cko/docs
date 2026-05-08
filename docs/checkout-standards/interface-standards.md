# Interface Configuration Standards

Physical and logical interface configuration for Cisco IOS-XE, FortiGate, and Meraki.

---

## Physical Interface Naming

### Cisco IOS-XE Interfaces

| Interface Type | Format | Example | Slots | Ports |
| --- | --- | --- | --- | --- |
| Gigabit Ethernet | `GigabitEthernet[S/P]` | `GigabitEthernet0/0` | 0-9 | 0-53 |
| Ten Gigabit Ethernet | `TenGigabitEthernet[S/P]` | `TenGigabitEthernet1/0` | 0-9 | 0-7 |
| Port Channel | `Port-channel[N]` | `Port-channel1` | N/A | 1-4096 |

### FortiGate Interfaces

| Interface Type | Format | Example | Notes |
| --- | --- | --- | --- |
| Physical Port | `port[N]` | `port1`, `port2` | Named per device |
| VLAN Subinterface | `port[N].[VID]` | `port1.100` | Tagged VLAN |
| Port Channel | `aggregate[N]` | `aggregate1` | LAG/bonding |

---

## Speed & Duplex Configuration

### Cisco IOS-XE Standards

| Link Type | Speed | Duplex | MTU | Notes |
| --- | --- | --- | --- | --- |
| Datacenter core | 10 Gbps | Full | 1500 | Fixed; negotiate disabled |
| Datacenter access | 1 Gbps | Full | 1500 | Fixed; negotiate disabled |
| Branch office | 1 Gbps | Full | 1500 | Fixed; negotiate disabled |
| WAN/Uplink | 1 Gbps (varies) | Full | 1500 | Carrier-negotiated |

### Speed Configuration Example

```ios
interface GigabitEthernet0/1
 speed 1000
 duplex full
 negotiation off
 no shutdown
!
```

### Auto-Negotiation Policy

**Standard:** Disable auto-negotiation on datacenter/office links; always explicit configuration.

**Rationale:** Fixed speed/duplex prevents negotiation timeouts and ensures predictable behavior.

```ios
interface GigabitEthernet0/0
 speed auto
 duplex auto
 negotiation auto
 ! This is ONLY used for ISP uplinks where carrier controls negotiation
!
```

---

## MTU Configuration

### Standard MTU Values

| Link Type | MTU | Notes |
| --- | --- | --- |
| Ethernet (standard) | 1500 | Default; no fragmentation |
| Jumbo Ethernet (DC) | 9000 | For storage/high-bandwidth links |
| IPsec VPN | 1400-1436 | Allow for encryption overhead |
| GRE Tunnel | 1400-1476 | GRE adds 24 bytes overhead |

### Path MTU Discovery (PMTUD)

**For IPv4:** Enable PMTUD (don't fragment bit honored).

```ios
interface GigabitEthernet0/1
 mtu 1500
 ip mtu 1500
 ip tcp adjust-mss 1380
!
```

**For IPv6:** Use path MTU discovery (enabled by default).

```ios
interface GigabitEthernet0/1
 mtu 1500
 ipv6 mtu 1500
!
```

---

## Flow Control & Pause Frames

### Flow Control Policy

**Standard:** Disable flow control on WAN uplinks; enable on switch-to-switch links.

| Link Type | Flow Control | Setting | Rationale |
| --- | --- | --- | --- |
| Switch-to-switch | Enabled | `flowcontrol send on` | Prevent buffer overflow |
| Router-to-switch | Disabled | `flowcontrol send off` | Router handles congestion via QoS |
| WAN uplink | Disabled | `flowcontrol send off` | ISP may not support; use QoS instead |

### Cisco IOS-XE Flow Control

```ios
interface GigabitEthernet1/0
 ! Switch-to-switch trunk
 flowcontrol send on
 flowcontrol receive on
!

interface GigabitEthernet0/0
 ! WAN uplink
 flowcontrol send off
 flowcontrol receive off
!
```

---

## Spanning Tree Per-Interface Configuration

### Access Port Settings

| Setting | Standard | Purpose |
| --- | --- | --- |
| Port Type | Access | Single VLAN only |
| STP Mode | Rapid PVST+ | Fast convergence |
| PortFast | Enabled | Skip listening/learning (access only) |
| BPDU Guard | Enabled | Disable port if BPDU received |
| BPDU Filter | Disabled | Allow BPDUs (protect, don't filter) |
| Root Guard | Disabled | Not applicable on access ports |

### Trunk Port Settings

| Setting | Standard | Purpose |
| --- | --- | --- |
| Port Type | Trunk | Multiple VLANs |
| STP Mode | Rapid PVST+ | Fast convergence per VLAN |
| PortFast | Trunk | Enable on all trunk links |
| BPDU Guard | Disabled | Trunks must accept BPDUs |
| BPDU Filter | Disabled | Standard STP operation |
| Root Guard | Enabled | Prevent non-core becoming root |

### Spanning Tree Configuration

```ios
interface GigabitEthernet0/0
 ! Access port
 switchport mode access
 switchport access vlan 100
 spanning-tree portfast
 spanning-tree bpduguard enable
!

interface GigabitEthernet0/1
 ! Trunk port (switch-to-switch)
 switchport mode trunk
 switchport trunk native vlan 999
 spanning-tree portfast trunk
 spanning-tree guard root
 spanning-tree bpduguard disable
!
```

---

## Neighbor Discovery (CDP & LLDP)

### CDP vs LLDP Policy

**Standard:** Use protocol based on connected device:

- **CDP:** Enabled on Cisco-facing interfaces (internal Cisco-to-Cisco links only)
- **LLDP:** Enabled on other device-facing interfaces (Cisco-to-FortiGate, Cisco-to-Meraki, etc.)

| Link Type | Protocol | Enabled | Purpose |
| --- | --- | --- | --- |
| Cisco-to-Cisco (internal) | CDP | Yes | Device discovery, neighbor info |
| Cisco-to-FortiGate | LLDP | Yes | Cross-vendor discovery |
| Cisco-to-Meraki | LLDP | Yes | Cross-vendor discovery |
| External uplinks | LLDP | Yes | Provider equipment discovery |
| All other | Both | Yes | Redundancy for discovery |

### Global Configuration

**Enable LLDP globally (runs on all interfaces by default):**

```ios
lldp run
!
```

**Enable CDP on specific Cisco-facing interfaces:**

```ios
interface GigabitEthernet0/1
 description CORE-SWITCH_GI0/1
 ! Cisco-facing interface: enable CDP
 cdp enable
 lldp transmit
 lldp receive
!

interface GigabitEthernet0/2
 description FIREWALL-FORTIGATE_GI0/1
 ! FortiGate-facing interface: LLDP only
 no cdp enable
 lldp transmit
 lldp receive
!
```

### LLDP Timers

```ios
lldp timer 30
lldp holdtime 120
lldp reinit 2
!
```

---

## Link Aggregation (LAG/Port Channel)

### Port Channel Configuration

**Standard:** Use LAG for redundancy on critical uplinks (switch-to-switch, router-to-switch).

| Parameter | Standard | Notes |
| --- | --- | --- |
| Protocol | LACP (802.3ad) | Dynamic; preferred over static |
| Mode | Active | Actively negotiate LAG |
| Member Interfaces | 2-4 links | Balance bandwidth; failover on member down |
| Load Balancing | Source/dest IP | Distribute traffic across members |
| Spanning Tree | Per VLAN | STP on port channel, not members |

### Cisco LAG Configuration

```ios
interface Port-channel1
 description CORE-TO-ACCESSSW
 switchport mode trunk
 switchport trunk native vlan 1
 spanning-tree guard root
!

interface GigabitEthernet1/0
 description CORE-TO-ACCESSSW-G1-0
 switchport mode trunk
 channel-group 1 mode active
!

interface GigabitEthernet1/1
 description CORE-TO-ACCESSSW-G1-1
 switchport mode trunk
 channel-group 1 mode active
!
```

### FortiGate Aggregate Configuration

```fortios
config system interface
    edit "aggregate1"
        set type aggregate
        set member "port1" "port2"
        set lacp-mode active
        set ip 10.0.1.1 255.255.255.0
    next
end
```

---

## Interface Descriptions

### Description Format

**Format:** `[Attached-Device]_[Attached-Interface]`

| Interface | Description | Attached Device |
| --- | --- | --- |
| `Gi0/1` | `AWSTGW_GI0/1` | AWS Transit Gateway |
| `Gi0/2` | `AZUREMSEE_GI0/1` | Azure ExpressRoute MSEE |
| `Gi0/3` | `GCPIC_GI0/1` | GCP Cloud Interconnect |
| `Gi1/0` | `LON-FW-PRI_GI0/0` | LON1-PFW-01A (primary) |
| `Gi1/1` | `LON-FW-SEC_GI0/0` | LON1-PFW-01B (secondary) |

### Description Configuration

```ios
interface GigabitEthernet0/1
 description AWS-TGW_GI0/1
 ip address 10.0.128.1 255.255.255.252
!

interface GigabitEthernet0/2
 description AZURE-MSEE_GI0/1
 ip address 10.0.129.1 255.255.255.252
!
```

---

## Shutdown Policy

### Interface Shutdown Rules

| Interface State | Reason | Action |
| --- | --- | --- |
| Active | In production | `no shutdown` |
| Inactive (planned) | Awaiting cable/device | Keep `shutdown` until ready |
| Decommissioned | No longer in use | `shutdown` + comment with date |
| Maintenance | Temporary disable | `shutdown` + record timestamp |

### Decommissioned Interface Example

```ios
interface GigabitEthernet0/7
 shutdown
 description DECOMMISSIONED-20260501-oldISP
!
```

---

## IP Address Assignment

### Loopback Addresses

**Standard:** One loopback per router (for iBGP, OOB management).

```ios
interface Loopback0
 description Mgmt-Loopback
 ip address 10.0.0.1 255.255.255.255
 ip ospf network point-to-point
!
```

### Management Interface

**Standard:** Dedicated management IP on separate interface (not data).

```ios
interface GigabitEthernet0/0
 description Mgmt-Interface
 ip address 10.0.10.1 255.255.255.0
 no ip route-cache
!
```

---

## QoS Marking on Interfaces

### Trust Boundary

Mark DSCP values only from **trusted sources** (internal switches, routers); untrust external/user traffic.

| Interface | Trust | DSCP Remark | Notes |
| --- | --- | --- | --- |
| Datacenter core (internal) | Yes | Trust incoming DSCP | Accept marked traffic |
| Office switch (internal) | Yes | Trust incoming DSCP | Accept marked traffic |
| ISP uplink (external) | No | Remark to 0 (CS0) | Reset DSCP; prevent injection |
| Wireless AP | Partial | Trust VoIP DSCP only | Only trust voice marking |

```ios
interface GigabitEthernet0/1
 ! Datacenter core (trusted)
 ip dscp config trust
!

interface GigabitEthernet0/0
 ! ISP uplink (untrusted)
 ip dscp config untrusted
 service-policy input UNTRUST-POLICE
!
```

---

## Meraki Cloud-Managed Interface Configuration

### Uplink Configuration

```text
Dashboard → Network Settings → Addressing and VLANs

Uplink 1 (Primary): WAN1 (Auto-DHCP or Static)
Uplink 2 (Secondary): WAN2 (Auto-DHCP or Static)
Failover: Primary > Secondary
```

### Port Configuration (Meraki Switches)

| Port Type | Speed | PoE | Spanning Tree | Example Port |
| --- | --- | --- | --- | --- |
| Server/Core | Auto or Fixed 1 Gbps | Off | Enabled | 1-2 (uplink) |
| Access-Device | Auto | On | BPDU Guard | 3-26 (APs, cameras) |
| Trunk | Auto | Off | Enabled | 47-48 (switch-to-switch) |

### Meraki Switch Port Configuration Example

```text
Dashboard → Switch → Ports

Port 1: Trunk (to core), Span Tree: Enabled
Port 3-26: Access (default VLAN 100), PoE: On, Span Tree: BPDU Guard
Port 47-48: Trunk (to other switch), Span Tree: Enabled
```

---

## Troubleshooting

### Common Interface Issues

| Issue | Diagnosis | Resolution |
| --- | --- | --- |
| Link down | Check physical cable | Verify cable integrity; check speed/duplex mismatch |
| Errors/CRC | Excessive collisions | Check duplex setting; test cable; monitor for electrical noise |
| MTU too small | Fragmentation, timeouts | Increase MTU or enable PMTUD; test Path MTU |
| LAG member down | One link in port channel failed | Check individual link state; replace faulty cable |
| STP loop | Repeated blocking | Verify BPDU Guard on access; check topology |

### Verification Commands

**Cisco IOS-XE:**

```ios
show interface GigabitEthernet0/1
show interface GigabitEthernet0/1 counters errors
show spanning-tree interface GigabitEthernet0/1 detail
show port-channel summary
```

---

## Related Standards

- [VLAN Standards](vlan-standards.md) — Interface VLAN assignment, trunking
- [HA Standards](ha-standards.md) — HA heartbeat interface configuration
- [Syslog & Monitoring](syslog-monitoring-standards.md) — Management interface source address
