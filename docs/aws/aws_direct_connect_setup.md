# AWS Direct Connect — Connection Setup

AWS Direct Connect (DX) establishes a dedicated private network connection between an
on-premises network and AWS. Traffic bypasses the public internet entirely, providing
consistent latency, predictable throughput, and a path suitable for compliance workloads
that prohibit internet-traversing data transfer. This guide covers the connection from
physical circuit through to an established BGP session. BGP design and optimisation over
an established DX connection is covered in [BGP Stack (Flagship)](bgp_stack_vpn_over_dx.md).

---

## Architecture Overview

A Direct Connect connection places the customer router in the same co-location facility
as an AWS DX router. A cross-connect at the facility joins the two cages. From the AWS
side, the DX router connects to a Virtual Interface (VIF) — the logical construct that
carries BGP and data plane traffic into the AWS network.

```text
Customer router
      |
      | Cross-connect (co-location facility)
      |
AWS DX router
      |
      | Virtual Interface (Private VIF / Transit VIF / Public VIF)
      |
VGW (Virtual Private Gateway)   or   DX Gateway → TGW
      |
VPC(s)
```

Two connection models exist:

| Model | Speed | How |
| --- | --- | --- |
| Dedicated | 1 / 10 / 100 Gbps | Direct physical port on AWS DX hardware; ordered through AWS Console |
| Hosted | 50 Mbps – 10 Gbps (sub-1G or shared) | Ordered through an APN (AWS Partner Network) partner who owns the port; capacity is allocated from the partner's connection |

Dedicated connections are owned end-to-end by the customer. Hosted connections are
appropriate when the required bandwidth is below 1 Gbps or when the customer is not
co-located with an AWS DX facility and needs a partner to provide transport.

---

## Step 1 — Order the Connection

In the AWS Management Console, navigate to **Direct Connect → Connections → Create
connection**. Provide:

- **Connection name**: descriptive; include site identifier and purpose
- **Location**: the DX facility where the cross-connect will be installed
- **Port speed**: 1G, 10G, or 100G for Dedicated; or the hosted capacity tier
- **Provider**: for Hosted connections, select the APN partner

AWS processes the request and generates a **Letter of Authorization – Connecting
Facility Assignment (LOA-CFA)**. This document is the cross-connect authorisation:
it identifies the AWS cage, patch panel, and port. Download it from the Console once
the connection reaches "Requested" state.

For Hosted connections, provide the LOA-CFA or the equivalent service key to the APN
partner rather than to the facility directly — the partner manages the physical
provisioning on their infrastructure.

---

## Step 2 — Physical Cross-Connect

Submit the LOA-CFA to the co-location facility's remote hands or ticketing system.
The facility installs a cross-connect between the customer's cage (or MMR) and the
AWS cage at the patch panel port specified in the LOA-CFA.

Typical timeline: **3–15 business days**. Some facilities offer expedited cross-connect
installation for an additional fee. The AWS Console connection status remains
"Requested"
until the facility completes the cross-connect and AWS detects a physical signal.

Once the cross-connect is installed and a physical signal is present on both ends, the
connection state in the Console changes to **"Available"**.

---

## Step 3 — Verify Physical Layer

Before configuring the VIF and BGP, confirm the physical layer is healthy.

**AWS Console checks:**

- Connection state: **Available**
- Connection speed and location match what was ordered

**Customer router (Cisco IOS-XE):**

```text

show interfaces GigabitEthernet0/0
show interfaces GigabitEthernet0/0 transceiver
```

Confirm: interface is up/up, optical Rx power is within the transceiver's acceptable
range. A connection in "Available" state with a down interface on the customer side
indicates a cabling, fibre, or SFP issue — not an AWS problem.

**Customer router (FortiGate):**

```bash

get system interface
diagnose hardware deviceinfo nic <port-name>
```

---

## Step 4 — Create a Virtual Interface (VIF)

A VIF is the logical layer on top of the DX connection. It carries 802.1Q tagged
Ethernet frames on a specified VLAN ID. The BGP session for on-premises-to-VPC
connectivity runs inside the VIF.

Three VIF types:

| VIF type | Connects to | Use case |
| --- | --- | --- |
| Private VIF | Virtual Private Gateway (VGW) attached to a single VPC | Single-VPC access; simpler setup |
| Transit VIF | DX Gateway, which associates with one or more Transit Gateways | Multi-VPC and multi-region access; recommended for enterprise |
| Public VIF | AWS public services (S3, SQS, DynamoDB, etc.) | Accessing AWS public endpoints over DX without using the internet; requires a public ASN |

For most enterprise deployments, the Transit VIF is the correct choice. It allows a
single DX connection to reach VPCs across multiple regions through TGW associations on
the DX Gateway.

**VIF configuration parameters:**

| Parameter | Notes |
| --- | --- |
| VLAN ID | 802.1Q tag used on the customer router subinterface; must be unique per VIF on the connection |
| Customer ASN | The BGP ASN of the on-premises router (private ASN 64512–65534 is standard) |
| Amazon-side ASN | AWS DX ASN is 7224; configurable on the VGW if using a custom ASN |
| BGP auth key | MD5 password for the BGP session; optional but recommended |
| IP addressing | AWS provides a /30 pair, or specify APIPA (169.254.x.x/30) to avoid consuming routable space |

