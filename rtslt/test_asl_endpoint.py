"""
Test ASL WebSocket endpoint to verify it's working correctly
"""
import asyncio
import json
import numpy as np
import websockets
import ssl

async def test_asl_endpoint():
    """Test the ASL WebSocket endpoint"""
    
    # Create SSL context (allow self-signed cert)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    uri = "wss://192.168.100.201:8000/ws/asl/"
    
    try:
        print(f"[TEST] Connecting to {uri}")
        async with websockets.connect(uri, ssl=ssl_context) as websocket:
            print("[TEST] Connected!")
            
            # Wait for connection message
            msg = await websocket.recv()
            print(f"[TEST] Received: {msg}")
            
            # Send dummy landmarks (10 frames of 126-dim data)
            print("\n[TEST] Sending landmarks (10 frames)...")
            for frame_num in range(15):  # Need 10 to trigger prediction
                landmarks = np.random.rand(126).tolist()  # Random 126-dim vector
                
                data = {
                    'type': 'landmarks',
                    'landmarks': landmarks,
                    'has_hands': True
                }
                
                await websocket.send(json.dumps(data))
                print(f"  Frame {frame_num + 1}/15 sent...")
                
                # Check for predictions
                try:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                    print(f"  Response: {msg}")
                except asyncio.TimeoutError:
                    pass  # No response yet
            
            print("\n[TEST] Sending final frames and waiting for predictions...")
            for i in range(5):
                try:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    print(f"  Prediction: {msg}")
                except asyncio.TimeoutError:
                    print("  No prediction received")
            
            print("\n[TEST] Test complete")
    
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == '__main__':
    asyncio.run(test_asl_endpoint())
