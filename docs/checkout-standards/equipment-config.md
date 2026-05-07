# Equipment Configuration Standards

Baseline and standard configurations for Cisco and FortiGate devices.

---

## Cisco IOS-XE

### Baseline Configuration Template

**System Identification:**

```ios
hostname <DEVICE_NAME>
ip domain name checkout.com
ip domain name vrf Mgmt-vrf checkout.com
```

**SSH and Encryption:**

```ios
crypto key generate rsa modulus 4096
ip ssh version 2
ip ssh time-out 60
ip ssh authentication-retries 3
ip ssh server algorithm authentication keyboard
ip ssh server algorithm kex ecdh-sha2-nistp521 ecdh-sha2-nistp384
ip ssh server algorithm hostkey rsa-sha2-512 rsa-sha2-256
ip ssh server algorithm encryption aes256-gcm aes256-ctr
ip ssh server algorithm mac hmac-sha2-512 hmac-sha2-256
ip ssh server algorithm publickey ecdsa-sha2-nistp521 ecdsa-sha2-nistp384
```

**AAA (TACACS+ with Local Fallback):**

```ios
aaa new-model
aaa authentication login default group tacacs+ local
aaa authentication enable default group tacacs+ enable
aaa accounting commands 15 default start-stop group tacacs+
aaa accounting connection default start-stop group tacacs+
aaa accounting exec default start-stop group tacacs+
aaa accounting system default start-stop group tacacs+
!
username <LOCAL_ADMIN> algorithm-type scrypt secret <PASSWORD>
enable algorithm-type scrypt secret <PASSWORD>
service password-encryption
```

**Logging:**

```ios
service timestamps log datetime msec localtime show-timezone year
service timestamps debug datetime localtime msec show-timezone
logging enable
logging buffered 64000
logging console critical
logging host <SYSLOG_SERVER>
logging trap informational
logging source-interface <LOOPBACK_OR_MGMT_INTERFACE>
login on-failure log
login on-success log
```

**NTP:**

```ios
ntp authenticate
ntp authentication-key 1 md5 <NTP_KEY>
ntp trusted-key 1
ntp server <NTP_SERVER_1> source <INTERFACE>
ntp server <NTP_SERVER_2> source <INTERFACE>
ntp server <NTP_SERVER_3> source <INTERFACE>
ntp access-group peer <NTP_ACL>
ntp access-group serve-only <NTP_SERVE_ACL>
```

**Banners:**

```ios
banner motd #
***********************************************************************
*                                                                     *
*  UNAUTHORIZED ACCESS TO THIS NETWORK DEVICE IS STRICTLY PROHIBITED  *
*                                                                     *
*  This is a private network. You must have explicit permission to    *
*  access or configure this device. All activities are logged and     *
*  violations may result in disciplinary action.                      *
*                                                                     *
***********************************************************************
#
!
banner exec #
This is $(hostname) which is a PRODUCTION Network Device.
Observe all relevant CHANGE CONTROL procedures.
#
```

**SNMP (SNMPv3):**

```ios
ip access-list standard ACL_SNMP_IN
 permit <MONITORING_STATION_IP>
 deny any log
!
snmp-server group <SNMP_GROUP> v3 priv read All_MIB_View access ACL_SNMP_IN
snmp-server view All_MIB_View iso included
snmp-server user <SNMP_USER> <SNMP_GROUP> v3 auth sha <AUTH_PASS> priv aes 128 <PRIV_PASS>
snmp-server location <DC>-<RACK>-<POSITION>
snmp-server contact "CKO Network Services"
```

**VTY Access Control:**

```ios
ip access-list standard ACL_VTY_IN
 permit <MANAGEMENT_SUBNET>
 deny any log
!
line vty 0 15
 transport input ssh
 access-class ACL_VTY_IN in vrf-also
 exec-timeout 10
 login authentication default
!
line con 0
 exec-timeout 10
!
```

**Global Service Security:**

```ios
no service pad
no service dhcp
no ip bootp server
service tcp-keepalives-in
service tcp-keepalives-out
no cdp run
no ip source-route
```

**Command and Configuration Archive:**

```ios
archive
 log config
  logging enable
  logging persistent auto
  hidekeys
  path flash:/$h$t
  write-memory
!
aaa authorization exec default group tacacs+ local none
aaa authorization commands 0 default group tacacs+ local none
aaa authorization commands 1 default group tacacs+ local none
aaa authorization commands 15 default group tacacs+ local none
logging userinfo
```

### VRF-Lite Configuration

See [Cisco VRF-Lite for Cloud Provider Separation](../cisco/cisco_vrf_config.md)

### BGP Configuration

See [BGP Standards](bgp-standards.md)

### Security Hardening

See [Security Hardening Standards](security-hardening.md)

---

## FortiGate

### Baseline Configuration Template

**System Identification:**

```fortios
config system global
    set hostname <DEVICE_NAME>
    set timezone <TIMEZONE_ID>
end
```

**NTP Synchronization:**

```fortios
config system ntp
    set type custom
    config ntpserver
        edit 1
            set server <NTP_SERVER_1>
        next
        edit 2
            set server <NTP_SERVER_2>
        next
    end
end
```

