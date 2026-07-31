# IRTP Examples

**Version:** 0.1 (Experimental)

This document provides practical examples demonstrating how applications interact with the Intelligent Realtime Transport Protocol (IRTP). The examples focus on the IRTP programming model rather than any specific AI provider implementation.

---

# Example 1 — Creating a Session

Every interaction begins by creating an IRTP session.

```python
from irtp import Session

session = Session(
    endpoint="wss://provider.example/realtime"
)

await session.connect()
```

Once connected, the session is responsible for negotiating protocol capabilities and establishing communication with the remote endpoint.

---

# Example 2 — Sending a Prompt

Applications communicate through the session interface.

```python
response = await session.send(
    "Explain quantum computing."
)

print(response)
```

The application does not interact directly with WebSockets, HTTP requests, or provider-specific APIs.

---

# Example 3 — Interactive Session

```python
await session.connect()

while True:

    prompt = input("> ")

    if prompt.lower() == "exit":
        break

    response = await session.send(prompt)

    print(response)

await session.close()
```

IRTP manages the session lifecycle while presenting a simple request/response interface to the application.

---

# Example 4 — Streaming Responses

Applications may process incremental responses.

```python
await session.connect()

async for chunk in session.stream(
    "Describe the history of networking."
):

    print(chunk, end="")
```

Streaming allows large responses to be consumed without waiting for the complete message.

---

# Example 5 — Capability Negotiation

Following transport establishment, the peers exchange protocol capabilities.

Example capability advertisement:

```json
{
  "type": "capability",
  "capabilities": {
    "streaming": true,
    "chunking": true,
    "compression": false,
    "binary": false
  }
}
```

Applications typically do not perform capability negotiation directly; the IRTP session manager handles this automatically.

---

# Example 6 — Chunked Message

Large logical messages may be transmitted as multiple chunks.

```json
{
  "session": "session-1",
  "sequence": 42,
  "chunk": {
    "index": 2,
    "total": 5
  },
  "payload": "..."
}
```

IRTP performs message reassembly before exposing the completed message to the application.

---

# Example 7 — Transport Independence

Changing transports should not require application changes.

```python
session = Session(
    transport=WebSocketTransport(...)
)
```

Later:

```python
session = Session(
    transport=LocalTransport(...)
)
```

The remainder of the application remains unchanged.

---

# Example 8 — Provider Independence

Switching AI providers requires replacing only the provider adapter.

```text
Application
      │
      ▼
IRTP Session
      │
      ▼
OpenAI Adapter
      │
      ▼
Realtime API
```

Later:

```text
Application
      │
      ▼
IRTP Session
      │
      ▼
Local Adapter
      │
      ▼
Local Runtime
```

Application code remains identical.

---

# Example 9 — Session Lifecycle

Typical lifecycle:

```text
Create Session
      │
Connect
      │
Capability Negotiation
      │
Session Ready
      │
Exchange Messages
      │
Close Session
```

Applications only interact with the session manager.

---

# Example 10 — Graceful Shutdown

```python
try:

    await session.connect()

    response = await session.send(
        "Hello."
    )

finally:

    await session.close()
```

A graceful shutdown ensures resources are released and the transport connection is terminated cleanly.

---

# Example 11 — Error Handling

```python
try:

    response = await session.send(
        prompt
    )

except IRTPTransportError:

    print("Transport unavailable.")

except IRTPProtocolError:

    print("Protocol violation.")

except IRTPApplicationError:

    print("Application rejected request.")
```

Separating errors by layer allows applications to implement appropriate recovery strategies.

---

# Example 12 — Custom Transport

Developers may implement new transports by conforming to the IRTP transport interface.

```python
class CustomTransport(Transport):

    async def connect(self):
        ...

    async def send(self, message):
        ...

    async def receive(self):
        ...

    async def close(self):
        ...
```

No modifications to the IRTP protocol layer are required.

---

# Example 13 — Envelope Construction

Every application message is wrapped in an IRTP envelope before transmission.

```json
{
  "version": "0.1",
  "session": "session-42",
  "sequence": 19,
  "type": "message",
  "payload": {
    "prompt": "Summarize TCP congestion control."
  }
}
```

The envelope provides protocol metadata independent of the underlying transport.

---

# Example 14 — Multiple Sessions

Applications may manage multiple concurrent sessions.

```python
session_a = Session(...)
session_b = Session(...)

await session_a.connect()
await session_b.connect()

await session_a.send("Hello")

await session_b.send("Status?")
```

Each session maintains independent sequencing, capabilities, and transport state.

---

# Example 15 — Reference Architecture

```text
                    Application

                         │

                         ▼

                  IRTP Session API

                         │

                         ▼

                 Capability Manager

                         │

                         ▼

                  Envelope Builder

                         │

                         ▼

                 Transport Interface

          ┌──────────────┼──────────────┐

          │                             │

          ▼                             ▼

  WebSocket Transport          Local Transport

          │                             │

          ▼                             ▼

   Remote AI Provider           Local AI Runtime
```

---

# Example 16 — Philosophy

Traditional integrations often bind applications directly to a provider-specific API.

```text
Application
      │
      ▼
Provider API
```

IRTP introduces an abstraction layer.

```text
Application
      │
      ▼
IRTP
      │
      ▼
Provider Adapter
      │
      ▼
Provider
```

The application depends only on IRTP, enabling transport and provider implementations to evolve independently.

---

# Summary

These examples demonstrate the core design philosophy of IRTP:

* applications communicate with sessions rather than transports
* transports move serialized protocol messages without interpreting them
* provider adapters isolate vendor-specific APIs
* protocol envelopes standardize communication
* capability negotiation enables extensibility
* session management provides a consistent programming model
* transport independence allows the same application to operate across multiple communication mechanisms

By maintaining clear boundaries between application logic, protocol semantics, transport mechanics, and provider-specific behavior, IRTP provides a reusable foundation for interoperable AI communication.

