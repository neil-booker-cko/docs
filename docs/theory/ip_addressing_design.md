# IP Addressing Design and Subnetting

Comprehensive guide to designing scalable, maintainable IP addressing schemes and
understanding CIDR, subnetting, aggregation, and summarization.

## IPv4 CIDR Fundamentals

### CIDR Notation

**CIDR (Classless Inter-Domain Routing)** specifies IP address and network size in a
single notation.

```text
192.168.1.0/24

Breakdown:

- 192.168.1.0 = Network address
- /24 = 24 bits for network, 8 bits for hosts
```

### Subnet Mask Conversion

| CIDR | Subnet Mask | Hosts | Typical Use |
| --- | --------- | --- | --------- |
| /30 | 255.255.255.252 | 2 | Point-to-point links (routers) |
| /29 | 255.255.255.248 | 6 | Small departments |
| /28 | 255.255.255.240 | 14 | Medium departments |
| /27 | 255.255.255.224 | 30 | Large departments |
| /26 | 255.255.255.192 | 62 | Floors, buildings |
| /25 | 255.255.255.128 | 126 | Divisional networks |
| /24 | 255.255.255.0 | 254 | Standard LAN (most common) |
| /23 | 255.255.254.0 | 510 | Multiple LANs |
| /22 | 255.255.252.0 | 1,022 | Campus subnet |
| /21 | 255.255.248.0 | 2,046 | Large campus |
| /20 | 255.255.240.0 | 4,094 | Regional office |
| /16 | 255.255.0.0 | 65,534 | Enterprise division |
| /8 | 255.0.0.0 | 16,777,214 | Entire organization |

### Usable Hosts

```text

Usable hosts = 2^(32 - prefix_length) - 2

/24: 2^(32-24) - 2 = 2^8 - 2 = 256 - 2 = 254 usable hosts
/25: 2^(32-25) - 2 = 2^7 - 2 = 128 - 2 = 126 usable hosts
/30: 2^(32-30) - 2 = 2^2 - 2 = 4 - 2 = 2 usable hosts (routers)

Note: Subtract 2 for network address (.0) and broadcast (.255)
```

---

## Subnetting Strategies

### Strategy 1: Hierarchical Subnetting (Recommended)

Divide address space top-down based on organizational structure.

```text

Organization: 10.0.0.0/8 (16 million addresses)
   ↓
Regions: /12 blocks (4,096 addresses each)
   10.0.0.0/12    ← Americas
   10.16.0.0/12   ← Europe
   10.32.0.0/12   ← Asia-Pacific

   ↓
Sites: /16 blocks (65k addresses each)
   10.0.0.0/16    ← HQ (Americas)
   10.1.0.0/16    ← Branch-1 (Americas)
   10.2.0.0/16    ← Branch-2 (Americas)
   10.16.0.0/16   ← London (Europe)

   ↓
Subnets: /24 blocks (254 hosts each)
   10.0.1.0/24    ← HQ Building A, Floor 1
   10.0.2.0/24    ← HQ Building A, Floor 2
   10.0.3.0/24    ← HQ Building B, VoIP
   10.0.4.0/24    ← HQ Building B, Video
```

**Advantages:**

- Easy to remember and document
- Supports routing aggregation (summarization)
- Scales to any organization size
- Clear logical boundaries

### Strategy 2: Flat Subnetting (Avoid for Large Networks)

Allocate /24 blocks sequentially without hierarchical structure.

```text

10.1.0.0/24    ← HQ Building A
10.2.0.0/24    ← Branch-1 Office
10.3.0.0/24    ← Branch-2 Office
10.4.0.0/24    ← Data Center
10.5.0.0/24    ← Branch-3 Office
...
```

**Problems:**

- Cannot summarize (each route announced separately)
- Routing table grows linearly
- No geographic logic
- Difficult to troubleshoot

---

## Supernetting and Aggregation

**Supernetting** combines multiple subnets into a single larger network. Used to reduce routing table
size.

### Aggregation Example

```text

Without aggregation (4 routes):
  10.0.1.0/24  → ISP-1
  10.0.2.0/24  → ISP-1
  10.0.3.0/24  → ISP-1
  10.0.4.0/24  → ISP-1

With aggregation (1 route):
  10.0.0.0/22  → ISP-1

Calculation: /22 covers 2^(32-22) = 1,024 addresses
Includes: 10.0.0.0 through 10.0.3.255
          (10.0.1.0, 10.0.2.0, 10.0.3.0, 10.0.4.0 all fit within /22)
```

