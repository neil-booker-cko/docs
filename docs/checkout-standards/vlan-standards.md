# VLAN Configuration Standards

VLAN allocation, tagging, trunking, and naming conventions for Cisco IOS-XE and FortiGate.

---

## VLAN Allocation Scheme

### Standard VLAN Ranges

| VLAN Range | Purpose | Allocation | Notes |
| --- | --- | --- | --- |
| 1 | Default VLAN | Reserved | Do not use for data; must untagged native VLAN on trunks |
| 10-99 | Management | Static allocation | Out-of-band, not routed to data VLANs by default |
| 100-199 | Data - Primary | Dynamic or static | Primary business applications |
| 200-299 | Data - Secondary | Dynamic or static | Secondary/backup applications |
| 300-399 | Voice/VoIP | Static allocation | QoS priority, no data traffic |
| 400-499 | IoT/Sensors | Static allocation | Isolated, restricted routing |
| 500-599 | Guest/Temporary | Dynamic or static | No access to internal resources |
| 600-699 | DMZ/Public | Static allocation | Inbound-only, firewalled |
| 700-799 | Reserved | N/A | Future use |
| 800-999 | Cloud/WAN | Static allocation | AWS, Azure, GCP VPN transport |
| 1000-1094 | Extended range | Static allocation | If 802.1Q extended VLANs needed |

### Per-Site VLAN Assignment

Standard VLAN numbering across all sites (no site-specific VLAN IDs). Use consistent
numbers regardless of location for ease of troubleshooting.

**Example — London office (LON1):**

| VLAN | Name | Purpose |
| --- | --- | --- |
| 10 | Mgmt-LON | Management access (LON datacenter/office) |
| 100 | Data-Primary | Primary business systems |
| 300 | Voice-LON | VoIP phones, call control |
| 400 | IoT-Sensors | Printers, cameras, access control |
| 500 | Guest-LON | Visitor WiFi, no data access |

---

## VLAN Naming Conventions

**Format:** `<PURPOSE>-<SITE>` or `<PURPOSE>` (if global)

### Standard VLAN Names

| VLAN ID | Name | Scope |
| --- | --- | --- |
| 10 | Mgmt | Global (management) |
| 100 | Data | Global (primary data) |
| 200 | Data-Secondary | Global (secondary data) |
| 300 | Voice | Global (VoIP) |
| 400 | IoT | Global (sensors/constrained) |
| 500 | Guest | Global (guest/temporary) |
| 600 | DMZ | Global (inbound-only) |
| 800-899 | AWS | Global (AWS transport) |
| 900-999 | Azure / GCP | Global (Azure/GCP transport) |

Site-specific VLANs (wireless, branch-specific):

| VLAN ID | Name | Scope |
| --- | --- | --- |
| 10 | Mgmt | All sites (same VLAN ID) |
| 100 | Data-Primary | All sites (same VLAN ID) |

---

## VLAN Tagging & Trunking

### 802.1Q Tagging

**Standard:** All inter-switch and uplink links must use 802.1Q tagging (not ISL).

| Link Type | Native VLAN | Tagged VLANs | Notes |
| --- | --- | --- | --- |
| Switch-to-Switch Trunk | 1 (default) | 2-1005 (all except 1) | VLAN 1 untagged for backward compatibility |
| Access-to-Switch | Assigned per port | None | Each access port in single VLAN |
| Router Subinterface | N/A (per trunk) | All routed VLANs | One subinterface per VLAN |
| Firewall Trunk | 1 (default) | All transit VLANs | Firewall enforces policies per VLAN |

### Cisco IOS-XE Trunk Configuration

```ios
interface GigabitEthernet0/1
 switchport mode trunk
 switchport trunk native vlan 1
 switchport trunk allowed vlan 1-1005
 no shutdown
!
```

### FortiGate VLAN Trunk Configuration

```fortios
config system interface
    edit "port1"
        set vdom "root"
        set ip 10.0.1.1 255.255.255.0
        set type aggregate
    next
    edit "port1.100"
        set vdom "root"
        set vlanid 100
        set interface "port1"
        set ip 10.1.0.1 255.255.255.0
    next
end
```

---

## Spanning Tree Per VLAN (PVST)

### PVST Configuration

Enable Per-VLAN Spanning Tree to optimize traffic per VLAN.

| Setting | Standard | Notes |
| --- | --- | --- |
| Mode | PVST+ (Cisco) or MSTP (multi-VLAN) | PVST+ preferred for simplicity |
| Bridge Priority | Datacenter core: 4096; Secondary: 8192 | Lower priority = root bridge for VLAN |
| Port Cost | Auto (based on speed) | Do not manually override |
| Port Priority | Default (128) | Only override for tie-breaking |
| BPDU Guard | Enabled on access ports | Prevent loop attacks from end devices |
| Root Guard | Enabled on non-core ports | Prevent non-core switch becoming root |

