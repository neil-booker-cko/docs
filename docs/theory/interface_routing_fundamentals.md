# Interface and Routing Fundamentals

Essential concepts for configuring interfaces and basic routing on network devices.

---

## At a Glance

| Concept | Purpose | Key Attribute | Example |
| --- | --- | --- | --- |
| **Physical Interface** | Direct cable connection | Speed, duplex, MTU | Gi0/0/1 (1 Gbps) |
| **Virtual Interface (VLAN)** | Logical grouping on switch | VLAN ID; L2 broadcast domain | VLAN 100 (IP 10.0.100.1) |
| **Loopback Interface** | Always-up virtual interface | Used for routing source/management | Lo0 (10.0.0.1 management) |
| **Tunnel Interface** | Encapsulated connection | Protocol (GRE, IPsec); endpoints | Tunnel0 (GRE 10.0.0.1→20.0.0.1) |
| **Subinterface** | VLAN per physical port | VLAN tag (802.1Q); IP per tag | Gi0/0.100 (VLAN 100) |
| **Port Channel** | Aggregated links | Load balancing algo (hash-based) | Po1 (Gi0/0-1 bundled) |
| **Default Route** | Route to unknown destinations | Metric; next-hop | 0.0.0.0/0 → 10.0.0.1 |
| **Routing Table** | All known routes | Prefix; next-hop; metric | 192.168.1.0/24 → 10.0.0.1 |

---

## Network Interfaces

### Interface Types

| Type | Purpose | Example |
| --- | --------- | --- |
| **Physical (Ethernet)** | Direct connection to network cable | Ethernet0, GigabitEthernet0/1 |
| **Virtual (VLAN)** | Logical interface on switch; bridges physical ports | VLAN100, VLAN1 |
| **Loopback** | Virtual interface (always up); used for routing/management | Lo0, Loopback0 |
| **Tunnel** | Encapsulated connection across internet | Tunnel0, gre-tunnel1 |
| **Subinterface** | Logical sub-interface for VLANs | Gi0/1.100, eth0.200 |
| **Port Channel** | Aggregation of multiple physical ports | Po1, Bond0 |

### Interface States

Every interface has two states:

| State | Meaning | Can forward traffic? |
| --- | --------- | --- |
| **Up** | Physical link active AND line protocol up | ✓ Yes |
| **Down** | Physical link inactive OR line protocol down | ✗ No |
| **Administratively Down** | Manually disabled by admin | ✗ No |

```text
Example interface states:
  GigabitEthernet0/1 is up, line protocol is up
    → Physical link connected AND IP configured correctly

  GigabitEthernet0/2 is down, line protocol is down
    → No cable connected OR cable failure

  GigabitEthernet0/3 is administratively down, line protocol is down
    → Admin ran "shutdown" command
```

---

## IP Addressing Basics

### IPv4 Address Components

Every interface needs:

1. **IP Address**: Unique identifier in a subnet (e.g., 192.168.1.10)
1. **Subnet Mask**: Defines which portion is network, which is host (e.g., 255.255.255.0 or /24)
1. **Default Gateway**: Router to send traffic destined for other networks

### Subnet Mask Notation

| Notation | CIDR | Hosts | Usage |
| --- | --------- | --- | --------- |
| 255.255.255.0 | /24 | 254 | Standard LAN subnet |
| 255.255.255.128 | /25 | 126 | Small departments |
| 255.255.255.192 | /26 | 62 | Very small LANs |
| 255.255.0.0 | /16 | 65,534 | Large networks |
| 255.255.255.255 | /32 | 1 | Host routes, loopbacks |

### IP Address Types

- **Unicast**: Traffic to single host (192.168.1.10)
- **Broadcast**: Traffic to all hosts in subnet (192.168.1.255)
- **Multicast**: Traffic to group of hosts (224.0.0.1)
- **Loopback**: Virtual address (127.0.0.1 for local, 10.0.0.1 for routing)

---

## Routing Fundamentals

### Routing Decision

When a packet arrives at an interface, the router:

1. **Extract destination IP** from packet
1. **Lookup routing table** for matching destination
1. **Forward via next-hop** (or default route if no match)
1. **Decrement TTL** and forward to egress interface

```text

Example routing decision:

Packet arrives with DST=10.0.0.5

Routing table:
  10.0.0.0/24     → Next-hop 192.168.1.1 (match!)
  172.16.0.0/16   → Next-hop 192.168.1.2
  0.0.0.0/0       → Next-hop 192.168.1.254 (default)

Decision: Forward to 192.168.1.1 via exit interface GigabitEthernet0/1
```

### Routing Table Entry

Each entry contains:

| Field | Example | Meaning |
| --- | --------- | --- |
| **Destination Network** | 10.0.0.0/24 | Packets with DST in this range... |
| **Next-hop IP** | 192.168.1.1 | ...are sent to this address |
| **Metric** | 100 | Cost of path (lower = preferred) |
| **Administrative Distance** | 110 | Trust level (lower = more trusted) |
| **Egress Interface** | GigabitEthernet0/1 | Physical port to send packet out |

### Static vs Dynamic Routing

