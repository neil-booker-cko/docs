# FortiGate Troubleshooting

Common FortiGate issues affecting routing, connectivity, policies, and high availability with
diagnostic commands and remediation steps. Applies to FortiOS deployments on FortiGate firewalls.

---

## Quick Diagnosis

| Symptom | Likely Cause | First Check |
| --- | --- | --- |
| **Traffic not flowing** | Firewall policy blocking; wrong interface in policy | Check firewall log; verify policy source/dest/service |
| **Asymmetric routing** | Return path takes different gateway; not in routing table | Check routing table; verify both directions |
| **BGP not learning routes** | BGP not running; neighbor not up; AS mismatch | Check BGP status; verify neighbor IP/AS |
| **HA failover not working** | HA not synchronized; heartbeat link down; priority issue | Check HA sync status; verify heartbeat interface |
| **IPsec tunnel down** | Phase 1 failure; pre-shared key mismatch; crypto mismatch | Check tunnel status; review IKE logs; verify pre-shared key |
| **DNS not resolving** | DNS server unreachable; DNS firewall policy blocking; cache stale | Check DNS configuration; verify server reachability |
| **VPN client can't connect** | VPN service not running; SSL cert issue; auth failure | Check VPN service status; verify certificate; check RADIUS |
| **Performance degradation** | CPU/memory high; traffic exceeding interface capacity; DPI overhead | Check system resources; monitor interface utilization |

---

## Firewall Policy and Traffic Flow

### Symptom: "Traffic Blocked by Firewall"

#### Check 1: Verify policy exists and matches traffic

```fortios
! FortiGate
get firewall policy
! Lists all firewall policies; verify source, destination, service match

get firewall policy <policy-id>
! Shows detailed policy configuration

! Look for:
! - Source interface: matches ingress interface
! - Source address: matches source IP
! - Destination: matches destination IP
! - Service: matches application port/protocol
! - Action: "accept" (not "deny")
! - Schedule: enabled/active
```

#### Check 2: Review traffic in firewall log

```fortios
! Enable real-time log view during traffic attempt:
execute tail -f var/log/firewall
! Filter for matching traffic:
! Src: <client-ip>, Dst: <destination-ip>, Service: <port>
! Shows "blocked" or "accepted"
```

#### Check 3: Verify policy not disabled

```fortios
! Check if policy is disabled:
get firewall policy <policy-id> | grep status
! If "status: disable", enable it:
config firewall policy
  edit <policy-id>
    set status enable
  next
end
```

### Symptom: "Asymmetric Routing" (One-Way Communication)

**Cause:** Outbound traffic takes one path (via Policy A), return traffic takes different path (via
Policy B) due to different routing or policy configuration.

**Diagnosis:**

```fortios
! Trace outbound path:
diagnose firewall iproutetable list | grep <destination-ip>
! Shows which gateway the destination matches

! Check return path from destination:
! From external device, determine which gateway response goes through
! May require logging at both ends

! In firewall log, look for asymmetry:
! Outbound: Src=internal, Dst=external, Egress=port1
! Return: Src=external, Dst=internal, Ingress=port2
```

**Remediation:**

1. Verify routing table has bidirectional paths:

```fortios
get router static
! Both directions should have explicit routes or default route
```

1. Use PBR (Policy-Based Routing) to force symmetric paths:

```fortios
config router policy
  edit 1
    set src "internal-subnet"
    set dst "external-destination"
    set gateway <specific-gateway-ip>
  next
end
```

---

## Routing Issues

### Symptom: "Routes Not Appearing in Routing Table"

#### Check 1: Verify routing protocol running

```fortios
get router info routing-table all
! Lists all routes from all sources (static, BGP, OSPF, etc.)

get router ospf status  ! If using OSPF
get router bgp status   ! If using BGP
```

#### Check 2: Verify BGP neighbors up

```fortios
get router bgp neighbor
! Shows neighbor IP, AS, state
! Should show "established" for each neighbor

! If not established, check:
! - BGP service started
! - Local AS number correct
! - Neighbor IP reachable
! - Pre-shared key if authentication enabled
```

#### Check 3: Verify route is advertised

```fortios
! Check BGP advertisement from this router:
diagnose router bgp summary
! Shows outbound and inbound routes

! On neighbor, verify route received:
! SSH to neighbor and check routing table
```

#### Check 4: Check for routing filters

```fortios
! Filters may be blocking routes:
get router prefix-list
get route-map
! Verify no deny rules blocking the route
```

### Symptom: "BGP Flapping" (Route Appearing/Disappearing)

**Cause:** BGP route becomes unavailable (metric change, neighbor down), re-converges, becomes
available again.

