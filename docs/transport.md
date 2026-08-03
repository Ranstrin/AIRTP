# AIRTP Transport Layer Specification

**Status:** Draft Specification

---

# Abstract

The AIRTP Transport Layer defines the interface responsible for establishing, maintaining, and terminating communication channels between an AIRTP provider adapter and a remote endpoint.

The transport layer exists solely to move serialized messages between endpoints. It intentionally has no knowledge of AIRTP protocol semantics, application logic, or provider-specific message interpretation.

By isolating transport mechanics from protocol behavior, AIRTP allows applications, providers, and communication technologies to evolve independently.

---

# 1. Design Goals

The AIRTP transport layer is designed around the following objectives.

* Transport independence
* Provider independence
* Pluggable implementations
* Minimal transport assumptions
* Explicit lifecycle management
* Clean separation of responsibilities

---

# 2. Layer Position

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
Transport Interface
      │
 ┌────┴───────────────┐
 ▼                    ▼
WebSocket      Local Transport
Transport
      │
      ▼
Remote Endpoint
```

The transport layer communicates only with the provider adapter.

Applications never interact with transport implementations directly.

---

# 3. Responsibilities

The transport layer is responsible for communication mechanics.

Its responsibilities include:

* opening communication channels
* configuring secure connections
* authenticating with remote endpoints
* sending serialized messages
* receiving serialized messages
* orderly connection shutdown
* reporting transport failures

The transport layer does **not** perform:

* capability negotiation
* protocol parsing
* envelope construction
* logical message assembly
* provider event translation
* application processing

Those responsibilities belong to higher layers.

---

# 4. Transport Interface

Every transport implementation exposes the same public interface.

```python
class Transport:

    async def connect(self):
        ...

    async def send(self, message):
        ...

    async def receive(self):
        ...

    async def close(self):
        ...
```

The Session and Provider Adapter depend only on this interface.

Transport implementations remain interchangeable.

---

# 5. Transport Lifecycle

Every transport follows the same lifecycle.

```text
Transport Created
        │
        ▼
Configuration Loaded
        │
        ▼
Connect()
        │
        ▼
Connected
        │
        ▼
Send / Receive
        │
        ▼
Close()
        │
        ▼
Disconnected
```

The lifecycle remains consistent regardless of the underlying transport technology.

---

# 6. Connection State

Transport implementations should maintain explicit connection state.

Recommended states include:

```text
DISCONNECTED

CONNECTING

CONNECTED

CLOSING

CLOSED

FAILED
```

Explicit state simplifies debugging, recovery, and lifecycle management.

---

# 7. Transport Independence

AIRTP intentionally avoids dependence upon any networking technology.

Possible implementations include:

* WebSocket
* HTTP Streaming
* TCP
* Unix Domain Socket
* Named Pipe
* Local IPC
* Shared Memory
* Future transports

Applications remain unchanged when replacing one transport with another.

---

# 8. WebSocket Transport

The reference implementation currently communicates using secure WebSockets.

Typical responsibilities include:

* establishing TLS connections
* performing the WebSocket handshake
* transmitting serialized protocol messages
* receiving provider messages
* orderly connection shutdown

All WebSocket-specific behavior remains confined to the transport implementation.

---

# 9. Local Transport

AIRTP also supports transports that communicate directly with local runtimes.

Example:

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
Local Transport
      │
      ▼
Local AI Runtime
```

The remainder of the AIRTP architecture remains unchanged.

---

# 10. Authentication

Authentication belongs to the transport layer.

Possible authentication mechanisms include:

* API keys
* OAuth tokens
* Mutual TLS
* Local authentication
* Future authentication methods

Authentication metadata is transmitted during connection establishment and must never be embedded within AIRTP protocol payloads.

---

# 11. Message Flow

The transport layer moves serialized messages without interpreting them.

```text
AIRTP Envelope
       │
       ▼
Serialize
       │
       ▼
Transport.send()
       │
       ▼
Communication Channel
       │
       ▼
Transport.receive()
       │
       ▼
Deserialize
       │
       ▼
AIRTP Envelope
```

Transport implementations do not inspect or modify application payloads.

---

# 12. Reliability

Reliability characteristics are provided by the selected transport implementation.

Typical guarantees may include:

* ordered delivery
* reliable delivery
* encrypted communication
* automatic retransmission
* connection recovery

AIRTP does not require any specific reliability mechanism.

---

# 13. Error Handling

Transport implementations report communication failures without interpreting protocol behavior.

Examples include:

* connection refused
* timeout
* TLS failure
* authentication failure
* network unavailable
* connection reset
* handshake failure

Higher protocol layers determine how recovery should occur.

---

# 14. Shutdown

Orderly shutdown follows a predictable sequence.

```text
Application
      │
      ▼
Session Close
      │
      ▼
Provider Shutdown
      │
      ▼
Transport.close()
      │
      ▼
Flush Pending Data
      │
      ▼
Release Resources
      │
      ▼
Disconnected
```

Transport implementations should release resources even when failures occur.

---

# 15. Security Considerations

Transport implementations should:

* verify remote identities
* validate TLS certificates
* encrypt communication
* protect authentication credentials
* avoid logging sensitive information
* fail securely

Provider credentials, bearer tokens, and authentication material should never appear inside AIRTP protocol payloads.

---

# 16. Extensibility

Future transport implementations may provide:

* compression
* adaptive buffering
* connection pooling
* multiplexing
* protocol upgrades
* transport metrics
* congestion awareness
* distributed routing

These features should remain transparent to applications using the AIRTP Session interface.

---

# 17. Reference Implementation

The AIRTP reference implementation currently includes a WebSocket transport used by provider adapters.

Additional transports can be implemented by conforming to the Transport interface without modifying the Session or Provider Adapter layers.

This separation enables experimentation with new communication technologies while preserving application compatibility.

---

# 18. Guiding Principle

> The transport layer exists to move bytes—not to understand them.

The transport implementation establishes communication, authenticates with remote endpoints, and transfers serialized protocol messages.

Protocol semantics belong to the AIRTP Session.

Provider behavior belongs to the Provider Adapter.

By maintaining these boundaries, AIRTP achieves transport independence, provider independence, and a consistent programming model for AI applications.
