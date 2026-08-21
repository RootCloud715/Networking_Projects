# Web Proxy (v0.1)

A minimal, single-threaded HTTP proxy server built from scratch in Python using raw sockets. It sits between a client and origin server: it accepts the client's HTTP request, forwards a reconstructed request to the origin server, and relays the origin response bytes back to the client without inspecting or modifying the response.

> **Status: v0.1** — supports basic plain-HTTP `GET` requests using absolute-form proxy requests. Client headers are not preserved, HTTPS/`CONNECT` is unsupported, and requests/responses use simplified HTTP parsing.

---

## How It Works

```text
Client
   │
   │ client_socket
   ▼
 Proxy
   │
   │ proxy_client_socket
   ▼
Origin Server
```

The proxy maintains **two separate TCP sockets** per request:

* `client_socket` — connection between the client and proxy.
* `proxy_client_socket` — connection between the proxy and origin server.

The proxy does not generate application content; it parses the client's request, constructs a new origin request, and relays the origin response back to the client.

### Request Flow

1. The proxy listens on `0.0.0.0:9999` and accepts an incoming client connection.

2. It reads up to 4096 bytes from the client socket and treats the received data as the HTTP request.

3. `parse_request()` validates the request line and extracts the `method`, `hostname`, `port`, and `path`.

4. Proxy clients send the **absolute-form URL** in the request line:

   ```http
   GET http://example.com/index.html HTTP/1.1
   ```

   Unlike a direct HTTP request:

   ```http
   GET /index.html HTTP/1.1
   Host: example.com
   ```

5. The proxy opens a new TCP connection to `(hostname, port)`.

6. It reconstructs the request using the **path** and a `Host:` header. Other client headers are not forwarded.

   ```http
   GET /index.html HTTP/1.1
   Host: example.com
   ```

7. The proxy sends the reconstructed request to the origin server.

8. It repeatedly calls `recv()` on the origin socket and forwards each received chunk to the client.

9. When `recv()` returns `b''`, the origin has closed its connection.

10. Both per-request sockets are closed and the proxy accepts the next client.

---

## Project Structure

```text
web_proxy/
├── proxy.py      # Proxy implementation
└── README.md
```

Everything currently lives in a single file:

* `parse_request(message)` — parses and validates the HTTP request line and extracts `(method, hostname, port, path)`.
* `run_proxy()` — manages the listening socket, client connections, origin connections, response relay, error handling, and socket cleanup.

---

## Running It

### Terminal 1 — Start the Proxy

```bash
python3 proxy.py
```

The proxy listens on:

```text
0.0.0.0:9999
```

Stop it with:

```text
Ctrl+C
```

### Terminal 2 — Test with curl

```bash
curl -x http://127.0.0.1:9999 -v http://neverssl.com/
```

You can also configure a browser's manual HTTP proxy:

```text
Proxy: 127.0.0.1
Port: 9999
```

Use a plain-HTTP site for testing.

---

## Errors Encountered While Building

These were real bugs encountered during development. They are kept as a debugging log because each one maps to a specific networking or programming misunderstanding.

| #  | Bug                                                                  | Root Cause                                                                                                                                                 |
| -- | -------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1  | `IndentationError`                                                   | Mixed 3-space/4-space indentation in the same function block.                                                                                              |
| 2  | `AttributeError: module 'argparse' has no attribute 'parse_request'` | Confused the standard-library `argparse` module with the custom `parse_request()` function defined in the same file.                                       |
| 3  | Proxy always connected to one fixed address                          | `connect()` used hardcoded address values instead of the `hostname`/`port` returned by `parse_request()`.                                                  |
| 4  | `OSError` on `.accept()`                                             | Called `.accept()` on an outgoing socket instead of the listening socket. `.accept()` is only used on a listening socket waiting for incoming connections. |
| 5  | Response relayed to the wrong destination                            | Sent the origin response through `proxy_client_socket` instead of `client_socket`.                                                                         |
| 6  | Infinite loop / stuck relay                                          | `recv()` was performed outside the relay loop, causing the same stale data to be processed repeatedly.                                                     |
| 7  | `OSError: Bad file descriptor`                                       | Sockets were closed inside the relay loop without immediately breaking out of the loop.                                                                    |
| 8  | Proxy died after exactly one request                                 | The main listening socket was mistakenly closed per request instead of only closing the per-request sockets.                                               |
| 9  | List index confusion                                                 | Used `[1]` expecting the first element of a list. Python uses zero-based indexing, so the first element is `[0]`.                                          |
| 10 | `ValueError: not enough values to unpack`                            | Malformed request lines were split into an unexpected number of fields and were not initially handled by the per-request exception logic.                  |

