# Naming Conventions

Standards for device, interface, and logical resource naming.

---

## Device Naming

### Cisco Routers

Format: `ck-[region]-[type]-[instance]`

| Example | Meaning |
| --- | --- |
| `ck-us-core-01` | Checkout US core router, instance 01 |
| `ck-eu-edge-02` | Checkout EU edge router, instance 02 |

### FortiGate Firewalls

Format: `ck-[region]-fw-[instance]`

| Example | Meaning |
| --- | --- |
| `ck-us-fw-01` | Checkout US firewall, instance 01 |

---

## Interface Naming

### Physical Interfaces (Cisco)

Use Cisco default: `GigabitEthernet0/0`, `GigabitEthernet0/1`, etc.

Description format: `[peer-type]–[purpose]–[destination]`

| Interface | Description | Purpose |
| --- | --- | --- |
| `Gi0/1` | `DX–AWS–TGW-64512` | AWS Direct Connect to TGW |
| `Gi0/2` | `ER–Azure–MSEE-12076` | Azure ExpressRoute to MSEE |
| `Gi0/3` | `IC–GCP–CloudRouter` | GCP Cloud Interconnect |

### VLAN Subinterfaces

Format: `[physical].[vlan]` with description `[VRF]–[purpose]`

| Interface | VLAN | Description | Purpose |
| --- | --- | --- | --- |
| `Gi0/1.100` | 100 | `AWS–transport–FG` | FortiGate AWS transport |
| `Gi0/1.200` | 200 | `AZURE–transport–FG` | FortiGate Azure transport |
| `Gi0/1.300` | 300 | `GCP–transport–FG` | FortiGate GCP transport |

---

## VRF Naming

**Standard:** Uppercase, cloud provider name or purpose

| VRF | Purpose |
| --- | --- |
| `AWS` | Amazon Web Services |
| `AZURE` | Microsoft Azure |
| `GCP` | Google Cloud Platform |
| `Mgmt` | Management plane (IOS-XE built-in) |

---

## Route Map and Prefix List Naming

**Route Maps:** `RM-[source]-[direction]`

- `RM-AWS-IN` — AWS inbound filtering
- `RM-FG-AWS-OUT` — FortiGate AWS outbound

**Prefix Lists:** `PFX-[vrf]-[purpose]`

- `PFX-AWS-TRANSPORT` — AWS transport link addressing
- `PFX-GCP-INTERNAL` — GCP internal routes

---

## BGP Neighbor Descriptions

Format: `[peer-type]–[purpose]–[AS]–[region]`

| Description | Purpose |
| --- | --- |
| `AWS-TGW-DX-64512-us` | AWS TGW via Direct Connect, AS 64512 |
| `FG-WAN-AWS-65001` | FortiGate WAN peer for AWS, AS 65001 |
| `ER-MSEE-PRIMARY-12076` | Azure MSEE primary, AS 12076 |
