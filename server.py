import asyncio
import base64
import json
import sys
import websockets

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass
class Appointment:
    id: str
    timestamp: datetime
    patient_name: str
    mrn: str
    date: str
    time: str
    provider: str
    reason: str
    status: Literal["pending", "scheduled", "cancelled"]


config = {
    "eventTypeId": "2954150",
    "email": "junaidhassan9299@gmail.com",
    "language": "en",
}

appointment = Appointment(
    id="-1",
    timestamp=datetime.now(),
    patient_name="",
    mrn="",
    date="",
    time="",
    provider="",
    reason="",
    status="pending"
)


def sts_connect():
    # you can run export DEEPGRAM_API_KEY="your key" in your terminal to set your API key.
    # api_key = os.getenv('DEEPGRAM_API_KEY')
    # if not api_key:
    #     raise ValueError("DEEPGRAM_API_KEY environment variable is not set")

    sts_ws = websockets.connect(
        "wss://agent.deepgram.com/v1/agent/converse",
        subprotocols=["token", "723035c42506107c8552bcfa82fea9c0782d3013"]
    )
    return sts_ws


async def twilio_handler(twilio_ws):
    audio_queue = asyncio.Queue()
    streamsid_queue = asyncio.Queue()

    async with sts_connect() as sts_ws:

        # --- Function definitions ---
        def set_patient_name(name: str):
            appointment.patient_name = name
            print(f"[FUNCTION] Setting patient name: {name}")
            return {"status": "ok", "name": name}

        def set_mrn(mrn: str):
            appointment.mrn = mrn
            print(f"[FUNCTION] Setting MRN: {mrn}")
            return {"status": "ok", "mrn": mrn}

        def set_date(date: str):
            appointment.date = date
            print(f"[FUNCTION] Setting date: {date}")
            return {"status": "ok", "date": date}

        def set_time(time: str):
            appointment.time = time
            print(f"[FUNCTION] Setting time: {time}")
            return {"status": "ok", "time": time}

        def set_provider(provider: str):
            appointment.provider = provider
            print(f"[FUNCTION] Setting provider: {provider}")
            return {"status": "ok", "provider": provider}

        def set_reason(reason: str):
            appointment.reason = reason
            print(f"[FUNCTION] Setting reason: {reason}")
            return {"status": "ok", "reason": reason}

        def schedule_appointment():
            print(f"[FUNCTION] Scheduling appointment... {appointment}")
            return {"status": "ok", "scheduled": True}

        def clear_appointment():
            print(f"[FUNCTION] Clearing appointment form... {appointment}")
            return {"status": "ok", "cleared": True}

        config_message = {
            "type": "Settings",
            "audio": {
                "input": {"encoding": "mulaw", "sample_rate": 8000},
                "output": {"encoding": "mulaw", "sample_rate": 8000, "container": "none"},
            },
            "agent": {
                "language": "en",
                "listen": {
                    "provider": {
                        "type": "deepgram",
                        "model": "nova-3-medical",
                        "keyterms": ["appointment", "patient", "schedule"]
                    }
                },
                "think": {
                    "provider": {
                        "type": "open_ai",
                        "model": "gpt-4o-mini",
                        "temperature": 0.7
                    },
                    "prompt": "You are a helpful medical appointment scheduling assistant.",
                    "functions": [
                        {
                            "name": "set_patient_name",
                            "description": "Set the patient's name",
                            "parameters": {
                                "type": "object",
                                "properties": {"name": {"type": "string"}},
                                "required": ["name"]
                            }
                        },
                        {
                            "name": "set_mrn",
                            "description": "Set the patient's MRN",
                            "parameters": {
                                "type": "object",
                                "properties": {"mrn": {"type": "string"}},
                                "required": ["mrn"]
                            }
                        },
                        {
                            "name": "set_date",
                            "description": "Set the date for the appointment",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "date": {
                                        "type": "string",
                                        "description": "The date of the appointment in YYYY-MM-DD format"
                                    }
                                },
                                "required": [
                                    "date"
                                ]
                            }
                        },
                        {
                            "name": "set_time",
                            "description": "Set the time for the appointment",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "time": {
                                        "type": "string",
                                        "description": "The time of the appointment in HH:MM format"
                                    }
                                },
                                "required": [
                                    "time"
                                ]
                            }
                        },
                        {
                            "name": "set_provider",
                            "description": "Set the healthcare provider for the appointment",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "provider": {
                                        "type": "string",
                                        "description": "The name of the healthcare provider"
                                    }
                                },
                                "required": [
                                    "provider"
                                ]
                            }
                        },
                        {
                            "name": "set_reason",
                            "description": "Set the reason for the appointment",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "reason": {
                                        "type": "string",
                                        "description": "The reason for the appointment"
                                    }
                                },
                                "required": [
                                    "reason"
                                ]
                            }
                        },
                        {
                            "name": "schedule_appointment",
                            "description": "Schedule the current appointment",
                            "parameters": {
                                "type": "object",
                                "properties": {},
                                "required": []
                            }
                        },
                        {
                            "name": "clear_appointment",
                            "description": "Clear the current appointment form",
                            "parameters": {
                                "type": "object",
                                "properties": {},
                                "required": []
                            }
                        }
                    ]
                },
                "speak": {
                    "provider": {
                        "type": "deepgram",
                        "model": "aura-2-helena-en"
                    }
                },
                "greeting": "Hello! I can help you schedule a medical appointment. What's the patient's name?"
            }
        }

        await sts_ws.send(json.dumps(config_message))

        async def sts_sender(sts_ws):
            while True:
                chunk = await audio_queue.get()
                await sts_ws.send(chunk)

        async def sts_receiver(sts_ws):
            stream_id = await streamsid_queue.get()
            async for message in sts_ws:
                if isinstance(message, str):
                    decoded = json.loads(message)
                    msg_type = decoded.get("type")

                    if msg_type == "UserStartedSpeaking":
                        await twilio_ws.send(json.dumps({"event": "clear", "streamSid": stream_id}))

                    elif msg_type == "FunctionCallRequest":
                        print(decoded)
                        function = decoded.get("functions")[0]
                        fn_id = function.get("id")
                        fn_name = function.get("name")
                        raw_args = function.get("arguments", "{}")
                        args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                        print(f"[FUNCTION CALL RECEIVED] {fn_name}({args})({raw_args})")

                        match fn_name:
                            case "set_patient_name":
                                name = args.get("name")
                                result = set_patient_name(name)

                            case "set_mrn":
                                mrn = args.get("mrn")
                                result = set_mrn(mrn)

                            case "set_date":
                                date = args.get("date")
                                result = set_date(date)

                            case "set_time":
                                time = args.get("time")
                                result = set_time(time)

                            case "set_provider":
                                provider = args.get("provider")
                                result = set_provider(provider)

                            case "set_reason":
                                reason = args.get("reason")
                                result = set_reason(reason)

                            case "schedule_appointment":
                                schedule_appointment()

                            case "clear_appointment":
                                clear_appointment()

                            case _:
                                print("UNKNOWN CASE")

                        await sts_ws.send(json.dumps({
                            "type": "FunctionCallResponse",
                            "id": fn_id,
                            "name": fn_name,
                            "content": "Success",
                        }))
                    else:
                        print(decoded)
                    continue

                # Handle audio from DG
                media_message = {
                    "event": "media",
                    "streamSid": stream_id,
                    "media": {"payload": base64.b64encode(message).decode("ascii")},
                }
                await twilio_ws.send(json.dumps(media_message))

        async def twilio_receiver(twilio_ws):
            BUFFER_SIZE = 20 * 160
            inbuffer = bytearray(b"")
            async for message in twilio_ws:
                try:
                    data = json.loads(message)
                    if data["event"] == "start":
                        streamsid_queue.put_nowait(data["start"]["streamSid"])
                    elif data["event"] == "media" and data["media"]["track"] == "inbound":
                        inbuffer.extend(base64.b64decode(data["media"]["payload"]))
                    elif data["event"] == "stop":
                        break

                    while len(inbuffer) >= BUFFER_SIZE:
                        audio_queue.put_nowait(inbuffer[:BUFFER_SIZE])
                        inbuffer = inbuffer[BUFFER_SIZE:]
                except:
                    break

        await asyncio.wait([
            asyncio.ensure_future(sts_sender(sts_ws)),
            asyncio.ensure_future(sts_receiver(sts_ws)),
            asyncio.ensure_future(twilio_receiver(twilio_ws)),
        ])

        await twilio_ws.close()


async def router(websocket, path):
    print(f"Incoming connection on path: {path}")
    if path == "/twilio":
        print("Starting Twilio handler")
        await twilio_handler(websocket)


def main():
    # use this if using ssl
    # ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    # ssl_context.load_cert_chain('cert.pem', 'key.pem')
    # server = websockets.serve(router, '0.0.0.0', 443, ssl=ssl_context)

    # use this if not using ssl
    server = websockets.serve(router, "localhost", 5000)
    print("Server starting on ws://localhost:5000")

    asyncio.get_event_loop().run_until_complete(server)
    asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    sys.exit(main() or 0)
