# CDP vs LLDP — Neighbor Discovery Protocols

CDP (Cisco Discovery Protocol) and LLDP (Link Layer Discovery Protocol) both solve the
same fundamental problem: discovering and sharing information with directly connected
neighbors at Layer 2. CDP is Cisco proprietary and has been the default on Cisco devices
since the early 1990s. LLDP is an IEEE standard (802.1AB) designed for vendor-neutral
discovery and is now mandated in many networks. Both protocols send periodic advertisements
that are not forwarded by bridges, ensuring link-local neighbor awareness without flooding
the network.

For detailed frame formats, see [CDP Packet Format](../packets/cdp.md) and
[LLDP Packet Format](../packets/lldp.md).

---

## At a Glance

| Property | CDP (v2) | LLDP (IEEE 802.1AB) |
| --- | --- | --- |
| **Standard** | Cisco proprietary | IEEE 802.1AB-2016 (open) |
| **Transport** | Layer 2 (SNAP, LLC) | Layer 2 (EtherType `0x88CC`) |
| **Destination MAC** | `01:00:0C:CC:CC:CC` | `01:80:C2:00:00:0E` |
| **Encapsulation** | IEEE 802.3 + LLC + SNAP | Direct Ethernet II |
| **Default TX Interval** | 60 seconds | 30 seconds |
| **Default TTL / Hold Time** | 180 seconds | 120 seconds (4× TX interval) |
| **Information exchanged** | Device ID, port, platform, capabilities, software version, IP address | Chassis ID, port ID, TTL, system name, description, capabilities, management IP |
| **Extensibility** | TLV-based, proprietary extensions | TLV-based, organisational-specific TLVs |
| **Hardware requirement** | Cisco devices only | Any vendor (Cisco, Arista, Juniper, Fortinet, etc.) |
| **Interoperability** | Cisco to Cisco only | Any vendor to any vendor |

---

## How Each Protocol Works

### CDP Discovery Process

CDP runs continuously on all Cisco devices by default. Every 60 seconds, each interface
sends a CDP multicast frame listing all adjacent interfaces and their attributes. These
frames are encapsulated in IEEE 802.3 LLC+SNAP headers with a Cisco-reserved multicast
MAC (`01:00:0C:CC:CC:CC`).

A router receives a neighbor's CDP advertisement and caches the information for 180
seconds. If no refresh is received before the hold time expires, the neighbor entry is
deleted. The local router then learns:

- Device ID (hostname or serial number)
- Port identifier (interface name, e.g., "Gi0/0/1")
- Device platform (e.g., "Cisco IOS-XE")
- Software version
- Capabilities bitmap (Router, Switch, Host, Transparent Bridge, etc.)
- IP address(es) associated with the device

**Example:** A Catalyst 9300 switch discovers that a Cisco 4461 router is directly
connected on Ge1/0/1 and learns the router's hostname, model, IOS version, and
management IP, all from a single CDP message.

### LLDP Discovery Process

LLDP follows a similar pattern but uses IEEE 802.1AB standardised TLV encoding. Every
30 seconds (by default), each interface sends an LLDP multicast frame to the reserved
LLDP MAC (`01:80:C2:00:00:0E`). LLDP frames use EtherType `0x88CC` and contain no
additional encapsulation.

LLDP is designed for multi-vendor environments. Mandatory TLVs include:

- Chassis Identifier (system MAC or management IP)
- Port Identifier (interface name or MAC)
- Time To Live (TTL, usually 120 seconds)

Optional TLVs advertise:

- System Name (hostname)
- System Description (platform, version)
- System Capabilities (router, switch, repeater, etc.)
- Management Address (IPv4, IPv6, or IPX)
- Organisation-Specific TLVs (vendor extensions)

**Example:** A Fortinet FortiGate and a Cisco IOS-XE router, connected via a port,
exchange LLDP frames. The FortiGate learns the Cisco's hostname and management IP; the
Cisco learns the FortiGate's hostname and capabilities, regardless of vendor.

---

## Key Differences

### Frame Format and Encapsulation

**CDP** wraps its payload in IEEE 802.3 LLC/SNAP headers, making it vendor-specific at
the encapsulation level. Cisco routers and switches recognise the SNAP OUI `00:00:0C` and
CDP protocol ID `0x2000`.

