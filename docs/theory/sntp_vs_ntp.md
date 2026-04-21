# SNTP vs NTP — Time Synchronisation Protocols

SNTP (Simple Network Time Protocol) and NTP (Network Time Protocol) both synchronise system
clocks across a network. NTP (RFC 5905) is a complex, full-featured protocol designed for
highly accurate timekeeping with sub-millisecond precision. SNTP (RFC 5905 simplified subset)
is a lightweight variant for devices that do not require such precision. Both use the same
packet format and UDP port but differ in implementation complexity, accuracy, overhead, and
use cases. Understanding the trade-offs is essential for network infrastructure design,
especially in environments requiring timing precision (financial systems, telecom, power
grids) or serving resource-constrained devices (IoT, embedded systems).

For detailed packet format information, see [NTP Packet Format](../packets/ntp.md).

---

## At a Glance

| Property | NTP (Full) | SNTP (Simplified) |
| --- | --- | --- |
| **RFC** | RFC 5905, RFC 5906 | RFC 5905 (simplified client mode) |
| **Complexity** | High (full state machine) | Low (client-only, stateless) |
| **Synchronisation accuracy** | < 1 millisecond (sub-µs under ideal conditions) | ±100 milliseconds typical |
| **Stratification** | 16-level hierarchy (stratum 0–15) | Simplified stratum support |
| **Modes** | 9 modes (server, client, peer, broadcast, etc.) | Client mode only (simplified) |
| **Clock filtering** | Yes (multiple samples, outlier removal) | Optional or none |
| **Frequency discipline** | Yes (PLL/FLL control loop) | Usually not |
| **Polling** | Adaptive polling (range 64–1024 seconds) | Fixed polling interval |
| **UDP Port** | `123` | `123` (same) |
| **Packet size** | 48 bytes (fixed) | 48 bytes (same) |
| **CPU overhead** | Moderate (computation, state machine) | Minimal (simple query/response) |
| **Memory footprint** | Large (state, filter arrays) | Small (minimal state) |
| **Bandwidth usage** | Efficient (adaptive polls) | Efficient (fixed polls) |
| **Root delay handling** | Explicit calculation | May ignore or simplify |
| **Use case** | Precision timing for networks, distributed systems | Simple timekeeping for clients, IoT devices |
| **Vendor support** | All network devices, servers, desktops | Simpler devices, constrained IoT |

---

## How Each Protocol Works

### NTP: Hierarchical Time Distribution

NTP is designed as a **hierarchical system** where time flows from authoritative sources
(atomic clocks, GPS receivers) down through multiple server layers to clients. Every NTP
participant maintains state about peers and adapts its behaviour based on network
conditions.

**NTP stratum levels:**

- **Stratum 0:** Atomic clock, GPS receiver, radio clock (physical time source; not networked)
- **Stratum 1:** Network-connected NTP server directly connected to Stratum 0 source
- **Stratum 2:** NTP server that synchronises to Stratum 1 server(s)
- **Stratum 3 and beyond:** Servers synchronising to Stratum 2 or lower
- **Stratum 16:** Unsynchronised (time source unknown or unavailable)

```mermaid
graph TD
    A["Atomic Clock (Stratum 0)"]
    B1["GPS/NTP Server (Stratum 1)<br/>Directly connected to atom"]
    B2["NTP Server (Stratum 1)<br/>Via CDMA signal"]
    C1["NTP Server (Stratum 2)<br/>Synced to B1"]
    C2["NTP Server (Stratum 2)<br/>Synced to B2"]
    D1["NTP Client (Stratum 3)<br/>Synced to C1"]
    D2["NTP Client (Stratum 3)<br/>Synced to C2"]
    E["Workstation (Stratum 4)<br/>Synced to D1/D2"]

    A --> B1
    A --> B2
    B1 --> C1
    B1 --> C2
    B2 --> C1
    B2 --> C2
    C1 --> D1
    C2 --> D2
    D1 --> E
    D2 --> E
```text

**NTP synchronisation process:**

1. **Clock filter:** An NTP client sends queries to multiple servers and collects samples.
   It filters outliers and selects the best samples.

2. **Clustering:** The client identifies which servers are reliable and groups them into
   clusters.

3. **Selection:** From clusters, the client selects the best server (lowest stratum, best
   roundtrip time).

4. **Clock discipline:** The client adjusts its system clock using two control loops:
   - **Phase Lock Loop (PLL):** For steady-state frequency adjustment
   - **Frequency Lock Loop (FLL):** For rapid frequency adjustment when far off

5. **Mitigation:** NTP implements protections against:
   - Falsetickers (servers with incorrect time)
   - Byzantine attacks (malicious time advertisements)
   - Network jitter and asymmetric delays

