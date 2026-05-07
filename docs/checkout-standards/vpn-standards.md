# VPN Configuration Standards

IPsec and Site-to-Site VPN standards for secure communications between datacenters and branch
offices.

---

## Site-to-Site IPsec VPN

Standards for VPN tunnels between remote sites using IKEv2 and strong encryption.

### Phase 1 (IKE Negotiation)

| Parameter | Standard | Notes |
| --- | --- | --- |
| Protocol | IKEv2 | IKEv1 deprecated; use IKEv2 exclusively |
| Encryption | AES-256-GCM (preferred) or AES-256-CBC | Minimum 256-bit AES |
| Integrity/Auth | SHA-384 (with GCM) or SHA-256 (with CBC) | PRF-SHA384 if using GCM |
| Key Exchange | Group 19-21 (preferred: 21) | Group 14+ minimum; elliptic curve preferred |
| Key Lifetime | 24 hours (86400 seconds) | Refresh interval |
| DPD Mode | On Demand | Detect peer down only when silent |
| DPD Retry | 20 seconds, 3 retries | 60 seconds total to declare peer dead |
| NAT Traversal | Enabled | Handle devices behind NAT |
| Keepalive | 20 seconds | Maintain NAT mappings |

### Phase 2 (IPsec Negotiation)

| Parameter | Standard | Notes |
| --- | --- | --- |
| Encryption | AES-256-GCM (preferred) or AES-256-CBC | Match encryption strength to Phase 1 |
| Integrity | None (GCM implicit) or SHA-256 (CBC) | GCM includes authentication |
| Key Exchange | Group 19-21 (preferred: 21) | Must match Phase 1 for PFS |
| PFS | Enabled | Perfect Forward Secrecy required |
| Key Lifetime | 1 hour (3600 seconds) | Shorter than Phase 1 |

### FortiOS Configuration Example

**Phase 1:**

```fortios
config vpn ipsec phase1-interface
    edit "VPN-TO-REMOTE"
        set interface "wan1"
        set ike-version 2
        set peertype any
        set net-device disable
        set proposal aes256gcm-prfsha384
        set dhgrp 21
        set remote-gw 1.2.3.4
        set psksecret "YourStrongPresharedKey"
        set keylife 86400
        set dpd on-demand
        set dpd-retryinterval 20
        set dpd-retrycount 3
        set nattraversal enable
        set keepalive 20
    next
end
```

**Phase 2:**

```fortios
config vpn ipsec phase2-interface
    edit "VPN-TO-REMOTE"
        set phase1name "VPN-TO-REMOTE"
        set proposal aes256gcm
        set dhgrp 21
        set pfs enable
        set keylifeseconds 3600
        set keylifekbs 0
        set auto-negotiate enable
        set src-subnet 10.10.1.0 255.255.255.0
        set dst-subnet 192.168.1.0 255.255.255.0
    next
end
```

---

## Cisco IOS-XE IPsec VPN

Standards for Cisco-based site-to-site VPN tunnels.

### Phase 1 Requirements

- **Protocol:** IKEv2 only
- **Encryption:** AES-256-GCM recommended; minimum AES-256-CBC
- **Integrity:** PRFSHA384 (GCM) or SHA-256 (CBC)
- **Key Exchange:** Diffie-Hellman Group 19-21 (21 preferred)
- **Key Lifetime:** 28800 seconds (8 hours)
- **DPD:** Enabled with appropriate intervals

### Phase 2 Requirements

- **Encryption:** AES-256-GCM or AES-256-CBC
- **Integrity:** SHA-256 (if not using GCM)
- **PFS:** Enabled with Group 19-21
- **Key Lifetime:** 3600 seconds (1 hour)

---

## VPN Design Principles

### Route Advertisement

- Use BGP to advertise local prefixes to remote sites
- Filter advertised routes using prefix-lists
- Apply route-maps for traffic engineering (Local Preference/AS Path Prepending)

### Traffic Steering

**Inbound (from remote):**

- Use Local Preference to prefer primary links
- Primary: `set local-preference 200`
- Secondary: `set local-preference 150`

**Outbound (to remote):**

- Use AS Path Prepending to prefer primary links
- Secondary: `set as-path prepend <LOCAL_AS> <LOCAL_AS>`

### Monitoring

- Enable BFD for fast failover detection (sub-second responsiveness)
- Configure BGP keepalive/hold timers (recommend 10/30 seconds)
- Log neighbor state changes for troubleshooting

---

## Pre-Shared Key Management

- Store PSKs in secure credential management system (e.g., LastPass, HashiCorp Vault)
- Minimum 32 characters: mixed case, numbers, special characters
- Rotate PSKs annually and after any suspected compromise
- Never commit PSKs to version control or documentation

---

## Testing and Validation

Before production deployment:

1. **Phase 1 Negotiation:** Verify IKE state is "MAIN" or "ESTABLISHED"
2. **Phase 2 Negotiation:** Verify IPsec state is "QM-IDLE" or "QUICK"
3. **Bidirectional Traffic:** Test ping across tunnel in both directions
4. **Failover:** Verify secondary tunnel takes over when primary fails
5. **MTU Path:** Test with large packets (1400+ bytes) to ensure no fragmentation issues

---

## Related Standards

- [BGP Standards](bgp-standards.md)
- [Security Hardening - SSH](security-hardening.md#ssh-hardening)
- [Equipment Configuration](equipment-config.md)
