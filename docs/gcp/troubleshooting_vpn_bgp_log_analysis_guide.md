# Troubleshooting GCP VPN & BGP: Log Analysis Guide

## 1. Overview

This guide covers log signatures for common failure scenarios in the
Cloud Interconnect + HA VPN overlay architecture: IKEv2 negotiation failures,
DPD timeouts, BGP session drops, and Cloud Interconnect underlay issues.
Log sources are FortiGate and Cisco IOS-XE. GCP-side events are visible via
**Cloud Logging** (`gcloud logging`) and the Cloud Console VPN/Router pages.

---

## 2. IKEv2 / IPsec Failures

### Phase 1 — Proposal Mismatch

**Symptom:** HA VPN tunnel does not establish.

**FortiGate log signature:**

```text
ike 0:gcp-havpn-tunnel1: sent IKE msg (SA_INIT): x.x.x.x:500->y.y.y.y:500
ike 0:gcp-havpn-tunnel1: recv IKE msg (SA_INIT): y.y.y.y:500->x.x.x.x:500
ike 0:gcp-havpn-tunnel1: proposal did not match
ike 0:gcp-havpn-tunnel1: no SA proposal chosen
```

**Cause:** GCP HA VPN default IKEv2 proposal: `aes256-sha256, dh14`.
Common mismatch: FortiGate configured with `dhgrp 2` (1024-bit) while GCP
defaults to group 14 (2048-bit). GCP also supports groups 15, 16, 19, 20.

**Resolution:** Set FortiGate Phase 1 `dhgrp 14` to match GCP's default,
or create a custom policy in GCP that matches your FortiGate configuration.

---

### Phase 1 — Pre-Shared Key Mismatch

**FortiGate log signature:**

```text
ike 0:gcp-havpn-tunnel1: AUTH verification failed
ike 0:gcp-havpn-tunnel1: sending AUTHENTICATION_FAILED notify
ike 0:gcp-havpn-tunnel1: established failed
```

**Cause:** PSK set in FortiGate Phase 1 does not match the PSK configured on
the GCP VPN tunnel. Note: GCP requires separate PSKs per tunnel (Tunnel 1 and
Tunnel 2 of an HA VPN gateway have independent PSKs).

---

### DPD Timeout — Silent Path Loss

**FortiGate log signature:**

```text
ike 0:gcp-havpn-tunnel1: DPD timeout
ike 0:gcp-havpn-tunnel1: connection expiring due to phase1 down
ike 0:gcp-havpn-tunnel1: sending delete for IKEv2 SA
iked[500]: gcp-havpn-tunnel1 goes DOWN
BGP: %BGP-5-ADJCHANGE: neighbor 169.254.1.1 Down Interface flap
```

**Normal behaviour** with `link-down-failover enable`. The second tunnel should
absorb traffic immediately. Investigate the underlying path: check Interconnect
circuit metrics or Cisco interface errors if both tunnels DPD simultaneously.

**GCP Cloud Logging query for tunnel events:**

```bash
gcloud logging read \
  'resource.type="vpn_tunnel" AND
   (jsonPayload.message:"DPD" OR jsonPayload.message:"tunnel down")' \
  --limit=20 --format=json
```

---

## 3. BGP Session Issues

### BGP Hold-Timer Expiry

**FortiGate log signature:**

```text
BGP: %BGP-5-ADJCHANGE: neighbor 169.254.1.1 Down BGP Notification sent
BGP: %BGP-3-NOTIFICATION: sent to neighbor 169.254.1.1 4/0 (hold time expired)
```

**Cause:** BGP keepalives lost during IKEv2 re-key or DPD event. Verify the
hold-timer (30s) exceeds the DPD detection window (10s × 2 = 20s). Check
`diagnose vpn tunnel list name gcp-havpn-tunnel1` for re-key events coinciding
with the BGP drop timestamp.

---

### BGP OpenConfirm / Capability Error

**FortiGate log signature:**

```text
BGP: %BGP-5-ADJCHANGE: neighbor 169.254.1.1 -> OpenConfirm
BGP: %BGP-3-NOTIFICATION: received from neighbor 169.254.1.1 2/6 (Unsupported Capability)
```

**Cause:** BGP capability negotiation failed. Common causes: ASN mismatch
(`remote-as` on FortiGate does not match Cloud Router ASN `65001`), or
multi-protocol capability conflict. Cloud Router requires standard IPv4 unicast
BGP — no additional capability flags needed.

---

### Routes Not Received from Cloud Router

**FortiGate diagnostic:**

```fortios
get router info bgp neighbors 169.254.1.1
! Check: BGP state = Established
! Check: "Updates received" counter is non-zero

get router info bgp network
! GCP VPC prefix should appear with Next Hop 169.254.1.1 or 169.254.2.1
```

**GCP diagnostic:**

```bash
# Confirm Cloud Router sees the on-premises prefix
gcloud compute routers get-status gcp-vpn-router \
  --region=europe-west2 \
  --format="json(result.bgpPeerStatus)"

# Check what routes are being advertised to FortiGate
gcloud compute routers get-status gcp-vpn-router \
  --region=europe-west2 \
  --format="json(result.bgpPeerStatus[].advertisedRoutes)"
```

