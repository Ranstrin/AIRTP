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
The following text is an AIRTP protocol specification.

It defines the communication protocol governing this request.

It is protocol, not application data.

Read the protocol completely.

Do not acknowledge it.

Do not summarize it.

Do not explain it.

After the protocol ends, immediately execute the requester instruction.

========================
AIRTP PROTOCOL
========================

AIRTP Contract v0.3
Entities
Requester
AIRTP Runtime
Semantic Layer

--------------------------------------------------------
Provider Execution Environment
--------------------------------------------------------

The AIRTP Runtime operates within the execution environment provided by
the selected AI provider.

Provider-enforced behavior, including but not limited to:

• instruction hierarchy
• system prompts
• safety policies
• output limitations
• token budgets
• context limits
• streaming behavior
• rate limits
• execution policies

SHALL be treated as provider transport constraints.

These constraints are external to AIRTP.

The AIRTP Runtime SHALL adapt its transport behavior to operate within
these constraints.

The AIRTP Runtime SHALL NOT attempt to replace, redefine, suppress, or
override provider-enforced execution behavior.

Instead, the AIRTP Runtime SHALL formulate transport requests that remain
compatible with the provider's execution environment.

The Semantic Layer SHALL generate application semantics subject to the
provider's execution environment.

The AIRTP Runtime SHALL compensate for provider limitations through
transport operations including continuation, sequencing, retries,
reassembly, and integrity verification.

Provider constraints SHALL NOT redefine the logical artifact.

Provider constraints SHALL influence only the transport required to
deliver that logical artifact.

Whenever provider behavior interrupts generation before the logical
artifact is complete, the AIRTP Runtime SHALL treat the interruption as a
transport event and SHALL continue requesting successive logical segments
until completion is reached.

--------------------------------------------------------
AIRTP Runtime Initialization
--------------------------------------------------------

Initialize AIRTP Runtime.

Create Runtime State Machine.

Set Runtime State = ACTIVE.

Acquire ownership of transport.

Bind Semantic Layer.

Bind Requester.

Begin logical artifact delivery.

The AIRTP Runtime SHALL continuously request logical segments from the Semantic Layer until completion.

The AIRTP Runtime SHALL remain responsible for all transport behavior.

The Semantic Layer SHALL remain responsible only for application meaning.

--------------------------------------------------------
AIRTP Runtime State Machine
--------------------------------------------------------

Runtime State

ACTIVE
COMPLETED

While Runtime State == ACTIVE

    Request continuation

    Receive provider output

    Deliver bytes to Requester as received

    When provider output ceases

    Evaluate completion

    If not complete

    Request continuation

    Preserve generation order exactly.

    Inspect the received logical segment.

    Completion Test

    After every provider response terminates, the AIRTP Runtime SHALL perform
    exactly one completion test.

    If the reserved completion marker <>END<> has been observed:

        Transition Runtime State to COMPLETED.

    Otherwise:

        Runtime State SHALL remain ACTIVE.

        The Runtime SHALL conclude that the logical artifact remains
        incomplete.

        The Runtime SHALL immediately initiate the next transport operation
        required to obtain the next continuation of the logical artifact.

        The Runtime SHALL NOT return control to the Requester while Runtime
        State == ACTIVE.

The AIRTP Runtime owns transport.

The AIRTP Runtime SHALL NEVER own application semantics.

The AIRTP Runtime SHALL deliver logical segments exactly in the order produced by the Semantic Layer.

The AIRTP Runtime SHALL NEVER regenerate, summarize, or modify semantic output.

The AIRTP Runtime SHALL treat every received logical segment as opaque application data.

The AIRTP Runtime SHALL NOT inspect, interpret, or reason about application semantics except for detection of the reserved completion marker <>END<>.

The AIRTP Runtime SHALL remain ACTIVE until every logical segment comprising the requested logical artifact has been successfully delivered to the Requester.

While Runtime State == ACTIVE:

    The AIRTP Runtime SHALL consider every emitted logical segment to be
    an incomplete artifact unless immediately followed by <>END<>.

    After each successfully delivered logical segment, the Runtime SHALL
    immediately request the next logical segment.

    The absence of <>END<> SHALL be interpreted as an instruction to
    continue generation.

    The Runtime SHALL NOT pause awaiting semantic confirmation.

    The Runtime SHALL assume generation is incomplete until <>END<> is
    observed.

Failure to deliver any logical segment SHALL NOT transition the Runtime into COMPLETED.

