# TCP Header

TCP provides reliable, ordered, and error-checked delivery of a byte stream between
applications. The minimum header is 20 bytes; the Options field can extend it to
60 bytes. Data Offset indicates the actual header length in 32-bit words.

## Quick Reference

| Property | Value |
| --- | --- |
| **OSI Layer** | Layer 4 — Transport |
| **TCP/IP Layer** | Transport |
| **RFC** | RFC 9293 |
| **Wireshark Filter** | `tcp` |
| **IP Protocol** | `6` |

## Header Structure

```mermaid
---
title: "TCP Packet"
---
packet
0-15: "Source Port"
16-31: "Destination Port"
32-63: "Sequence Number"
64-95: "Acknowledgment Number"
96-99: "Data Offset"
100-102: "Reserved"
103: "NS"
104: "CWR"
105: "ECE"
106: "URG"
107: "ACK"
108: "PSH"
109: "RST"
110: "SYN"
111: "FIN"
112-127: "Window Size"
128-143: "Checksum"
144-159: "Urgent Pointer"
160-191: "Options (if Data Offset > 5)"
```

## Field Reference

| Field | Bits | Description |
| --- | --- | --- |
| **Source Port** | 16 | Port number of the sending application. |
| **Destination Port** | 16 | Port number of the receiving application. |
| **Sequence Number** | 32 | Position of the first byte of this segment in the sender's byte stream. Used for ordering and reassembly. |
| **Acknowledgment Number** | 32 | Next sequence number the sender expects to receive. Valid only when ACK flag is set. |
| **Data Offset** | 4 | Header length in 32-bit words. Minimum `5` (20 bytes); maximum `15` (60 bytes). |
| **Reserved** | 3 | Must be zero. |
| **NS** | 1 | ECN nonce concealment protection (RFC 3540). |
| **CWR** | 1 | Congestion Window Reduced. Sender reduced its congestion window in response to an ECE signal. |
| **ECE** | 1 | ECN-Echo. Signals congestion to the sender when set in an ACK. |
| **URG** | 1 | Urgent pointer field is significant. |
| **ACK** | 1 | Acknowledgment number is valid. Set on all segments after the initial SYN. |
| **PSH** | 1 | Push. Receiver should pass buffered data to the application immediately. |
| **RST** | 1 | Reset the connection. Sent in response to an invalid segment or to abort a connection. |
| **SYN** | 1 | Synchronise sequence numbers. Set only on the first two segments of the three-way handshake. |
| **FIN** | 1 | No more data from the sender. Initiates the four-way connection termination. |
| **Window Size** | 16 | Number of bytes the sender is willing to receive, starting from the acknowledgment number. Forms the basis of TCP flow control. |
| **Checksum** | 16 | One's complement checksum over a pseudo-header (source/destination IP, protocol, segment length), TCP header, and payload. |
| **Urgent Pointer** | 16 | Offset from the sequence number to the last urgent byte. Valid only when URG is set. |
| **Options** | 0–320 | Variable-length options padded to a 32-bit boundary. Common options: MSS, Window Scale, SACK, Timestamps. |

## Connection Establishment (Three-Way Handshake)

SYN and SYN-ACK exchange synchronises sequence numbers in both directions before
any data is transferred.

```mermaid

sequenceDiagram
    participant C as Client
    participant S as Server
    C->>S: SYN (seq=x)
    S->>C: SYN-ACK (seq=y, ack=x+1)
    C->>S: ACK (seq=x+1, ack=y+1)
    Note over C,S: Connection established
    C->>S: Data (seq=x+1)
    S->>C: ACK (ack=x+1+len)
```

## Connection Termination

### Graceful close (FIN)

Either side may initiate a graceful close. Because TCP is full-duplex, each direction
is closed independently — a FIN closes only the sender's direction, allowing the
other side to continue sending until it is ready to close.

```mermaid

sequenceDiagram
    participant C as Client
    participant S as Server
    C->>S: FIN (seq=x)
    S->>C: ACK (ack=x+1)
    Note over S: Server may still send data
    S->>C: FIN (seq=y)
    C->>S: ACK (ack=y+1)
    Note over C,S: Connection fully closed
```

The client enters `TIME_WAIT` after sending the final ACK and holds the connection
state for 2× MSL (Maximum Segment Lifetime, typically 60–120 seconds) to absorb any
delayed duplicate segments.

### Abortive reset (RST)

RST immediately tears down the connection without a four-way exchange. Any buffered
data is discarded. Common causes:

| Scenario | Direction |
| --- | --- |
| Connection attempt to a closed port | Server → Client |
| Application crash or forceful close (`SO_LINGER` with timeout 0) | Either |
| Middlebox or firewall policy rejection | Middlebox → Either |
| Half-open connection detected (one side rebooted) | Either |
| Out-of-window segment received | Either |

```mermaid

sequenceDiagram
    participant C as Client
    participant S as Server
    C->>S: SYN (seq=x)
    S->>C: RST-ACK
    Note over C,S: Connection refused — port closed
```

## Notes

- **Window Scale option** (RFC 1323) shifts the Window Size field left by up to 14

  bits, allowing windows up to 1 GB — essential for high-bandwidth, high-latency paths.

- **SACK (Selective Acknowledgment)** allows the receiver to acknowledge

  non-contiguous blocks, avoiding unnecessary retransmission of already-received data.

- **Timestamps option** enables RTT measurement and protects against sequence number

  wrap-around (PAWS) on fast connections.
