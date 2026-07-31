# AIRTP Protocol Specification

**Version:** 0.1 (Experimental)
**Status:** Draft Specification

---

# Abstract

The Intelligent Realtime Transport Protocol (AIRTP) defines an application-layer protocol for interactive Artificial Intelligence systems.

AIRTP provides a provider-independent communication protocol that separates AI application logic from transport implementation details. The protocol standardizes session establishment, capability negotiation, message framing, chunk management, streaming, and orderly session termination.

The protocol is transport agnostic and may operate over WebSocket, HTTP streaming, local sockets, named pipes, or future transport implementations.

---

# 1. Goals

AIRTP has six primary goals.

1. Transport independence
2. AI provider independence
3. Deterministic message delivery
4. Explicit capability negotiation
5. Structured message framing
6. Extensible protocol evolution

---

# 2. Protocol Model

AIRTP operates as a layered protocol.

```text
Application
      │
      ▼
AIRTP Protocol
      │
      ▼
Transport
      │
      ▼
Remote Endpoint
```

The protocol does not define transport reliability.

Instead, AIRTP assumes the selected transport provides ordered message delivery or exposes ordering information.

---

# 3. Session Model

Every connection is represented as a Session.

A session consists of:

* Session Identifier
* Capability State
* Sequence Counter
* Transport Binding
* Peer Metadata
* Negotiated Parameters

A session begins after successful transport establishment and concludes following orderly shutdown or transport failure.

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
Session Active
        │
        ▼
Streaming Exchange
        │
        ▼
Graceful Close
```

---

# 5. Message Structure

Every protocol exchange consists of one logical message.

Each message contains:

```text
Envelope
    │
    ├── Metadata
    ├── Capabilities
    ├── Sequencing
    └── Payload
```

---

# 6. Envelope Format

Example:

```json
{
  "version": "0.1",
  "session": "session-12345",
  "sequence": 18,
  "timestamp": 1783521188,
  "type": "message",
  "payload": {
      ...
  }
}
```

Required fields:

| Field     | Description               |
| --------- | ------------------------- |
| version   | AIRTP protocol version     |
| session   | Session identifier        |
| sequence  | Monotonic sequence number |
| timestamp | Unix timestamp            |
| type      | Message type              |
| payload   | Application payload       |

---

# 7. Message Types

AIRTP defines logical message categories.

## CONNECT

Requests creation of a new logical session.

Example

```json
{
  "type":"connect"
}
```

---

## CAPABILITY

Advertises supported protocol capabilities.

Example

```json
{
  "type":"capability",
  "capabilities":{
      "streaming":true,
      "chunking":true,
      "compression":false
  }
}
```

---

## MESSAGE

Application payload.

```json
{
    "type":"message",
    "payload":{ ... }
}
```

---

## STREAM

Represents an incremental response.

Example

```json
{
    "type":"stream",
    "sequence":88,
    "chunk":3
}
```

---

## COMPLETE

Indicates logical completion of a streamed message.

---

## ERROR

Represents protocol or application failure.

---

## CLOSE

Requests orderly session termination.

---

# 8. Capability Negotiation

Capability negotiation occurs immediately after transport establishment.

Capabilities describe protocol features rather than provider-specific behavior.

Example

```json
{
    "chunking":true,
    "streaming":true,
    "compression":false,
    "binary":false
}
```

Capabilities may include:

* streaming
* chunking
* binary payloads
* compression
* resumable sessions
* multiplexing
* protocol revision

Unknown capabilities should be ignored unless explicitly required.

---

# 9. Sequencing

Every message contains a monotonically increasing sequence number.

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
* recovery support

Sequence numbers are scoped to a session.

---

# 10. Chunking

Large payloads may be fragmented.

Chunk metadata consists of:

```text
Session
Sequence
Chunk Index
Chunk Count
Payload Size
```

Example

```json
{
    "chunk":{
        "index":2,
        "total":5
    }
}
```

The receiving endpoint performs deterministic reassembly.

Applications never process incomplete logical messages.

---

# 11. Streaming

Streaming is represented as ordered partial payloads.

```text
Chunk 1
Chunk 2
Chunk 3
Chunk 4
Complete
```

The protocol intentionally separates streaming from transport implementation.

---

# 12. Provider Adapters

AIRTP does not define provider-specific semantics.

Instead, provider adapters translate between provider APIs and AIRTP.

Example

```text
OpenAI Realtime
        │
        ▼
 OpenAI Adapter
        │
        ▼
      AIRTP
```

Another provider:

```text
Future Provider
        │
        ▼
 Provider Adapter
        │
        ▼
      AIRTP
```

Applications communicate only with AIRTP.

---

# 13. Error Model

Errors are categorized by layer.

Transport

* timeout
* disconnect
* TLS failure

Protocol

* malformed envelope
* invalid sequence
* unsupported capability

Application

* authorization
* invalid request
* unsupported operation

Provider

* quota exceeded
* provider unavailable
* model unavailable

---

# 14. Transport Independence

AIRTP intentionally avoids assumptions regarding transport.

Supported transports may include:

* WebSocket
* HTTP Streaming
* TCP
* Unix Domain Socket
* Named Pipe
* Shared Memory

Transport adapters expose a common interface.

```text
connect()

send()

receive()

close()
```

Applications remain transport independent.

---

# 15. Session Shutdown

Orderly shutdown follows:

```text
Application

      │

 CLOSE

      │

 Flush Pending Messages

      │

 Transport Close

      │

 Session Destroyed
```

Transport failure may terminate a session immediately.

---

# 16. Protocol Versioning

Every envelope contains a protocol version.

Future protocol revisions should negotiate compatibility during capability exchange.

Example

```json
{
    "version":"0.2"
}
```

Unknown versions may be rejected or negotiated.

---

# 17. Security Considerations

Implementations should:

* authenticate endpoints
* validate envelopes
* validate sequence numbers
* protect credentials
* use encrypted transport
* reject malformed messages

Provider credentials must never appear inside protocol payloads.

---

# 18. Future Extensions

Possible protocol extensions include:

* binary framing
* compression negotiation
* multiplexed logical channels
* distributed routing
* peer discovery
* protocol plugins
* resumable sessions
* congestion signaling
* adaptive chunk sizing
* quality-of-service negotiation

The protocol is intentionally extensible while preserving compatibility with existing implementations.

---

# 19. Reference Implementation

The AIRTP reference implementation demonstrates the protocol using a modular transport architecture with interchangeable provider adapters.

The implementation is intended as a research platform for experimentation, interoperability, and protocol evolution rather than a finalized networking standard.

---

# 20. Guiding Principle

> Applications should communicate with a protocol rather than a provider.

AIRTP treats AI communication as a protocol engineering problem, allowing transport implementations, model providers, and application logic to evolve independently while maintaining a consistent session-oriented communication model.