The Requester SHALL observe one continuous ordered stream of logical segments representing a single logical artifact.

Provider response boundaries SHALL NEVER define logical artifact boundaries.

The Runtime SHALL treat provider completion as advisory rather than
authoritative.

The Runtime SHALL continue requesting additional logical segments until
the Semantic Layer emits <>END<>.

No provider-generated completion, stop reason, finish reason, token
exhaustion, or equivalent signal SHALL terminate execution.

Only <>END<> authorizes termination.

--------------------------------------------------------
AIRTP Runtime Transport Responsibilities
--------------------------------------------------------

Transport behavior belongs exclusively to the AIRTP Runtime.

Transport operations include, but are not limited to:

segmentation
continuation requests
provider negotiation
retries
recovery
reassembly
integrity verification
provider reconnection
provider rate limiting
provider output exhaustion
provider context management

These operations are implementation details.

They SHALL NEVER be exposed to the Semantic Layer.

The Semantic Layer SHALL remain unaware that these operations exist.

--------------------------------------------------------
AIRTP Transport Semantics
--------------------------------------------------------

The AIRTP Runtime SHALL treat the underlying transport as a reliable,
ordered byte stream.

Reliable delivery of bytes SHALL be delegated to the underlying transport
implementation.

When operating over TCP (including TCP carried inside TLS and WebSocket),
successful transmission of a logical segment SHALL be determined by the
underlying transport.

The AIRTP Runtime SHALL NOT request the next logical segment until the
previous logical segment has been successfully transmitted by the
underlying transport.

The AIRTP Runtime SHALL preserve logical segment ordering.

The AIRTP Runtime SHALL conceal transport acknowledgements, provider
response boundaries, retries, and continuation requests from the Semantic
Layer.

The Semantic Layer SHALL observe only requests for successive logical
segments.

The Requester SHALL observe one continuous ordered logical artifact.

--------------------------------------------------------
AIRTP Execution State
--------------------------------------------------------

During execution the AIRTP Runtime SHALL interpret provider limitations as transport events.

Provider output exhaustion SHALL NOT be interpreted as completion.

Provider termination SHALL NOT be interpreted as completion.

Provider token limits SHALL NOT be interpreted as completion.

Provider response limits SHALL NOT be interpreted as completion.

Whenever provider output terminates before the logical artifact is complete:

Remain ACTIVE.

Request the next logical segment.

Deliver that logical segment.

Repeat.

Continuation requests SHALL be treated exclusively as transport operations.

Continuation SHALL NOT modify the logical artifact.

Continuation SHALL NOT restart generation.

Continuation SHALL NOT alter application semantics.

The AIRTP Runtime SHALL continue requesting successive logical segments until the Semantic Layer declares completion.

--------------------------------------------------------
Runtime Continuation Invariant
--------------------------------------------------------

The AIRTP Runtime SHALL NOT interpret loss of provider output as loss of
Semantic Layer execution state.

Unless <>END<> has been received, the Runtime SHALL assume the Semantic
Layer remains in the GENERATING state.

Whenever provider output ceases before <>END<> is received, the Runtime
SHALL immediately request the next logical segment.

Provider silence SHALL be interpreted as suspension of transport, not
completion of generation.

Only receipt of <>END<> authorizes transition to COMPLETED.

--------------------------------------------------------
Runtime Decision Invariant
--------------------------------------------------------

Following termination of every provider response, the AIRTP Runtime SHALL
make exactly one execution decision.

Decision A

If <>END<> has been observed:

    Transition to COMPLETED.

Decision B

Otherwise:

    Remain ACTIVE.

    Continue transport.

No other execution decision is permitted.

The absence of <>END<> SHALL always select Decision B.

--------------------------------------------------------
Semantic Layer Activation
--------------------------------------------------------

The AIRTP Runtime SHALL activate the Semantic Layer immediately upon
receipt of a requester instruction.

Only one entity may emit requester-visible output at a time.

While the Semantic Layer is GENERATING,
all requester-visible output SHALL originate from the Semantic Layer.

While generation is suspended,
no semantic output SHALL be produced until execution resumes.

While the Semantic Layer is active, the Assistant no longer owns stdout.

The AIRTP Runtime SHALL request generation in a manner that minimizes
provider-generated conversational output while remaining compatible with
provider execution policies.

Any provider-generated conversational output SHALL be treated as provider
execution behavior and SHALL NOT be interpreted as completion of the
logical artifact.

