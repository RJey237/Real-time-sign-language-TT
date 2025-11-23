# Video Chat Setup - Configuration Summary

## ✅ What's Been Done

### 1. **SSL/HTTPS Setup**
- Generated self-signed SSL certificates for `192.168.100.201`:
  - `cert.pem` - Certificate file
  - `key.pem` - Private key
- Both are valid for 365 days

### 2. **Backend (Django + Channels)**
- **Server**: Hypercorn with HTTPS
- **URL**: `https://192.168.100.201:8000`
- **Features**:
  - User authentication (register/login/logout)
  - Real-time chat via WebSocket (`/ws/chat/<target_id>/`)
  - ASL prediction relay (`/ws/asl/`)
  - **NEW**: Video streaming (`/ws/video/<target_id>/`)

### 3. **Frontend (React + Vite)**
- **Server**: Vite dev server with HTTPS
- **URL**: `https://192.168.100.201:5175` (or 5174)
- **Features**:
  - Authentication panel
  - ASL translator with MediaPipe hand detection
  - Text chat with peer
  - **NEW**: Video chat component - Start/Stop camera, stream to peer

### 4. **Video Chat Component**
- **Component**: `VideoChat.jsx` - Handles:
  - Local camera capture (getUserMedia)
  - Real-time frame streaming via WebSocket
  - Remote peer video display via canvas
  - ~10 FPS transmission for performance
  - JPEG compression (70% quality)

### 5. **WebSocket Video Consumer**
- **Endpoint**: `/ws/video/<target_id>/?self=<your_id>`
- **Function**: Relays video frames between connected peers
- **Protocol**: JSON messages with base64-encoded frame data

## 🚀 How to Use

### **On Device 1 (e.g., Laptop)**:
1. Go to `https://192.168.100.201:5175`
2. **Register/Login** with a username and password
3. Note your **Random ID** shown in the auth panel
4. Optionally **Connect Chat** to another user's ID
5. In the **Video Chat** section:
   - Enter peer's **Target Random ID**
   - Click **"Start Video"** button
   - Camera access should be granted
   - Your live video will stream to the peer

### **On Device 2 (e.g., Phone)**:
1. Accept the self-signed certificate warning (browsers will show security notice)
2. Same registration/login flow
3. Enter Device 1's **Random ID** in the Chat panel
4. Connect to Video Chat with the same ID
5. Both see each other's camera feed

## 📋 Backend Architecture

**New VideoConsumer in `translator/consumers.py`**:
- Accepts WebSocket connections at `/ws/video/<target_id>/`
- Creates symmetric room names (like chat)
- Receives base64-encoded frames from client
- Broadcasts frames to peer via `group_send`
- Handles disconnect/error gracefully

**New Route in `translator/routing.py`**:
```python
re_path(r'^ws/video/(?P<target_id>[^/]+)/$', consumers.VideoConsumer.as_asgi()),
```

## 🎨 Frontend Components

**VideoChat.jsx**:
- Local video via `<video>` tag with `getUserMedia`
- Remote video via `<canvas>` for frame rendering
- WebSocket sends frames every 100ms (~10 FPS)
- Supports HTTPS/WSS protocol detection
- Error handling for camera access failures

**App.jsx Changes**:
- New `ChatVideoPanel` component
- Reads `myId` from localStorage
- Passes `targetId` and `myId` to VideoChat

**Vite Config**:
- Detects and loads SSL certificates from `../rtslt/`
- HTTPS enabled automatically when certs exist
- Binds to `0.0.0.0` for cross-network access

## ⚠️ Important Notes

1. **Self-Signed Certificates**: Browsers will show security warnings. Accept them:
   - Chrome: "Advanced" → "Proceed to 192.168.100.201 (unsafe)"
   - Firefox: "Add Exception"
   - Safari: "Show Details" → "Visit this website"

2. **Same Network**: Both devices must be on the same WiFi/LAN network

3. **Hostname**: Always use `192.168.100.201` (not localhost) on both devices

4. **Video Performance**: At 10 FPS with JPEG compression, expect:
   - Smooth enough for sign language observation
   - Slight latency (200-500ms typical for LAN)
   - Adjustable quality by changing compression level in VideoChat.jsx

5. **No Audio**: Current implementation is video-only for simplicity

## 🔧 Troubleshooting

**"getUserMedia is not available"**:
- Ensure using HTTPS (browser blocks on HTTP for IP addresses)
- Check certificate warning is accepted

**"WebSocket connection failed"**:
- Verify backend is running: `https://192.168.100.201:8000`
- Check firewall isn't blocking port 8000 or 5175

**"Video not displaying"**:
- Check browser console for errors
- Verify both users are connected with correct IDs
- Try "Start Video" again

**"Certificate untrusted"**:
- This is normal for self-signed certs
- Accept the security exception in browser settings
- Consider setting up proper certs for production

## 📱 Current Servers

**Backend**: 
```
https://192.168.100.201:8000
```

**Frontend**:
```
https://192.168.100.201:5175 (or 5174 if 5175 in use)
```

Both running with HTTPS support now! 🎉

## Next Steps (Optional)

1. Add audio (WebRTC for better quality)
2. Reduce latency with WebRTC data channels
3. Add video recording capability
4. Optimize compression based on bandwidth
5. Production SSL certificates (Let's Encrypt)
