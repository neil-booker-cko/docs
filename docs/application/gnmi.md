# gNMI — gRPC Network Management Interface

gNMI (gRPC Network Management Interface, OpenConfig specification) provides a unified
interface for network device configuration, operational data retrieval, and streaming
telemetry. It uses gRPC (HTTP/2) with Protocol Buffers (proto3) for encoding. gNMI is
increasingly adopted by modern network vendors — Cisco IOS-XE, Arista EOS, Juniper
Junos, Nokia SR OS — as the preferred telemetry and configuration interface.

## Quick Reference

| Property | Value |
| --- | --- |
| **OSI Layer** | Layer 7 — Application |
| **Specification** | OpenConfig gNMI (github.com/openconfig/gnmi) |
| **Wireshark Filter** | `grpc` (payload is protobuf-encoded) |
| **TCP Port** | `9339` (IANA assigned for gNMI) |
| **Transport** | gRPC over HTTP/2; TLS mandatory |
| **Encoding** | proto3 (default), JSON_IETF, ASCII |

---

## gRPC Transport

gNMI messages are exchanged as gRPC unary or bidirectional streaming calls over
HTTP/2. TLS is mandatory. Mutual TLS (mTLS) is recommended so both the client and
the device authenticate each other with certificates.

### gNMI Service Definition

```protobuf
service gNMI {
  rpc Capabilities(CapabilityRequest) returns (CapabilityResponse);
  rpc Get(GetRequest)                 returns (GetResponse);
  rpc Set(SetRequest)                 returns (SetResponse);
  rpc Subscribe(stream SubscribeRequest) returns (stream SubscribeResponse);
}
```

---

## gNMI RPCs

### Capabilities

Discover the YANG models, encodings, and gNMI version supported by the device.
Always call `Capabilities` first to confirm model paths and available encodings.

### Get

Retrieve configuration or operational data at a specific path. Equivalent to
NETCONF `<get-config>` or `<get>`.

```text

GetRequest:
  path:     /interfaces/interface[name=GigabitEthernet0/0]/state/counters
  type:     STATE | CONFIG | OPERATIONAL | ALL
  encoding: JSON_IETF
```

### Set

Modify configuration. Supports `Update` (merge), `Replace` (full replace), and
`Delete` operations combined in a single atomic transaction.

```text

SetRequest:
  update:

    - path: /interfaces/interface[name=GigabitEthernet0/0]/config/description
      val:  "Uplink to Core"

      val:  "Uplink to Core"
```

### Subscribe

Streaming telemetry — the most important gNMI RPC. The client sends a
`SubscribeRequest` specifying paths and subscription mode; the server streams
`SubscribeResponse` updates.

---

## Subscription Modes

| Mode | Description |
| --- | --- |
| **STREAM / SAMPLE** | Server sends updates at a fixed interval (`sample_interval` in nanoseconds). |
| **STREAM / ON_CHANGE** | Server sends an update only when the value changes. More efficient for infrequently changing state. |
| **STREAM / TARGET_DEFINED** | Device chooses the most appropriate mode for each path. |
| **ONCE** | Single snapshot; the stream closes after delivering current state. |
| **POLL** | Client sends `Poll` messages; server responds with current state on each poll. |

### Subscribe Example (SAMPLE, every 10 seconds)

```json

{
  "subscribe": {
    "subscription": [
      {
        "path": "/interfaces/interface/state/counters",
        "mode": "SAMPLE",
        "sample_interval": 10000000000
      }
    ],
    "mode": "STREAM",
    "encoding": "JSON_IETF"
  }
}
```

---

## Path Structure

gNMI paths correspond to YANG container and list nodes. List keys are specified
in square brackets:

```text

/interfaces/interface[name=GigabitEthernet0/0]/state/in-octets

/network-instances/network-instance[name=default]
  /protocols/protocol[identifier=BGP][name=BGP]
  /bgp/neighbors/neighbor[neighbor-address=10.0.0.1]/state
```

A `prefix` can be set on a request to reduce repetition when subscribing to
multiple paths within the same YANG subtree.

---

## Telemetry Collection

Common open-source collection stack:

```text

Device (gNMI TCP 9339)
  → gnmic / telegraf (gNMI input plugin)
    → InfluxDB / Prometheus / OpenTSDB
      → Grafana
```

| Tool | Language | Notes |
| --- | --- | --- |
| `gnmic` | Go | Feature-rich CLI collector and gNMI client (openconfig/gnmic). |
| `telegraf` | Go | InfluxData collector; gNMI input plugin supports Subscribe. |
| `pygnmi` | Python | Lightweight Python gNMI client library. |
| `cisco-gnmi-python` | Python | Cisco's gNMI Python client with IOS-XE helpers. |

---

## Cisco IOS-XE Configuration

```ios

! Enable gNMI with TLS
gnxi
gnxi secure-server
gnxi secure-port 9339
gnxi secure-trustpoint <trustpoint-name>

! Verify
show gnxi state detail
```

---

## gNMI vs NETCONF

| Property | gNMI | NETCONF |
| --- | --- | --- |
| **Transport** | gRPC / HTTP/2 | SSH / TLS |
| **Encoding** | Protobuf, JSON_IETF | XML |
| **Streaming telemetry** | Native (Subscribe RPC) | Requires NETCONF notifications (limited) |
| **Transactional config** | Set is atomic; no candidate datastore | Candidate datastore, commit, rollback |
| **Best for** | Streaming telemetry, operational state | Transactional configuration management |
| **Model discovery** | Capabilities RPC | `ietf-yang-library` get |

---

## Notes

- gNMI requires TLS. Self-signed certificates are acceptable for lab use; production
  deployments should use a PKI with device certificates.

- Cisco IOS-XE gNMI support: 16.12+ for `Get` and `Subscribe`; 17.x for full `Set`
  support. Check `show gnxi state detail` for capability confirmation.

- `ON_CHANGE` subscription is more efficient than `SAMPLE` for infrequently changing
  state (BGP session status, interface admin state). `SAMPLE` is correct for counters
  and gauges.

- Not all paths support `ON_CHANGE` — use `Capabilities` or device documentation to
  confirm. Unsupported paths fall back to `TARGET_DEFINED` behaviour.

- FortiGate has limited native gNMI support; FortiOS primarily exposes REST and SNMP
  for telemetry. FortiManager may provide limited gNMI in newer releases.

- The `sample_interval` field is in nanoseconds: 10 s = `10000000000`.
