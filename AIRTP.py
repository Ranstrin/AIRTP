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

import asyncio
import argparse
import json
import uuid
import hashlib
import ssl
import sys
import os

from dataclasses import dataclass, field
from typing import Dict, Any
from websockets.exceptions import ConnectionClosed

@dataclass
class AIRTPConfig:
    endpoint: str
    api_key: str
    model: str = "gpt-realtime"

try:
    import websockets

except ImportError:

    print(
        "Install dependency: pip install websockets"
    )

    raise



# ============================================================
# Configuration
# ============================================================


AIRTP_VERSION = "AIRTP/0.1"


DEFAULT_CHUNK_SIZE = 4096



# ============================================================
# Capability Negotiation
# ============================================================


@dataclass
class CapabilityProfile:


    protocol: str = AIRTP_VERSION

    chunk_size: int = DEFAULT_CHUNK_SIZE

    maximum_chunk_size: int = 8192

    streaming: bool = True

    resume: bool = False

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )



class CapabilityNegotiator:


    def __init__(self):

        self.profile = CapabilityProfile()



    def create_hello(self):


        return {


            "protocol":

                AIRTP_VERSION,


            "message_type":

                "CAPABILITY_REQUEST",


            "payload":

            {


                "features":

                [

                    "chunking",

                    "streaming",

                    "resume"

                ]

            }

        }



    def process_response(

        self,

        response

    ):


        payload = response.get(

            "payload",

            {}

        )


        self.profile.chunk_size = (

            payload

            .get(

                "chunk_size",

                DEFAULT_CHUNK_SIZE

            )

        )


        self.profile.maximum_chunk_size = (

            payload

            .get(

                "maximum_chunk_size",

                8192

            )

        )


        self.profile.streaming = (

            payload

            .get(

                "streaming",

                True

            )

        )


        self.profile.metadata = payload



        return self.profile




# ============================================================
# Chunk Management
# ============================================================


class ChunkManager:


    def __init__(

        self,

        size=DEFAULT_CHUNK_SIZE

    ):


        self.size = size



    def split(

        self,

        data

    ):


        chunks = []


        total = (

            len(data)

            +

            self.size

            -

            1

        ) // self.size



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




    def assemble(

        self,

        chunks

    ):


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



    def create(

        self,

        message_type,

        payload,

        message_id=None

    ):


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



# ============================================================
# Integrity
# ============================================================


def checksum(data):


    return hashlib.sha256(

        data.encode("utf-8")

    ).hexdigest()



# ============================================================
# WebSocket TLS Transport
# ============================================================


class WebSocketTransport:


    def __init__(

        self,

        endpoint,

        api_key=None,

        verify_tls=True

    ):


        self.endpoint = endpoint

        self.api_key = api_key

        self.verify_tls = verify_tls

        self.socket = None



    async def connect(self):
    
        if not self.api_key:
            raise RuntimeError(
                "OpenAI API key required"
            )
    
        headers = [
            (
                "Authorization",
                f"Bearer {self.api_key}"
            ),
        ]
    
        ssl_context = ssl.create_default_context()
    
        #print(
            #"Connecting:",
            #self.endpoint,
            #flush=True
        #)
        
        #print(
        #    "Headers:",
        #    [
        #        (
        #            key,
        #                    "***" if key == "Authorization" else value
        #)
        #        for key, value in headers
        #    ],
        #    flush=True
        #)
        
        
        self.socket = await websockets.connect(
            self.endpoint,
            extra_headers=headers,
            ssl=ssl_context,
            ping_interval=20,
            ping_timeout=20,
            close_timeout=10,
        )



    async def send(self, message):

        #print("SEND RAW:", message, flush=True)
        await self.socket.send(message)


    async def receive(self):
        try:
            return await self.socket.recv()
        except ConnectionClosed:
            return None
    
    
    async def close(self):
    
        if self.socket:
    
            await self.socket.close()

            self.socket = None





# ============================================================
# OpenAI Provider Adapter
# ============================================================


