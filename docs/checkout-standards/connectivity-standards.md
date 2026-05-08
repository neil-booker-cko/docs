# Connectivity Standards

Standards for datacenter interconnection, cloud provider connectivity, and internet access patterns.

---

## Design Principles

All datacenter-to-cloud and datacenter-to-internet connectivity follows these principles:

- **Fast Failover:** Deploy dual redundant paths with BFD for sub-second detection
- **BGP-Driven:** Use BGP for dynamic routing and traffic engineering
- **Prefix Filtering:** Apply strict ingress/egress filtering to prevent route hijacking
- **Route Manipulation:** Use Local Preference (outbound) and AS Path Prepending (inbound) for steering
- **Logging:** Enable logging on all policies and BGP state changes for troubleshooting

---

## ISP Internet Connectivity

### Design Pattern

**Dual ISP connections with BGP and BFD:**

- Primary and secondary ISP links with independent BGP peerings
- Local Preference used to steer outbound traffic via preferred ISP
- AS Path Prepending used to steer inbound traffic from preferred ISP
- BFD enabled for fast failure detection (200ms interval, 3 retry count)
- Bogon filtering on ingress interfaces

### Configuration Components

**Interface Configuration:**

- Enable BFD with 200ms intervals
- Disable CDP and LLDP for security
- Apply bogon ACL to inbound traffic
- Configure speed and load monitoring

**BGP Configuration:**

- Log neighbor state changes
- Configure BGP password (MD5) for security
- Enable BFD fallover for fast failover
- Apply route-maps for Local Preference and AS Path manipulation
- Limit received prefixes to 1 (expect only default route from ISP)

**Prefix Filtering:**

- Define local public IP range in prefix-list (to advertise outbound)
- Define default route prefix-list (to receive inbound)

**Route Manipulation:**

- **Inbound:** Primary ISP receives Local Preference 200; Secondary receives 150
- **Outbound:** Secondary ISP receives AS Path Prepend (×2) to discourage inbound

**Security Filtering:**

- Apply ACL to filter bogon (invalid) IP ranges
- Blocks RFC1918, loopback, multicast, documentation ranges

### Reference

See [Configuration Standard - ISP Connectivity](../checkout-standards/connectivity-standards.md)
for full configuration examples.

---

## AWS Direct Connect (Switch to TGW)

### Design Pattern

**Cisco Switch to AWS TGW via AWS Direct Connect:**

- BGP session between network switch and AWS Direct Connect Gateway (DXGW)
- BFD enabled for sub-second failover (300ms intervals)
- OSPF used between switch and firewall (gateway protocol)
- Route redistribution between BGP (to AWS) and OSPF (to firewall)
- Dedicated VRF for AWS routing

### Configuration Components

**Layer 3 Handoff (Switch to FW):**

- Dedicated VLAN (example: 601) for handoff subnet
- IPv4 address assigned from handoff subnet
- OSPF authentication (MD5) for routing security
- Firewall elected as OSPF DR (priority 255)

**BGP Configuration (Switch to AWS):**

- BGP AS number unique per datacenter
- BGP router-id set to handoff subnet IP
- Advertise only the local prefix (firewall handoff subnet)
- Receive AWS TGW subnets; filter via prefix-list
- Apply route-maps for Local Preference steering
- Soft reconfiguration enabled for faster policy changes

**OSPF Configuration (Switch to FW):**

- OSPF process number matches BGP AS for consistency
- Confined to handoff subnet (single area per DC)
- Passive interfaces by default; activate only on handoff
- BGP routes redistributed into OSPF

**Prefix Filtering:**

- Local prefix-list: handoff subnet CIDR
- Remote prefix-list: AWS TGW CIDR block

**Route Manipulation:**

- Primary link: Local Preference 200
- Secondary link: Local Preference 150 (+ AS Path Prepend ×1 on outbound)

### Reference

See [Configuration Standard - AWS Connectivity (Switch/Direct Connect)](../checkout-standards/connectivity-standards.md)
for full Cisco and FortiGate examples.

---

## AWS Firewall-to-TGW VPN

### Design Pattern

**Firewall-based VPN to AWS TGW when Direct Connect unavailable:**

- IPsec tunnels (dual redundancy) from firewall to AWS VPN endpoints
- IKEv2 with strong encryption (AES-256-GCM or AES-256-CBC)
- BGP over IPsec for dynamic routing (failover support)
- Static route to local DC CIDR (as backup/blackhole route)
- Route redistribution from BGP to firewall policy routing

### IPsec Configuration

- **Phase 1:** IKEv2, AES256-SHA256, DH Group 19, 28800s (8hr) key lifetime
- **Phase 2:** AES256-SHA256, DH Group 19 (PFS), 3600s (1hr) key lifetime
- **DPD:** On-demand with 20s retry interval

### BGP Configuration

- BGP AS unique per datacenter
- Router-id set to firewall management interface IP
- Peers: AWS VPN endpoint BGP addresses
- Network statement: local DC CIDR block
- Keepalive/hold timers: 10/30 seconds (tight monitoring)
- Soft reconfiguration enabled
- Graceful restart enabled

### Route Filtering

- **Inbound:** Deny default route (blackhole), deny other DC AS numbers
- **Outbound:** Permit only local DC CIDR block

### Static Route Backup

- Route to local DC CIDR pointing to Null0 (blackhole)
- Distance 250 (lower priority than BGP route)
- Acts as failsafe if BGP routing fails

### Reference

See [Configuration Standard - AWS Connectivity (Firewall to TGW VPN)](../checkout-standards/connectivity-standards.md)
for full configuration examples.

---

## Multi-Site Design (Hub-and-Spoke)

### Hub (Primary Datacenter)

- Advertises all internal DC prefixes to spoke sites via BGP/VPN
- Receives spoke-site prefixes from each spoke
- Acts as gateway for inter-spoke communication

### Spokes (Remote Sites/Secondary DCs)

- Advertise only their local prefixes to hub
- Receive hub and all other spoke prefixes from hub
- Inter-spoke communication routes through hub

### Prefix Advertisement Policy

| Direction | Advertise | Receive | Route Map |
| --- | --- | --- | --- |
| Hub → Spoke | Hub + all DC subnets | Spoke subnets only | INBOUND-FILTER |
| Spoke → Hub | Spoke subnets only | Hub + all other spokes | OUTBOUND-FILTER |

### Failover Behavior

- Primary link failure triggers BFD detection → immediate BGP failover
- Secondary link takes over within 300ms
- BGP timers ensure route convergence within 90-120 seconds

---

## Testing and Validation Checklist

Before deploying any connectivity:

- [ ] BGP session established and showing as "Established"
- [ ] Received correct number and type of routes
- [ ] Advertised correct local subnets
- [ ] BFD status "Up" on both directions
- [ ] Bidirectional ping test across tunnel/link succeeds
- [ ] Failover test: kill primary, verify secondary takes over
- [ ] Convergence time verified (should be <300ms with BFD)
- [ ] Logging enabled and functioning
- [ ] Prefix filtering validated (unexpected routes denied)

---

## Related Standards

- [BGP Standards](bgp-standards.md)
- [VPN Standards](vpn-standards.md)
- [Security Hardening](security-hardening.md)
- [Routing Design](routing-design.md)
