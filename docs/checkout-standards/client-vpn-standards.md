# Client VPN Standards

FortiGate IPsec remote access VPN for datacenter fallback access and office remote access to
internal services. Okta RADIUS authentication is used where an Okta agent is reachable; local
credentials are used as a fallback for offices without agent connectivity.

---

## Overview

| Use Case | Sites | Authentication | IKE Version |
| --- | --- | --- | --- |
| Datacenter fallback | LD7, LD8, DC4, DB3, SG3 | Okta RADIUS | IKEv2 |
| Office remote access | London, New York, Paris, Perth, Riyadh, Tel Aviv | Local or Okta RADIUS | IKEv2 |

Split tunneling is enabled on all sites — only traffic destined for internal Checkout networks
routes through the VPN. All other traffic exits the client's local internet connection.

**Rationale:** These VPNs are support tools, not corporate internet gateways. Engineers connect to
a site VPN to access that site's infrastructure during support or maintenance. Forcing all client
traffic through the site would degrade the engineer's internet connectivity and add unnecessary
load to the site firewall. Full-tunnel VPN is not appropriate for this use case.

---

## IPsec Parameters

IKEv2 is the standard for all deployments. IKEv1 remains in service on sites not yet migrated;
see [Legacy: IKEv1](#legacy-ikev1-existing-sites) for that configuration.

| Parameter | Standard | Notes |
| --- | --- | --- |
| IKE Version | 2 | |
| Phase 1 Proposals | AES256-SHA256, AES128-SHA256 | Tested with FortiClient 7.0 |
| Phase 1 DH Group | 19 | Single group only — see note below |
| Phase 1 Key Lifetime | 86400 s | 24 hours |
| Authentication | PSK | Unique per site; stored in LastPass |
| Phase 2 Proposals | AES256-SHA256, AES128-SHA256 | |
| Phase 2 DH Group | 19 | Single group only |
| Phase 2 Key Lifetime | 43200 s | 12 hours |
| Replay Detection | Enabled | |
| Perfect Forward Secrecy | Enabled | |
| DPD Mode | On Idle | Detects disconnected clients |
| DPD Retry Interval | 60 s | |

**DH Group — IKEv2 uses Group 19 (single group only):**

- **Negotiation bug (FortiOS 7.4.4–7.4.8):** When multiple DH groups are configured, FortiGate
  returns `INVALID_KE_PAYLOAD` even if the client's proposed group is in the list. Configure
  exactly one group on both Phase 1 and Phase 2. Permanent fix is FortiOS 8.0. See
  [KB article](#fortinet-documentation).
- Group 19 (P-256 ECDH) is the correct single group for IKEv2 — supported on all platforms
  including macOS and iOS FortiClient.

**IKEv1 legacy sites use Group 18 — Apple client limitation:**

macOS FortiClient does not support DH groups above 18 for IKEv1. FortiClient 7.4.2 defaulted
to Group 20, causing "tunnel configuration is unsupported" errors on macOS. Group 18 is the
maximum for IKEv1 on Apple clients. See [KB article](#fortinet-documentation). This is one
reason to migrate IKEv1 sites to IKEv2.

Tested versions: FortiOS 7.4.5 and FortiClient VPN 7.0.6.

---

## Authentication

### Datacenter Sites — Okta RADIUS

Datacenters use Okta RADIUS for MFA authentication. The RADIUS client is configured with
`source-ip` set to the cluster management VLAN IP (consistent with the
[source-IP principle](ha-standards.md#source-ip-principle)) and a secondary server for
redundancy.

The remote auth timeout must be extended to allow time for users to approve the Okta push.

### Office Sites — Local or Okta RADIUS

Offices use local user accounts where no Okta agent is reachable. Where an Okta agent is
accessible, RADIUS can be added to the user group alongside local accounts. The Phase 1
`authusrgrp` references the same user group in both cases.

---

## FortiGate Configuration

### Global Settings

Required for Okta MFA — extends the RADIUS authentication timeout to allow push approval.

```fortios
config system global
    set remoteauthtimeout 60
end
```

### Users and Groups

#### Okta RADIUS (Datacenters and Okta-Enabled Offices)

```fortios
config user radius
    edit "Okta_MFA_Radius"
        set server "<OKTA_RADIUS_PRIMARY_IP>"
        set secret ENC <RADIUS_SECRET>
        set auth-type pap
        set source-ip <CLUSTER_MGMT_IP>
        set secondary-server "<OKTA_RADIUS_SECONDARY_IP>"
        set secondary-secret ENC <RADIUS_SECRET>
    next
end
```

#### Local Users (Offices Without Okta Agent)

```fortios
config user local
    edit "<USERNAME>"
        set type password
        set passwd <PASSWORD>
    next
end
```

#### User Group

The user group can contain local users, the RADIUS server, or both. Phase 1 references this
group for authentication.

```fortios
config user group
    edit "IPsec_VPN_Group"
        set member "Okta_MFA_Radius"
    next
end
```

For offices with local users only, replace `"Okta_MFA_Radius"` with the local usernames.

### Firewall Objects

```fortios
config firewall address
    edit "IPsec_Client_Range"
        set type iprange
        set comment "IPsec VPN Client Range"
        set start-ip <START_IP>
        set end-ip <END_IP>
    next
    edit "<SITE_SUPERNET_NAME>"
        set subnet <PREFIX> <MASK>
        set comment "Site supernet for split-tunnel destinations"
    next
end

config firewall addrgrp
    edit "IPsec_Client_Destinations"
        set member <ADDRESS_LIST>
        set comment "IPsec VPN Destination List"
    next
end
```

`IPsec_Client_Destinations` contains all internal subnets the VPN client can reach. This is
referenced by `ipv4-split-include` in Phase 1 to enforce split tunneling.

### Phase 1 Interface

```fortios
config vpn ipsec phase1-interface
    edit "IPsec_Client_1"
        set type dynamic
        set interface "<WAN_INTERFACE>"
        set ike-version 2
        set local-gw <WAN_INTERFACE_IP>
        set peertype any
        set net-device disable
        set mode-cfg enable
        set proposal aes256-sha256 aes128-sha256
        set dpd on-idle
        set comments "IPsec Client VPN"
        set dhgrp 19
        set eap enable
        set eap-identity send-request
        set authusrgrp "IPsec_VPN_Group"
        set ipv4-start-ip <CLIENT_RANGE_START>
        set ipv4-end-ip <CLIENT_RANGE_END>
        set dns-mode auto
        set ipv4-split-include "IPsec_Client_Destinations"
        set save-password enable
        set client-auto-negotiate enable
        set client-keep-alive enable
        set psksecret ENC <VPN_PSK>
        set dpd-retryinterval 60
    next
end
```

`set local-gw` binds the Phase 1 to a specific WAN IP. Required when the WAN interface has
multiple IPs or is a VLAN subinterface. `eap enable` with `eap-identity send-request` passes
EAP credentials to the RADIUS server for Okta MFA.

### Phase 2 Interface

```fortios
config vpn ipsec phase2-interface
    edit "IPsec_Client_1"
        set phase1name "IPsec_Client_1"
        set proposal aes256-sha256 aes128-sha256
        set dhgrp 19
        set comments "IPsec Client VPN"
    next
end
```

No `src-subnet`/`dst-subnet` is needed — client IPs are assigned dynamically via `mode-cfg`.

### Zone

Group all VPN Phase 1 interfaces into a zone. Firewall policies reference the zone rather
than individual VPN interfaces, which simplifies policy management on dual-ISP sites.

```fortios
config system zone
    edit "IPsec_Clients"
        set interface "IPsec_Client_1"
    next
end
```

On dual-ISP sites, add both interfaces: `set interface "IPsec_Client_1" "IPsec_Client_2"`.

### Firewall Policy

```fortios
config firewall policy
    edit <POLICY_NUMBER>
        set name "Remote Access VPN"
        set srcintf "IPsec_Clients"
        set dstintf <DESTINATION_INTERFACE_LIST>
        set action accept
        set srcaddr "IPsec_Client_Range"
        set dstaddr "IPsec_Client_Destinations"
        set schedule "always"
        set service <PERMITTED_SERVICES>
        set logtraffic all
        set logtraffic-start enable
    next
end
```

---

## Dual ISP Sites

Sites with two WAN links run a separate Phase 1 and Phase 2 interface per link. The VPN client
IP range is split evenly between the two Phase 1 interfaces. Both interfaces are added to the
`IPsec_Clients` zone — no policy changes required.

**IP range split example:** Total range `10.x.x.1–10.x.x.254`

- `IPsec_Client_1` (bond0.901): `10.x.x.1–10.x.x.127`
- `IPsec_Client_2` (bond0.902): `10.x.x.128–10.x.x.254`

```fortios
config vpn ipsec phase1-interface
    edit "IPsec_Client_1"
        set interface "bond0.901"
        set local-gw <ISP1_IP>
        set ipv4-start-ip <START_IP>
        set ipv4-end-ip <END_IP>
        [... same parameters as above ...]
    next
    edit "IPsec_Client_2"
        set interface "bond0.902"
        set local-gw <ISP2_IP>
        set ipv4-start-ip <START_IP>
        set ipv4-end-ip <END_IP>
        [... same parameters as above ...]
    next
end
config vpn ipsec phase2-interface
    edit "IPsec_Client_1"
        set phase1name "IPsec_Client_1"
        set proposal aes256-sha256 aes128-sha256
        set dhgrp 19
        set comments "IPsec Client VPN"
    next
    edit "IPsec_Client_2"
        set phase1name "IPsec_Client_2"
        set proposal aes256-sha256 aes128-sha256
        set dhgrp 19
        set comments "IPsec Client VPN"
    next
end
config system zone
    edit "IPsec_Clients"
        set interface "IPsec_Client_1" "IPsec_Client_2"
    next
end
```

Configure the secondary WAN IP in FortiClient as the backup remote gateway.

---

## FortiClient Settings

FortiClient VPN must use **Advanced Settings** to match the FortiGate configuration. The
defaults do not match — IKE version and DH groups must be set manually.

### Connection

| Setting | Value |
| --- | --- |
| VPN Type | IPsec VPN |
| Remote Gateway | WAN IP of site (primary); second WAN IP (backup, dual-ISP sites) |
| Authentication Method | Pre-Shared Key |
| Key | From LastPass |
| XAuth / EAP Username | Okta email address (Okta sites) or local username |

### Advanced — VPN Settings

| Setting | Value |
| --- | --- |
| IKE | Version 2 |
| Options | Mode Config |

### Advanced — Phase 1

| Setting | Value |
| --- | --- |
| Proposals | AES256-SHA256, AES128-SHA256 |
| DH Group | 19 |
| Key Life | 86400 s |
| Dead Peer Detection | Enabled |
| NAT Traversal | Enabled |

### Advanced — Phase 2

| Setting | Value |
| --- | --- |
| Proposals | AES256-SHA256, AES128-SHA256 |
| DH Group | 19 |
| Key Life | 43200 s |
| Replay Detection | Enabled |
| Perfect Forward Secrecy | Enabled |

---

## Legacy: IKEv1 (Existing Sites)

Sites not yet migrated to IKEv2 run IKEv1 in aggressive mode with XAuth PAP. New deployments
must use IKEv2. **DH Group 18 is used for IKEv1** — macOS FortiClient does not support Group 19+
for IKEv1. The Phase 2 and zone configurations are identical to IKEv2 except for the DH group.

```fortios
config vpn ipsec phase1-interface
    edit "IPsec_Client_1"
        set type dynamic
        set interface "<WAN_INTERFACE>"
        set mode aggressive
        set peertype any
        set net-device disable
        set mode-cfg enable
        set proposal aes256-sha256 aes128-sha256
        set dpd on-idle
        set comments "IPsec Client VPN"
        set dhgrp 18
        set xauthtype pap
        set authusrgrp "IPsec_VPN_Group"
        set ipv4-start-ip <CLIENT_RANGE_START>
        set ipv4-end-ip <CLIENT_RANGE_END>
        set dns-mode auto
        set ipv4-split-include "IPsec_Client_Destinations"
        set unity-support disable
        set save-password enable
        set psksecret ENC <VPN_PSK>
        set dpd-retryinterval 60
    next
end
```

FortiClient advanced settings for IKEv1 sites: IKE Version 1, Mode Aggressive, DH Group 18
(Phase 1 and Phase 2). Do not use Group 19+ — unsupported by macOS FortiClient for IKEv1.

---

## Verification

```fortios
! Active IPsec tunnels
get vpn ipsec tunnel summary

! Phase 1 status and negotiated parameters
diagnose vpn ike gateway list

! Phase 2 status
diagnose vpn tunnel list

! Connected VPN clients and assigned IPs
diagnose vpn ike users list

! RADIUS authentication debug (run before client connects)
diagnose debug application fnbamd -1
diagnose debug enable
```

---

## Pre-Shared Key Management

- PSKs are unique per site — do not reuse across sites
- Store in LastPass under the site's entry
- Minimum 32 characters: mixed case, numbers, and special characters
- Rotate after any suspected compromise

---

## Related Standards

- [Equipment Configuration](equipment-config.md) — RADIUS client config and source-ip principle
- [High Availability](ha-standards.md#source-ip-principle) — Source-IP principle for cluster services
- [Firewall Standards](firewall-standards.md) — Policy ordering and zone design
- [VPN Standards](vpn-standards.md) — Site-to-site IPsec cipher suites
- [Security Hardening](security-hardening.md) — Credential management

## Fortinet Documentation

- [FortiOS 7.4 — FortiClient as dialup client](https://docs.fortinet.com/document/fortigate/7.4.4/administration-guide/785501/forticlient-as-dialup-client)
  — FortiGate-side config for IKEv2 and IKEv1 dialup IPsec VPN
- [FortiOS 7.4 — Remote access VPN overview](https://docs.fortinet.com/document/fortigate/7.4.1/administration-guide/190553/remote-access)
  — Overview of all remote access VPN types supported in FortiOS
- [FortiClient 7.0.6 — Standalone VPN client](https://docs.fortinet.com/document/forticlient/7.0.6/administration-guide/269779/standalone-vpn-client)
  — FortiClient VPN-only client configuration (IPsec and SSL VPN)
- [KB: Users fail to connect — mismatched DH group in KE payload (FortiOS 7.4.4–7.4.8)](https://community.fortinet.com/fortigate-3/technical-tip-users-fail-to-connect-to-ipsec-vpn-with-error-mismatched-dh-group-in-ke-payload-211754?tid=211754&fid=3)
  — Multi-DH-group `INVALID_KE_PAYLOAD` bug in IKEv2; workaround is single DH group 19; fix in FortiOS
    8.0
- [KB: Unable to connect — tunnel configuration is unsupported for dial-up IPsec (macOS FortiClient)](https://community.fortinet.com/fortigate-3/troubleshooting-tip-fix-unable-to-connect-to-vpn-because-tunnel-configuration-is-unsupported-error-for-dial-up-ipsec-connections-211134)
  — macOS FortiClient 7.4.2 defaults to DH Group 20 for IKEv1, which is unsupported; max is Group 18;
    fixed in 7.4.3
