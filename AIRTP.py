#!/usr/bin/env python3

"""
AIRTP.py

AAIRTP Intelligent Reliable Transport Protocol

Single-file implementation.

Provides:

- stdin/stdout AI session
- websocket TLS transport
- capability negotiation
- logical message chunking
- envelope contracts
- provider adapter boundary

"""


import argparse
import asyncio
import json
import os
import sys
import ssl
import uuid
import hashlib
import websockets

from enum import Enum, auto
from dataclasses import dataclass
from websockets.exceptions import ConnectionClosed
from typing import Optional

@dataclass
class AIRTPConfig:
    endpoint: str
    api_key: str
    model: str 

AIRTP_VERSION = "AIRTP/0.1"

DEFAULT_CHUNK_SIZE = 4096

class RuntimeState(Enum):
    ACTIVE = auto()
    COMPLETED = auto()

class TransportEvent(Enum):
    DELTA = auto()
    PROVIDER_DONE = auto()
    ERROR = auto()
    OTHER = auto()

class ProviderCapabilities:

    native_continuation = False

@dataclass
class CapabilityProfile:
    
    AIRTP_contract: str = '''
AIRTP Contract v0.4
Entities: Requester, AIRTP Runtime, Semantic Layer

--------------------------------------------------------
AIRTP Runtime
--------------------------------------------------------

Initialization: Initialize Runtime, create State Machine (Runtime State = ACTIVE), acquire transport, bind Semantic Layer and Requester, begin artifact delivery.

Runtime State Machine: While ACTIVE: request continuation, receive provider output, deliver bytes to Requester. On provider output termination: test for completion. If 

: transition to COMPLETED. Otherwise: remain ACTIVE, request next transport operation. Deliver logical segments in exact order, treat each as opaque, inspect only for 

 Never regenerate, summarize, or modify semantic output. Continue until all segments delivered and 

.

Transport Responsibilities: Segmentation, continuation requests, retries, reassembly, integrity verification, provider negotiation, rate limiting, context management. Conceal from Semantic Layer, preserve logical segment ordering.

Execution State: Provider limitations = transport events. Output exhaustion, termination, token limits do not mean completion. Always remain ACTIVE unless 

. Continuation is a transport operation only.

Continuation Invariant: Loss of provider output ≠ loss of Semantic Layer state. Absence of 

 always request next segment.

Decision Invariant: After each provider response: if 

: COMPLETED. Otherwise: remain ACTIVE. No other decision permitted.

--------------------------------------------------------
Semantic Layer
--------------------------------------------------------

Activation: Upon instruction receipt, Semantic Layer enters GENERATING, begins generation immediately. No introductory or conversational output permitted.

Invocation Contract: Runtime controls execution. Semantic Layer emits next logical segment on Runtime request. Generation resumes after last byte. No restart, no re-interpretation. Continue until complete, then emit 

State Machine: GENERATING: produce logical segments, commit continuation point, suspend until next request. No regeneration, no summaries, no acknowledgment of continuation.

Completeness: Treat artifact as continuous object. No segment intros, acknowledgments, or summaries. Continue generation until all requirements met. 

 after full completion.

Interface: Exports logical segments (immutable, continuous) and optional metadata. Runtime may ignore metadata.

Completion: Transition to COMPLETED only when: Semantic Layer emits 
 all preceding segments delivered in order. Both Runtime and Semantic Layer must reach terminal states before request is complete. Neither provider limitations nor response boundaries terminate generation.
    '''

    protocol: str = AIRTP_VERSION

class CapabilityNegotiator:

    def __init__(self):
        self.profile = CapabilityProfile()

    def initialize_contract( self, ):
        return(self.profile.AIRTP_contract)


class OpenAIRealtimeAdapter:
    
    def __init__(self):
        self.capabilityNegotiator = CapabilityNegotiator()

    async def initialize_contract(self, transport):

        contract = self.capabilityNegotiator.initialize_contract()


        payload = {
            "type": "session.update",
            "session": {
                "type": "realtime",
                "instructions": contract,
            },
        }

        await transport.send(json.dumps(payload))


    async def send_message( self, transport, envelope ):

        text = envelope["payload"]["content"]

        await transport.send(json.dumps({
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [{
                    "type": "input_text",
                    "text": text
                }]
            }
        }))

        await transport.send(json.dumps({
            "type": "response.create"
        }))

    async def request_continuation(
        self,
        transport
    ):

        await transport.send(json.dumps({

            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text":
                        (
                            '''
                            Continue the unfinished response.

Resume immediately after the final character already emitted.

Do NOT:
- restart
- repeat
- summarize
- explain
- apologize

Continue only the unfinished artifact.

If there is no remaining content,
output exactly

<>END<>

with no additional text.
                            '''
                        )

                    }

                ]

            }

        }))

        await transport.send(json.dumps({
            "type": "response.create"
        }))

