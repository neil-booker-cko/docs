# FortiGate AAA Minimal Configuration

This template configures local users, TACACS+, RADIUS, and LDAP authentication. Replace
CAPITALIZED values.

## Configuration Breakdown

```fortios
config system admin
  edit "admin"
    set password YOUR_PASSWORD_HERE
    set accprofile "super_admin"
  next
end
```

Creates local admin user:

- **admin** = username
- **YOUR_PASSWORD_HERE** = password (replace with secure password)
- **accprofile "super_admin"** = full access to FortiGate
- **"change_admin"** = restricted profile (change configs, view logs only)

```fortios
config system tacacs+
  set server 192.0.2.10
  set secret TACACS_KEY_HERE
  set port 49
  set timeout 5
  set authen-type ascii
end
```

TACACS+ server configuration:

- **192.0.2.10** = TACACS+ server IP (replace with your server)
- **TACACS_KEY_HERE** = shared secret (must match server)
- **port 49** = TACACS+ port (default)
- **timeout 5** = seconds to wait before failover
- **authen-type ascii** = ASCII authentication (vs. PAP)

```fortios
config system radius
  edit 1
    set server 192.0.2.20
    set secret RADIUS_KEY_HERE
    set radius-port 1812
    set timeout 5
  next
end
```

RADIUS server configuration:

- **192.0.2.20** = RADIUS server IP
- **RADIUS_KEY_HERE** = shared secret
- **radius-port 1812** = RADIUS authentication port (1813 = accounting)

```fortios
config user ldap
  edit "LDAP-SERVER"
    set server "192.0.2.30"
    set cnid "cn"
    set dn "dc=example,dc=com"
    set type posixAccount
  next
end
```

LDAP directory integration:

- **192.0.2.30** = LDAP server (Active Directory compatible)
- **cnid "cn"** = common name attribute
- **dn "dc=example,dc=com"** = LDAP base DN (replace with your domain)
- **type posixAccount** = LDAP object class

```fortios
config system interface
  edit "port1"
    set allowaccess ping http https ssh snmp
  next
end
```

Restricts management access:

- **ping http https ssh snmp** = allowed protocols
- Omit `telnet` and `ftp` (insecure)

## Customization

### Add More Local Users

```fortios
edit "poweruser"
  set password POWER_PASSWORD_HERE
  set accprofile "super_admin"
next
```

### Use Only TACACS+ (No Local Fallback)

Configure authentication policy to require TACACS+ only (FortiGate admin portal).

### Change TACACS+ Authentication Type

For PAP (less secure, for legacy systems):

```fortios
set authen-type pap
```

### Add Multiple RADIUS Servers

```fortios
edit 2
  set server 192.0.2.21
  set secret RADIUS_KEY_HERE
  set radius-port 1812
next
```

### Restrict SSH Access to Specific IPs

```fortios
config system interface
  edit "port1"
    set allowaccess ssh
    set administrative-access-product-bundle implicit
    set ssh-access-level read-write
  next
end
```

## Verification

After applying:

```fortios
get system admin
! Check: Admin users and profiles

diagnose system session list
! Check: Current login sessions

get system tacacs+
! Check: TACACS+ server status

get system radius
! Check: RADIUS server configuration

diagnose debug authd
! Troubleshoot authentication issues
```

## Next Steps

- Configure SSH hardening (see [SSH minimal](ssh-minimal.md))
- Implement security hardening (see [Security hardening minimal](security-hardening-minimal.md))
- Review [FortiGate AAA configuration guide](../../fortigate/fortigate_aaa_config.md)