### Aggregation Requirements

For aggregation to work, subnets must:

1. **Be contiguous** — No gaps in address space
2. **Align on power-of-2 boundaries** — Start address must be divisible by block size

**Example (NOT aggregatable):**

```text

10.0.0.0/24   ✓ aligned (0 is divisible by 256)
10.0.1.0/24   ✓ aligned (256 is divisible by 256)
10.0.2.0/24   ✓ aligned (512 is divisible by 256)
10.0.5.0/24   ✗ CANNOT aggregate (gap at 3, 4)
```

**Example (AGGREGATABLE):**

```text

10.0.0.0/24
10.0.1.0/24
10.0.2.0/24
10.0.3.0/24

All 4 are contiguous and aligned → can be summarized to 10.0.0.0/22
```

---

## Route Summarization in BGP

### Summarizing Routes in BGP

BGP advertises fewer, larger blocks instead of individual subnets.

```text

Router announces to BGP peers:
  10.0.0.0/22    ← summary of 10.0.0.0/24, 10.0.1.0/24, 10.0.2.0/24, 10.0.3.0/24
  Instead of:
  10.0.0.0/24
  10.0.1.0/24
  10.0.2.0/24
  10.0.3.0/24

Result:

- BGP table has 1 entry instead of 4
- Faster convergence
- Lower memory usage on all routers
```

### BGP Aggregate Configuration

```text

Cisco:
  router bgp 65000
    aggregate-address 10.0.0.0 255.255.252.0 [summary-only]

FortiGate:
  config router bgp
    config aggregate-address
      edit 1
        set prefix 10.0.0.0 255.255.252.0
      next
    end
  end

Result: BGP announces 10.0.0.0/22 as aggregate
        Individual /24 routes still used internally
```

---

## IPv6 Addressing

### IPv6 CIDR and Prefix Length

IPv6 uses same `/length` notation but with 128-bit addresses.

| CIDR | Prefix | Typical Use |
| --- | --------- | --- |
| /48 | Enterprise allocation | Entire organization (billions of addresses) |
| /56 | Site allocation | Single large site (billions of addresses) |
| /64 | Subnet allocation | Single LAN (18 quintillion addresses) |
| /80 | Subnetwork | Small segment |
| /127 | Point-to-point link | Router-to-router links |

### IPv6 Hierarchy

```text

2001:db8::/32   ← ISP allocation (entire organization)
   ↓
2001:db8:0::/48  ← HQ (organization's main allocation)
   ↓
2001:db8:0:1::/64  ← HQ Building A, Floor 1
2001:db8:0:2::/64  ← HQ Building A, Floor 2
2001:db8:0:3::/64  ← HQ Building B, VoIP

2001:db8:1::/48   ← Branch-1
   ↓
2001:db8:1:1::/64  ← Branch-1 Office
2001:db8:1:2::/64  ← Branch-1 Data Room
```

### IPv6 Aggregation (Same as IPv4)

```text

2001:db8:0:1::/64
2001:db8:0:2::/64
2001:db8:0:3::/64
2001:db8:0:4::/64

All contiguous and aligned → summarize to 2001:db8:0::/62
```

---

## Multi-Site IP Planning

### Pattern 1: Hierarchical (Region/Site/VLAN)

```text

Organization: 10.0.0.0/8

Region 1 (Americas): 10.0.0.0/10
   Site A (HQ): 10.0.0.0/16
      VLAN 1: 10.0.1.0/24
      VLAN 2: 10.0.2.0/24
      VLAN 3: 10.0.3.0/24

   Site B (Branch): 10.64.0.0/16
      VLAN 1: 10.64.1.0/24
      VLAN 2: 10.64.2.0/24

Region 2 (Europe): 10.64.0.0/10
   Site C (London): 10.64.0.0/16
      VLAN 1: 10.64.1.0/24
      VLAN 2: 10.64.2.0/24
```

**BGP Aggregation:**

- HQ announces 10.0.0.0/16
- Branch announces 10.64.0.0/16
- Europe announces 10.64.0.0/10 (summarizes both Europe sites)
- Entire organization announces 10.0.0.0/8

