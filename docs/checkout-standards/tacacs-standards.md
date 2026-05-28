# TACACS+ Standards

TACACS+ (Terminal Access Controller Access-Control System Plus) provides centralized
authentication, authorization, and accounting (AAA) for network device access.
Checkout runs `tac_plus` — an open-source TACACS+ server originally developed by Cisco.

For device-side AAA configuration (client), see [Equipment Configuration](equipment-config.md).

---

## tac_plus Server

**Config file:** `/etc/tac_plus.conf`

**Test config without reloading:**

```bash
tac_plus -P -C /etc/tac_plus.conf
```

**Accounting log:** `/var/log/tac_plus.acct`

The accounting log records authorized commands and sessions. It does not record authentication
attempts — check syslog for authentication failures.

---

## Global Configuration

```text
# Accounting log
accounting file = /var/log/tac_plus.acct

# Pre-shared key used by all client devices
key = <KEY>
```

Per-device keys can be set if needed (not standard):

```text
# host = <HOST_IP> {
#   key = <KEY>
# }
```

---

## User Configuration

```text
user = <USERNAME> {
    name = <FULL_NAME>
    member = <GROUP_NAME>
    login = PAM           # Cisco / Perle — authenticates against AD
    pap = PAM             # FortiGate — authenticates against AD
    enable = <PASSWORD>   # Enable mode password (Cisco only)
}

user = DEFAULT {
    name = Default User
    member = network_ro   # Fall-through to read-only if no specific user entry
    login = PAM
    pap = PAM
}

user = $enab15$ {
    name = Enable Password
    enable = <PASSWORD>   # Password for Cisco enable mode
}
```

**Notes:**

- Users can only be a member of one group
- Groups can be nested (one level only — a group can be a member of one other group)
- `login = PAM` / `pap = PAM` delegates password validation to PAM (Active Directory via SSSD)

---

## Access Control Lists

ACL entries are regular expressions. The `.` character matches any single character unless
escaped with `\`.

```text
# acl = <ACL_NAME> {
#   deny = 192\.168\.0\.13$
#   permit = 192\.168\.[01]\.
# }
```

Apply an ACL to a group to restrict which devices members can authenticate against:

```text
group = <GROUP_NAME> {
    acl = <ACL_NAME>
    ...
}
```

---

## Cisco Groups

```text
group = network_ro {
    default service = deny
    service = exec {
        priv-lvl = 1
    }
    cmd = show {
        permit .*
    }
    cmd = enable {
        permit .*
    }
    cmd = dir {
        permit .*
    }
    cmd = terminal {
        permit .*
    }
    cmd = more {
        permit .*
    }
    cmd = exit {
        permit .*
    }
    cmd = logout {
        permit .*
    }
    cmd = traceroute {
        permit .*
    }
    cmd = ping {
        permit .*
    }
}

group = network_rw {
    default service = permit
    service = exec {
        priv-lvl = 15
    }
}
```

---

## FortiGate Groups

FortiGate uses PAP for TACACS+ authentication. The `admin_prof` attribute maps to a FortiGate
admin profile configured locally on the device.

```text
group = network_ro {
    default service = deny
    service = fortigate {
        admin_prof = fortigate-read-only
    }
}

group = network_rw {
    default service = permit
    service = fortigate {
        admin_prof = super_admin
    }
}
```

---

## Perle Groups

```text
group = network_ro {
    default service = deny
    service = perlecli {
        priv-lvl = 8
    }
    service = perleweb {
        priv-lvl = 8
    }
}

group = network_rw {
    default service = permit
    service = perlecli {
        priv-lvl = 12
    }
    service = perleweb {
        priv-lvl = 12
    }
}
```

---

## Security Considerations

### Encryption Limitation

TACACS+ encrypts the packet body using an MD5-based XOR mechanism. RFC 8907 (the 2021 TACACS+
standard) explicitly classifies this as obfuscation rather than encryption:

> The obfuscation mechanism is not encryption and provides minimal confidentiality. It is
> vulnerable to known-plaintext attacks.

This is a protocol-level limitation with no in-protocol remediation. TACACS+ is retained over
alternatives (RADIUS, LDAP) because it is the only protocol that supports per-command
authorization — a core operational requirement for Checkout network device access control.

**Accepted risk:** MD5 obfuscation documented as a known limitation.

**Mitigations in place:**

- TACACS+ traffic isolated to the management network (VLAN 701); does not traverse the data plane
- Strong, unique shared keys per device group
- Full session and command accounting to centralized syslog (Datadog for long-term retention)

**Future path:** TACACS+ over TLS (RFC 9325, published 2022) wraps TACACS+ in TLS 1.3,
preserving per-command authorization while replacing MD5 obfuscation with proper encryption.
Monitor IOS-XE and `tac_plus-ng` for production-ready support before re-evaluating.

---

## Related Standards

- [Equipment Configuration](equipment-config.md) — Device-side AAA (TACACS+ client config)
- [Security Hardening](security-hardening.md) — SSH and access control standards
- [Syslog & Monitoring](syslog-monitoring-standards.md) — Authentication event logging
