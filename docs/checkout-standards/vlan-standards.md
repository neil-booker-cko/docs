# VLAN Configuration Standards

VLAN allocation, tagging, trunking, and naming conventions for Cisco IOS-XE and FortiGate.
VLANs differ between datacenters and office locations.

---

## VLAN Allocation Scheme

### Datacenter VLAN Ranges

| VLAN Range | Purpose | Allocation | Notes |
| --- | --- | --- | --- |
| 1 | Default VLAN | Reserved | Do not use; VLAN 999 is native VLAN on trunks |
| 10-19 | Management | Static allocation | Out-of-band, not routed to data VLANs |
| 999 | Dummy/Shutdown (Native) | Static allocation | Unused VLAN; all interfaces in this VLAN are shutdown; used as native VLAN on trunks |
| 20-29 | Reserved | N/A | Future use |
| 100-199 | Production Data | Static allocation | Primary business applications |
| 200-299 | DR/Backup | Static allocation | Disaster recovery, backup systems |
| 300-399 | Voice/SIP | Static allocation | Voice gateways, SIP signaling |
| 400-499 | Storage (SAN) | Static allocation | iSCSI, NAS traffic isolation |
| 500-599 | Reserved | N/A | Future use |
| 800-899 | AWS Direct Connect | Static allocation | AWS VPC transport |
| 900-999 | Azure/GCP | Static allocation | Azure ER, GCP IC transport |

### Office VLAN Ranges

| VLAN Range | Purpose | Allocation | Notes |
| --- | --- | --- | --- |
| 1 | Default VLAN | Reserved | Do not use; VLAN 999 is native VLAN on trunks |
| 10-19 | Management | Static allocation | Out-of-band network management |
| 999 | Dummy/Shutdown (Native) | Static allocation | Unused VLAN; all interfaces in this VLAN are shutdown; used as native VLAN on trunks |
| 100-199 | Corporate Data | Static or dynamic | Employee workstations, desktops |
| 300-399 | Voice/VoIP | Static allocation | IP phones, call control |
| 400-499 | IoT/Sensors | Static allocation | Printers, cameras, access control |
| 500-599 | Guest/Visitor | Dynamic allocation | Temporary/guest WiFi access |
| 600-699 | Wireless (5GHz) | Static allocation | 802.11ac/ax high-bandwidth |
| 800-899 | Site-to-Site VPN | Static allocation | Branch-to-HQ VPN transport |

### VLAN Naming Convention

Standard VLAN numbering across all sites (no site-specific VLAN IDs). Use consistent
numbers regardless of location for ease of troubleshooting.

**Example — Dublin Datacenter (ELD7):**

| VLAN | Name | Purpose |
| --- | --- | --- |
| 10 | Mgmt | Out-of-band management |
| 100 | Prod-Data | Production applications |
| 200 | DR-Backup | Disaster recovery systems |
| 300 | Voice | SIP gateways |
| 400 | Storage | SAN/iSCSI |
| 800 | AWS-DX | AWS Direct Connect |

**Example — London Office (LON1):**

| VLAN | Name | Purpose |
| --- | --- | --- |
| 10 | Mgmt | Management access |
| 100 | Corp-Data | Employee workstations |
| 300 | Voice | VoIP phones |
| 400 | IoT | Printers, cameras |
| 500 | Guest | Visitor WiFi |
| 600 | Wireless | High-speed wireless |

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

**Standard:** All inter-switch and uplink links must use 802.1Q tagging (not ISL). Use VLAN 999
(Dummy/Shutdown) as the native VLAN on all trunks and shutdown all interfaces assigned to VLAN 999
to prevent accidental native VLAN leaks.

| Link Type | Native VLAN | Tagged VLANs | Notes |
| --- | --- | --- | --- |
| Switch-to-Switch Trunk | 999 (Dummy/Shutdown) | 2-998, 1000-1005 | All active VLANs tagged; native is unused |
| Access-to-Switch | Assigned per port | None | Each access port in single VLAN |
| Router Subinterface | N/A (per trunk) | All routed VLANs | One subinterface per VLAN |
| Firewall Trunk | 999 (Dummy/Shutdown) | All transit VLANs | Native VLAN unused; all transit traffic tagged |

### Cisco IOS-XE Trunk Configuration

**VLAN 999 Setup (one-time on each switch):**

```ios
vlan 999
 name Dummy-Shutdown
!
interface GigabitEthernet0/1
 switchport access vlan 999
 shutdown
!
interface GigabitEthernet0/2
 switchport access vlan 999
 shutdown
!
```

**Trunk Configuration (all switch-to-switch and uplinks):**

```ios
interface GigabitEthernet0/48
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 2-998,1000-1005
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