| Aspect | Static | Dynamic |
| --- | --------- | --- |
| **Setup** | Manual route entry | Automatic via protocol (BGP, OSPF) |
| **Scalability** | Small networks only | Large networks |
| **Convergence** | Manual intervention | Automatic in seconds |
| **Overhead** | Minimal | More CPU/bandwidth |
| **Use case** | Test networks, default routes | Production networks |

**Example Static Route:**

```text

Network: 10.0.0.0/24
Next-hop: 192.168.1.1
Result: All traffic for 10.0.0.0/24 goes via 192.168.1.1
```

**Example Dynamic Route (OSPF):**

```text

OSPF learns: 10.0.0.0/24 reachable via 192.168.1.1
If link fails, OSPF recalculates and finds alternate path
All routers update routing tables automatically
```

---

## Interface Configuration Workflow

### Step 1: Assign IP Address

```text

Cisco:
  interface GigabitEthernet0/1
    ip address 192.168.1.1 255.255.255.0

FortiGate:
  config system interface
    edit "port1"
      set ip 192.168.1.1 255.255.255.0
```

### Step 2: Enable Interface

```text

Cisco:
  interface GigabitEthernet0/1
    no shutdown

FortiGate:
  config system interface
    edit "port1"
      set status up
```

### Step 3: Verify Status

```text

Cisco:
  show interface GigabitEthernet0/1

FortiGate:
  get system interface port1
```

---

## Default Route

A **default route** handles all packets with no specific routing table match.

### Why Default Routes?

Without a default route:

- All unmatched traffic is dropped
- Requires explicit route for every possible destination

With default route:

- Unmatched traffic forwarded to ISP or core network
- Single route covers all "everything else"

### Configuration

```text

Cisco:
  ip route 0.0.0.0 0.0.0.0 192.168.1.254

Meaning: All traffic (0.0.0.0/0) → next-hop 192.168.1.254

FortiGate:
  config router static
    edit 1
      set destination 0.0.0.0 0.0.0.0
      set gateway 192.168.1.254
      set device "port1"
```

---

## Loopback Interfaces

A **loopback** is a virtual interface that never goes down (as long as the router is running).

### Use Cases

1. **Router ID**: OSPF and BGP use loopback as router identifier
1. **Management**: Telnet/SSH to loopback (works even if physical link fails)
1. **Testing**: Source/sink for test traffic
1. **Route redistribution**: Stable address for announcing services

### Configuration

```text

Cisco:
  interface Loopback0
    ip address 10.0.0.1 255.255.255.255

FortiGate:
  config system interface
    edit "loopback"
      set type loopback
      set ip 10.0.0.1 255.255.255.255
```

### Router ID Selection

Most routing protocols pick router ID in this order:

1. Manually configured router ID
1. Highest loopback IP address
1. Highest physical interface IP address

**Best practice:** Manually set router ID to loopback IP.

```text

Cisco:
  router bgp 65000
    bgp router-id 10.0.0.1

Cisco OSPF:
  router ospf 1
    router-id 10.0.0.1
```

---

## Interface Configuration Best Practices

| Best Practice | Reason |
| --- | --------- |
| Use descriptive interface names/descriptions | Troubleshooting clarity |
| Set IP on loopback for router ID | Stable, never-down address |
| Use static IP internally, DHCP on access | Predictable core, flexible edges |
| Enable all interfaces; use ACLs for policy | Easier troubleshooting than disabled ports |
| Document IP plan | Prevents conflicts, enables capacity planning |
| Use /32 for loopbacks, /24+ for subnets | Subnetting efficiency |
| Assign addresses in logical blocks | Easier summarization and design |
| Test connectivity with ping/traceroute | Verify routing before production |

---

## Troubleshooting Checklist

| Check | Command | Look for |
| --- | --------- | --- |
| Interface is up | `show int status` | "Up" state |
| IP address configured | `show int brief` | IP address present |
| Default route exists | `show ip route` | 0.0.0.0/0 entry |
| Can reach gateway | `ping <gateway-ip>` | Replies received |
| TTL not the issue | Traceroute | Hops count down |
| No ACL blocking | `show ip access-list` | No implicit deny |

---

## Summary

- **Interfaces** must be up, have IP address, and be connected
- **Routing table** maps destinations to next-hops
- **Static routes** work for small networks; use for defaults and testing
- **Dynamic routing** (BGP, OSPF) scales to large networks
- **Loopback** provides stable management and router ID
- **Default route** (0.0.0.0/0) catches all unmatched traffic
- **Verify** connectivity with ping/traceroute before production deployment

---

## See Also

- [IP Addressing Design](../theory/ip_addressing_design.md) — Subnetting strategies and address planning
- [Switching Fundamentals](../theory/switching_fundamentals.md) — VLANs and broadcast domains
- [Static vs Dynamic Routing](../theory/static_vs_dynamic_routing.md) — Choosing a routing strategy
- [Cisco Interface Configuration](../cisco/cisco_interface_config.md) — IOS-XE interface setup
- [OSPF Fundamentals](../theory/ospf_fundamentals.md) — Dynamic routing on interfaces
