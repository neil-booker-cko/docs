# Administrative Distance

Administrative Distance (AD) is a Cisco IOS concept representing the trustworthiness
of a routing information source. When the same prefix is learned from multiple sources
(e.g. OSPF and a static route), the router installs the route with the **lowest AD**
into the routing table. AD is a locally significant value — it is not advertised to
neighbours.

Other vendors use the same concept under different names: Juniper calls it

**route preference** (also lower = better), while some vendors use the term
**administrative weight**.

---

## Cisco IOS / IOS-XE

| Source | AD | Notes |
| --- | --- | --- |
| Connected interface | `0` | Always preferred; cannot be overridden by routing |
| Static route | `1` | Default; configurable per route with `ip route ... <ad>` |
| EIGRP summary route | `5` | Auto-summary routes created by EIGRP |
| External BGP (eBGP) | `20` | Routes learned from an external AS |
| Internal EIGRP | `90` | Routes learned via EIGRP within the AS |
| IGRP (deprecated) | `100` | Removed from IOS 12.3 |
| OSPF | `110` | OSPFv2 and OSPFv3 |
| IS-IS | `115` | |
| RIP | `120` | RIPv1, RIPv2, RIPng |
| ODR (On Demand Routing) | `160` | Hub-and-spoke stub routing over HDLC |
| External EIGRP | `170` | Routes redistributed into EIGRP from another source |
| Internal BGP (iBGP) | `200` | Routes learned from peers in the same AS |
| Unknown / unreachable | `255` | Route is not installed in the forwarding table |

### Floating Static Routes

A static route with an AD higher than the primary routing protocol acts as a backup.
When the dynamic route disappears from the table, the static route is installed.

```text
ip route 10.1.0.0 255.255.0.0 192.0.2.1 150
```

This route is only active if no OSPF (AD 110) or EIGRP (AD 90) route for the prefix
exists.

---

## Juniper Junos — Route Preference

Junos uses **preference** (lower = better). Unlike Cisco AD, Junos preference can be
modified at the protocol level or per route via routing policy.

| Source | Preference | Notes |
| --- | --- | --- |
| Direct (connected) | `0` | |
| Local (router's own address) | `0` | |
| Static | `5` | |
| RSVP | `7` | Traffic Engineering |
| LDP | `9` | MPLS label distribution |
| OSPF internal | `10` | |
| IS-IS L1 internal | `15` | |
| IS-IS L2 internal | `18` | |
| RIP | `100` | |
| OSPF external (Type 2) | `150` | |
| IS-IS L1 external | `160` | |
| IS-IS L2 external | `165` | |
| BGP (eBGP and iBGP) | `170` | Junos does not differentiate by default |
| OSPF external (Type 1) | `150` | |

> Junos treats eBGP and iBGP at the same preference by default (`170`). Use routing
> policy to differentiate if needed.

---

## Cisco NX-OS

NX-OS uses the same AD values as IOS with minor differences.

| Source | AD | Notes |
| --- | --- | --- |
| Connected | `0` | |
| Static | `1` | |
| eBGP | `20` | |
| EIGRP internal | `90` | |
| OSPF | `110` | |
| IS-IS | `115` | |
| RIP | `120` | |
| EIGRP external | `170` | |
| iBGP | `200` | |

---

## Arista EOS

| Source | AD | Notes |
| --- | --- | --- |
| Connected | `0` | |
| Static | `1` | |
| eBGP | `20` | |
| OSPF internal | `110` | |
| IS-IS | `115` | |
| RIP | `120` | |
| OSPF external | `150` | |
| iBGP | `200` | |

---

## Cisco vs Juniper Comparison

| Protocol | Cisco AD | Juniper Preference |
| --- | --- | --- |
| Connected | `0` | `0` |
| Static | `1` | `5` |
| eBGP | `20` | `170` |
| OSPF internal | `110` | `10` |
| IS-IS | `115` | `15` / `18` |
| RIP | `120` | `100` |
| OSPF external | `110` | `150` |
| iBGP | `200` | `170` |

The most significant difference: Cisco strongly prefers eBGP (AD 20) over IGPs,
while Juniper places all BGP routes at preference 170 — below all IGP routes by
default.

---

## Fortinet FortiGate — Distance

FortiGate does not use "administrative distance" in the traditional sense. Instead,
route selection is determined by:

1. **Prefix length** — Longest prefix match always wins
1. **Static vs Dynamic** — Static routes can override dynamic routes via configurable distance
1. **Protocol metric** — Within BGP, OSPF, or RIP, the protocol's own metric determines preference

### Static Route Distance (FortiGate)

Static routes have an optional **distance** value (0-255):

```fortios
config router static
  edit 1
    set destination 10.1.0.0 255.255.0.0
    set gateway 192.0.2.1
    set distance 10
    ! Distance 10 — higher than most dynamic protocols, acts as backup
  next
end
```

**Common distance values:**

| Distance | Typical Use |
| --- | --- |
| `0` | Default static route; preferred over all dynamic routes |
| `10` | Backup to OSPF (cost 10) |
| `20` | Backup to eBGP |
| `100` | Backup to RIP; preferred over OSPF |
| `255` | Route is never installed (disabled effectively) |

### Dynamic Routing Metrics (FortiGate)

FortiGate's dynamic routing protocols do not have an "AD" equivalent — they compete
on metric alone once prefix length is matched:

- **OSPF:** Cost (lower = better)
- **BGP:** AS path length, local preference, MED, etc.
- **RIP:** Hop count (max 15)

If two OSPF routes for the same prefix exist (e.g., via different neighbors),
FortiGate selects the one with lower cost. Equally-good routes load-balance (ECMP).

### Example: Static Route Overriding OSPF

```fortios
! OSPF learns 10.1.0.0/16 with cost 100
! Static route configured as backup:

config router static
  edit 1
    set destination 10.1.0.0 255.255.0.0
    set gateway 192.0.2.2
    set distance 110
    ! Distance 110: only used if OSPF route disappears
  next
end
```

---

## Notes

- AD is evaluated **before** the best-path algorithm within a routing protocol.
  Two OSPF routes competing with each other use OSPF metric, not AD. AD only
  resolves conflicts between different routing sources.

- **Route redistribution** does not carry AD. A route redistributed from EIGRP
  into OSPF is installed with OSPF's AD (110) on the receiving router.

- Cisco **ECMP** requires all candidate routes to have the same AD and metric.
  Routes from different protocols cannot be load-balanced unless manipulated with
  policy.

- A static route to Null0 with AD 254 is a common pattern for BGP black-hole
  communities — high enough to lose to any real route.
