# IPsec Best Practices

Security and operational best practices for IPsec VPN deployments. Covers IKE version selection,
authentication methods, cryptographic algorithm strength, key management, and deployment
considerations.

For IPsec protocol details see [IPsec & IKE](../theory/ipsec.md). For third-party VPN configuration
see [FortiGate Third-Party VPN](../fortigate/fortigate_third_party_vpn.md), [AWS Third-Party VPN](../aws/aws_third_party_vpn.md),
[Azure Third-Party VPN](../azure/azure_third_party_vpn.md), [GCP Third-Party VPN](../gcp/gcp_third_party_vpn.md).

---

## 1. IKE Version Selection

### IKEv1 (Legacy) vs IKEv2 (Modern)

| Aspect | IKEv1 | IKEv2 |
| --- | --- | --- |
| **RFC** | RFC 2409 | RFC 7539 |
| **Phases** | 2 phases (Phase 1: ISAKMP, Phase 2: Quick Mode) | 2 exchanges (IKE_SA_INIT, IKE_AUTH) |
| **Modes** | Main Mode, Aggressive Mode | Single exchange (no mode selection) |
| **Cryptographic Agility** | Inflexible (all algos pre-agreed) | Flexible (can negotiate algos mid-exchange) |
| **Rekeying Overhead** | High (full Phase 1 renegotiation) | Low (only Child SA rekeying) |
| **Deployment** | Widely deployed; legacy devices | Modern; recommended default |
| **Security** | Weaker (vulnerable to some attacks if weak crypto) | Stronger (built-in AEAD, DH group requirements) |
| **RFC Compliance** | Obsolete (RFC 6539) | Current (RFC 7539, RFC 8439) |

### Recommendation

**Use IKEv2 exclusively for all new deployments.** Reasons:

1. IKEv1 is obsolete and receiving no security updates
2. IKEv2 has proven 15+ years of deployment and security hardening
3. Cloud providers (AWS, Azure, GCP) default to IKEv2
4. IKEv2 reduces rekeying overhead (important for long-lived VPNs)

**When to use IKEv1:**

- Legacy devices with no IKEv2 support (very rare after 2020)
- Temporary interop with old on-prem equipment during migration

**When to retire IKEv1:**

- Plan migration: set sunset date (e.g., end of 2025)
- Test IKEv2 config in parallel
- Migrate all peers; decommission IKEv1 policies

---

## 2. Authentication Methods

### Pre-Shared Key (PSK) vs Certificates

| Aspect | PSK | Certificates (PKI) |
| --- | --- | --- |
| **Ease of Deployment** | Simple (one string) | Complex (PKI infrastructure required) |
| **Scalability** | N peers = N keys (manual overhead) | Automated issuance & renewal |
| **Key Management** | Manual distribution | Centralized CA; automated distribution |
| **Compromise Recovery** | Replace single PSK globally | Revoke certificate; issue new one |
| **Use Case** | 2-4 VPN peers; on-prem to cloud | 10+ peers; enterprise; mobile workforce |

### PSK Best Practices

If using PSK:

1. **Minimum length: 32 characters** (256 bits of entropy if truly random)

```text
Good:  "h7$K9mP2xQ@vL5bN8jF3cR$W2yD9gT6sE"  (32 random chars)
Bad:   "MyPassword123" (predictable; only 13 chars)
Bad:   "password" (4 bits entropy; trivial to crack)
```text

2. **Character set: Include uppercase, lowercase, numbers, symbols**

```text
Character set size = 95 (a-z, A-Z, 0-9, symbols)
32-char PSK = 95^32 possible values ≈ 2^209 bits entropy
Sufficient: Yes (exceeds 128-bit minimum)
```text

3. **Unique PSK per peer** — Do not reuse the same PSK for multiple tunnels

```text
Peer 1: "h7$K9mP2xQ@vL5bN8jF3cR$W2yD9gT6sE"
Peer 2: "aB4@nK7pL$jM2xQ9wR5sT$vC3dF6eG8hI"
(Different PSK for each peer prevents compromise cascade)
```text

4. **Secure distribution** — PSK must be transmitted securely (not via email/Slack)

