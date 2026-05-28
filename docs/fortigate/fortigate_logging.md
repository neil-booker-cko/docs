# FortiGate Logging Reference

FortiGate generates structured logs for every significant event — traffic sessions, security detections,
system changes, and VPN state transitions. Understanding the `type`, `subtype`, and `action` fields
is essential for building filters, triaging alerts, and writing SIEM correlation rules.

---

## At a Glance

| Field | Purpose | Where It Appears |
| --- | --- | --- |
| `type` | Top-level log category (traffic, event, utm, etc.) | Every log |
| `subtype` | Sub-category within the type | Every log |
| `action` | What FortiGate did — or what happened — to the session/event | Most logs |
| `logid` | Unique 10-digit identifier for the specific event within type/subtype | Every log |
| `policyid` | Firewall policy that matched (0 = no policy, implicit deny) | Traffic logs |
| `sessionid` | Tracks all log entries belonging to one TCP/UDP session | Traffic logs |

---

## Log Types and Subtypes

FortiGate organizes logs into five top-level types. Each type contains multiple subtypes.

### `type=traffic`

Records TCP/UDP/ICMP sessions handled by the firewall policy engine.

| Subtype | Description |
| --- | --- |
| `forward` | Traffic routed between interfaces (most common — LAN→WAN, branch→DC, etc.) |
| `local` | Traffic to/from the FortiGate itself (management, BGP, SNMP, syslog) |
| `multicast` | Multicast group traffic |
| `sniffer` | Packets captured by an interface in sniffer/tap mode |

### `type=event`

Records operational state changes: logins, VPN tunnels, routing changes, hardware events.

| Subtype | Description |
| --- | --- |
| `system` | CPU/memory thresholds, config changes, firmware events, HA failovers |
| `router` | BGP/OSPF neighbour state changes, route table events |
| `vpn` | IPsec phase1/phase2 tunnel up/down, IKE negotiation, DPD failures |
| `user` | Admin logins, captive portal auth, RADIUS/TACACS+ authentication |
| `endpoint` | FortiClient EMS registration, compliance posture changes |
| `wireless` | AP association, SSID events, rogue AP detection (managed APs only) |
| `ha` | HA cluster state changes, failover events, heartbeat failures |
| `compliance` | Security rating checks, compliance scan events |
| `wad` | Web application daemon events (proxy mode) |

### `type=utm`

Security inspection results from UTM profiles applied to traffic. A session can generate multiple
UTM log entries (one per engine that fired).

| Subtype | Description |
| --- | --- |
| `av` | Antivirus scan result — file blocked, quarantined, or passed |
| `webfilter` | Web category/URL filter decision |
| `ips` | Intrusion prevention signature match |
| `app-ctrl` | Application identified and action taken (e.g., BitTorrent blocked) |
| `emailfilter` | Spam/phishing detection for SMTP/IMAP/POP3 |
| `dlp` | Data loss prevention rule match |
| `anomaly` | Protocol anomaly or rate-based detection (DoS policy) |
| `voip` | SIP/H.323 session events |
| `icap` | External ICAP server response (content adaptation) |
| `waf` | Web application firewall rule match |
| `file-filter` | File type/extension filter match (separate from AV) |

### `type=dns`

DNS query and response logs (requires DNS filter or local DNS logging enabled).

| Subtype | Description |
| --- | --- |
| `dns-response` | DNS response logged (with resolution result and action) |
| `dns-query` | DNS query logged (less common; requires explicit config) |

### `type=ssh`

SSH deep-inspection tunnel events.

| Subtype | Description |
| --- | --- |
| `ssh` | SSH channel open/close, command logging |

---

## Traffic Log Actions

The `action` field on a `type=traffic` log is the most-queried field in operational troubleshooting.
Definitions from the FortiOS 7.6.6 log message reference.

| Action | Meaning | Common Cause |
| --- | --- | --- |
| `accept` | **Allowed forward session.** The standard action for forward traffic permitted by policy. Very common. | Any permitted session through the firewall (`subtype=forward`) |
| `close` | **Local-traffic session allowed.** Session to/from the FortiGate itself completed. | Management traffic, BGP, SNMP, NTP (`subtype=local`) |
| `deny` | **Session was denied** by policy. | Explicit deny rule, implicit deny, or no matching policy (`policyid=0`) |
| `timeout` | **Allowed session timed out** — idle timer expired with no FIN or RST. | No traffic for the session's timeout period (defaults: 3600s TCP, 60s UDP, 10s TCP half-open) |
| `client-rst` | **Session reset by client** — client sent TCP RST. | App closed socket abruptly, browser tab closed, client-side timeout |
| `server-rst` | **Session reset by server** — server sent TCP RST. | Server rejected connection, TLS mismatch, app-level refusal |
| `start` | **Session start log** — emitted when the session is first created. | Requires `set logtraffic-start enable` on the policy; always paired with a later end-of-session log |
| `dns` | **DNS query returned an error.** | DNS filter match, NXDOMAIN, or resolution failure |
| `ip-conn` | **Failed connection attempt.** | SYN with no SYN-ACK, half-open session, unreachable host |

