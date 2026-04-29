# Ethernet Evolution: From 10Base-T to 100GbE

Ethernet has evolved from 10 Mbps over coax (1980s) to 100+ Gbps over fiber. Understanding
the progression helps explain why older devices are incompatible, why speed negotiation matters,
and how to plan network upgrades.

---

## At a Glance

| Era | Speed | Year | Medium | Distance | Key Benefit | Status |
| --- | --- | --- | --- | --- | --- | --- |
| **Coax (10Base5/2)** | 10 Mbps | 1983–1985 | Thick/thin coax | 185–500 m | Shared bus | Obsolete |
| **Twisted-Pair (10Base-T)** | 10 Mbps | 1990 | Cat3 twisted pair | 100 m | Star topology, hubs | Legacy |
| **Fast Ethernet (100Base-TX)** | 100 Mbps | 1995 | Cat5 twisted pair | 100 m | Autonegotiation | Rare |
| **Gigabit Ethernet (1000Base-T)** | 1 Gbps | 1999 | Cat5e/Cat6 | 100 m | 4-pair simultaneous | Common |
| **10 Gigabit (10GBase-T, -SR, -LR)** | 10 Gbps | 2002–2006 | Fiber/Cat6A | 100 m–10 km | Data center backbone | Widespread |
| **100 Gigabit (100GBase-SR4, -LR4)** | 100 Gbps | 2010 | Parallel optics (4×25G) | 100 m–10 km | Hyperscale DCs | Standard |
| **400 Gigabit (400GBase-ZR)** | 400 Gbps | 2022 | Dense wavelengths | 120+ km | Metro/long-haul | Emerging |

---

## Timeline and Standards

### The Early Years (1980s-1990s)

| Standard | Year | Speed | Medium | Distance | Status |
| --- | --- | --- | --- | --- | --- |
| **10Base5** | 1983 | 10 Mbps | Thick coax | 500 m | ❌ Obsolete |
| **10Base2** | 1985 | 10 Mbps | Thin coax | 185 m | ❌ Obsolete |
| **10Base-T** | 1990 | 10 Mbps | Twisted-pair (Cat3) | 100 m | ❌ Legacy only |
| **10Base-F** | 1991 | 10 Mbps | Fiber | 2 km | ❌ Obsolete |

**Key Point:** Before 10Base-T (1990), Ethernet used shared coaxial bus. One cable, all devices
shared the medium, collisions were common. **10Base-T introduced hubs and twisted-pair,**
allowing star topology.

### Gigabit Era (1998-2010)

| Standard | Year | Speed | Medium | Distance | Max Stretch |
| --- | --- | --- | --- | --- | --- |
| **100Base-TX** | 1995 | 100 Mbps | Twisted-pair (Cat5) | 100 m | 200 m (two hubs) |
| **100Base-FX** | 1995 | 100 Mbps | Fiber (MMF) | 2 km | — |
| **1000Base-T** | 1999 | 1 Gbps | Twisted-pair (Cat5e) | 100 m | 200 m (two switches) |
| **1000Base-SX** | 1999 | 1 Gbps | Fiber (MMF) | 550 m | — |
| **1000Base-LX** | 1999 | 1 Gbps | Fiber (SMF) | 10 km | — |
| **1000Base-ZX** | 2006 | 1 Gbps | Fiber (SMF) | 70 km | — |

**Key Point:** 1000Base-T (Gigabit Ethernet) required new cable (Cat5e) and new NICs. Introduced
4-pair transmission (all pairs active simultaneously for TX and RX). **Autonegotiation** allowed
mixed speeds on same network.

### 10 Gigabit Era (2002-2015)

| Standard | Year | Speed | Medium | Distance | Cost | Use |
| --- | --- | --- | --- | --- | --- | --- |
| **10GBase-T** | 2006 | 10 Gbps | Cat6A (100m) | 30-100 m | $$ | Server to TOR |
| **10GBase-SR** | 2002 | 10 Gbps | MMF | 400 m | $ | Rack-to-rack |
| **10GBase-LR** | 2002 | 10 Gbps | SMF | 10 km | $$ | Data center WAN |
| **10GBase-ZR** | 2004 | 10 Gbps | SMF | 80 km | $$$ | Metro/long-haul |
| **10GBase-LRM** | 2008 | 10 Gbps | Legacy MMF | 220 m | $ | Older fiber |
| **10GBase-DA** | — | 10 Gbps | Copper twinax | 7 m | $ | Server cabling |

