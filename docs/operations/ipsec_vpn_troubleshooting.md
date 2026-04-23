# IPsec VPN Troubleshooting

Layered diagnostic approach for IPsec VPN connectivity issues. IPsec VPN establishment proceeds
through four distinct layers: network reachability, IKE Phase 1 (ISAKMP SA), IPsec Phase 2 (Child SA),
and routing/traffic flow. Each layer has specific diagnostic commands and common failure modes.

For IPsec theory see [IPsec & IKE](../theory/ipsec.md). For third-party VPN configuration see
[FortiGate Third-Party VPN](../fortigate/fortigate_third_party_vpn.md), [AWS Third-Party VPN](../aws/aws_third_party_vpn.md),
[Azure Third-Party VPN](../azure/azure_third_party_vpn.md), [GCP Third-Party VPN](../gcp/gcp_third_party_vpn.md).

---

## IPsec State Machine

```mermaid
graph TD
    IDLE["IDLE<br/>No connection"]
    IKE1["IKE Phase 1<br/>Negotiate encryption<br/>authentication, DH"]
    IKE2["IKE Phase 2<br/>Negotiate IPsec<br/>transform-set, traffic selectors"]
    EST["ESTABLISHED<br/>SA active<br/>Traffic flowing"]
    REKEY["REKEYING<br/>SA lifetime expired<br/>New SA negotiating"]
    DOWN["DOWN<br/>SA deleted or error"]

    IDLE -->|Initiate| IKE1
    IKE1 -->|Phase 1 OK| IKE2
    IKE1 -->|Timeout/Mismatch| DOWN
    IKE2 -->|Phase 2 OK| EST
    IKE2 -->|Timeout/Mismatch| DOWN
    EST -->|Lifetime expired| REKEY
    REKEY -->|Rekey OK| EST
    REKEY -->|Rekey fail| DOWN
    EST -->|Peer disconnect| DOWN
    DOWN -->|Manual clear| IDLE
```text

---

## Layer 1: Network Reachability

IPsec requires UDP 500 (IKE) and UDP 4500 (IPsec NAT-Traversal) to reach the peer. Network-layer
issues block IKE negotiation before any cryptographic errors can occur.

### Check UDP 500/4500 Reachability

**From local side:**

```bash
# Test UDP 500 reachability to peer
nc -u -w 1 203.0.113.5 500 < /dev/null

# Test UDP 4500 reachability (NAT-Traversal)
nc -u -w 1 203.0.113.5 4500 < /dev/null

# Ping peer public IP (ICMP)
ping -c 3 203.0.113.5
```text

