# BGP Community Reference

BGP Communities (RFC 1997) are 32-bit tags attached to BGP routes as a path
attribute (Type 8). They allow route grouping for policy application — filtering,
local-preference setting, AS-path prepending — without embedding logic in the prefix
itself. Extended Communities (RFC 4360) are 64-bit and used for MPLS VPNs, EVPN,
and traffic engineering. Large Communities (RFC 8092) are 96-bit and allow
structured provider policies with full 32-bit ASN support.

## Quick Reference

| Property | Value |
| --- | --- |
| **Standard Communities** | RFC 1997 — 32-bit, format `AS:value` |
| **Extended Communities** | RFC 4360 — 64-bit, 2-byte Type + 6-byte Value |
| **Large Communities** | RFC 8092 — 96-bit, format `ASN:LD1:LD2` |
| **Well-known registry** | RFC 8195 |
| **BGP Attribute Type** | Type 8 (COMMUNITY), Type 16 (EXTENDED COMMUNITIES), Type 32 (LARGE COMMUNITY) |
| **Transitivity** | Optional transitive — passed to eBGP peers unless explicitly stripped |

---

## Standard Well-Known Communities (RFC 1997)

These communities have globally defined behaviour and must be honoured by all
compliant implementations.

| Community Value | Name | Behaviour |
| --- | --- | --- |
| `0xFFFF0000` (`65535:0`) | GRACEFUL_SHUTDOWN (RFC 8326) | Signals that the advertising router is about to go offline. Receivers should set local-preference to 0, enabling pre-maintenance traffic drain. |
| `0xFFFFFF01` (`65535:65281`) | NO_EXPORT | Do not advertise to eBGP peers. Routes may be shared with iBGP peers and confederation peers within the local AS. |
| `0xFFFFFF02` (`65535:65282`) | NO_ADVERTISE | Do not advertise to any peer — internal or external. The route is local to this router only. |
| `0xFFFFFF03` (`65535:65283`) | NO_EXPORT_SUBCONFED | Do not advertise outside the local confederation sub-AS. Equivalent to NO_EXPORT within a confederation member. |
| `0xFFFFFF04` (`65535:65284`) | NOPEER (RFC 3765) | Do not advertise to settlement-free or bilateral peering partners. Used by providers to prevent routes from propagating across peering fabrics. |
| `0x00000000` (`0:0`) | INTERNET | Route should be announced to the internet. Default behaviour; rarely set explicitly. |

---

## Community Format

Standard communities are expressed as two 16-bit decimal values separated by a
colon: `<AS>:<value>`. Example: `65000:100`.

The high 16 bits are typically the originating AS number; the low 16 bits carry a
locally defined policy tag. There is no universal convention, but common patterns
include:

| Example | Typical Meaning |
| --- | --- |
| `65000:100` | Prefer this route — set local-pref 200 at ingress |
| `65000:200` | Depref this route — set local-pref 100 at ingress |
| `65000:300` | Blackhole this prefix |
| `65000:999` | Do not export to customers |

---

## AWS BGP Communities (Direct Connect)

AWS attaches communities to routes advertised over Direct Connect to indicate route
origin. On-premises routers send communities to AWS to signal inbound path
preference.

### Received from AWS

| Community | Meaning |
| --- | --- |
| `7224:8100` | Routes originating from the same AWS Region |
| `7224:8200` | Routes originating from the same continent |

### Sent to AWS (inbound traffic engineering)

| Community | Local Preference Applied by AWS | Use |
| --- | --- | --- |
| `7224:9100` | 100 (lowest) | Use this path as backup only |
| `7224:9200` | 200 | Use this path as secondary |
| `7224:9300` | 300 (highest) | Use this path as primary |

On-premises routers attach `7224:9300` to routes sent over the preferred Direct
Connect connection and `7224:9100` over the backup to influence which connection AWS
uses for return traffic.

---

## Azure BGP Communities (ExpressRoute)

Azure attaches communities to routes advertised over ExpressRoute private peering to
indicate the origin region. Match these on-premises to set local preference for
inbound traffic engineering.

| Community | Meaning |
| --- | --- |
| `12076:51004` | Routes from Azure West Europe |
| `12076:51005` | Routes from Azure North Europe |
| `12076:51006` | Routes from Azure East US |
| `12076:5xxxx` | Region-specific — see Azure documentation for the full list |
| `12076:20000` | Routes originating from Exchange-based (public peering) connections |

---

## Extended Communities (RFC 4360)

Extended communities are 8 bytes: a 2-byte Type field followed by a 6-byte Value
field. They are widely used in MPLS VPN and EVPN control planes.

| Type Code | Name | Use |
| --- | --- | --- |
| `0x0002` | Route Target (RT) | MPLS L3VPN — identifies which VRFs should import this route. |
| `0x0003` | Route Origin (RO) | MPLS L3VPN — identifies the VRF that originated the route. |
| `0x0006` | L2VPN Info | VPLS and EVPN signalling. |
| `0x000B` | Cost Community | IGP cost traffic engineering; Cisco-proprietary. |

Route Targets in `AS:value` notation example: `65000:10` as an RT causes all PE
routers with VRF import `65000:10` to install the route.

---

## Large Communities (RFC 8092)

Large communities are 12 bytes: a 4-byte Global Administrator (full 32-bit ASN)
followed by two 4-byte Local Data fields. Format: `ASN:LD1:LD2`.

Designed for 4-byte ASN environments where the originating AS number does not fit in
the 16-bit high field of a standard community.

| Field | Size | Description |
| --- | --- | --- |
| Global Administrator | 32 bits | The originating or administering ASN (4-byte). |
| Local Data 1 | 32 bits | First locally assigned policy field. |
| Local Data 2 | 32 bits | Second locally assigned policy field. |

Example: `64500:1:100` — AS 64500, action 1 (blackhole), prefix tag 100.

---

## Cisco Configuration Examples

Tag outbound routes with NO_EXPORT:

```ios
route-map RM-TAG-NO-EXPORT permit 10
 set community no-export
```

Strip all communities before advertising to a customer:

```ios

route-map RM-STRIP-COMMUNITIES permit 10
 set community none
```

Match an inbound community and set local preference (e.g. AWS primary path):

```ios

ip community-list standard AWS-PRIMARY permit 7224:9300
!
route-map RM-AWS-IN permit 10
 match community AWS-PRIMARY
 set local-preference 300
route-map RM-AWS-IN permit 20
```

Apply the route-map to a BGP neighbour:

```ios

router bgp 65000
 neighbor 169.254.1.1 route-map RM-AWS-IN in
```

Add a community tag on routes advertised to a peer:

```ios

route-map RM-PEER-OUT permit 10
 set community 65000:200 additive
```

---

## Notes

- Communities are **optional transitive** attributes — they are forwarded to eBGP

  peers by default. Always strip internal policy communities before advertising to
  customers or peers using `set community none` in an outbound route-map.

- Multiple communities can be attached to a single route. Match with

  `ip community-list` using `permit` entries; use `match community <list-name>`
  in route-maps.

- `show ip bgp <prefix>` displays the communities attached to a route.

  `show ip bgp community <value>` filters the BGP table to routes carrying that
  community.

- The `additive` keyword in `set community` appends to existing communities rather

  than replacing them. Without `additive`, any existing communities are overwritten.

- For 4-byte ASN environments, prefer Large Communities (RFC 8092) over standard

  communities to avoid the 16-bit AS field truncation problem.
