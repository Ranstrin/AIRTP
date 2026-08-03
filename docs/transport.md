# Updated Transport Layer Specification

**Version:** 0.2 (Aligned with AIRTP.py Reference Implementation)

**Status:** Draft Specification

---

# Abstract

This document updates the AIRTP Transport Layer Specification to reflect the practical details of the single-file AIRTP.py reference implementation. It incorporates the layered architecture defined in the architecture.md document and provides a concrete description of how the AIRTP.py transport layer operates, including its interface, behavior, and integration with the overall AIRTP runtime.

---

# 1. Design Goals

The transport layer in AIRTP.py adheres to the following objectives:

* Transport independence
* Provider independence
* Minimal interface exposed to higher layers
* Explicit connect/send/receive/close lifecycle
* Clear separation of transport and protocol logic
* Seamless handling of streaming deltas from the provider
* Secure communication over TLS

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
Transport Interface (AIRTP.py)
      │
 ┌─────┴──────────────┐
 ▼                    ▼
WebSocketTransport (AIRTP.py)      Future Transports
      │
      ▼
Remote Endpoint or Local AI Runtime
```

In AIRTP.py, the transport layer is implemented by the `WebSocketTransport` class. It provides a concrete realization of the transport responsibilities and maintains an independent lifecycle.

---

# 3. Responsibilities

The transport layer in AIRTP.py is responsible for the following:

* Opening a secure WebSocket connection to the remote provider endpoint (`connect`)
* Sending serialized AIRTP envelopes over the WebSocket (`send`)
* Receiving serialized provider messages (`receive`)
* Detecting connection closures and handling reconnection if needed
* Closing the WebSocket connection cleanly on shutdown (`close`)
* Verifying TLS certificates and enforcing secure communication

The transport layer does not perform:

* Protocol parsing
* Capability negotiation
* Logical message reassembly
* Envelope construction

These responsibilities are handled by the higher layers in the AIRTP stack.

---

# 4. Transport Interface

The transport interface in AIRTP.py follows the same core interface defined in the original specification.

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

In AIRTP.py, this interface is concretely implemented by the `WebSocketTransport` class. It relies on the `websockets` library to manage low-level WebSocket communication, while exposing an asynchronous send/receive API.

---

# 5. Transport Lifecycle

Each transport instance in AIRTP.py follows a predictable lifecycle:

```text
Transport Created
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
        ▼Disconnected
        │
        ▼
Close()
        │
        ▼
Transport Closed
```

This lifecycle is driven by the session and runtime layers, which call the transport’s `connect`, `send`, `receive`, and `close` methods at appropriate times.

---

# 6. Connection State

The transport in AIRTP.py maintains the following implicit connection states:

* DISCONNECTED (before `connect` or after `close`)
* CONNECTED (after successful `connect`)
* FAILED (if the WebSocket connection is lost unexpectedly)

While the implementation does not expose an explicit state machine for connection states, it relies on handling `ConnectionClosed` exceptions to transition to a FAILED state and trigger orderly shutdown.

---

# 7. Transport Independence

Although AIRTP.py currently implements only the WebSocket transport, the interface is designed to allow future transports such as:

* HTTP/2 streaming
* Local UNIX domain sockets
* Named pipes
* Future low-latency transports

All such future transports would implement the same `Transport` interface, preserving the layered architecture described in `architecture.md`.

---

# 8. WebSocket Transport in AIRTP.py

The `WebSocketTransport` class in AIRTP.py includes detailed behavior for WebSocket communication. Responsibilities include:

1. Establishing a secure WebSocket connection using TLS, including default certificate validation.
2. Adding the `Authorization: Bearer <api_key>` header to authenticate with the provider.
3. Sending serialized JSON messages as text frames over the WebSocket (`send` method).
4. Receiving text frames from the WebSocket and returning them as raw JSON strings (`receive` method).
5. Handling `ConnectionClosed` exceptions and returning `None` to signal an unexpected closure.
6. Gracefully closing the WebSocket connection and releasing resources (`close` method).

---

# 9. Local Transport (Future)

AIRTP.py currently does not include a local transport. However, future implementations may introduce local transports using inter-process communication (IPC), for example UNIX domain sockets, allowing communication with local AI runtimes without changing the higher layers of the AIRTP stack.

---

# 10. Authentication

In AIRTP.py, authentication is handled entirely by the transport layer. The `WebSocketTransport` adds the `Authorization` header with the API key. This ensures that provider credentials are never exposed in the protocol payload. The transport layer is responsible for secure credential handling.

---

# 11. Message Flow

The AIRTP.py transport layer moves serialized messages without interpreting them.

```text
AIRTP Envelope
       │
       ▼
json.dumps()
       │
       ▼
WebSocketTransport.send()
       │
       ▼
WebSocket Channel
       │
       ▼
WebSocketTransport.receive()
       │
       ▼
raw JSON
```

The transport does not inspect or modify message content. This ensures a clean separation between protocol semantics and transport mechanics.---

# 12. Reliability

The `WebSocketTransport` in AIRTP.py relies on the inherent reliability of the WebSocket protocol. This includes:

* Ordered delivery: WebSocket messages arrive in the order they are sent.
* Reliable message transmission over TCP.
* Automatic reconnect options (though not yet integrated directly in AIRTP.py).
* TLS encryption ensuring data confidentiality and integrity.

While the transport does not provide explicit retransmission, it leverages the WebSocket layer’s reliability and integrity guarantees.

---

# 13. Error Handling

The transport in AIRTP.py reports communication failures without interpreting protocol semantics. Examples include:

* Connection closed errors (handled as `ConnectionClosed` exceptions).
* TLS or handshake errors (surfaced as exceptions during `connect`).
* Invalid endpoint or network unreachable errors.

The higher layers (runtime and session) are responsible for determining recovery strategies based on these transport-level errors.

---

# 14. Shutdown

Orderly shutdown in AIRTP.py follows a predictable sequence:

```text
Application
      │
      ▼
Session Close
      │
      ▼
Transport.close()
      │
      ▼
WebSocket Closed
      │
      ▼
Resources Released
```

The transport ensures that all resources are cleaned up, even in the case of unexpected failures.

---

# 15. Security Considerations

The transport in AIRTP.py adheres to the security best practices:

* TLS is enabled by default and verifies certificates unless explicitly overridden.
* API keys are never included in message payloads, only in WebSocket headers.
* No sensitive user information is logged by the transport layer.
* Remote endpoint identity is verified through TLS certificate validation.

---

# 16. Extensibility

The AIRTP.py transport implementation can be extended in the future to support:

* Compression (e.g., WebSocket per-message deflate)
* Connection pooling for multiple simultaneous sessions
* Adaptive buffering and congestion control
* Multiplexing multiple logical sessions over a single WebSocket connection

These extensions can be integrated without altering the session or provider adapter layers.

---

# 17. Reference Implementation in AIRTP.py

The `WebSocketTransport` class in AIRTP.py serves as the initial reference implementation of the AIRTP transport layer. It demonstrates the core principles:

* Minimal interface (`connect`, `send`, `receive`, `close`)
* Transport independence from higher protocol layers
* Secure WebSocket communication
* Support for streaming deltas from providers
* Clean lifecycle management and error propagation

---

# 18. Guiding Principle

> The transport layer exists to move bytes—not to understand them.

In AIRTP.py, the `WebSocketTransport` fulfills this principle by focusing solely on reliable, secure message transmission. This separation of responsibilities ensures that the AIRTP protocol remains provider-agnostic and transport-flexible, enabling future extension without affecting session or application code.
:w
