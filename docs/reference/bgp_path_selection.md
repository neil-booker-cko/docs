# BGP Best Path Selection

BGP is a path-vector protocol — when multiple paths to the same prefix exist, the
router runs a deterministic algorithm to select a single best path to install in the
RIB and advertise to peers. The algorithm is purely local: it operates on the
attributes already present in the BGP table and produces no new packet fields.
BGP itself runs over TCP port 179, but path selection is a control-plane decision.

## Quick Reference

| Property | Value |
| --- | --- |
| **OSI Layer** | Layer 7 — Application (control-plane decision) |
| **Transport** | TCP port `179` |
| **RFC** | RFC 4271 (BGP-4) |
| **Scope** | Local to the router — not a packet field |
| **Wireshark Filter** | `bgp` |

---

## Cisco IOS / IOS-XE Best Path Selection

Cisco evaluates candidate paths in the order below. The first step that produces a
clear winner terminates the algorithm.

**Mnemonic:** *Weight, Local-Pref, Locally originated, AS path, Origin, MED,
eBGP/iBGP, IGP metric, Oldest, Router-ID, Cluster-list, Neighbor IP*
— sometimes remembered as **"We Locally Observe Attributes Of Many Internet
Gateway Routers Checking Next-hops"**.

| Step | Attribute | Prefer | Notes |
| --- | --- | --- | --- |
| 1 | **Weight** | Highest | Cisco proprietary. Local to the router only — never advertised. Default: `32768` (local), `0` (received). |
| 2 | **Local Preference** | Highest | Carried in iBGP updates across the AS. Not sent to eBGP peers. Default: `100`. |
| 3 | **Locally originated** | Local | Routes injected by this router via `network`, `redistribute`, or `aggregate-address` are preferred over routes learned from a peer. |
| 4 | **AS Path length** | Shortest | Number of AS numbers in `AS_PATH`. `AS_SET` counts as one element. Disabled with `bgp bestpath as-path ignore`. |
| 5 | **Origin** | IGP > EGP > ? | `i` (IGP) preferred over `e` (EGP) preferred over `?` (Incomplete). |
| 6 | **MED** | Lowest | Multi-Exit Discriminator. Compared only between paths from the same neighbouring AS by default. See notes. |
| 7 | **eBGP over iBGP** | eBGP | An eBGP-learned path is always preferred over an iBGP-learned path. |
| 8 | **IGP metric to next-hop** | Lowest | Interior cost to reach the BGP next-hop address. |
| 9 | **Oldest eBGP path** | Oldest | Most stable eBGP path preferred. Skipped when `bgp bestpath as-path multipath-relax` is enabled. |
| 10 | **BGP Router ID** | Lowest | Originating router's BGP Router ID. For reflected routes, the Originator ID attribute is used instead. |
| 11 | **Cluster list length** | Shortest | Route reflection only. Shorter cluster list = fewer reflector hops. |
| 12 | **Neighbour IP address** | Lowest | Final tiebreaker. IP address of the BGP peer from which the path was received. |

---

## Juniper Junos Best Path Selection

| Step | Attribute | Prefer | Notes |
| --- | --- | --- | --- |
| 1 | **Local Preference** | Highest | Default `100`. Carried in iBGP only; stripped before sending to eBGP peers. |
| 2 | **AS Path length** | Shortest | Confederation segments excluded by default. |
| 3 | **Origin** | IGP > EGP > ? | Mirrors RFC 4271 ordering. |
| 4 | **MED** | Lowest | Compared between paths from the same peer AS by default. `path-selection always-compare-med` enables global comparison. |
| 5 | **eBGP over iBGP** | eBGP | Externally learned routes preferred over internally learned. |
| 6 | **IGP metric to next-hop** | Lowest | Resolved via the active routing table. |
| 7 | **BGP Router ID** | Lowest | Originator ID used for reflected routes. |
| 8 | **Peer IP address** | Lowest | Tiebreaker when Router IDs are equal. |

> Junos has no Weight attribute. Per-prefix preference is achieved via Local
> Preference or routing policy. There is no "oldest eBGP path" step by default.

---

## Key Attribute Summary

| Attribute | Scope | Set via | Cisco default |
| --- | --- | --- | --- |
| **Weight** | Router-local only | `route-map`, `neighbor weight` | `32768` local / `0` received |
| **Local Preference** | AS-wide (iBGP) | `route-map set local-preference` | `100` |
| **MED** | Suggests to peer AS | `route-map set metric`, received from eBGP peer | `0` when set |
| **AS Path** | eBGP-propagated | Built automatically; `as-path prepend` to inflate | Actual path |
| **Origin** | Per-route | Origination method (`network`=`i`, `redistribute`=`?`) | `i` for `network` |

---

## Cisco vs Junos Comparison

| Step | Cisco IOS | Junos |
| --- | --- | --- |
| 1 | Weight (highest) | Local Preference (highest) |
| 2 | Local Preference (highest) | AS Path length (shortest) |
| 3 | Locally originated | Origin (IGP > EGP > ?) |
| 4 | AS Path length (shortest) | MED (lowest) |
| 5 | Origin (IGP > EGP > ?) | eBGP over iBGP |
| 6 | MED (lowest) | IGP metric (lowest) |
| 7 | eBGP over iBGP | Router ID (lowest) |
| 8 | IGP metric (lowest) | Peer IP (lowest) |
| 9 | Oldest eBGP path | — |
| 10 | Router ID (lowest) | — |
| 11 | Cluster list (shortest) | — |
| 12 | Neighbour IP (lowest) | — |

---

## Notes

- **Weight is Cisco-only.** It is not a BGP attribute and is never advertised to any
  peer. Use Local Preference for AS-wide path preference.

- **MED comparison scope.** By default, MED is only compared between paths from the
  same neighbouring AS. `bgp always-compare-med` forces comparison across all paths.
  Use with caution — inconsistent MED values across peers can cause routing instability.

- **Missing MED.** A route with no MED is treated as MED `0` by default (best).
  `bgp bestpath med missing-as-worst` treats it as `4294967295` (worst) instead.

- **ECMP / multipath.** Configure `maximum-paths` (iBGP: `maximum-paths ibgp`). All
  attributes through step 8 must be equal. `bgp bestpath as-path multipath-relax`
  allows eBGP multipath across different AS numbers; step 9 onward is then skipped.

- **Route reflection.** When a route reflector re-advertises a route it adds the
  Originator ID (the originating speaker's Router ID). Step 10 uses Originator ID
  instead of Router ID to prevent the reflector from incorrectly preferring itself.
