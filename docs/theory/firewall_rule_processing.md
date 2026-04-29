# Firewall Rule Processing and Packet Flow

Complete guide to understanding how packets are evaluated against firewall rules and
access control lists.

---

## At a Glance

| Aspect | Stateless (ACL) | Stateful (Firewall Policy) |
| --- | --- | --- |
| **Evaluation Scope** | Per-packet, independent | Per-connection (session tracking) |
| **Rule Direction** | Unidirectional (in/out separate) | Bidirectional (single policy) |
| **Return Traffic** | Requires explicit rule | Automatic (established connection) |
| **Performance** | Fast (simple match) | Slower (connection state tracking) |
| **Complexity** | High (need in + out rules) | Low (bidirectional single rule) |
| **Implicit Deny** | Yes (recommended) | Yes (recommended) |
| **Use Case** | Network layer filtering | Application layer / DPI |
| **Example Platforms** | Cisco router ACLs, Fortinet (ACCEPT-phase) | FortiGate policies, Cisco ASA, Palo Alto Networks |

---

## Fundamental Concepts

### Rule Processing Order

Firewall rules are evaluated **top-to-bottom, first match wins**.

```text
Rule 1: Allow TCP 443 (HTTPS)
Rule 2: Allow TCP 80 (HTTP)
Rule 3: Deny all

Packet arrives: SRC=10.0.0.1, DST=1.1.1.1, PROTO=TCP, PORT=443

Evaluation:
  Check Rule 1: "Allow TCP 443" → MATCH!
  Action: ALLOW
  (Rules 2 and 3 never evaluated)

Result: Packet forwarded
```

### Implicit Deny (Deny Everything Else)

If no rule matches, traffic is **implicitly denied**.

```text

Rule 1: Allow HTTP
Rule 2: Allow HTTPS
(no more rules)

Packet: SSH to 1.1.1.1
  Check Rule 1: "Allow HTTP" → NO MATCH
  Check Rule 2: "Allow HTTPS" → NO MATCH
  Implicit Deny: DROP

Result: Packet dropped
```

**Note:** Some systems require explicit deny; others use implicit. Check your platform.

---

## Stateful vs Stateless Processing

### Stateless Firewalls (ACLs)

Evaluate each packet independently, no knowledge of previous packets.

```text

Rule: Allow TCP port 443 from 10.0.0.0/8 to any

Packet 1 (Outbound): 10.0.1.1:50000 → 1.1.1.1:443
  Evaluation: Source 10.0.0.0/8? YES → Allow

Packet 2 (Return): 1.1.1.1:443 → 10.0.1.1:50000
  Evaluation: Source 10.0.0.0/8? NO (source is 1.1.1.1)
  Result: DROP!

Problem: Return traffic blocked because rule doesn't match inbound direction
```

**Solution:** Add explicit return-traffic rule OR use stateful firewall.

### Stateful Firewalls (Firewall Policies)

Remember established connections; automatically allow return traffic.

```text

Policy: Allow TCP port 443 from Internal to External

Connection 1 (Outbound): Internal:10.0.1.1 → External:1.1.1.1:443
  Evaluation: Matches policy → Allow
  Firewall remembers: "Connection established"

Return traffic: External:1.1.1.1:443 → Internal:10.0.1.1
  Evaluation: Part of established connection
  Result: ALLOW (automatic, no rule needed)
```

**Advantage:** Return traffic automatic; simpler rules.

---

## Packet Flow Through Rules

### Typical Evaluation Order

```text

1. Check source/destination IP address

   ↓ (if match, continue; if no match, skip to next rule)

2. Check protocol (TCP, UDP, ICMP, etc.)

   ↓

3. Check source port (if applicable)

   ↓

4. Check destination port (if applicable)

   ↓

5. Check other criteria (DSCP, application, etc.)

   ↓

6. If all criteria match → apply action (Allow/Deny/Log)

   ↓

7. If any criterion doesn't match → check next rule

8. If no rule matches → implicit deny
```

### Example: Multi-Criteria Matching

```text

Rule 1:
  Source IP: 10.0.0.0/24
  Destination IP: 1.1.1.0/24
  Protocol: TCP
  Destination Port: 443
  Action: Allow

Incoming packet: 10.0.0.5 → 8.8.8.8:443 (TCP)

Evaluation:
  Source 10.0.0.0/24? YES (10.0.0.5 matches)
  Destination 1.1.1.0/24? NO (8.8.8.8 doesn't match)
  Result: SKIP to next rule

Action: Check next rule (not allowed by Rule 1)
```

---

## Rule Ordering and Optimization

### Problem: Inefficient Rule Order

