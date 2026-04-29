# WiFi Troubleshooting

Common WiFi connectivity, authentication, roaming, and performance issues with diagnostic
procedures and remediation steps. Applies to enterprise deployments using 802.1X, WPA2/WPA3,
and dual-band (2.4/5 GHz) or tri-band (2.4/5/6 GHz) APs.

---

## Quick Diagnosis

| Symptom | Likely Cause | First Check |
| --- | --- | --- |
| **Cannot associate to SSID** | AP not broadcasting; wrong password; wrong security mode | Verify SSID visible in scan; check AP power; confirm security settings |
| **Associates but no IP address** | DHCP failure; AP-to-DHCP path broken; client misconfigured | Check DHCP server reachable from AP VLAN; verify client DHCP enabled |
| **Associates, has IP, but no internet** | Firewall policy; routing; VLAN mismatch | Test ping to gateway; check firewall rules for VLAN; verify AP trunk config |
| **Slow throughput** | Interference; too many clients on AP; weak signal | Run WiFi analyzer; check AP client count; measure RSSI |
| **Frequent disconnections** | Weak signal; co-channel interference; AP instability | Check RSSI >–67 dBm; verify non-overlapping channels; reboot AP |
| **802.1X authentication fails** | RADIUS unreachable; credentials wrong; wrong EAP method | Verify RADIUS server IP and port reachable; check client password; confirm EAP method matches |
| **Roaming slow (>1s latency)** | 802.11r not enabled; RADIUS latency high; channel switch slow | Enable FT on APs; check RADIUS RTT; verify band steering not causing delay |
| **One device won't connect** | Old device; unsupported security; driver issue | Check device OS/WiFi chip support; try reset/forget SSID; update driver |

---

## Association Failures

### Symptom: "Cannot Connect to Network" (Repeated Attempts)

**Initial checks:**

1. Verify SSID is visible: run WiFi scan on client, see SSID broadcast by AP

1. Confirm security mode matches:

    - Client expecting WPA3-Personal but AP set to WPA2-Personal

    - Client has WPA3 capable but AP only supports WPA2

1. Check SSID broadcast enabled (some APs allow hidden SSID; disable for troubleshooting)

**AP-side diagnosis:**

```text
Check AP association logs:

  - Is client MAC visible in associated clients list?

  - If not: client never reached AP (weak signal, interference)

  - If yes but keeps dropping: authentication loop (see 802.1X section)
```

**Signal strength check:**

- If RSSI <–75 dBm: move closer to AP or reduce AP transmit power

- Measure SNR: if <15 dB, check for interference or microwave ovens

### Symptom: "Incorrect Password" (Despite Correct Entry)

**WPA3-Personal (SAE handshake):**

- SAE is timing-sensitive; if client and AP clocks skewed >30 seconds, handshake may fail silently

- **Fix:** Sync NTP on client and AP

**WPA2-Personal (PSK):**

- Verify AP SSID exactly matches client (case-sensitive)

- Check AP is not in "transition mode" (mixed WPA2/WPA3) — some old clients fail in transition

**Enterprise (802.1X):**

