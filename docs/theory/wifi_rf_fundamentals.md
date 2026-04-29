# WiFi RF Fundamentals

Radio Frequency (RF) propagation determines WiFi coverage, throughput, and reliability.
Understanding channels, bands, signal strength (RSSI), signal-to-noise ratio (SNR), and interference
is essential for site surveys, troubleshooting, and capacity planning in wireless networks.

---

## At a Glance

| Concept | Definition | Typical Range | Impact |
| --- | --- | --- | --- |
| **RSSI** | Received Signal Strength Indicator | -30 to -90 dBm | Higher (closer to 0) = stronger signal; -67 dBm is typical minimum for data |
| **SNR** | Signal-to-Noise Ratio | 5–40 dB | >25 dB is excellent; <15 dB degrades throughput |
| **Path Loss** | Signal attenuation over distance | Exponential with distance | Doubles every 6 dB; halving distance gains ~6 dB |
| **Fading** | Multipath signal cancellation | Varies by environment | Causes dropouts; diversity antennas mitigate |
| **Interference** | Overlapping signals from other networks | CoChannel / Adjacent | Reduces SNR; channel selection critical |
| **Noise Floor** | Background RF energy | -95 to -80 dBm | Depends on band congestion; higher in 2.4 GHz |

---

## Frequency Bands and Channels

### 2.4 GHz Band

Frequencies 2400–2484 MHz. **Only 3 non-overlapping channels globally:** 1, 6, 11 (US/EIRP
regulations). Channels 12–14 allowed in Japan/other regions but rare.

**Characteristics:**

- Excellent range and wall penetration

- Heavily congested (Bluetooth, microwave ovens, cordless phones, neighboring WiFi)

- High noise floor, especially in dense urban areas

- Limited to 20 MHz channel width without significant overlap on channels 1, 6, 11

### 5 GHz Band

Frequencies 5150–5825 MHz (varies by region). Many non-overlapping channels: 36–48 (UNII-1), 52–144
(UNII-2/C), 149–165 (UNII-3). 160 MHz channels possible (36–48, 100–144, 149–165 are the standard
bondings).

**Characteristics:**

- Less congested than 2.4 GHz

- Shorter range, worse wall penetration

- Supports wider channels (80/160 MHz) for higher throughput

- Multiple UNII sub-bands with different transmission power limits

### 6 GHz Band (WiFi 6E / WiFi 7)

Frequencies 5925–7125 MHz. Vast number of channels (80-MHz channels: 1, 5, 9, 13, 17, 21, ..., 201;
160-MHz channels possible). **Requires WiFi 6E or WiFi 7 hardware.**

**Characteristics:**

- Minimal interference (newly opened spectrum)

- Excellent for high-density deployments

- Short range (similar to 5 GHz)

- Not backward compatible with older standards

---

## Signal Strength and Quality

### RSSI (Received Signal Strength Indicator)

Measured in dBm (decibels relative to 1 milliwatt). **Higher values (closer to 0) indicate stronger
signals.**

| RSSI | Quality | Typical Use |
| --- | --- | --- |
| -30 to -50 dBm | Excellent | Very close to AP; not typical in production |
| -50 to -67 dBm | Good | Primary coverage area; reliable data rates |
| -67 to -75 dBm | Fair | Acceptable coverage; reduced throughput |
| -75 to -85 dBm | Poor | Marginal coverage; significant packet loss |
| < -85 dBm | Very poor | Unreliable; disconnection likely |

### SNR (Signal-to-Noise Ratio)

The ratio of signal power to background noise. Measured in dB.

| SNR | Quality | Typical Rate |
| --- | --- | --- |
| > 40 dB | Excellent | Max rate (1+ Gbps) |
| 25–40 dB | Good | High throughput (500+ Mbps) |
| 15–25 dB | Fair | Moderate throughput (100–300 Mbps) |
| 5–15 dB | Poor | Very low throughput; disconnection risk |
| < 5 dB | Unusable | Connection unstable |

A high SNR is more important than raw RSSI. An AP at -70 dBm with SNR 30 dB will perform better than
one at -60 dBm with SNR 10 dB.

---

## Path Loss and Coverage

### Free Space Path Loss

Signal strength decreases with distance. In free space (no obstacles), the signal strength drops by
~6 dB for every doubling of distance (inverse square law).

**Example:** If an AP at 1 meter away measures -40 dBm, at 2 meters it measures ~-46 dBm,
at 4 meters ~-52 dBm.

In real buildings, path loss is worse due to walls, furniture, and multipath. Rule of thumb:

**expect 35–45 dB path loss over 30 meters indoors.**

### Coverage Prediction

Site survey tools (WiFi analyzers) measure real-world RSSI at various locations. Don't rely on
theoretical coverage maps — buildings vary widely. Always conduct a physical survey before
deployment.

---

## Interference and Channel Planning

### Co-Channel Interference

Two APs on the same channel (e.g., both on channel 1) cause co-channel interference. Signals
collide, SNR drops, throughput degrades. On 2.4 GHz, only use channels 1, 6, 11 to avoid overlap.

### Adjacent Channel Interference

Channels 1 and 2 partially overlap. Using 1 and 2 in adjacent areas degrades both. Stick to 1, 6, 11
separation (25 MHz apart).

### Dynamic Frequency Selection (DFS)

On 5 GHz, some channels require DFS to avoid radar interference (UNII-2 and UNII-2C: channels
52–144). If radar is detected, the AP must vacate the channel within 30 seconds. Automatic channel
selection often switches away from DFS channels during operation, causing roaming.

---

## Fading and Multipath

### Multipath Fading

Radio waves bounce off walls, furniture, and metal objects, arriving at the receiver via multiple
paths with different phase relationships. Constructive interference (paths add) strengthens the
signal; destructive interference (paths cancel) causes dropouts.

**Mitigation:** Spatial diversity (multiple antennas). Modern APs use MIMO (Multiple-Input
Multiple-Output) to transmit/receive on multiple antennas simultaneously, increasing
resilience to fading.

---

## Notes / Gotchas

- **RSSI Alone Doesn't Tell the Story:** High RSSI (-50 dBm) with low SNR (5 dB) is worse
  than moderate RSSI (-70 dBm) with high SNR (25 dB). Always check SNR in site surveys.

- **2.4 GHz is Crowded:** Neighbors' WiFi networks, Bluetooth devices, and microwave ovens
  all use 2.4 GHz. If only 1–2 non-overlapping channels are available, that network will
  experience interference. Disable 2.4 GHz or move performance-critical clients to 5/6 GHz.

- **Channel Width vs Interference:** 40 MHz channels on 2.4 GHz consume 2 of the 3
  non-overlapping channels, leaving minimal options. Use 20 MHz on 2.4 GHz or avoid 2.4 GHz
  altogether in dense environments.

- **DFS Channel Vacate Causes Roaming:** APs on UNII-2 channels (52–144) must move
  off-channel if radar is detected, triggering client roaming. Use non-DFS channels (1, 6,
  11, 36–48, 149–165) for stable operation unless you need UNII-2 capacity.

- **Wall Attenuation is Highly Variable:** Concrete, metal studs, and plumbing attenuate
  signals far more than drywall. Site surveys are essential; theoretical coverage maps are
  unreliable in real buildings.

---

## See Also

- [WiFi Standards Comparison](wifi_standards_comparison.md)

- [WiFi Network Design](wifi_network_design.md)

- [WiFi Security](wifi_security.md)

- [QoS](qos.md)