---

## Errors Encountered While Testing

| # | Symptom                                                                             | Diagnosis                                                                                                                                                                                                                                       |
| - | ----------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 | `curl: (7) Failed to connect... Connection refused`                                 | The proxy process had crashed from an earlier unhandled exception, so nothing was listening on port `9999`.                                                                                                                                     |
| 2 | Entire proxy process exits on one bad request                                       | An exception inside the main loop was terminating the process. Per-request handling was moved inside `try/except/finally` so the listening loop survives request errors.                                                                        |
| 3 | `curl: (52) Empty reply from server` / `[WinError 10060] connection attempt failed` | The proxy timed out while connecting to the origin server.                                                                                                                                                                                      |
| 4 | Same connection intermittently succeeds/fails                                       | IPv4 connectivity to the tested origin was unreliable while direct `curl` could succeed over IPv6. The proxy currently uses `AF_INET`, so it is IPv4-only. A 5-second socket timeout prevents an unreachable origin from blocking indefinitely. |
| 5 | `301 Moved Permanently` from `pypi.org`                                             | Expected behavior. The origin server redirects HTTP traffic to HTTPS. The proxy successfully relayed the redirect response.                                                                                                                     |

---

## Known Limitations & Roadmap

This is **v0.1**, deliberately scoped to basic HTTP proxy mechanics.

### HTTPS / `CONNECT`

Not implemented.

HTTPS proxies normally receive:

```http
CONNECT example.com:443 HTTP/1.1
```

The proxy would need to establish a TCP connection to the destination, return:

```http
HTTP/1.1 200 Connection Established
```

and then become a raw bidirectional byte tunnel. TLS traffic would remain encrypted between the client and origin.

### Concurrency

The proxy is currently single-threaded.

One slow client/origin connection blocks the next client.

Future implementations could use:

* `threading`
* `select`
* `selectors`
* `asyncio`

### Caching

The proxy does not inspect response headers such as `Cache-Control`, `ETag`, or `Content-Length`, so every request is forwarded directly to the origin.

### `Transfer-Encoding: chunked`

The proxy treats chunked responses as opaque bytes and forwards them without decoding them.

This is correct for transparent relay behavior because the client is responsible for interpreting the HTTP response.

Chunk-aware processing would only become necessary for features such as caching, body inspection, or response-size analysis.

### Persistent Connections / Keep-Alive

The proxy currently closes both sockets after the origin closes its connection.

It does not:

* reuse origin connections
* maintain persistent client connections
* support multiple HTTP requests over one connection

### HTTP Request Framing

v0.1 assumes the complete HTTP request is available within a single:

```python
recv(4096)
```

call.

This is a simplification.

TCP provides a **byte stream**, not message boundaries. A complete HTTP request may arrive across multiple `recv()` calls.

### Client Headers

Only the `Host` header is reconstructed.

Headers such as:

```text
User-Agent
Accept
Cookie
Accept-Encoding
Connection
```

are not forwarded.

### IPv6

The proxy uses:

```python
socket.AF_INET
```

and the simplified URL parser does not support IPv6 literal addresses.

---

## Roadmap

```text
v0.1
 ├── Raw TCP proxy
 ├── HTTP GET
 ├── Request-line parsing
 ├── Origin connection
 ├── Response relay
 └── Error handling

v0.2
 ├── Proper HTTP request framing
 ├── Header parsing
 ├── Header forwarding
 └── Better HTTP validation

v0.3
 ├── HTTPS CONNECT tunneling
 └── Bidirectional socket relay

v0.4+
 ├── Concurrency
 ├── Persistent connections
 ├── Caching
 └── More complete HTTP handling
```

**Current goal:** understand the mechanics of TCP sockets, HTTP proxy requests, connection lifecycle, and byte-stream relaying before adding higher-level proxy features.
