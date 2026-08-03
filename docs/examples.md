# AIRTP Examples

**Version:** 0.1 (Experimental)

This document demonstrates how applications interact with the AI Realtime Transport Protocol (AIRTP).

The examples focus on the public AIRTP programming model rather than provider-specific APIs or transport implementations.

---

# Example 1 — Creating a Session

Every AIRTP application begins by creating a session.

```python
from AIRTP import Session

session = Session(
    endpoint="wss://provider.example/realtime"
)
```

A Session represents one logical communication channel.

Applications communicate only with the Session interface.

---

# Example 2 — Connecting

Establish the transport and initialize the provider.

```python
await session.connect()
```

During connection AIRTP automatically:

* establishes the transport
* authenticates the endpoint
* negotiates protocol capabilities
* initializes the provider session

Applications do not perform these steps directly.

---

# Example 3 — Sending a Request

Applications exchange logical messages.

```python
response = await session.send(
    "Explain quantum computing."
)

print(response)
```

The Session hides provider APIs, transport protocols, and protocol framing.

---

# Example 4 — Interactive Console

```python
await session.connect()

try:

    while True:

        prompt = input("> ")

        if prompt.lower() == "exit":
            break

        response = await session.send(prompt)

        print(response)

finally:

    await session.close()
```

The application communicates only through the Session interface.

---

# Example 5 — Streaming

Applications may request streamed responses.

```python
await session.connect()

async for chunk in session.stream(
    "Describe the history of networking."
):

    print(chunk, end="")
```

AIRTP converts provider-specific streaming events into a consistent application interface.

---

# Example 6 — Transport Independence

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

Application logic remains unchanged.

---

# Example 7 — Provider Independence

Applications communicate with AIRTP rather than directly with a provider.

```text
Application
      │
      ▼
AIRTP Session
      │
      ▼
OpenAI Adapter
      │
      ▼
OpenAI Realtime API
```

Replacing the provider:

```text
Application
      │
      ▼
AIRTP Session
      │
      ▼
Local Adapter
      │
      ▼
Local Runtime
```

Only the provider adapter changes.

---

# Example 8 — Session Lifecycle

```text
Session Created
        │
Transport Connected
        │
Capability Negotiation
        │
Provider Initialization
        │
Session Ready
        │
Message Exchange
        │
Session Closed
```

The Session coordinates the complete lifecycle.

---

# Example 9 — Graceful Shutdown

```python
try:

    await session.connect()

    response = await session.send(
        "Hello."
    )

finally:

    await session.close()
```

Graceful shutdown releases transport resources and terminates the provider session cleanly.

---

# Example 10 — Error Handling

```python
try:

    response = await session.send(prompt)

except AIRTPTransportError:

    print("Transport unavailable.")

except AIRTPProtocolError:

    print("Protocol error.")

except AIRTPProviderError:

    print("Provider unavailable.")
```

Separating failures by architectural layer simplifies recovery.

---

# Example 11 — Automatic Capability Negotiation

Applications never negotiate protocol capabilities directly.

```python
await session.connect()
```

Internally AIRTP performs capability negotiation before the session becomes available.

Possible negotiated capabilities include:

* streaming
* chunking
* compression
* protocol version

---

# Example 12 — Logical Message Assembly

Providers may emit many transport events.

```text
Provider

delta

delta

delta

done
```

AIRTP assembles these into one logical response.

```python
response = await session.send(
    "Summarize TCP congestion control."
)

print(response)
```

Applications do not manage provider events.

---

# Example 13 — Multiple Sessions

Applications may maintain multiple concurrent sessions.

```python
session_a = Session(...)
session_b = Session(...)

await session_a.connect()
await session_b.connect()

await session_a.send("Hello")

await session_b.send("Status?")
```

Each Session maintains independent transport, sequencing, and provider state.

---

# Example 14 — Implementing a Custom Transport

New transports implement the Transport interface.

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

No modifications to the Session or Provider Adapter are required.

---

# Example 15 — Implementing a Provider Adapter

Provider adapters translate between AIRTP and provider-specific APIs.

```python
class ProviderAdapter:

    async def initialize(self, transport):
        ...

    async def send_message(self, transport, message):
        ...

    async def receive_message(self, transport):
        ...

    async def close(self, transport):
        ...
```

Replacing a provider requires replacing only the adapter implementation.

---

# Example 16 — Reference Architecture

```text
                    Application
                          │
                          ▼
                    AIRTP Session
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
   Capability Negotiation       Logical Messaging
      Session Lifecycle         Stream Assembly
                          │
                          ▼
                  Provider Adapter
                          │
                          ▼
                  Transport Interface
            ┌─────────────┴─────────────┐
            ▼                           ▼
      WebSocket Transport        Local Transport
                          │
                          ▼
                    Remote Endpoint
```

Applications communicate only with the Session.

---

# Example 17 — Philosophy

Traditional integrations often couple applications directly to provider APIs.

```text
Application
      │
      ▼
Provider API
```

AIRTP introduces a stable protocol layer.

```text
Application
      │
      ▼
AIRTP Session
      │
      ▼
Provider Adapter
      │
      ▼
Transport
      │
      ▼
Provider
```

This separation allows providers, transports, and protocol implementations to evolve independently.

---

# Summary

These examples demonstrate the core AIRTP programming model.

* Applications communicate only with Sessions.
* Sessions manage the complete communication lifecycle.
* Provider adapters isolate vendor-specific APIs.
* Transports provide communication without interpreting protocol semantics.
* Capability negotiation occurs automatically.
* Logical messages are presented independently of transport events.
* Streaming is exposed through a consistent interface.
* Providers and transports may be replaced without changing application code.

By maintaining clear boundaries between application logic, protocol behavior, provider integration, and communication mechanics, AIRTP provides a reusable foundation for interoperable AI communication.