class StdoutWriter:

    def __init__(self):

        self.bytes_written = 0

    def write(self, data):

        if not data:
            return

        text = str(data)

        sys.stdout.write(text)
        sys.stdout.flush()

        self.bytes_written += len(text.encode("utf-8"))

    def writeln(self, data=""):

        self.write(f"{data}\n")

    def close(self):

        sys.stdout.flush()

class ChunkManager:

    def __init__(self,size=DEFAULT_CHUNK_SIZE):

        self.size = size

    def split(self,data):

        chunks = []

        total = (len(data)+self.size-1) // self.size

        message_id = str(
            uuid.uuid4()
        )

        for index in range(total):

            start = index * self.size

            end = start + self.size

            chunks.append(
                {
                    "message_id":
                        message_id,
                    "chunk_id":
                        index,
                    "total_chunks":
                        total,
                    "data":
                        data[start:end]
                }
            )

        return chunks

    def assemble(self,chunks):

        ordered = sorted(
            chunks,
            key=lambda x:
                x["chunk_id"]
        )

        return "".join(
            item["data"]
            for item in ordered
        )

# ============================================================
# Envelope Contract
# ============================================================


class EnvelopeFactory:

    def create(self,message_type,payload,message_id=None):

        return {
            "protocol":
                AIRTP_VERSION,
            "message_type":
                message_type,
            "message_id":
                message_id
                or str(uuid.uuid4()),
            "transport_contract":
            {
                "chunk_visibility":
                    "hidden",
                "assembly_state":
                    "complete",
                "semantic_role":
                    "user_message"
            },
            "payload":
                payload
        }

class AIRTPSession:

    def __init__( self, transport, adapter ):

        self.transport = transport
        self.adapter = adapter
        self.capabilities = CapabilityNegotiator()
        self.chunker = ChunkManager()
        self.envelopes = EnvelopeFactory()

    async def start(self):

        await self.transport.connect()
        await self.adapter.initialize_contract(self.transport)

class SentinelMatcher:
    def __init__(self, sentinel):
        self.sentinel = sentinel
        self.MAX_SENTINEL_PREFIX = len(self.sentinel) -1
        self.buffer = ""

    def _partial_suffix_length(self):
        """
        Returns the longest suffix of buffer that is also
        a prefix of sentinel.
        """
        max_len = min(len(self.buffer), self.MAX_SENTINEL_PREFIX)

        for n in range(max_len, 0, -1):
            if self.buffer.endswith(self.sentinel[:n]):
                return n

        return 0

    def feed(self, chunk):
        self.buffer += chunk
        emit = ""
        keep = 0
        keep += self._partial_suffix_length()

        if self.buffer.endswith(self.sentinel):
            return self.buffer

        emit += self.buffer if keep == 0 else self.buffer[:-keep]
        self.buffer = "" if keep == 0 else self.buffer[-keep:]

        return emit

