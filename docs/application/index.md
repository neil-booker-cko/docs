# Application Protocols

Reference pages for application-layer protocols used in network infrastructure. Covers
message formats, port numbers, operation modes, and security considerations — distinct
from vendor configuration guides.

---

## Web

| Protocol | Port | Transport | RFC |
| --- | --- | --- | --- |
| [HTTP / HTTPS](http.md) | 80 / 443 | TCP | RFC 9110 |

## Infrastructure Services

| Protocol | Port | Transport | RFC |
| --- | --- | --- | --- |
| [DNS](dns.md) | 53 | UDP / TCP | RFC 1034, 1035 |
| [DHCP](dhcp.md) | 67/68 | UDP | RFC 2131 |
| [NTP](ntp.md) | 123 | UDP | RFC 5905 |
| [PTP](ptp.md) | 319/320 | UDP | IEEE 1588 |

## AAA

| Protocol | Port | Transport | RFC |
| --- | --- | --- | --- |
| [RADIUS](radius.md) | 1812/1813 | UDP | RFC 2865 |
| [TACACS+](tacacs.md) | 49 | TCP | RFC 8907 |

## Management & Monitoring

| Protocol | Port | Transport | RFC |
| --- | --- | --- | --- |
| [SSH](ssh.md) | 22 | TCP | RFC 4251 |
| [SNMP](snmp.md) | 161/162 | UDP | RFC 3411 |
| [Syslog](syslog.md) | 514 UDP / 601 TCP | UDP / TCP | RFC 5424 |
| [NetFlow / IPFIX](netflow.md) | 2055 / 4739 | UDP | RFC 7011 |
| [NETCONF / RESTCONF](netconf.md) | 830 / 443 | TCP | RFC 6241, 8040 |
| [gNMI](gnmi.md) | 9339 | TCP (gRPC) | OpenConfig |

---

## See Also

- [TCP/UDP Ports Reference](../reference/ports.md) — full port reference table
- [Cisco AAA Config](../cisco/cisco_aaa_config.md) — RADIUS/TACACS+ vendor config
- [Cisco SNMP Config](../cisco/cisco_snmp_config.md) — SNMP vendor config
- [Cisco Syslog Config](../cisco/cisco_syslog_config.md) — syslog vendor config