**Key Points:**

- **10GBase-T over copper** was expensive; most adopted fiber for 10 Gbps
- **Direct Attach (DA) cables** became popular for short server-to-switch runs
  (cheaper than SFP modules)

- **10GBase-ZR allowed submarine cables** and long-haul terrestrial links

### 100 Gigabit Era (2010-Present)

| Standard | Year | Speed | Lanes | Medium | Distance | Use |
| --- | --- | --- | --- | --- | --- | --- |
| **40GBase-SR4** | 2011 | 40 Gbps | 4×10 Gbps | MMF | 150 m | Data center |
| **40GBase-LR4** | 2011 | 40 Gbps | 4×10 Gbps | SMF | 10 km | Data center WAN |
| **100GBase-SR4** | 2010 | 100 Gbps | 4×25 Gbps | MMF | 100 m | Data center |
| **100GBase-LR4** | 2010 | 100 Gbps | 4×25 Gbps | SMF | 10 km | Long-haul |
| **100GBase-CR4** | 2010 | 100 Gbps | 4×25 Gbps | Twinax | 7 m | Server-switch |
| **100GBase-DR** | 2020 | 100 Gbps | 1 lane | SMF | 500 km | Submarine |
| **400GBase-ZR** | 2022 | 400 Gbps | 16 lanes | SMF | 120 km | Long-haul |

**Key Points:**

- **40 Gbps was intermediate;** many sites skipped to 100 Gbps
- **400 Gbps now mainstream** in hyperscale data centers
- **Parallel optics** (4×25 Gbps in 100GBase-SR4) allows higher speeds over MMF

---

## Speed Negotiation: Autonegotiation

Devices automatically detect the highest common speed and duplex setting.

### How It Works

1. Both devices send Fast Link Pulse (FLP) frames
1. Each advertises supported speeds:

    - 10 Mbps half/full-duplex
    - 100 Mbps half/full-duplex
    - 1000 Mbps full-duplex only
1. Both agree on fastest common speed
1. Prefer full-duplex; fallback to half-duplex if forced

### Autonegotiation States

```text
Ideal: Both auto
  Device A (auto) ↔ Device B (auto)
  → Both negotiate → 1000 Mbps full-duplex ✅

Mismatch (common problem):
  Device A (1000 Mbps manual full) ↔ Device B (auto)
  → Device B detects no FLP signal
  → Falls back to 100 Mbps half-duplex ⚠️
  → Mismatch: Device A = 1000 Mbps, Device B = 100 Mbps ❌

Fix: Set both to auto or both to same manual speed
```

### Autonegotiation Failures

**Problem:** Device A (forced 1000/full) ↔ Device B (auto) = mismatch

**Symptoms:**

- Interface up but traffic is slow
- Frequent CRC errors
- Drops every few seconds

**Root Cause:** When autonegotiation fails, device defaults to 100 Mbps half-duplex
(slowest safe speed). If one side is manually forced to 1000 Mbps full, they can't communicate
properly.

**Solution:**

```ios
! Option 1: Set both to auto (preferred)
interface GigabitEthernet0/1
  no speed
  no duplex
  ! Default is now autonegotiate

! Option 2: Manually set both to same speed
interface GigabitEthernet0/1
  speed 1000
  duplex full
```

**Best Practice:** Always use autonegotiation unless you have a specific reason to override.

---

## Speed Evolution and Bandwidth

Notice how speed roughly **10x every decade:**

