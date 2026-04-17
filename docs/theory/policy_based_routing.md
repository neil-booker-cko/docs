# Policy-Based Routing (PBR) Fundamentals

Guide to routing packets based on policies rather than just destination IP address.

## Traditional Routing vs Policy-Based Routing

### Traditional Routing (Destination-Based)

Routes packets based ONLY on destination IP address.

```text
Routing table entry:
  Destination: 10.0.0.0/24
  Next-hop: 192.168.1.1

Packet: SRC=10.1.1.1, DST=10.0.0.5
  Routing decision: Destination is 10.0.0.0/24 → Next-hop 192.168.1.1
  (Source, port, protocol ignored)
```

**Limitation:** All traffic to same destination takes same path, regardless of source or application.

### Policy-Based Routing (PBR)

Routes packets based on **multiple criteria** beyond destination.

```text

Policy: If source is 10.1.0.0/16 AND protocol is HTTP
  Then route via ISP-1

Packet: SRC=10.1.1.1, DST=10.0.0.5, PROTO=TCP:80
  Evaluation: Source 10.1.0.0/16? YES → Protocol HTTP? YES
  Action: Route via ISP-1 next-hop
```

---

## Policy Criteria

PBR can match on:

| Criteria | Example |
| --- | --------- |
| **Source IP** | 10.1.0.0/24 (specific subnet) |
| **Destination IP** | 192.168.0.0/16 |
| **Protocol** | TCP, UDP, ICMP |
| **Source Port** | 22 (SSH), 443 (HTTPS) |
| **Destination Port** | 3306 (MySQL), 5432 (PostgreSQL) |
| **DSCP** | EF (voice), AF4 (video) |
| **Application** | Requires DPI; HTTP, FTP, etc. |
| **Incoming Interface** | port1, port2 |

---

## Policy Actions

When traffic matches a policy, apply an action:

| Action | Effect |
| --- | --------- |
| **Set next-hop** | Route via specific gateway IP |
| **Set outgoing interface** | Send via specific egress port |
| **Set metric** | Assign cost (affects route selection) |
| **Set priority** | Assign QoS class |
| **Mark DSCP** | Set QoS marking |
| **Deny** | Drop traffic |
| **Count** | Log/count matching traffic |

---

## Use Cases

### Use Case 1: Multi-ISP Load Balancing

Two ISPs, balance traffic between them.

```text

Policy 1: If source is 10.0.0.0/24
  Route via ISP-1 next-hop 200.1.1.1

Policy 2: If source is 10.1.0.0/24
  Route via ISP-2 next-hop 200.2.1.1

Result:
  Traffic from subnet 10.0.0.0/24 → ISP-1
  Traffic from subnet 10.1.0.0/24 → ISP-2
  Both ISP links utilized
```

### Use Case 2: Priority Routing for Critical Apps

VoIP and video get high-quality path; others get cheaper path.

```text

Policy 1: If protocol is UDP AND dst-port is 5060 (SIP/VoIP)
  Route via primary ISP (low-latency path)
  Set DSCP to EF (voice priority)

Policy 2: If protocol is TCP AND dst-port is 443 (HTTPS browsing)
  Route via secondary ISP (cheaper)
  Set DSCP to CS0 (best-effort)

Result:
  VoIP: high-quality path, low latency
  Web browsing: cost-effective path
```

### Use Case 3: Backup Link Failover

Route via primary by default; failover to backup on failure.

```text

Policy 1: If primary ISP is up
  Route via primary ISP next-hop 200.1.1.1

Policy 2: If primary ISP is down
  Route via backup ISP next-hop 200.2.1.1

Result:
  Normal: primary link carries traffic
  Primary fails: automatic failover to backup
```

### Use Case 4: Access Control Based on Source

Different security levels for different sources.