class OpenAIRealtimeAdapter:


    def __init__(

        self,

        model="gpt-realtime"

    ):


        self.model = model



    async def initialize(self, transport):

        #
        # Transport establishment is complete.
        #
        # AIRTP capability negotiation belongs to the AIRTP protocol layer,
        # not the provider transport.
        #
            # The OpenAI Realtime service already emits "session.created"
        # immediately after connection. There is no provider initialization
        # required here for basic text exchanges.
        #
        return


    async def send_message(

        self,

        transport,

        envelope

    ):

        #
        # Translate AIRTP envelope into an OpenAI request.
        #
        text = envelope["payload"]["content"]

        event = {

            "type": "conversation.item.create",
    
            "item": {

                "type": "message",

                "role": "user",

                "content": [

                    {

                        "type": "input_text",

                        "text": text

                    }

                ]

            }

        }

        try:

            #print("SENDING USER MESSAGE", flush=True)
            await transport.send(
                json.dumps(event)
            )

            await transport.send(
                json.dumps({
                    "type": "response.create"
                })
            )

        except Exception as exc:

            raise RuntimeError(
                f"Provider send failed: {exc}"
            )
        
    async def receive_message(

        self,

        transport

    ):

        output = []

        while True:

            raw = await transport.receive()

            if raw is None:
                raise RuntimeError("Transport closed")

            event = json.loads(raw)

            event_type = event.get("type")

            #
            # Provider bookkeeping.
            #
            if event_type.startswith("session."):
                continue

            if event_type.startswith("conversation."):
                continue

            if event_type.startswith("rate_limits."):
                continue

            #
            # Provider errors.
            #
            if event_type == "error":
                raise RuntimeError(
                    event["error"]["message"]
                )
    
            #
            # Normalize every provider text delta into AIRTP text.
            #
            delta = None

            if event_type == "response.output_text.delta":
                delta = event.get("delta")

            elif event_type == "response.output_audio_transcript.delta":
                delta = event.get("delta")

            elif event_type == "response.output_text.done":
                delta = event.get("text")

            if delta:
                output.append(delta)
                continue

            #
            # Ignore non-text provider media.
            #
            if event_type.startswith("response.output_audio"):
                continue

            if event_type.startswith("response.content_part"):
                continue

            if event_type.startswith("response.output_item"):
                continue

            #
            # Logical response complete.
            #
            if event_type == "response.done":
                return "".join(output)

# ============================================================
# AIRTP Session
# ============================================================


class AIRTPSession:

    def __init__(
        self,
        transport,
        adapter
    ):

        self.transport = transport
        self.adapter = adapter
        self.capabilities = CapabilityNegotiator()
        self.chunker = ChunkManager()
        self.envelopes = EnvelopeFactory()

    async def start(self):

        await self.transport.connect()

        await self.adapter.initialize(
            self.transport
        )

    async def send_logical_message(
        self,
        message
    ):

        chunks = self.chunker.split(message)

        assembled = self.chunker.assemble(chunks)

        envelope = self.envelopes.create(
            "MODEL_REQUEST",
            {
                "content": assembled
            }
        )

        await self.adapter.send_message(
            self.transport,
            envelope
        )

        return await self.adapter.receive_message(
            self.transport
        )

# ============================================================
# Interactive Shell
# ============================================================


class InteractiveShell:


    def __init__(

        self,

        session

    ):


        self.session = session



    async def process(

        self,

        text

    ):


        response = await self.session.send_logical_message(

            text

        )


        print(

            response,

            flush=True

        )



    async def interactive(self):


        #print(

            #"AIRTP session ready",

            #flush=True

        #)



        while True:


            try:


                text = await asyncio.to_thread(input, "> ")


            except EOFError:


                break



            if text.lower() in (

                "exit",

                "quit"

            ):


                break



            if text.strip():


                await self.process(

                    text

                )



    async def pipe_mode(self):


        data = sys.stdin.read()



        if data.strip():


            await self.process(

                data

            )



    async def run(self):


        if sys.stdin.isatty():


            await self.interactive()



        else:


            await self.pipe_mode()




# ============================================================
# CLI
# ============================================================