### SNTP: Stateless Client-Only Mode

SNTP is a **simplified client-only implementation** of NTP. An SNTP client sends a single
query to an NTP server and uses the response to set (or adjust) the system clock. No state
is maintained; no multiple samples are taken; no filtering or clustering occurs.

**SNTP synchronisation process:**

```text
SNTP Client              NTP Server (Stratum 1/2/3)
    |                           |
    | NTP Request              |
    | (T1: client send time)   |
    |------------------------->|
    |                           | T2: server receive time
    |                           | T3: server send time
    |                           |
    | NTP Response              |
    | (T1, T2, T3, T4)         |
    |<-------------------------|
    |                           |
    | (calculate offset)        |
    | offset = (T2 - T1 + T3 - T4) / 2
    |
    | (set system clock)
    | (optionally adjust using calculated offset)
```text

**Key differences from NTP:**

1. **No state machine:** SNTP does not maintain peer state or synchronisation state. It
   sends a query and uses the response.

2. **Single sample:** One query, one response. No filtering or outlier removal.

3. **No clock discipline:** SNTP simply sets the time; it does not use feedback loops to
   gradually adjust frequency.

4. **No server selection:** SNTP uses a single configured server (or round-robins a list).
   No clustering or fallback logic.

---

## Accuracy and Precision

### NTP Accuracy (Sub-millisecond to Nanoseconds)

NTP achieves high accuracy through multiple mechanisms:

1. **Multiple servers:** A client queries multiple servers and selects the best one,
   reducing the impact of a single bad server.

2. **Clock filtering:** Samples are collected and filtered over time. Outliers are
   discarded. The filtered samples improve accuracy.

3. **Frequency discipline:** By adjusting the clock frequency (not just the time), NTP
   maintains accuracy between polls.

4. **Roundtrip delay compensation:** NTP calculates network delay and compensates for it
   in the time adjustment.

5. **Stratum awareness:** An NTP client prefers servers with lower stratum (closer to the
   atomic clock source). Time error accumulates with each hop; lower stratum means
   less accumulated error.

**Typical NTP accuracy:**

| Condition | Accuracy |
| --- | --- |
| LAN, single Stratum 1 server | < 1 millisecond (sub-µs possible) |
| LAN, multiple Stratum 2 servers | 1–10 milliseconds |
| WAN (Internet), multiple Stratum 2/3 servers | 10–100 milliseconds |
| WAN with high jitter | 100–500 milliseconds |

### SNTP Accuracy (Milliseconds to Tens of Milliseconds)

SNTP achieves lower accuracy because it uses a single sample and does not filter or
discipline the clock.

**Typical SNTP accuracy:**

| Condition | Accuracy |
| --- | --- |
| LAN, low-jitter link | ±10–50 milliseconds |
| LAN, variable jitter | ±50–100 milliseconds |
| WAN (Internet) | ±100–500 milliseconds |
| High-latency networks | ±500ms–1 second |

**Offset calculation (one-way view):**
```text
offset = (T2 - T1 + T3 - T4) / 2

If roundtrip delay is 100ms (symmetric):
  T1 = 10:00:00.000
  T2 = 10:00:00.050 (server received after 50ms)
  T3 = 10:00:00.150 (server sent, 100ms later)
  T4 = 10:00:00.200 (client received after 50ms)

  offset = (50 + 150 - 200) / 2 = 0ms (correct!)

But if jitter exists:
  T1 = 10:00:00.000
  T2 = 10:00:00.070 (link was slow)
  T3 = 10:00:00.170
  T4 = 10:00:00.280 (return link was slow)

  offset = (70 + 170 - 280) / 2 = -20ms (error!)
```text

A single sample can be significantly skewed by network jitter. NTP mitigates this via
filtering; SNTP cannot.

---

## Stratum and Clock Hierarchy

### Understanding Stratum

**Stratum** is NTP's concept of proximity to the reference clock (Stratum 0):

| Stratum | Source | Accuracy | Use Case |
| --- | --- | --- | --- |
| 0 | Atomic clock, GPS, CDMA | Nanoseconds | Physical time source |
| 1 | NTP server directly connected to Stratum 0 | < 1µs | ISP core, data centre |
| 2 | NTP server synced to Stratum 1 | < 10µs | Enterprise core, ISP regional |
| 3 | NTP server synced to Stratum 2 | < 100µs | Branch office, campus |
| 4–15 | Chains of servers | Milliseconds | Devices, endpoints |
| 16 | Unsynchronised | N/A | Clock not set or source lost |

NTP clients prefer lower-stratum servers because error accumulates with each hop. An NTP
client will synchronise to a Stratum 3 server if a Stratum 2 is unavailable, but will
always prefer the Stratum 2 if both are reachable.

### SNTP Stratum Handling