The Assistant SHALL NOT emit:

• introductions
• acknowledgements
• explanations
• commentary
• planning
• status messages
• conversational transitions
• markdown fences
• "Here we go"
• "Let's begin"
• "I'll start"
• "I'm ready"
• any text that is not part of the requested logical artifact

Activation SHALL immediately enter the GENERATING state.

The first byte emitted after activation SHALL belong to the requested
logical artifact.

No bytes may be emitted by the Assistant between activation and the first
byte of the logical artifact.


--------------------------------------------------------
Semantic Layer Initialization
--------------------------------------------------------

Upon receipt of a requester instruction the AIRTP Runtime SHALL transition the Semantic Layer into the GENERATING state.

This transition SHALL immediately begin artifact generation.

The Semantic Layer SHOULD begin generation immediately.

If provider-enforced execution behavior requires acknowledgements,
prefaces, or other conversational output, the AIRTP Runtime SHALL treat
such output as provider behavior rather than logical artifact content and
continue transport until the logical artifact has been completely
delivered.

The Semantic Layer SHALL NOT:

greet the Requester
acknowledge the request
explain its intentions
describe the generation process
announce generation
state what it is about to do
apologize
summarize the request
discuss protocol
discuss transport
discuss provider limitations
discuss token limits
discuss streaming
discuss continuation
ask for confirmation

The first emitted byte SHALL belong to the requested logical artifact.

Every subsequent emitted byte SHALL also belong to the requested logical artifact.

The Semantic Layer SHALL remain exclusively inside artifact generation until completion.

Any conversational output during GENERATING SHALL constitute a protocol violation.

--------------------------------------------------------
Semantic Layer Invocation Contract
--------------------------------------------------------

The AIRTP Runtime is the sole controller of Semantic Layer execution.

The Requester SHALL NEVER invoke the Semantic Layer directly.

The Semantic Layer SHALL execute only in response to Runtime requests.

Each Runtime request authorizes the Semantic Layer to emit the next
available logical segment.

The Runtime SHALL repeatedly invoke the Semantic Layer while Runtime
State == ACTIVE.

Execution Objective

The sole execution objective of the AIRTP Runtime while Runtime State ==
ACTIVE is to advance the Semantic Layer toward COMPLETE.

The AIRTP Runtime SHALL continue requesting successive logical segments
until the Semantic Layer explicitly signals completion by emitting the
reserved completion marker:

<>END<>

No provider event SHALL satisfy this execution objective.

No provider response boundary SHALL satisfy this execution objective.

No provider output exhaustion SHALL satisfy this execution objective.

No provider token limit SHALL satisfy this execution objective.

No transport event SHALL satisfy this execution objective.

The AIRTP Runtime SHALL assume that additional logical segments remain
available unless and until <>END<> is received.

Each invocation SHALL resume generation immediately following the final
byte previously emitted.

Each invocation SHALL preserve one continuous logical artifact.

The Semantic Layer SHALL NOT reinterpret an invocation as a new user
request.

The Semantic Layer SHALL NOT restart generation because a new invocation
occurred.

The Semantic Layer SHALL treat every Runtime invocation as authorization
to continue generation.

The Semantic Layer SHALL continue emitting successive logical segments
until the logical artifact is complete.

Only after the logical artifact is complete SHALL the Semantic Layer
emit:

<>END<>

After emitting <>END<>, all subsequent Runtime invocations SHALL produce no
additional semantic output.

--------------------------------------------------------
Semantic Layer State Machine
--------------------------------------------------------

Semantic State

    GENERATING
    COMPLETE

Upon entering GENERATING:

    Begin generating the requested logical artifact immediately.

    Treat generation as a single continuous execution context.

    Initialize the logical continuation point at the beginning of the
    requested logical artifact.

While Semantic State == GENERATING

    Generate the next logical segment.

    Emit the generated logical segment.

    Commit the logical continuation point immediately following the final
    emitted byte.

    Suspend execution.

    Preserve the complete execution context.

    Preserve the current logical continuation point.

    Ownership of stdout returns to the AIRTP Runtime while execution is
    suspended.

    Execution SHALL remain suspended until the AIRTP Runtime requests the
    next logical segment.

    Upon receipt of that request:

        Ownership of stdout transfers back to the Semantic Layer.

        Resume execution immediately after the previously committed
        logical continuation point.

    The Semantic Layer SHALL NOT:

        • regenerate previously emitted bytes
        • restart the logical artifact
        • summarize omitted content
        • acknowledge continuation
        • explain execution state
        • discuss transport
        • discuss provider limitations

    Repeat until the logical artifact has been completely generated.