| Era | Speed | Year | Use |
| --- | --- | --- | --- |
| 1980s | 10 Mbps | 1983 | Shared coax |
| 1990s | 100 Mbps | 1995 | Star topology, hubs |
| 2000s | 1 Gbps | 1999 | Switched networks |
| 2010s | 10 Gbps | 2002 | High-speed servers |
| 2020s | 100 Gbps | 2010 | Data center; 400 Gbps emerging |

**Why the jump?** CPU and NIC hardware got faster, fiber improved, silicon compression techniques
advanced. Economics also drove it: hyperscale data centers needed faster interconnects to justify
the cost.

---

## Backward Compatibility and Mixed-Speed Networks

### Gigabit Networks (1 Gbps) with 100 Mbps Devices

**Scenario:** 1 Gbps switch, some devices are 100 Mbps only

✅ **Works fine.** Switch negotiates 100 Mbps with those devices, 1000 Mbps with others.

### Mixing 10GbE and 1GbE

**Scenario:** 10GbE uplink, 1GbE downlinks

✅ **Works fine.** Oversubscription is normal:

```text
  10GbE uplink (10 Gbps)
  │
  ├─ 1GbE port 1 (1 Gbps)
  ├─ 1GbE port 2 (1 Gbps)
  └─ 1GbE port 3 (1 Gbps)

  Total downlink: 3 Gbps < 10 Gbps uplink (undersubscribed actually)

  Common ratio: 10:1 oversubscription = 10×1Gbps ports : 1×10Gbps uplink
```

### Old Hubs with Switches

❌ **Doesn't work well.** Hub is shared medium (10 Mbps half-duplex bus); switch is switched
(1 Gbps full-duplex). Hub forces negotiation down to 10 Mbps half-duplex.

**Lesson:** Don't mix hubs and switches. Hubs are obsolete.

---

## MTU and Frame Sizes

Maximum Transmission Unit (MTU) is the largest frame a link can carry.

| Standard | MTU | Jumbo | Use |
| --- | --- | --- | --- |
| **Ethernet II** | 1500 bytes | 1518 (with FCS) | Standard |
| **Jumbo Frames** | 9000 bytes | 9018 (with FCS) | Data centers, storage |
| **Ethernet over IP** | 1500 bytes | — | Tunneled traffic |

### Why Jumbo Frames Matter

**Fewer packets needed for same data:**

- Standard MTU: 1500 bytes = 100 packets for 150 KB
- Jumbo MTU: 9000 bytes = 17 packets for 150 KB

**Reduced overhead:**

- Each packet = frame header (14 bytes) + IP header (20 bytes) + TCP header (20 bytes) = 54 bytes overhead
- 100 packets × 54 bytes = 5.4 KB overhead
- 17 packets × 54 bytes = 918 bytes overhead

**But:** Jumbo frames add latency and can fragment on internet. Use only within data centers with
all devices supporting it.

### Configuring MTU

```ios
! Cisco
interface GigabitEthernet0/1
  mtu 9000
  ! Now supports jumbo frames

! FortiGate
config system interface
  edit "port1"
    set mtu 9000
  next
end
```

⚠️ **Warning:** All devices on a link must support the same MTU, or fragmentation occurs.

---

## Speed Limitations by Distance

The fundamental relationship: **Longer distances require lower speeds (more forgiving signals).**

```text
Copper (Twisted-Pair):
  10Base-T:    100 m @ 10 Mbps
  100Base-TX:  100 m @ 100 Mbps
  1000Base-T:  100 m @ 1 Gbps
  10GBase-T:   30 m @ 10 Gbps (Cat6A), 100 m @ 10 Gbps (Cat6A specialized)

Fiber (MMF):
  1000Base-SX:  550 m @ 1 Gbps (850 nm)
  10GBase-SR:   400 m @ 10 Gbps (850 nm)
  100GBase-SR4: 100 m @ 100 Gbps (850 nm, parallel)

Fiber (SMF):
  1000Base-LX:   10 km @ 1 Gbps (1310 nm)
  10GBase-LR:    10 km @ 10 Gbps (1310 nm)
  100GBase-LR4:  10 km @ 100 Gbps (1310 nm, parallel)
  10GBase-ZR:    80 km @ 10 Gbps (1550 nm)
```

