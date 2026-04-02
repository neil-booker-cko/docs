# Application Protocol Reference

Message format and behaviour reference for application layer protocols. For Layer 2–4
wire formats see [Packet Headers](../packets/index.md); for routing protocol formats
see [Routing Protocols](../routing/index.md).

---

## Management & Monitoring

| Protocol | Port | Description |
| --- | --- | --- |
| [SSH](ssh.md) | TCP `22` | Encrypted remote access, command execution, and tunnelling |
| [SNMP](snmp.md) | UDP `161` / `162` | Network device monitoring and management; v1, v2c, v3 |
| [Syslog](syslog.md) | UDP `514` / TCP `601` / TCP `6514` | Centralised log message transport |
