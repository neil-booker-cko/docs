# Cisco SSH Minimal Configuration

This template enables SSH v2 with secure algorithms and authentication. Replace CAPITALIZED
values.

## Configuration Breakdown

```ios
ip ssh version 2
```

Forces SSH v2 only (deprecated SSHv1 disabled). IOS-XE defaults to v2, but explicit config ensures
it.

```ios
ip ssh rsa keypair-name SSH-KEY-1
crypto key generate rsa modulus 2048 label SSH-KEY-1
```

Generates 2048-bit RSA key pair (sufficient for most deployments). Use 4096-bit for higher
security:

```ios
crypto key generate rsa modulus 4096 label SSH-KEY-1
```

```ios
ip ssh authentication retries 3
ip ssh time-out 120
```

SSH protocol settings:

- **authentication retries 3** = allow 3 failed login attempts before disconnecting
- **time-out 120** = 120 seconds (2 minutes) for initial connection setup

```ios
ip scp server enable
```

Enables SCP (Secure Copy) for encrypted file transfers (needed for config/image transfers).

```ios
line vty 0 4
  transport input ssh
  exec-timeout 10 0
  login local
```

VTY (terminal) configuration:

- **transport input ssh** = allow SSH only (blocks telnet)
- **exec-timeout 10 0** = 10-minute idle timeout
- **login local** = use local username/password

```ios
username admin privilege 15 secret YOUR_PASSWORD_HERE
```

Local user account (use `secret` for encrypted storage, never plain-text `password`).

## Customization

### Change Key Modulus Size

For FIPS 140-2 compliance (4096-bit):

```ios
crypto key generate rsa modulus 4096 label SSH-KEY-1
```

### Use ECDSA Instead of RSA

Faster key exchange, smaller footprint:

```ios
ip ssh rsa keypair-name SSH-KEY-1
crypto key generate rsa modulus 2048 label SSH-KEY-1
! Or for ECDSA on newer IOS-XE:
crypto key generate ec label SSH-KEY-ECDSA
ip ssh ec-name SSH-KEY-ECDSA
```

### Change SSH Listen Port

(Non-standard port reduces automated attacks):

```ios
ip ssh port 2222 rotary 1
line vty 0 4 rotary 1
  transport input ssh
```

Then connect: `ssh -p 2222 admin@10.0.0.1`

### Allow Specific IPs Only

```ios
access-list 1 permit 10.0.0.0 0.0.0.255
line vty 0 4
  access-class 1 in
```

### Require AAA Authentication

Instead of `login local`:

```ios
aaa new-model
aaa authentication login default group tacacs+ local
line vty 0 4
  login authentication default
```

## Verification

After applying:

```ios
show ip ssh
! Check: SSH version, key info, timeout settings

show crypto key mypubkey rsa
! Check: RSA public key (for SSH client verification)

show users
! Check: Current SSH sessions

debug ip ssh
! Troubleshoot SSH connection issues
```

- Configure key-based authentication with SSH certificates (see [AAA minimal](aaa-minimal.md))
- Implement security hardening (see [Security hardening minimal](security-hardening-minimal.md))
