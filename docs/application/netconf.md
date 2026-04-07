# NETCONF and RESTCONF — Network Configuration Protocols

NETCONF (RFC 6241) provides a standardised XML-based protocol for installing,
manipulating, and deleting network device configuration. It uses a transactional
model with candidate, running, and startup datastores and explicit commit operations.
RESTCONF (RFC 8040) exposes the same YANG data models over a RESTful HTTP API,
allowing easier programmatic access. Both protocols use YANG (RFC 7950) data models
to describe device capabilities and data structures.

## Quick Reference

| Property | Value |
| --- | --- |
| **OSI Layer** | Layer 7 — Application |
| **RFC** | RFC 6241 (NETCONF), RFC 8040 (RESTCONF), RFC 7950 (YANG) |
| **Wireshark Filter** | `ssh` (NETCONF over SSH) |
| **TCP Port (NETCONF)** | `830` (SSH subsystem `netconf`) |
| **TCP Port (RESTCONF)** | `443` / `8443` (HTTPS; no fixed IANA port) |

---

## NETCONF

### Transport and Framing

NETCONF runs over SSHv2 (mandatory) using the `netconf` SSH subsystem. TLS transport
is also defined (RFC 7589). Messages are framed using chunked encoding (RFC 6242,
mandatory for NETCONF 1.1):

```text
\n##<length>\n
<xml message>
\n##\n
```

The legacy end-of-message delimiter `]]>]]>` is used for NETCONF 1.0 only.

### Protocol Layers

| Layer | Description |
| --- | --- |
| **Content** | YANG data models defining configuration and operational data. |
| **Operations** | RPC calls: `get`, `get-config`, `edit-config`, `copy-config`, `delete-config`, `lock`, `unlock`, `commit`, `discard-changes`, `validate`, `close-session`, `kill-session`. |
| **Messages** | `<rpc>` / `<rpc-reply>` / `<notification>` wrapped in XML. |
| **Secure Transport** | SSH (mandatory) or TLS. |

### Datastores

| Datastore | Description |
| --- | --- |
| **running** | Currently active configuration. Always present. |
| **candidate** | Edit workspace. Changes are not applied until `<commit>`. Requires `:candidate` capability. |
| **startup** | Configuration loaded at boot. Requires `:startup` capability. |

### Session Establishment

On connect, both peers exchange `<hello>` messages advertising capabilities:

```xml
<!-- Server hello -->
<hello xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <capabilities>
    <capability>urn:ietf:params:netconf:base:1.1</capability>
    <capability>urn:ietf:params:netconf:capability:candidate:1.0</capability>
    <capability>urn:ietf:params:netconf:capability:validate:1.1</capability>
  </capabilities>
  <session-id>42</session-id>
</hello>
```

### get-config

```xml
<rpc message-id="1" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <get-config>
    <source><running/></source>
    <filter type="subtree">
      <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces"/>
    </filter>
  </get-config>
</rpc>
```

### edit-config and commit

```xml
<!-- 1. Edit the candidate datastore -->
<rpc message-id="2" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <edit-config>
    <target><candidate/></target>
    <config>
      <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
        <interface>
          <name>GigabitEthernet0/0</name>
          <description>Uplink to Core</description>
          <enabled>true</enabled>
        </interface>
      </interfaces>
    </config>
  </edit-config>
</rpc>

<!-- 2. Commit to activate -->
<rpc message-id="3" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <commit/>
</rpc>
```

### NETCONF Operations Reference

| Operation | Description |
| --- | --- |
| `get` | Retrieve running configuration and operational state. |
| `get-config` | Retrieve configuration from a specific datastore. Supports subtree and XPath filters. |
| `edit-config` | Modify a target datastore. `operation` attribute controls merge, replace, create, delete, or remove. |
| `copy-config` | Copy a full datastore to another (e.g. candidate → startup). |
| `delete-config` | Delete an entire datastore (not `running`). |
| `lock` / `unlock` | Lock a datastore to prevent concurrent modification. |
| `commit` | Apply candidate datastore to running. |
| `discard-changes` | Roll back candidate to match running. |
| `validate` | Validate a datastore without committing. |
| `kill-session` | Terminate another active session by session-id. |

---

## RESTCONF

### Transport

RESTCONF runs over HTTPS. The root resource is discovered via
`/.well-known/host-meta` or is typically accessible at `/restconf`.

### HTTP Method Mapping

| HTTP Method | NETCONF Equivalent | Description |
| --- | --- | --- |
| `GET` | `<get>` / `<get-config>` | Read configuration or operational data. |
| `POST` | `<edit-config>` (create) | Create a new resource. Fails if it already exists. |
| `PUT` | `<edit-config>` (replace) | Replace an entire resource. |
| `PATCH` | `<edit-config>` (merge) | Merge/update specific fields. |
| `DELETE` | `<edit-config>` (delete) | Delete a resource. |

### URL Structure

```text
https://<device>/restconf/data/<module>:<container>/<list>=<key>
```

Retrieve interface configuration:

```text
GET https://router/restconf/data/ietf-interfaces:interfaces/interface=GigabitEthernet0%2F0
Accept: application/yang-data+json
```

Update description via PATCH:

```http
PATCH /restconf/data/ietf-interfaces:interfaces/interface=GigabitEthernet0%2F0
Content-Type: application/yang-data+json

{
  "ietf-interfaces:interface": {
    "name": "GigabitEthernet0/0",
    "description": "Uplink to Core"
  }
}
```

---

## YANG Data Models

YANG (RFC 7950) defines the structure, types, and constraints of configuration and
operational data. Key model sources:

| Source | Examples | Notes |
| --- | --- | --- |
| **IETF** | `ietf-interfaces`, `ietf-routing`, `ietf-bgp` | RFC-defined, vendor-neutral. |
| **OpenConfig** | `openconfig-interfaces`, `openconfig-bgp` | Industry consortium; practical vendor-neutral models. |
| **Vendor/native** | Cisco IOS-XE `cisco-xe-ietf-*`, FortiGate proprietary | Device-specific extensions. |

Supported models and revisions are discoverable via NETCONF:

```xml
<rpc message-id="4" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <get>
    <filter type="subtree">
      <modules-state xmlns="urn:ietf:params:xml:ns:yang:ietf-yang-library"/>
    </filter>
  </get>
</rpc>
```

### Cisco IOS-XE — Enable NETCONF

```ios
netconf-yang
netconf-yang feature candidate-datastore
```

---

## Notes

- NETCONF authentication uses SSH keys or certificates. Password authentication is
  supported by the SSH layer but should be avoided in production.
- `ncclient` (Python) is the standard NETCONF client library for automation scripts.
- RESTCONF is more approachable for scripting — standard HTTPS, JSON or XML payloads,
  curl-compatible — but lacks NETCONF's full transactional commit model.
- RESTCONF does not support `lock`, `discard-changes`, or confirmed commit.
- Cisco YANG Suite and `pyang` are useful tools for exploring, validating, and
  converting YANG models.
- The `edit-config` `operation` attribute defaults to `merge` if not specified.
  Use `replace` to overwrite a list entry entirely, or `delete` to remove it.
