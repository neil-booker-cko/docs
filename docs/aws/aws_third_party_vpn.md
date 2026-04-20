# AWS: Third-Party VPN Configuration Guide

Complete reference for establishing IPsec VPN connectivity from Amazon VPC to external third-party
networks without AWS Direct Connect. Uses AWS Virtual Private Gateway (VGW) and AWS-managed IPsec
tunnels with dynamic BGP routing or static routes.

For IPsec fundamentals see [IPsec & IKE](../theory/ipsec.md). For AWS Direct Connect (higher
throughput alternative) see [AWS Direct Connect Setup](aws_direct_connect_setup.md). For
troubleshooting see [IPsec VPN Troubleshooting](../operations/ipsec_vpn_troubleshooting.md).

---

## 1. Overview

### When to Use AWS Site-to-Site VPN

AWS VPN is appropriate when:

- No Direct Connect available in your region
- Lower bandwidth requirement (up to 1.25 Gbps aggregate)
- Cost-sensitive (pay per VPN connection + data transfer)
- Third-party peer is external; no shared dedicated circuit
- Failover option to DX (DX as primary, VPN as backup)

### Limitations vs Direct Connect

| Aspect | VPN | Direct Connect |
| --- | --- | --- |
| **Bandwidth** | Up to 1.25 Gbps | Dedicated circuits (1 Gbps, 10 Gbps, 100 Gbps) |
| **Latency** | Internet (variable, 30-100ms typical) | Dedicated (consistent, <20ms typical) |
| **Throughput** | Limited by Internet | Guaranteed |
| **Cost** | Lower per connection | Higher; monthly circuit fee |
| **Setup Time** | Minutes (console) | Days/weeks (carrier provisioning) |

---

## 2. Architecture

```mermaid
graph LR
    VPC["VPC<br/>CIDR: 10.0.0.0/16"]
    VGW["Virtual Private<br/>Gateway (VGW)<br/>ASN: 64512"]
    Internet["Internet<br/>IPsec Tunnel<br/>UDP 500 / 4500"]
    Peer["Third-Party Peer<br/>Remote Network<br/>192.168.0.0/16"]

    VPC -->|BGP ASN 64512| VGW
    VGW -->|Encrypt/Decrypt<br/>via IPsec| Internet
    Internet -->|IPsec Tunnel| Peer
    Peer -->|Return Traffic<br/>via Tunnel| Internet

    subgraph AWS ["AWS Configuration"]
        VGW
        RT["Route Table<br/>10.0.0.0/16 → VGW"]
    end

    subgraph TP ["Third-Party Config<br/>(Their Responsibility)"]
        Peer
        R["Routes to reach<br/>10.0.0.0/16"]
    end
```text

---

## 3. Configuration

### A. Create Virtual Private Gateway (VGW)

AWS Console:

1. VPC → Virtual Private Gateways → Create Virtual Private Gateway
2. Name: `third-party-vpn-gw`
3. ASN: `64512` (AWS default) or custom ASN for BGP
4. Create
5. Attach to VPC

Alternatively, via CLI:

```bash
aws ec2 create-vpn-gateway \
  --type ipsec.1 \
  --amazon-side-asn 64512 \
  --tag-specifications 'ResourceType=vpn-gateway,Tags=[{Key=Name,Value=third-party-vpn-gw}]'

aws ec2 attach-vpn-gateway \
  --vpn-gateway-id vgw-1a2b3c4d \
  --vpc-id vpc-12345678
```text

### B. Create Customer Gateway (CGW)

Define the third-party peer's public IP and BGP ASN.

AWS Console:

