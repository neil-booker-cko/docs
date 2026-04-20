# Cisco Security Hardening Minimal Configuration

This template applies foundational security controls: service disabling, NTP, logging, SNMP
hardening, and control plane protection.

## Configuration Breakdown

### Disable Unnecessary Services

```ios
no service pad
no service finger
no service udp-small-servers
no service tcp-small-servers
no ip directed-broadcast
no cdp run
```

Disables attack surface:

- **pad, finger, udp/tcp-small-servers** = legacy services (rarely needed)
- **directed-broadcast** = prevents directed broadcast amplification attacks
- **cdp run** = disables Cisco Discovery Protocol (optional; disable if not needed)

### NTP Configuration

```ios
ntp server 169.254.169.123 prefer
ntp source Loopback0
```

Time synchronization (critical for logging accuracy, TLS certificates):

- **169.254.169.123** = AWS/cloud NTP endpoint (replace with your NTP server)
- **prefer** = use this server as primary
- **ntp source** = ensure consistent source IP for NTP requests

### Logging

```ios
logging host 192.0.2.50
logging trap informational
logging source-interface Loopback0
logging buffered 10000
```

Send logs to syslog server:

- **192.0.2.50** = syslog server IP (replace with your server)
- **informational** = log level (debug, info, notice, warning, error)
- **source-interface Loopback0** = ensures consistent sender IP
- **buffered 10000** = keep 10K lines local buffer before syslog

### SNMP Security

```ios
snmp-server community PUBLIC_STRING ro
snmp-server community PRIVATE_STRING rw 1
access-list 1 permit 192.0.2.0 0.0.0.255
snmp-server access-list 1
```

SNMP v2c with restricted access:

- **PUBLIC_STRING** = read-only community (replace with strong string)
- **PRIVATE_STRING** = read-write community (restrict to admin subnet)
- **access-list 1** = limit SNMP to trusted subnet (192.0.2.0/24)

For SNMP v3 (recommended):

```ios
snmp-server group ADMIN v3 priv
snmp-server user admin ADMIN v3 auth sha AUTH_KEY priv aes 256 PRIV_KEY
snmp-server access-list 1
```

### Banners and Passwords

```ios
enable secret ENABLE_PASSWORD_HERE
banner motd ^C
WARNING: Unauthorized access is prohibited.
All activity is logged and monitored.
^C
```

Credentials and login warnings:

- **enable secret** = encrypted enable password (use `secret`, never `password`)
- **banner motd** = message-of-the-day before login (discourages unauthorized access)

### Line Security

```ios
line console 0
  exec-timeout 5 0
  logging synchronous
  no modem InOut

line vty 0 4
  exec-timeout 10 0
  logging synchronous
  transport input ssh
```

Terminal line hardening:

- **exec-timeout** = idle timeout (5 min console, 10 min SSH)
- **logging synchronous** = don't interrupt command input with log messages
- **no modem InOut** = disable modem (console only)
- **transport input ssh** = SSH only (no telnet)

### IP Security

```ios
service tcp-keepalives-in
service tcp-keepalives-out
no ip redirects
no ip source-route
```

Network layer protections:

- **tcp-keepalives** = detect broken connections quickly
- **no redirects** = prevent ICMP redirect attacks
- **no source-route** = block loose/strict source routing attacks

### Control Plane Protection

```ios
ip cef
control-plane
  service-policy input COPP-POLICY
```

Enable CEF (Cisco Express Forwarding) and apply Control Plane Policing (COPP) policy to protect
the router's management plane from DDoS attacks.

## Customization

### Change Syslog Server

Replace `192.0.2.50` with your syslog server IP:

```ios
logging host 192.0.2.100
logging trap warning
! warning = only critical, alert, emergency, error
```

### Change NTP Server

Replace `169.254.169.123` with your NTP server:

```ios
ntp server 10.0.0.1 prefer
```

### Add More SNMP Access

```ios
access-list 1 permit 192.0.2.0 0.0.0.255
access-list 1 permit 10.0.0.0 0.0.255.255
snmp-server access-list 1
```

### Enable AAA Integration

```ios
aaa new-model
aaa authentication login default local
aaa authorization exec default local
```

### Disable Specific Unused Services

```ios
no ip http server
no ip http secure-server
no service config
```

## Verification

After applying:

```ios
show services
! Check: Unnecessary services disabled

show ntp status
! Check: NTP synchronization status

show logging
! Check: Log buffer and syslog configuration

show snmp
! Check: SNMP configuration and access lists

show running-config | include (service | no service)
! Check: All security-related service settings
```

- Configure AAA for centralized authentication (see [AAA minimal](aaa-minimal.md))
- Configure SSH (see [SSH minimal](ssh-minimal.md))
