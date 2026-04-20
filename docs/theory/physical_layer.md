# Physical Layer (L1) Fundamentals

Layer 1 defines the physical transmission of bits over cabling: copper, fiber, wireless. Understanding
cabling types, distances, and standards is critical for network design and troubleshooting.

## Copper Cabling

### Twisted-Pair Standards

All modern Ethernet uses twisted-pair copper (TP) with standardized categories.

| Category | Standard | Speed | Bandwidth | Distance | Use Case |
| --- | --- | --- | --- | --- | --- |
| **Cat5** | TIA/EIA-568B | 100 Mbps | 100 MHz | 100m | Legacy; avoid for new |
| **Cat5e** | TIA/EIA-568B | 1 Gbps | 100 MHz | 100m | ✅ Gigabit Ethernet |
| **Cat6** | TIA/EIA-568B | 10 Gbps | 250 MHz | 55m (10GbE), 100m (1GbE) | Data centers, future-proof |
| **Cat6A** | TIA/EIA-568B | 10 Gbps | 500 MHz | 100m | 10GbE over long distances |
| **Cat7** | ISO/IEC 11801 | 10 Gbps | 600 MHz | 100m | SFP+ over TP; not widely adopted |
| **Cat8** | TIA/EIA-568B | 40 Gbps | 2000 MHz | 30m | Data centers (short run) |

**Key Points:**

- **Cat5e is minimum for new deployments.** Cat5 (non-e) is 100 Mbps; phased out.
- **Cat6 for 10GbE over 55m.** Beyond 55m, use Cat6A or fiber.
- **Cat8 requires short runs** (30m); rarely used outside data centers.
- **Physical specs matter:** Cable construction, twist rate, shielding affect performance.

### Twisted-Pair Shielding

Shielding reduces electromagnetic interference (EMI):

| Type | Shielding | Cost | EMI Protection | Flexibility | Use |
| --- | --- | --- | --- | --- | --- |
| **UTP** | None | $ | Low | High | General office |
| **STP** | Foil+Drain | $$ | Medium | Low | Industrial environments |
| **ScTP** | Foil only | $$ | Medium | High | Data centers |
| **S/STP** | Braid+Foil | $$$ | High | Low | High-interference areas |

**Most common:** UTP (unshielded) for offices, STP/ScTP for data centers.

### Connector Standards

#### RJ45 (8P8C)

Standard connector for twisted-pair Ethernet:

```text
Pin Layout (TIA/EIA-568B - standard):
1: Orange/White
2: Orange
3: Green/White
4: Blue
5: Blue/White
6: Green
7: Brown/White
8: Brown
```

**Wiring Standards:**

- **568B (preferred):** Orange-White, Orange, Green-White, Blue, Blue-White, Green,
  Brown-White, Brown
- **568A:** Green-White, Green, Orange-White, Blue, Blue-White, Orange, Brown-White, Brown

**Use 568B on both ends for straight-through cables.** 568A/568B creates crossover
(rarely used in modern switching).

#### Connector Quality

Cheap connectors cause intermittent issues:

- ✅ Gold-plated contacts (corrosion-resistant)
- ✅ Shielded RJ45 for STP/ScTP cables
- ❌ Nickel-plated (tarnishes, poor contact)
- ❌ Plastic boots (snap off, expose pins)

---

## Fiber Optic Cabling

Fiber transmits data as light pulses; immune to electromagnetic interference and supports
long distances.

### Single-Mode vs Multi-Mode

| Aspect | Single-Mode (SMF) | Multi-Mode (MMF) |
| --- | --- | --- |
| **Core Diameter** | 8–10 μm | 50 μm, 62.5 μm |
| **Light Paths** | 1 mode | Multiple modes (rays) |
| **Distance** | 10 km+ | 300–2000 m |
| **Speed Support** | 100 Gbps+ | 10 Gbps typically |
| **Cost** | $$ (laser required) | $ (LED sufficient) |
| **Common Use** | Long-distance, ISP links | Data centers, buildings |
| **Dispersion** | Low (wavelength spread) | High (modal dispersion) |

**When to use:**

- **SMF:** WAN, ISP, inter-campus (1+ km)
- **MMF:** Data center, building cabling (< 500 m)

