# Application Protocol Reference

Message format and behaviour reference for application layer protocols. For Layer 2–4
wire formats see [Packet Headers](../packets/index.md); for routing protocol formats
see [Routing Protocols](../routing/index.md).

---

## Web

| Protocol | Port | Description |
| --- | --- | --- |
| [HTTP / HTTPS](http.md) | TCP `80` / `443` | Hypertext Transfer Protocol; HTTP/1.1, HTTP/2, HTTP/3 over QUIC |

## Infrastructure

| Protocol | Port | Description |
| --- | --- | --- |
| [DNS](dns.md) | UDP/TCP `53` | Domain name resolution; A, AAAA, MX, TXT, DNSSEC |
| [DHCP](dhcp.md) | UDP `67`/`68` | Dynamic IP address assignment; DORA exchange, relay, DHCPv6 |
| [NTP](ntp.md) | UDP `123` | Network time synchronisation; stratum hierarchy, NTS authentication |
| [PTP](ptp.md) | UDP `319`/`320` / Ethernet `0x88F7` | Precision Time Protocol; sub-microsecond clock sync |

## AAA

| Protocol | Port | Description |
| --- | --- | --- |
| [RADIUS](radius.md) | UDP `1812`/`1813` | Remote Authentication Dial-In User Service; network access AAA |
| [TACACS+](tacacs.md) | TCP `49` | Terminal Access Controller Access-Control System; device management AAA |

## Management & Monitoring

| Protocol | Port | Description |
| --- | --- | --- |
| [SSH](ssh.md) | TCP `22` | Encrypted remote access, command execution, and tunnelling |
| [SNMP](snmp.md) | UDP `161` / `162` | Network device monitoring and management; v1, v2c, v3 |
| [Syslog](syslog.md) | UDP `514` / TCP `601` / TCP `6514` | Centralised log message transport |
| [NetFlow / IPFIX](netflow.md) | UDP `2055` / TCP `4739` | IP flow export for traffic analysis and monitoring |
| [NETCONF / RESTCONF](netconf.md) | TCP `830` / HTTPS | XML and REST-based network configuration; YANG data models |
| [gNMI](gnmi.md) | TCP `9339` | gRPC-based streaming telemetry and configuration |
