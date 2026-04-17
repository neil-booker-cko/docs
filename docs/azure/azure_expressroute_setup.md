# Azure ExpressRoute — Circuit Setup

Azure ExpressRoute establishes a private connection between an on-premises network and
Azure through a connectivity provider or a direct physical port at an ExpressRoute
Direct
location. Traffic does not traverse the public internet. This guide covers the circuit
from creation through to an established BGP session with the Microsoft Enterprise Edge.
BGP design over an established circuit is in [BGP Stack (Flagship)](bgp_stack_vpn_over_expressroute.md).

---

## Architecture Overview

An ExpressRoute circuit always terminates on a pair of Microsoft Enterprise Edge (MSEE)
routers. The MSEE pair is a design constant — Microsoft operates two physical paths into
every ExpressRoute location. To achieve full redundancy, the customer must connect to
both MSEEs. A circuit with only one path active is treated as degraded by Azure.

```text
Customer network
      |
      | (provider circuit or direct cross-connect)
      |
Connectivity provider PoP   OR   ExpressRoute Direct location
      |
MSEE-1 (primary)    MSEE-2 (secondary)
      |                    |
      +--------------------+
             |
      ExpressRoute circuit
             |
   ExpressRoute Gateway (in VNet)
             |
          VNet(s)
```

The customer is responsible for establishing BGP sessions to both MSEE paths. Azure
manages the MSEE infrastructure; the customer manages everything from their network edge
to the MSEE.

---

## Connection Models

