# FortiGate IPsec VPN Minimal Configuration

This template establishes a route-based IPsec tunnel with IKEv2 and BGP dynamic routing. Replace
CAPITALIZED values.

## Configuration Breakdown

```fortios
config vpn ipsec phase1-interface
  edit "tunnel1"
    set interface "port1"
    set ike-version 2
    set peertype any
    set peer 203.0.113.2
    set psksecret "PSK_PASSWORD_HERE"
    set proposal aes256-sha256
    set dhgrp 14
    set lifetime 28800
    set nattraversal enable
    set dpd on-demand
  next
end
```

Configures IKEv2 Phase 1 (SA negotiation):

- **port1** = egress interface (replace with your WAN port)
- **ike-version 2** = IKEv2 (modern; use 1 for legacy peers)
- **peer 203.0.113.2** = remote peer IP (replace with tunnel endpoint)
- **psksecret** = pre-shared key (minimum 16 characters)
- **proposal aes256-sha256** = encryption and integrity algorithms
- **dhgrp 14** = Diffie-Hellman group (14 = 2048-bit, 19/20 = 256/384-bit curves)
- **lifetime 28800** = SA lifetime in seconds (8 hours)
- **nattraversal enable** = NAT-T for traversal through NAT/firewalls
- **dpd on-demand** = Dead Peer Detection (detects dead tunnels)

```fortios
config vpn ipsec phase2-interface
  edit "tunnel1"
    set phase1name "tunnel1"
    set proposal aes256-sha256
    set pfs enable
    set dhgrp 14
    set lifetime 3600
  next
end
```

Configures IPsec Phase 2 (child SA for traffic encryption):

- **phase1name "tunnel1"** = links to Phase 1 SA (must match edit name)
- **proposal aes256-sha256** = encryption/integrity (should match Phase 1)
- **pfs enable** = Perfect Forward Secrecy (separate key for each phase 2)
- **dhgrp 14** = DH group for phase 2 key derivation
- **lifetime 3600** = child SA lifetime in seconds (1 hour)

```fortios
config system interface
  edit "tunnel1"
    set vdom "root"
    set ip 10.255.0.1 255.255.0.0
    set type tunnel
    set remote-ip 10.255.0.2
    set interface "port1"
  next
end
```

Creates a logical tunnel interface:

- **10.255.0.1/24** = local tunnel endpoint (replace with your tunnel subnet)
- **10.255.0.2** = remote tunnel endpoint (replace with peer's tunnel IP)
- **port1** = bound to physical egress interface

```fortios
config router bgp
  set as 65000
  set router-id 10.0.0.1
  config neighbor
    edit "10.255.0.2"
      set remote-as 65001
      set ebgp-multihop 2
    next
  end
  config network
    edit 1
      set prefix 10.1.0.0 255.255.0.0
    next
  end
end
```

Runs BGP over the tunnel for dynamic route exchange. See [BGP minimal](bgp-minimal.md) for details.

## Customization

### Change Encryption Algorithm

Replace `aes256-sha256` with alternatives:

- `aes128-sha256` (128-bit AES, less CPU)
- `aes256-sha512` (256-bit AES, stronger hash)
- `chacha20poly1305` (modern, requires FortiOS 6.4.2+)

Both Phase 1 and Phase 2 proposals should match (or be compatible with peer).

### Change DH Group

Replace `dhgrp 14` with:

- `dhgrp 5` (1536-bit, older)
- `dhgrp 14` (2048-bit, current standard)
- `dhgrp 19` (256-bit ECDH, modern)
- `dhgrp 20` (384-bit ECDH, strongest)

Must match peer configuration.

### Change to IKEv1

For legacy third-party peers:

```fortios
set ike-version 1
set proposal aes256-sha256
set dhgrp 2
! IKEv1 only supports dhgrp 1,2,5
```

### Use Static Routes Instead of BGP

Remove BGP configuration and add static route over tunnel:

```fortios
config router static
  edit 1
    set destination 192.168.0.0 255.255.0.0
    set gateway 10.255.0.2
    set device "tunnel1"
  next
end
```

### Dial-Up VPN (Dynamic Peer IP)

For remote peers with dynamic IPs, use:

```fortios
set peertype dynamic
! Omit "set peer" line to accept any IP
set mode aggressive
! Use aggressive mode for faster negotiation
```

## Verification

After applying:

```fortios
diagnose vpn ike gateway list
! Check: Phase 1 status = established

diagnose vpn tunnel list
! Check: Phase 2 status, traffic statistics

diagnose vpn tunnel stat
! Check: Encrypted/decrypted byte counters

get router info bgp summary
! Check: BGP neighbor status (if using BGP)
```
