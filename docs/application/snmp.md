# SNMP

The Simple Network Management Protocol provides a framework for monitoring and
managing network devices. An SNMP manager queries or configures agents running on
devices; agents send unsolicited traps to notify managers of events. SNMP messages
are ASN.1/BER encoded. Three major versions are in use, with significantly different
security models.

## Quick Reference

| Property | Value |
| --- | --- |
| **OSI Layer** | Layer 7 — Application |
| **TCP/IP Layer** | Application |
| **RFC** | RFC 1157 (v1), RFC 1901 + RFC 1905 (v2c), RFC 3411–3418 (v3) |
| **Wireshark Filter** | `snmp` |
| **UDP Ports** | `161` (agent — Get/Set), `162` (manager — Traps/Informs) |

---

## SNMPv1

Defined in RFC 1157. Simple community-string authentication (cleartext). Still found
on legacy devices.

**Message structure:**

```text
SEQUENCE {
  version    INTEGER (0)          -- v1
  community  OCTET STRING         -- cleartext community name
  pdu        PDU                  -- GetRequest | GetNextRequest |
}                                 --   GetResponse | SetRequest | Trap
```

**PDU types:**

| Type | Direction | Description |
| --- | --- | --- |
| GetRequest | Manager → Agent | Retrieve the value of one or more OIDs. |
| GetNextRequest | Manager → Agent | Retrieve the next OID in the MIB tree. Used to walk a MIB. |
| GetResponse | Agent → Manager | Response to Get/GetNext/Set. Contains error status and variable bindings. |
| SetRequest | Manager → Agent | Set the value of one or more OIDs. |
| Trap | Agent → Manager | Unsolicited notification. No acknowledgement. |

---

## SNMPv2c

Defined in RFC 1901 (community-based) and RFC 1905 (PDU format). Adds `GetBulkRequest`
and `InformRequest`, and improves error handling. Community string remains cleartext.

**Message structure:**

```text

SEQUENCE {
  version    INTEGER (1)          -- v2c
  community  OCTET STRING         -- cleartext community name
  pdu        PDU                  -- GetRequest | GetNextRequest | GetResponse |
}                                 --   SetRequest | GetBulkRequest |
                                  --   InformRequest | SNMPv2-Trap | Report
```

**Additional PDU types over v1:**

| Type | Direction | Description |
| --- | --- | --- |
| GetBulkRequest | Manager → Agent | Retrieve large blocks of data in a single request. Replaces repeated GetNextRequest walks. Controlled by `non-repeaters` and `max-repetitions` fields. |
| InformRequest | Manager → Manager | Acknowledged notification between managers. The receiver sends a GetResponse to acknowledge. |
| SNMPv2-Trap | Agent → Manager | Unsolicited notification. No acknowledgement. Replaces v1 Trap with a standardised format. |
| Report | Agent → Manager | Used internally by SNMPv3 engines. |

---

## SNMPv3

Defined in RFC 3411–3418. Introduces a proper security model with authentication and
encryption. The community string is replaced by a user-based security model (USM).

**Message structure:**

```text

SEQUENCE {
  msgVersion         INTEGER (3)
  msgGlobalData      SEQUENCE {
    msgID            INTEGER            -- unique message identifier
    msgMaxSize       INTEGER            -- max message size sender can receive
    msgFlags         OCTET STRING       -- 1 byte: [reportable | priv | auth]
    msgSecurityModel INTEGER (3)        -- 3 = USM
  }
  msgSecurityParameters  OCTET STRING  -- USM parameters (see below)
  msgData            CHOICE {
    plaintext        scopedPDU          -- if not encrypted
    encryptedPDU     OCTET STRING       -- if privFlag set
  }
}
```

**USM Security Parameters:**

| Parameter | Description |
| --- | --- |
| **msgAuthoritativeEngineID** | Unique ID of the authoritative SNMP engine (agent for Get/Set, manager for Informs). |
| **msgAuthoritativeEngineBoots** | Number of times the engine has (re)initialised. Used for replay protection. |
| **msgAuthoritativeEngineTime** | Seconds since last boot. Combined with EngineBoots for replay protection (±150s window). |
| **msgUserName** | Security name of the user on whose behalf the message is sent. |
| **msgAuthenticationParameters** | HMAC digest of the message (blank when not authenticated). |
| **msgPrivacyParameters** | Encryption initialisation vector (blank when not encrypted). |

**Security levels:**

| Level | Auth | Priv | Description |
| --- | --- | --- | --- |
| `noAuthNoPriv` | No | No | No authentication or encryption. Community-string equivalent. |
| `authNoPriv` | Yes | No | HMAC authentication (MD5 or SHA). Message integrity but cleartext. |
| `authPriv` | Yes | Yes | HMAC authentication + AES/DES encryption. Recommended for production. |

---

## PDU Structure (All Versions)

All Get/Set/Response PDUs share a common structure:

```text

PDU {
  request-id    INTEGER       -- correlates requests to responses
  error-status  INTEGER       -- 0=noError, 1=tooBig, 2=noSuchName, ...
  error-index   INTEGER       -- points to the failing variable binding (0 if no error)
  variable-bindings SEQUENCE OF VarBind {
    name  OID
    value ANY                 -- value or error (noSuchObject, noSuchInstance, endOfMibView)
  }
}
```

---

## Version Comparison

| Feature | v1 | v2c | v3 |
| --- | --- | --- | --- |
| Authentication | Community string (cleartext) | Community string (cleartext) | HMAC-MD5 / HMAC-SHA |
| Encryption | None | None | AES-128 / AES-256 / 3DES |
| Bulk retrieval | No | GetBulkRequest | GetBulkRequest |
| Acknowledged traps | No | InformRequest | InformRequest |
| 64-bit counters | No | Yes (Counter64) | Yes (Counter64) |
| Error handling | Limited | Improved | Improved |

## Notes

- **SNMPv1 and v2c should not be used on untrusted networks** — the community string
  is transmitted in cleartext and provides no replay protection. Use SNMPv3 `authPriv`
  for any management traffic crossing untrusted segments.

- **OIDs** (Object Identifiers) are hierarchical dotted-notation identifiers for
  managed objects (e.g. `1.3.6.1.2.1.1.1.0` = `sysDescr.0`). MIBs provide
  human-readable names for OIDs.

- **Engine ID discovery** is required before SNMPv3 authentication can succeed.
  A manager sends an unauthenticated probe to discover the agent's EngineID,
  EngineBoots, and EngineTime before sending an authenticated request.

- **SNMP over TCP** (port 161) is supported but uncommon. UDP is standard.
