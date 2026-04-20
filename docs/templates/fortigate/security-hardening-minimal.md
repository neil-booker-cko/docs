# FortiGate Security Hardening Minimal Configuration

This template applies foundational security controls: NTP, logging, SNMP hardening, management
interface restrictions, and strong cryptography.

## Configuration Breakdown

### Admin Session Timeout

```fortios
config system global
  set admintimeout 10
end
```

Idle timeout for admin sessions (minutes):

- **10** = 10-minute idle timeout (recommended 5-30 minutes)

### NTP Configuration

```fortios
config system global
  set timezone "UTC"
  set ntp-server 169.254.169.123
  set ntp-sync-interval 60
  set log-utc enable
end
```

Time synchronization (critical for logging, security audits):

- **timezone "UTC"** = set FortiGate timezone
- **ntp-server 169.254.169.123** = NTP endpoint (replace with your NTP server)
- **ntp-sync-interval 60** = sync every 60 seconds
- **log-utc enable** = log timestamps in UTC

```fortios
config system ntp
  set ntpsync enable
  set type fortiguard
  set server "0.ubuntu.pool.ntp.org" "1.ubuntu.pool.ntp.org"
end
```

NTP service configuration:

- **ntpsync enable** = synchronize system clock with NTP servers
- **type fortiguard** = use public NTP pool (or `type custom` for private servers)

### Logging

```fortios
config log syslogd setting
  set status enable
  set server 192.0.2.50
  set port 514
  set facility local7
  set source-ip 10.0.0.1
end
```

Syslog forwarding (send logs to central server):

- **192.0.2.50** = syslog server IP (replace with your server)
- **port 514** = syslog port
- **facility local7** = syslog facility (local0-local7 for custom apps)
- **source-ip 10.0.0.1** = ensure consistent sender IP

```fortios
config log disk setting
  set status enable
  set diskfull-action overwrite
end
```

Local disk logging:

- **status enable** = keep local logs
- **diskfull-action overwrite** = overwrite oldest logs when disk full

### SNMP Hardening

```fortios
config system snmp community
  edit 1
    set name "public"
    set hosts 192.0.2.100
    set status enable
  next
  edit 2
    set name "private"
    set hosts 192.0.2.100 192.0.2.101
  next
end
```

SNMP v2c with restricted access:

- **community "public"** = read-only community (replace with strong string)
- **hosts** = limit to specific IPs (trusted monitoring servers)

For SNMP v3 (recommended):

```fortios
config system snmp user
  edit "admin"
    set auth-proto sha
    set auth-pwd AUTH_PASSWORD
    set priv-proto aes
    set priv-pwd PRIV_PASSWORD
  next
end
```

### Management Interface Security

```fortios
config system interface
  edit "port1"
    set allowaccess ping https ssh
    set administrative-access-product-bundle implicit
  next
end
```

Restrict management access:

- **ping https ssh** = allow ICMP, HTTPS, SSH only
- Omit `http` (insecure), `ftp`, `telnet` (deprecated)
- **administrative-access-product-bundle implicit** = enforce product bundle restrictions

### Network Security

```fortios
config system global
  set accept-source-route disable
  set accept-redirects disable
  set revoke-wan-access disable
  set send-pmtu-icmp enable
end
```

IP security controls:

- **accept-source-route disable** = prevent loose/strict source routing attacks
- **accept-redirects disable** = block ICMP redirect attacks
- **revoke-wan-access disable** = prevent admin access from WAN (requires firewall policy)
- **send-pmtu-icmp enable** = allow PMTU discovery for optimal packet sizing

### Cryptography

```fortios
config system global
  set dh-params 2048
  set strong-crypto enable
end
```

Strong encryption:

- **dh-params 2048** = Diffie-Hellman key size (use 4096 for FIPS compliance)
- **strong-crypto enable** = use only strong ciphers (disable weak algorithms)

## Customization

### Change Syslog Server

Replace `192.0.2.50` with your syslog server:

```fortios
config log syslogd setting
  set status enable
  set server 10.0.0.100
  set port 514
end
```

### Add SNMP Trap Receivers

```fortios
config system snmp sysuptime
  set enable enable
end

config system snmp trap-receiver
  edit 1
    set ipaddr 192.0.2.60
    set port 162
    set query-v1-status enable
  next
end
```

### Restrict Admin Access by IP

```fortios
config firewall address
  edit "admin-subnet"
    set subnet 192.0.2.0 255.255.255.0
  next
end

config system interface
  edit "port1"
    set allowaccess ping https ssh
    set access-class "admin-subnet"
  next
end
```

### Enable Firewall Logging

```fortios
config log traffic
  set local enable
  set utm enable
end
```

Log all traffic (can be verbose; enable selectively).

## Verification

After applying:

```fortios
get system global | grep ntp
! Check: NTP configuration

get log syslogd setting
! Check: Syslog server configuration

diagnose sys ntp status
! Check: NTP sync status

get system snmp community
! Check: SNMP community configuration

show system interface port1
! Check: Management interface access settings
```

## Next Steps

- Configure AAA (see [AAA minimal](aaa-minimal.md))
- Configure SSH hardening (see [SSH minimal](ssh-minimal.md))
- Review [FortiGate security hardening guide](../../operations/security_hardening.md)
