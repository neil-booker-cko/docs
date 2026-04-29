# WiFi Standards Comparison

802.11 standards define radio transmission rates, frequency bands, and physical layer technologies
for wireless networks. Each generation improves throughput, latency, and power efficiency.
Understanding standards is essential for choosing equipment, capacity planning, and ensuring
compatibility with clients.

---

## At a Glance

| Standard | Year | Band(s) | Max Rate | Typical Range | Use Case | Status |
| --- | --- | --- | --- | --- | --- | --- |
| 802.11a | 1999 | 5 GHz | 54 Mbps | ~30m | Legacy enterprise | Obsolete |
| 802.11b | 1999 | 2.4 GHz | 11 Mbps | ~40m | Legacy consumer | Obsolete |
| 802.11g | 2003 | 2.4 GHz | 54 Mbps | ~40m | Legacy consumer/SMB | Obsolete |
| 802.11n (WiFi 4) | 2009 | 2.4/5 GHz | 600 Mbps | ~50m | Consumer/SMB | Declining |
| 802.11ac (WiFi 5) | 2013 | 5 GHz | 3.5 Gbps | ~40m | Enterprise/consumer | Current standard |
| 802.11ax (WiFi 6) | 2021 | 2.4/5/6 GHz | 9.6 Gbps | ~40m | High-density enterprise | Recommended |
| 802.11be (WiFi 7) | 2024 | 2.4/5/6 GHz | 46 Gbps | ~40m | Next-gen enterprise | Emerging |

---

## 802.11 Evolution

### Legacy Standards (a/b/g)

802.11b (2.4 GHz, 11 Mbps) and 802.11a/g (54 Mbps) dominated the 2000s. Both are end-of-life but may
still be found in legacy deployments. Clients from these eras have weak security (WEP) and poor
performance. Decomission in new deployments.

### 802.11n (WiFi 4) — 2009

First to introduce MIMO (Multiple-Input Multiple-Output) and wider channels (40 MHz), achieving 600
Mbps theoretical max. Dual-band (2.4 GHz and 5 GHz). Still widely deployed but aging; many
enterprise networks are migrating away.

### 802.11ac (WiFi 5) — 2013

5 GHz only, 80/160 MHz channels, MU-MIMO (multi-user MIMO), up to 3.5 Gbps. Industry standard for
the last decade. Excellent backward compatibility with 802.11n. Sufficient for most enterprise use
cases but aging as density increases.

### 802.11ax (WiFi 6) — 2021

Dual-band (2.4/5 GHz), OFDMA (orthogonal frequency division multiple access), up to 9.6 Gbps. Better
performance in dense environments, lower latency, improved power efficiency. **Recommended for new
enterprise deployments.**

### 802.11be (WiFi 7) — 2024

Triple-band (2.4/5/6 GHz), 320 MHz channels, 46 Gbps theoretical max. Uses 6 GHz band (new
spectrum). Still emerging; client and AP maturity is developing. Future standard but not yet
necessary for most deployments.

---

## Frequency Bands

### 2.4 GHz

Unlicensed band, global availability, excellent range, but crowded (microwave ovens, Bluetooth,
cordless phones interfere). Only 3 non-overlapping channels (1, 6, 11 in most regions). Better wall
penetration than 5 GHz.

**Use:** Backward compatibility, guest networks, IoT devices.

### 5 GHz

Unlicensed band, many non-overlapping channels (36–165), lower interference, but shorter range and
worse wall penetration than 2.4 GHz. Less congested. Multiple sub-bands (UNII-1/2/3/4).

**Use:** Primary band for high-performance networks, enterprise SSIDs.

### 6 GHz (WiFi 6E / WiFi 7)

Newly opened unlicensed spectrum (2023). Vast number of channels, minimal interference. Requires
WiFi 6E or WiFi 7 equipment and WPA3 (regulatory requirement). Not backwards compatible with
older APs/clients.

**Use:** High-density environments, future-proofing, enterprise campuses.

---

## Backward Compatibility and Channel Widths

### HT (High Throughput) and VHT (Very High Throughput)

802.11n uses HT (20/40 MHz channels). 802.11ac uses VHT (20/40/80/160 MHz). Wider channels = higher
throughput but more susceptible to interference. On 2.4 GHz, 40 MHz channels reduce the effective
number of non-overlapping channels to 1–2.

### Legacy Rates

All modern standards negotiate **legacy rates** (6, 9, 12, 18, 24 Mbps) for compatibility with older
clients. If a legacy client connects, the AP may reduce throughput for the entire BSS (Basic Service
Set). Use band steering or separate SSIDs to minimize impact.

---

## Choosing a Standard

**For new deployments:** 802.11ax (WiFi 6) is the current standard. Mature hardware,
excellent performance, lower cost than WiFi 7.

**For high-density environments (universities, stadiums, offices):** WiFi 6 or WiFi 7.
OFDMA and MU-MIMO handle many simultaneous clients better than WiFi 5.

**For budget-conscious deployments:** 802.11ac is still acceptable but avoid 802.11n for new APs.

**For IoT and guest networks:** Dual-band 802.11ax APs with separate SSIDs (one 2.4 GHz
for legacy IoT, one 5 GHz for performance).

---

## Notes / Gotchas

- **Legacy Rate Negotiation:** A single 802.11b client connecting to an 802.11ac AP forces
  the AP to advertise legacy rates, potentially reducing peak throughput for all clients on
  that AP. Isolate legacy clients on separate APs or SSIDs.

- **Channel Width and Interference:** 40 MHz channels on 2.4 GHz leave only one usable
  non-overlapping channel (6). Avoid 40 MHz on 2.4 GHz in dense deployments; use 20 MHz
  or disable 2.4 GHz entirely if all clients support 5/6 GHz.

- **6 GHz Requires WiFi 6E/7 and WPA3:** The new 6 GHz band (WiFi 6E, WiFi 7) requires both
  6E-certified hardware AND WPA3 (regulatory requirement). Older APs and clients cannot use it,
  even if they support 802.11ax.

- **Throughput vs Real-World Rates:** Rated speeds (e.g., 3.5 Gbps for WiFi 5) are
  theoretical maximum under ideal conditions. Real-world throughput is typically 40–60%
  of rated speed due to overhead, interference, and client limitations.

- **Standards are NOT Backward Compatible Across Major Generations:** 802.11ac APs can
  accept 802.11n clients, but 802.11n APs cannot handle 802.11ac clients. Upgrading from
  802.11n to 802.11ac requires new hardware; it's not a firmware update.

---

## See Also

- [RF Fundamentals](wifi_rf_fundamentals.md)

- [WiFi Security](wifi_security.md)

- [WiFi Network Design](wifi_network_design.md)

- [QoS](qos.md)