**LLDP** uses a simple EtherType field (`0x88CC`) directly in the Ethernet frame. This
is standard on all modern switches and is directly recognisable without special LLC/SNAP
parsing.

### Transmission Interval and Convergence

**CDP:** 60-second default advertisement interval means discovery takes up to 60 seconds.
Hold time is 180 seconds (3× the TX interval). A failed neighbor might take 180 seconds
to be forgotten.

**LLDP:** 30-second default advertisement interval (half CDP's) and 120-second TTL (4×
the TX interval). Faster neighbour detection by default.

### Information Content

**CDP** provides richer Cisco-specific information:

- IOS version and image details
- IP address (explicit field in TLV)
- Capabilities bitmap optimised for Cisco devices
- VTP management domain

**LLDP** provides standardised multi-vendor information:

- System name and description
- Chassis ID (could be MAC, IP, or interface name)
- Port ID (interface name, MAC, or alias)
- Management address(es) for out-of-band access
- Power consumption (PoE), VLAN information via extensions

### Vendor Support and Interoperability

**CDP:** Works only between Cisco devices. Non-Cisco devices (Arista, Juniper, Fortinet,
etc.) do not support CDP and cannot learn from or respond to CDP advertisements.

**LLDP:** Supported by all major network vendors. A Cisco IOS-XE router can discover a
Fortinet FortiGate, Juniper vSRX, or Arista switch running LLDP. This is critical in
heterogeneous networks.

### Extensibility

**CDP:** Proprietary TLV extensions are defined by Cisco and understood only by Cisco
devices.

**LLDP:** Includes an organisational-specific TLV type (Type 127) for vendor extensions.
Cisco uses this to advertise proprietary information while remaining LLDP-compliant.

---

## Configuration and Operational Use Cases

### When to Use CDP

- **Cisco-only networks:** Networks with only Cisco devices can rely on CDP. It is
  enabled by default and requires no configuration.

- **Rapid troubleshooting in known environments:** CDP's rich information (IOS version,
  IP, capabilities) makes it ideal for Cisco technical staff who know they are dealing
  with Cisco equipment.

- **Legacy infrastructure:** Older networks built on CDP may not have the operational
  maturity to migrate to LLDP. Migration effort might not justify the benefit.

- **Cisco-specific integrations:** Some Cisco tools and workflows (e.g., older device
  discovery scripts, Cisco DNA Center) were built around CDP.

**Example:** A Cisco SE troubleshooting a Catalyst 9300 stack runs `show cdp neighbors
detail` to confirm that adjacent switches are running the correct IOS version without
logging into them.

### When to Use LLDP

- **Multi-vendor environments:** Any network with Fortinet FortiGate, Juniper, Arista,
  or other non-Cisco devices must use LLDP for universal neighbor discovery.

- **Greenfield deployments:** New networks should standardise on LLDP from the start.

- **Compliance and standards:** Some organisations require IEEE standards for discovery
  (e.g., 802.1AB compliance in data centre designs).

- **Telemetry and automation:** LLDP is more predictable across vendors, making
  automation scripts more portable.

- **Service provider environments:** ISPs and hosting providers with diverse vendor
  footprints standardise on LLDP.

**Example:** An organisation with Cisco and Fortinet hybrid architecture enables LLDP
on all devices. Border gateways (FortiGate) now report their uplink status and
management IP to internal Cisco routers and switches via standard LLDP TLVs.

---

## Cisco Examples

### Enable LLDP on Cisco IOS-XE

By default, Cisco devices run CDP. LLDP is disabled by default and must be explicitly
enabled.

```ios
! Enable LLDP globally
lldp run

! Configure LLDP on an interface
interface GigabitEthernet0/0/1
 lldp transmit
 lldp receive
```

### Disable CDP and Enable LLDP

To migrate from CDP to LLDP on a Cisco device:

```ios
! Disable CDP globally (and on all interfaces)
no cdp run

! Enable LLDP globally
lldp run

! Verify LLDP is active
show lldp neighbors
```

### Display Neighbor Information

