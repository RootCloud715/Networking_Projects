# SMTP Mail Client

A Python mail client that connects to Gmail's SMTP server and sends an email over TLS — prompts interactively for subject, body, and an optional file attachment (PDF, image, etc). Built in two versions: one using raw TCP sockets to implement the SMTP protocol manually, and one using Python's `smtplib` standard library.

## Files

- `raw_socket_client.py` — sends mail using only the `socket` and `ssl` modules. Manually performs the TLS handshake, sends each SMTP command (`EHLO`, `AUTH LOGIN`, `MAIL FROM`, `RCPT TO`, `DATA`), and reads the server's response after each step.
- `smtp_client.py` — the interactive client, built on `smtplib` and `email.message.EmailMessage`. Prompts for subject, body, and an optional attachment path at runtime instead of sending a fixed message.

## Setup

### 1. Generate a Gmail App Password

Gmail does not accept your normal account password over SMTP. You need:
1. 2-Step Verification enabled on your Google account.
2. An App Password generated at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) (16 characters, no spaces).

### 2. Set environment variables

**Linux / macOS:**
```bash
export GMAIL_ADDRESS="your_email@gmail.com"
export GMAIL_APP_PASSWORD="your16charapppassword"
export Recpt_GMAIL_ADDRESS="recipient@gmail.com"
```

**Windows (PowerShell):**
```powershell
$env:GMAIL_ADDRESS = "your_email@gmail.com"
$env:GMAIL_APP_PASSWORD = "your16charapppassword"
$env:Recpt_GMAIL_ADDRESS = "recipient@gmail.com"
```

### 3. Run it

```bash
python smtp_client.py
```

You'll be prompted for:
```
Enter subject:
Enter body:
Enter path to attachment (or press Enter to skip):
```

Leaving the attachment prompt blank sends a plain text-only email. Any file path (`.pdf`, `.jpg`, `.png`, etc.) attaches that file to the message.

## How it works — the SMTP dialogue

| Step | Command | Server response | Purpose |
|---|---|---|---|
| 1 | *(TCP + TLS connect)* | `220` | Server greeting |
| 2 | `EHLO` | `250-...` | Client introduces itself, server lists capabilities |
| 3 | `AUTH LOGIN` | `334` | Server requests base64-encoded username |
| 4 | *(base64 email)* | `334` | Server requests base64-encoded password |
| 5 | *(base64 App Password)* | `235` | Authentication successful |
| 6 | `MAIL FROM:<...>` | `250` | Declares the envelope sender |
| 7 | `RCPT TO:<...>` | `250` | Declares the recipient |
| 8 | `DATA` | `354` | Server is ready for message content |
| 9 | headers + blank line + body + `.` | `250` | Message accepted |
| 10 | `QUIT` | `221` | Connection closed |

`raw_socket_client.py` performs each of these steps explicitly. `smtp_client.py` performs the same sequence internally through `smtplib`.

## How the attachment is built

`smtp_client.py` uses `email.message.EmailMessage.add_attachment()`, which converts the message into proper multipart MIME format automatically. The relevant steps:

1. The file is opened in **binary mode** (`"rb"`), since attachments (images, PDFs) are raw binary data, not text.
2. `mimetypes.guess_type(path)` inspects the filename to guess the MIME type (e.g. `application/pdf`, `image/png`) from its extension.
3. That result is split into a `maintype`/`subtype` pair (`"application"`, `"pdf"`), which `add_attachment()` requires as separate arguments.
4. `os.path.basename(path)` strips the full path down to just the filename, so the recipient sees `report.pdf`, not the entire local file path.
5. The message is fully assembled — subject, body, attachment — **before** the SMTP connection is opened, so nothing is sent half-built.

Attachment logic is skipped entirely if the user presses Enter with no path, checked with a plain truthiness check (`if attachment_path:`) on the input string, before any attempt is made to open a file.

## Notes

- Credentials are read from environment variables — never hardcoded in the source.
- `smtp_client.py` catches specific `smtplib` exceptions (`SMTPAuthenticationError`, `SMTPRecipientsRefused`, `SMTPException`) so a failure gives a clear reason instead of a raw crash.
- Only a single attachment per email is supported.

## Bugs hit during development (and what they taught)

Documented here deliberately — these were real mistakes made and fixed while building this, not hypothetical edge cases.

- **`bind()`/`listen()` instead of `connect()`** — an early raw-socket attempt tried to make the script act like a server (binding to Gmail's address) instead of a client connecting out to it. Fixed by using `.connect()`, the correct client-side verb.
- **`AttributeError` from double-encoding** — passed an already-`bytes` value into `.encode()` (a `str`-only method), and separately tried `.encode()` on the wrong object. Root cause was not tracking `str` vs `bytes` types through each step of the socket send/receive path.
- **Discarded return values** — `ssl.create_default_context()` and `mimetypes.guess_type()` were both called at different points without storing their return value, silently doing nothing useful. `wrap_socket()` was similarly called without capturing the new TLS-wrapped socket object it returns.
- **Missing angle brackets in `MAIL FROM`/`RCPT TO`** — sent bare addresses instead of `<address>`, which RFC 5321 requires as part of the command syntax; Gmail accepted it inconsistently until brackets were added.
- **Commands sent out of order** — `MAIL FROM`, `RCPT TO`, and `DATA` were initially skipped entirely, jumping straight from authentication to sending the message body, which breaks the server's expected command sequence.
- **Success message printed after a caught failure** — `print("Email was sent")` was originally placed *after* the `try/except` block instead of inside it, so it printed unconditionally even when an exception had just been caught and reported. Moved inside the `try`, right after the line that can actually confirm success.
- **`msg["Body"] = ...` instead of `msg.set_content(...)`** — tried to set the email body as if it were a header field. This doesn't raise an error, it just silently creates a meaningless extra header while leaving the actual message body empty. Headers (`Subject`, `From`, `To`) and message content (`set_content()`) are two different APIs on `EmailMessage`.
- **`filename=...` (literal Ellipsis)** — left a placeholder `...` in `add_attachment()`'s `filename` argument; this is valid Python (`Ellipsis`) so it didn't crash, it just set the wrong filename. Replaced with `os.path.basename(attachment_path)`.
- **Checking `file_data` to detect "no attachment"** — attempted to test whether an attachment was provided using a variable that wouldn't exist yet if the path were empty, since `open("")` fails before that variable is ever assigned. Fixed by checking the input string itself (`if attachment_path:`) before attempting to open anything.
- **`.split()` applied to a tuple** — `mimetypes.guess_type()` returns a tuple, not a string; `.split()` only exists on strings. The tuple is unpacked directly (`mime_type, encoding = ...`), and `.split("/")` is applied afterward to the resulting MIME-type string, not the tuple.