| Model | Description | Typical use case |
| --- | --- | --- |
| Co-located at Exchange | Customer equipment is at the same facility as the provider's network exchange; direct Layer 2 connection to provider edge | Fastest setup; best for customers already in major carrier-neutral data centres |
| Point-to-point Ethernet | Dedicated Ethernet circuit from customer site to provider PoP | Customer not in the same facility; standard enterprise WAN circuit |
| Any-to-any (IPVPN&#124;MPLS) | Provider integrates ExpressRoute into the customer's existing MPLS WAN; branch sites gain access without separate circuits | Customers with large MPLS WAN deployments wanting uniform Azure access from branches |
| ExpressRoute Direct | 10 or 100 Gbps direct physical connection from customer router to Microsoft; no provider intermediary | Very high bandwidth requirements; strict compliance requiring no third-party in path |

ExpressRoute Direct bypasses all connectivity providers. The customer provisions and
manages the physical cross-connect to Microsoft's facility directly. This model is
appropriate for organisations requiring dedicated port capacity at the highest bandwidth
tiers or where provider involvement is prohibited by policy.

---

## Peering Types

| Peering type | Reaches | Status |
| --- | --- | --- |
| Private Peering | Azure VNets — VMs, internal load balancers, AKS nodes | Current standard; most commonly used |
| Microsoft Peering | Microsoft 365, Azure Storage, Azure SQL, and other public Azure services | Current standard for public service access |
| ~~Public Peering~~ | ~~Azure public services~~ | Deprecated; replaced by Microsoft Peering |

Most organisations require Private Peering. Microsoft Peering is needed only when
accessing Microsoft 365 or Azure public services over ExpressRoute rather than the
internet. Microsoft Peering requires a public ASN and the configuration of route filters
to control which services are reachable — without route filters, no prefixes are
advertised.

---

## Step 1 — Create the Circuit

In the Azure Portal, navigate to **ExpressRoute → Create**.

| Parameter | Notes |
| --- | --- |
| Provider | Select the connectivity provider from the list, or "Not applicable" for ExpressRoute Direct |
| Peering location | The physical ExpressRoute location (city&#124;facility) where the circuit will terminate |
| Bandwidth | 50 Mbps to 10 Gbps; billed at the circuit level regardless of usage |
| SKU | Local (single region, no global routing), Standard (all regions in the same geopolitical boundary), Premium (global routing, M365) |

Once created, Azure assigns a **Service Key** — a UUID that uniquely identifies the
circuit. Hand this to the connectivity provider; it is their provisioning reference.
The circuit status in the Portal shows **"Not Provisioned"** until the provider
completes their side.

---

## Step 2 — Provider Provisioning

The provider uses the Service Key to provision the circuit on their infrastructure.
This involves configuring the VLAN, 802.1Q tagging, and routing toward the MSEE pair
at the chosen peering location.

The circuit status transitions from "Not Provisioned" to **"Provisioned"** once the
provider confirms readiness. **Timeline varies by provider: days to weeks.** Azure
does not control this phase — escalate delays directly with the provider.

Do not configure BGP on the customer router until the circuit shows "Provisioned".
Attempting to establish BGP before provider provisioning is complete will result in
a session that cannot establish regardless of customer-side configuration.

---

## Step 3 — Configure Private Peering

Private Peering is configured in the Azure Portal (ExpressRoute circuit → Peerings →
Azure Private) or via Azure CLI.

Required parameters:

| Parameter | Notes |
| --- | --- |
| Primary subnet | /30 for the BGP session on the primary MSEE path; Azure uses the first usable IP, customer uses the second |
| Secondary subnet | /30 for the BGP session on the secondary MSEE path; same convention |
| VLAN ID | 802.1Q tag for the primary path; the secondary path uses VLAN ID + 1 by convention (provider-dependent) |
| Customer ASN | On-premises BGP ASN |
| MD5 auth hash | Optional; recommended for session security |

Azure always uses ASN **12076** on the MSEE side. The customer router will peer to
12076 on both primary and secondary paths.

These subnets must not overlap with on-premises address space or VNet address space.
Use dedicated /30 ranges from a transit addressing block (e.g., 192.0.2.x/30 pairs
from a reserved block, or from private space not in use elsewhere).

---

## Step 4 — Configure the Customer Router

Two BGP sessions are required: one to the primary MSEE and one to the secondary MSEE.
These should be on separate physical or logical interfaces with separate VLAN IDs to
ensure path independence.

**Cisco IOS-XE:**

```text

! Primary path — VLAN 100
interface GigabitEthernet0/0.100
 encapsulation dot1Q 100
 ip address <primary-customer-ip> 255.255.255.252

router bgp 65001
 neighbor <primary-msee-ip> remote-as 12076
 neighbor <primary-msee-ip> password <auth-key>
 neighbor <primary-msee-ip> description Azure-ER-Primary-MSEE
 !
 address-family ipv4
  neighbor <primary-msee-ip> activate
  neighbor <primary-msee-ip> soft-reconfiguration inbound
  network 10.0.0.0 mask 255.255.0.0
 exit-address-family

! Secondary path — VLAN 101 (on secondary router or secondary interface)
interface GigabitEthernet0/1.101
 encapsulation dot1Q 101
 ip address <secondary-customer-ip> 255.255.255.252

router bgp 65001
 neighbor <secondary-msee-ip> remote-as 12076
 neighbor <secondary-msee-ip> password <auth-key>
 neighbor <secondary-msee-ip> description Azure-ER-Secondary-MSEE
 !
 address-family ipv4
  neighbor <secondary-msee-ip> activate
  neighbor <secondary-msee-ip> soft-reconfiguration inbound
  network 10.0.0.0 mask 255.255.0.0
 exit-address-family
```

**FortiGate:**

```bash

config system interface
 edit "er-primary"
  set vdom "root"
  set ip <primary-customer-ip> 255.255.255.252
  set type vlan
  set interface "<physical-port>"
  set vlanid 100
 next
 edit "er-secondary"
  set vdom "root"
  set ip <secondary-customer-ip> 255.255.255.252
  set type vlan
  set interface "<physical-port>"
  set vlanid 101
 next
end

config router bgp
 set as 65001
 config neighbor
  edit "<primary-msee-ip>"
   set remote-as 12076
   set password <auth-key>
   set description "Azure-ER-Primary-MSEE"
  next
  edit "<secondary-msee-ip>"
   set remote-as 12076
   set password <auth-key>
   set description "Azure-ER-Secondary-MSEE"
  next
 end
 config network
  edit 1
   set prefix 10.0.0.0 255.255.0.0
  next
 end
end
```

Both BGP sessions must reach the Established state. Azure monitors both paths; if only
one is established, the circuit is reported as degraded in the Portal even if traffic
is flowing on the active path.

---

## Step 5 — Link to a VNet Gateway

The ExpressRoute circuit does not connect to a VNet automatically. A dedicated
**ExpressRoute Gateway** must be deployed in each VNet that requires access.

1. In the target VNet, create a Gateway Subnet (a dedicated /27 or /28 named

   "GatewaySubnet" exactly — Azure requires this name)

2. Deploy an ExpressRoute Gateway resource in the GatewaySubnet. Choose the SKU

   (Standard, HighPerformance, UltraPerformance, ErGw1Az/2Az/3Az) based on
   required throughput and availability zone support

3. Create a Connection resource linking the Gateway to the ExpressRoute circuit

Multiple VNets can connect to a single ExpressRoute circuit through separate Gateway
Connection resources. The number of VNet Gateways per circuit depends on the circuit
SKU:

| Circuit SKU | VNet Gateways |
| --- | --- |
| Local | Up to 10 VNets in the local region |
| Standard | Up to 10 VNets |
| Premium | Up to 100 VNets |

---

## ExpressRoute Global Reach

ExpressRoute Global Reach connects two on-premises sites through Microsoft's backbone
using their respective ExpressRoute circuits. Traffic between Site A and Site B flows:
Site A → MSEE → Microsoft backbone → MSEE → Site B — without traversing the internet
or an Azure VNet.

This is useful for branch-to-branch or site-to-site connectivity where both sites
already have ExpressRoute circuits and the organisation wants to avoid building a
separate private WAN link between them. Global Reach requires the Premium SKU on both
circuits.

---

## Redundancy

Both MSEE paths (primary and secondary) must be connected and their BGP sessions must
be established for full circuit redundancy. Azure treats a circuit with one active path
as degraded. If the single active path then fails, there is no backup — the circuit is
down.

**BFD (Bidirectional Forwarding Detection)** is supported by Azure on ExpressRoute
Private Peering. Enable BFD on the customer router for fast failure detection — BFD
can detect path failure in milliseconds rather than waiting for BGP hold timer expiry
(default 90 seconds). This significantly reduces failover time when one MSEE path fails
and traffic must shift to the other.

For diverse provider redundancy, provision two circuits from different connectivity
providers, each terminating at a different peering location. This protects against a
provider's infrastructure failure, not just a port or link failure.

See [BGP Stack (Flagship)](bgp_stack_vpn_over_expressroute.md) for BGP configuration
for path preference and failover design.

---

## Verification

| Check | Azure Portal | Customer router (Cisco IOS-XE) | Customer router (FortiGate) |
| --- | --- | --- | --- |
| Circuit provisioning state | ExpressRoute → circuit → Overview: Provider status = Provisioned | — | — |
| BGP session state | Peerings → Azure Private: Status = Enabled | `show bgp neighbors <msee-ip>` — state: Established | `get router info bgp summary` |
| Prefixes received from Azure | Not shown in Portal | `show bgp ipv4 unicast neighbors <msee-ip> received-routes` | `get router info bgp neighbors <msee-ip> received-routes` |
| Prefixes advertised to Azure | Not shown in Portal | `show bgp ipv4 unicast neighbors <msee-ip> advertised-routes` | `get router info bgp neighbors <msee-ip> advertised-routes` |
| VNet routing | VNet → Subnets → effective routes: on-premises prefixes visible via ExpressRoute Gateway | — | — |
