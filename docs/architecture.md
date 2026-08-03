# AIRTP Architecture

**Version:** 0.1 (Experimental)

---

# Overview

The AI Realtime Transport Protocol (AIRTP) is a session-oriented communication layer that separates AI applications from provider-specific APIs and transport implementations.

Rather than allowing applications to communicate directly with a provider, AIRTP introduces a stable protocol layer responsible for managing session state, capability negotiation, message framing, logical message assembly, and provider adaptation.

This separation allows applications to communicate through a consistent interface while providers, transports, and protocol implementations evolve independently.

---

# Design Philosophy

AIRTP is built around one guiding principle:

> Applications should communicate with a protocol—not with a provider.

An AIRTP application exchanges logical requests and responses with a session. The session coordinates protocol behavior while delegating provider-specific behavior and network communication to interchangeable components.

The result is a layered architecture with clear boundaries between responsibilities.

---

# Layered Architecture

```text
                    Application
                          │
                          ▼
                  AIRTP Session API
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
 Capability Negotiation           Logical Message Flow
 Envelope Construction            Stream Reassembly
 Session State                    Error Translation
                          │
                          ▼
                  Provider Adapter
                          │
        ┌─────────────────┴─────────────────┐
        ▼                                   ▼
 OpenAI Realtime Adapter           Future Provider Adapter
                          │
                          ▼
                  Transport Interface
                          │
        ┌─────────────────┴─────────────────┐
        ▼                                   ▼
 WebSocket Transport               Local Transport
                          │
                          ▼
                    Remote Endpoint
```

Each layer communicates only with the layer immediately below it.

---

# Core Components

## Session

The Session is the primary interface presented to applications.

Applications never communicate directly with transports or provider APIs.

The session is responsible for:

* session lifecycle management
* capability negotiation
* logical message sequencing
* envelope construction
* message dispatch
* stream assembly
* graceful shutdown

From the application's perspective, a session behaves as a single logical communication channel.

---

## Provider Adapter

Provider adapters isolate vendor-specific behavior.

Responsibilities include:

* provider authentication
* provider session initialization
* request serialization
* provider event translation
* response assembly
* provider shutdown

The adapter converts AIRTP logical messages into provider-specific requests and converts provider events back into AIRTP logical responses.

Replacing a provider requires replacing only the adapter.

---

## Transport

The transport layer moves serialized protocol messages between AIRTP and a remote endpoint.

The transport is responsible for:

* establishing connections
* authentication headers
* TLS configuration
* sending serialized messages
* receiving serialized messages
* orderly shutdown

The transport intentionally does not understand AIRTP protocol semantics.

---

# Logical Message Flow

Applications exchange complete logical messages rather than transport events.

```text
Application

      │

session.send()

      │

AIRTP Session

      │

Provider Adapter

      │

Transport

      │

Remote Provider
```

Responses follow the reverse path.

If the provider streams multiple transport messages, AIRTP assembles them internally before returning a complete logical response unless the application explicitly requests streaming.

---

# Streaming

AIRTP separates logical streaming from transport streaming.

```text
Provider Events

      │

delta

delta

delta

done

      │

AIRTP Stream Assembly

      │

Logical Response
```

Applications never manage transport fragmentation.

The session determines whether a provider supports streaming and exposes a consistent programming model regardless of provider implementation.

---

# Capability Negotiation

After the transport connection has been established, AIRTP negotiates protocol capabilities with the remote endpoint.

Capabilities may include:

* streaming
* chunking
* compression
* binary payload support
* protocol revision
* future extensions

Negotiation is performed automatically by the session manager.

Applications typically do not interact with capability negotiation directly.

---

# Message Lifecycle

A typical AIRTP request follows this sequence.

```text
Application

      │

Create Request

      │

Envelope Construction

      │

Provider Translation

      │

Transport Send

      │

Remote Provider

      │

Provider Events

      │

AIRTP Reassembly

      │

Logical Response

      │

Application
```

Transport details remain hidden from the application.

---

# Session Lifecycle

Every AIRTP session progresses through the same high-level states.

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

Graceful Shutdown

        │

Transport Closed
```

Each stage has clearly defined responsibilities, simplifying error handling and future protocol evolution.

---

# Error Model

AIRTP classifies failures according to architectural layer.

**Transport**

* connection failures
* TLS errors
* authentication failures
* network interruption

**Protocol**

* malformed envelopes
* unsupported capabilities
* sequencing violations

**Provider**

* invalid requests
* provider-specific errors
* model unavailable
* quota exceeded

Applications may recover differently depending on which layer generated the error.

---

# Extensibility

AIRTP is designed to evolve without changing application code.

Future protocol features may include:

* multiplexed sessions
* resumable streams
* adaptive chunk sizing
* compression negotiation
* binary framing
* distributed routing
* protocol plugins

These features can be introduced through capability negotiation while preserving compatibility with existing applications.

---

# Security

Security responsibilities are divided by layer.

The transport layer manages:

* TLS
* endpoint authentication
* credential transmission

The protocol layer manages:

* envelope validation
* sequencing
* capability validation

Provider credentials remain transport metadata and are never embedded inside AIRTP protocol messages.

---

# Guiding Principle

AIRTP treats AI communication as a protocol engineering problem rather than a provider integration problem.

Applications depend only on the AIRTP session interface.

Provider adapters isolate vendor-specific APIs.

Transport implementations isolate networking details.

By maintaining these boundaries, AIRTP enables interoperable AI communication while allowing transports, providers, and protocol implementations to evolve independently.
