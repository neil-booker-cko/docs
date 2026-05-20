# DHCP Standards

FortiGate acts as the DHCP server for all office sites. Each VLAN interface has its own DHCP
scope. Datacenter subnets use static addressing throughout — no DHCP in DC environments.

---

## Lease Time Standards

| Network Type | Lease Time | Seconds | Rationale |
| --- | --- | --- | --- |
| Corporate (data, mgmt, AP, server) | 24 hours | 86400 | Stable endpoints; reduces churn |
| Guest / IoT / high-density | 8 hours | 28800 | Higher turnover; reclaim addresses faster |

---

## DNS Service Settings

| Value | Behaviour | Use Case |
| --- | --- | --- |
| `dns-service local` | FortiGate serves DNS; resolves local zone records | Corporate VLANs |
| `dns-service default` | System DNS servers (external resolvers) | Guest VLANs |
| `dns-service specify` | Explicit DNS server IPs per scope | Where override is needed |

---

## IP Range Conventions

- **Reserve .1–.9** for infrastructure (default gateway, DNS, NTP, network address)
- Start DHCP ranges at `.10` for small subnets or as appropriate for larger subnets
- For large scopes spanning multiple /24 boundaries, define multiple `ip-range` blocks to
  avoid assigning the gateway address or other reserved IPs

---

## Corporate VLAN Scope (Standard)

```fortios
config system dhcp server
    edit <SCOPE_ID>
        set lease-time 86400
        set dns-service local
        set default-gateway <VLAN_GATEWAY_IP>
        set netmask <SUBNET_MASK>
        set interface "<VLAN_INTERFACE>"
        config ip-range
            edit 1
                set start-ip <RANGE_START>
                set end-ip <RANGE_END>
            next
        end
    next
end
```

**Example — single /24 (VLAN 50):**

```fortios
config system dhcp server
    edit 2
        set lease-time 86400
        set dns-service local
        set default-gateway 172.16.50.1
        set netmask 255.255.255.0
        set interface "x2.50"
        config ip-range
            edit 1
                set start-ip 172.16.50.10
                set end-ip 172.16.50.250
            next
        end
    next
end
```

---

## Large Subnet Scope (Multiple Ranges)

For subnets larger than /24, define multiple `ip-range` blocks if the gateway IP falls within
the range, or to split the allocation across the address space.

**Example — /19 with two ranges to span gateway boundary (VLAN 100):**

```fortios
config system dhcp server
    edit 12
        set lease-time 28800
        set dns-service default
        set default-gateway 192.168.100.1
        set netmask 255.255.224.0
        set interface "x2.100"
        config ip-range
            edit 1
                set start-ip 192.168.96.10
                set end-ip 192.168.99.250
            next
            edit 2
                set start-ip 192.168.100.10
                set end-ip 192.168.103.250
            next
        end
    next
end
```

---

## DHCP Reservations (Static Assignment by MAC)

Use reserved addresses to assign a fixed IP to a specific device without full static
configuration on the endpoint.

```fortios
config system dhcp server
    edit <SCOPE_ID>
        ...
        config reserved-address
            edit 1
                set ip <RESERVED_IP>
                set mac <MAC_ADDRESS>
            next
        end
    next
end
```

**Example:**

```fortios
config system dhcp server
    edit 9
        set lease-time 28800
        set dns-service local
        set default-gateway 172.16.20.1
        set netmask 255.255.240.0
        set interface "x2.20"
        config ip-range
            edit 1
                set start-ip 172.16.20.10
                set end-ip 172.16.25.250
            next
        end
        config reserved-address
            edit 1
                set ip 172.16.24.52
                set mac 9c:93:4e:90:1e:a4
            next
        end
    next
end
```

---

## Scope ID Numbering

Scope IDs (`edit <n>`) are arbitrary integers — they do not need to match VLAN numbers. Assign
sequentially or use a site-specific numbering scheme. Each scope must have a unique ID within
the DHCP server config.

---

## Cisco IOS-XE DHCP Snooping

DHCP snooping prevents rogue DHCP servers on the network by trusting only designated uplink
interfaces. All access ports are untrusted by default — any DHCP offer arriving on an untrusted
port is dropped.

### Global Configuration

Enable snooping on all VLANs that contain DHCP clients. The `no ip dhcp snooping information
option` line disables Option 82 insertion — FortiGate does not expect relay agent information
since it is directly serving these VLANs, and injecting Option 82 causes DHCP requests to be
discarded.

```ios
ip dhcp snooping vlan <VLAN_LIST>
no ip dhcp snooping information option
ip dhcp snooping
```

### Trusted Interfaces

Mark uplink interfaces towards the DHCP server (firewall) as trusted. All other interfaces
(access ports, user-facing trunks) remain untrusted.

**Access switch — uplink trunk towards core switch:**

```ios
interface <UPLINK_INTERFACE>
 ip dhcp snooping trust
!
```

**Core switch — interfaces towards the FortiGate firewall:**

```ios
interface <FIREWALL_UPLINK_INTERFACE>
 ip dhcp snooping trust
!
```

**Note:** If the uplink is a port-channel (LAG), apply `ip dhcp snooping trust` to the
port-channel interface, not the individual member interfaces.

### Full Access Switch Example

```ios
ip dhcp snooping vlan 10,20,40,100,200,202,400
no ip dhcp snooping information option
ip dhcp snooping

interface TwentyFiveGigE1/1/1
 description LON1-CSW-01_Tw1/0/4
 switchport mode trunk
 switchport nonegotiate
 switchport trunk native vlan 999
 switchport trunk allowed vlan 10,20,30,40,50,60,100,200,204,400
 channel-group 1 mode active
 lacp rate fast
 ip dhcp snooping trust
!
```

---

## Troubleshooting

```fortios
diagnose sys dhcp server list
diagnose sys dhcp server status <SCOPE_ID>
get system dhcp server
```

Check active leases:

```fortios
diagnose sys dhcp server lease interface <INTERFACE>
```

---

## Related Standards

- [VLAN Configuration](vlan-standards.md) — VLAN and interface design
- [DNS Standards](dns-standards.md) — Local DNS service (FortiGate DNS)
- [IP Addressing](ip-addressing.md) — Subnet allocation
- [Equipment Configuration](equipment-config.md) — FortiGate baseline (DHCP disabled on Cisco)