### Fiber Standards

| Standard | Medium | Speed | Distance | Wavelength | Use |
| --- | --- | --- | --- | --- | --- |
| **1000Base-SX** | MMF | 1 Gbps | 550 m | 850 nm | Intra-building |
| **1000Base-LX** | SMF/MMF | 1 Gbps | 10 km (SMF), 550 m (MMF) | 1310 nm | Long-distance |
| **10GBase-SR** | MMF | 10 Gbps | 400 m | 850 nm | Data center |
| **10GBase-LR** | SMF | 10 Gbps | 10 km | 1310 nm | WAN |
| **10GBase-ZR** | SMF | 10 Gbps | 80 km | 1550 nm | Long-haul |
| **100GBase-SR4** | MMF | 100 Gbps | 100 m | 850 nm (parallel) | Data center |
| **100GBase-LR4** | SMF | 100 Gbps | 10 km | 1310 nm (parallel) | Metro |

**Key Wavelengths:**

- **850 nm (near-IR):** Short-distance; LEDs sufficient
- **1310 nm (mid-IR):** Medium distance; lasers required
- **1550 nm (far-IR):** Long-distance; minimal dispersion

### Fiber Connectors

| Connector | Cores | Typical Use | Size |
| --- | --- | --- | --- |
| **LC** | 1 | Data centers, SFP modules | Small (1.25 mm ferrule) |
| **SC** | 1 | Legacy; being phased out | Medium (2.5 mm ferrule) |
| **ST** | 1 | Legacy; rarely used | Medium |
| **MPO/MTP** | 12/24 | High-density, 100GbE | Small; multiple cores |
| **APC** | 1 | Angled polished; lower reflection | Same sizes (LC-APC, SC-APC) |

**Modern standard:** LC connectors for single-fiber, MPO for multi-fiber bundles.

### Fiber Advantages and Disadvantages

✅ **Advantages:**

- Immune to electromagnetic interference
- Long distances (10 km+ on single-mode)
- Higher bandwidth (less attenuation over distance)
- No crosstalk between fibers

❌ **Disadvantages:**

- Higher cost (fiber, transceivers, tools)
- Fragile; requires careful handling
- Specialized test equipment (OTDR)
- Skill required for termination

---

## Distance and Speed Relationships

**Key principle:** Higher speeds support shorter distances.

```text
10GbE Copper (Cat6): 55m
10GbE Copper (Cat6A): 100m
10GbE Fiber (MMF): 400m
10GbE Fiber (SMF): 10 km

100GbE Copper: None standard
100GbE Fiber (MMF): 100m
100GbE Fiber (SMF): 10 km
```

**Why?** At high speeds, signal attenuation becomes critical. Fiber's lower attenuation allows
longer distances; copper suffers from:

- Insertion loss (resistance in wire)
- Return loss (reflections at impedance mismatches)
- NEXT (near-end crosstalk between pairs)

---

## Cabling Best Practices

✅ **Do:**

- Use Cat6 or Cat6A for new installations (future-proofing)
- Test all cable runs with a tester (cert of performance)
- Label both ends of every cable
- Use proper patch panel (TIA/EIA compliant)
- Keep cabling runs away from power lines (EMI source)
- Use shielded cabling in high-EMI environments
- Plan for future growth (run extra conduit)
- Document cabling plant (diagram, database)

❌ **Don't:**

- Use Cat5 (non-e) for new builds
- Mix 568A and 568B on same cable (causes crosstalk)
- Run cables alongside power/AC lines
- Exceed maximum bend radius (kinks damage cable)
- Reuse old patch cables without testing
- Use unshielded cable in noisy environments
- Terminate at the cable tray (use patch panel)
- Ignore cable slack (impacts airflow, creates fire hazard)

---

## Transceiver Modules (SFP, QSFP)

Small Form-Factor (SFP) and QSFP (Quad SFP) modules allow switches to support multiple fiber
types on demand.

### SFP (Small Form-Factor Pluggable)

Single-port transceiver module; supports speeds up to 10 Gbps.

