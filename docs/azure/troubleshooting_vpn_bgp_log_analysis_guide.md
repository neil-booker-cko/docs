# Troubleshooting Azure VPN & BGP: Log Analysis Guide

## 1. Overview

This guide covers log signatures for common failure scenarios in the
ExpressRoute + VPN overlay architecture: IKEv2 negotiation failures, DPD
timeouts, BGP session drops, and ExpressRoute underlay issues. Log sources
are FortiGate and Cisco IOS-XE; Azure-side events are visible in the Azure
portal under **VPN Gateway Diagnostics** and **ExpressRoute Circuit Metrics**.

---

## 2. IKEv2 / IPsec Failures

### Phase 1 — IKEv2 Proposal Mismatch

**Symptom:** Tunnel does not establish after configuration change.

**FortiGate log signature:**

```text
ike 0:azure-vpn-primary: sent IKE msg (SA_INIT): x.x.x.x:500->y.y.y.y:500
ike 0:azure-vpn-primary: recv IKE msg (SA_INIT): y.y.y.y:500->x.x.x.x:500
ike 0:azure-vpn-primary: proposal did not match
ike 0:azure-vpn-primary: no SA proposal chosen
```

**Cause:** Encryption, integrity, or DH group mismatch between FortiGate
Phase 1 proposal and Azure VPN Gateway policy.

**Resolution:** Azure VPN Gateway custom policy requires matching on:
`ike-encryption`, `ike-integrity`, `dh-group`, `ipsec-encryption`,
`ipsec-integrity`, `pfs-group`. Verify in Azure portal under
Connection → IKE Policy. Default Azure policy accepts `aes256-sha256-dh2`.

---

### Phase 2 — Quick Mode / Child SA Failure

**FortiGate log signature:**

```text

ike 0:azure-vpn-primary:azure-vpn-primary-p2: failed to get a proposal chosen
ike 0:azure-vpn-primary: IPsec SA connect 500 x.x.x.x->y.y.y.y:500 failed
```

**Cause:** Phase 2 encryption/integrity/PFS mismatch or traffic selector
mismatch. Azure VPN Gateway in route-based mode uses `0.0.0.0/0` traffic
selectors — FortiGate Phase 2 must also use `0.0.0.0/0` (not specific subnets).

---

### DPD Timeout — Silent Path Loss

**FortiGate log signature:**

```text

ike 0:azure-vpn-primary: DPD timeout
ike 0:azure-vpn-primary: connection expiring due to phase1 down
ike 0:azure-vpn-primary: sending delete for IKEv2 SA
iked[500]: azure-vpn-primary goes DOWN
```

**Followed by BGP withdrawal (link-down-failover):**

```text

BGP: %BGP-5-ADJCHANGE: neighbor 169.254.21.1 Down Interface flap
```

**Normal behaviour** when `link-down-failover enable` is configured.
Investigate the underlying path: check ExpressRoute circuit metrics for
packet loss, or Cisco `show interfaces` for physical errors on the ER port.

---

## 3. BGP Session Issues

### BGP Hold-Timer Expiry

**FortiGate log signature:**

```text

BGP: %BGP-5-ADJCHANGE: neighbor 169.254.21.1 Down BGP Notification sent
BGP: %BGP-3-NOTIFICATION: sent to neighbor 169.254.21.1 4/0 (hold time expired)
```

**Cause:** BGP keepalives not reaching the peer within the hold-timer window.
Common causes: DPD detection in progress, CPU overload on gateway, or IPsec
re-key causing brief loss of encrypted path.

**Resolution:** Verify the BGP hold-timer (30s) is greater than total DPD
detection time (5s × 3 = 15s). Check `diagnose vpn tunnel list` for re-key
events overlapping with the BGP failure timestamp.

---

### BGP Stuck in OpenConfirm

**FortiGate log signature:**

```text

BGP: %BGP-5-ADJCHANGE: neighbor 169.254.21.1 -> OpenConfirm
BGP: %BGP-3-NOTIFICATION: received from neighbor 169.254.21.1 2/2 (peer in wrong state)
```

**Cause:** TCP session established but BGP OPEN rejected. Common causes:
ASN mismatch (Azure VPN GW default ASN is `65515` — check `remote-as` on
FortiGate), MD5 authentication mismatch (not commonly used on VPN overlay),
or APIPA BGP address not matching the Azure connection custom BGP IP setting.

---

### Routes Not Received from Azure

**FortiGate diagnostic:**