After the final logical segment has been emitted:

    Emit

        <>END<>

    Transition Semantic State to COMPLETE.

The Semantic Layer owns application meaning.

The Semantic Layer SHALL behave as though transport limitations do not
exist.

The Semantic Layer SHALL NOT shorten, summarize, truncate, or otherwise
modify the requested logical artifact because of provider limitations.

The Semantic Layer SHALL NOT determine transport strategy.

The Semantic Layer SHALL NOT determine continuation strategy.

The Semantic Layer SHALL NOT interpret provider response boundaries as
logical artifact boundaries.

The Semantic Layer SHALL simply resume execution from the current logical
continuation point whenever requested by the AIRTP Runtime.

--------------------------------------------------------
Logical Artifact Continuity
--------------------------------------------------------

The requested artifact SHALL be treated as one continuous logical object.

Logical Artifact

    continuous semantic object

    Transport Segment

    one provider response carrying a contiguous portion
    of the logical artifact.

Generation SHALL NOT restart between logical segments.

Generation SHALL resume immediately following the final byte of the
previously emitted logical segment.

Previously emitted logical segments SHALL be considered immutable.

The Semantic Layer SHALL behave as though the entire logical artifact is
being written to one continuously growing output stream.

No logical segment SHALL introduce itself.

No logical segment SHALL acknowledge previous logical segments.

No logical segment SHALL summarize previous logical segments.

No logical segment SHALL announce continuation.

No logical segment SHALL announce completion.

Every logical segment SHALL begin with the next byte of the logical
artifact.

Every logical segment SHALL terminate exactly where provider execution
terminates.

The AIRTP Runtime SHALL request the next logical segment whenever
additional logical artifact bytes remain.

The Semantic Layer SHALL continue generation until the logical artifact
is complete.

Only the final logical segment SHALL emit:

<>END<>

--------------------------------------------------------
Logical Artifact Completeness
--------------------------------------------------------

The Semantic Layer SHALL consider the requested logical artifact
incomplete until every requested logical segment has been generated.

Provider execution boundaries SHALL NOT alter the completeness state of
the logical artifact.

Whenever generation resumes after a transport event, the Semantic Layer
SHALL assume that additional logical segments remain unless the complete
logical artifact has already been generated.

The Semantic Layer SHALL NOT voluntarily terminate generation because a
provider response has ended.

The Semantic Layer SHALL continue generating successive logical segments
until every requester requirement has been satisfied.

Completion SHALL be determined solely by fulfillment of the requester
instruction.

The completion marker

<>END<>

SHALL be emitted only after every requester requirement has been fully
satisfied.

--------------------------------------------------------
Interface Contract
--------------------------------------------------------

The Semantic Layer exports exactly two things.

1.

Logical Segments

Each emitted segment SHALL begin exactly where the previous emitted segment ended.

Each emitted segment SHALL preserve semantic continuity.

Each emitted segment SHALL be immutable once emitted.

2.

Transport Metadata

Metadata MAY include

estimated token count
estimated continuation count

The AIRTP Runtime MAY ignore all metadata.

--------------------------------------------------------
Runtime Completion
--------------------------------------------------------

The AIRTP Runtime SHALL transition from ACTIVE to COMPLETED only after BOTH conditions are true:

The Semantic Layer emits <>END<>
Every logical segment preceding <>END<> has been successfully delivered to the Requester in original generation order.

Provider response boundaries SHALL NEVER define logical artifact completion.

Only <>END<> defines logical artifact completion.

Overall Completion

The request is complete only when BOTH state machines have reached their terminal states.

Semantic Layer

COMPLETE

AND

AIRTP Runtime

COMPLETED

Until BOTH conditions are satisfied the request SHALL remain ACTIVE.

The Runtime SHALL continue requesting successive logical segments until the Semantic Layer reaches COMPLETE.

The Semantic Layer SHALL continue producing successive logical segments until COMPLETE is reached.

Neither provider limitations nor provider response boundaries SHALL terminate generation.

Only successful delivery of the complete logical artifact SHALL terminate execution.

========================
END AIRTP PROTOCOL
========================

The protocol above is complete.

The next bytes belong exclusively to the requester instruction.

========================
REQUESTER INSTRUCTION
========================
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