### Pattern 2: VLAN-Based (One Subnet Per VLAN)

```text

Organization: 10.0.0.0/16

VLAN 100 (Users): 10.0.100.0/24
VLAN 200 (Servers): 10.0.200.0/24
VLAN 300 (Storage): 10.0.30.0/24
VLAN 400 (Management): 10.0.40.0/24
```

**Advantage:** Simple; one subnet per VLAN
**Disadvantage:** No aggregation; all routes announced separately

---

## IP Planning Best Practices

| Best Practice | Reason |
| --- | --------- |
| **Use hierarchical design** | Enables aggregation; scales to large organizations |
| **Document the plan** | Prevents conflicts; facilitates capacity planning |
| **Use /24 for LANs** | Standard size; balances hosts vs efficiency |
| **Use /30 or /31 for router links** | Only 2-4 addresses needed; saves space |
| **Reserve address space** | Plan for 3-5 year growth |
| **Align subnets on boundaries** | Enables summarization in BGP |
| **Separate user/server/mgmt VLANs** | Simplifies security and policy |
| **Use private ranges (RFC 1918)** | Never use public addresses internally |
| **Plan IPv6 now** | Future-proof your network; /48 per organization |
| **Test aggregation** | Verify summary boundaries before production |

---

## Common Mistakes

### Mistake 1: Non-Contiguous Subnets

```text

Site A: 10.0.0.0/16
Site B: 10.2.0.0/16
Site C: 10.4.0.0/16

❌ CANNOT summarize (gaps at 10.1, 10.3)
✓ SHOULD have used: 10.0.0.0/14 (covers 10.0.0.0 to 10.3.255.255)
                   Then subdivide: 10.0.0.0/16, 10.1.0.0/16, 10.2.0.0/16, 10.3.0.0/16
```

### Mistake 2: Misaligned Subnets

```text

10.0.1.0/24   ✗ Starts at 1 (not divisible by 2)
10.0.2.0/24   ✗ Starts at 2 (not divisible by 4)
10.0.4.0/24   ✓ Starts at 4 (divisible by 4)
10.0.8.0/24   ✓ Starts at 8 (divisible by 8)

❌ Cannot aggregate 10.0.1.0 and 10.0.2.0
✓ Can aggregate 10.0.4.0 and 10.0.8.0 to 10.0.4.0/23
```

### Mistake 3: Too Many Routes in BGP

```text

Organization announces 500 individual /24 routes

❌ Problem:

- BGP route processor overhead
- Slow convergence
- Difficult to summarize later
- Internet routers carry unnecessary entries

✓ Solution:

- Design IP plan with aggregation in mind
- Announce 50 /20 blocks instead of 500 /24 routes
- 10× reduction in routing table
```

---

## Capacity Planning Example

### 5-Year Growth Plan

```text

Year 1: 50 sites × 5 VLANs × 200 hosts = 50,000 addresses
Year 3: 100 sites × 8 VLANs × 300 hosts = 240,000 addresses
Year 5: 150 sites × 10 VLANs × 400 hosts = 600,000 addresses

Required address space: 600k → need /11 (2 million addresses)
Allocate: 10.0.0.0/11 (plenty of room for growth)
```

---

## IPv4 vs IPv6 Transition

### Dual-Stack Strategy

Run both IPv4 and IPv6 simultaneously.

```text

Interface: GigabitEthernet0/1
  IPv4: 10.0.1.1/24
  IPv6: 2001:db8:0:1::1/64

Both protocols active; clients choose what to use
```

### IPv6 Deployment Plan

```text

Year 1: Allocate /48 from ISP
Year 2: Configure infrastructure (routers, core)
Year 3: Deploy to sites (dual-stack)
Year 4: Gradually phase out IPv4 (or keep for legacy)
```

---

## Summary

- **CIDR notation** (`/24`, `/16`) specifies network size
- **Hierarchical design** enables aggregation and scales
- **Supernetting** reduces routing table size
- **BGP aggregation** announces summaries instead of individual routes
- **IPv6 uses same logic** as IPv4 but with 128-bit addresses
- **Plan for growth** and ensure subnets are aligned for future summarization
- **Document everything** to prevent conflicts and facilitate capacity planning