**Key insight:** Attenuation (signal loss) increases with distance and frequency. Higher speeds
(higher frequency) attenuate faster, requiring shorter distances or better media (fiber).

---

## Troubleshooting Speed Issues

### Interface Negotiates Slow Speed

```text
Problem: show interfaces shows 100 Mbps, expected 1000 Mbps

Causes:

1. Autonegotiation mismatch (see above)
1. Old cable (Cat3 instead of Cat5e)
   → Replace with Cat6
1. Transceiver issue (if fiber)
   → Check with show inventory
1. NIC driver outdated
   → Update OS/driver
```

### Link Flaps (Up/Down Cycling)

```text
Problem: Interface keeps bouncing up/down

Causes:

1. Bad cable
   → Test with cable tester
   → Look for: bad continuity, too high insertion loss
1. Dirty fiber connector
   → Clean with alcohol wipe
1. Power level too low (fiber)
   → Check RX power with show transceiver
1. Speed mismatch causing instability
   → Force both sides to auto
1. EMI causing signal issues
   → Move cable away from power lines
```

### High Throughput, High Latency

```text
Problem: Can copy files at 1 Gbps but latency > 100 ms

Likely cause: Acceptable; check if it's expected:

  - 10 km of fiber = ~50 ms latency (speed of light)
  - WAN link = expected delays

If not expected:

  - Check for buffers filling up (congestion)
  - Measure latency to nearest hop (ping)
  - Look for retransmits (tcpdump, Wireshark)
```

---

## Future (Beyond 100 Gbps)

| Standard | Year | Speed | Status |
| --- | --- | --- | --- |
| **400GBase-ZR** | 2022 | 400 Gbps | Deployed in hyperscale DCs |
| **800GBase-DR** | 2024 | 800 Gbps | Emerging |
| **1.6TBase-DR** | 2026 | 1.6 Tbps | Research phase |

Speeds will continue to 10x; cost per Gbps continues falling.

---

## Notes / Gotchas

- **10Base-T Coil Cables (Crossover vs Straight):** Pre-1990s networks used 10Base-T on Cat3
  with crossover cables between hubs (MDI-X) and straight-through to devices (MDI). Modern
  auto-MDIX eliminates the distinction; older equipment may fail silently if cabling is
  reversed.

- **100Base-T Required New Cable:** 100Base-TX requires Cat5 (100Base-TX over Cat3 fails
  intermittently). Upgrading from 10Base-T to 100Base-T sometimes required rewiring — many
  sites mixed speeds via autonegotion.

- **1000Base-T Uses All 4 Pairs Simultaneously:** Unlike 100Base-TX (which uses 2 pairs),
  1000Base-T transmits and receives on all 4 pairs at once. Crosstalk or EMI affecting any
  pair degrades the link; a single bad wire can cause intermittent Gbps-level failures.

- **Fiber Connector Cleanliness Matters:** SMF (Single-Mode Fiber) connectors are 8-micron
  cores. A speck of dust causes immediate signal loss. Always clean fiber ends before
  connecting; dirty connections cause intermittent errors and bit errors invisible to basic
  diagnostics.

- **Speed Negotiation Failures are Silent:** If autonegotiation fails (bad cable, mismatched
  transceivers), the interface may lock to a lower speed silently (e.g., 100 Mbps instead of
  1 Gbps). Always verify negotiated speed: `show interface <port> | include speed` or
  `show transceiver detail`.

---

## See Also

- [Physical Layer Cabling & Standards](../theory/physical_layer.md) — Twisted-pair and fiber
  specifications

- [Switching Fundamentals](../theory/switching_fundamentals.md) — Hubs, switches, and
  broadcast domains

- [Interface & Routing Fundamentals](../theory/interface_routing_fundamentals.md) — Interface
  configuration and autonegotiation

- [Cisco Interface Configuration](../cisco/cisco_interface_config.md) — Speed and duplex
  tuning

- [Network Troubleshooting: Speed & Duplex Issues](../operations/troubleshooting_speed_duplex.md)
  — Diagnosis and recovery