```text
Methods:
  - In-person meeting (most secure)
  - Encrypted messaging (Signal, Wire)
  - Password manager with sharing (LastPass, 1Password Teams)
  - NOT: email, Slack, unencrypted chat
```text

5. **Regular rotation** — Change PSK every 90-180 days or on team changes

```text
Rotation procedure:
  1. Generate new PSK
  2. Distribute securely to peer
  3. Configure new PSK on both sides
  4. Test connectivity on new PSK
  5. Retire old PSK
```text

### Certificate-Based Authentication (PKI)

If deploying certificates:

1. **Use trusted CA** — Public CA (DigiCert, GlobalSign) or private CA (if enterprise-wide)

```text
Public CA: Higher cost, automatic browser trust
Private CA: Lower cost, requires distribution of CA cert to all peers
```text

2. **Certificate Subject Alternate Name (SAN)** — Include all possible peer identities

```text
CN=vpn-gateway-1.example.com
SAN=vpn-gateway-1.example.com, 203.0.113.1

(Covers both FQDN and IP identities)
```text

3. **Key size: RSA 2048-bit minimum; RSA 4096-bit preferred**

```text
RSA 2048: 112 bits symmetric equivalent (acceptable through 2030)
RSA 4096: 150 bits symmetric equivalent (long-term safe)
Prefer: RSA 4096 or ECDSA P-384 for new deployments
```text

4. **Certificate validity period: 1-2 years; not longer**

```text
1-year cert: Forces rekeying every year (security best practice)
5-year cert: Reduction in rotation overhead but stale cert risk higher
Choose 1-2 years; plan renewal 30 days before expiry
```text

5. **Certificate revocation checking** — Enable CRL or OCSP validation

```text
CRL (Certificate Revocation List): Periodic download; slower updates
OCSP (Online Certificate Status Protocol): Real-time validation; requires network connectivity
Recommendation: OCSP if available; CRL with short refresh interval as fallback
```text

---

## 3. Cryptographic Algorithm Selection

### Phase 1 (IKE) Encryption

**Current Recommendation (2026):**

```text
STRONG (use these):
  - AES-256-GCM   (AEAD; 256-bit; most secure)
  - AES-256-CBC   (traditional; 256-bit; solid)

ACCEPTABLE (transitional):
  - AES-128-GCM   (128-bit; adequate for 5-10 years)
  - AES-128-CBC   (128-bit; acceptable but not preferred)

DO NOT USE (deprecated):
  - 3DES            (64-bit block; vulnerable; do not use)
  - AES-128 non-AEAD (not FIPS 140-2 compliant for GCM)
```text

**Justification:**

- **AES-256**: 256-bit key resists all foreseeable attacks (NIST recommendation)
- **GCM (Galois/Counter Mode)**: Provides both encryption and authentication; built-in integrity
- **CBC (Cipher Block Chaining)**: Traditional mode; requires separate HMAC for authentication

### Phase 1 (IKE) Integrity / Authentication

**Current Recommendation:**

```text
STRONG:
  - SHA-256 (or stronger)
  - SHA-384
  - SHA-512

AVOID:
  - SHA-1   (deprecated since 2020; collision attacks known)
  - MD5     (broken; do not use)
```text

**When using GCM:** Integrity is provided by GCM (no separate HMAC needed). If using CBC, pair with
HMAC.

```text
Good combinations:
  AES-256-GCM            (built-in integrity; no HMAC needed)
  AES-256-CBC + HMAC-SHA-256
  AES-256-CBC + HMAC-SHA-384
```text

### Phase 2 (IPsec / ESP) Encryption

**Current Recommendation:**

```text
STRONG (use these):
  - AES-256-GCM   (AEAD; most secure)
  - AES-256-CBC + HMAC-SHA-256

ACCEPTABLE (transitional):
  - AES-128-GCM
  - AES-128-CBC + HMAC-SHA-256

DO NOT USE:
  - 3DES
  - AES with MD5 or SHA-1 authentication
```text

### Diffie-Hellman (DH) Group Selection

DH group provides forward secrecy (PFS - Perfect Forward Secrecy) by generating ephemeral session
keys per rekeying.

**Current Recommendation:**

