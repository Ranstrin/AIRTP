# AIRTP.py Examples

**Version:** 0.2

This document expands upon the original AIRTP examples by incorporating the single-file reference implementation described in the architecture guide. It demonstrates how AIRTP.py unifies the core AIRTP architecture layers into a single, concise implementation, allowing developers to use it directly for AI communication without needing to modify provider-specific logic.

## Example 1 — Running the AIRTP.py Session

AIRTP.py provides a self-contained executable session. After installation and configuration, it can be invoked directly from the command line.

```bash
export OPENAI_API_KEY="$(~/.AIRTP_KEYS/provider_key)"
python3 AIRTP.py
```

This will open an interactive console where the user can enter prompts and receive AI-generated responses. The session automatically handles transport, provider interactions, and protocol compliance.

## Example 2 — Executing an Inline Command

AIRTP.py can also execute commands piped into its standard input.

```bash
cat <<EOF | python3 AIRTP.py | tee outfile
Explain quantum entanglement
formatTemplate = {{{ $(cat ./formatTemplate) }}}
format it into a 5 topic essay using the formatTemplate
EOF
```

The output will be streamed back to the terminal as soon as it arrives from the provider, maintaining a continuous logical artifact.

## Example 3 — Connecting and Capability Negotiation

When AIRTP.py starts, it automatically establishes a WebSocket connection, sends the AIRTP protocol contract to the provider, and negotiates capabilities. This happens transparently to the user. No manual negotiation is required.

## Example 4 — Sending a Request with Logical Assembly

The AIRTP runtime in AIRTP.py automatically assembles all provider streaming events into a single logical response:

```bash
$ python3 AIRTP.py
> Describe how neural networks function.
```

AIRTP.py will continue requesting continuation segments from the provider until it receives the `<END>` marker, ensuring the response is complete.

## Example 5 — Streaming Output to Standard Output

The runtime streams each logical segment received from the provider directly to standard output. This default behavior allows users to see partial results in real time, even before the full response is complete.

## Example 6 — Graceful Shutdown

When the user exits the interactive shell (e.g., typing `exit` or pressing Ctrl+D), AIRTP.py closes the WebSocket transport cleanly. This ensures a graceful shutdown and releases all resources properly.

## Example 7 — Error Handling in AIRTP.py

AIRTP.py manages errors according to the underlying transport or provider layer. For example, a transport failure like a network disconnect will raise a runtime error, and a provider-specific error will also be surfaced. This allows applications based on AIRTP.py to handle errors cleanly in a consistent manner.

## Example 8 — Logical Continuation and Completion

AIRTP.py adheres to the protocol’s continuation
