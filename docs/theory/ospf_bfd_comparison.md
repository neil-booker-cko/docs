# OSPF Convergence: Standard vs. Tuned vs. Fast Hellos vs. BFD

## 1. Overview & Principles

OSPF detects failure when it stops receiving "Hello" packets. While naturally faster
than BGP, Default Settings rely on a "Dead Timer" that can lead to significant traffic
loss.

### The Dead Timer Problem

In standard OSPF, a router waits 4 times the Hello interval before declaring a neighbor
dead. On a 10Gbps link, 40 seconds of failure (Default Settings) results in **400
Gigabits of dropped data**.

### Tuned Timers vs. Fast Hellos

- **Tuned Timers (2s/8s):** A safe compromise for legacy hardware. Reduces detection

    from 40s to 8s without significantly stressing the CPU.

- **Fast Hellos (Sub-second):** Setting OSPF to sub-second hellos (e.g., `minimal

    hello-multiplier`) forces the CPU to process hellos constantly. Risks "False
    Positives" if the CPU hits 100% due to an unrelated task.

- **BFD (The Watchdog):** Sub-second detection offloaded to the forwarding plane.

    Allows OSPF to bypass the Dead Timer and run SPF immediately.

## 2. Failure Detection & Restoration Timelines

### Failure Detection (Neighbor Down)

```mermaid
timeline
    title OSPF Failure Detection
    section Default Settings (10s/40s)
        T=0s : Link/Neighbor Fails
        T=40s : Dead Timer Expires : Neighbor Down : SPF Calculation Triggered
    section Tuned (2s/8s)
        T=0s : Link/Neighbor Fails
        T=8s : Dead Timer Expires : Neighbor Down : SPF Calculation Triggered
    section Fast Hellos (1s/4s)
        T=0s : Link/Neighbor Fails
        T=4s : Dead Timer Expires : Neighbor Down : SPF Calculation Triggered
    section OSPF with BFD
        T=0s : Link/Neighbor Fails
        T=300ms : BFD Packet Miss 1
        T=900ms : BFD Detects Failure : OSPF Notified : SPF Calculation Triggered
```

### Restoration Timeline (Adjacency)

```mermaid

timeline
    title OSPF Restoration (Adjacency)
    section Standard OSPF
        T=0s : Physical Link Restored
        T+1s : Hello Sent / Received
        T+2s : 2-Way State (Neighbors See Each Other)
        T+3s : ExStart/Exchange (LSA Headers Swapped)
        T+5s : Loading State (LSAs Requested/Sent)
        T+6s : Full Adjacency : SPF Run : Route Installed
    section OSPF with BFD
        T=0s : Physical Link Restored
        T+0.5s : BFD Session Establishes
        T+1s : OSPF Hello / 2-Way State
        T+5s : SPF Run : Route Installed
```

## 3. Configuration Snippets

### Cisco IOS-XE OSPF with BFD

```ios

router ospf 1
 router-id 1.1.1.1
 bfd all-interfaces
 !
 ! Tune SPF throttling to react immediately to the BFD trigger
 timers throttle spf 50 200 5000
 timers lsa arrival 100
```

## 4. Comparison Summary

| Metric | Default Settings | Tuned Timers | Fast Hellos | OSPF + BFD |
| ----- | ----- | ----- | ----- | ----- |
| **Hello / Dead** | 10s / 40s | 2s / 8s | 1s / 4s | 10s / 40s (Backup) |
| **Detection Time** | \~40 Seconds | \~8 Seconds | \~4 Seconds | **< 1 Second** |
| **CPU Impact** | Low | Low-Medium | **High** | Low (Offloaded) |
| **Stability** | Very High | High | Moderate | **High** |
| **SPF Trigger** | After Dead Timer | After Dead Timer | After Dead Timer | **Immediate (via BFD)** |

## 5. Verification & Troubleshooting

| Command | Purpose |
| ----- | ----- |
| `show ip ospf interface` | Confirm OSPF BFD is enabled on the interface. |
| `show bfd neighbors` | Verify active heartbeats and negotiated intervals. |
| `show ip ospf neighbor` | Confirm adjacency status is "FULL". |
| `debug ip ospf adj` | Monitor adjacency state machine transitions. |

### Engineering Guidance

- **Use BFD** whenever the hardware supports it. It is the only way to achieve
sub-second

sub-second

    convergence safely.

- **Tuned Timers (2s/8s)** are a safe compromise for networks where BFD is not available

    and 8 seconds of downtime is acceptable.

- **Fast Hellos** should be a last resort for links where BFD is not available and

    convergence must be under 5 seconds.

- **LSA Throttling:** Pair BFD with tuned LSA generation timers (throttle SPF) for

    true "carrier-grade" convergence.
