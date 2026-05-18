# VPN Configuration Standards

IPsec and Site-to-Site VPN standards for secure communications between datacenters and branch
offices.

---

## Site-to-Site IPsec VPN

Standards for VPN tunnels between remote sites using IKEv2 and strong encryption.

### Cipher Suite Combinations

Select a complete cipher suite where all components match the same security level. Mismatching
levels (e.g., AES-256 with Group 14) wastes key material without improving real-world security.

**GCM vs CBC:** AES-GCM is an AEAD cipher — it provides encryption and integrity in a single
operation, so no separate HMAC algorithm is needed. AES-CBC requires a separate HMAC for integrity.
In IKEv2 Phase 1, both modes still require a **PRF (Pseudorandom Function)** for key derivation —
this is what the SHA value provides when using GCM; it is not providing message integrity.

| Tier | Use Case | Encryption | PRF / HMAC | DH Group |
| --- | --- | --- | --- | --- |
| **Tier 1** (Preferred) | All new tunnels | AES-256-GCM | PRF-SHA384 | Group 21 (P-521, 521-bit ECDH) |
| **Tier 2** (Acceptable) | Cloud interop | AES-256-GCM | PRF-SHA256 | Group 20 (P-384, 384-bit ECDH) |
| **Tier 3** (CBC fallback) | CBC required | AES-256-CBC | HMAC-SHA256 | Group 19 (P-256, 256-bit ECDH) |
| **Minimum** (Interop only) | Legacy peers | AES-256-CBC | HMAC-SHA256 | Group 14 (2048-bit MODP) |

**Do not use:** AES-128, SHA-1, MD5, 3DES, DES, or DH Groups 1, 2, or 5.

**Group 14 note:** Acceptable only when the remote peer does not support elliptic curve groups
(19–21). Always prefer ECDH (Groups 19–21) over MODP (Groups 14–16).

---

### Phase 1 (IKE Negotiation)

| Parameter | Standard | Notes |
| --- | --- | --- |
| Protocol | IKEv2 | IKEv1 deprecated; use IKEv2 exclusively |
| Encryption | AES-256-GCM (preferred) or AES-256-CBC | Minimum 256-bit AES |
| PRF / Integrity | PRF-SHA384 (with GCM) or HMAC-SHA256 (with CBC) | GCM: SHA provides key derivation only; CBC: SHA provides HMAC integrity |
| Key Exchange | Group 19–21 (preferred: 21) | Group 14 minimum; elliptic curve preferred |
| Key Lifetime | 24 hours (86400 seconds) | Refresh interval |
| DPD Mode | On Demand | Detect peer down only when silent |
| DPD Retry | 20 seconds, 3 retries | 60 seconds total to declare peer dead |
| NAT Traversal | Enabled | Handle devices behind NAT |
| Keepalive | 20 seconds | Maintain NAT mappings |

### Phase 2 (IPsec Negotiation)

| Parameter | Standard | Notes |
| --- | --- | --- |
| Encryption | AES-256-GCM (preferred) or AES-256-CBC | Match encryption strength to Phase 1 |
| Integrity | None (GCM is AEAD — integrity built-in) or HMAC-SHA256 (CBC) | Do not add a separate HMAC when using GCM |
| Key Exchange | Group 19–21 (preferred: 21) | Must match Phase 1 for PFS |
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
- **Encryption:** AES-256-GCM (Tier 1 preferred); AES-256-CBC (Tier 3 fallback)
- **PRF:** PRF-SHA384 with GCM (key derivation); HMAC-SHA256 with CBC (integrity + key derivation)
- **Key Exchange:** Group 21 (preferred), Group 20 or 19 acceptable; Group 14 last-resort interop only
- **Key Lifetime:** 86400 seconds (24 hours)
- **DPD:** Enabled with appropriate intervals

### Phase 2 Requirements

- **Encryption:** AES-256-GCM (preferred) or AES-256-CBC — match Phase 1
- **Integrity:** Not required with GCM (AEAD); HMAC-SHA256 with CBC
- **PFS:** Enabled — DH Group must match Phase 1
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
