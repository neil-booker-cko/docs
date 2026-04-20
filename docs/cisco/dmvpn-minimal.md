# Cisco DMVPN Minimal Configuration (Hub)

This template configures the DMVPN hub (multipoint GRE with IPsec). Spokes use a similar
configuration with `tunnel mode gre ip multipoint` and `tunnel destination` pointing to hub.

## Hub Configuration Breakdown

```ios
tunnel mode gre multipoint
```

Enables multipoint GRE; accepts connections from multiple spokes on one tunnel interface.

```ios
tunnel key 100
```

Tunnel key for multi-DMVPN support. All spokes must use the same key.

```ios
ip nhrp network-id 100
```

NHRP network ID (must match spokes). Enables NHRP registration/resolution.

```ios
ip nhrp authentication DMVPN_AUTH_HERE
```

NHRP authentication password (must match spokes). Replace with your password.

```ios
tunnel protection ipsec profile DMVPN-IPSEC
```

Encrypts all tunnel traffic with IPsec.

```ios
router eigrp 100
  network 10.255.0.0 0.0.255.255    ! Tunnel network
  network 10.0.0.0 0.0.255.255      ! Hub's local subnets
```

Runs EIGRP over the tunnel to advertise routes.

## Spoke Configuration (minimal differences)

On each spoke router, use:

```ios
interface Tunnel0
  ip address 10.255.0.X 255.255.0.0    ! Unique IP for each spoke (X = 2, 3, 4, ...)
  tunnel source GigabitEthernet0/0/0
  tunnel destination 10.0.0.1          ! Hub's tunnel IP
  tunnel mode gre ip multipoint        ! Point-to-multipoint mode
  tunnel key 100
  tunnel protection ipsec profile DMVPN-IPSEC
  ip nhrp network-id 100
  ip nhrp authentication DMVPN_AUTH_HERE
  ip nhrp nhs 10.255.0.1 nbma 203.0.113.1
  ! ip nhrp nhs = register with hub
  ! nbma = hub's public IP
```

## Customization

### Change Tunnel Network

Replace `10.255.0.0/16`:

```ios
interface Tunnel0
  ip address 10.255.0.1 255.255.0.0    ! Hub IP
```

Spokes get unique IPs: `10.255.0.2`, `10.255.0.3`, etc.

### Change EIGRP AS

Replace `100` with your AS:

```ios
router eigrp 100    ! Your AS number
```

### Change PSK

Generate strong key:

```bash
openssl rand -base64 32
```

Replace both `DMVPN_PSK_HERE` and `DMVPN_AUTH_HERE`.

### Add More Spokes

For each new spoke, add configuration on spoke and ensure hub can reach it.

## DMVPN Phases

This template is **Phase 1** (all traffic through hub). For Phase 2/3, see
[DMVPN theory guide](../theory/dmvpn.md).

## Verification

After applying:

```ios
show interface Tunnel0
! Check: Tunnel interface "up"

show ip nhrp
! Check: NHRP registrations from spokes

show ip route eigrp
! Check: EIGRP routes learned

show crypto session brief
! Check: IPsec SAs active
```

- Review [DMVPN configuration guide](../cisco/cisco_dmvpn_config.md) for Phase 2/3
- Add BFD for faster convergence
- Implement access lists for hub-based filtering