### accept: session close and accept: session timeout

Two important sub-variants appear in the `msg` field of `action=accept` logs. They indicate
sessions that were permitted by policy but ended abnormally — distinguishable from normal traffic
by the `proto_state` field.

**accept: session close** — the session TTL (expire counter) counted down to zero while the
connection was idle. FortiGate transitions the session from ESTABLISHED to CLOSE_WAIT and
terminates it. Look for `proto_state=07` (CLOSE_WAIT).

**accept: session timeout** — an incomplete TCP handshake timed out. The client sent a SYN but
the server never replied with a SYN-ACK. FortiGate waits for `tcp-halfopen-timer` to expire before
closing the half-open session. Look for `proto_state=02` (SYN_SENT).

| `proto_state` value | TCP state | Meaning |
| --- | --- | --- |
| `01` | ESTABLISHED | Normal active session |
| `02` | SYN_SENT | Half-open — client sent SYN, no SYN-ACK received |
| `07` | CLOSE_WAIT | Session idle; TTL expired; FortiGate terminating |

These sub-variants are useful for distinguishing unreachable servers (`proto_state=02`) from
sessions that were established but abandoned without a clean close (`proto_state=07`).

---

## Event Log Actions

Event log actions describe state transitions rather than permit/deny decisions.

### VPN (`subtype=vpn`)

| Action | Meaning |
| --- | --- |
| `tunnel-up` | IPsec phase1 SA established; tunnel is operational |
| `tunnel-down` | IPsec phase1 SA torn down (manual, DPD, or idle timeout) |
| `negotiate` | Phase2 SA negotiation in progress |
| `negotiate-error` | Phase2 negotiation failed (mismatched proposals, auth failure) |
| `dpd-failure` | Dead Peer Detection timeout — remote end unreachable |
| `replay-error` | Anti-replay check failed on received packet |
| `error` | Generic IKE/IPsec error (check `msg` field for detail) |

### Router (`subtype=router`)

| Action | Meaning |
| --- | --- |
| `up` | BGP/OSPF neighbour established |
| `down` | BGP/OSPF neighbour dropped |
| `change` | Routing table entry added, removed, or modified |

### User (`subtype=user`)

| Action | Meaning |
| --- | --- |
| `login` | Successful admin or captive-portal login |
| `logout` | Session ended (timeout or explicit logout) |
| `failed` | Authentication failure (wrong password, RADIUS rejection) |
| `lock` | Account locked after repeated failures |

### System (`subtype=system`)

| Action | Meaning |
| --- | --- |
| `login` | Admin logged into GUI, CLI, or SSH |
| `logout` | Admin session ended |
| `modify` | Configuration change committed |
| `performance-statistics` | Periodic CPU/memory/session stats (generated every minute) |
| `ha-activity` | HA cluster role change (primary/secondary) |

---

## UTM Log Actions

UTM logs record what the security engine decided to do with the inspected content.

| Action | Meaning | Applies To |
| --- | --- | --- |
| `blocked` | Content matched a signature/category and was **blocked** | AV, webfilter, IPS, app-ctrl, DLP |
| `passthrough` | Matched but policy set to **monitor** — traffic allowed with a log | AV, webfilter, IPS, app-ctrl |
| `quarantined` | File sent to quarantine (FortiSandbox or local) | AV |
| `detected` | Threat found; action determined by profile (may also show as `blocked`) | IPS, anomaly |
| `reset` | Connection **reset** by UTM engine after inspection | IPS, webfilter (block with reset) |
| `dropped` | Packet dropped by the UTM engine (no RST) | IPS, anomaly |
| `monitored` | Informational detection; no blocking action taken | app-ctrl in monitor mode |
| `exempt` | Traffic was exempted from inspection by an override/exemption list | AV, webfilter |
| `close` | Inspected session ended normally | webfilter, app-ctrl |

---

## Key Log Fields Reference

Beyond `type`, `subtype`, and `action`, these fields appear frequently in filters and SIEM rules.