**Common causes:** Cloud Router in custom advertisement mode with the VPC
subnet not explicitly listed, or VPC subnet routes not being exported to
the Cloud Router's region.

---

## 4. Cloud Interconnect Underlay Issues

### BFD Session Down on Interconnect VLAN Attachment

**Cisco log signature:**

```text
%BFD-6-BFD_SESS_DOWN: BFD session ld:4097 handle:1 is going down Reason: DETECT_TIMER_EXPIRED
%BGP-5-ADJCHANGE: neighbor 169.254.0.2 Down BFD adjacency down
```

**Cause:** Physical circuit degradation or partner provider issue. Check
GCP console → Cloud Interconnect → Circuit → Metrics for operational status.
For Dedicated Interconnect, contact Google or the co-location provider.
For Partner Interconnect, contact the service provider.

**Cisco diagnostics:**

```ios
show bfd neighbors detail
! Check "Last packet received" timestamp — staleness indicates physical loss
show interfaces <IC-subinterface>
! Look for CRC errors, input errors, resets
show bgp neighbors 169.254.0.2 | include BGP state|Hold|keepalive
```

**GCP diagnostics:**

```bash
# Check VLAN attachment operational state
gcloud compute interconnects attachments describe <ATTACHMENT-NAME> \
  --region=europe-west2 \
  --format="yaml(operationalStatus,state)"

# View Interconnect metrics in Cloud Monitoring
gcloud monitoring metrics list --filter="metric.type:interconnects"
```

---

### Asymmetric Routing Between ECMP Paths

**Symptom:** Stateful firewall dropping return traffic; sessions stalling.

**Cause:** FortiGate installed both HA VPN tunnels as ECMP paths. GCP returns
traffic via a different path than the one used outbound. Without zone grouping,
FortiGate's state table rejects the asymmetric return packets.

**Resolution:**

```fortios
! Confirm both tunnel interfaces are in the same zone
config system zone
    edit "ZONE_GCP_VPN"
        set interface "gcp-havpn-tunnel1" "gcp-havpn-tunnel2"
    next
end

! Confirm loose RPF is set
config system interface
    edit "gcp-havpn-tunnel1"
        set src-check loose
    next
    edit "gcp-havpn-tunnel2"
        set src-check loose
    next
end
```

---

## 5. GCP-Side Diagnostics

| Tool | Command / Location | Purpose |
| --- | --- | --- |
| **Cloud Router BGP status** | `gcloud compute routers get-status <ROUTER>` | BGP session state, prefixes learned/advertised |
| **VPN tunnel status** | `gcloud compute vpn-tunnels describe <TUNNEL>` | IKEv2 status, DPD state |
| **Cloud Logging** | `gcloud logging read 'resource.type="vpn_tunnel"'` | Tunnel up/down events |
| **Cloud Logging (Router)** | `gcloud logging read 'resource.type="gce_router"'` | BGP session events |
| **VPC Routes** | `gcloud compute routes list --filter="network=prod-vpc"` | Dynamic routes learned from BGP |
| **Interconnect status** | `gcloud compute interconnects describe <IC>` | Physical circuit state |
| **Network Topology** | Cloud Console → Network Topology | Visual path tracing end-to-end |

### Useful Cloud Logging Query — BGP and VPN Events

```bash
gcloud logging read \
  'resource.type=("vpn_tunnel" OR "gce_router") AND
   (jsonPayload.message:"BGP" OR
    jsonPayload.message:"IKE" OR jsonPayload.message:"DPD")' \
  --freshness=1h \
  --limit=50 \
  --format="table(timestamp,resource.type,jsonPayload.message)"
```

---

## 6. Quick Fault Isolation Checklist

```text
HA VPN tunnel not establishing?
  └─ Check Phase 1 proposal: dhgrp must match (GCP default: 14)
  └─ Verify PSK matches per tunnel (Tunnel 1 and 2 have independent PSKs)
  └─ Check FortiGate can reach GCP gateway public IP (UDP 500/4500)
  └─ Review: diagnose vpn ike log-filter dst-addr4 <gcp-vpn-gw-ip>

BGP not establishing over tunnel?
  └─ Confirm tunnel is UP first
  └─ Check remote-as matches Cloud Router ASN (e.g. 65001)
  └─ Check BGP peer IP on FortiGate matches Cloud Router interface IP

BGP established but no GCP routes received?
  └─ Check Cloud Router custom advertisement config
  └─ Run: gcloud compute routers get-status <ROUTER> and check bgpPeerStatus
  └─ Verify VPC subnet routes are in the Cloud Router's advertisement list

Underlay Interconnect BGP flapping?
  └─ Check BFD: show bfd neighbors
  └─ Check interface errors: show interfaces <IC-subinterface>
  └─ Check VLAN attachment state: gcloud compute interconnects attachments describe

Asymmetric drops through firewall?
  └─ Confirm zone grouping: both tunnel VTIs in ZONE_GCP_VPN
  └─ Confirm loose RPF on both tunnel interfaces
  └─ Check session table: get system session list | grep <destination-ip>
```
