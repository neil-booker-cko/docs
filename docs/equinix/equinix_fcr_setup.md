# Equinix FCR Setup and Provisioning Guide

Complete reference for provisioning Fabric Cloud Router, creating virtual connections, and
configuring BGP.

## Quick Start: Basic FCR Provisioning

### 1. Create FCR Instance (Equinix Console)

```text
Equinix Console → Fabric → Fabric Cloud Router
  Name: my-fcr-primary
  Metro: SJC (San Jose)
  ASN: 65001 (private ASN)
  BGP Timers: hello 3s, holdtime 9s

Create
```text

Result: FCR instance ready to receive vConnections.

### 2. Create vConnection (DC-to-FCR)

```text
Equinix Console → Fabric → Virtual Connections
  Type: DC (Datacenter) to Fabric Cloud Router
  Source: Your DC (via cross-connect)
  Destination: my-fcr-primary (SJC)
  Bandwidth: 10Gbps

Create
```text

Result: vConnection pending. Equinix provides cross-connect details.

### 3. Establish BGP Session (Your Router)

```text
Your Cisco router:
  router bgp 65000
    neighbor 10.255.0.1 remote-as 65001
    neighbor 10.255.0.1 timers 3 9
```text

Result: BGP peering with FCR (status: Established).

### 4. Advertise Routes

```text
Your Cisco router:
  network 10.0.0.0 mask 255.0.0.0  ! Local DC subnets

BGP announces: 10.0.0.0/8 → FCR → Cloud provider
```text

---

## Detailed Provisioning Steps

## Step 1: Create FCR Instance

### 1.1 Access Equinix Console

```text
1. Log in to Equinix console
2. Navigate to Fabric → Fabric Cloud Router
3. Click "Create"
```text

### 1.2 Configure FCR Parameters

```yaml
Name: my-fcr-primary
Description: Primary FCR for cloud interconnect

Location (Metro):
  Primary: SJC (San Jose)  # Choose primary metro

Routing (BGP):
  ASN Type: Private  # Use private ASN (65000–65534)
  ASN: 65001

BGP Timers:
  Hello Interval: 3 seconds
  Hold Time: 9 seconds

Notifications: Enable (email on vConnection status changes)
```text

### 1.3 Review and Create

```text
Summary:
  ✓ FCR Name: my-fcr-primary
  ✓ Metro: SJC
  ✓ ASN: 65001
  ✓ BGP Timers: 3s/9s

[Create FCR]
```text

**Status:** FCR created. Equinix assigns:
- FCR ID: fcr-xxxxx
- BGP peering IP: 10.255.0.1 (primary), 10.255.0.2 (secondary/redundancy)
- Route reflector IP (if applicable)

---

## Step 2: Create Virtual Connections (vConnections)

### 2.1 DC-to-FCR vConnection

#### Prerequisites

- FCR instance created (from Step 1)
- Your datacenter's cross-connect point in same Equinix metro
- Bandwidth reserved (1Gbps, 10Gbps, or 100Gbps)

#### Provisioning Steps

```text
Equinix Console → Fabric → Virtual Connections → New

Type: DC (Datacenter)

Source Configuration:
  Datacenter Location: [Your DC's Equinix metro]
  Port or Cross-Connect: [Select your cross-connect]
  VLAN: [Equinix-assigned or custom]

Destination Configuration:
  Type: Fabric Cloud Router
  FCR: my-fcr-primary (SJC)

Connection Details:
  Bandwidth: 10Gbps
  Redundancy: None (or add 2nd vConnection for redundancy)

Notifications: Enable

[Create vConnection]
```text

**Status:** vConnection created. Equinix provides:
- vConnection ID: vc-xxxxx
- BGP peer IP (your side): 10.255.1.1/30
- BGP peer IP (FCR side): 10.255.1.2/30
- Cross-connect order details (if needed)

#### 2.2 Verify vConnection Status

```text
Equinix Console → Fabric → Virtual Connections
Status progression:
  PENDING_APPROVAL → WAITING_FOR_CUSTOMER → ACTIVE

Once ACTIVE:
  ✓ Layer 2 link is up
  ✓ Ready for BGP peering
```text

### 2.3 Cloud Provider vConnection (Optional)

#### Create AWS Direct Connect via FCR

```text
Equinix Console → Fabric → Virtual Connections → New

Type: Fabric Cloud Router to Cloud Provider

Source Configuration:
  Type: Fabric Cloud Router
  FCR: my-fcr-primary

Destination Configuration:
  Cloud Provider: AWS
  Region: us-east-1
  Account ID: 123456789012

BGP Configuration:
  BGP ASN: 16509 (AWS)
  Customer Gateway ASN: 65001 (your FCR ASN)

[Create vConnection]
```text

**Status:** AWS vConnection created. AWS receives BGP prefixes advertised by FCR.

