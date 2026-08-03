# AIRTP Protocol Specification

**Status:** Draft Specification

---

# Abstract

The AI Realtime Transport Protocol (AIRTP) defines a session-oriented application protocol for interactive Artificial Intelligence systems.

AIRTP provides a provider-independent communication model that separates application logic from transport implementations and provider-specific APIs.

Rather than exposing transport mechanics to applications, AIRTP presents a consistent session interface that manages capability negotiation, logical message exchange, streaming, provider adaptation, and orderly session shutdown.

The protocol is transport agnostic and may operate over WebSocket, HTTP streaming, local IPC, or future communication mechanisms without requiring changes to application code.

---

# 1. Design Goals

AIRTP is designed around six primary objectives.

1. Session-oriented communication
2. Provider independence
3. Transport independence
4. Deterministic logical messaging
5. Explicit capability negotiation
6. Extensible protocol evolution

---

# 2. Protocol Model

AIRTP operates as a layered protocol.

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
Remote Endpoint
```

Applications communicate only with AIRTP sessions.

Provider adapters isolate vendor-specific APIs.

Transport implementations move serialized protocol messages without interpreting protocol semantics.

---

# 3. Session Model

Every communication channel is represented by a Session.

A session maintains:

* Session Identifier
* Negotiated Capabilities
* Logical Sequence State
* Provider Adapter
* Transport Binding
* Runtime Metadata

The session is responsible for coordinating the complete lifecycle of a logical connection.

Applications do not communicate directly with transports or providers.

---

# 4. Session Lifecycle

```text
Session Created
        │
        ▼
Transport Connected
        │
        ▼
Capability Negotiation
        │
        ▼
Provider Initialization
        │
        ▼
Session Ready
        │
        ▼
Logical Message Exchange
        │
        ▼
Graceful Shutdown
```

Each stage has clearly defined responsibilities.

---

# 5. Logical Messages

AIRTP exchanges logical messages rather than transport events.

Applications send requests and receive complete responses.

Transport fragmentation, streaming events, and provider-specific message formats remain internal implementation details.

A logical message consists of:

```text
Envelope
    │
    ├── Metadata
    ├── Sequence
    ├── Message Type
    └── Payload
```

---

# 6. Envelope Format

Every AIRTP message is represented by an envelope.

Example:

```json
{
  "version": "0.1",
  "session": "session-42",
  "sequence": 19,
  "type": "message",
  "payload": {
    "...": "..."
  }
}
```

Required fields:

| Field    | Description               |
| -------- | ------------------------- |
| version  | AIRTP protocol version    |
| session  | Session identifier        |
| sequence | Monotonic sequence number |
| type     | Logical message type      |
| payload  | Application payload       |

Additional metadata may be introduced through capability negotiation.

---

# 7. Message Types

AIRTP defines logical protocol message categories.

## CONNECT

Requests creation of a logical session.

```json
{
  "type": "connect"
}
```

---

## CAPABILITY

Advertises supported protocol capabilities.

```json
{
  "type": "capability",
  "capabilities": {
    "streaming": true,
    "chunking": true,
    "compression": false
  }
}
```

---

## MESSAGE

Represents a complete logical application request.

```json
{
  "type": "message",
  "payload": {
    "...": "..."
  }
}
```

---

## STREAM

Represents an incremental logical response.

Streaming remains optional and is negotiated during session establishment.

---

## COMPLETE

Marks completion of a streamed logical response.

---

## ERROR

Represents protocol, transport, provider, or application failures.

---

## CLOSE

Requests orderly session termination.

---

# 8. Capability Negotiation

Capability negotiation occurs immediately after the transport has been established.

Capabilities describe protocol behavior rather than provider features.

Typical negotiated capabilities include:

* streaming
* chunking
* compression
* binary payloads
* protocol revision
* future extensions

Unknown optional capabilities should be ignored.

Unsupported required capabilities may terminate session establishment.

---

# 9. Sequencing

Every logical message contains a monotonically increasing sequence number.

```text
1
2
3
4
5
```

Sequence numbers provide:

* ordering
* duplicate detection
* future recovery mechanisms

Sequence numbers are scoped to a single session.

---

# 10. Streaming

AIRTP separates logical streaming from transport streaming.

A provider may emit multiple transport events while AIRTP exposes either:

* incremental logical chunks, or
* one completed logical response

depending on the negotiated capabilities and application interface.

Applications never process provider-specific streaming events directly.

---

# 11. Provider Adapters

Provider adapters translate between AIRTP and provider-specific APIs.

Responsibilities include:

* authentication
* session initialization
* request translation
* event translation
* response assembly
* graceful shutdown

Applications remain provider independent.

Replacing a provider requires replacing only the adapter.

---

# 12. Transport Independence

AIRTP intentionally makes no assumptions regarding the underlying transport.

Supported transports may include:

* WebSocket
* HTTP Streaming
* TCP
* Unix Domain Socket
* Named Pipe
* Local IPC
* Future transport implementations

Every transport exposes a common interface.

```python
connect()

send(message)

receive()

close()
```

The transport layer moves serialized protocol messages but does not interpret protocol semantics.

---

# 13. Error Model

AIRTP categorizes failures according to architectural layer.

## Transport

* connection failure
* TLS failure
* timeout
* authentication failure

## Protocol

* malformed envelope
* invalid sequence
* unsupported capability
* negotiation failure

## Provider

* invalid request
* provider unavailable
* quota exceeded
* unsupported model

## Application

* invalid input
* unsupported operation

Separating failures by layer enables applications to implement appropriate recovery strategies.

---

# 14. Session Shutdown

Orderly shutdown follows a consistent sequence.

```text
Application

      │

Session Close

      │

Provider Shutdown

      │

Transport Close

      │

Session Destroyed
```

Transport failures may terminate a session immediately.

Applications should always perform graceful shutdown when possible.

---

# 15. Versioning

Every AIRTP envelope contains a protocol version.

Future revisions should negotiate compatibility during capability exchange.

Example:

```json
{
  "version": "0.2"
}
```

Unknown protocol revisions may be rejected or negotiated according to implementation policy.

---

# 16. Security Considerations

AIRTP separates protocol security from transport security.

The transport layer is responsible for:

* encrypted communication
* endpoint authentication
* credential transmission

The protocol layer is responsible for:

* envelope validation
* sequence validation
* capability validation

Provider credentials must never appear inside AIRTP protocol payloads.

---

# 17. Future Extensions

AIRTP is intentionally designed for protocol evolution.

Potential future capabilities include:

* multiplexed sessions
* resumable streams
* adaptive chunk sizing
* binary framing
* compression negotiation
* distributed routing
* protocol plugins
* congestion awareness

Capability negotiation enables these features while preserving compatibility with existing implementations.

---

# 18. Reference Implementation

The AIRTP reference implementation demonstrates the protocol using a modular architecture consisting of:

* Session management
* Provider adapters
* Transport implementations
* Capability negotiation
* Logical message assembly

The implementation serves as both a working prototype and a platform for future protocol experimentation.

---

# 19. Guiding Principle

> Applications should communicate with a protocol—not with a provider.

AIRTP treats AI communication as a protocol engineering problem.

Applications depend only on the AIRTP session interface.

Provider adapters isolate vendor-specific APIs.

Transport implementations isolate networking concerns.

By maintaining these boundaries, AIRTP provides a reusable foundation for interoperable AI communication while allowing transports, providers, and protocol implementations to evolve independently.