**Global System Security:**

```fortios
config system global
    set admin-https-ssl-versions tlsv1-3
    set gui-cdn-usage enable
    set gui-display-hostname disable
    set log-single-cpu-high enable
    set post-login-banner disable
    set pre-login-banner enable
    set strong-crypto enable
end
```

**SSH Hardening:**

```fortios
config system global
    set ssh-enc-algo chacha20-poly1305@openssh.com aes256-ctr aes256-gcm@openssh.com
    set ssh-kex-algo diffie-hellman-group-exchange-sha256 curve25519-sha256@libssh.org ecdh-sha2-nistp256 ecdh-sha2-nistp384 ecdh-sha2-nistp521
    set ssh-mac-algo hmac-sha2-256 hmac-sha2-256-etm@openssh.com hmac-sha2-512 hmac-sha2-512-etm@openssh.com
end
```

**Auto-Install Disable:**

```fortios
config system auto-install
    set auto-install-config disable
    set auto-install-image disable
end
```

**Password Policy:**

```fortios
config system password-policy
    set status enable
    set apply-to admin-password
    set minimum-length 12
    set min-lower-case-letter 1
    set min-upper-case-letter 1
    set min-non-alphanumeric 0
    set min-number 1
    set expire-status enable
    set expire-day 90
    set reuse-password disable
end

config system global
    set admin-lockout-threshold 3
    set admin-lockout-duration 60
end
```

**Administrator Access:**

```fortios
config system admin
    edit <USERNAME>
        set trusthost <MANAGEMENT_IP> <SUBNET_MASK>
    next
    delete admin
end

config system global
    set admin-https-redirect disable
    set admin-sport 4434
    set admintimeout 5
end

config system interface
    edit port1
        set allowaccess ssh https ping snmp
    next
end
```

**DNS and Network Settings:**

```fortios
config system dns
    set primary <DNS_SERVER_1>
    set secondary <DNS_SERVER_2>
end

config system zone
    edit <ZONE_NAME>
        set intrazone deny
    next
end
```

**SNMP (SNMPv3 Only):**

```fortios
config system snmp sysinfo
    set status enable
    set description "<DEVICE_MODEL>"
    set contact-info "CKO Network Services"
    set location "<DC>-<RACK>"
end

config system snmp community
    delete public
end

config system snmp user
    edit <SNMP_USER>
        set trap-status disable
        set security-level auth-priv
        set auth-proto sha
        set auth-pwd ENC <AUTH_PASSWORD>
        set priv-proto aes
        set priv-pwd ENC <PRIV_PASSWORD>
        set ha-direct enable
    next
end
```

**Logging and Event Management:**

```fortios
config log eventfilter
    set event enable
end

config log syslogd setting
    set status enable
    set server <SYSLOG_SERVER_IP>
    set mode reliable
    set port 601
    set source-ip <FORTIOS_IP>
end
```

**Global Interface Security:**

```fortios
config system interface
    edit <WAN_INTERFACE>
        unselect allowaccess https ssh snmp http
    next
end

config system global
    set admin-telnet disable
    set gui-ipv6 disable
end
```

### High Availability Configuration

See [Security Hardening Standards - FortiOS HA](security-hardening.md#high-availability)

### Multi-VDOM Setup

TODO: Add VDOM configuration for cloud separation

### BGP Neighbor Configuration

TODO: Add FortiGate BGP neighbor templates

### Security Hardening

See [Security Hardening Standards](security-hardening.md)

---

## Network Management

### Out-of-Band Management (OOB)

**Standard:** Dedicated management VLAN with separate routing.

| Device Type | Management IP | VLAN | VRF/VDOM |
| --- | --- | --- | --- |
| Core Router | `10.x.x.1` | 999 | Mgmt |
| Firewall | `10.x.x.2` | 999 | Mgmt (or root VDOM) |

### Backup and Recovery

**Configuration Backup:**

- **Frequency:** After every configuration change (automated)
- **Retention:** Minimum 30 days of daily backups
- **Location:** Offsite storage with encryption
- **Cisco:** Archive via `copy running-config backup-url`
- **FortiGate:** Native backup via admin GUI or `execute backup ...`

### Firmware Updates

**Firmware Versioning:**

- Track all firmware versions in network inventory
- Cisco IOS-XE: Minimum supported version per device type
- FortiGate: Follow Fortinet patch schedule; test in lab first

**Update Procedures:**

- Schedule updates during change windows (see Maintenance Windows)
- Always backup running configuration before update
- Verify device functionality post-update
- Document update in change log

---

## Maintenance Windows

**Change Control Requirements:**

- All configuration changes require change control approval
- Changes scheduled during designated maintenance windows
- Backup created before any configuration modification
- Post-change verification documented
- Rollback plan documented before change execution

**Typical Maintenance Windows:**

- **Standard:** Monthly second Tuesday, 22:00-04:00 UTC
- **Emergency:** Ad-hoc approval for security issues
- **Blackout Periods:** Major business events; coordinated in advance
