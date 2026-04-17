# FortiGate Policy-Based Routing Configuration Guide

Complete reference for implementing policy-based routing on Fortinet FortiGate.

## Quick Start: Basic PBR

```text
config router policy
  edit 1
    set input-device "port1"
    set src "10.0.0.0/24"
    set dst "any"
    set protocol "ip"
    set gateway "192.168.1.254"
  next
end
```

---

## Policy-Based Routing Components

### Input Interface

Specifies which interface incoming traffic arrives on.

```text

config router policy
  edit 1
    set input-device "port1"  ! Apply to traffic entering port1
    ! Only traffic arriving on port1 will be evaluated
  next
end
```

### Source Address

Traffic matching this source IP/subnet.

```text

config address
  edit "Internal-Subnet"
    set subnet 10.0.0.0 255.255.255.0
  next
end

config router policy
  edit 1
    set src "Internal-Subnet"
    ! Or use "10.0.0.0 255.255.255.0" directly
  next
end
```

### Destination Address

Traffic destined for this IP/subnet (optional; "any" = all destinations).

```text

config router policy
  edit 1
    set dst "any"  ! All destinations
    ! Or specific: set dst "external-server"
  next
end
```

### Protocol

Specify which protocols to match (IP, TCP, UDP, etc.).

```text

config router policy
  edit 1
    set protocol "ip"    ! All IP protocols
    ! Or: "tcp", "udp", etc.
  next
end
```

### Gateway (Next-hop)

Route via this gateway IP.

```text

config router policy
  edit 1
    set gateway "192.168.1.254"  ! Route via this IP
  next
end
```

---

## Complete PBR Configuration Example

### Scenario: Multi-ISP Load Balancing

```text

Internal: 10.0.0.0/24

ISP-1: gateway 200.1.1.1 (quality link)
ISP-2: gateway 200.2.1.1 (cost-effective link)

Requirement:

  - Traffic from 10.0.1.0/25 → ISP-1
  - Traffic from 10.0.1.128/25 → ISP-2
  - VoIP → ISP-1 (high priority)
```

**Configuration:**

```text

config address
  edit "subnet-1"
    set subnet 10.0.1.0 255.255.255.128
  next

  edit "subnet-2"
    set subnet 10.0.1.128 255.255.255.128
  next

  edit "isp-1-gateway"
    set subnet 200.1.1.1 255.255.255.255
  next

  edit "isp-2-gateway"
    set subnet 200.2.1.1 255.255.255.255
  next
end

config router policy
  ! Policy 1: Subnet 1 → ISP-1 (priority 1, evaluated first)
  edit 1
    set input-device "vlan100"
    set src "subnet-1"
    set dst "any"
    set protocol "ip"
    set gateway "200.1.1.1"
    set comments "Subnet 1 to ISP-1"
  next

  ! Policy 2: Subnet 2 → ISP-2 (priority 2)
  edit 2
    set input-device "vlan100"
    set src "subnet-2"
    set dst "any"
    set protocol "ip"
    set gateway "200.2.1.1"
    set comments "Subnet 2 to ISP-2"
  next

  ! Policy 3: VoIP to ISP-1 (priority 3, matches SIP port)
  edit 3
    set input-device "vlan100"
    set src "10.0.0.0 255.255.0.0"  ! Any internal IP
    set dst "any"
    set protocol "tcp"
    set service "SIP"  ! or specific port 5060
    set gateway "200.1.1.1"
    set comments "VoIP to ISP-1 (quality link)"
  next
end
```

---

## Matching by Service (Protocol/Port)

### Match Specific Protocols

```text

config firewall service custom
  edit "VoIP-SIP"
    set protocol TCP
    set tcp-portrange 5060
  next

  edit "VoIP-RTP"
    set protocol UDP
    set udp-portrange 10000-11000
  next
end

config router policy
  edit 1
    set src "any"
    set dst "any"
    set service "VoIP-SIP" "VoIP-RTP"
    set gateway "200.1.1.1"  ! Quality ISP for VoIP
  next
end
```

### Match by Protocol Type

```text

config router policy
  ! HTTP (port 80)
  edit 1
    set protocol "tcp"
    set service "HTTP"
    set gateway "200.2.1.1"  ! Cost-effective ISP for web
  next

  ! HTTPS (port 443)
  edit 2
    set protocol "tcp"
    set service "HTTPS"
    set gateway "200.2.1.1"
  next
end
```

---

## Advanced: Output Interface Selection

### Explicit Outgoing Interface

```text

config router policy
  edit 1
    set input-device "vlan100"
    set src "10.0.0.0/24"
    set dst "any"
    set output-device "port1"  ! Force traffic out this interface
  next
end
```

---

## PBR with DSCP Marking

### Mark Traffic with QoS

```text

config router policy
  edit 1
    set src "10.0.1.0/25"
    set dst "any"
    set gateway "200.1.1.1"

    ! Mark outgoing traffic with DSCP EF (voice)
    set dscp-forward enable
    set dscp-forward-value "EF"
  next
end
```

