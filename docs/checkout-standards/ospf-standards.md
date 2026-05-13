# OSPF Configuration Standards

OSPF configuration and operational standards for Checkout. All OSPF configuration must use the
modern interface-based configuration approach. Network statements are deprecated; all networks
must be explicitly enabled on interfaces.

---

## OSPF Process Configuration

**Standard:** Single OSPF process (ID 1) per router.

```ios
router ospf 1
 router-id 10.0.0.1
 default-information originate always
 log-adjacency-changes detail
!
```

**Important:** Do NOT use network statements. All VLAN/interface routing must be explicitly
configured on interfaces using `ip ospf [process-id] area [area-id]` commands (see
Interface Configuration section below).

---

## Interface-Based OSPF Configuration (Modern Approach)

**Standard:** Enable OSPF directly on interfaces rather than using network statements. This
provides granular control, clearer intent, and easier troubleshooting.

**Key Rules:**

- Enable OSPF on each interface with `ip ospf [process-id] area [area-id]`
- Configure timers per-interface for fine-tuned convergence
- Apply authentication per-interface
- Do NOT use network statements in router config

**Example — Data VLAN on router:**

```ios
interface Vlan100
 ip address 10.0.100.1 255.255.255.0
 ip ospf 1 area 0
 ip ospf authentication message-digest
 ip ospf message-digest-key 1 md5 MyAuthKey123
 ip ospf hello-interval 10
 ip ospf dead-interval 40
!
```

**Example — Inter-router link:**

```ios
interface GigabitEthernet0/0
 ip address 10.0.0.1 255.255.255.252
 ip ospf 1 area 0
 ip ospf authentication message-digest
 ip ospf message-digest-key 1 md5 MyAuthKey123
 ip ospf hello-interval 10
 ip ospf dead-interval 40
!
```

---

## OSPF Timers & BFD (Recommended)

**Standard:** Use BFD for fast failure detection on all OSPF neighbors where supported.
BFD enables sub-second convergence and is strongly recommended for critical links.

### Standard Timers (without BFD)

| Timer | Value | Use Case |
| --- | --- | --- |
| Hello interval | 10 seconds | Normal operation (fallback only) |
| Dead interval | 40 seconds | Detection timeout (4x hello) |
| Retransmit interval | 5 seconds | LSA retransmit |

### Recommended: Fast Convergence (with BFD)

| Timer | Value | Use Case |
| --- | --- | --- |
| Hello interval | 30 seconds | BFD handles fast detection |
| Dead interval | 120 seconds | Longer dead (BFD sub-second) |
| BFD interval | 300ms tx/rx | Sub-second failover |

**Configuration (BFD preferred):**

First, define a global BFD template (see [BFD Standards](bfd-standards.md)):

```ios
bfd-template single-hop BFD_STANDARD
 interval min-tx 300 min-rx 300 multiplier 3
 no echo
!
```

Then apply to interfaces:

```ios
interface GigabitEthernet0/0
 ip ospf hello-interval 30
 ip ospf dead-interval 120
 ip ospf retransmit-interval 5
 ip ospf fall-over bfd
 bfd template BFD_STANDARD
!
```

**Configuration (without BFD - fallback only):**

```ios
interface GigabitEthernet0/0
 ip ospf hello-interval 10
 ip ospf dead-interval 40
 ip ospf retransmit-interval 5
!
```

---

## OSPF Authentication (Recommended)

**Standard:** Enable MD5 authentication on all OSPF-enabled interfaces to prevent unauthorized
LSA injection and rogue router attacks. Authentication is required for all production deployments.

```ios
interface Vlan100
 ip ospf authentication message-digest
 ip ospf message-digest-key 1 md5 MyAuthKey123
!

interface GigabitEthernet0/0
 ip ospf authentication message-digest
 ip ospf message-digest-key 1 md5 MyAuthKey456
!
```

**Key Management:**

- Rotate keys annually
- Use strong, unique key per area or per router pair
- Document key changes in change log
- Coordinate key rotation with peer networks during maintenance windows

---

## OSPF Areas

**Standard:** Use area 0 for all backbone links; additional areas for scalability.

| Area | Purpose | Interfaces |
| --- | --- | --- |
| 0 (Backbone) | Core interconnection | Core routers, critical links |
| 1 (Office) | Office sites | Office subnets, access layer |
| 2 (DC) | Datacenter | Datacenter subnets |

---

## OSPF Cost and Metric

**Standard:** Use default auto-cost (100 Mbps basis). Do NOT manually override costs.

```ios
router ospf 1
 auto-cost reference-bandwidth 100
!
```

---

## Default Route Propagation

**Standard:** Originate default route from border routers (core routers with external connectivity).

```ios
router ospf 1
 default-information originate always
!
```

---

## OSPF Passive Interfaces

**Standard:** Make all interfaces passive except inter-router links and redundancy links.

```ios
router ospf 1
 passive-interface default
 no passive-interface GigabitEthernet0/0
 no passive-interface GigabitEthernet0/1
!
```

---

## Verification Commands

```ios
show ospf neighbor
show ospf interface
show ip route ospf
show ospf database
debug ip ospf hello
```

---

## Related Standards

- [Routing Design](routing-design.md)
- [Security Hardening](security-hardening.md) — OSPF authentication
- [BGP Standards](bgp-standards.md) — Hybrid routing design
