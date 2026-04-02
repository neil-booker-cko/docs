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

## Management & Monitoring

| Protocol | Port | Description |
| --- | --- | --- |
| [SSH](ssh.md) | TCP `22` | Encrypted remote access, command execution, and tunnelling |
| [SNMP](snmp.md) | UDP `161` / `162` | Network device monitoring and management; v1, v2c, v3 |
| [Syslog](syslog.md) | UDP `514` / TCP `601` / TCP `6514` | Centralised log message transport |