| Type | Speed | Distance | Medium | Cost |
| --- | --- | --- | --- | --- |
| **SFP (1000Base-SX)** | 1 Gbps | 550 m | MMF | $ |
| **SFP (1000Base-LX)** | 1 Gbps | 10 km | SMF | $ |
| **SFP+ (10GBase-SR)** | 10 Gbps | 400 m | MMF | $$ |
| **SFP+ (10GBase-LR)** | 10 Gbps | 10 km | SMF | $$ |
| **SFP+ (10GBase-T)** | 10 Gbps | 30 m | Copper | $$ |
| **SFP-DA (Direct Attach)** | 10 Gbps | 7 m | Copper twinax | $ |

### QSFP (Quad SFP)

Four-channel transceiver; supports higher bandwidth (40 Gbps, 100 Gbps).

| Type | Speed | Lanes | Distance | Cost |
| --- | --- | --- | --- | --- |
| **QSFP+ (40GBase-SR4)** | 40 Gbps | 4×10 Gbps | 150 m | $$$ |
| **QSFP+ (40GBase-LR4)** | 40 Gbps | 4×10 Gbps | 10 km | $$$ |
| **QSFP28 (100GBase-SR4)** | 100 Gbps | 4×25 Gbps | 100 m | $$$$ |
| **QSFP28 (100GBase-LR4)** | 100 Gbps | 4×25 Gbps | 10 km | $$$$ |

---

## Troubleshooting Physical Layer Issues

### No Link (Interface Down)

```text
Symptoms: Interface shows "administratively down" or "down"

Checklist:
1. Check cable connection (both ends)
   show interfaces GigabitEthernet0/1  # Cisco

2. Test cable with tester (not a light tester)
   - Check continuity: all 8 wires
   - Measure insertion loss (should be < -5 dB at 1 Gbps)

3. Check transceiver (if SFP/QSFP)
   show interfaces transceiver
   show inventory  # Cisco

4. Verify speed/duplex (see Speed/Duplex Mismatch below)

5. Check for cable damage (kinks, cuts, EMI)
```

### Speed/Duplex Mismatch

```text
Symptoms: Interface up but slow, occasional drops, CRC errors

Common issue: One side set to 1000 Mbps full-duplex, other to 100 Mbps half-duplex

Fix:
- Set both sides to autonegotiate (preferred)
  interface GigabitEthernet0/1
    no speed 1000
    no duplex full
    # Now autonegotiates

- Or manually match speeds
  interface GigabitEthernet0/1
    speed 1000
    duplex full
```

### High CRC Errors

```text
Symptoms: show interfaces | include CRC

Causes:
1. Collisions (half-duplex network)
   - Upgrade to full-duplex

2. Cable damage
   - Replace cable

3. EMI from power lines
   - Reroute cabling away from power
   - Use shielded cable

4. Transceiver mismatch (fiber)
   - Ensure SMF-to-SMF or MMF-to-MMF
   - Check wavelength match (850 nm, 1310 nm, 1550 nm)
```

### Fiber Power Loss Too High

```text
Symptoms: show interfaces transceiver | include Power

Typical RX power: -3 dBm (weak signal), -20 dBm (normal)

Causes:
1. Cable exceeds distance limit
   - 1000Base-SX (550 m max on MMF)
   - Check with OTDR (Optical Time Domain Reflectometer)

2. Dirty or damaged fiber connectors
   - Clean with alcohol and lint-free cloth
   - Replace if scratched

3. Wrong fiber type
   - SX modules require MMF, not SMF
   - Check transceiver/cable pairing
```

---

## Reference: Common Cable Runs

| Link | Medium | Distance | Standard |
| --- | --- | --- | --- |
| Patch cable (device to patch panel) | Cat6e UTP | 5 m | TIA-568B |
| Backbone (rack to rack, same building) | Cat6A UTP or SMF | 100 m | TIA-568B |
| Between buildings | SMF | 1+ km | IEEE 802.3 |
| Data center (rack to switch) | Cat6A or MMF | 100 m | IEEE 802.3 |
| Long-haul WAN | SMF | 10+ km | RFC 7491 |

---

## Next Steps

- Review [Ethernet Evolution](ethernet_evolution.md) for speed standards
- Understand [Switching Fundamentals](switching_fundamentals.md) for link-layer concepts
- See [Port Aggregation](port_aggregation.md) for multi-link bonding
