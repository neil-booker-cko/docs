# Cisco IPsec Site-to-Site VPN Minimal Configuration

This template establishes a site-to-site IPsec tunnel using IKEv2. Replace CAPITALIZED values.

## Configuration Breakdown

### IKE Phase 1 (ISAKMP)

```ios
crypto ikev2 proposal PROPOSAL-1
  encryption aes-cbc-256
  integrity sha256
  dh-group 14
```

Defines IKE negotiation parameters:

- **encryption aes-cbc-256**: AES-256 encryption
- **integrity sha256**: HMAC-SHA256 for authentication
- **dh-group 14**: 2048-bit Diffie-Hellman (sufficient for most deployments)

```ios
crypto ikev2 keyring KEYRING-1
  peer 203.0.113.5
    pre-shared-key YOUR_PSK_HERE
```

Stores the pre-shared key (PSK). Replace:

- `203.0.113.5` = peer's public IP
- `YOUR_PSK_HERE` = 32+ character random key (generate with openssl: `openssl rand -base64 32`)

### IPsec Phase 2 (Child SA)

```ios
crypto ipsec transform-set TS-1 esp-aes 256 esp-sha256-hmac
  mode tunnel
```

Defines IPsec encryption:

- **esp-aes 256**: AES-256 encryption for traffic
- **esp-sha256-hmac**: HMAC-SHA256 for traffic integrity
- **mode tunnel**: Tunnel mode (creates new IP header)

### Tunnel Interface

```ios
interface Tunnel0
  ip address 169.254.1.1 255.255.255.252
  tunnel source 203.0.113.1
  tunnel destination 203.0.113.5
  tunnel mode ipsec ipv4
  tunnel protection ipsec profile IPSEC-PROFILE-1
```

Creates the tunnel:

- **169.254.1.1/30** = tunnel interface IP (pair with peer's tunnel IP, e.g., 169.254.1.2)
- **tunnel source 203.0.113.1** = your public IP
- **tunnel destination 203.0.113.5** = peer's public IP
- **ip mtu 1400** = accounts for IPsec overhead (1500 - 100 bytes)

### Traffic Selectors (Crypto ACL)

```ios
access-list 101 permit ip 10.0.0.0 0.0.255.255 192.168.0.0 0.0.255.255
```

Defines which traffic to encrypt:

- **10.0.0.0/16** = your subnet
- **192.168.0.0/16** = peer's subnet

Only packets matching both source and destination are encrypted.

## Customization

### Change Peer IP

Replace all occurrences of `203.0.113.5`:

```ios
crypto ikev2 keyring KEYRING-1
  peer YOUR_PEER_IP    ! Replace 203.0.113.5
    pre-shared-key YOUR_PSK_HERE

interface Tunnel0
  tunnel source YOUR_PUBLIC_IP    ! Replace 203.0.113.1
  tunnel destination YOUR_PEER_IP ! Replace 203.0.113.5
```

### Change Tunnel IPs

```ios
interface Tunnel0
  ip address 169.254.1.1 255.255.255.252
```

Replace `169.254.1.1` with a unique tunnel IP for this router. Configure peer's tunnel as
`169.254.1.2` (next IP in /30 range).

### Change Traffic Selectors

```ios
access-list 101 permit ip 10.0.0.0 0.0.255.255 192.168.0.0 0.0.255.255
```

Replace subnets:

- First IP range = your subnets
- Second IP range = peer's subnets

Add more lines for multiple subnets:

```ios
access-list 101 permit ip 10.0.0.0 0.0.255.255 192.168.0.0 0.0.255.255
access-list 101 permit ip 10.1.0.0 0.0.255.255 192.169.0.0 0.0.255.255
```

### Change PSK

Generate a strong key:

```bash
openssl rand -base64 32
# Example output: h7$K9mP2xQ@vL5bN8jF3cR$W2yD9gT6sE
```

Replace `YOUR_PSK_HERE` with the generated key. **Must be identical on both peers.**

## Verification

After applying:

```ios
show crypto session brief
! Check: IKE and IPsec SAs listed

show crypto ikev2 sa
! Check: Status should be "ESTABLISHED"

show crypto ipsec sa
! Check: Outbound/inbound SPIs and counters

show interface Tunnel0
! Check: Tunnel interface "up"

ping 169.254.1.2
! Check: Can reach peer's tunnel IP
```

## Troubleshooting

| Issue | Check |
| --- | --- |
| IKE Phase 1 fails | PSK mismatch; peer IP unreachable; firewall blocking UDP 500/4500 |
| IKE Phase 2 fails | Transform mismatch; traffic selectors don't match on both sides |
| Tunnel up, no traffic | Routes missing; ACL blocking; MTU too large |

- Add BGP over tunnel (see [BGP minimal](bgp-minimal.md))
- Add BFD for faster failure detection (see [BFD minimal](bfd-minimal.md))
- Review [IPsec VPN guide](../operations/ipsec_vpn_troubleshooting.md) for diagnostics
