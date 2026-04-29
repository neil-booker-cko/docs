# WiFi Roaming (802.11r/k/v)

Fast roaming protocols (802.11r Fast Roaming, 802.11k Radio Resource Management, 802.11v
Wireless Network Management) reduce latency and packet loss when clients move between access
points. Without these extensions, handovers cause multi-second delays or dropped connections,
degrading VoIP, video, and real-time applications. Enterprise networks deploy these in
combination to enable seamless roaming across large deployments.

---

## At a Glance

| Protocol | Purpose | Latency Reduction | Client Support | Typical Use |
| --- | --- | --- | --- | --- |
| **802.11r (FT)** | Fast Transition; pre-authentication + key caching | 50–200 ms | Most modern | Universal roaming |
| **802.11k (RRM)** | Radio Resource Mgmt; AP assists neighbor discovery | Not direct | Recent phones | Better AP selection |
| **802.11v (BTM)** | BSS Transition Mgmt; AP requests client move | Not direct | Recent phones | Load balancing |
| **Standard Roaming** | No extensions; re-authentication on every handover | 1–4 seconds | All devices | Legacy / budget |

---

## The Roaming Problem

### Legacy Roaming (No Extensions)

When a client moves from AP-A to AP-B:

1. Client associates to AP-B (beacon/probe exchange)
1. Client must **re-authenticate** with AP-B's RADIUS server (if 802.1X enabled)
1. Keys are renegotiated; PTK (Pairwise Transient Key) recomputed
1. DHCP lease may be renewed (if client moves to different subnet/VLAN)

**Total time: 1–4 seconds. Impact: VoIP drops, video stalls, TCP streams timeout.**

### Modern Roaming (With Extensions)

Extensions allow:

- **Pre-authentication:** Client caches keys with candidate APs before moving
- **Fast Key Derivation:** New keys computed from cached material in <100 ms
- **Network Assistance:** AP suggests better APs to improve handover target selection
- **Load Balancing:** AP can request client move to less-congested AP

**Total time: 50–200 ms. Impact: Seamless for user-perceptible (no drops).**

---

## 802.11r (Fast Roaming / FT)

### Purpose

Reduces re-authentication latency by pre-computing pairwise keys (PTKs) with candidate APs
before the client moves. On handover, the new AP already has the PTK; no RADIUS round-trip
needed.

### Key Concept: Pairwise Master Key (PMK) Caching

In standard WPA2/WPA3:

- PMK is derived from user credentials (password or certificate) and cached by RADIUS server and client
- PTK is derived from PMK and cached at current AP
- On roam to new AP, client must request new PTK from RADIUS (slow)

With 802.11r:

- PMK is cached on client for extended period
- Client can derive new PTK with new AP using cached PMK
- No RADIUS required; FT can complete in one frame exchange

### FT Methods

#### Over-the-Air (OTA)

Client pre-authenticates with candidate APs in the background:

```text
Client (AP-A): "I want to roam; send me pre-auth with AP-B"
AP-A: Forwards pre-auth request to AP-B via distribution system
AP-B: Computes and caches PTK for client
AP-B: Returns cached PTK to client (via AP-A)
Client: Now has PTK pre-computed for AP-B
```

On actual handover, client can immediately use the pre-cached PTK.

#### Over-DS (Distribution System)

Older method; AP-B communicates with RADIUS via the DS (wired network):

```text
Client → AP-A: "Planning to roam"
AP-A → DS → AP-B: Request FT key for client
AP-B ↔ RADIUS: Validate and compute PTK
AP-B → DS → AP-A: Return pre-computed PTK
Client → AP-B: Handover (PTK already cached)
```