```text
STRONG (use these):
  - DH Group 14 (2048-bit MODP)    [RFC 3526] — Default; sufficient
  - DH Group 20 (4096-bit MODP)    [RFC 3526] — Stronger; more CPU
  - DH Group 19 (ECDH P-256)       [RFC 5639] — Elliptic curve; fast

ACCEPTABLE (transitional):
  - DH Group 5  (1536-bit MODP)    [RFC 2409] — Weak; for interop only

DO NOT USE:
  - DH Group 1  (768-bit MODP)     (broken; 64-bit effective security)
  - DH Group 2  (1024-bit MODP)    (deprecated; 80-bit effective security)
```text

**Justification:**

- **Group 14** (2048-bit): Sufficient for 30+ years; widely supported
- **Group 20** (4096-bit): Stronger; slight CPU overhead (~10-20% on modern hardware)
- **Group 19** (ECDH): Faster computation; smaller key sizes; more recent deployment

**Recommendation:** Use DH Group 14 (2048-bit) as minimum; Group 20 for high-security requirements.

---

## 4. Perfect Forward Secrecy (PFS)

PFS ensures that compromise of a single session key does not reveal all past traffic. Enabled by
using DH group in Phase 2 (or higher).

### Enable PFS

**Cisco:**

```ios
crypto ipsec transform-set STRONG esp-aes 256 esp-sha256-hmac
  mode tunnel

crypto ipsec profile STRONG-PROFILE
  set transform-set STRONG
  set pfs group14
  ! PFS enabled with Group 14 DH
end
```text

**FortiGate:**

```fortios
config vpn ipsec
  edit "strong-tunnel"
    set proposal aes256-sha256
    set pfs enable
    set pfs-dh-group 14
  next
end
```text

**AWS/Azure/GCP:** PFS is enabled by default; cannot be disabled.

### PFS Behavior

```text
Without PFS:
  Session Key = derive(Pre-Shared Key, Protocol Context)
  If PSK compromised → All past traffic decrypted

With PFS:
  Session Key = derive(Pre-Shared Key + Ephemeral DH, Protocol Context)
  If PSK compromised → Only current session affected; past traffic safe
```text

---

## 5. Deployment Considerations

### IKE Configuration Checklist

```yaml
Phase 1 (IKE):
  - Version: IKEv2 (mandatory)
  - Encryption: AES-256-GCM or AES-256-CBC
  - Integrity: SHA-256 or stronger
  - DH Group: Group 14 (2048-bit) minimum
  - Lifetime: 3600-28800 seconds (1-8 hours)
  - DPD: Enabled (dead peer detection)
  - NAT-Traversal: Auto-detect

Phase 2 (IPsec/ESP):
  - Encryption: AES-256-GCM or AES-256-CBC
  - Integrity: HMAC-SHA-256 (if using CBC)
  - PFS: Enabled with Group 14
  - Lifetime: 3600 seconds (same as Phase 1 or slightly longer)
  - Traffic Selectors: Verified against peer documentation

Authentication:
  - Method: Certificates (preferred) or PSK (if <5 peers)
  - PSK length: 32+ characters (if using PSK)
  - PSK rotation: Every 90-180 days
  - Certificates: 2048-bit RSA minimum; 1-2 year validity

Additional:
  - All DES, 3DES, MD5, SHA-1: Disabled
  - Anti-replay: Enabled
  - NAT-Traversal: Enabled for internet-facing VPNs
```text

### Vendor-Specific Hardened Profiles

**Cisco IOS-XE (Example):**

```ios
crypto ikev2 proposal HARDENED
  encryption aes-cbc-256
  integrity sha256 sha384
  dh-group 14 20

crypto ikev2 policy HARDENED
  proposal HARDENED
  lifetime 28800

crypto ipsec transform-set HARDENED esp-aes 256 esp-sha256-hmac
  mode tunnel

crypto ipsec profile HARDENED
  set transform-set HARDENED
  set pfs group14
  set security-association lifetime seconds 3600
```text

**FortiGate (Example):**

```fortios
config vpn ike
  edit "hardened-proposal"
    set version 2
    set encryption aes256
    set integrity sha256
    set dhgrp 14
    set lifetime 28800
  next
end

config vpn ipsec
  edit "hardened-tunnel"
    set type tunnel
    set proposal aes256-sha256
    set pfs enable
    set pfs-dh-group 14
    set lifetime 3600
  next
end
```text