**Expected behavior:**
- UDP tests return immediately (even if peer doesn't respond, no timeout)
- Ping returns replies (indicates network path exists)

**Common failures:**
- Connection timeout → Firewall blocking; check ACLs or NSGs
- No route to host → Routing issue on local gateway

### Check Firewall Rules

**Cisco ASA / IOS firewall:**

```ios
show access-list | include 203.0.113.5
show route 203.0.113.5
```text

**AWS Security Group / NACLs:**

```bash
aws ec2 describe-security-groups \
  --query 'SecurityGroups[*].[GroupId, GroupName, IpPermissions]' \
  --filters "Name=ip-permission.from-port,Values=500" "Name=ip-permission.to-port,Values=500"
```text

**Azure Network Security Group:**

```bash
az network nsg rule list \
  --resource-group my-rg \
  --nsg-name my-nsg \
  --query "[?protocol=='UDP' && (destinationPortRange=='500' || destinationPortRange=='*')]"
```text

**FortiGate firewall policy:**

```fortios
show firewall policy | grep 203.0.113.5
```text

### Check NAT & NAT-Traversal

If either side is behind NAT, IPsec uses UDP 4500 (NAT-Traversal). Some firewalls block or mangle
UDP 4500.

**Cisco:** NAT exemptions required for IPsec traffic:

```ios
access-list 101 permit esp 10.0.0.0 0.0.255.255 203.0.113.0 0.0.0.255
nat (inside) 0 access-list 101
```text

**Azure / AWS:** Security groups/NACLs must allow UDP 4500 inbound/outbound.

**FortiGate:** Automatic NAT-Traversal detection; no manual config required.

---

## Layer 2: IKE Phase 1 (ISAKMP SA)

Phase 1 negotiates encryption, authentication, and Diffie-Hellman parameters to establish a secure
channel for Phase 2 negotiation. Failures here indicate cryptographic algorithm or pre-shared key
mismatches.

### Common Phase 1 Failures

| Error | Cause | Fix |
| --- | --- | --- |
| **IKE proposal mismatch** | Encryption, integrity, or DH group differs | Agree on same proposal; common: AES-256, SHA-256, DH group 14 |
| **Pre-Shared Key (PSK) mismatch** | Different PSK on local vs peer | Verify PSK identity on both sides (case-sensitive) |
| **Peer ID mismatch** | Local ID (FQDN, IP) doesn't match peer expectation | Verify peer ID configuration (IKEv2 uses IP by default) |
| **DPD timeout** | Dead Peer Detection timeout; peer unresponsive | Increase DPD retry interval; check peer firewall |
| **Main Mode timeout** | IKEv1 Main Mode negotiation stalled | Switch to Aggressive Mode or IKEv2 (recommended) |

### Cisco IOS-XE Diagnostics

```ios
! Check IKE SAs (Security Associations)
show crypto ikev2 sa
! Example output:
!  IKEv2 SAs:
!  Session-id:local  203.0.113.1-13/0x0   remote 198.51.100.5-11/0x0
!  Status : ESTABLISHED

! Check IKE proposals configured
show crypto ikev2 proposal
! Example: encryption aes-cbc-256, integrity sha256, dh-group 14

! Enable IKE debug (verbose)
debug crypto ikev2

! Check pre-shared key in keyring
show crypto keyring
! DO NOT display actual PSK; just verify it exists

! Check peer IP / identity
show crypto ikev2 profile
```text

### FortiGate Diagnostics

```fortios
! Check IKE SAs
diagnose vpn ike status
! Example output: STATUS_ESTABLISHED (Phase 1 active)

! Check IKE proposal
show vpn ike
! Lists IKE proposals; verify encryption, integrity, dh-group

! Enable IKE debug
diagnose debug reset
diagnose debug enable
diagnose debug application ike -1

! Check pre-shared key (masked)
show vpn ipsec manual
! Verify PSK identity matches peer

! Check DPD status
show vpn ike detailed
```text

### Verify PSK & Peer IP

**Both sides must have:**
1. **Same PSK** (string or hex, case-sensitive)
2. **Peer's public IP** correctly configured
3. **IKEv2 proposal** (encryption, integrity, DH) matching

---

## Layer 3: IPsec Phase 2 (Child SA / CHILD_SA)

Phase 2 establishes the IPsec tunnel protecting data traffic. Failures here indicate transform-set
(ESP algorithm) or traffic selector mismatches.

### Common Phase 2 Failures

| Error | Cause | Fix |
| --- | --- | --- |
| **Transform mismatch** | ESP encryption/authentication differs | Agree on same transform-set; common: AES-256, HMAC-SHA-256 |
| **Traffic selector mismatch** | Local subnets don't match peer's expectations | Verify subnets (CIDR ranges) on both sides |
| **PFS group mismatch** | Perfect Forward Secrecy group differs | Match DH group (group 14 common) or disable PFS on both sides |
| **SA lifetime mismatch** | Rekey lifetime differs significantly | Set same lifetime on both sides (3600 seconds common) |
| **NAT-T protocol issue** | UDP 4500 blocked or rewritten | Check firewall; may need to disable NAT-Traversal if both sides public |

### Cisco IOS-XE Diagnostics

```ios
! Check IPsec SAs (Phase 2)
show crypto ipsec sa
! Example output:
!  outbound esp sas:
!    spi: 0x12345678(305441912)
!      transform: esp-aes 256 esp-sha256-hmac
!      in use settings: tunnel mode, transform set MYTS
!  inbound esp sas:
!    spi: 0x87654321(2271908641)

! Check transform-set
show crypto ipsec transform-set
! Example: crypto ipsec transform-set MYTS esp-aes 256 esp-sha256-hmac

! Check traffic selectors (crypto ACL)
show access-list | include crypto
! Example: permit ip 10.0.0.0 0.0.255.255 192.168.0.0 0.0.255.255

! Enable IPsec debug
debug crypto ipsec
```text

### FortiGate Diagnostics

```fortios
! Check IPsec Phase 2 SAs
diagnose vpn tunnel list
! Example output:
!  partner-vpn: local-ip=203.0.113.1 remote-ip=198.51.100.5
!  Status: up
!  Incoming: 1234 bytes, Outgoing: 5678 bytes
!  spi: 0xabcd1234 (inbound), 0x5678ef00 (outbound)

! Check IPsec proposal
show vpn ipsec
! Lists Phase 2 proposals (ESP transforms)

! Check traffic selectors (policy)
show vpn ipsec phase2-interface
! Verifies which subnets are protected by the tunnel

! Enable IPsec debug
diagnose debug reset
diagnose debug enable
diagnose debug application ipsec -1
```text

### Verify Transform-Set & Traffic Selectors

**Both sides must have:**
1. **Same transform-set** (ESP encryption/authentication)
2. **Matching traffic selectors** (local subnet ↔ remote subnet)
3. **Same PFS group** (or both disabled)
4. **Synchronous SA lifetimes** (or at least similar)

---

## Layer 4: Routing & Traffic Flow

Once Phase 1 and Phase 2 are established, the tunnel is up but traffic may not flow if routes are
missing or policies block traffic.

### Check Routes over Tunnel

**Cisco:**

```ios
! Check static routes pointing to tunnel
show route | include tunnel

! Check dynamic routes learned via BGP
show ip bgp summary
show ip bgp neighbors 169.254.21.2
show ip route bgp | include 192.168.0.0

! Check route table
show ip route 192.168.0.0
```text

**Azure:**

```bash
az network route-table route list \
  --resource-group my-rg \
  --route-table-name my-routes \
  --query "[*].[name, addressPrefix, nextHopType]"
```text

**AWS:**

```bash
aws ec2 describe-route-tables \
  --route-table-ids rtb-1a2b3c4d \
  --query 'RouteTables[*].Routes[*].[DestinationCidrBlock, State, GatewayId]'
```text

**GCP:**

```bash
gcloud compute routes list --filter "network:my-vpc" \
  --format "table(name,destination_range,next_hop_gateway,next_hop_vpn_tunnel)"
```text

**FortiGate:**

```fortios
get router info routing-table all
! Check if peer subnets are reachable via tunnel interface

diagnose ip route list
! Detailed routing table with metrics
```text

### Check Asymmetric Routing

Asymmetric routing occurs when return traffic takes a different path than outbound traffic.

**Check:**
1. Both sides have routes to each other's subnets
2. Both sides send traffic through the same tunnel
3. BGP metrics agree on which path is preferred

**Example (asymmetric):**
- Spoke A → Hub → Spoke B (outbound via tunnel)
- Spoke A ← Spoke B directly (return bypasses hub; no tunnel)

#### Fix:
- Ensure both spokes have static routes or BGP routes pointing via hub for all remote subnets
- In DMVPN Phase 3, disable split-horizon on hub EIGRP interface

### Check ACLs & Policies Blocking Traffic

**Cisco ASA / IOS:**

```ios
show access-list | include 192.168.0.0
! Verify ACL permits traffic from VPC to peer subnet
```text

**AWS Security Group:**

```bash
aws ec2 describe-security-groups \
  --group-id sg-12345678 \
  --query 'SecurityGroups[0].IpPermissions'
```text

**Azure NSG:**

```bash
az network nsg rule list \
  --resource-group my-rg \
  --nsg-name my-nsg \
  --query "[?destinationAddressPrefix=='192.168.0.0/16']"
```text

**FortiGate:**

```fortios
show firewall policy | grep partner-vpn
! Verify policy permits traffic from internal → tunnel interface
```text

### Check MTU & Fragmentation

IPsec adds overhead (~73 bytes for ESP + ICV). If MTU is too large, packets fragment or get dropped
(if DF bit set).

**Calculate tunnel MTU:**

```text
Tunnel MTU = Interface MTU − IPsec overhead (73 bytes ESP + ICV)
Example: 1500 − 73 = 1427 bytes
```text

**Check MTU on tunnel interface:**

**Cisco:**

```ios
show interface tunnel 0 | include MTU
! Should be 1400-1436 bytes (accounting for IPsec overhead)
```text

**FortiGate:**

```fortios
show system interface | grep -A 5 partner-vpn
! Check mtu setting (should be ~1400 bytes)
```text

**AWS / Azure / GCP:** MTU typically set to 1500 at VPN gateway; endpoints should clamp MSS to 1379
or lower.

---

## Common Issues Quick Reference

| Symptom | Likely Cause | First Check | Fix |
| --- | --- | --- | --- |
| **Tunnel never comes up** | Network unreachable or firewall blocking | Ping peer IP; check UDP 500/4500 | Allow UDP 500/4500; check firewall rules |
| **IKE Phase 1 fails** | PSK mismatch or proposal mismatch | `show crypto ikev2 sa`; check PSK | Verify PSK matches; align IKE proposal |
| **IKE Phase 1 OK, Phase 2 fails** | Transform mismatch or traffic selector mismatch | `show crypto ipsec sa`; check ACL | Align transform-set; verify subnets match |
| **Tunnel up but no traffic** | Routes missing or ACL blocking | `show route`; check firewall policy | Add static route or BGP route; verify ACL |
| **Asymmetric traffic** | Return path doesn't use tunnel | `traceroute` from both sides | Add routes on both sides; verify BGP metrics |
| **High packet loss over tunnel** | MTU too large; fragmentation | Check tunnel MTU vs interface MTU | Reduce tunnel MTU to 1300-1400 bytes |
| **Intermittent disconnections** | DPD timeout or slow rekey | Check DPD settings; check SA lifetime | Increase DPD retry interval; extend lifetime |
| **One tunnel up, one down** | ISP/carrier asymmetry or single link failure | Check both tunnel states separately | Normal for redundant designs; both protect traffic |

---

## Cisco IOS-XE Comprehensive Diagnostics

### Phase 1 & Phase 2 Status

```ios
! Full IKE & IPsec status
show crypto session brief
! Compact summary of all tunnels

show crypto ikev2 sa
! IKE Phase 1 Security Associations

show crypto ipsec sa
! IPsec Phase 2 (ESP) Security Associations

show crypto ipsec sa peer 203.0.113.5
! Filter by peer IP
```text

### Configuration Verification

```ios
! IKE proposal
show crypto ikev2 proposal
show crypto ikev2 policy

! IPsec transform-set
show crypto ipsec transform-set

! Traffic selectors (crypto ACL)
show access-list | include crypto

! Pre-shared keys (masked for security)
show crypto ikev2 keyring
show crypto keyring
```text

### Debug Output

```ios
! Verbose IKE negotiation
debug crypto ikev2
! Shows proposal exchange, DH, authentication

! Verbose IPsec negotiation
debug crypto ipsec
! Shows Phase 2 negotiation, transform-set, traffic selectors

! Disable debug (important!)
undebug all
```text

### Real-Time Monitoring

```ios
! Monitor tunnel status continuously
! (requires SSH session or terminal)
debug crypto condition peer 203.0.113.5
! Filters debug output to specific peer

! Monitor tunnel rekey
show crypto ipsec sa | include Lifetime
```text

---

## FortiGate Comprehensive Diagnostics

### Phase 1 & Phase 2 Status

```fortios
! IKE Phase 1 status
diagnose vpn ike status
! Lists ISAKMP SAs; status should be STATUS_ESTABLISHED

! IPsec Phase 2 tunnel status
diagnose vpn tunnel list
! Shows tunnel endpoints, in/out bytes, SPI values

! Detailed tunnel info
show vpn ipsec tunnel status
! Similar to diagnose vpn tunnel list (FortiOS 7+)
```text

### Configuration Verification

```fortios
! IKE proposals
show vpn ike

! IPsec proposals (Phase 2)
show vpn ipsec

! Tunnel interfaces
show system interface | grep tunnel

! Pre-shared key (masked)
show vpn ipsec manual
! Displays configured PSK identity (not plaintext)
```text

### Debug Output

```fortios
! Enable debug logging
diagnose debug reset
diagnose debug enable

! IKE debug
diagnose debug application ike -1

! IPsec debug
diagnose debug application ipsec -1

! Filter to specific peer
diagnose vpn ike log filter name partner-vpn

! Disable debug
diagnose debug disable
```text

### Real-Time Monitoring

```fortios
! Monitor active sessions over tunnel
diagnose sys session list | grep partner-vpn
! Shows active flows (source, destination, protocol, bytes)

! Monitor tunnel rekey
diagnose vpn tunnel list | grep -i rekey

! Monitor DPD heartbeats
diagnose vpn ike log list
! Shows IKE events including DPD
```text

---

## Troubleshooting Flowchart

1. **Tunnel shows down?**
   - ✓ Check UDP 500/4500 reachability (Layer 1)
   - ✓ Verify firewall rules allow traffic
   - ✓ Check IKE Phase 1 status (IKE SA established?)

2. **IKE Phase 1 fails?**
   - ✓ Verify PSK matches (case-sensitive)
   - ✓ Verify IKE proposal (encryption, integrity, DH group)
   - ✓ Check peer IP configuration

3. **IKE Phase 1 OK, Phase 2 fails?**
   - ✓ Verify IPsec transform-set matches
   - ✓ Verify traffic selectors (local/remote subnets)
   - ✓ Check PFS group mismatch

4. **Tunnel up, traffic not flowing?**
   - ✓ Verify routes exist (static or BGP)
   - ✓ Check ACLs / firewall policies
   - ✓ Verify MTU (1300-1400 bytes typical)

5. **Intermittent drops or high packet loss?**
   - ✓ Check MTU and fragmentation
   - ✓ Check DPD / keepalive settings
   - ✓ Monitor SA rekey events

---

## Next Steps

- [IPsec & IKE](../theory/ipsec.md) — Detailed protocol theory
- [IPsec VPN Best Practices](ipsec_vpn_best_practices.md) — Security hardening and configuration
- [FortiGate Third-Party VPN](../fortigate/fortigate_third_party_vpn.md) — Device-specific config
- [AWS Third-Party VPN](../aws/aws_third_party_vpn.md) — Cloud VPN setup
