# Naming Standards

Consistent naming across physical devices, interfaces, and logical resources ensures clarity,
enables automation, and allows easy identification of equipment type, location, and purpose.

---

## Physical Device Naming

Device names follow a hierarchical structure for on-premises equipment:

**Format: `SSSS-RRR[FF]-NN[M]`**

| Component | Length | Required | Example | Purpose |
| --- | --- | --- | --- | --- |
| Site (SSSS) | 4 chars | Yes | LON1, ELD7 | Location identifier |
| Role (RRR) | 3 chars | Yes | CSW, ASW, PFW | Device role (not vendor) |
| Floor (FF) | 2 chars | No | 01-99, 0G, B1 | Physical floor/level |
| Device (NN) | 2 chars | Yes | 01-99 | Sequential number |
| Member (M) | 1 char | No | A, B, C | Stack/cluster member |

### Site Identifiers

**Data Centers:**

| Identifier | Location |
| --- | --- |
| EDB3 | Dublin |
| EDC4 | Ashburn |
| ELD7 | Slough |
| ELD8 | Docklands |
| ESG3 | Singapore |

**Offices** (IATA airport codes):

| Identifier | Location | Status | Identifier | Location | Status |
| --- | --- | --- | --- | --- | --- |
| LON | London | Active | MRU | Mauritius | Active |
| NYC | New York | Active | SFO | San Francisco | Active |
| PAR | Paris | Active | DXB | Dubai | Active |
| TLL | Tallinn | Active | SNG | Singapore | Active |
| HKG | Hong Kong | Active | SHG | Shanghai | Active |
| MEL | Melbourne | Active | BER | Berlin | Closed |
| OPO | Porto | Closed | PER | Perth | Closed |

### Role Identifiers

| Identifier | Role |
| --- | --- |
| ASW | Access Switch |
| CSW | Core Switch |
| ISW | Internet Switch |
| WSW | Wireless Switch |
| PFW | Physical Firewall |
| VFW | Virtual Firewall |
| SRV | Server |
| WAP | Wireless Access Point |
| CON | Console Server |

### Floor Identifiers

| Identifier | Floor |
| --- | --- |
| 01-99 | Floors 1-99 |
| 0G | Ground floor |
| B1-B9 | Basements 1-9 |
| MZ | Mezzanine |

### Device/Member Identifiers

| Identifier | Meaning |
| --- | --- |
| 01-99 | Sequential device number |
| A | Primary/first member of stack/cluster |
| B | Secondary/second member |
| C-Z | Additional stack members |

### Physical Device Examples

**Data Center Core Switch:**

- `ELD7-CSW-01` — Slough datacenter, core switch, device 01

**Office Access Switch Stack:**

- `LON1-ASW04-01A` — London office, access switch, floor 4, device 01, primary
- `LON1-ASW04-01B` — London office, access switch, floor 4, device 01, secondary

**Office Firewall Pair:**

- `LON1-PFW-01A` — London office, physical firewall, device 01, active
- `LON1-PFW-01B` — London office, physical firewall, device 01, standby

**Wireless Access Point:**

- `LON1-WAP04-16` — London office, WAP on floor 4, device 16

**Console Server:**

- `ELD7-CON-01` — Slough datacenter, console server, device 01

---

## Interface and Logical Resource Naming

### Physical Interface Descriptions

Configure interface descriptions with this format: `[Attached-Device]_[Attached-Interface]`

**Case convention:** Match the case of the attached device's interface naming:

- Cisco: Uppercase `Gi0/0`, `Gi0/1` (abbreviated GigabitEthernet)
- FortiGate: Lowercase `port1`, `port2` (per FortiGate standard)

**Cisco to Cisco:**

| Interface | Description | Connected Device | Purpose |
| --- | --- | --- | --- |
| `Gi0/1` | `AWSTGW_Gi0/1` | AWS TGW | AWS Direct Connect handoff |
| `Gi0/2` | `AZUREMSEE_Gi0/1` | Azure MSEE | Azure ExpressRoute handoff |
| `Gi0/3` | `GCPIC_Gi0/1` | GCP Cloud Router | GCP Cloud Interconnect handoff |
| `Gi1/0` | `LON1-PFW-01A_Gi0/0` | LON1-PFW-01A | Local firewall link (primary) |
| `Gi1/1` | `LON1-PFW-01B_Gi0/0` | LON1-PFW-01B | Local firewall link (secondary) |

