# BGP Stack Analysis: VPN Overlay over DX Transit VIF

## 1. Overview & Principles

This architecture utilizes a layered protocol approach to provide encrypted,
high-bandwidth
connectivity to AWS. The Cisco IOS-XE handles the physical path (Direct Connect),
while the FortiGate manages the security layer (IPsec).

### The "Protocol Stack"

The design consists of a recursive routing model:

- **Data Plane:** Traffic is encapsulated in an IPsec tunnel.
- **Overlay BGP:** FortiGate to TGW sessions running inside the tunnel.
- **Underlay BGP:** Cisco to AWS Transit VIF sessions carrying the IPsec transport.

### Deterministic Failover Logic

Since AWS **does not support BFD over VPN**, we must rely on a hierarchy of timers:

- **Underlay (Cisco):** Uses BFD (300ms x 3) to ensure that if a DX fiber cut occurs,

    the transport path shifts in <1s.

- **Overlay (FortiGate):** Uses aggressive Dead Peer Detection (DPD) and BGP Next-Hop

    Tracking. By linking BGP to the VTI status via `link-down-failover`, we ensure
    that routes are withdrawn the moment the tunnel path is declared dead by DPD,
    rather than waiting for the BGP hold-timer.

## 2. Detection & Restoration Timelines

### Underlay Failure (DX Fiber Cut)

```mermaid
timeline
    title Failure Scenario: Underlay DX Failover
    section Underlay (Cisco DX)
        T=0ms : Primary DX Failure
        T=900ms : BFD Detects Failure : Cisco Switches IPsec traffic to Secondary DX
    section Overlay (FortiGate VPN)
        T=0ms-900ms : Brief packet loss during switch
        T=950ms : Path Restored : IPsec Tunnel stays UP : NO OVERLAY BGP FLAP
```

### Overlay Failure (Silent Path Loss)

```mermaid

timeline
    title Failure Scenario: VPN Path Failure (No BFD)
    section Optimized Timers
        T=0s : VPN Path Fails (TGW side)
        T=15s : DPD Retries Exhausted (5s x 3) : VTI Interface Down
        T=16s : Link-Down Failover triggers : BGP Session Killed : Routes Dropped
```

## 3. Configuration

### A. Cisco IOS-XE (Underlay - Modern Address-Family)

```ios

bfd-template single-hop AWS-DX-BFD
 interval min-tx 300 min-rx 300 multiplier 3
 no bfd echo
!
router bgp 65000
 bgp router-id 10.0.0.1
 bgp log-neighbor-changes
 !
 address-family ipv4 vrf AWS
  neighbor 169.254.x.2 remote-as 64512
  neighbor 169.254.x.2 description AWS-TGW-DX
  neighbor 169.254.x.2 fall-over bfd
  neighbor 169.254.x.2 activate
  neighbor 169.254.x.2 send-community both
  neighbor 169.254.x.2 route-map RM-DX-PRIMARY-IN in
  neighbor 169.254.x.2 route-map RM-DX-PRIMARY-OUT out
 exit-address-family
!
```

> VRF `AWS` must be defined and the DX interface assigned to it before this config is
> applied. See the [VRF-Lite config guide](../cisco/cisco_vrf_config.md) for VRF
> definitions and FortiGate subinterface requirements.

### B. FortiGate Overlay (Phase 1 & BGP Neighbors)

BFD is not supported on the VPN overlay. DPD with `link-down-failover` provides
fast failure detection. AWS TGW BGP timers are fixed at **10s keepalive / 30s
hold** — configure the FortiGate to match.

```fortios

config vpn ipsec phase1-interface
    edit "vpn-071eda31a-0"
        set interface "bond0.601"
        set npu-offload enable # Critical for offloading encryption/jitter
        set dpd on-idle
        set dpd-retryinterval 5
        set dpd-retrycount 3
        set proposal aes256-sha256
        set dhgrp 19
        set remote-gw 10.200.3.62
    next
end

config router bgp
    set graceful-restart enable
    set graceful-restart-time 120 # Standardized for AWS maintenance
    config neighbor
        edit "169.254.157.253"
            set description "PRIMARY-TGW-TUNNEL"
            set link-down-failover enable # Trigger withdrawal on VTI down
            set timers-keepalive 10
            set timers-holdtime 30
            set capability-graceful-restart enable
            set route-map-in "INBOUND-AWS-PRI"
            set route-map-out "OUTBOUND-AWS-PRI"
        next
    end
end
```

## 4. Comparison Summary

| Metric | Default Settings | Optimized BGP Stack |
| :--- | :--- | :--- |
| **Underlay Detection** | 180 Seconds | **900ms (BFD)** |
| **Overlay Detection** | 30 Seconds (BGP hold-timer) | **15 Seconds (DPD 5s × 3 + link-down-failover)** |
| **BGP Link Reaction** | Passive | **Active (Link-Down Failover)** |
| **Security Standard** | None | **AES-256 / DH-21** |
| **NPU Offload** | Disabled | **Enabled (Encryption acceleration)** |

## 5. Verification & Troubleshooting

| Command | Platform | Purpose |
| :--- | :--- | :--- |
| `show bfd neighbors` | Cisco | Verify Cisco Underlay BFD session health. |
| `show bgp vpnv4 unicast vrf AWS summary` | Cisco | BGP neighbour state in VRF AWS |
| `show bgp vpnv4 unicast vrf AWS neighbors 169.254.x.2` | Cisco | Full BGP detail for TGW peer |
| `show ip route vrf AWS` | Cisco | Routing table for VRF AWS |
| `get router info bgp neighbors 169.254.y.y` | FortiGate | Confirm holdtime 30s, keepalive 10s, and failover status. |
| `diagnose vpn tunnel list name <tunnel-name>` | FortiGate | Monitor DPD retry counters. |
| `get router info bgp neighbors` | FortiGate | Verify Community tagging (7224:7300) for path steering. |
| `diagnose sniffer packet any 'port 179' 4` | FortiGate | Verify 10s BGP keepalives on the wire. |
