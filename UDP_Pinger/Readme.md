# UDP Pinger

A Python implementation of a client-server "ping" utility built on top of **UDP**, inspired by the classic Kurose & Ross (*Computer Networking: A Top-Down Approach*) socket programming assignment.

The client sends 10 sequenced "ping" messages to a server over UDP, the server randomly drops some packets/replies to simulate real network loss, and the client measures the **Round Trip Time (RTT)** for each successful reply — reporting a final summary of packet loss and min/avg/max RTT, similar to the standard OS `ping` command.

## How It Works

Unlike TCP, UDP provides **no built-in reliability** — no handshake, no acknowledgments, no retransmission. This project intentionally uses UDP so that loss-detection and retry logic must be implemented explicitly at the application layer:

1. The client sends a ping message (`seq:timestamp`) to the server.
2. The server randomly decides (with a set probability) whether to:
   - Drop the incoming ping entirely, or
   - Receive it but drop the outgoing reply.
3. If the client doesn't receive a reply within a **1-second timeout**, it retries the same sequence number, up to **3 attempts**.
4. If all 3 attempts fail, that sequence number is marked as lost.
5. After all 10 sequence numbers are processed, the client prints a summary: packets sent/received/lost, and min/avg/max RTT (in milliseconds).

## Project Structure

```
udp-pinger/
├── client.py
├── server.py
├── README.md
└── LICENSE
```

## Requirements

- Python 3.x (standard library only — no external dependencies)

## Usage

Run the server and client in **two separate terminals** (the server runs an infinite loop and must be running before/while the client sends pings):

**Terminal 1 — start the server:**
```bash
python server.py
```

**Terminal 2 — run the client:**
```bash
python client.py
```

### Example Output

**Client:**
```
Reply from ('127.0.0.1', 9999): seq=0 time=0.43ms
Reply from ('127.0.0.1', 9999): seq=1 time=0.14ms
Reply from ('127.0.0.1', 9999): seq=2 time=0.18ms
Reply from ('127.0.0.1', 9999): seq=3 time=0.48ms
Request timed out: seq=4
Reply from ('127.0.0.1', 9999): seq=5 time=0.35ms
Reply from ('127.0.0.1', 9999): seq=6 time=0.47ms
Reply from ('127.0.0.1', 9999): seq=7 time=0.27ms
Request timed out: seq=8
Reply from ('127.0.0.1', 9999): seq=9 time=0.38ms

--- Summary ---
Packets: Sent=10, Received=8, Lost=2
RTT min/avg/max = 0.14/0.34/0.48 ms
```

**Server:**
```
[*] Server is listening on 127.0.0.1:9999
[!] Simulating dropped packets
[!] Simulating dropped response
...
```

## Design Notes

- **No TCP-style handshake.** UDP is connectionless — there is no SYN/ACK. Sequence numbers alone identify each ping message.
- **Timeout-based loss detection.** Since UDP gives no signal when a packet is lost, the client's socket timeout (`settimeout(1)`) is the *only* mechanism for detecting that something went wrong.
- **Retry with a bounded limit.** Each sequence number gets up to 3 attempts before being marked as permanently lost, preventing indefinite retries while still tolerating transient delays.
- **`time.monotonic()` for timing**, not `time.time()` — RTT measurement requires a clock that is guaranteed never to jump backward (e.g., due to NTP correction), which `monotonic()` guarantees and wall-clock time does not.
- **The client cannot distinguish *why* a packet was lost.** A timeout could mean the ping never reached the server, the reply never made it back, or the server deliberately dropped it to simulate loss — these are observationally identical from the client's side.

## Relationship to Real `ping`

This project mimics the *behavior* of the standard `ping` utility (RTT measurement, loss reporting, min/avg/max summary) but is **not** a reimplementation of it. Real `ping` uses **ICMP Echo Request/Reply** messages, a distinct network-layer protocol with no ports and typically requiring elevated privileges — not UDP sockets. This client/server pair only works against the custom server included in this repo, since it relies on a specific application-defined message format (`seq:timestamp`) that no real-world server would understand.

## License

MIT 