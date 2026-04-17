# Troubleshooting Guide: VPN & BGP Log Signatures

When a VPN fails "silently," the FortiGate logs contain specific sequences that
reveal whether the root cause was a network interruption, a configuration mismatch,
or a peer timeout.

## 1. The "DPD Timeout" Signature

**Scenario:** The tunnel was up, but heartbeats stopped receiving a response.

- **Log Message:** `IPsec phase 1 dead peer detection`
- **Log Detail:** `dpd-failure` or `detect-timeout`
- **Tell-tale Sign:** Look for the "detect/retry" sequence. If you see the log entry

    followed immediately by the tunnel tearing down, the FortiGate sent its 3 retries
    (based on your 5s x 3 config) and got no answer.

- **Root Cause:** Usually a "Gray Failure" in the path (packet loss on the DX or

    ISP) or the remote peer (AWS TGW) becoming unresponsive.

## 2. The "BGP Hold Timer" Signature

**Scenario:** The IPsec tunnel stayed up, but the routing session died.

- **Log Message:** `BGP neighbor status changed`
- **Log Detail:** `state=Established->Idle`, `reason=Hold Timer Expired`
- **Tell-tale Sign:** If the VPN tunnel logs show no "Down" event, but BGP shows

    a timeout, the encrypted path is technically "Up" but failing to pass BGP Keepalives
    (TCP 179).

- **Root Cause:** MTU/Fragmentation issues (BGP updates are too large for the tunnel)

    or a firewall policy/ACL blocking TCP 179.

## 3. The "Link-Down Failover" Signature

**Scenario:** BGP was killed because the interface went down.

- **Log Message:** `BGP neighbor status changed`
- **Log Detail:** `reason=Interface Down`
- **Tell-tale Sign:** You will see a `tunnel-down` log for the VTI followed within

    milliseconds by the BGP `Idle` log.

- **Root Cause:** This confirms your `link-down-failover` setting is working correctly.

    The outage was triggered by the VPN layer, not a BGP timer issue.

## 4. The "IKE Re-key" Signature

**Scenario:** The tunnel drops every ~8 hours or ~1 hour.

- **Log Message:** `IPsec phase 1 SA deleted` / `IPsec phase 1 SA established`
- **Log Detail:** `reason=rekey`
- **Tell-tale Sign:** If the outage coincides with a re-key log, the two sides failed

    to agree on the new security parameters before the old ones expired.

- **Root Cause:** Phase 1/2 proposal mismatches (especially DH Group or Keylife)

    or "Strict Re-key" being enabled on one side but not the other.

## 5. Historical Troubleshooting Commands

Run these via CLI to see the history of the sessions:

| Command | Purpose |
| :--- | :--- |
| `get router info bgp neighbors  &#124; grep -A 5 "Datagrams"` | See if BGP is failing to send or receive packets. |
| `get vpn ipsec tunnel details` | Check the `Success/Failure` count for DPD heartbeats. |
| `diagnose vpn ike log-filter dst-addr4` | Filter debug logs for a specific tunnel. |
| `execute log filter category 4` | Filter for VPN events. |
| `execute log display` | View the most recent filtered log entries. |

## 6. Correlating with AWS

Always check the **AWS CloudWatch Metrics** for the VPN connection:

- **TunnelState:** Did AWS see the tunnel go down at the same time?
- **TunnelDataIn / TunnelDataOut:** Was there a one-way traffic drop (Asymmetry)?
- **BGPStatus:** Did the TGW see the BGP session drop before or after the tunnel?
