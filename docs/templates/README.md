# Configuration Templates

Minimal working examples for Cisco IOS-XE and FortiGate platforms. Each template includes only
essential configuration for the feature to function. Use these as starting points and customize for
your environment.

---

## Cisco IOS-XE Templates

| Template | File | Description |
| --- | --- | --- |
| **BGP Minimal** | [bgp-minimal.ios](cisco/bgp-minimal.ios) | Single EBGP peering session |
| **BGP Explanation** | [bgp-minimal.md](cisco/bgp-minimal.md) | Step-by-step guide and customization |
| **OSPF Minimal** | [ospf-minimal.ios](cisco/ospf-minimal.ios) | Single area OSPF with one neighbor |
| **OSPF Explanation** | [ospf-minimal.md](cisco/ospf-minimal.md) | Configuration walkthrough |
| **EIGRP Minimal** | [eigrp-minimal.ios](cisco/eigrp-minimal.ios) | Basic EIGRP with two neighbors |
| **EIGRP Explanation** | [eigrp-minimal.md](cisco/eigrp-minimal.md) | Configuration guide |
| **BFD Minimal** | [bfd-minimal.ios](cisco/bfd-minimal.ios) | BFD with BGP integration |
| **BFD Explanation** | [bfd-minimal.md](cisco/bfd-minimal.md) | BFD configuration guide |
| **IPsec VPN Minimal** | [ipsec-vpn-minimal.ios](cisco/ipsec-vpn-minimal.ios) | Site-to-site IPsec tunnel |
| **IPsec Explanation** | [ipsec-vpn-minimal.md](cisco/ipsec-vpn-minimal.md) | VPN setup walkthrough |
| **DMVPN Minimal** | [dmvpn-minimal.ios](cisco/dmvpn-minimal.ios) | Hub-and-spoke DMVPN |
| **DMVPN Explanation** | [dmvpn-minimal.md](cisco/dmvpn-minimal.md) | DMVPN configuration guide |
| **HSRP Minimal** | [hsrp-minimal.ios](cisco/hsrp-minimal.ios) | Active/standby gateway redundancy |
| **HSRP Explanation** | [hsrp-minimal.md](cisco/hsrp-minimal.md) | HSRP setup guide |

---

## FortiGate Templates

| Template | File | Description |
| --- | --- | --- |
| **BGP Minimal** | [bgp-minimal.conf](fortigate/bgp-minimal.conf) | Single EBGP peering session |
| **BGP Explanation** | [bgp-minimal.md](fortigate/bgp-minimal.md) | Configuration walkthrough |
| **OSPF Minimal** | [ospf-minimal.conf](fortigate/ospf-minimal.conf) | Single area OSPF |
| **OSPF Explanation** | [ospf-minimal.md](fortigate/ospf-minimal.md) | OSPF configuration guide |
| **BFD Minimal** | [bfd-minimal.conf](fortigate/bfd-minimal.conf) | BFD with BGP integration |
| **BFD Explanation** | [bfd-minimal.md](fortigate/bfd-minimal.md) | BFD setup guide |
| **IPsec VPN Minimal** | [ipsec-vpn-minimal.conf](fortigate/ipsec-vpn-minimal.conf) | Site-to-site VPN tunnel |
| **IPsec Explanation** | [ipsec-vpn-minimal.md](fortigate/ipsec-vpn-minimal.md) | VPN setup guide |
| **VRRP Minimal** | [vrrp-minimal.conf](fortigate/vrrp-minimal.conf) | Virtual router redundancy |
| **VRRP Explanation** | [vrrp-minimal.md](fortigate/vrrp-minimal.md) | VRRP configuration guide |
| **HA Pair Minimal** | [ha-minimal.conf](fortigate/ha-minimal.conf) | Active/passive HA clustering |
| **HA Explanation** | [ha-minimal.md](fortigate/ha-minimal.md) | HA pair setup guide |

---

## How to Use These Templates

1. **Choose your platform** — Cisco or FortiGate
2. **Select the feature** — BGP, OSPF, VPN, etc.
3. **Review the markdown explanation** — Understand what each line does
4. **Copy the config** — Use the `.ios` or `.conf` file as a starting point
5. **Customize** — Replace IP addresses, interface names, ASNs with your values
6. **Test in lab first** — Validate before deploying to production

## Customization Tips

- **IP addresses**: Replace `10.0.0.0/24` style ranges with your network
- **Interface names**: Update `GigabitEthernet0/0/0` to match your device
- **BGP ASN**: Change `65000` to your autonomous system number
- **OSPF process**: Change process ID `1` to match your deployment
- **Passwords/PSKs**: Never use the example values in production; generate strong keys

---

## Feature Legend

✓ = Minimal template provided
□ = Not yet included

| Feature | Cisco | FortiGate | Notes |
| --- | --- | --- | --- |
| BGP | ✓ | ✓ | EBGP example; scale to iBGP by removing `remote-as` |
| OSPF | ✓ | ✓ | Single area; add areas as needed |
| EIGRP | ✓ | □ | Cisco proprietary |
| BFD | ✓ | ✓ | Integrated with IGP |
| IPsec VPN | ✓ | ✓ | IKEv2, AES-256, SHA-256 |
| DMVPN | ✓ | □ | Cisco proprietary |
| HSRP | ✓ | □ | Cisco proprietary |
| VRRP | □ | ✓ | Open standard; Cisco supports too |
| HA Pair | □ | ✓ | FortiGate-specific clustering |

---

## Production Checklist

Before deploying any template config to production:

- [ ] Change all IP addresses, subnets, and hostnames
- [ ] Update device-specific interfaces (Gig0/0/0 → your interface)
- [ ] Verify ASN and process IDs match your plan
- [ ] Generate strong pre-shared keys (32+ characters)
- [ ] Test in lab environment first
- [ ] Backup existing config before applying changes
- [ ] Have rollback plan in case of issues
- [ ] Schedule maintenance window with stakeholders
- [ ] Monitor CPU, memory, and convergence times post-deployment

---

## Next Steps

- Detailed configuration guides: See `/docs/` for comprehensive how-to documentation
- Troubleshooting: Check `/docs/operations/` for diagnostics and debugging
- Theory: Review `/docs/theory/` for protocol fundamentals
