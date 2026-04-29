# GLBP (Gateway Load Balancing Protocol)

Complete guide to Cisco's gateway redundancy and load balancing protocol.

---

## At a Glance

| Aspect | GLBP | HSRP | VRRP |
| --- | --- | --- | --- |
| **Active Forwarders** | Multiple (up to 4 AVFs) | One (active) | One (master) |
| **Load Balancing** | Yes (via 4 virtual MACs) | No (single gateway) | No (single gateway) |
| **Bandwidth Utilization** | High (all routers active) | Low (one gateway active) | Low (one gateway active) |
| **Virtual MACs** | 4 (one per forwarder) | 1 (00:00:5E:00:01:xx) | 1 (00:00:5E:00:01:xx) |
| **Convergence** | ~3 seconds (AVG + AVF election) | ~3–10 seconds | ~3–10 seconds |
| **Vendor** | Cisco proprietary | Cisco proprietary | Standards-based (RFC 3768) |
| **Complexity** | Medium (AVG + multiple AVFs) | Low | Low |
| **Best For** | Multi-router load sharing | Simple active/backup | Vendor-neutral networks |

---

## Core Concept

**GLBP** provides both gateway redundancy and load balancing across multiple routers.

Unlike HSRP and VRRP (where only one gateway is active), GLBP allows multiple gateways to
simultaneously forward traffic, distributing the load.

```text
HSRP/VRRP:
  Virtual IP: 192.168.1.1
  Active: Router A (forwards ALL traffic)
  Backup: Router B (idle, only takes over on failure)
  Unused capacity: Router B's bandwidth

GLBP:
  Virtual IP: 192.168.1.1
  Active Virtual Gateway (AVG): Router A (manages the group)
  Active Virtual Forwarders (AVF): Router A, B, C, D (all forward traffic)
  Load distributed: ARP replies return different MAC addresses
  Better utilization: All routers forwarding simultaneously
```

---

## GLBP vs HSRP vs VRRP

| Aspect | GLBP | HSRP | VRRP |
| --- | --- | --- | --- |
| **Redundancy** | Yes (AVG election) | Yes (active/backup) | Yes (master/backup) |
| **Load Balancing** | Yes (multiple AVFs) | No (single active) | No (single master) |
| **Active Gateways** | Up to 4 | 1 | 1 |
| **Vendor** | Cisco only | Cisco only | Standards-based |
| **Failover Time** | ~3 seconds | ~3-10 seconds | ~3-10 seconds |
| **Virtual MACs** | Yes (multiple) | Yes (1 MAC) | Yes (1 MAC) |
| **Bandwidth Utilization** | High (load shared) | Low (one gateway) | Low (one gateway) |
| **Complexity** | Medium | Low | Low |

---

## GLBP Roles

### Active Virtual Gateway (AVG)

Elected leader that manages the GLBP group and assigns virtual MAC addresses to
forwarders.

```text
AVG responsibilities:

  - Manage the GLBP group (similar to HSRP active router)
  - Assign virtual MAC addresses to Active Virtual Forwarders (AVFs)
  - Send hellos (every 3 seconds default)
  - Elect a new AVG if current one fails

AVG election:

  - Highest priority value wins
  - If tied, highest router ID wins

Virtual MAC format:
  0000.07XX.XXYY
  XX = GLBP group number
  YY = AVF number (01, 02, 03, 04)
```

### Active Virtual Forwarder (AVF)

Router assigned to forward traffic for the virtual IP.

```text
AVF responsibilities:

  - Reply to ARP requests for the virtual IP
  - Forward traffic destined for the virtual IP
  - Send hellos to the AVG
  - Respond to ICMP pings to the virtual IP

Number of AVFs:

  - Up to 4 AVFs per GLBP group
  - Each gets a unique virtual MAC address
  - All advertise the same virtual IP

AVF election:

  - Highest priority in the group becomes primary AVF
  - If primary fails, secondary becomes active
  - Load balancing achieved by returning different MACs
```

