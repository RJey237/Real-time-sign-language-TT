# Unified Video Chat with ASL Translator - Complete Setup

## ✅ What's Been Done

### **Single Unified Video Component**
- **UnifiedVideoChat.jsx**: Combines video streaming + ASL translator
- Shows your camera with ASL predictions overlay
- Shows peer's camera with their ASL predictions overlay
- Real-time hand gesture detection and translation

### **Architecture Overview**

```
┌─────────────────────────────────────────┐
│       UnifiedVideoChat Component         │
├─────────────────────────────────────────┤
│  • Video Stream (10 FPS) ──────────────→│
│  • ASL Predictions (Local) ────────────→│
│  • Peer Video (received) ──────────────→│
│  • Peer ASL (from chat relay) ────────→│
└─────────────────────────────────────────┘
         ↓                    ↓
    Video WebSocket     ASL WebSocket
         ↓                    ↓
    (0.0.0.0:8000)     (0.0.0.0:8000)
         ↓                    ↓
    VideoConsumer        ASLConsumer
         ↓                    ↓
         └──→ ChatConsumer (relays ASL predictions)
              ↓
              (broadcasts to peer)
```

### **Data Flow**

1. **Local ASL Prediction**:
   - Local video → ASL WebSocket → LSTM model → Prediction
   - Prediction overlaid on local camera feed
   - Also sent to chat for relay (event: `asl-prediction-local`)

2. **Peer ASL Reception**:
   - Chat WebSocket receives `asl_prediction` message from peer
   - Dispatches `remote-asl-prediction` event
   - UnifiedVideoChat displays on peer's video

3. **Video Streaming**:
   - Local camera → capture canvas → base64 JPEG
   - Sends via video WebSocket (10 FPS, 70% quality)
   - Backend filters and relays only to intended peer
   - Peer receives and draws on remote canvas

### **UI Layout**

```
┌──────────────────────────────────────────────────┐
│  📹 Video Chat with ASL Translator | Stop Video │
├──────────────────────────────────────────────────┤
│ ┌─────────────────────┐  ┌──────────────────┐   │
│ │ Your Camera & ASL   │  │  💬 Text Chat    │   │
│ │                     │  ├──────────────────┤   │
│ │ [Video Feed]        │  │ My ID: ABC123    │   │
│ │                     │  │ Peer ID: XYZ789  │   │
│ │ ┌─────────────────┐ │  │ [Connect] [Disc] │   │
│ │ │ Label: "A"      │ │  ├──────────────────┤   │
│ │ │ Confidence: 98% │ │  │ Chat messages:   │   │
│ │ └─────────────────┘ │  │ • user: hello    │   │
│ │                     │  │ • peer: hi there │   │
│ └─────────────────────┘  ├──────────────────┤   │
│ ┌─────────────────────┐  │ Message input    │   │
│ │ Peer's Camera & ASL │  │ [Send]           │   │
│ │                     │  └──────────────────┘   │
│ │ [Video Feed]        │                         │
│ │                     │                         │
│ │ ┌─────────────────┐ │                         │
│ │ │ Label: "B"      │ │                         │
│ │ │ Confidence: 95% │ │                         │
│ │ └─────────────────┘ │                         │
│ └─────────────────────┘                         │
└──────────────────────────────────────────────────┘
```

### **Backend Changes**

**VideoConsumer** (`/ws/video/<target_id>/`):
- Strictly one-to-one video relay (no echoes)
- Filters based on `sender_id` and `target_id`
- No frame loops

**ChatConsumer** (`/ws/chat/<target_id>/`):
- Handles `asl_prediction` type messages
- Relays to peer via `type: 'asl.prediction'`
- Passes through text messages normally

**ASLConsumer** (`/ws/asl/`):
- Unchanged - loads LSTM model, makes predictions
- Sends via separate WebSocket (not through video stream)

### **Frontend Flow**

1. **VideoAndChatPanel**: Container component
   - Manages IDs (myId, targetId)
   - Connects chat WebSocket
   - Listens for ASL prediction events

2. **UnifiedVideoChat**: Video component
   - Connects video WebSocket (peer video)
   - Connects ASL WebSocket (own predictions)
   - Listens for remote ASL predictions
   - Displays both local and peer cameras

3. **AuthPanel**: Unchanged
   - Register/login to get random_id
   - Same as before

### **How to Use**

**On Device 1:**
1. Go to `https://192.168.100.201:5174`
2. Register/Login → note your **Random ID** (e.g., `ABC123`)
3. Scroll to **Video Chat with ASL Translator**
4. Enter your ID in "My ID" field
5. Enter peer's ID in "Peer's ID" field  
6. Click **"Start Video"**
7. Grant camera permission
8. See your camera on left with ASL predictions
9. Text chat available on right panel

**On Device 2:**
1. Same URL and registration
2. Enter Device 1's Random ID in "Peer's ID"
3. Same flow
4. See both cameras + both ASL predictions in real-time

### **Current Servers**

- **Backend**: `https://192.168.100.201:8000`
  - Video WebSocket: `wss://192.168.100.201:8000/ws/video/`
  - ASL WebSocket: `wss://192.168.100.201:8000/ws/asl/`
  - Chat WebSocket: `wss://192.168.100.201:8000/ws/chat/`

- **Frontend**: `https://192.168.100.201:5174` (or 5175)
  - Uses HTTPS with self-signed certs

### **Key Features**

✅ **Unified Interface**: One video panel for both devices  
✅ **ASL Overlay**: Predictions displayed directly on video  
✅ **No Echo**: Peer video filtering prevents loops  
✅ **Real-time Chat**: Text messaging alongside video  
✅ **Cross-Network**: Both phone and laptop work  
✅ **Low Latency**: 10 FPS video + instant ASL  
✅ **HTTPS/WSS**: Secure connections with self-signed certs  

### **Technical Stack**

- **Frontend**: React + Vite with MediaPipe (removed from this component - ASL via backend only)
- **Backend**: Django Channels + Hypercorn (HTTPS)
- **ML**: TensorFlow/Keras LSTM (trained on ASL alphabet)
- **Networking**: WebSocket (video, ASL, chat on same server)
- **Relay**: ChatConsumer broadcasts ASL predictions between peers

### **Performance Notes**

- Video: ~10 FPS, 70% JPEG quality = ~50-100 KB/frame
- ASL: Predictions at video rate (~10 FPS)
- Chat: Instant (text only)
- Total bandwidth: ~500-1000 KB/s for dual video + ASL

### **Next Steps (Optional)**

1. Add audio stream (requires WebRTC upgrade)
2. Better compression (VP8/H264 codec)
3. Gesture confidence threshold
4. Recording capability
5. Production SSL certs (Let's Encrypt)
6. Media server (SFU) for 3+ participants

---

**Status**: ✅ **COMPLETE** - Unified video chat with real-time ASL translation ready for testing on both devices!