**AWS (Example):**

```bash
aws ec2 create-vpn-connection \
  --type ipsec.1 \
  --customer-gateway-id cgw-xxx \
  --vpn-gateway-id vgw-yyy \
  --options 'TunnelOptions=[{
    Phase1EncryptionAlgorithms=[{Value=AES256}],
    Phase1IntegrityAlgorithms=[{Value=SHA256}],
    Phase1DHGroupNumbers=[{Value=14}],
    Phase2EncryptionAlgorithms=[{Value=AES256}],
    Phase2IntegrityAlgorithms=[{Value=SHA256}]
  }]'
```text

---

## 6. Key Rotation & Rekeying

### Session Key Rotation (Automatic)

IPsec sessions automatically rekey (establish new keys) based on lifetime:

```text
Rekeying trigger:
  - Time-based: SA lifetime (3600 seconds = 1 hour)
  - Volume-based: Data volume (rarely used; 1 GB typical)

Behavior:
  1. New Child SA established (Phase 2 renegotiation)
  2. Old SA kept alive for brief period (graceful transition)
  3. New SA active; old SA deleted after grace period
  (Typically <1 second downtime)
```text

### Pre-Shared Key Rotation (Manual)

For PSK-authenticated tunnels:

1. **Generate new PSK** (32+ random characters)
2. **Distribute securely** (encrypted channel)
3. **Test in parallel** — Configure both PSKs on both sides (temporary dual-key setup)
4. **Switch** — Remove old PSK after confirmed working
5. **Document** — Log rotation date and new PSK hash (not plaintext)

**Testing:**

```text
Old PSK: "old_key_32_chars_12345678901234"
New PSK: "new_key_32_chars_12345678901234"

Config on both sides:
  [Old PSK config]
  [New PSK config]
  (Both active; tunnel uses new if available)

Verify: show crypto session

After confirmed working (24-48 hours):
  Remove old PSK config
  Keep new PSK only
```text

### Certificate Rotation

For certificate-authenticated tunnels:

1. **Generate new certificate** (request to CA)
2. **Install on both peers** — Load new cert; keep old cert in keyring
3. **Test** — Verify tunnel uses new certificate (check cert fingerprint in logs)
4. **Remove old certificate** — Delete from keyring after grace period (30+ days)

---

## 7. Compliance & Audit

### NIST SP 800-38D (Recommended)

```text
Algorithm:     AES-256-GCM
Key Length:    256 bits
IV (Nonce):    96 bits
Authentication Tag: 128 bits
```text

### FIPS 140-2 (US Government)

If compliance required:

```text
Approved algorithms:
  - AES with key sizes 128, 192, 256
  - HMAC-SHA-1, SHA-256, SHA-384, SHA-512
  - DH groups 14, 15, 16+

NOT approved:
  - 3DES (sunset 2023)
  - MD5, SHA-1 (deprecated for signatures)
```text

### PCI-DSS (Payment Card Industry)

```text
Requirements:
  - Encryption: AES-256
  - Key exchange: DH Group 14 or higher
  - Authentication: HMAC-SHA-256 or higher
  - Certificates: SHA-256 signatures (not SHA-1)
  - Rekeying: At least annually
```text

### Audit Checklist

- [ ] All IKE and IPsec algorithms documented
- [ ] DES/3DES/MD5/SHA-1 disabled (or marked for retirement)
- [ ] PSK rotation log maintained (dates, not keys)
- [ ] Certificates current (not expired, <2 years old)
- [ ] Certificate revocation checked (CRL or OCSP)
- [ ] PFS enabled on all tunnels
- [ ] DPD enabled on all internet-facing VPNs
- [ ] NAT-Traversal enabled where needed

---

## Next Steps

- [IPsec & IKE](../theory/ipsec.md) — Protocol details
- [IPsec VPN Troubleshooting](ipsec_vpn_troubleshooting.md) — Diagnostics
- [FortiGate Third-Party VPN](../fortigate/fortigate_third_party_vpn.md) — Implementation example