---

## Verification and Monitoring

### Check PBR Policies

```text

get router policy

! Shows all configured policies and their settings
```

### Monitor PBR Hit Counts

```text

get router policy summary

! Shows traffic statistics per policy:
! - bytes/packets forwarded
! - hit count (how many times matched)
```

### Check Specific Policy

```text

get router policy 1

! Detailed information about policy 1
```

### Verify Traffic Routing

```text

execute traceroute 8.8.8.8 -a 10.0.1.5

! Traceroute from source 10.0.1.5
! Should show ISP-1 gateway as first hop (if policy matched)
```

### Debug PBR Processing

```text

diagnose debug reset
diagnose debug enable
diagnose debug flow filter addr 10.0.1.5
diagnose debug flow trace start 100

! Send test traffic from 10.0.1.5
! Debug output shows policy evaluation

diagnose debug flow trace stop
```

---

## Common Issues and Fixes

### Issue: PBR Not Being Applied

**Cause:** Policy not matching incoming interface, or gateway unreachable.

**Check:**

```text

get router policy summary

! Verify hit count is increasing
! If 0 hits, policy not matching
```

**Fix:**

```text

config router policy
  edit 1
    set input-device "vlan100"  ! Verify correct interface
    set src "10.0.0.0/24"
    set gateway "200.1.1.1"  ! Verify gateway is reachable
  next
end
```

### Issue: Gateway Unreachable

**Cause:** Specified next-hop is down or not routable.

**Check:**

```text

execute ping 200.1.1.1

! Verify gateway is reachable
```

**Troubleshoot:**

```text

get router info routing-table static

! Verify route to gateway exists
```

**Solution:** Add backup gateway or health check.

```text

config router policy
  edit 1
    set src "10.0.0.0/24"
    set gateway "200.1.1.1"
    set secondary-gateway "200.2.1.1"  ! Failover
  next
end
```

### Issue: Asymmetric Routing (Return Traffic Takes Different Path)

**Cause:** Return traffic doesn't match PBR; takes default route via different ISP.

```text

Outbound (internal → external):
  PBR routes via ISP-1 (200.1.1.1)

Return (external → internal):
  External routers send back via default route
  Default might be ISP-2 (200.2.1.1)

Result: Return traffic via different ISP; possible rejects due to source IP filtering
```

**Solution:** Add reverse PBR policy for return traffic.

```text

config address
  edit "external-networks"
    set subnet 0.0.0.0 0.0.0.0  ! All external IPs
  next
end

config router policy
  edit 10
    set input-device "port1"  ! Incoming from ISP-1
    set src "external-networks"
    set dst "10.0.0.0 255.255.255.0"  ! Back to internal
    set gateway "internal-gateway"  ! Route back via same ISP
  next
end
```

### Issue: Traffic Not Being Prioritized

**Cause:** DSCP marking not enabled, or upstream routers not respecting DSCP.

**Check:**

```text

get firewall policy  ! Check if QoS traffic-shaper is applied

get router policy 1  ! Check if dscp-forward is enabled
```

**Fix:**

```text

config router policy
  edit 1
    set dscp-forward enable
    set dscp-forward-value "EF"  ! Mark as voice priority
  next
end
```

---

## Best Practices

| Practice | Reason |
| --- | --------- |
| **Use for small networks (<10 sites)** | Scales better with BGP beyond that |
| **Document each policy** | Facilitate troubleshooting and changes |
| **Order policies by priority** | Lower edit ID = higher priority (evaluated first) |
| **Test before production** | Verify return traffic works correctly |
| **Add secondary gateway** | Automatic failover if primary is down |
| **Monitor hit counts** | Ensure policies are actually matching |
| **Combine with firewall policies** | PBR for routing; policies for allow/deny |
| **Enable DSCP marking** | QoS depends on DSCP if downstream routers support it |
| **Use with static routes** | BGP for dynamic routing; PBR for policy routing |

---

## Configuration Checklist

- [ ] Define address objects for sources/destinations
- [ ] Create service objects for protocol/port matching (if needed)
- [ ] Create PBR policies with correct priorities
- [ ] Specify input interface for each policy
- [ ] Set gateway (next-hop) for each policy
- [ ] Enable DSCP marking if QoS needed
- [ ] Verify policies are applied (`get router policy`)
- [ ] Test traffic from different sources
- [ ] Verify return traffic works (no asymmetry)
- [ ] Add secondary gateway for failover
- [ ] Monitor hit counts regularly
- [ ] Document policies and gateways

---

## Quick Reference

```text

! Create address objects
config address
  edit "subnet-1"
    set subnet 10.0.1.0 255.255.255.128
  next
end

! Create router policy
config router policy
  edit 1
    set input-device "vlan100"
    set src "subnet-1"
    set dst "any"
    set gateway "200.1.1.1"
    set dscp-forward enable
    set dscp-forward-value "EF"
  next
end

! Verify
get router policy
get router policy summary
execute ping 200.1.1.1
```