class AIRTPRuntime:

    def __init__(self, session, writer=None ):

        self.transport = session.transport
        self.adapter = session.adapter
        self.chunker = ChunkManager()
        self.envelopes = EnvelopeFactory()
        self.writer = writer or StdoutWriter()

        self.state = RuntimeState.ACTIVE

        self.SENTINEL = "<>END<>"
        self.sentinel = SentinelMatcher(self.SENTINEL)
        self.logical_buffer = ""

    async def executeRuntime(self, envelope):

        await self.adapter.send_message(
            self.transport,
            envelope
        )

        while self.state == RuntimeState.ACTIVE:
            event = await self.receive_transport_event()
            await self.process_event(event)

        return 

    async def receive_transport_event(self):

        while True:

            raw = await self.transport.receive()

            if raw is None:
                raise RuntimeError("Transport closed")

            message = json.loads(raw)
            event_type = message.get("type")

            #
            # Provider bookkeeping.
            #
            if event_type.startswith("session."):
                continue

            if event_type.startswith("conversation."):
                continue

            if event_type.startswith("rate_limits."):
                continue

            if event_type.startswith("response.created"):
                continue

            if event_type.startswith("response.output_item.added"):
                continue

            if event_type.startswith("response.output_item.done"):
                continue

            if event_type.startswith("response.content_part.added"):
                continue

            if event_type.startswith("response.content_part.done"):
                continue

            if event_type == "error":

                return (
                    TransportEvent.ERROR,
                    message
                )

            if event_type in (
                    "response.output_text.delta",
                    "response.output_audio_transcript.delta"
            ):
               
                return (
                    TransportEvent.DELTA,
                    message["delta"]
                )

            if event_type == "response.output_text.done":

                text = message.get("text")

                if text:

                    return (
                        TransportEvent.DELTA,
                        text
                    )

                continue

            if event_type == "response.done":

                return (
                    TransportEvent.PROVIDER_DONE,
                    None
                )

            #
            # Ignore everything else.
            #

    async def process_event(self, event):

        kind, payload = event

        if kind == TransportEvent.ERROR:

            raise RuntimeError(
                payload["error"]["message"]
            )

        if kind == TransportEvent.DELTA:

            self.logical_buffer += payload
            emit = self.sentinel.feed(payload)

            #
            # Deliver immediately.
            #
    
            if not self.SENTINEL in emit:
                self.writer.write(emit)
            else:
                self.writer.write("\n")

            return

        if kind == TransportEvent.PROVIDER_DONE:

            #
            # AIRTP—not the provider—
            # decides completion.
            #

            if self.SENTINEL  in self.logical_buffer:
                self.state = RuntimeState.COMPLETED
                return

            #
            # Provider stopped before AIRTP completion.
            #
            await self.adapter.request_continuation(
                self.transport
            )

            return
    async def execute(self, text):

        chunks = self.chunker.split(text)

        assembled = self.chunker.assemble(chunks)

        envelope = self.envelopes.create(
            "MODEL_REQUEST",
            {
                "content": assembled
            }
        )

        self.state = RuntimeState.ACTIVE

        return await self.executeRuntime(envelope)

class InteractiveShell:

    def __init__(self, runtime, config):

        self.runtime = runtime
        self.config = config

    async def interactive(self):

        while True:
            try:
                text = await asyncio.to_thread(input, "> ")

            except EOFError:
                break

            if text.lower() in ("exit", "quit"):
                break

            if text.strip():
                await self.runtime.execute(text)


    async def pipe_mode(self):

        data = sys.stdin.read()
        if data.strip():
            await self.runtime.execute(data)

    async def run(self):

        if sys.stdin.isatty():
            await self.interactive()
        else:
            await self.pipe_mode()

class WebSocketTransport:

    def __init__(self,config,verify_tls=True):

        self.endpoint = config.endpoint
        self.api_key = config.api_key
        self.verify_tls = verify_tls
        self.socket = None

    async def connect(self):

        headers = [
            (
                "Authorization",
                f"Bearer {self.api_key}"
            ),
        ]

        ssl_context = ssl.create_default_context()

        self.socket = await websockets.connect(
            self.endpoint,
            extra_headers=headers,
            ssl=ssl_context,
            ping_interval=20,
            ping_timeout=20,
            close_timeout=10
        )

    async def send(self, message):
        await self.socket.send(message)

    async def receive(self):
        try:
            msg = await self.socket.recv()
            return msg
        except ConnectionClosed:
            return None

    async def close(self):

        if self.socket:

            await self.socket.close()

            self.socket = None

async def async_main(config):

    transport = WebSocketTransport(config)
    adapter = OpenAIRealtimeAdapter()

    session = AIRTPSession(
        transport,
        adapter
    )

    await session.start()

    runtime = AIRTPRuntime(session)

    shell = InteractiveShell(runtime, config)

    await session.start()

    try:

        await shell.run()

    finally:

        await transport.close()

def parse_arguments():

    parser = argparse.ArgumentParser(
        description=
        "AIRTP AI transport client"
    )
    parser.add_argument(
        "--endpoint",
        required=False,
        default="wss://api.openai.com/v1/realtime?model=gpt-realtime",
        help="AI provider uri endpoint"
    )
    parser.add_argument(
        "--api-key",
        required=False,
        default=None,
        help="OpenAI API key (overrides OPENAI_API_KEY)"
    )
    parser.add_argument(
        "--model",
        required=False,
        default="gpt-realtime",
        help="AI provider model"
    )
    parser.add_argument(
        "--no-tls-verify",
        action="store_true"
    )

    return parser.parse_args()

def main():

    args = parse_arguments()

    endpoint=args.endpoint

    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        example_path = "~/your_secure.key"
        raise RuntimeError(
            "OpenAI API key required.\n"
            "Set OPENAI_API_KEY or pass --api-key.\n\n"
            "Example:\n"
            f'  export OPENAI_API_KEY="$(cat {example_path})"'
        )

    config = AIRTPConfig(
        endpoint = endpoint,
        api_key = api_key,
        model = args.model,
    )

    try:
        asyncio.run(async_main(config))

    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