```text

Rules (worst case):
  Rule 1: Allow SSH from specific admin IP
  Rule 2: Allow HTTP from specific server
  Rule 3: Allow HTTPS from specific server
  Rule 4: Deny all port 22 (SSH)
  Rule 5: Allow all other traffic (catch-all)

Traffic: Internal SSH attempt
  Check Rule 1: Admin IP? NO
  Check Rule 2: HTTP? NO
  Check Rule 3: HTTPS? NO
  Check Rule 4: Port 22? YES → DENY

Result: 4 rule evaluations before denying
```

### Solution: Order by Frequency and Specificity

```text

Rules (optimized):
  Rule 1: Allow all established/related (stateful)
          (Matches 90% of traffic → evaluated first)

  Rule 2: Allow common services (HTTP/HTTPS)
          (Matches 8% of traffic)

  Rule 3: Allow specific admin access
          (Matches 1% of traffic)

  Rule 4: Deny malicious IPs (blacklist)
          (Matches <1% of traffic)

  Rule 5: Deny everything else
          (Catch-all, rarely used with explicit deny)

Result: Most traffic evaluated against 1–2 rules
```

---

## Common Rule Patterns

### Pattern 1: Default Deny (Most Secure)

Deny everything, then allow specific traffic.

```text

Rule 1: Allow port 443 from Internal to External
Rule 2: Allow port 80 from Internal to External
Rule 3: Allow SSH from Admin-IP to Servers
(implicit deny everything else)

Result: Only explicitly allowed traffic passes
Risk: Overly restrictive; users can't access needed services
```

### Pattern 2: Default Allow (Less Secure)

Allow everything, then deny specific traffic.

```text

Rule 1: Deny malware IPs
Rule 2: Deny port 25 (block spam)
Rule 3: Allow everything else

Result: Most traffic passes; only blocked traffic denied
Risk: Accidental open ports; less control
```

### Pattern 3: Balanced (Recommended)

Allow common services, deny specific threats, deny everything else.

```text

Rule 1: Allow HTTP/HTTPS to web servers
Rule 2: Allow SSH from admin IPs
Rule 3: Deny known malware IPs
Rule 4: Deny port 23 (Telnet)
(implicit deny everything else)

Result: Common services work; threats blocked; unknown = denied
Risk: Moderate; balance between usability and security
```

---

## Direction: Ingress vs Egress

Firewall rules evaluate traffic in different directions.

### Ingress (Inbound)

Traffic entering through interface.

```text

Interface: port1 (WAN, facing internet)

Ingress rules on port1:
  Rule 1: Allow TCP 443 from any to 192.168.1.100
  Rule 2: Deny all

Traffic: 1.1.1.1 (internet) → 192.168.1.100:443
  Direction: Ingress (entering port1)
  Evaluation: Matches Rule 1 → Allow
```

### Egress (Outbound)

Traffic leaving through interface.

```text

Interface: port1 (WAN)

Egress rules on port1:
  Rule 1: Allow to any
  Rule 2: Deny DNS to 8.8.8.8:53

Traffic: 192.168.1.1 (internal) → 8.8.8.8:53 (DNS)
  Direction: Egress (leaving port1)
  Evaluation: Matches Rule 2 → Deny
```

**Note:** Policies work differently (source zone → dest zone, not per-interface).

---

## Bidirectional vs Unidirectional

### Unidirectional Rules (ACLs)

Only affects traffic in one direction; return traffic requires separate rule.

```text

Cisco ACL on interface GigabitEthernet0/1 (inbound):
  permit tcp 10.0.0.0 0.0.0.255 any eq 443

Outbound traffic (10.0.0.5 → 1.1.1.1:443):
  Evaluation: ACL is inbound → not checked
  Result: Allowed (ACL only checks inbound traffic)

Return traffic (1.1.1.1:443 → 10.0.0.5):
  Evaluation: ACL is inbound → checked
  Criteria: permit tcp 10.0.0.0... (matches reverse direction? NO)
  Result: DENIED!
```

### Bidirectional Policies (Firewall Policies)

One policy allows both directions if stateful.

```text

FortiGate Policy:
  Source Zone: Internal
  Destination Zone: External
  Service: HTTPS
  Action: Allow

Outbound (Internal → External:443):
  Evaluation: Matches policy → Allow
  Firewall remembers connection

Return traffic (External:443 → Internal):
  Evaluation: Part of remembered connection
  Result: ALLOW (automatic, bidirectional)
```

---

## Logging and Troubleshooting

### Enable Logging to Identify Rule Matches

```text

Cisco ACL:
  permit tcp 10.0.0.0 0.0.0.255 any eq 443 log

Fortgate Policy:
  set logtraffic enable

Result: Each matching packet logged with action (allow/deny)
```