```fortios
execute diagnose debug bgp all  ! Verbose BGP debugging
! Monitor for route withdrawals and re-announcements
! Press Ctrl+C to stop
```

**Remediation:**

1. Stabilize BGP metrics (avoid changing costs continuously)

1. Enable BFD on BGP link:

```fortios
config router bgp
  edit <AS>
    config neighbor
      edit <neighbor-ip>
        set bfd enable
      next
    end
  next
end
```

1. Check for routing instability upstream (if route flapping from neighbor's direction).

---

## High Availability (HA) Issues

### Symptom: "HA Not Failover" (Backup Doesn't Take Over After Primary Fails)

#### Check 1: Verify HA enabled and synchronized

```fortios
get system ha status
! Shows:
! - HA Mode: Active-Passive (most common)
! - Sync Status: "in-sync" (both devices synchronized)
! - Primary: <device-name>
! - Secondary: <device-name>
```

#### Check 2: Verify heartbeat link up

HA requires a heartbeat link (often dedicated port) for synchronization:

```fortios
get system ha | grep heartbeat
! Shows heartbeat interface and status

! If heartbeat down, check physical link:
get interface <interface>
! Should show "link up" and "status: up"
```

#### Check 3: Verify priority correct

```fortios
get system ha | grep priority
! Higher priority = preferred primary
! If secondary has HIGHER priority, it becomes primary

! Set correct priority:
config system ha
  set priority 200  ! Primary (higher)
  ! or
  set priority 100  ! Secondary (lower)
end
```

#### Check 4: Check HA sync in logs

```fortios
execute tail -f var/log/ha
! Look for "sync OK" or "out of sync" messages
! If out of sync: check disk space, CPU, configuration differences
```

### Symptom: "HA Synchronization Stuck"

**Cause:** Configuration changes don't sync to secondary; only primary updated.

```fortios
! Force sync from primary:
execute ha push-config
! Pushes current primary config to secondary

! Verify secondary has same config:
! SSH to secondary and compare settings
```

**Note:** Some changes (license, system settings) don't sync automatically. Manual sync required.

---

## IPsec VPN Issues

### Symptom: "IPsec Tunnel Down"

#### Check 1: Verify tunnel status

```fortios
get vpn ipsec tunnel name <tunnel-name>
! Shows tunnel state (up/down), IKE version, encryption

get vpn ipsec stats
! Shows tunnel statistics
```

#### Check 2: Check Phase 1 (IKE) status

```fortios
diagnose vpn ike log
! Shows IKE negotiation logs; reveals where handshake fails

! Common failures:
! - NO_PROPOSAL_CHOSEN: encryption/auth mismatch
! - AUTH_FAILED: pre-shared key mismatch
! - INVALID_IKE_SPI: duplicate tunnel, wrong remote IP
```

#### Check 3: Verify pre-shared key

```fortios
get vpn ipsec phase1-interface <interface>
! Pre-shared key shown encrypted (for security)
! Verify with remote peer — keys must match exactly
```

#### Check 4: Check encryption algorithm mismatch

```fortios
get vpn ipsec phase1-interface <interface> | grep -E "encryption|authentication"
! Local config shows algorithms

! Remote peer must match:
! - Encryption: AES-128/256, DES, 3DES
! - Authentication: MD5, SHA1, SHA256
! - DH Group: 1, 2, 5, 14, 15, 16, etc.
```

#### Check 5: Verify network connectivity to remote peer

```bash
diagnose debug icmp trace <remote-peer-ip> count 3
! Should get responses from remote peer's IP
! If unreachable: routing broken before IPsec can work
```

### Symptom: "IPsec Tunnel Up But No Traffic Flowing"

**Cause:** Phase 1 (IKE) successful but Phase 2 (IPsec) negotiation failing or policies not
matching.

#### Check 1: Verify Phase 2 policy

```fortios
get vpn ipsec phase2-interface <interface>
! Shows encryption, authentication, PFS settings for data traffic

! Both ends must match:
! - Encryption algorithm
! - Authentication algorithm
! - PFS (Perfect Forward Secrecy): enabled/disabled on both
```

#### Check 2: Check firewall policy allows tunnel traffic

```fortios
get firewall policy
! Must have policy allowing traffic through tunnel interface
! Source: local subnet, Destination: remote subnet
! Interface: tunnel interface
! Action: accept
```

#### Check 3: Verify route to remote subnet

```fortios
diagnose firewall iproutetable list | grep <remote-subnet>
! Should show route via tunnel interface or gateway
```

---

## Interface and Connectivity Issues

### Symptom: "Interface Down or Flapping"

#### Check 1: Check physical status

```fortios
get interface <interface>
! Look for:
! - "link: up" (physical link OK)
! - "status: up" (interface operational)
! - Speed/duplex settings correct
```

#### Check 2: Verify IP configuration

```fortios
get interface | grep -A5 <interface>
! Verify:
! - IP address assigned
! - Netmask correct
! - No IP conflicts
```

#### Check 3: Check for port flapping

```fortios
get interface <interface>
! Look at "RX/TX packets" and "errors"
! High error rate = physical layer issue (cable, transceiver, switch port)
```

#### Check 4: Verify MTU not causing issues

```fortios
get interface <interface> | grep mtu
! Default 1500; if lower, may fragment large packets
! Tunnel interfaces often need lower MTU (1436 for GRE/IPsec overhead)
```

---

## DNS and Name Resolution

### Symptom: "DNS Not Resolving"

#### Check 1: Verify DNS servers configured

```fortios
get system dns
! Shows primary and secondary DNS servers
! Verify IP addresses correct
```

#### Check 2: Test DNS server reachability

```bash
execute ping <dns-server-ip>
! Should get responses
```

#### Check 3: Test name resolution

```bash
execute nslookup example.com <dns-server-ip>
! Should resolve to IP address
! If fails: DNS server unreachable or misconfigured
```

#### Check 4: Check firewall policy allows DNS

```fortios
get firewall policy
! Must allow traffic to DNS server (UDP 53)
! From internal interface to DNS interface
```

#### Check 5: Flush DNS cache

```fortios
execute flush system dns-cache
! Clear cached DNS entries
! Useful if DNS server changed IP recently
```

---

## System Performance and Resources

### Symptom: "Slow Performance or High CPU/Memory"

#### Check 1: Monitor system resources

```fortios
get system performance status
! Shows:
! - CPU: percentage used (should be <80% under normal load)
! - Memory: percentage used
! - Network throughput
! - IPS/AV activity
```

#### Check 2: Identify heavy processes

```fortios
execute top
! Shows CPU usage by process
! "ips" or "av" processes often CPU-heavy if scanning enabled
! "httpsd" (management interface) or "sslvpnd" (SSL VPN) if high connections
```

#### Check 3: Check interface utilization

```fortios
get interface <interface>
! Look at RX/TX rates
! If approaching interface speed limit, upgrade link or add load balancing
```

#### Check 4: Disable unnecessary features

If CPU high, consider:

- Disabling IPS scanning on low-traffic policies

- Disabling antivirus if not needed

- Reducing logging verbosity

- Upgrading to higher capacity device

```fortios
config firewall policy
  edit <policy>
    set ips-sensor ""  ! Disable IPS
    set av-profile ""  ! Disable antivirus
  next
end
```

---

## Best Practices for FortiGate Troubleshooting

| Practice | Reason |
| --- | --- |
| **Check firewall logs first** | Most issues visible in logs; fastest diagnosis |
| **Verify bidirectional connectivity** | Check both directions; asymmetric issues common |
| **Enable debug sparingly** | High overhead; disable after capturing logs |
| **Document baseline performance** | Know normal CPU/memory for comparison |
| **Monitor HA sync status regularly** | Prevents failover surprises |
| **Test failover periodically** | Ensure secondary truly takes over if primary fails |
| **Review BGP/OSPF logs** | Routing issues often preceded by neighbor flaps |
| **Update FortiOS regularly** | Security and stability patches important |

---

## Notes / Gotchas

- **Firewall Policy Order Matters:** Policies evaluated top-to-bottom; first match wins. More
  specific policies should be higher priority (above general policies).

- **Interface Naming:** Exact interface names required in policies. "port1" is not "port 1".
  Use `get interface` to confirm spelling.

- **Pre-Shared Key Whitespace:** Extra spaces in pre-shared key break authentication silently.
  Verify exact key with remote peer; no leading/trailing spaces.

- **HA Licenses:** Both devices in HA must have same license level. Mismatched licensing can
  cause sync issues.

- **MTU on Tunnels:** IPsec/GRE tunnels reduce available MTU for encapsulated traffic. Set lower
  MTU or allow fragmentation to prevent silent packet loss.

- **Debug Output Verbose:** `execute diagnose debug` produces lots of output; use grep to filter
  to relevant traffic (e.g., source IP, protocol).

---

## See Also

- [FortiGate BGP Configuration](../cisco/fortigate_bgp_config.md)

- [FortiGate SD-WAN Configuration](../fortigate/fortigate_sdwan.md)

- [IPsec & IKE Theory](../theory/ipsec.md)

- [BGP Troubleshooting](bgp_troubleshooting.md)

- [OSPF Troubleshooting](ospf_troubleshooting.md)