- See [802.1X Authentication Failures](#8021x-authentication-failures) below

---

## DHCP and IP Address Assignment

### Symptom: "Associated but No IP Address"

#### Step 1: Verify DHCP server is reachable

From AP or controller, ping DHCP server IP:

```bash
ping <dhcp-server-ip>
```

If unreachable: check routing, firewall rules, or DHCP server interface on correct VLAN.

#### Step 2: Check DHCP relay configuration

If AP is on different VLAN than DHCP server, verify IP helper address (Cisco) or DHCP relay
(FortiGate) is configured:

**Cisco IOS-XE:**

```ios
interface Vlan100
 ip helper-address 192.168.1.1  ! DHCP server IP
!
```

**FortiGate:**

```fortios
config system dhcp-server
  edit <pool-id>
    set interface "VLAN100"
    set lease-time 86400
  next
end
```

#### Step 3: Check AP to DHCP path in firewall

Firewall policy must allow AP (or management interface) to reach DHCP server on UDP 67/68.

#### Step 4: Monitor DHCP on client

On Windows:

```bash
ipconfig /all          ! Check if DHCP-assigned or manual IP
ipconfig /release      ! Release current IP
ipconfig /renew        ! Request new IP from DHCP
```

On macOS/iOS:

Settings → WiFi → Network Details → DHCP or Manual IP

### Symptom: "DHCP Timeout" (Takes >30 seconds)

**Causes:**

- DHCP server slow or overloaded

- High latency between AP and DHCP server (>500 ms)

- Client DHCP timeout set too low

**Check DHCP server load:**

```bash
DHCP server: Check active leases and log
  If many "DECLINE" or "NACK" responses: DHCP pool exhausted or misconfigured
```

**Increase DHCP timeout on client (if configurable):**

Some devices allow DHCP timeout tuning; set to 30–60 seconds.

---

## 802.1X Authentication Failures

### Symptom: "Authenticating..." Hangs Then Fails

#### Check 1: RADIUS server reachable

From AP, verify RADIUS server (typically UDP 1812/1813) is reachable:

```bash
# Cisco
test aaa server radius <radius-server-ip>

# FortiGate (CLI)
diagnose debug radius
! Then attempt authentication on client and watch debug output
```

#### Check 2: RADIUS secret matches

AP and RADIUS server must have matching shared secret (pre-shared key). If mismatch, RADIUS
rejects AP requests silently (no error logs on AP; only RADIUS rejects in RADIUS logs).

**Remedy:** Verify RADIUS shared secret on AP and RADIUS server match exactly.

#### Check 3: Verify correct EAP method

Client PEAP settings must match RADIUS configuration:

```text
Client Config:          RADIUS Config:
  EAP: PEAP              Must support PEAP
  Inner: MSCHAP-v2       Must have MSCHAP-v2 enabled
  Validate cert: Yes     Server certificate must be installed
```

#### Check 4: Server certificate validation

If client is set to "Validate server certificate" but AP cert is self-signed or expired:

- Client hangs during TLS handshake

- **Remedy:** Install valid certificate or disable validation (less secure)

#### Check 5: Credentials wrong

RADIUS server checks username/password against backend (AD, LDAP, local DB).

Test credentials directly (if possible):

```bash
# Linux radtest utility
radtest username password <radius-server-ip> 0 <shared-secret>
```

If RADIUS responds "Access-Reject": credentials are wrong or user account disabled.

### Symptom: "EAP-PEAP Failed" (After Appearing to Succeed)

**Cause:** Client entered credentials in PEAP tunnel, RADIUS validated them, but session key
negotiation failed.

**Typical causes:**

- RADIUS server and client clocks too far apart (>30 seconds)

- MTU too small; fragmented EAP frames not reassembled

- PTK (Pairwise Transient Key) derivation error

**Remedies:**

1. Sync NTP on AP and RADIUS server (ensure time within 30 seconds)

1. Check MTU: AP and RADIUS server should be on networks with MTU ≥1500

1. Increase EAPOL retransmit timeout on AP (default 3 sec; try 10 sec)

---

## Roaming and Handover Issues

### Symptom: "Roaming Causes Disconnection" (>2 seconds)

#### Check 1: 802.11r (FT) enabled?

Without FT, clients must re-authenticate with RADIUS on every handover (1–3 seconds). Enable FT:

**Cisco IOS-XE:**

```ios
ap groupname <group>
 dot11-5ghz
  ft-over-air
 exit
!
```

**FortiGate:**

```fortios
config wireless-controller vap
  edit "corp-ssid"
    set ft-over-ds enable
  next
end
```

#### Check 2: RADIUS latency

If RADIUS server is distant, authentication may take >1 second, causing roaming lag.

**Measure RADIUS RTT:**

```bash
# From AP, measure ping to RADIUS server
ping <radius-ip>
# Should be <100 ms; if >500 ms, consider local RADIUS proxy
```

#### Check 3: RSSI at roaming boundary

If APs overlap poorly (coverage gap), client may disconnect during roam before new AP has strong
signal. Verify at least –67 dBm overlap between adjacent APs.

#### Check 4: Channel switch delay

If client roams to AP on different channel (e.g., 2.4 GHz to 5 GHz), channel switch adds 50–200
ms.

---

## Performance Issues

### Symptom: "WiFi Speeds Low" (<50% Rated)

#### Step 1: Check RSSI and SNR

Run WiFi analyzer at client location:

- **RSSI:** Should be >–67 dBm for good throughput

- **SNR:** Should be >25 dB; <15 dB is poor

If RSSI poor: move closer to AP or reduce AP transmit power (too high causes overlap, forcing
lower rates).

#### Step 2: Check client rate

Use WiFi analyzer to see negotiated rate:

```text
Expected: 802.11ac (80 MHz) = 300–600 Mbps per client
Actual: 54 Mbps or less
  → Client may be on legacy 802.11g rate (2.4 GHz fallback)
  → Check for legacy clients forcing legacy rates on AP
```

#### Step 3: Check AP client load

Count associated clients on AP:

**Cisco:**

```ios
show ap config general
! Look for "Number of Clients"
```

**FortiGate:**

```fortios
get wireless-controller ap status
! Look for "Client Count"
```

If >20 clients: AP throughput shared across all; per-client speeds drop.

**Remedy:** Add more APs or implement load balancing (802.11v).

#### Step 4: Check interference

Run WiFi analyzer, check for overlapping networks on same channel:

```text
Your SSID: Channel 6, RSSI –55 dBm
Neighbor: Channel 5, RSSI –60 dBm
Neighbor: Channel 7, RSSI –65 dBm
```

Overlapping channels cause SNR degradation. Move AP to different channel or reduce power.

### Symptom: "Throughput Drops at Specific Locations"

**Likely causes:**

- **Multipath fading:** Radio waves bouncing off walls/furniture, cancelling out

- **Interference:** Microwave oven, cordless phone, or neighboring WiFi

- **Metal obstacles:** Filing cabinets, reinforced walls, metal studs

**Diagnosis:**

1. Run WiFi analyzer at location: measure RSSI variation (should be stable, not fluctuating)

1. If RSSI very variable (–50 to –80 dBm swings), multipath fading likely

1. If stable RSSI but low SNR: interference (check for microwave, Bluetooth)

**Remedies:**

- Move AP to reduce multipath (avoid placing between parallel walls)

- Use AP with diversity antennas (MIMO)

- Move client away from interference source (microwave)

- Switch to 5 GHz (less affected by microwaves than 2.4 GHz)

---

## Channel and Frequency Issues

### Symptom: "AP Suddenly Stops Working" (5 GHz)

**Likely cause:** DFS (Dynamic Frequency Selection) radar detection on UNII-2 channels (52–144).

If radar detected, AP must vacate channel within 30 seconds:

1. Check AP logs for "radar detected" or "DFS event"

1. AP will move to alternate channel (automatic)

1. Clients may roam if using 802.11k/v

**Prevention:**

- Use non-DFS channels (1, 6, 11 on 2.4 GHz; 36–48, 149–165 on 5 GHz)

- If UNII-2 needed, enable 802.11k (RRM) for assisted roaming

### Symptom: "2.4 GHz Network Unusable"

**Cause:** Saturation from neighboring networks, microwave ovens, Bluetooth.

**Diagnosis:**

1. Run WiFi analyzer: count number of networks on each channel

1. If >5 networks on channels 1–11: congestion

**Remedies:**

1. Disable 2.4 GHz SSID (migrate all clients to 5 GHz)

1. If 2.4 GHz required: use 20 MHz channel width and channels 1, 6, 11 only (non-overlapping)

1. Reduce AP power to avoid overlap with neighbors

1. Move AP away from microwave and cordless phones

---

## Best Practices for Troubleshooting

| Practice | Reason |
| --- | --- |
| **Baseline healthy network first** | Know what "good" looks like before troubleshooting issues |
| **Test with simple device first** | Isolate client issues from network issues |
| **Check signal (RSSI/SNR) early** | Many issues trace back to weak signal |
| **Monitor AP logs continuously** | Identify patterns before users complain |
| **Enable debug on AP during issue** | Capture exact error messages (EAP failure, DFS event, etc.) |
| **Test from multiple locations** | Identify coverage gaps vs widespread issue |
| **Verify both directions** | If traffic asymmetric, routing may be broken upstream |
| **Don't assume latest AP firmware** | Some firmware versions have bugs; check release notes |

---

## Notes / Gotchas

- **RSSI Variation is Normal:** Fluctuations of ±5 dB over time are expected due to movement
  and multipath. Monitor for sustained drops, not brief dips.

- **Legacy Client Handshake:** If old device connects to modern AP, entire SSID may negotiate
  legacy rates (802.11g at 54 Mbps). Isolate legacy clients on separate SSID or AP.

- **Certificate Expiration Silent Failure:** Server certificate expiration in 802.1X causes
  immediate EAP failure with minimal AP logging. Always monitor certificate expiry dates.

- **VLAN Mismatch:** If AP trunk port misconfigured, DHCP traffic may not reach server (AP on
  wrong VLAN). Verify AP management VLAN matches configuration and wired network.

- **MTU Fragmentation:** If MTU too small between AP and RADIUS, large EAP frames fragment and
  drop. Verify MTU ≥1500 on AP and RADIUS server networks.

---

## See Also

- [WiFi RF Fundamentals](../theory/wifi_rf_fundamentals.md)

- [802.1X and EAP Authentication](../theory/wifi_authentication_8021x.md)

- [WiFi Roaming (802.11r/k/v)](../theory/wifi_roaming.md)

- [WiFi Security](../theory/wifi_security.md)

- [WiFi Network Design](../theory/wifi_network_design.md)

- [BGP Troubleshooting](bgp_troubleshooting.md)