### Identifying Which Rule Matched

```text

Log output:
  ACL log entry: "10.0.1.5 → 8.8.8.8:443 permitted by ACL permit 10"
  Policy log entry: "10.0.1.5 → 8.8.8.8 HTTPS Policy ID 5 allowed"

Interpretation:

  - Know which rule evaluated the traffic
  - Can adjust rule priority or criteria
```

### Hit Counters

Track how many times each rule matched.

```text

Cisco:
  show access-lists
  → Displays hit count for each ACL rule

FortiGate:
  get firewall policy summary
  → Shows traffic stats per policy

Use: Identify unused rules; optimize rule order
```

---

## Performance Considerations

### Rule Evaluation CPU Cost

Each rule evaluation consumes CPU. Optimization improves throughput.

```text

Optimization techniques:

  1. Order rules by frequency (most-matched first)
  2. Remove duplicate rules
  3. Consolidate similar rules into groups
  4. Use stateful inspection (avoid return-traffic rules)
  5. Use longest-match-first for IP subnets
```

### Hardware Offloading

Some platforms offload rule evaluation to hardware ASICs.

```text

Cisco hardware-based ACL lookup: O(1) lookup time
FortiGate hardware NP6 lookup: O(1) lookup time
Software-based: Linear scan through rules

Impact: Hardware much faster; no CPU bottleneck
```

---

## Common Mistakes

### Mistake 1: Forgetting Implicit Deny

```text

Rules:
  Rule 1: Allow SSH
  Rule 2: Allow HTTP
  (no explicit deny)

Unknown traffic arrives
  Evaluation: Doesn't match Rule 1 or 2
  Result: Implicit deny (DROPPED)

Expectation vs Reality:
  Expectation: "Only SSH and HTTP blocked; other stuff works"
  Reality: "Only SSH and HTTP work; everything else blocked"
```

### Mistake 2: Rules in Wrong Order

```text

Rules (wrong order):
  Rule 1: Allow all
  Rule 2: Deny malware IPs

Traffic from malware IP
  Evaluation: Rule 1 (Allow all) matches → ALLOW
  Rule 2 never evaluated (first match wins)

Result: Malware allowed because rule 1 caught it first
```

### Mistake 3: Bidirectional Assumption

```text

ACL Rule: Allow TCP 443 outbound

Assumption: "HTTP/S traffic to internet allowed"

Reality:
  Outbound (internal → internet:443): NOT CHECKED (outbound ACL only for egress)
  Inbound (return, internet:443 → internal): CHECKED, doesn't match

Result: Return traffic blocked; connection fails
```

### Mistake 4: Overlapping Rules with Different Actions

```text

Rules:
  Rule 1: Deny 10.0.1.0/24
  Rule 2: Allow 10.0.1.100

Traffic from 10.0.1.100
  Evaluation: Rule 1 (Deny 10.0.1.0/24) matches (10.0.1.100 is in range) → DENY
  Rule 2 never evaluated (first match wins)

Result: Traffic denied, even though Rule 2 would allow it

Solution: Put more specific rule (Rule 2) before general rule (Rule 1)
```

---

## Rule Design Best Practices

| Best Practice | Reason |
| --- | --------- |
| **Order by frequency** | Most-matched rules first = faster evaluation |
| **Use implicit deny** | Default secure; allows only known-good traffic |
| **Log important rules** | Track what's being allowed/denied |
| **Document rule intent** | Facilitate future changes |
| **Remove unused rules** | Improves performance; reduces confusion |
| **Use stateful inspection** | Automatic return-traffic; simpler rules |
| **Test rule changes** | Catch mistakes before production |
| **Review rules quarterly** | Identify obsolete/redundant rules |
| **Group related rules** | Easier to manage and understand |
| **Use specific sources/ports** | Reduces false positives; better security |

---

## Summary

- **Rules evaluated top-to-bottom; first match wins**
- **Implicit deny = only explicitly allowed traffic passes (secure)**
- **Stateful firewalls auto-allow return traffic; ACLs require explicit rules**
- **Order rules by frequency for performance**
- **Bidirectional policies simplify configuration vs unidirectional ACLs**
- **Log important rules to troubleshoot**
- **Test changes before deploying to production**

---

## See Also

- [Access Control Lists (ACLs) Reference](../reference/acl_reference.md)
- [Cisco ACL Configuration](../cisco/cisco_acl_config.md)
- [Fortinet FortiGate Policies](../fortigate/fortigate_firewall_policies.md)
- [Stateful Firewall Concepts](../theory/stateful_inspection.md)
- [NAT & Port Translation](../theory/nat.md)
