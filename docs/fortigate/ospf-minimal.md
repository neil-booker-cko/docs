# FortiGate OSPF Minimal Configuration

This template establishes a single-area OSPF routing process. Replace CAPITALIZED values.

## Configuration Breakdown

```fortios
config router ospf
  set router-id 10.0.0.1
```

Enables OSPF with **router-id 10.0.0.1**. Must be unique. Replace with a loopback IP or
management interface IP.

```fortios
  config area
    edit 0.0.0.0
    next
  end
```

Declares the backbone area (**0.0.0.0**). All routers must be in area 0 for single-area OSPF.

```fortios
  config ospf-interface
    edit "port1"
      set interface "port1"
      set ip 10.0.0.1 255.255.255.0
      set authentication-type simple
      set authentication-key "OSPF_PASSWORD_HERE"
    next
  end
```

Configures OSPF on an interface:

- **port1** = interface name (replace with your port)
- **10.0.0.1 255.255.255.0** = interface IP and mask
- **authentication-type simple** = plain-text password (MD5 or SHA available)
- **authentication-key** = OSPF neighbor authentication

```fortios
  config network
    edit 1
      set prefix 10.1.0.0 255.255.0.0
      set area 0.0.0.0
    next
  end
```

Advertises a network:

- **10.1.0.0/16** = network to advertise (replace with your subnet)
- **0.0.0.0** = area (must match configured area)

## Customization

### Change Router ID

Replace `10.0.0.1` with your unique ID (loopback preferred).

### Change Interface

Replace `port1` with your interface (port2, port3, etc. or VLAN name).

### Change Area

For multi-area OSPF, create additional areas:

```fortios
config area
  edit 0.0.0.0
  next
  edit 0.0.0.1
  next
end
```

Then add interfaces to area 0.0.0.1 by modifying `ospf-interface` and `network` entries.

### Change Authentication

For MD5:

```fortios
set authentication-type md5
set authentication-key-id 1
set md5-key "MD5_KEY_HERE"
```

For SHA-256:

```fortios
set authentication-type sha
set sha256-key "SHA256_KEY_HERE"
```

### Add More Networks

```fortios
edit 2
  set prefix 10.2.0.0 255.255.0.0
  set area 0.0.0.0
next
edit 3
  set prefix 10.3.0.0 255.255.0.0
  set area 0.0.0.0
next
```

## Verification

After applying:

```fortios
get router info ospf status
! Check: OSPF enabled, Router ID listed

get router info ospf neighbors
! Check: Neighbor state = "Full"

get router info ospf database
! Check: LSA entries from neighbors

diagnose ip route list
! Detailed routing table with OSPF routes
```

- Add BFD for faster failure detection (see [BFD minimal](bfd-minimal.md))
- Review [FortiGate OSPF guide](../fortigate/fortigate_ospf_config.md)
