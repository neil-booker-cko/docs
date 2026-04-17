# Syslog

Syslog is a standard for forwarding log messages across an IP network. It is used
universally by network devices, servers, and applications to send structured event
data to a central collector. Two formats are in use: the legacy BSD format (RFC 3164)
and the current structured format (RFC 5424).

## Quick Reference

| Property | Value |
| --- | --- |
| **OSI Layer** | Layer 7 — Application |
| **TCP/IP Layer** | Application |
| **RFC** | RFC 5424 (current), RFC 3164 (legacy BSD) |
| **Wireshark Filter** | `syslog` |
| **Transport** | UDP `514` (traditional), TCP `601` (reliable, RFC 3195), TCP `6514` (TLS) |

## Message Format (RFC 5424)

RFC 5424 messages are UTF-8 text with a defined structure:

```text
<PRI>VERSION TIMESTAMP HOSTNAME APP-NAME PROCID MSGID STRUCTURED-DATA MSG
```

**Example:**

```text

<165>1 2026-04-02T10:23:15.123Z router01 bgpd 1234 BGP-PEER
  [exampleSDID@32473 peer="10.0.0.1"] BGP peer 10.0.0.1 state changed to Established
```

## PRI Field

The PRI value encodes both the **Facility** and **Severity**:

```text

PRI = (Facility × 8) + Severity
```

The value is wrapped in angle brackets: `<165>` = Facility 20 (local4) × 8 +
Severity 5 (Notice).

## Header Fields

| Field | Description |
| --- | --- |
| **PRI** | Priority value: `<` + (Facility × 8 + Severity) + `>`. Range 0–191. |
| **VERSION** | Syslog protocol version. Always `1` for RFC 5424. Absent in RFC 3164. |
| **TIMESTAMP** | RFC 3339 timestamp (e.g. `2026-04-02T10:23:15.123Z`). RFC 3164 uses a shorter format (`Apr  2 10:23:15`). |
| **HOSTNAME** | FQDN, IP address, or hostname of the originating device. `-` if unknown. |
| **APP-NAME** | Name of the application or process generating the message. `-` if unknown. |
| **PROCID** | Process ID or similar identifier. `-` if not applicable. |
| **MSGID** | Message type identifier for filtering. `-` if not applicable. |
| **STRUCTURED-DATA** | Zero or more `[SD-ID param="value"]` elements providing structured key-value data. `-` if absent. |
| **MSG** | Free-form log message. Separated from STRUCTURED-DATA by a space. |

## Facility Values

| Value | Facility |
| --- | --- |
| `0` | Kernel messages |
| `1` | User-level messages |
| `2` | Mail system |
| `3` | System daemons |
| `4` | Security / authorisation |
| `5` | Syslog daemon internal |
| `6` | Line printer subsystem |
| `9` | Clock daemon |
| `10` | Security / authorisation |
| `11` | FTP daemon |
| `12` | NTP subsystem |
| `16–23` | Local use (`local0`–`local7`) — commonly used by network devices |

## Severity Values

| Value | Severity | Meaning |
| --- | --- | --- |
| `0` | Emergency | System is unusable |
| `1` | Alert | Immediate action required |
| `2` | Critical | Critical condition |
| `3` | Error | Error condition |
| `4` | Warning | Warning condition |
| `5` | Notice | Normal but significant |
| `6` | Informational | Informational message |
| `7` | Debug | Debug-level message |

## RFC 3164 vs RFC 5424

| Feature | RFC 3164 (Legacy) | RFC 5424 (Current) |
| --- | --- | --- |
| Timestamp format | `Mmm DD HH:MM:SS` (no year, no timezone) | RFC 3339 with timezone |
| Structured data | No | Yes (`[SD-ID key="value"]`) |
| Unicode support | No | Yes (UTF-8 with BOM) |
| Message length | 1024 bytes max | Unlimited (transport-dependent) |
| Version field | Absent | `1` |

## Notes

- **Cisco IOS** uses local0–local7 (`16`–`23`) by default. Most network vendors map

  their log levels to the 0–7 severity scale with vendor-specific facility mappings.

- **UDP transport** is fire-and-forget — messages can be lost under load or on a

  lossy path. For critical infrastructure logs, TCP or TLS (RFC 5425) should be used.

- **TLS (RFC 5425)** over TCP port `6514` provides both reliability and

  confidentiality — important when logs traverse untrusted networks.

- **RELP** (Reliable Event Logging Protocol) is a common alternative to TCP syslog,

  adding application-layer acknowledgement to prevent message loss.