### Cisco IOS-XE Spanning Tree Configuration

```ios
spanning-tree mode pvst
spanning-tree vlan 100 priority 4096
spanning-tree vlan 300 priority 8192
!
interface GigabitEthernet0/1
 spanning-tree bpduguard enable
 spanning-tree guard root
!
```

---

## VLAN Access Control

### Access Port Configuration

| Setting | Standard | Purpose |
| --- | --- | --- |
| Mode | Access (not trunk) | Single VLAN per port |
| Spanning Tree | PortFast (access), normal (server) | Avoid STP delays on access ports |
| BPDU Guard | Enabled | Prevent accidental loop creation |
| Dynamic VLAN Assignment | Disabled (static VLAN) | Fixed VLAN assignment per switch port |

### Dynamic VLAN Assignment (Optional)

If using 802.1X or MAC-based assignment:

- **Authentication:** 802.1X with RADIUS backend (ACS, ISE)
- **Fallback VLAN:** Guest VLAN for non-compliant devices
- **Reauthentication:** Every 24 hours
- **Logoff Action:** Return to default VLAN

---

## VLAN Routing (Inter-VLAN Routing)

### Routing Architecture

All VLAN-to-VLAN routing must pass through a router (Cisco, FortiGate, or virtual router).

| Routing Method | Advantage | Limitation |
| --- | --- | --- |
| Router-on-a-stick | Simple setup | Single uplink; performance bottleneck |
| Multilayer Switch (Cisco Catalyst) | Distributed routing; better performance | Higher cost |
| FortiGate (security edge) | Integrated firewall + routing | Centralized (all traffic through FW) |

### Default Route Per VLAN

All VLANs must have a default gateway:

| VLAN | Gateway | Priority |
| --- | --- | --- |
| 10 (Mgmt) | 10.0.10.1 (local router) | Primary |
| 100 (Data) | 10.0.100.1 (firewall/router) | Primary |
| 300 (Voice) | 10.0.30.1 (voice gateway) | Primary |

---

## VLAN Isolation & Access Control

### Data VLAN Isolation

By default:

- **VLAN 100 ↔ VLAN 200:** No cross-routing (different subnets)
- **VLAN 300 (Voice) ↔ VLAN 100 (Data):** Allow inbound RTP (UDP 5000-5999) only
- **VLAN 400 (IoT) ↔ All data VLANs:** Deny (except DNS outbound)
- **VLAN 500 (Guest) ↔ Internal VLANs:** Deny all

Enforce via:

1. **Firewall policies** (FortiGate, Meraki)
2. **Access lists** (Cisco router on trunk)
3. **VRF separation** (if using VRF-Lite)

### Management VLAN (VLAN 10)

- **Access:** SSH from specific admin subnets only
- **Isolation:** No routing to data/voice VLANs
- **Monitoring:** SNMP from dedicated NMS server only

---

## Voice VLAN Configuration

### Cisco IOS-XE Voice VLAN

```ios
interface GigabitEthernet0/1
 switchport mode access
 switchport access vlan 100
 switchport voice vlan 300
 spanning-tree portfast
!
```

### FortiGate Voice VLAN

```fortios
config system interface
    edit "voice-vlan"
        set ip 10.0.30.1 255.255.255.0
        set vlanid 300
    next
end
```

---

## VLAN Monitoring & Troubleshooting

### Verification Commands

**Cisco IOS-XE:**

```ios
show vlan brief
show spanning-tree vlan 100
show interface GigabitEthernet0/1 switchport
show interface trunk
```

**FortiGate:**

```fortios
get system interface | grep -A 5 vlanid
diagnose sys vlan list
```

### Common Issues

| Issue | Cause | Resolution |
| --- | --- | --- |
| VLAN traffic not routing | Native VLAN mismatch | Verify native VLAN same on both trunk ends |
| STP blocking port | Loop detected | Check cable; enable BPDU Guard on edge ports |
| Hosts can't reach gateway | VLAN not routed | Add VLAN interface to router; set default route |
| Voice/data intermingling | Incorrect VLAN assignment | Verify switch port config and 802.1Q tags |

---

## Related Standards

- [Interface Configuration Standards](interface-standards.md) — Speed, MTU, spanning tree per port
- [Naming Standards](naming-conventions.md) — VLAN and interface naming
- [Security Hardening](security-hardening.md) — VLAN-level access control
- [Firewall Policy Standards](firewall-standards.md) — Inter-VLAN traffic policies