SNTP clients may be **stratum-aware** but typically do not. A simple SNTP client:

```text
1. Send query to configured server
2. Receive response
3. If server reports Stratum 16 (unsynchronised), optionally reject response
4. Otherwise, set clock to received time
```text

SNTP does not select among multiple servers based on stratum; it uses a single server or
round-robins a static list.

---

## Use Cases and Deployment Scenarios

### When to Use NTP

**Full NTP is necessary when:**

1. **High-accuracy timekeeping is required:**
   - Financial systems (trading, settlement, audit trails)
   - Telecom networks (CDMA timers, call accounting)
   - Power grids (synchrophasors, fault timestamps)
   - Scientific experiments (nanosecond-level precision)

   **Accuracy needed:** < 1 millisecond

2. **Distributed systems requiring consensus:**
   - Kubernetes, Consul, ETCD (cluster members must have synchronized clocks)
   - Database replication and consistency (timestamps for ordering)
   - Blockchain (consensus depends on time ordering)

   **Accuracy needed:** < 1–10 milliseconds

3. **Network infrastructure where clock discipline improves reliability:**
   - Large data centres with thousands of devices
   - Service provider backbone
   - Carrier-grade networks

4. **Multi-hop time distribution:**
   - NTP is designed for scalable, hierarchical distribution
   - A single NTP stratum 1 server can support hundreds of clients across multiple
     strata

**Typical NTP deployment:**

```text
ISP Stratum 1 NTP Server (GPS-synchronized)
        |
    ----+----
   /    |    \
  /     |     \
Core-1 Core-2 Core-3 (Stratum 2)
  |      |      |
  +------+------+
        |
    ----+-----
   /    |     \
  /     |      \
Edge-1 Edge-2 Edge-3 (Stratum 3)
  |      |      |
Routers/Switches/Servers (Stratum 4)
```text

### When to Use SNTP

**SNTP is sufficient when:**

1. **Simple time keeping for clients:**
   - PCs, workstations, printers (setting time to ±100ms is fine)
   - IoT devices, sensors (logging timestamps, daily tasks)
   - Consumer devices (consumer routers, NAS boxes)

   **Accuracy needed:** ±100 milliseconds to ±1 second

2. **Resource-constrained devices:**
   - Embedded systems, microcontrollers with limited RAM
   - Devices with limited CPU (cannot run full NTP state machine)
   - Low-bandwidth links (satellite, cellular with high latency)

3. **Periodic time sync (not real-time):**
   - A device syncs once at boot-up or once per day
   - Does not require continuous discipline

4. **Simple architecture:**
   - Client devices query a single, trusted NTP server (often in-house)
   - No need for fallback, clustering, or Byzantine protection

**Typical SNTP deployment:**

```text
In-house NTP Server (Stratum 2, synced to internet)
        |
    ----+----+----
   /    |    |    \
IoT   PC  Printer Smart-Home
Sensor    (client) (SNTP client)
```text

---

## Practical Differences That Matter

### CPU and Memory Overhead

| Implementation | CPU | Memory | Duration |
| --- | --- | --- | --- |
| **NTP full** | 5–10% (during sync) | 100–500 KB | Continuous |
| **SNTP simple** | < 1% (per query) | < 50 KB | Brief (send/recv) |

A modern router can easily run full NTP. An embedded device (< 1 MB RAM) should use SNTP.

### Convergence Time

**NTP:** Takes 10–20 minutes to fully converge and discipline the clock. Initial time
setting can be quick, but frequency adjustment requires multiple samples.

**SNTP:** Sets time immediately on the first response. However, without frequency
discipline, the clock will drift over time.

### Clock Drift

**NTP-synchronized systems:** Drift is negligible (< 1 second per year) because the
frequency is continuously adjusted.

**SNTP-synchronized systems:** Drift depends on hardware oscillator quality:
- Good quartz crystal: ~50 ppm (5 seconds per day)
- Poor crystal: ~500 ppm (50 seconds per day)
- Without periodic SNTP syncs, clock can drift significantly

### Network Resilience

**NTP:** Queries multiple servers, falls back gracefully. If one server fails, NTP
continues syncing with others. Peers can sync with each other (peer mode).

**SNTP:** Queries a single server (or rounds-robins a static list). If the server is
unavailable, no time sync occurs. No peer support.

---

## Cisco Configuration Examples

### NTP Server (Stratum 1)

```ios
! Configure NTP server with external time source
ntp clock-period 3705600  ! Update interval
ntp update-calendar  ! Update NVRAM calendar

! Peer with another NTP server (redundancy)
ntp peer 10.0.1.100

! Act as authoritative server (Stratum 1)
ntp master 1

! Allow clients to sync
ntp access-group query-only
ntp access-group serve 10  ! Allow from ACL 10

! Verify
show ntp status
show ntp associations
```text