| Field | Description | Example |
| --- | --- | --- |
| `logid` | 10-digit unique event ID (first 4 digits = category) | `0000000013` (traffic forward close) |
| `level` | Syslog severity: `emergency`, `alert`, `critical`, `error`, `warning`, `notice`, `information`, `debug` | `notice` |
| `vd` | VDOM name the log originated from | `root` |
| `policyid` | Matched firewall policy ID (0 = implicit deny) | `42` |
| `sessionid` | Session handle — links start/close/UTM entries for one flow | `1234567890` |
| `srcip` / `dstip` | Source and destination IP | `10.0.1.10`, `8.8.8.8` |
| `srcport` / `dstport` | Source and destination port | `54321`, `443` |
| `proto` | IP protocol number | `6` (TCP), `17` (UDP), `1` (ICMP) |
| `service` | Resolved service name | `HTTPS`, `DNS`, `custom-tcp-8080` |
| `sentbyte` / `rcvdbyte` | Bytes sent/received for the session | `4096`, `123456` |
| `duration` | Session duration in seconds | `300` |
| `msg` | Human-readable description (most useful for event logs) | `Phase 1 IKE SA established` |
| `appid` / `app` | Application identified by app-ctrl engine | `19265`, `HTTPS.BROWSER` |
| `catdesc` | Web filter category description | `Information Technology` |
| `crscore` / `craction` | IPS threat score and action | `50`, `block` |
| `virus` | Virus/malware name from AV engine | `EICAR_TEST_FILE` |
| `url` | URL inspected by webfilter | `https://example.com/path` |

---

## LogID Ranges

The first four digits of a `logid` identify the log category. Useful for writing syslog filters.

| LogID Prefix | Category |
| --- | --- |
| `0000` | Traffic (forward, local, sniffer) |
| `0100` | Event — system |
| `0101` | Event — router |
| `0102` | Event — VPN |
| `0103` | Event — user |
| `0104` | Event — HA |
| `0200` | UTM — antivirus |
| `0201` | UTM — webfilter |
| `0204` | UTM — IPS |
| `0206` | UTM — anomaly |
| `0209` | UTM — app-ctrl |
| `0317` | UTM — DNS filter |

---

## Example Log Entries

**Traffic — normal HTTPS session closed by FIN:**

```text
date=2026-05-28 time=14:22:01 devname=ELD7-FGT-01 logid=0000000013 type=traffic subtype=forward
level=notice vd=root action=close policyid=10 srcip=10.0.1.50 srcport=54321 dstip=1.2.3.4
dstport=443 proto=6 service=HTTPS duration=42 sentbyte=8192 rcvdbyte=204800 msg="traffic forward"
```

**Traffic — blocked by implicit deny:**

```text
date=2026-05-28 time=14:23:15 devname=ELD7-FGT-01 logid=0000000020 type=traffic subtype=forward
level=notice vd=root action=deny policyid=0 srcip=10.0.1.51 srcport=12345 dstip=10.99.0.1
dstport=22 proto=6 service=SSH msg="iprope_in_check() check failed, drop"
```

**Event — IPsec tunnel up:**

```text
date=2026-05-28 time=14:25:00 devname=ELD7-FGT-01 logid=0102024576 type=event subtype=vpn
level=notice vd=root action=tunnel-up tunneltype=ipsec tunnelid=2001 remip=203.0.113.10
msg="IPsec phase 1 tunnel established."
```

**UTM — IPS signature blocked:**

```text
date=2026-05-28 time=14:30:55 devname=ELD7-FGT-01 logid=0419016384 type=utm subtype=ips
level=alert vd=root action=blocked sessionid=9988776 srcip=10.0.1.52 dstip=10.0.2.100
proto=6 service=HTTP attack="MS.Windows.SMB.CVE-2017-0143" severity=critical craction=block
```

---

## Notes / Gotchas

- **`deny` vs `policyid=0`:** A `deny` log with `policyid=0` means the traffic hit the implicit
  deny at the bottom of the policy table — there was no explicit deny rule. Check if a missing
  policy is the cause before adding block rules.
- **`accept` is the normal action for permitted forward traffic** — it is not a rare or special
  condition. `close` is specifically for local-traffic sessions (traffic to/from the FortiGate
  itself, such as management, BGP, or syslog). If you're seeing lots of `accept`, that is expected.
- **Missing end-of-session log:** If you see `start` but no matching end log, either the session
  is still active or it was reset — check for `client-rst` or `server-rst` with the same
  `sessionid`.
- **UTM log without traffic log:** UTM logs always have a matching traffic log in the same session.
  If you can only see UTM entries, the traffic log filter may be set to `utm` (log only security
  events) rather than `all`.
- **`client-rst`/`server-rst` do not always mean a firewall block:** These identify which endpoint
  sent the RST. Cross-reference UTM logs to determine whether a security profile triggered the
  reset rather than the endpoint.
- **Performance statistics spam:** `subtype=system action=performance-statistics` logs fire every
  minute and can dominate disk usage. Filter these out in syslog forwarding rules if they are not
  needed for monitoring.
- **VDOM source:** All logs include a `vd` field. In multi-VDOM deployments, always filter by
  `vd` before drawing conclusions from log volume or action counts.

---

## See Also

- [Firewall Policies & Access Control](fortigate_firewall_policies.md)
- [Syslog & Monitoring Standards](../checkout-standards/syslog-monitoring-standards.md)
- [Security Hardening](../operations/security_hardening.md)
- [Third-Party VPN](fortigate_third_party_vpn.md)