```ios
! Show CDP neighbors (if still enabled)
show cdp neighbors
show cdp neighbors detail

! Show LLDP neighbors (if enabled)
show lldp neighbors
show lldp neighbors detail

! Typical output:
! Device ID        : R2.example.com
! Entry address(es):
!   IP address    : 192.0.2.2
! Platform        : Cisco 4461 Router
! Capabilities    : Router
! Software Version: Cisco IOS-XE Software, Version 17.6.1
! Hold time       : 180 seconds (CDP) or 120 seconds (LLDP)
```

---

## FortiGate Examples

Fortinet FortiGate appliances support LLDP but do not support CDP. LLDP is the only
option for neighbor discovery on FortiGate.

### Enable LLDP on FortiGate

```fortios
! Enable LLDP
config system lldp-settings
 set status enable
end

! Verify LLDP status
diagnose netlink lldp

! List neighbors discovered via LLDP
diag netlink lldp summary
```

### Display LLDP Neighbor Information

```fortios
! Show LLDP neighbors on all interfaces
diag netlink lldp summary

! Typical output:
! Interface: port1
!   Chassis ID: 00:11:22:33:44:55 (MAC)
!   Port ID: Gi0/0/1
!   Port Description: Uplink to R1 Core
!   System Name: R1.example.com
!   System Capability: Router
!   Management IP: 192.0.2.1
```

### Heterogeneous Discovery Scenario

In a hybrid Cisco + FortiGate architecture:

1. **Cisco side:** Enable both CDP (for Cisco-to-Cisco) and LLDP (for Cisco-to-FortiGate):

   ```ios
   lldp run
   cdp run  ! Keep for internal Cisco discovery
   ```

2. **FortiGate side:** Enable LLDP only:

   ```fortios
   config system lldp-settings
    set status enable
   end
   ```

3. **Result:** Both Cisco and FortiGate devices see each other via LLDP. Cisco routers
   also see each other via CDP for richer Cisco-specific detail.

---

## Practical Deployment Considerations

### Discovery Automation and Inventory

**CDP** enables quick, low-touch device inventory in Cisco shops. A network management
tool can walk a single core switch, learn all directly connected devices via `show cdp
neighbors`, and build a network diagram. This works for Cisco-only networks but fails
when a non-Cisco device is encountered.

**LLDP** enables multi-vendor inventory tools. Tools like:

- Cisco DNA Center (via LLDP integration)
- Arista CloudVision
- Open-source network monitoring (LibreNMS, Oxidized)

...can consume LLDP data from any vendor, making LLDP the standard for heterogeneous
environments.

### Troubleshooting and Verification

Both protocols are useful for verifying expected topology:

```ios
! Confirm that R2 is a peer (expected topology)
show cdp neighbors | include R2
show lldp neighbors | include R2

! If a neighbor is missing, suspect:
! 1. Link failure
! 2. Neighbor device powered off
! 3. Discovery protocol disabled on that interface
! 4. TTL/hold time expired (refresh expected in < 60 seconds for CDP, < 30 for LLDP)
```

### Security Implications

Both CDP and LLDP are **link-local only** — they are not forwarded by switches or
routers. However:

- **Information disclosure:** Advertising device model, software version, and
  capabilities reveals information useful to attackers. In some security policies,
  CDP/LLDP advertisements are disabled at untrusted ports (edge switches facing
  untrusted users).

- **Mitigation:** Disable on untrusted interfaces:

  ```ios
  interface Gi0/0/X
   no cdp enable
   no lldp transmit
   no lldp receive
  ```

---

## Notes

- Both CDP and LLDP require **direct Layer 2 connectivity** — they do not traverse
  routers or Layer 3 boundaries. If two devices are separated by a router, they will not
  discover each other via CDP or LLDP.

- LLDP frames are sometimes filtered by strict access control lists on management VLANs.
  Ensure the management IP address and LLDP multicast address (`01:80:C2:00:00:0E`) are
  allowed in ACLs if neighbour discovery is required.

- Cisco devices can run both CDP and LLDP simultaneously. CDP provides richer Cisco-to-
  Cisco discovery; LLDP bridges to non-Cisco devices.

- Some network management tools (e.g., Cisco Network Assistant) relied exclusively on
  CDP. Migrating to LLDP may require tool updates.

- **RFC references:** LLDP is defined in IEEE 802.1AB-2016. CDP has no formal RFC
  (Cisco proprietary) but its frame format is documented in Cisco technical literature.
