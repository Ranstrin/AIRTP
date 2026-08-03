# AIRTP — AI Realtime Transport Protocol

🌐 **Project Website:** https://www.airtp.com

AIRTP is an experimental, open-source protocol and reference implementation for session-oriented AI communication.

Rather than integrating applications directly with provider-specific APIs, AIRTP introduces a protocol layer that separates application logic from provider implementations and transport mechanics. Applications communicate through a consistent Session interface while AIRTP manages provider adaptation, transport communication, capability negotiation, and logical message exchange.

AIRTP treats AI communication as a protocol engineering problem rather than a provider integration problem.

---

# Why AIRTP?

Modern AI applications increasingly require:

* Persistent conversational sessions
* Streaming responses
* Multiple AI providers
* Local and remote execution
* Transport flexibility
* Consistent programming interfaces

Without an abstraction layer, applications become tightly coupled to provider-specific APIs and networking implementations.

AIRTP introduces a stable protocol boundary that allows applications, providers, and transports to evolve independently.

---

# Architecture

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
                  ┌───────┴────────┐
                  ▼                ▼
          OpenAI Adapter     Future Adapter
                          │
                          ▼
                  Transport Interface
                  ┌───────┴────────┐
                  ▼                ▼
          WebSocket TLS      Local Transport
                          │
                          ▼
                    Remote Endpoint
```

Applications communicate only with the AIRTP Session.

Provider adapters isolate vendor-specific APIs.

Transport implementations isolate communication mechanics.

---

# Design Principles

AIRTP is built around several core principles.

* Session-oriented communication
* Provider independence
* Transport independence
* Explicit capability negotiation
* Deterministic logical messaging
* Extensible protocol evolution
* Clear separation of responsibilities

Each architectural layer has a single, well-defined responsibility.

---

# Example

```python
from AIRTP import Session

session = Session(
    endpoint="wss://provider.example/realtime"
)

await session.connect()

response = await session.send(
    "Explain quantum computing."
)

print(response)

await session.close()
```

Applications never communicate directly with provider APIs or transport implementations.

---

# Session Lifecycle

Every AIRTP session follows the same lifecycle.

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
```

The Session coordinates the complete communication lifecycle.

---

# Key Features

* Session-oriented API
* Provider adapter architecture
* Pluggable transport implementations
* Automatic capability negotiation
* Logical message abstraction
* Streaming support
* Layered protocol architecture
* Extensible design

---

# Documentation

The repository is organized into several companion documents.

| Document            | Description                   |
| ------------------- | ----------------------------- |
| **README.md**       | Project overview              |
| **architecture.md** | Overall system architecture   |
| **protocol.md**     | AIRTP protocol specification  |
| **transport.md**    | Transport layer specification |
| **examples.md**     | Programming examples          |

---

# Project Status

**Version:** 0.1 (Experimental)

AIRTP is an active research project exploring interoperable AI communication through protocol abstraction.

The current implementation serves as a reference architecture for experimentation, refinement, and future protocol evolution rather than a finalized networking standard.

---

# Contributing

Contributions, discussion, and experimentation are encouraged.

Areas of interest include:

* Additional provider adapters
* Alternative transport implementations
* Protocol evolution
* Capability negotiation
* Session management
* Documentation
* Testing and interoperability

---

# Guiding Principle

> **Applications should communicate with a protocol—not with a provider.**

AIRTP separates application logic, protocol behavior, provider integration, and communication mechanics into independent layers.

By maintaining these boundaries, AIRTP enables interoperable AI communication while allowing providers, transports, and protocol implementations to evolve independently.