```text

Policy 1: If source is admin subnet 10.0.100.0/24
  Allow all destinations

Policy 2: If source is user subnet 10.0.1.0/24
  Deny access to finance servers
  Route to content filter first

Result:
  Admins: unrestricted access
  Users: restricted, filtered
```

---

## PBR vs Routing Protocols

### Dynamic Routing (BGP, OSPF)

- Routes converge based on network topology
- Automatic failover on link failure
- Complex configuration
- Scales to thousands of routers

### Policy-Based Routing (PBR)

- Routes based on packet attributes
- Manual failover or health checks
- Simple configuration
- Good for 2-10 site networks

### When to Use Each

| Scenario | Use |
| --- | --------- |
| **Small network (2-10 sites)** | PBR (simpler) |
| **Large network (100+ sites)** | BGP (scales) |
| **Multi-ISP load balancing** | PBR (per-source routing) |
| **Sub-second convergence needed** | BGP + FRR (faster than PBR health checks) |
| **Complex routing policies** | PBR (more granular than BGP) |

---

## Implementation Comparison

### Cisco Implementation

Uses **route-maps** with match/set commands.

```text

route-map PBR-POLICY permit 10
  match ip address source-subnet
  set ip next-hop 192.168.1.1
```

### FortiGate Implementation

Uses **policy-based routes** with match criteria and actions.

```text

config router policy
  edit 1
    set src "source-address"
    set dst "destination-address"
    set gateway "gateway-ip"
```

### Both Accomplish Same Goal

- Match on traffic criteria
- Set alternative next-hop
- Enable per-flow (or per-class) routing decisions

---

## PBR Packet Flow

```text

Packet arrives
  ↓

1. Check PBR policy (if enabled on interface/interface-group)

   ↓

2. If PBR matches:

   a. Apply action (set next-hop, mark DSCP, etc.)
   b. Bypass normal routing table
   c. Forward via PBR next-hop
   ↓

3. If PBR doesn't match or PBR not enabled:

   a. Proceed to normal routing table lookup
   b. Route based on destination IP
   c. Forward normally
```

---

## PBR vs Firewall Policies

### Firewall Policies

- Control traffic BETWEEN zones (allow/deny)
- Applied at zone boundary
- Order matters (first match wins)

### PBR

- Control ROUTING of allowed traffic (next-hop selection)
- Applied to ingress interface
- Overrides normal routing table

**Both can coexist:**

```text

Firewall Policy: Allow traffic from Internal to External
  ↓ (allowed)
PBR Policy: If source is admin, route via primary ISP
  ↓ (routing decision)
BGP/Static Route: Default route to ISP
```

---

## Limitations and Considerations

### CPU Overhead

PBR evaluation adds CPU cost per packet. Modern hardware offloads this.

### Asymmetric Routing

If return path doesn't match PBR, traffic might take different path back.

```text

Outbound: PBR routes via ISP-1
Return: ISP-1 sends back to ISP-2
Result: Traffic asymmetric; may trigger security alerts
```

### Complexity vs BGP

PBR good for simple cases. BGP better for complex, large networks.

---

## PBR Best Practices

| Practice | Reason |
| --- | --------- |
| **Use for 2-10 sites** | Scales better with BGP beyond that |
| **Test before production** | Asymmetric routing can break connectivity |
| **Document policies** | Facilitate troubleshooting |
| **Monitor PBR hit counts** | Verify policies are actually being used |
| **Use with health checks** | Automatic failover if next-hop down |
| **Combine with BGP** | BGP for inter-domain, PBR for intra-domain |
| **Match on specific criteria** | Too-broad match can unintentionally redirect traffic |
| **Enable logging** | Track which traffic matches policy |

---

## Summary

- **PBR** routes based on packet attributes (source, protocol, port)
- **Traditional routing** uses only destination IP
- **Use cases:** load balancing, priority routing, failover, access control
- **Good for:** small networks (2-10 sites), specific policy needs
- **Combine with BGP** for larger, more scalable designs
- **Test asymmetric routing** before production deployment