---

## Step 3: Configure BGP on Your Router

### 3.1 BGP Configuration Template (Cisco IOS-XE)

```ios
configure terminal

! Define BGP process
router bgp 65000
  bgp router-id 10.0.0.1  ! Your router's ID

  ! Peer with FCR (via DC-to-FCR vConnection)
  neighbor 10.255.1.2 remote-as 65001
  neighbor 10.255.1.2 description "Equinix FCR Primary"
  neighbor 10.255.1.2 timers 3 9 0

  ! Optional: Secondary FCR for redundancy
  neighbor 10.255.1.6 remote-as 65001
  neighbor 10.255.1.6 description "Equinix FCR Secondary"
  neighbor 10.255.1.6 timers 3 9 0

  ! Address family
  address-family ipv4
    neighbor 10.255.1.2 activate
    neighbor 10.255.1.2 soft-reconfiguration inbound
    neighbor 10.255.1.6 activate
    neighbor 10.255.1.6 soft-reconfiguration inbound

    ! Advertise your local routes
    network 10.0.0.0 mask 255.0.0.0  ! DC subnets
    network 10.1.0.0 mask 255.255.0.0

    ! Optional: Receive routes from FCR
    ! (default: receive all routes advertised by FCR)

  exit-address-family

end
```text

### 3.2 Verification

```text
show bgp ipv4 unicast summary
  BGP router identifier 10.0.0.1, local AS number 65000

  Neighbor V AS MsgRcvd MsgSent InQ OutQ Up/Down State
  10.255.1.2 4 65001 10 10 0 0 00:05:32 Established
  10.255.1.6 4 65001 3 3 0 0 00:01:00 Established

show bgp ipv4 unicast
  Network Next Hop Metric LocPrf Weight Path
  *> 10.0.0.0/8 0.0.0.0 0 32768 i
  * 172.31.0.0/16 10.255.1.2 0 65001 16509 i  (AWS)
  *> 192.168.0.0/16 10.255.1.2 0 65001 8075 i  (Azure)
```text

---

## Step 4: Configure BGP on FCR (Optional for Advanced Topology)

### FCR BGP Configuration Model

FCR acts as a **Route Reflector** or **BGP Hub** peering with:
- Your on-prem routers
- Cloud provider routers
- Other FCR instances (multi-metro)

**Typical FCR BGP configuration** (managed via Equinix API):

```text
FCR BGP Configuration (Equinix-managed):
  ASN: 65001
  Router ID: 10.255.0.1

  BGP Neighbors:
    Your router (10.255.1.2): AS 65000
    AWS TGW (internal): AS 16509
    Azure VNG (internal): AS 8075
    GCP CCR (internal): AS 15169

  Route Reflection:
    Reflects routes from AWS → Your DC
    Reflects routes from Your DC → AWS
```text

**You typically don't configure FCR directly.** Equinix manages BGP on FCR; you configure:
- BGP adjacency (peering)
- Route advertisements (what you want to advertise)
- Route filtering (what routes you accept)

---

## Virtual Connection Management

### 3.1 Monitoring vConnection Status

```text
Equinix Console → Fabric → Virtual Connections

Status Codes:
  ACTIVE: Link is up, BGP can establish
  PROVISIONING: Being created (wait)
  PENDING_APPROVAL: Awaiting Equinix/customer approval
  WAITING_FOR_CUSTOMER: Waiting for your router config
  DEPROVISIONING: Being deleted
  DELETED: No longer available
  FAILED: Error (check notification details)
```text

### 3.2 Viewing BGP Peer Information

```text
Equinix Console → Fabric → Virtual Connections → [vConnection]
BGP Details:
  BGP Peer IP (Customer): 10.255.1.1
  BGP Peer IP (Equinix): 10.255.1.2
  BGP ASN (Customer): 65000
  BGP ASN (Equinix): 65001
  BGP Status: Established
  Uptime: 3 days 2 hours
```text

### 3.3 Upgrading vConnection Bandwidth

```text
Equinix Console → Fabric → Virtual Connections → [vConnection] → Edit

Bandwidth: 10Gbps → 100Gbps

[Apply]

Status: UPDATING → ACTIVE (typically 15–30 minutes)
```text

**No downtime during upgrade** (Equinix handles carrier transition).

### 3.4 Adding Redundancy

#### Initial Setup (Single vConnection)
```text
Your DC ←(vConnection #1)→ FCR
```text

#### Add Second vConnection
```text
Equinix Console → Fabric → Virtual Connections → New
(Create vConnection #2: identical to #1)

Result:
  Your DC ←(vConnection #1)→ FCR
  Your DC ←(vConnection #2)→ FCR
```text