1. VPC → Customer Gateways → Create Customer Gateway
2. Name: `third-party-cgw`
3. BGP ASN: `65100` (third party's ASN; agree beforehand)
4. Public IP: `203.0.113.5` (third-party peer's public IP, or leave blank for dynamic)
5. Create

Via CLI:

```bash
aws ec2 create-customer-gateway \
  --type ipsec.1 \
  --public-ip 203.0.113.5 \
  --bgp-asn 65100 \
  --tag-specifications 'ResourceType=customer-gateway,Tags=[{Key=Name,Value=third-party-cgw}]'
```text

### C. Create Site-to-Site VPN Connection

AWS Console:

1. VPC → Site-to-Site VPN Connections → Create VPN Connection
2. Name: `third-party-vpn`
3. Virtual Private Gateway: `third-party-vpn-gw`
4. Customer Gateway: `third-party-cgw` (or Target Customer Gateway ID)
5. Static Route Propagation: disable (we'll use BGP)
6. Tunnel Options: keep defaults (AWS selects IKEv2, AES-256-GCM, etc.)
7. Create

Via CLI:

```bash
aws ec2 create-vpn-connection \
  --type ipsec.1 \
  --customer-gateway-id cgw-1a2b3c4d \
  --vpn-gateway-id vgw-1a2b3c4d \
  --options TunnelOptions=[{Phase1EncryptionAlgorithms=[{Value=AES256}],Phase2EncryptionAlgorithms=[{Value=AES256}]}]
```text

### D. Enable VPN Route Propagation (BGP)

For dynamic routing, enable BGP route propagation on your route tables.

AWS Console:

1. VPC → Route Tables → select your route table
2. Route Propagation tab → Edit Route Propagation
3. Select the VGW → Save

Via CLI:

```bash
aws ec2 enable-vgw-route-propagation \
  --route-table-id rtb-1a2b3c4d \
  --gateway-id vgw-1a2b3c4d
```text

Once enabled, AWS will automatically propagate routes learned from the third party via BGP.

### E. Download VPN Configuration

AWS Console:

1. VPC → Site-to-Site VPN Connections → select your connection
2. Download Configuration button → select your device type (Generic, Cisco, Fortinet, etc.)
3. Download the configuration file

This file contains:

- Pre-shared keys (PSK) for both tunnels
- VGW public IP addresses (two for redundancy)
- IKEv2 proposal parameters (encryption, DH group, etc.)
- IPsec Phase 2 settings

**Share the Pre-Shared Keys and tunnel endpoints with the third party.**

### F. Static Routes (If BGP Not Used)

If the third party cannot support BGP:

AWS Console:

1. VPC → Site-to-Site VPN Connections → select connection
2. Static Routes tab → Add Static Route
3. Destination: `192.168.0.0/16` (third-party network)
4. Add Route

Via CLI:

```bash
aws ec2 create-vpn-connection-route \
  --vpn-connection-id vpn-1a2b3c4d \
  --destination-cidr-block 192.168.0.0/16
```text

### G. Third-Party Configuration (Cisco Example)

On the third-party Cisco router, configure IPsec to match AWS VGW:

```ios
! Extract from AWS-provided config file:
! - PSK (Pre-Shared Key)
! - AWS VGW IP addresses (two tunnels)
! - IKEv2 proposal

crypto ikev2 proposal AWS-PROPOSAL
  encryption aes-cbc-256
  integrity sha256
  dh-group 14

crypto ikev2 policy AWS-POLICY
  proposal AWS-PROPOSAL

crypto ikev2 keyring AWS-KEYRING
  peer 54.240.228.1      ! AWS VGW tunnel endpoint 1
    pre-shared-key EXAMPLE_PSK_1
  peer 52.89.241.113     ! AWS VGW tunnel endpoint 2
    pre-shared-key EXAMPLE_PSK_2

crypto ipsec transform-set AWS-TS esp-aes 256 esp-sha256-hmac
  mode tunnel

crypto ipsec profile AWS-PROFILE
  set transform-set AWS-TS
  set pfs group14

interface Tunnel1
  ip address 169.254.10.1 255.255.255.252     ! AWS-provided address
  tunnel source 203.0.113.5
  tunnel destination 54.240.228.1
  tunnel mode ipsec ipv4
  ip mtu 1436
  tunnel protection ipsec profile AWS-PROFILE

router bgp 65100
  bgp router-id 203.0.113.5
  neighbor 169.254.10.2 remote-as 64512       ! AWS VGW BGP peer
  address-family ipv4
    network 192.168.0.0 mask 255.255.0.0
    neighbor 169.254.10.2 activate
  exit-address-family
```text

---

## 4. Comparison Summary

| Feature | AWS VPN | AWS Direct Connect | Choice |
| --- | --- | --- | --- |
| **Bandwidth** | Up to 1.25 Gbps aggregate | 1/10/100 Gbps dedicated | DX for high throughput |
| **Latency** | Internet (variable) | Consistent, low | DX for predictable latency |
| **Cost** | Per-connection + data | Monthly circuit | VPN for ad-hoc, DX for permanent |
| **Setup Time** | Minutes | Weeks | VPN for urgent |
| **BGP Support** | Yes | Yes | Both support dynamic routing |
| **Failover** | Can combine as DX+VPN backup | Primary | VPN as backup to DX |

---

## 5. Verification & Troubleshooting

### Check VGW Status

```bash
aws ec2 describe-vpn-gateways \
  --vpn-gateway-ids vgw-1a2b3c4d \
  --query 'VpnGateways[*].[VpnGatewayId,State,Type]'
```text

### Check VPN Connection Status

```bash
aws ec2 describe-vpn-connections \
  --vpn-connection-ids vpn-1a2b3c4d \
  --query 'VpnConnections[*].[VpnConnectionId,State,Options]'
```text

Both tunnels should show state: `available`. Tunnel state changes to `up` when third party
connects.

### Check BGP Routes Learned

```bash
aws ec2 describe-vpn-gateway-routes \
  --vpn-gateway-id vgw-1a2b3c4d \
  --filters Name=state,Values=available
```text

### Check Route Table Propagation

```bash
aws ec2 describe-route-tables \
  --route-table-ids rtb-1a2b3c4d \
  --query 'RouteTables[*].Routes[*].[DestinationCidrBlock,State,GatewayId]'
```text

---

## Common Issues

| Issue | Cause | Fix |
| --- | --- | --- |
| **Tunnel state: down** | No traffic; peer not connecting | Verify PSK and tunnel IPs with third party |
| **Tunnel up but no traffic** | BGP not established; no routes | Check BGP neighbor status; verify IPs |
| **Packet loss over tunnel** | MTU too large; fragmentation | Reduce tunnel MTU to 1436 or lower |
| **One tunnel down, one up** | ISP/carrier asymmetry | Normal; both tunnels maintain redundancy |

---

## Next Steps

- [IPsec & IKE](../theory/ipsec.md) — Protocol fundamentals
- [IPsec VPN Troubleshooting](../operations/ipsec_vpn_troubleshooting.md) — Detailed diagnostics
- [AWS Direct Connect Setup](aws_direct_connect_setup.md) — Higher bandwidth alternative