---

## Step 5 — Configure BGP on the Customer Router

AWS requires BGP for all VIF types. There is no static routing option for Direct
Connect.

The following examples use APIPA addressing, which avoids allocating routable /30
subnets for VIF peerings. The BGP neighbour address is the AWS-assigned APIPA address
from the VIF configuration screen.

**Cisco IOS-XE — Private or Transit VIF:**

```text

! Create the subinterface for the VIF VLAN
interface GigabitEthernet0/0.100
 encapsulation dot1Q 100
 ip address 169.254.100.2 255.255.255.252
!
! BGP session toward AWS
router bgp 65001
 neighbor 169.254.100.1 remote-as 7224
 neighbor 169.254.100.1 password <BGP-AUTH-KEY>
 neighbor 169.254.100.1 description AWS-DX-PRIVATE-VIF
 !
 address-family ipv4
  neighbor 169.254.100.1 activate
  neighbor 169.254.100.1 soft-reconfiguration inbound
  ! Advertise on-premises prefixes — do not advertise a default route
  network 10.0.0.0 mask 255.255.0.0
 exit-address-family
```

**FortiGate:**

```bash

config system interface
 edit "dx-vif100"
  set vdom "root"
  set ip 169.254.100.2 255.255.255.252
  set allowaccess ping
  set type vlan
  set interface "<physical-port>"
  set vlanid 100
 next
end

config router bgp
 set as 65001
 config neighbor
  edit "169.254.100.1"
   set remote-as 7224
   set password <BGP-AUTH-KEY>
   set description "AWS-DX-PRIVATE-VIF"
  next
 end
 config network
  edit 1
   set prefix 10.0.0.0 255.255.0.0
  next
 end
end
```

Once the BGP session establishes, the customer router will receive VPC CIDR prefixes
from AWS and AWS will begin advertising the on-premises prefixes into the VPC route
tables.

---

## Step 6 — DX Gateway and Transit VIF

For multi-VPC or multi-region access, use a DX Gateway:

1. **Create the DX Gateway**: Direct Connect → Direct Connect Gateways → Create.

   Assign an Amazon-side ASN (64512–65534 recommended; must differ from the TGW ASN).

2. **Associate the DX Gateway with a TGW**: in the TGW console, create an association

   between the TGW and the DX Gateway. Specify which VPC CIDRs the TGW should advertise
   to the DX Gateway.

3. **Create a Transit VIF** pointing at the DX Gateway rather than a VGW.
4. Configure the customer router as above — the BGP session is the same structure; only

   the remote-as and the prefixes advertised by AWS differ.

A single DX Gateway can be associated with TGWs in multiple AWS regions, allowing one
physical DX connection to reach VPCs across regions. Up to 20 TGW-to-DX-Gateway
associations are supported per DX Gateway.

---

## Redundancy

AWS recommends two DX connections from different DX locations (not just different cages
within the same facility) for protection against location-level failure. The two
connections should each have their own VIF and BGP session; BGP path selection
differentiates primary from secondary using AS-path prepending or Local Preference.

A site-to-site VPN over the internet provides a cold standby path. Make the VPN less
preferred by prepending the on-premises ASN on BGP advertisements received over the VPN,
or by applying a lower Local Preference on the customer router for VPN-learned routes.

See [BGP Stack (Flagship)](bgp_stack_vpn_over_dx.md) for the BGP configuration for
primary/backup path design.

---

## Key BGP Behaviours

- AWS advertises the VPC CIDR attached to the VGW (Private VIF) or all TGW-attached
  VPC CIDRs (Transit VIF)

- The default prefix limit is 100 routes per BGP session on a Private VIF and 200 on a
  Transit VIF. Exceeding the limit causes the BGP session to be reset

- AWS will not accept a default route (0.0.0.0/0) advertised by the customer over a
  Private or Transit VIF

- APIPA addressing (169.254.x.x) on the VIF is expected and supported — do not filter
  this range on the customer router

---

## Verification

| Check | AWS Console | Customer router (Cisco IOS-XE) | Customer router (FortiGate) |
| --- | --- | --- | --- |
| Physical connection state | Connection status: Available | `show interfaces Gi0/0` — line up, protocol up | `get system interface` |
| BGP session state | VIF status: Available; BGP status: Up | `show bgp neighbors 169.254.100.1` | `get router info bgp summary` |
| Prefixes received from AWS | Not visible in Console | `show bgp ipv4 unicast neighbors 169.254.100.1 received-routes` | `get router info bgp neighbors 169.254.100.1 received-routes` |
| Prefixes advertised to AWS | Not visible in Console | `show bgp ipv4 unicast neighbors 169.254.100.1 advertised-routes` | `get router info bgp neighbors 169.254.100.1 advertised-routes` |
| VPC route table | VPC → Route Tables → check for on-premises prefixes with target VGW &#124; TGW | — | — |
