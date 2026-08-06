# AIRTP — AIRTP Intelligent Realtime Transport Protocol

🌐 Project Website: https://www.airtp.com

AIRTP is an experimental, open-source protocol and reference implementation for session-oriented AI communication. It separates application logic from provider implementations and transport mechanics by introducing a stable protocol layer.

Applications communicate through a consistent session interface, while AIRTP manages provider adaptation, transport negotiation, capability profiling, and logical message exchange.

AIRTP treats AI communication as a protocol engineering problem rather than a provider integration problem.

---

# Why AIRTP?

Modern AI applications increasingly require:

- Persistent conversational sessions
- Streaming responses
- Multiple AI providers
- Local and remote execution
- Transport flexibility
- Consistent programming interfaces

Without an abstraction layer, applications become tightly coupled to provider-specific APIs and networking implementations.

AIRTP introduces a stable protocol boundary that allows applications, providers, and transports to evolve independently.

---

# Architecture

AIRTP is designed with a layered architecture:

```text
                    Application
                          │
                          ▼
                  AIRTP Session API
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

Each layer communicates only with the layer immediately below it. This separation of responsibilities simplifies error handling, protocol evolution, and introduces flexibility for future extensions.

---

# AIRTP.py — Single-File Implementation

`AIRTP.py` is a single-file implementation that brings together the core concepts and architecture of AIRTP into a concise, runnable example. It demonstrates how the layered design is realized and serves as a reference implementation.

## Key Components in AIRTP.py

1. Session Management (`AIRTPSession`):
   - Manages transport connections and capability negotiation.
   - Constructs message envelopes and initializes the provider adapter.
   - Presents a uniform interface to the application.

2. Provider Adapter (`OpenAIRealtimeAdapter`):
   - Isolates OpenAI-specific behavior.
   - Translates AIRTP logical messages into provider-specific requests.
   - Handles response assembly and continuation requests when the provider stops before completion.

3. Transport Layer (`WebSocketTransport`):
   - Uses WebSocket over TLS for secure communication.
   - Manages connection establishment, authorization headers, and reliable message delivery.
   - Unaware of protocol semantics; focuses solely on message transport.

4. Runtime State Machine (`AIRTPRuntime`):
   - Manages the `ACTIVE` and `COMPLETED` states of a single logical request.
   - Issues continuation requests if provider output stops prematurely.
   - Delivers complete logical artifacts by assembling streaming deltas and detecting the `<END>` marker.

5. Chunking and Envelope Management (`ChunkManager` and `EnvelopeFactory`):
   - Splits large messages into chunks and reassembles them.
   - Constructs protocol-compliant envelopes with metadata such as message IDs and semantic roles.

6. Interactive Shell (`InteractiveShell`):
   - Provides a simple command-line interface for interactive sessions or piped input.
   - Allows users to send text to the session and receive streaming responses in real-time.

---

# Example Usage of AIRTP.py

To use the single-file implementation, place your OpenAI API key in an environment variable or pass it via command line:

```bash
export OPENAI_API_KEY="$(~/.AIRTP_KEYS/provider_key)"
python3 AIRTP.py
```

You can interactively enter requests, such as:

```text
> Explain quantum computing.
```

The response will stream back through standard output, assembling the complete logical artifact.

To run a request from a file or piped input:

```bash
cat <<EOF | python3 AIRTP.py | tee outfile
explain photosynthesis
formatTemplate = {{{ $(cat ./formatTemplate) }}}
format it into a 5 topic essay using the formatTemplate
EOF
```

---

# Execution Flow in AIRTP.py

1. The WebSocket transport establishes a secure connection to the provider endpoint.
2. The OpenAI adapter sends the AIRTP protocol contract and negotiates capabilities.
3. The user input is read (either from interactive prompt or piped input).
4. The runtime splits the input into chunks, wraps it in an envelope, and sends it to the provider.
5. The provider returns streaming deltas, which the runtime writes to standard output.
6. If the provider stops before the logical artifact is complete, the runtime sends continuation requests until the completion marker `<END>` is detected.
7. Once the full response is delivered, the session can shut down gracefully.

---

# Session Lifecycle

AIRTP.py follows the same session lifecycle as described in the architecture:

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

The runtime manages the full lifecycle and ensures consistent behavior across different environments.

---

# Features Demonstrated in AIRTP.py

- Single-file, portable reference implementation
- Session-oriented API
- WebSocket TLS transport
- OpenAI provider adapter
- Automatic capability negotiation via the AIRTP contract
- Logical message chunking and reassembly
- Runtime state machine enforcing logical artifact continuity
- Streaming response assembly
- Clear separation of protocol, transport, and provider concerns

---

# Extensibility and Future Evolution

While `AIRTP.py` focuses on OpenAI as the provider, the architecture supports future extensibility. Additional provider adapters, alternative transports, and evolving protocol features can be integrated by replacing or extending the relevant layers.

The guiding principle remains: Applications communicate with a protocol, not with a provider.

---

# Project Status

**Version:** 0.1 (Experimental)

`AIRTP.py` is part of an active research project exploring interoperable AI communication. The current implementation serves as a reference architecture for experimentation and refinement, not a finalized standard.

---

# Contributing

Contributions to AIRTP and `AIRTP.py` are encouraged.

Areas of interest include:

- Additional provider adapters (e.g., other AI platforms)
- Alternative transport implementations (e.g., HTTP/2, local transports)
- Protocol evolution (e.g., new capability negotiation options)
- Session management improvements
- Testing, documentation, and interoperability experiments

---

# Guiding Principle

> Applications should communicate with a protocol—not with a provider.

AIRTP.py embodies this principle by clearly separating application logic from provider integration and transport mechanics. This design ensures that AI communication remains stable and interoperable, even as providers and technologies evolve.
