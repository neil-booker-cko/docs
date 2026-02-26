# Cisco IOS: Optimized BFD Configuration Guide

This guide provides sample configurations for implementing **Bidirectional Forwarding
Detection (BFD)** with BGP, OSPF, and EIGRP on Cisco IOS/IOS-XE.

The configurations below use the **BFD Template** approach, which is the modern
standard for ensuring consistent timers across multiple protocols and interfaces.

## 1. Global BFD Template Configuration

Before configuring the routing protocols, define a BFD template to specify your
intervals.

```ios
bfd-template single-hop OPTIMIZED-BFD
 interval min-tx 300 min-rx 300 multiplier 3
!
```

* **min-tx/min-rx 300:** Sends/receives a heartbeat every 300 milliseconds.
* **multiplier 3:** Declares the link down after 3 missed packets (900ms total detection).

## 2. Interface Configuration

Apply the BFD template to the physical or logical interface where the neighbors
reside.

```ios
interface GigabitEthernet1
 description PEERING-LINK
 ip address 10.1.1.1 255.255.255.252
 bfd template OPTIMIZED-BFD
!
```

## 3. BGP Optimization with BFD

BGP relies on the `fall-over` command to link the BGP session status to the BFD
state.

```ios
router bgp 65001
 neighbor 10.1.1.2 remote-as 65002
 neighbor 10.1.1.2 fall-over bfd
 !
 ! Optional: Keep default BGP timers high to save CPU
 ! as BFD handles the fast detection.
 neighbor 10.1.1.2 timers 60 180
!
```

## 4. OSPF Optimization with BFD

For OSPF, you can enable BFD globally for all interfaces or selectively.

```ios
router ospf 1
 router-id 1.1.1.1
 ! Enable BFD on all OSPF-enabled interfaces
 bfd all-interfaces
 !
 ! Optional: Tune SPF throttling to react quickly to the BFD trigger
 timers throttle spf 50 200 5000
 timers lsa arrival 100
!
```

## 5. EIGRP Optimization with BFD

EIGRP supports BFD per-interface or for all interfaces within the autonomous system.

```ios
router eigrp 100
 ! For classic mode:
 bfd all-interfaces
 !
 ! For Named Mode (recommended):
 address-family ipv4 unicast autonomous-system 100
  af-interface default
   bfd
  exit-af-interface
 !
 ! Optional: Tune the hold-timer to remain at 15s for stability
 ! while BFD provides sub-second failure detection.
  af-interface GigabitEthernet1
   hello-interval 5
   hold-time 15
  exit-af-interface
!
```

## 6. Verification Commands

Use these commands to ensure BFD is correctly registered with the routing protocols.

| Command | Purpose |
| ----- | ----- |
| `show bfd neighbors` | Verify the active heartbeats and their intervals. |
| `show ip bgp neighbors &#124; inc BFD` | Check if a BGP neighbor is registered with BFD. |
| `show ip ospf interface` | Confirm OSPF BFD is enabled on the interface. |
| `show ip eigrp interfaces detail` | Verify EIGRP BFD registration. |
