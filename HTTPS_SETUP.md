# HTTPS Setup Complete ✅

## Status
- ✅ Frontend: HTTPS on `https://192.168.100.201:5175`
- ✅ Backend: HTTPS on `https://192.168.100.201:8000`
- ✅ WebSocket: WSS (Secure WebSocket) enabled
- ✅ SSL Certificates: Self-signed, valid for 365 days

## Files Generated
```
rtslt/
  ├── server.crt    (SSL Certificate)
  ├── server.key    (Private Key)
  ├── cert.pem      (Copy for Vite)
  └── key.pem       (Copy for Vite)
```

## How to Run

### Backend (Hypercorn with HTTPS)
```bash
cd rtslt
python -m hypercorn --bind 0.0.0.0:8000 --certfile server.crt --keyfile server.key rtslt.asgi:application
```

### Frontend (Vite with HTTPS)
```bash
cd frontend
npm run dev
```

The frontend will automatically use HTTPS because the certificates exist at `../rtslt/cert.pem` and `../rtslt/key.pem`.

## Access URLs
- **Frontend**: `https://192.168.100.201:5175`
- **Backend API**: `https://192.168.100.201:8000/api/`
- **Video Chat WebSocket**: `wss://192.168.100.201:8000/ws/video/`
- **ASL WebSocket**: `wss://192.168.100.201:8000/ws/asl/`
- **Chat WebSocket**: `wss://192.168.100.201:8000/ws/chat/`

## Browser Certificate Warning ⚠️
Since we're using self-signed certificates, your browser will show a security warning:
- Chrome: Click "Advanced" → "Proceed to 192.168.100.201 (unsafe)"
- Firefox: Click "Advanced" → "Accept the Risk and Continue"
- Safari: Trust the certificate

This is expected for self-signed certs. The connection is still secure (encrypted).

## Testing
1. Open `https://192.168.100.201:5175` in your browser
2. Ignore the SSL warning and proceed
3. Register with username and password
4. Try the video chat between two devices

## API Verification
Test the register endpoint:
```bash
curl -X POST https://192.168.100.201:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}' \
  -k
```

The `-k` flag tells curl to ignore SSL certificate validation.

---
**All systems ready for secure video chat! 🎥**