### Secondary AVF

Backup forwarder that takes over if primary fails.

```text
Example: 4-router network with 4 AVFs
  Router A: Primary AVF (0000.0701.0001)
  Router B: Secondary AVF (0000.0701.0002)
  Router C: Secondary AVF (0000.0701.0003)
  Router D: Secondary AVF (0000.0701.0004)

If Router A fails:
  Router B becomes primary (0000.0701.0001)
  Remaining routers shift roles
```

---

## GLBP Load Balancing Methods

### Host-based Load Balancing (Default)

Hosts load-balance based on ARP replies. Each host learns a different MAC for the
virtual IP.

```text
Network: 4 hosts, 4 gateways with GLBP

Host 1 ARP request: "Who has 192.168.1.1?"
AVG replies: "MAC 0000.0701.0001" (Router A)

Host 2 ARP request: "Who has 192.168.1.1?"
AVG replies: "MAC 0000.0701.0002" (Router B)

Host 3 ARP request: "Who has 192.168.1.1?"
AVG replies: "MAC 0000.0701.0003" (Router C)

Host 4 ARP request: "Who has 192.168.1.1?"
AVG replies: "MAC 0000.0701.0004" (Router D)

Result: Traffic distributed across 4 gateways
Advantage: No per-flow balancing overhead
Disadvantage: Uneven if some hosts send more traffic
```

### Round-robin Load Balancing

AVG cycles through MAC addresses sequentially.

```text
ARP request 1: MAC 0000.0701.0001
ARP request 2: MAC 0000.0701.0002
ARP request 3: MAC 0000.0701.0003
ARP request 4: MAC 0000.0701.0004
ARP request 5: MAC 0000.0701.0001 (cycles back)
```

### Weighted Load Balancing

Assign weights to control how many ARP responses each forwarder gets.

```text
Router A: weight 50 (50% of ARP responses)
Router B: weight 30 (30% of ARP responses)
Router C: weight 20 (20% of ARP responses)

Result: Load proportional to assigned weights
```

---

## GLBP Failover Scenarios

### AVF Failure

If an Active Virtual Forwarder fails, secondary takes over.

```text
Scenario: Router A (primary AVF) fails

Before failure:
  Host 1 → Router A (0000.0701.0001)
  Host 2 → Router B (0000.0701.0002)
  Host 3 → Router C (0000.0701.0003)

After Router A fails:
  AVG assigns Router B as new primary AVF
  Router B takes MAC 0000.0701.0001
  Host 1 traffic redirected to Router B
  Host 2 traffic now uses Router C (MAC 0000.0701.0002)
```

### AVG Failure

New AVG is elected; load balancing continues.

```text
Scenario: Router A (AVG) fails

Before failure:
  Router A: AVG and primary AVF
  Router B: Primary AVF 2
  Router C: Secondary AVF 2
  Router D: Secondary AVF 3

After Router A fails:
  Router B elected as new AVG
  Router B remains primary AVF
  Router C promoted to primary AVF 2
  Router D remains secondary

Traffic impact: Minimal (only during AVG election, ~3 seconds)
```

---

## GLBP Design Patterns

### Pattern 1: Dual Gateway Load Balancing

Two gateways share load equally.

```text
        Virtual IP: 192.168.1.1

        Router A                Router B
     (AVG + AVF 1)           (Secondary)
         |                       |
    50% traffic             50% traffic
         |                       |
      Host 1                  Host 2
      Host 3                  Host 4

GLBP elected MAC:
  Host 1 → 0000.0701.0001 (Router A)
  Host 2 → 0000.0701.0002 (Router B)
  Host 3 → 0000.0701.0001 (Router A)
  Host 4 → 0000.0701.0002 (Router B)
```

### Pattern 2: Weighted Load Balancing (Multi-Speed Links)