#### Update BGP
```text
Your router:
  neighbor 10.255.1.2 remote-as 65001  ! vConnection #1
  neighbor 10.255.1.6 remote-as 65001  ! vConnection #2

(Both announce same routes; traffic load-balances)
```text

---

## vLAN Tagging (Layer 2 Details)

### Untagged vLAN (Simple)

```text
Your switch port → (untagged) → Equinix cross-connect → FCR vConnection
```text

**Configuration:**
- Your switch: Interface in native VLAN
- No tagging required
- Simplest setup

### Tagged vLAN (Multi-vConnection)

```text
Your switch port → (tagged)
  ├─ VLAN 100 → vConnection #1
  ├─ VLAN 101 → vConnection #2
  └─ VLAN 102 → Secondary DC
```text

**Configuration:**
```text
switch# conf t
interface Ethernet1/1
  switchport mode trunk
  switchport trunk allowed vlan 100,101,102
```text

---

## Equinix API Provisioning (Alternative to Console)

### 1. Authenticate

```bash
curl -X POST https://api.equinix.com/fabric/v4/auth/tokens \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your-api-key",
    "password": "your-api-secret"
  }'
```text

Result: `access_token` for subsequent API calls.

### 2. Create FCR (API)

```bash
curl -X POST https://api.equinix.com/fabric/v4/routers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-fcr-primary",
    "location": { "metroCode": "SJC" },
    "package": { "code": "STANDARD" },
    "notifications": [
      { "type": "ALL", "emails": ["ops@company.com"] }
    ]
  }'
```text

### 3. Create vConnection (API)

```bash
curl -X POST https://api.equinix.com/fabric/v4/connections \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "dc-to-fcr",
    "type": "IP_VC",
    "bandwidth": 10000,  # 10Gbps in Mbps
    "notifications": [{ "type": "ALL", "emails": ["ops@company.com"] }],
    "aSide": {
      "accessPoint": { "type": "COLO", "location": "SJC" },
      "linkProtocol": { "type": "DOT1Q", "vlanTag": 100 }
    },
    "zSide": {
      "accessPoint": {
        "type": "FABRIC_CLOUD_ROUTER",
        "router": { "uuid": "fcr-xxxxx" }
      }
    }
  }'
```text

---

## Troubleshooting Provisioning

### Issue: vConnection Stuck in "PENDING_APPROVAL"

**Cause:** Equinix waiting for approval.

**Fix:**
```text
Equinix Console → Virtual Connections → [vConnection] → Details
  Click: "Approve" (if option available)

Or contact Equinix support: support@equinix.com
```text

### Issue: BGP Peer Down

**Cause:** vConnection not ACTIVE, or BGP not configured on your router.

**Check:**
```text
Equinix Console → Virtual Connections → [vConnection]
  Status: ACTIVE? (if not, wait for provisioning)

Your router:
  show bgp ipv4 unicast summary
  show bgp ipv4 unicast neighbors 10.255.1.2
```text

**Fix:**
1. Ensure vConnection is ACTIVE
2. Verify BGP neighbor IP is correct
3. Check firewall allows BGP (port 179)
4. Verify ASN in BGP neighbor statement matches FCR ASN

### Issue: Routes Not Received

**Cause:** Routes not advertised by FCR or access list blocking.

**Check:**
```text
Your router:
  show bgp ipv4 unicast
  (Should see routes from AWS/Azure/GCP)

show bgp ipv4 unicast neighbors 10.255.1.2 received-routes
```text

**Fix:**
1. Verify FCR has received routes from cloud provider
2. Check route filtering/access lists on your router
3. Verify local preference isn't rejecting routes

---

## Best Practices

| Practice | Reason |
| --- | --- |
| **Use private ASNs (65000–65534)** | Easier to scale, avoids public ASN conflicts |
| **Deploy secondary FCR in different metro** | Survives metro failure |
| **Use aggressive BGP timers (3s/9s)** | Faster failure detection |
| **Document vConnection assignments** | Simplifies troubleshooting and changes |
| **Enable Equinix notifications** | Alerts on vConnection status changes |
| **Test BGP failover in lab first** | Avoid surprises in production |
| **Monitor BGP session uptime** | Track reliability (should be 99.9%+) |

---

## Summary

1. **Create FCR instance** in Equinix console (specify ASN, BGP timers)
2. **Create vConnections** (DC-to-FCR, cloud provider vConnections)
3. **Configure BGP** on your router (peer with FCR, advertise routes)
4. **Verify status** (BGP Established, routes received)
5. **Monitor uptime** (track convergence time, test failover)

---

## Next Steps

- [Cisco to Equinix FCR](cisco_to_equinix_fcr.md) — Complete Cisco config
- [FortiGate to Equinix FCR](fortigate_to_equinix_fcr.md) — FortiGate integration
- [IP WAN Best Practices](equinix_ip_wan_best_practices.md) — Design and operations
