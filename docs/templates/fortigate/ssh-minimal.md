# FortiGate SSH Minimal Configuration

This template enables SSH with strong key exchange, key-based authentication, and secure
algorithms.

## Configuration Breakdown

```fortios
config system global
  set ssh-hostkey-algorithm rsa2048
  set sshd-max-auth-tries 3
  set admin-ssh-port 22
  set admin-ssh-grace-time 120
  set admin-ssh-aes-gcm-16 enable
  set ssh-strict-key-exchange enable
end
```

SSH protocol hardening:

- **ssh-hostkey-algorithm rsa2048** = use 2048-bit RSA (sufficient; use rsa4096 for higher
  security)
- **sshd-max-auth-tries 3** = allow 3 failed login attempts before disconnecting
- **admin-ssh-port 22** = SSH port (change to non-standard port to reduce automated attacks)
- **admin-ssh-grace-time 120** = 120 seconds for initial connection
- **admin-ssh-aes-gcm-16 enable** = use AES-GCM-128 (stronger encryption)
- **ssh-strict-key-exchange enable** = enforce strict SSH protocol (prevents downgrade attacks)

```fortios
config system interface
  edit "port1"
    set allowaccess https ssh ping
  next
end
```

Restrict management access:

- **https ssh ping** = allow HTTPS, SSH, and ICMP only
- Omit `http` (insecure), `ftp`, `telnet` (deprecated)

```fortios
config system admin
  edit "admin"
    set ssh-public-key1 "ssh-rsa AAAAB3NzaC1yc2E... user@host"
  next
end
```

Adds SSH public key for key-based authentication (more secure than password):

- **ssh-public-key1** = user's public key (replace with actual key)

## Customization

### Use Stronger Key Algorithm

For ECDSA (faster, more modern):

```fortios
set ssh-hostkey-algorithm ecdsa256
! Or ecdsa384 for stronger
```

### Change SSH Port

To reduce automated attacks (note: less convenient):

```fortios
set admin-ssh-port 2222
```

Then connect: `ssh -p 2222 admin@10.0.0.1`

### Allow Only Specific Source IPs

```fortios
config firewall address
  edit "trusted-subnet"
    set subnet 192.0.2.0 255.255.255.0
  next
end

config firewall policy
  edit 1
    set srcaddr "trusted-subnet"
    set dstintf "port1"
    set action accept
    set schedule "always"
  next
end
```

### Require Certificate-Based Authentication

Generate certificate on FortiGate, export for client:

```fortios
config system certificate ca
  edit "admin-ca"
    set scep-url "https://ca.example.com/scep"
  next
end
```

### Add SSH Key for Automation

For scripts/Ansible:

```fortios
set ssh-public-key2 "ssh-rsa AAAAB3NzaC... automation@prod"
```

FortiGate supports up to 4 SSH public keys per user.

### Disable Password Authentication (Keys Only)

Not directly available in config; requires FortiGate 6.4.1+. Use LDAP/RADIUS instead:

```fortios
config system admin
  edit "admin"
    set remote-auth enable
    set remote-group "ldap-group"
  next
end
```

## Verification

After applying:

```fortios
get system global | grep ssh
! Check: SSH configuration settings

diagnose debug ssh
! Enable SSH debug for troubleshooting

show system admin
! Check: Admin users and SSH keys

get system interface port1
! Check: Port1 management access settings
```

## Next Steps

- Configure AAA with TACACS+/RADIUS (see [AAA minimal](aaa-minimal.md))
- Implement security hardening (see [Security hardening minimal](security-hardening-minimal.md))
- Review [FortiGate SSH configuration guide](../../fortigate/fortigate_ssh_config.md)