**Cisco to FortiGate:**

| Interface | Description | Connected Device | Purpose |
| --- | --- | --- | --- |
| `Gi0/4` | `ELD7-PFW-01A_port1` | ELD7-PFW-01A | Datacenter FW primary uplink |
| `Gi0/5` | `ELD7-PFW-01B_port1` | ELD7-PFW-01B | Datacenter FW secondary uplink |

### VLAN Subinterfaces

Format: `[physical].[vlan]` with description: `[Attached-Device]_[Attached-Interface]`

Match the case of the attached device's interface naming: Cisco uses uppercase Gi, FortiGate uses
lowercase port.

| Subinterface | VLAN | Description | VRF | Purpose |
| --- | --- | --- | --- | --- |
| `Gi0/1.100` | 100 | `LON1-PFW-01A_port1` | AWS | Firewall AWS transport |
| `Gi0/1.200` | 200 | `LON1-PFW-01A_port2` | Azure | Firewall Azure transport |
| `Gi0/1.300` | 300 | `LON1-PFW-01A_port3` | GCP | Firewall GCP transport |

### VRF Naming

Standard VRF names by purpose:

| VRF | Purpose |
| --- | --- |
| `Mgmt-vrf` | Management plane (Cisco IOS-XE built-in) |
| `AWS` | Amazon Web Services |
| `Azure` | Microsoft Azure |
| `GCP` | Google Cloud Platform |

### Route Map Naming

Format: `RM_[source]_[direction]`

| Route Map | Direction | Purpose |
| --- | --- | --- |
| `RM_AWS_IN` | Inbound | AWS route filtering/manipulation |
| `RM_AWS_OUT` | Outbound | AWS route filtering/manipulation |
| `RM_AZURE_IN` | Inbound | Azure route filtering/manipulation |
| `RM_AZURE_OUT` | Outbound | Azure route filtering/manipulation |
| `RM_GCP_IN` | Inbound | GCP route filtering/manipulation |
| `RM_GCP_OUT` | Outbound | GCP route filtering/manipulation |

### Prefix List Naming

Format: `PL_[vrf]_[purpose]`

| Prefix List | Purpose |
| --- | --- |
| `PL_AWS_TRANSPORT` | AWS transport link addressing (handoff subnet) |
| `PL_AWS_INTERNAL` | AWS internal routes to advertise to TGW |
| `PL_AZURE_TRANSPORT` | Azure ExpressRoute handoff subnet |
| `PL_AZURE_INTERNAL` | Azure internal routes to advertise |
| `PL_GCP_TRANSPORT` | GCP Cloud Interconnect handoff subnet |
| `PL_GCP_INTERNAL` | GCP internal routes to advertise |
| `PL_BOGON` | Bogon/invalid IP ranges (ingress filtering) |

### BGP Neighbor Descriptions

Format: `[peer-type]-[purpose]-[AS]-[region]` or `[peer-type]-[REGION]-[purpose]-[AS]`

| Description | Peer Type | Purpose |
| --- | --- | --- |
| `AWS-TGW-DX-64512-us` | Cloud | AWS TGW via Direct Connect, AS 64512 |
| `AZURE-MSEE-12076-primary` | Cloud | Azure ExpressRoute MSEE primary, AS 12076 |
| `GCP-CloudRouter-64514-primary` | Cloud | GCP Cloud Interconnect, AS 64514 |
| `FG-LON-AWS-65001` | Internal | FortiGate London WAN peer for AWS, AS 65001 |
| `CORE-EU-iBGP-65000` | Internal | EU core iBGP peer, AS 65000 |

### Access Control List Naming

Format: `ACL_[REASON]_IN` or `ACL_[REASON]_OUT`

| ACL | Direction | Purpose |
| --- | --- | --- |
| `ACL_BOGON_IN` | Inbound | Blocks RFC1918, loopback, multicast, documentation ranges |
| `ACL_MGMT_IN` | Inbound | Restricts management access to approved subnets |
| `ACL_SNMP_IN` | Inbound | Restricts SNMP queries to NMS hosts |
| `ACL_DEFAULT_OUT` | Outbound | Default outbound filtering rules |
