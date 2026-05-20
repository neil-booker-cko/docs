# NetFlow Standards

NetFlow configuration standards for Cisco IOS-XE and FortiOS. The collector for all sites is
LogicMonitor. Flow export uses the management VRF/interface to keep telemetry traffic off the
data plane.

---

## Collector

| Parameter | Value |
| --- | --- |
| Collector | LogicMonitor |
| Protocol | UDP |
| Port | 2055 |
| Transport | Via management VRF / management interface |

---

## Cisco IOS-XE

### Flow Records

Two records are defined — one for ingress, one for egress. Both capture the full 5-tuple plus
interface, ToS, direction, byte/packet counters, TCP flags, and timestamps.

```ios
flow record LMNF-Input
 description IPv4 NetFlow
 match ipv4 source address
 match ipv4 destination address
 match transport source-port
 match transport destination-port
 match ipv4 protocol
 match interface input
 match ipv4 tos
 match flow direction
 collect interface output
 collect counter bytes long
 collect counter packets long
 collect transport tcp flags
 collect timestamp absolute first
 collect timestamp absolute last
!
flow record LMNF-Output
 match ipv4 tos
 match ipv4 protocol
 match ipv4 source address
 match ipv4 destination address
 match transport source-port
 match transport destination-port
 match interface output
 match flow direction
 collect interface input
 collect counter bytes long
 collect counter packets long
 collect transport tcp flags
 collect timestamp absolute first
 collect timestamp absolute last
!
```

### Flow Exporter

Export to LogicMonitor via the management VRF. Source from the management or loopback interface
to ensure flows are identifiable and routed correctly.

```ios
flow exporter LMPoller
 description Export to LogicMonitor
 destination <COLLECTOR_IP> vrf Mgmt-vrf
 source <MGMT_OR_LOOPBACK_INTERFACE>
 transport udp 2055
 template data timeout 60
!
```

### Flow Monitors

```ios
flow monitor LM-MON-INPUT
 description IPv4 LMNF Ingress Exports
 exporter LMPoller
 cache timeout active 60
 record LMNF-Input
!
flow monitor LM-MON-OUTPUT
 description IPv4 LMNF Egress Exports
 exporter LMPoller
 cache timeout active 60
 record LMNF-Output
!
```

### Applying Monitors

Apply to VLAN configurations (preferred) or individual interfaces:

```ios
vlan configuration <VLAN_LIST>
 ip flow monitor LM-MON-INPUT input
 ip flow monitor LM-MON-OUTPUT output
!
```

Or per-interface:

```ios
interface GigabitEthernet0/0
 ip flow monitor LM-MON-INPUT input
 ip flow monitor LM-MON-OUTPUT output
!
```

### Troubleshooting Commands

```ios
show flow monitor name LM-MON-INPUT cache format table
show flow monitor name LM-MON-INPUT cache sort highest counter packets long top 10 format table
show flow exporter LMPoller statistics
show flow interface GigabitEthernet0/0
```

---

## FortiOS

### Global NetFlow Configuration

```fortios
config system netflow
    set active-flow-timeout 60
    set inactive-flow-timeout 10
    set template-tx-timeout 300
    config collectors
        edit 1
            set collector-ip "<COLLECTOR_IP>"
            set source-ip "<CLUSTER_MGMT_IP>"
        next
    end
end
```

### Per-Interface Sampling

Enable NetFlow sampling on each interface that should export flows. Use `both` to capture
ingress and egress, or `rx`/`tx` for a single direction.

```fortios
config system interface
    edit "<INTERFACE>"
        set netflow-sampler both
    next
end
```

### HA Clusters

In an active-passive HA cluster, only the active device exports NetFlow. Set `source-ip` to
the cluster's shared management VLAN interface IP — this IP is synced across both nodes via HA
config sync and follows the active device on failover, so the collector always sees the same
source address.

See [High Availability Standards — NetFlow](ha-standards.md#netflow) for full details.

---

## Platform Support

| Platform | NetFlow Support | Notes |
| --- | --- | --- |
| Cisco IOS-XE | Full (Flexible NetFlow v9) | Two records (input/output); export via Mgmt-vrf |
| FortiOS | Yes (IPFIX/NetFlow v9) | Per-interface sampler; HA active node only |
| Perle Console Server | Not available | No NetFlow support |

---

## Related Standards

- [SNMP Standards](snmp-standards.md)
- [Syslog & Monitoring](syslog-monitoring-standards.md)
- [High Availability Standards](ha-standards.md)
- [NetFlow Protocol Reference](../application/netflow.md)