### NTP Client (Full NTP)

```ios
! Configure as NTP client syncing to multiple servers
ntp server 10.0.1.1 prefer  ! Primary (lowest latency/stratum)
ntp server 10.0.1.2  ! Secondary
ntp server 10.0.1.3  ! Tertiary

! Configure NTP options
ntp authenticate  ! Enable authentication
ntp trusted-key 1  ! Accept key 1
ntp authentication-key 1 md5 MyNTPKeySecret

! Enable NTP updates
ntp update-calendar  ! Update NVRAM

! Verify
show ntp status
show ntp associations detail
```text

### SNTP Client (Simplified)

```ios
! Use sntp (simple mode) instead of ntp
sntp server 10.0.1.100 prefer
sntp server 10.0.1.101

! Set update interval (default 30 minutes)
sntp poll-interval 1800

! Verify
show sntp status
```text

### NTP with Authentication

```ios
! Configure NTP with MD5 authentication
ntp authenticate
ntp authentication-key 1 md5 MySecureNTPKey
ntp trusted-key 1

! Require authentication from peers
ntp peer 10.0.1.200 key 1

! Verify
show ntp associations
debug ntp authentication
```text

---

## FortiGate Configuration Examples

### NTP Server Configuration

```text
config system ntp
 set ntpserver
  edit 1
   set server "time.nist.gov"
   set port 123
  next
  edit 2
   set server "10.0.1.1"  ! Internal server
   set port 123
  next
 end
 set type fortisiem  ! Force time sync via ntp
 set ntpsync enable
 set server-mode disable
end

! Verify
get system ntp status
```text

### NTP Client with Multiple Servers

```text
config system ntp
 set ntpserver
  edit 1
   set server "ntp1.example.com"
  next
  edit 2
   set server "ntp2.example.com"
  next
 end
 set ntpsync enable
end
```text

---

## Timing Requirements by Application

### High Precision (< 1ms)

**Applications:**
- Stock trading, derivatives, high-frequency trading
- Telephony (CDMA, LTE timing)
- Power grid monitoring (synchrophasors)
- Distributed database consistency (Spanner, CockroachDB)

**Protocol:** NTP with Stratum 1/2 servers, BFD for convergence

**Example config:** Multiple Stratum 1 servers, multiple Stratum 2 backup servers, active
polling

### Medium Precision (1–100ms)

**Applications:**
- Kubernetes cluster synchronisation
- Cloud infrastructure logging and auditing
- Video surveillance (timestamp correlation)
- Enterprise backup and archival

**Protocol:** NTP with Stratum 2/3 servers, or SNTP from reliable source

**Example config:** 2–3 NTP servers, discipline clock, allow 100ms error

### Low Precision (> 100ms)

**Applications:**
- Workstations, printers (log timestamps)
- IoT devices (daily sync OK)
- Network monitoring and syslog (order of operations OK within seconds)
- Consumer devices

**Protocol:** SNTP from any available server

**Example config:** Single SNTP server, sync once per day or on boot

---

## When to Use Each

### Use Full NTP When

- **Sub-second timing accuracy required** (financial, telecom, power, distributed systems)
- **Multiple time sources available** and fallback is needed
- **Large network** where hierarchical time distribution is important
- **Device has adequate resources** (CPU, memory)
- **Clock discipline** (frequency correction) is beneficial

### Use SNTP When

- **Simple time setting** (accuracy ±100ms is fine)
- **Device is resource-constrained** (IoT, embedded, legacy hardware)
- **Single, trusted time source** available
- **Periodic sync** (once per day, not continuous)
- **No complex fallback logic** needed

---

## Notes

- **BFD and NTP integration:** BFD (Bidirectional Forwarding Detection) can detect failures
  in NTP servers within < 1 second, improving overall system resilience.

- **Stratum 1 servers are rare:** True Stratum 1 servers (directly connected to atomic
  clocks or GPS) are expensive and typically run only at ISP data centres and large
  enterprises. Most organisations use publicly available Stratum 1/2 servers (NIST, NTP
  Pool) as their reference.

- **GPS vs CDMA:** GPS receivers provide accurate time (±100ns) but require outdoor
  antennas and clear sky view. CDMA cell towers provide time but are carrier-dependent.

- **Leap seconds:** NTP handles leap seconds (adjustments when UTC adds a second). SNTP may
  or may not handle them; care is needed.

- **Authentication:** NTP supports MD5 and symmetric-key authentication. Modern deployments
  may use HTTPS or other methods for server queries.

- **RFC references:** NTP is RFC 5905 (v4) and RFC 5906 (authentication). SNTP is a
  simplified client mode defined in RFC 5905.
