# BGP Convergence: Failure Detection, Restoration, and Dampening

This documentation compares Border Gateway Protocol (BGP) behavior under different
timer configurations, BFD usage, and the impact of Route Dampening on recovery.

---

## 1. Failure Detection Timeline (Route Removal)

Failure detection is where BFD provides the most significant advantage. Standard
BGP relies on control-plane keepalives, whereas BFD operates in the forwarding plane
for sub-second reaction.

```mermaid
timeline
    title BGP Failure Detection (Route Removal)
    section Standard (60s/180s)
        T=0s : Link/Neighbor Failure
        T=60s : 1st Keepalive Missed
        T=120s : 2nd Keepalive Missed
        T=180s : Hold Timer Expires : Session Terminated : Route Removed
    section Tuned (3s/9s)
        T=0s : Link/Neighbor Failure
        T=3s : 1st Keepalive Missed
        T=6s : 2nd Keepalive Missed
        T=9s : Hold Timer Expires : Session Terminated : Route Removed
    section BFD (300ms x 3)
        T=0s : Link/Neighbor Failure
        T=300ms : 1st BFD Packet Missed
        T=600ms : 2nd BFD Packet Missed
        T=900ms : BFD Detects Failure : BGP Notified : Route Removed
```

---

## 2. Restoration Timeline (Clean Link)

When a stable link returns, restoration involves the TCP handshake and BGP state
machine. BFD facilitates the initial signal, but protocol overhead is the bottleneck.

```mermaid
timeline
    title BGP Route Restoration (Clean Link)
    section Standard BGP
        T=0s : Physical Link Restored
        T+2s : TCP 3-Way Handshake
        T+5s : BGP Open/Confirm Exchange
        T+10s : BGP Established : Updates Received : Route Installed
    section BGP with BFD
        T=0s : Physical Link Restored
        T+0.5s : BFD Session Up
        T+2s : BGP initiates TCP Handshake
        T+5s : BGP Open/Confirm Exchange
        T+10s : BGP Established : Updates Received : Route Installed
```

---

## 3. Restoration Timeline (Flapping Link / Dampening)

If a link has been unstable, **Route Dampening** prevents the route from being used
immediately upon restoration. The "Penalty" must decay below the "Reuse" limit before
the route is re-installed.

```mermaid
timeline
    title BGP Recovery with Route Dampening
    section Standard Dampening
        T=0s : Link Flapped 4 times (Penalty = 4000)
        T+15 min : Half-life decay reaches 2000 (Suppress Limit)
        T+30 min : Penalty decays to 750 (Reuse Limit) : Route Installed
    section Tuned Dampening
        T=0s : Link Flapped 4 times (Penalty = 4000)
        T+5 min : Half-life decay reaches 2000
        T+10 min : Penalty decays to 750 (Reuse Limit) : Route Installed
    section No Dampening
        T=0s : Link Restored
        T+10s : BGP Established : Route Installed
```

---

## 4. Comparison Summary

| Metric | Standard BGP | Tuned BGP | BGP with BFD |
| :--- | :--- | :--- | :--- |
| **Detection Time** | ~180 Seconds | ~9 Seconds | < 1 Second |
| **Restoration (Stable)** | ~10-15 Seconds | ~10-15 Seconds | ~10-15 Seconds |
| **Restoration (Flap)** | ~30-60 Minutes | ~10-20 Minutes | ~30-60 Minutes |
| **CPU Impact** | Very Low | **High** | Low (Offloaded) |
| **Stability** | Very High | Risky | Very High |

### Dampening Logic Reference

- **Penalty per Flap:** 1000
- **Suppress Limit:** 2000 (Default)
- **Reuse Limit:** 750 (Default)
- **Half-life:** 15 minutes (Standard) vs 5 minutes (Aggressive/Tuned)

### Engineering Guidance

- **Use BFD** for sub-second failure detection.
- **Avoid Tuned BGP Timers** if hardware supports BFD; they tax the control plane
    CPU.
- **Use Dampening** on EBGP edge interfaces to protect your internal network from
    unstable internet routes.