Slower link gets less traffic.

```text
Router A: 1 Gbps link, weight 70 (70% traffic)
Router B: 100 Mbps link, weight 30 (30% traffic)

Result: Load balanced according to link capacity
```

### Pattern 3: Multi-Group GLBP

Multiple GLBP groups for redundancy across different subnets.

```text
GLBP Group 1: 192.168.1.1
  Router A: AVG + primary AVF
  Router B: Secondary AVF

GLBP Group 2: 192.168.2.1
  Router B: AVG + primary AVF
  Router A: Secondary AVF

Benefit: Each subnet's traffic load-balanced
         Cross-router redundancy
```

---

## GLBP Convergence

### Failure Detection

GLBP detects failures faster than HSRP/VRRP by default.

```text
Default timers:
  Hello: 3 seconds
  Hold: 10 seconds (must miss 3 hellos)

Total detection time: ~10 seconds

Fast timers (optional):
  Hello: 1 second
  Hold: 4 seconds

Total detection time: ~4 seconds

Faster detection = faster failover = less packet loss
```

### Convergence Example

```text
T=0s:     Router A fails
T=3s:     Router B detects failure (missed 1 hello)
T=10s:    AVG election complete
T=12s:    New AVG sends GLBP updates
T=13s:    All hosts learn new MAC addresses
T=15s:    Full convergence (traffic resumed)

Total outage: ~10-15 seconds (depends on how many hellos missed)
```

---

## Best Practices

| Practice | Reason |
| --- | --- |
| **Use 4 AVFs per group** | Maximum load balancing benefit |
| **Set equal priority if equal capacity** | Simplest and fairest distribution |
| **Weight links by capacity** | Match load to available bandwidth |
| **Monitor AVG elections** | High AVG churn = network instability |
| **Test failover regularly** | Ensure convergence is acceptable |
| **Use weighted load balancing** | Better than host-based if capacity varies |
| **Tune timers carefully** | Faster timers = more CPU, more messages |
| **Document group topology** | Complex with multiple groups |
| **Ensure AVG/AVF redundancy** | Every router should be both AVG and AVF candidate |
| **Don't mix GLBP with HSRP/VRRP** | Use one protocol per subnet |

---

## GLBP vs HSRP/VRRP Decision Matrix

| Scenario | Best Choice | Why |
| --- | --- | --- |
| Two routers, active/backup only | HSRP or VRRP | Simpler, less CPU, sufficient redundancy |
| Multiple routers, bandwidth utilization matters | GLBP | Load balancing justifies added complexity |
| Need standards-based solution | VRRP | Not vendor-locked |
| Cisco-only environment, equal capacity gateways | GLBP | Best load balancing |
| Asymmetric links (different speeds) | GLBP with weights | Optimal utilization |
| High-availability critical, simplicity important | HSRP | Proven, well-understood |

---

## Summary

- **GLBP** provides redundancy AND load balancing across multiple gateways
- **AVG** manages the group; **AVFs** forward traffic
- **Multiple MACs** for same VIP enable load distribution at ARP level
- **Up to 4 forwarders** per group, each getting unique virtual MAC
- **Better bandwidth utilization** than HSRP/VRRP since all gateways active
- **Faster convergence** (3 seconds default) than HSRP/VRRP
- **Cisco proprietary** — not available on other vendors
- **Complexity trade-off** — more features but more to configure and monitor

---

## See Also

- [HSRP/VRRP/GLBP Comparison](../theory/hsrp_vrrp_vs_glbp.md)
- [Cisco Gateway Redundancy Configuration](../cisco/cisco_hsrp_vrrp_glbp_config.md)
- [Gateway Redundancy & Failover](../theory/gateway_redundancy_fundamentals.md)
- [Cisco Interface Configuration](../cisco/cisco_interface_config.md)
- [Network Redundancy & High Availability](../operations/network_redundancy.md)
