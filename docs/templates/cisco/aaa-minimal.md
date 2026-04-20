# Cisco AAA Minimal Configuration

This template enables Authentication, Authorization, and Accounting (AAA) with local users and
optional TACACS+ integration. Replace CAPITALIZED values.

## Configuration Breakdown

```ios
aaa new-model
```

Enables AAA framework (required for all AAA features).

```ios
aaa authentication login default local
```

Uses local username/password for login authentication. Replace `local` with `group tacacs+` if using
TACACS+ exclusively.

```ios
aaa authentication enable default enable
```

Uses enable password for privilege escalation. For TACACS+:

```ios
aaa authentication enable default group tacacs+ local
```

```ios
aaa authorization exec default local
aaa accounting exec default start-stop group tacacs+
aaa accounting commands 15 default start-stop group tacacs+
```

Authorization: Controls what commands users can run (local database).
Accounting: Logs all exec sessions and privilege-15 commands to TACACS+.

```ios
tacacs server TAC-SERVER
  address ipv4 192.0.2.10
  key TACACS_KEY_HERE
  timeout 10
```

Defines TACACS+ server:

- **192.0.2.10** = TACACS+ server IP (replace with your server)
- **TACACS_KEY_HERE** = shared secret (must match server config)
- **timeout 10** = seconds to wait for response

```ios
username admin privilege 15 password YOUR_PASSWORD_HERE
username operator privilege 5 password YOUR_PASSWORD_HERE
```

Local user accounts as backup when TACACS+ unavailable:

- **privilege 15** = admin (full access)
- **privilege 5** = operator (limited commands)

```ios
line console 0
  login authentication default
  exec-timeout 5 0

line vty 0 4
  login authentication default
  exec-timeout 5 0
  transport input ssh
```

Console and telnet/SSH line config:

- **login authentication default** = use AAA login method
- **exec-timeout 5 0** = 5-minute idle timeout (0 = no timeout)
- **transport input ssh** = allow SSH only (no telnet)

## Customization

### Use TACACS+ Only (No Local Fallback)

```ios
aaa authentication login default group tacacs+ local
! Tries TACACS+ first, falls back to local
```

### Use RADIUS Instead of TACACS+

```ios
radius server RAD-SERVER
  address ipv4 192.0.2.20
  key RADIUS_KEY_HERE

aaa authentication login default group radius local
aaa accounting exec default start-stop group radius
```

### Add More Privilege Levels

```ios
username poweruser privilege 10 password YOUR_PASSWORD_HERE
! Custom privilege level between 5 and 15
```

### Enable Command Authorization from TACACS+

```ios
aaa authorization commands 15 default group tacacs+ local
aaa authorization commands 5 default group tacacs+ local
```

### Change Timeout (Minutes)

```ios
line vty 0 4
  exec-timeout 10 0
  ! 10 minutes idle timeout
```

## Verification

After applying:

```ios
show aaa methods
! Check: Authentication/authorization/accounting methods

show tacacs
! Check: TACACS+ server stats

show users
! Check: Current logged-in users

debug aaa authentication
! Troubleshoot AAA issues (disable with: no debug all)
```

## Next Steps

- Configure SSH certificates for key-based auth (see [SSH minimal](ssh-minimal.md))
- Implement security hardening (see [Security hardening minimal](security-hardening-minimal.md))
- Review [AAA configuration guide](../../cisco/cisco_aaa_config.md)