def parse_arguments():


    parser = argparse.ArgumentParser(

        description=

        "AIRTP AI transport client"

    )



    parser.add_argument(

        "--endpoint",

        required=True,

        help=

        "WebSocket TLS endpoint"

    )



    parser.add_argument(

        "--api-key",

        required=False,

        default=None,

        help=

        "Optional API credential"

    )



    parser.add_argument(

        "--model",

        default="gpt-realtime"

    )



    parser.add_argument(

        "--no-tls-verify",

        action="store_true"

    )



    return parser.parse_args()




# ============================================================
# Main Runtime
# ============================================================


async def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--endpoint",
        default="wss://api.openai.com/v1/realtime?model=gpt-realtime"
    )

    parser.add_argument(
        "--api-key",
        default=None,
        help="OpenAI API key (overrides OPENAI_API_KEY)"
    )

    args = parser.parse_args()

    endpoint = args.endpoint

    transport = WebSocketTransport(
        endpoint=endpoint,
        api_key= args.api_key or os.environ.get("OPENAI_API_KEY")
    )

    adapter = OpenAIRealtimeAdapter()

    session = AIRTPSession(
        transport=transport,
        adapter=adapter
    )

    shell = InteractiveShell(
        session=session
    )

    await session.start()


    try:

        await shell.run()

    finally:


        await transport.close()




if __name__ == "__main__":


    asyncio.run(

        main()

    )
    # ============================================================
# Mock AI Endpoint
#
# Local protocol validation server
# ============================================================


class MockAIServer:


    def __init__(self):

        self.messages = {}



    async def handler(

        self,

        websocket

    ):


        async for raw in websocket:


            envelope = json.loads(raw)



            message_type = (

                envelope.get(

                    "message_type"

                )

            )



            if message_type == (

                "CAPABILITY_REQUEST"

            ):


                response = {


                    "protocol":

                        AIRTP_VERSION,


                    "message_type":

                        "CAPABILITY_RESPONSE",


                    "payload":

                    {


                        "chunk_size":

                            4096,


                        "maximum_chunk_size":

                            8192,


                        "streaming":

                            True

                    }

                }



                await websocket.send(

                    json.dumps(response)

                )



            elif message_type == (

                "MODEL_REQUEST"

            ):


                payload = (

                    envelope

                    .get(

                        "payload",

                        {}

                    )

                )



                content = (

                    payload

                    .get(

                        "content",

                        ""

                    )

                )



                reply = {


                    "type":

                        "response.output_text.delta",


                    "delta":

                        (

                        "Received logical message "

                        "of "

                        + str(len(content))

                        + " characters."

                        )

                }



                await websocket.send(

                    json.dumps(reply)

                )



                await websocket.send(

                    json.dumps({

                        "type":

                            "response.done"

                    })

                )

# ============================================================
# Streaming Response Receiver
# ============================================================


class StreamingReceiver:


    async def stream(

        self,

        transport

    ):


        while True:


            raw = await transport.receive()



            event = json.loads(raw)



            event_type = event.get(

                "type"

            )



            if event_type == (

                "response.output_text.delta"

            ):


                delta = event.get(

                    "delta",

                    ""

                )


                #print(

                    #delta,

                    #end="",

                    #flush=True

                #)



            elif event_type == (

                "response.done"

            ):


                print()

                break

# ============================================================
# Session Identity
# ============================================================


class SessionIdentity:


    def __init__(self):


        self.session_id = str(

            uuid.uuid4()

        )



    def metadata(self):


        return {


            "session_id":

                self.session_id,


            "protocol":

                AIRTP_VERSION

        }

# ============================================================
# Dynamic Window Manager
# ============================================================


class WindowManager:


    def __init__(self):


        self.chunk_size = 4096

        self.maximum_message_size = None



    def negotiate(

        self,

        capability_response

    ):


        payload = capability_response.get(

            "payload",

            {}

        )



        self.chunk_size = (

            payload.get(

                "recommended_chunk_size",

                self.chunk_size

            )

        )



        self.maximum_message_size = (

            payload.get(

                "maximum_message_size"

            )

        )



    def get_chunk_size(self):


        return self.chunk_size


