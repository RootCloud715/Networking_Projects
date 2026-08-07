# Simple Python Web Server

A minimal HTTP web server built from scratch using raw TCP sockets. It handles one request per connection: it accepts a client, parses the HTTP GET request, looks up the requested file, and returns either a `200 OK` response with the file's contents or a `404 Not Found` error.

This project was built to understand what's actually happening under the hood of every web server (Apache, nginx, etc.) at the socket and protocol level.

## Features

- Listens for incoming TCP connections on 127.0.0.1:9999
- Performs minimal HTTP request-line parsing to extract the requested file path.
- Serves files in binary mode, allowing HTML, images, PDFs, and other binary files to be transmitted without text decoding.
- Returns a basic `404 Not Found` response for missing files
- Returns a `405` response for non-GET request methods
- Guards against malformed/empty requests
- Runs continuously, handling one client at a time in a loop

## How It Works

1. **Listening socket** — created once, bound to `(HOST, PORT)`, and calls `.listen()` to wait for incoming connections.
2. **`accept()`** — blocks until a client connects, then returns a brand-new **connection socket** dedicated to that client (distinct from the listening socket, which is never used to send/receive data directly).
3. **`recv()`** — reads the raw HTTP request bytes off the connection socket and decodes them to a string.
4. **Parsing** — splits the request on whitespace; the second token (e.g. `/index.html`) is the requested path. The leading slash is stripped to turn it into a valid relative filename.
5. **File lookup** — attempts to `open()` the file in binary mode (`'rb'`):
   - **Success** → reads the file's bytes, builds an `HTTP/1.1 200 OK` header, and sends header + file bytes together.
   - **`FileNotFoundError`** → sends an `HTTP/1.1 404 Not Found` header instead.
6. **Close & repeat** — the connection socket is closed, and the loop returns to `accept()` to wait for the next client. The listening socket itself is never closed, which is why the server can keep serving new requests indefinitely.

## Requirements

- Python 3.x (no external dependencies — uses only the built-in `socket` module)

## Usage

1. Place the files you want to serve (e.g. `index.html`) in the same directory as `web_server.py`.
2. Run the server:
   ```bash
   python web_server.py
   ```
3. You should see:
   ```
   [*] server is listening on 9999:127.0.0.1
   ```
4. Open a browser and navigate to:
   ```
   http://127.0.0.1:9999/index.html
   ```
5. Request a file that doesn't exist to see the 404 behavior:
   ```
   http://127.0.0.1:9999/doesnotexist.html
   ```



## Project Files

| File | Purpose |
|---|---|
| `web_server.py` | The server implementation |
| `index.html` | Sample file to test a successful `200 OK` response |

## Known Limitations

- Handles one request at a time (no threading/concurrency) — a second client must wait until the current request-response cycle finishes.
- No support for HTTP methods other than `GET` (returns `405` for anything else).
- No `Content-Type` header is set, so browsers infer file type rather than being told explicitly.
- No support for persistent (`keep-alive`) connections — each request opens and closes its own connection socket.
- No path-traversal protection; requested paths are currently converted directly into filesystem paths.

## Key Concepts Demonstrated

- **Listening socket vs. connection socket**: the listening socket only exists to `accept()` new clients; only the connection socket returned by `accept()` is bound to a specific client and can send/receive data.
- **`bytes` vs. `str`**: sockets only transmit `bytes`. Text must be `.encode()`d before sending; received data must be `.decode()`d before parsing.
- **Binary-safe file reads**: files are opened in `'rb'` mode so that non-text files (images, PDFs, etc.) aren't corrupted by text-mode decoding.
- **The `accept()` loop**: wrapping `accept()` in `while True` lets a single listening socket serve an unlimited sequence of distinct client connections, each identified by its own IP/port 4-tuple.
- **TCP vs. HTTP**: TCP provides the reliable byte stream between client and server, while HTTP defines the application-layer request and response format carried over that TCP connection.