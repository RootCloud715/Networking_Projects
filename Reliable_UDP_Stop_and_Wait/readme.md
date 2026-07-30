# Reliable UDP – Stop-and-Wait ARQ (v0.1)

A Python implementation of a reliable data transfer protocol built on top of UDP using the **Stop-and-Wait Automatic Repeat reQuest (ARQ)** algorithm.

This project demonstrates how reliability can be implemented over an unreliable transport protocol by adding retransmissions, sequence numbers, duplicate detection, and timeout handling.

> **Status:** v0.1 (Learning Project)

---

## Features

- UDP client/server communication
- Stop-and-Wait protocol
- Sequence numbers
- Timeout-based retransmission
- Duplicate packet detection
- Duplicate response handling
- Simulated packet loss
- Simulated response loss

---

## Why This Project?

UDP provides:

- No reliability
- No acknowledgements
- No retransmissions
- No ordering guarantees

This project adds reliability at the application layer using the Stop-and-Wait ARQ algorithm — the same core idea (in simplified form) behind TCP's own reliability guarantees.

---

## Project Structure

```
.
├── client.py
├── server.py
└── README.md
```

---

## Protocol

### Packet Format

Current packet format:

```
<sequence_number>:<message>

Example:
0:hello_server!
1:hello_server!
```

The server responds with:

```
<sequence_number>:echo:<message>

Example:
0:echo:hello_server!
```

---

## How It Works

1. Client sends a packet with a sequence number.
2. Server receives the packet.
3. Server may randomly drop the packet (simulation).
4. Server processes the packet.
5. Server sends a response containing the same sequence number.
6. Client waits for a matching sequence number, discarding any stale/mismatched responses.
7. If no matching response arrives within the timeout budget, the client retransmits the packet.
8. If a duplicate packet arrives, the server resends the previous cached response instead of reprocessing it.

---

## Bugs I Hit While Building This

Building this taught me more from debugging it than from writing the happy path. A few worth recording:



**1. Double-sending on retry**
An early version of the retry loop sent the packet once inside `try`, and *again* inside the `except TimeoutError` block — then let the `while` loop repeat on top of that. Net effect: every timeout actually sent two packets, not one, silently doubling network load and making duplicate-response races more likely. Fixed by letting the loop's natural repetition be the only place a resend happens.

**2. Accepting any datagram as "the" response**
The original client did `recvfrom()` and assumed whatever came back was the reply to the request it just sent. This breaks the moment stale/duplicate responses are possible — a leftover response from a previous retry can arrive right when the client is expecting a fresh one, and gets accepted as valid. Fixed by having the server echo back the sequence number, and having the client verify it matches before accepting the response — discarding (not resending on) anything that doesn't match.

**3. `settimeout()` resets on every call, it isn't cumulative**
Assumed `socket.settimeout(5)` gave a single 5-second budget for an entire "wait for a valid response" operation. In reality, it resets on every individual blocking call — so a loop that discards stale packets and calls `recvfrom()` again could theoretically wait far longer than 5 seconds if junk packets kept trickling in. Fixed by tracking elapsed time with `time.monotonic()` and passing the *remaining* budget into `settimeout()` on each inner-loop iteration.

---

## Why This Matters for Security

This project started as a networking exercise, but a lot of the mechanisms here are directly relevant to application and cloud security:

- **Sequence numbers as replay protection.** The seq-number check that prevents the server from reprocessing a duplicate request is structurally the same idea behind replay-attack prevention in real protocols — TLS record sequence numbers, Kerberos ticket nonces, and OAuth `nonce`/`state` parameters all exist to stop an attacker (or an unreliable network) from getting an old, valid message accepted a second time.

- **Idempotency as a security property, not just a reliability one.** The reason duplicate processing matters isn't just correctness — non-idempotent operations (balance transfers, privilege grants, counter increments) processed twice due to a replayed or retried request are a real class of bug/vulnerability. Payment APIs (e.g. Stripe's idempotency keys) and AWS SQS FIFO's deduplication IDs solve exactly this problem, using the same at-least-once-delivery + receiver-side-cache pattern built here.

- **Trusting unauthenticated fields.** The current protocol trusts the sequence number and source address as-is, with no signature or MAC. A natural next step — and one I plan to explore — would be adding HMAC-based message authentication, since in a real adversarial setting an attacker could forge sequence numbers or spoof a source address to bypass the dedup cache entirely.

---

## Simulated Network Conditions

To test protocol reliability, the server randomly simulates:

- Packet loss
- Response loss

This forces the client to perform retransmissions.

---

## Running

### Start the server

```bash
python server.py
```

### Start the client

```bash
python client.py
```

---

## Example Output

**Server**

```
[*] UDP server is listening on 0.0.0.0:9998
[!] Simulating dropped packets
[!] Simulating dropped response
```

**Client**

```
[!] Timeout, retry 1/5
echo: hello_server!
```

---

## Current Limitations

This is an educational implementation. Current limitations include:

- Text-based packet format
- No checksum
- No binary packet headers
- No message authentication (no HMAC/signature — seq numbers and addresses are trusted as-is)
- No explicit ACK packet
- Sequence numbers increase indefinitely
- `last_seen` dedup cache grows forever with no eviction
- Fixed timeout value
- Single-client testing focus

---

## Future Improvements

Planned for future versions:

- ACK packet type
- Alternating-bit protocol (0/1 sequence numbers)
- Binary packet format using `struct`
- CRC32 checksum
- HMAC-based message authentication
- Time-bounded eviction for the dedup cache
- Packet corruption simulation
- Packet reordering simulation
- Network delay simulation
- RTT measurement
- Exponential backoff
- Transfer statistics
- Wireshark packet analysis
- Sliding Window protocol
- Go-Back-N
- Selective Repeat

---

## Concepts Demonstrated

- UDP Socket Programming
- Reliable Data Transfer
- Stop-and-Wait ARQ
- Timeout Handling
- Retransmission
- Duplicate Detection
- Sequence Numbers
- Idempotency
- Fault Simulation
- Application-layer Reliability

---

## Built With

- Python 3
- `socket`
- `time`
- `random`

---

## License

This project is intended for educational purposes.