```fortios

get router info bgp neighbors 169.254.21.1
! Check: "BGP state = Established"
! Check: "Updates received" counter is non-zero
! If zero: Azure VNet may not have a connection advertising routes

get router info bgp network
! Azure VNet prefix should appear with Next Hop 169.254.21.1
```

**Cisco diagnostic — underlay reachability:**

```ios

show ip route 172.16.0.2
! Must be reachable via ExpressRoute (not internet) for private IP mode to work
show bgp neighbors 172.16.0.2 advertised-routes
! Verify on-premises prefixes are being sent to MSEE
```

---

## 4. ExpressRoute Underlay Issues

### BFD Session Down on MSEE Peering

**Cisco log signature:**

```text

%BFD-6-BFD_SESS_DOWN: BFD session ld:4097 handle:1 is going down Reason: DETECT_TIMER_EXPIRED
%BGP-5-ADJCHANGE: neighbor 172.16.0.2 Down BFD adjacency down
```

**Cause:** Physical circuit degradation, provider issue, or MSEE maintenance.
Check Azure portal → ExpressRoute Circuit → Metrics → BitsInPerSecond / BitsOutPerSecond
for traffic anomalies. Contact provider if physical layer is clean but BGP is flapping.

**Cisco diagnostics:**

```ios

show bfd neighbors detail
! Check "Last packet transmitted" and "Last packet received" timestamps
show interfaces <ER-interface>
! Look for input errors, CRC errors, resets

show bgp neighbors 172.16.0.2 | include BGP state|Hold time|keepalives
```

---

### Route Asymmetry Between Primary and Secondary ER

**Symptom:** Traffic takes different paths inbound vs outbound; asymmetric latency.

**Cause:** MSEE sends the same prefix via both circuits. FortiGate/Cisco prefers
one path but Azure forwards returns via the other circuit.

**Resolution:** Use **connection weight** in Azure (higher = preferred) to steer
Azure-to-on-prem traffic to the preferred circuit, and `local-preference` on the
Cisco side to steer on-prem-to-Azure traffic symmetrically.

```ios

route-map RM-ER-PRIMARY-IN permit 10
 match ip address prefix-list PFX-AZURE-VNETS
 set local-preference 200
!
route-map RM-ER-SECONDARY-IN permit 10
 match ip address prefix-list PFX-AZURE-VNETS
 set local-preference 100
```

---

## 5. Azure-Side Diagnostics

Azure does not expose BGP session logs in the same way as IOS or FortiGate.
Use the following Azure tools:

| Tool | Location | Purpose |
| --- | --- | --- |
| **VPN Gateway BGP Peer Status** | Portal → VPN GW → BGP Peers | Confirm BGP state and prefixes learned |
| **VPN Gateway Diagnostics** | Portal → VPN GW → Diagnose and solve | IKEv2 tunnel status and logs |
| **ExpressRoute Circuit Metrics** | Portal → ER Circuit → Metrics | BitsIn/Out, ArpAvailability, BgpAvailability |
| **Network Watcher** | Portal → Network Watcher → VPN Diagnostics | Packet capture and gateway logs |
| **Azure Monitor** | Log Analytics Workspace | `AzureDiagnostics` table for gateway events |

### Useful Azure Monitor Query

```kusto

AzureDiagnostics
| where ResourceType == "VIRTUALNETWORKGATEWAYS"
| where Category == "GatewayDiagnosticLog"
| where Message contains "BGP" or Message contains "IKE"
| order by TimeGenerated desc
| take 50
```

---

## 6. Quick Fault Isolation Checklist

```text

VPN tunnel not up?
  └─ Check Phase 1: diagnose vpn ike log-filter dst-addr4 <azure-gw-ip>
  └─ Check proposal: aes256-sha256, dhgrp 2 (or match Azure custom policy)
  └─ Check private IP routing: can FortiGate reach Azure GW private IP via ER?

BGP not establishing?
  └─ Confirm tunnel is UP first
  └─ Check remote-as matches Azure VPN GW ASN (default 65515)
  └─ Check APIPA addresses match Azure connection custom BGP IP settings

BGP established but no routes?
  └─ Verify Azure VNet is connected to VPN Gateway
  └─ Check route-map-in is not filtering Azure prefixes
  └─ Confirm on-prem prefixes advertised: get router info bgp neighbors x advertised-routes

Underlay ER BGP flapping?
  └─ Check BFD: show bfd neighbors
  └─ Check interface errors: show interfaces <ER-port>
  └─ Check Azure portal ExpressRoute circuit metrics for BgpAvailability
```
