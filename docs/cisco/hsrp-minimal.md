# Cisco HSRP Minimal Configuration

This template configures HSRP for gateway redundancy. One router acts as Active, the other as
Standby. Replace CAPITALIZED values.

## Configuration Breakdown

### Primary Router (Active)

```ios
interface GigabitEthernet0/0/1
  ip address 10.0.1.1 255.255.255.0
```

Router's physical interface on the LAN (replace with your interface and IP).

```ios
  standby version 2
```

Uses HSRP version 2 (supports IPv6; recommended over v1).

```ios
  standby 1 ip 10.0.1.254
```

Virtual IP address that clients use as default gateway. Replace `10.0.1.254` with an IP in your
LAN subnet (typically the broadcast address or .254).

```ios
  standby 1 priority 110
```

Priority: higher priority = more likely to be Active (range 0-255, default 100). Primary has 110
to become active.

```ios
  standby 1 preempt
```

Allows this router to **take over** if it comes back online and has higher priority.

### Secondary Router (Standby)

Same configuration but:

```ios
  standby 1 priority 100
```

Lower priority (100) means it will be Standby if both routers are up.

## Customization

### Change Interface

Replace `GigabitEthernet0/0/1` with your actual interface (e.g., `Ethernet0/0`).

### Change Virtual IP

```ios
standby 1 ip 10.0.1.254
```

Replace `10.0.1.254` with the IP address you want clients to use as default gateway.

### Change Priority

Increase primary priority to ensure it's active:

```ios
standby 1 priority 110    ! Primary (higher = active)
standby 1 priority 100    ! Standby (lower = backup)
```

### Add HSRP Authentication (Recommended)

For security, add authentication (text or MD5):

```ios
standby 1 authentication md5 key-string YOUR_PASSWORD_HERE
```

Must be **identical on both routers**.

### IPv6 Support

HSRP v2 supports IPv6. Add:

```ios
standby 1 ipv6 2001:db8::1/64
```

## Verification

After applying:

```ios
show standby
! Check: Group state (Active/Standby), Virtual IP, priority

show standby brief
! Quick summary

show interface GigabitEthernet0/0/1 | include HSRP
! Verify HSRP enabled on interface
```

## Testing Failover

1. **On the active router**, shut down the interface or reload:

   ```ios
   interface GigabitEthernet0/0/1
   shutdown
   ```

2. **On the standby router**, verify it becomes active:

   ```ios
   show standby
   ! Should show state = "active"
   ```

3. **Bring primary back online** (if it has `preempt`):

   ```ios
   interface GigabitEthernet0/0/1
   no shutdown
   ```

4. **Primary takes over** (because it has higher priority and `preempt` enabled).

- Add BFD for sub-second failover (see [BFD minimal](bfd-minimal.md))
- Implement HSRP on multiple subnets for redundancy
- Review [HSRP configuration guide](../cisco/cisco_hsrp_vrrp.md) for advanced features