**OTA is preferred** (faster, doesn't require DS involvement).

### Configuration

**Cisco IOS-XE:**

```ios
interface GigabitEthernet1
 wireless ap groupname corp-aps
!
ap groupname corp-aps
 802.11r ft-over-ds enable
 ft-reassoc-timeout 20
!
```

**FortiGate:**

```fortios
config wireless-controller vap
  edit "corp-ssid"
    set ft-over-ds enable
    set ft-reassoc-timeout 20
  next
end
```

**Cisco Meraki:**

Dashboard → Configure → Wireless → Networks → SSID Settings → Advanced → "Enable 802.11r Fast
Roaming". Meraki applies setting to all APs in network automatically; no per-AP configuration
needed.

### Deployment Considerations

- **AP Coordination:** APs must share PMK cache (often via controller or 802.11r distribution
  system)

- **PSK vs 802.1X:** FT works with both; 802.1X deployment requires RADIUS coordination
- **Device Support:** Most modern phones (iOS 11+, Android 10+, Windows 10+) support FT; older
  devices do not

---

## 802.11k (Radio Resource Management)

### Purpose

Provides clients with information about neighboring APs (signal strength, load, capability) to
make informed roaming decisions. Without RRM, clients roam reactively (wait for signal to drop
below threshold); with RRM, clients roam proactively (move to better AP before current AP
becomes poor).

### Key Mechanisms

#### Neighbor Report Request

Client or AP requests a list of neighboring APs with their capabilities:

```text
Client → AP: "Send me neighbor reports (SSIDs and capabilities)"
AP → Client: "AP-B (ch 36, RSSI -65), AP-C (ch 40, RSSI -72), ..."
Client: Uses this list to choose best roaming target
```

#### BSS Transition Management Query

Client queries the current AP: "Where should I roam?"

```text
Client → AP: "I'm considering roaming; which AP do you recommend?"
AP → Client: "Try AP-B on channel 36; it has lower load"
```

#### Beacon Request

Client can request neighbor APs send beacons with specific parameters (useful in dense
deployments).

### Deployment Impact

**Without 802.11k:**

- Client roams based purely on signal strength threshold
- May stay on degraded AP if signal is still above threshold
- Roams to AP with strongest signal (not necessarily best load/quality)

**With 802.11k:**

- AP assists; suggests better targets based on load, throughput, or AP capability
- Client makes smarter roaming decisions
- Enables coordinated load balancing across APs

### Configuration

**Cisco IOS-XE:**

```ios
interface GigabitEthernet1
 wireless ap groupname corp-aps
!
ap groupname corp-aps
 802.11k dot11k enable
 dot11k neighbor-list enable
!
```

**FortiGate:**

```fortios
config wireless-controller vap
  edit "corp-ssid"
    set neighbor-report-enable
  next
end
```

---

## 802.11v (Wireless Network Management / BTM)

### Purpose

Allows APs to actively manage client roaming by sending BSS Transition Management (BTM)
requests asking clients to move to a different AP. Used for:

- Load balancing (move clients from congested AP)
- Maintenance (gracefully move clients off AP before reboot)
- Link quality optimization (move to better channel or AP)

### Request Format

```text
AP → Client: "Please roam to AP-B (channel 36, BSSID xx:xx:xx:xx:xx:xx)"
             "Reason: network is congested; recommended transition time = 100ms"
Client: Acknowledges and roams to AP-B
```

Client is not forced; it can decline the request. Well-behaved clients roam on request; legacy
clients may ignore it.

### Use Cases

#### Load Balancing

When an AP becomes congested:

```text
AP-A (congested): Sends BTM request to 5 clients
  "Move to AP-B (less congested)"
Clients: Roam to AP-B
Result: Load distributed; capacity improved
```

#### Maintenance Window

Before maintenance:

```text
AP-A: Sends BTM request to all clients
  "Roam to AP-B; will be offline for maintenance in 5 minutes"
Clients: Gracefully migrate to AP-B
Admin: Takes AP-A offline for maintenance
Result: No connection drops during maintenance
```

### Configuration

**Cisco IOS-XE:**

```ios
interface GigabitEthernet1
 wireless ap groupname corp-aps
!
ap groupname corp-aps
 802.11v bss-transition-management enable
 btm-load-balance-time 10  # BTM interval in seconds
!
```

**FortiGate:**

```fortios
config wireless-controller vap
  edit "corp-ssid"
    set bss-transition-management-support
  next
end
```

---

## Combined Deployment (FT + RRM + BTM)

### Typical Enterprise Setup

For seamless roaming across 20+ APs in a large campus:

1. **Enable 802.11r (FT):** Reduces handover latency to <100 ms
1. **Enable 802.11k (RRM):** Clients make smarter roaming decisions based on AP load
1. **Enable 802.11v (BTM):** APs can actively request clients to move for load balancing

### Configuration Workflow

#### Step 1: Centralized Configuration (Controller or Firmware)

```text
All APs inherit settings from wireless controller or controller group
  802.11r: enable FT-over-Air, PMK caching
  802.11k: enable RRM, neighbor list
  802.11v: enable BTM, set load balance threshold
```

#### Step 2: Client Provisioning

```text
iOS/Android/Windows:

  - Supplicant must support FT, RRM, BTM (most modern devices do)
  - No user configuration needed (automatic negotiation)
```

#### Step 3: Monitoring

```text
Monitor roaming events:

  - Successful pre-auth with candidate APs
  - Handover latency (should be <200 ms)
  - Roaming direction (client following AP recommendations or not)
```

---

## Roaming Latency Breakdown

### Without Extensions (Standard)

| Phase | Time | Notes |
| --- | --- | --- |
| Scan for APs | 100–500 ms | Passive or active |
| Associate | 50–100 ms | Authentication frame exchange |
| 802.1X re-auth (RADIUS) | 500–2000 ms | RADIUS round-trip time |
| PTK derivation | 50–100 ms | Key computation |
| **Total** | **1000–3000 ms** | User perceives drop |

### With FT (802.11r)

| Phase | Time | Notes |
| --- | --- | --- |
| Pre-authentication (background) | 100–300 ms | Happens before actual move |
| Associate to new AP | 50–100 ms | Authentication frame exchange |
| PTK derivation (pre-cached) | <50 ms | Using cached material |
| **Total** | **50–200 ms** | Imperceptible to user |

---

## Roaming Best Practices

| Practice | Reason |
| --- | --- |
| **Enable 802.11r on all enterprise APs** | Sub-200 ms handover essential for VoIP/video |
| **Match 802.11r settings across APs** | FT requires consistent key derivation |
| **Use FT-over-Air (OTA) method** | Faster than over-DS (distribution system) |
| **Enable 802.11k for AP-assisted decisions** | Improves roaming target selection |
| **Enable 802.11v for load balancing** | Automatic redistribution of clients |
| **Monitor roaming events in logs** | Identify clients with poor roaming behavior |
| **Test with real devices before rollout** | Different OS versions have varying FT support |
| **Combine with 802.1X for security** | FT + 802.1X provides fast + secure roaming |
| **Avoid mixing FT-capable and non-FT APs** | Disables FT for clients in mixed environment |

---

## Notes / Gotchas

- **FT Across Controllers:** If APs are managed by multiple controllers (distributed deployment),
  PMK caching must be synchronized; some controllers support PMK-R0 caching across domains.
- **Legacy Devices Fallback:** If a device does not support FT, roaming falls back to standard
  (slow) authentication. Presence of even one non-FT device does not degrade FT-capable devices.
- **RRM Requires Capable APs:** 802.11k neighbor reports depend on APs being capable and
  configured to send them; legacy APs will not respond to RRM requests.
- **BTM Client Compliance:** Well-behaved clients (modern iOS, Android, Windows) accept BTM
  requests; older devices may ignore them. Cannot force roaming on non-compliant clients.
- **Channel Switching During Roam:** If client roams to AP on different channel, firmware update
  of both APs may be required for consistent FT behavior.

---

## See Also

- [WiFi Standards Comparison](wifi_standards_comparison.md)
- [WiFi RF Fundamentals](wifi_rf_fundamentals.md)
- [WiFi Security](wifi_security.md)
- [802.1X and EAP Authentication](wifi_authentication_8021x.md)
- [WiFi Network Design](wifi_network_design.md)
