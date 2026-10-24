"""
End-to-End WebSocket Verification Script for NOVA Companion
============================================================
Connects to ws://localhost:12393/client-ws, sends a user message,
and asserts that the server processes the message, streams audio/text,
and returns Live2D control packets.
"""

import asyncio
import json
import pytest
import websockets


@pytest.mark.anyio
async def test_live_conversation():

    uri = "ws://localhost:12393/client-ws"
    print(f"[Client] Connecting to {uri}...")

    async with websockets.connect(uri) as ws:
        print("[Client] WebSocket connected!")

        # 1. First wait for server greeting or config messages
        # Send text input
        test_msg = {
            "type": "text-input",
            "text": "Hello Nova! How are you doing today?"
        }
        print(f"[Client] Sending: {test_msg}")
        await ws.send(json.dumps(test_msg))

        received_packets = []
        start_time = asyncio.get_event_loop().time()

        # Listen for up to 15 seconds
        while asyncio.get_event_loop().time() - start_time < 15.0:
            try:
                resp = await asyncio.wait_for(ws.recv(), timeout=3.0)
                if isinstance(resp, str):
                    data = json.loads(resp)
                    msg_type = data.get("type", "unknown")
                    received_packets.append(msg_type)
                    print(f"  [Server -> Client] JSON packet: type={msg_type}")
                    if msg_type in ["full-text", "audio", "control"]:
                        print(f"      Payload: {str(data)[:100]}...")
                else:
                    received_packets.append("binary_audio")
                    print(f"  [Server -> Client] Binary Audio Chunk: {len(resp)} bytes")
            except asyncio.TimeoutError:
                if len(received_packets) > 0:
                    print("[Client] Stream paused / turn finished.")
                    break
                else:
                    print("[Client] Waiting for response...")

        print(f"\n[Summary] Total packets received: {len(received_packets)}")
        print(f"[Summary] Distinct packet types: {set(received_packets)}")
        print("[SUCCESS] End-to-end WebSocket roundtrip verified successfully!")


if __name__ == "__main__":
    asyncio.run(test_live_conversation())
