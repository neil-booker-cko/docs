# TCP/UDP Well-Known Ports

IANA assigns port numbers in three ranges. Ports `0`–`1023` are well-known (system)
ports, requiring elevated privileges to bind. Ports `1024`–`49151` are registered
(user) ports. Ports `49152`–`65535` are dynamic/ephemeral ports used as source ports
for client connections.

---

## Port Ranges

| Range | Name | Description |
| --- | --- | --- |
| `0` – `1023` | Well-known | Assigned by IANA; require root/admin to bind |
| `1024` – `49151` | Registered | IANA-registered; no privilege required |
| `49152` – `65535` | Dynamic / Ephemeral | Client source ports (OS-assigned) |

Linux default ephemeral range: `32768`–`60999`
(`/proc/sys/net/ipv4/ip_local_port_range`).
Windows default: `49152`–`65535`.

---

## File Transfer & Remote Access

| Port | Protocol | Service | Notes |
| --- | --- | --- | --- |
| `20` | TCP | FTP Data | Active mode data channel |
| `21` | TCP | FTP Control | Command channel |
| `22` | TCP | SSH / SCP / SFTP | Secure Shell and file transfer |
| `23` | TCP | Telnet | Cleartext; avoid in production |
| `69` | UDP | TFTP | Trivial FTP; used for network device image transfers |
| `115` | TCP | SFTP (legacy) | Simple FTP; not related to SSH SFTP |
| `989` | TCP | FTPS Data | FTP over TLS — data channel |
| `990` | TCP | FTPS Control | FTP over TLS — command channel |

---

## Email

| Port | Protocol | Service | Notes |
| --- | --- | --- | --- |
| `25` | TCP | SMTP | Server-to-server mail transfer |
| `110` | TCP | POP3 | Mail retrieval (cleartext) |
| `143` | TCP | IMAP | Mail access (cleartext) |
| `465` | TCP | SMTPS | SMTP with implicit TLS (legacy, re-assigned) |
| `587` | TCP | SMTP Submission | MSA; auth + STARTTLS for clients |
| `993` | TCP | IMAPS | IMAP over TLS |
| `995` | TCP | POP3S | POP3 over TLS |

---

## Web

| Port | Protocol | Service | Notes |
| --- | --- | --- | --- |
| `80` | TCP | HTTP | Plain HTTP (HTTP/1.1 and HTTP/2 cleartext) |
| `443` | TCP/UDP | HTTPS | HTTP over TLS; UDP/443 for HTTP/3 (QUIC) |
| `8080` | TCP | HTTP Alternate | Common dev/proxy port; not IANA well-known |
| `8443` | TCP | HTTPS Alternate | Common dev/proxy TLS port |

---

## Name & Directory Services

| Port | Protocol | Service | Notes |
| --- | --- | --- | --- |
| `53` | UDP/TCP | DNS | UDP for queries; TCP for zone transfers and large responses |
| `88` | UDP/TCP | Kerberos | Authentication |
| `389` | TCP | LDAP | Cleartext directory access |
| `464` | UDP/TCP | Kerberos (kpasswd) | Password change |
| `636` | TCP | LDAPS | LDAP over TLS |
| `3268` | TCP | LDAP Global Catalog | Microsoft AD |
| `3269` | TCP | LDAPS Global Catalog | Microsoft AD over TLS |

---

## Network Management & Monitoring

| Port | Protocol | Service | Notes |
| --- | --- | --- | --- |
| `161` | UDP | SNMP | Agent — receives GET/SET from manager |
| `162` | UDP | SNMP Trap | Manager — receives traps/informs from agents |
| `514` | UDP | Syslog | RFC 3164 / RFC 5424 UDP transport |
| `601` | TCP | Syslog (reliable) | RFC 3195 reliable delivery over TCP |
| `6514` | TCP | Syslog over TLS | RFC 5425 encrypted syslog |

---

## Network Infrastructure

| Port | Protocol | Service | Notes |
| --- | --- | --- | --- |
| `67` | UDP | DHCP Server | Server listens; client broadcasts to port 67 |
| `68` | UDP | DHCP Client | Client listens for server responses |
| `123` | UDP | NTP | Time synchronisation |
| `179` | TCP | BGP | eBGP and iBGP sessions |
| `500` | UDP | IKEv1 / IKEv2 | IPsec key exchange |
| `4500` | UDP | IKEv2 NAT-T | IPsec with NAT traversal |

---

## VPN & Tunnelling

| Port | Protocol | Service | Notes |
| --- | --- | --- | --- |
| `1194` | UDP/TCP | OpenVPN | Default OpenVPN port |
| `1701` | UDP | L2TP | Layer 2 Tunnelling Protocol |
| `1723` | TCP | PPTP | Point-to-Point Tunnelling Protocol (deprecated) |
| `4500` | UDP | IKEv2 NAT-T | IPsec encapsulation over NAT |
| `51820` | UDP | WireGuard | Default WireGuard port |

---

## Security & Authentication

| Port | Protocol | Service | Notes |
| --- | --- | --- | --- |
| `49` | TCP/UDP | TACACS+ | Terminal Access Controller (Cisco AAA) |
| `1812` | UDP | RADIUS Auth | RFC 2865 authentication and authorisation |
| `1813` | UDP | RADIUS Accounting | RFC 2866 accounting |
| `2083` | TCP | cPanel (HTTPS) | Not IANA; mentioned for awareness |

---

## Databases

| Port | Protocol | Service | Notes |
| --- | --- | --- | --- |
| `1433` | TCP | Microsoft SQL Server | |
| `1521` | TCP | Oracle DB | |
| `3306` | TCP | MySQL / MariaDB | |
| `5432` | TCP | PostgreSQL | |
| `6379` | TCP | Redis | |
| `27017` | TCP | MongoDB | |

---

## Other Common Services

| Port | Protocol | Service | Notes |
| --- | --- | --- | --- |
| `111` | UDP/TCP | RPC portmapper | Used by NFS/NIS |
| `119` | TCP | NNTP | Network News Transport Protocol |
| `445` | TCP | SMB (CIFS) | Windows file sharing; direct TCP (no NetBIOS) |
| `514` | TCP | rsh | Remote Shell — **not** syslog on TCP |
| `546` | UDP | DHCPv6 Client | IPv6 DHCP |
| `547` | UDP | DHCPv6 Server | IPv6 DHCP |
| `587` | TCP | SMTP Submission | See Email section above |
| `853` | TCP | DNS over TLS (DoT) | RFC 7858 |
| `2049` | TCP/UDP | NFS | Network File System |
| `3389` | TCP | RDP | Remote Desktop Protocol (Windows) |
| `5060` | UDP/TCP | SIP | Session Initiation Protocol (VoIP) |
| `5061` | TCP | SIPS | SIP over TLS |

---

## Notes

- **TCP/514 is rsh (remote shell)**, not reliable syslog. RFC 3195 uses TCP/601 for

  reliable syslog delivery. This distinction matters for firewall rules.

- **UDP vs TCP for DNS**: Queries use UDP/53 by default. Responses larger than the

  negotiated EDNS0 payload (typically 4096 bytes) and zone transfers (AXFR/IXFR)
  use TCP/53. Always allow both.

- **IPsec**: ESP (IP protocol 50) and AH (IP protocol 51) are IP protocols, not

  TCP/UDP ports. IKE uses UDP/500; NAT traversal encapsulates ESP in UDP/4500.

- The full IANA port registry is published at

  `https://www.iana.org/assignments/service-names-port-numbers/`.
