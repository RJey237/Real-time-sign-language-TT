import React, { useEffect, useRef, useState } from 'react';
import { Hands, HAND_CONNECTIONS } from '@mediapipe/hands'
import { Camera } from '@mediapipe/camera_utils'
import { drawConnectors, drawLandmarks } from '@mediapipe/drawing_utils'

const HOST = typeof window !== 'undefined' ? window.location.hostname : 'localhost'
const WS_PROTOCOL = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
const WS_BASE = `${WS_PROTOCOL}//${HOST}:8000`

export default function UnifiedVideoChat({ initialMyId = '', initialTargetId = '', myId = '', targetId = '', isConnected = false }) {
  // --- STATE ---
  const [joined, setJoined] = useState(isConnected);
  const displayMyId = myId || initialMyId;
  const displayTargetId = targetId || initialTargetId;
  
  // --- REFS ---
  const localVideoRef = useRef(null);
  const localCanvasRef = useRef(null);
  const remoteVideoRef = useRef(null);
  const wsVideoRef = useRef(null);
  const wsASLRef = useRef(null);
  const handsRef = useRef(null);
  const cameraRef = useRef(null);
  const lastSentLandmarksRef = useRef(0);
  const lastVideoSentRef = useRef(0);
  
  const [videoActive, setVideoActive] = useState(false);
  const [error, setError] = useState(null);
  const [localPrediction, setLocalPrediction] = useState(null);
  const [remotePrediction, setRemotePrediction] = useState(null);
  const [chat, setChat] = useState([]);
  const [text, setText] = useState('');
  const [ws, setWs] = useState(null);

  // --- HANDLERS ---

  const handleDisconnect = () => {
    setJoined(false);
    setVideoActive(false);
    setChat([]);
    if (ws) ws.close();
    if (wsVideoRef.current) wsVideoRef.current.close();
    if (wsASLRef.current) wsASLRef.current.close();
  };

  // --- EFFECTS (Only run when 'joined' is true) ---

  useEffect(() => {
    // Sync joined state with isConnected prop
    setJoined(isConnected);
  }, [isConnected]);

  useEffect(() => {
    if (!joined) return;
    const handler = (e) => setRemotePrediction(e.detail);
    window.addEventListener('remote-asl-prediction', handler);
    return () => window.removeEventListener('remote-asl-prediction', handler);
  }, [joined]);

  useEffect(() => {
    if (!joined) return;
    const hands = new Hands({
      locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`
    });
    hands.setOptions({ maxNumHands: 2, modelComplexity: 1, minDetectionConfidence: 0.6, minTrackingConfidence: 0.6 });
    hands.onResults(onResults);
    handsRef.current = hands;
    return () => { try { handsRef.current?.close() } catch {} };
  }, [joined]);

  const onResults = (results) => {
    const canvas = localCanvasRef.current;
    const video = localVideoRef.current;
    if (!canvas || !video) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.save();
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(results.image, 0, 0, canvas.width, canvas.height);

    const all = results.multiHandLandmarks || [];
    if (all.length > 0) {
      all.forEach(lm => {
        drawConnectors(ctx, lm, HAND_CONNECTIONS, { color: '#00FF00', lineWidth: 2 });
        drawLandmarks(ctx, lm, { color: '#FF0000', lineWidth: 1 });
      });
    } else {
      setLocalPrediction(null);
    }
    ctx.restore();

    const now = performance.now();
    if (now - lastSentLandmarksRef.current > 50) {
      // Only send landmarks if hands are detected
      if (all.length > 0) {
        const flat = [];
        for (let h = 0; h < Math.min(2, all.length); h++) {
          const lm = all[h];
          for (let i = 0; i < lm.length; i++) {
            flat.push(lm[i].x, lm[i].y, lm[i].z ?? 0);
          }
        }
        while (flat.length < 126) flat.push(0);

        if (wsASLRef.current && wsASLRef.current.readyState === WebSocket.OPEN) {
          wsASLRef.current.send(JSON.stringify({ type: 'landmarks', landmarks: flat.slice(0, 126), has_hands: true }));
        }
      } else {
        // No hands detected - send signal to reset prediction
        if (wsASLRef.current && wsASLRef.current.readyState === WebSocket.OPEN) {
          wsASLRef.current.send(JSON.stringify({ type: 'landmarks', landmarks: [], has_hands: false }));
        }
      }
      lastSentLandmarksRef.current = now;
    }
  };

  useEffect(() => {
    if (!joined || !videoActive) return;
    const start = async () => {
      try {
        const cam = new Camera(localVideoRef.current, {
          onFrame: async () => { await handsRef.current.send({ image: localVideoRef.current }); },
          width: 640, height: 480
        });
        cameraRef.current = cam;
        await cam.start();
        setError(null);
      } catch (err) {
        setError('Camera access failed: ' + err.message);
        setVideoActive(false);
      }
    };
    start();
    return () => { try { cameraRef.current?.stop() } catch {} };
  }, [joined, videoActive]);

  useEffect(() => {
    if (!joined || !videoActive) return;
    const wsUrl = `${WS_BASE}/ws/video/${displayTargetId}/?self=${displayMyId}`;
    const ws = new WebSocket(wsUrl);
    wsVideoRef.current = ws;
    ws.onopen = () => startSendingFrames();
    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        if (data.type === 'frame' && data.frame_data) displayRemoteFrame(data.frame_data);
      } catch (err) {}
    };
    ws.onerror = () => setError('Video connection failed');
    return () => { if (ws && ws.readyState === WebSocket.OPEN) ws.close(); };
  }, [joined, videoActive, displayTargetId, displayMyId]);

  useEffect(() => {
    if (!joined || !videoActive) return;
    const wsUrl = `${WS_BASE}/ws/asl/`;
    const ws = new WebSocket(wsUrl);
    wsASLRef.current = ws;
    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        if (data.type === 'prediction') {
          setLocalPrediction({ label: data.label, confidence: data.confidence });
          window.dispatchEvent(new CustomEvent('asl-prediction-local', {
            detail: { label: data.label, confidence: data.confidence }
          }));
        }
      } catch (err) {}
    };
    return () => { if (ws && ws.readyState === WebSocket.OPEN) ws.close(); };
  }, [joined, videoActive]);

  useEffect(() => {
    if (!joined) return;
    const qs = `?self=${encodeURIComponent(displayMyId)}`;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const BACKEND_HOST_STR = window.location.hostname === 'localhost' ? '127.0.0.1' : window.location.hostname;
    const sock = new WebSocket(`${protocol}//${BACKEND_HOST_STR}:8000/ws/chat/${encodeURIComponent(displayTargetId)}/${qs}`);
    
    sock.onopen = () => setChat([{ sys: true, text: 'Chat connected' }]);
    sock.onclose = () => setChat(c => [...c, { sys: true, text: 'Chat disconnected' }]);
    sock.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        if (data.type === 'message') {
          setChat(c => [...c, { sender: data.sender, text: data.text }]);
        } else if (data.type === 'asl_prediction') {
          window.dispatchEvent(new CustomEvent('remote-asl-prediction', {
            detail: { label: data.label, confidence: data.confidence }
          }));
        }
      } catch {}
    };
    setWs(sock);
    return () => { if (sock && sock.readyState === WebSocket.OPEN) sock.close(); };
  }, [joined, displayTargetId, displayMyId]);

  const startSendingFrames = () => {
    const send = () => {
      if (!localCanvasRef.current || !wsVideoRef.current || wsVideoRef.current.readyState !== WebSocket.OPEN) {
        requestAnimationFrame(send);
        return;
      }
      const now = Date.now();
      if (now - lastVideoSentRef.current < 150) {
        requestAnimationFrame(send);
        return;
      }
      try {
        const frameData = localCanvasRef.current.toDataURL('image/jpeg', 0.5);
        wsVideoRef.current.send(JSON.stringify({ type: 'frame', frame_data: frameData }));
        lastVideoSentRef.current = now;
      } catch (err) {}
      requestAnimationFrame(send);
    };
    requestAnimationFrame(send);
  };

  const displayRemoteFrame = (frameDataUrl) => {
    if (!remoteVideoRef.current) return;
    const img = new Image();
    img.src = frameDataUrl;
    img.onload = () => {
      remoteVideoRef.current.width = img.width;
      remoteVideoRef.current.height = img.height;
      const ctx = remoteVideoRef.current.getContext('2d');
      ctx.clearRect(0, 0, remoteVideoRef.current.width, remoteVideoRef.current.height);
      ctx.drawImage(img, 0, 0);
    };
  };

  const sendMessage = () => {
    if (!ws || ws.readyState !== WebSocket.OPEN || !text) return;
    ws.send(JSON.stringify({ type: 'message', text }));
    setText('');
  };

  // --- RENDER ---

  return (
    <div className="unified-app-root">
      <style>{cssStyles}</style>

      {/* --- MAIN INTERFACE --- */}
      {/* LEFT: VIDEO AREA */}
      <div className="video-panel">
        <div className="panel-header">
          <h3>📹 Video Chat</h3>
          <div className="controls">
            {!videoActive ? (
              <button onClick={() => setVideoActive(true)} className="btn btn-primary">
                Start Camera
              </button>
            ) : (
              <button onClick={() => setVideoActive(false)} className="btn btn-danger">
                Stop Camera
              </button>
            )}
          </div>
        </div>

        {error && <div className="error-msg">{error}</div>}

        <div className="video-stage">
          {!videoActive ? (
            <div className="empty-state">Camera is Off</div>
          ) : (
            <>
              {/* Remote Video (Big) */}
              <canvas ref={remoteVideoRef} className="remote-video" />
              
              {/* Local Video (PIP) */}
              <div className="local-pip">
                <video ref={localVideoRef} style={{ display: 'none' }} />
                <canvas ref={localCanvasRef} className="local-canvas" />
              </div>

              {/* ASL Overlay */}
              {remotePrediction && (
                <div className="asl-badge">
                  <span className="asl-text">{remotePrediction.label}</span>
                  <span className="asl-conf">{(remotePrediction.confidence * 100).toFixed(0)}%</span>
                </div>
              )}
            </>
          )}
        </div>
      </div>

          {/* RIGHT: CHAT AREA */}
          <div className="chat-panel">
            <div className="panel-header">
              <h3>💬 Chat</h3>
              <button onClick={handleDisconnect} className="btn btn-sm btn-danger">
                Disconnect
              </button>
            </div>

            <div className="id-bar">
              <div className="id-tag">Me: {displayMyId}</div>
              <div className="id-tag">Peer: {displayTargetId}</div>
            </div>

            <div className="chat-messages">
              {chat.length === 0 && <div className="chat-empty">No messages yet</div>}
              {chat.map((m, i) => (
                <div key={i} className={`message ${m.sys ? 'sys' : ''}`}>
                  {m.sys ? (
                    <span className="sys-text">{m.text}</span>
                  ) : (
                    <>
                      <div className="avatar">{m.sender ? m.sender[0].toUpperCase() : '?'}</div>
                      <div className="bubble">
                        <div className="sender">{m.sender}</div>
                        <div className="text">{m.text}</div>
                      </div>
                    </>
                  )}
                </div>
              ))}
            </div>

            <div className="chat-input-area">
              <input
                className="chat-input"
                placeholder="Type a message..."
                value={text}
                onChange={e => setText(e.target.value)}
                onKeyPress={e => e.key === 'Enter' && sendMessage()}
              />
              <button onClick={sendMessage} className="btn btn-send">Send</button>
            </div>
          </div>
    </div>
  );
}

// --- CSS STYLES ---
const cssStyles = `
  /* Root Container */
  .unified-app-root {
    position: relative;
    width: 100%;
    height: 100%;
    background-color: #0f172a;
    color: #e2e8f0;
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    display: flex;
    flex-direction: row;
    overflow: hidden;
    z-index: 1;
  }

  /* --- AUTH OVERLAY --- */
  .auth-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(15, 23, 42, 0.95);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10000;
  }

  .auth-card {
    background: #1e293b;
    padding: 2rem;
    border-radius: 12px;
    width: 100%;
    max-width: 400px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    border: 1px solid #334155;
  }

  .auth-title { margin-top: 0; text-align: center; color: #2dd4bf; margin-bottom: 1.5rem; }
  
  .auth-inputs { display: flex; flex-direction: column; gap: 1rem; margin-bottom: 1.5rem; }
  
  .input-group label { display: block; font-size: 0.85rem; color: #94a3b8; margin-bottom: 0.4rem; }
  
  .auth-input {
    width: 100%;
    padding: 0.75rem;
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 6px;
    color: white;
    font-size: 1rem;
  }
  .auth-input:focus { outline: 2px solid #2dd4bf; border-color: transparent; }

  .btn-block { width: 100%; padding: 0.8rem; font-size: 1rem; }

  /* --- MAIN LAYOUT --- */
  .video-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 1rem;
    background-color: #1e293b;
    border-right: 1px solid #334155;
    position: relative;
  }

  .chat-panel {
    width: 360px;
    display: flex;
    flex-direction: column;
    background-color: #0f172a;
    padding: 1rem;
    box-shadow: -2px 0 10px rgba(0,0,0,0.2);
    z-index: 20; /* Ensure chat sits above if needed */
  }

  /* --- MOBILE LAYOUT --- */
  @media (max-width: 768px) {
    .unified-app-root { flex-direction: column; }
    .video-panel { flex: none; height: 40vh; padding: 0.5rem; border-right: none; border-bottom: 1px solid #334155; }
    .chat-panel { flex: 1; width: 100%; padding: 0.5rem; }
    .local-pip { width: 80px !important; height: 106px !important; bottom: 10px !important; left: 10px !important; }
  }

  /* --- COMPONENTS --- */
  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    height: 40px;
    z-index: 30; /* Ensure buttons are clickable */
  }
  .panel-header h3 { margin: 0; font-size: 1.1rem; color: #2dd4bf; }

  .btn {
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.2s;
    position: relative;
    z-index: 50; /* High z-index for clickability */
  }
  .btn:active { opacity: 0.8; }
  .btn-primary { background-color: #2dd4bf; color: #0f172a; }
  .btn-danger { background-color: #f43f5e; color: white; }
  .btn-sm { padding: 0.3rem 0.8rem; font-size: 0.8rem; }
  .btn-send { background-color: #2dd4bf; color: #0f172a; margin-left: 0.5rem; }

  .video-stage {
    flex: 1;
    background: #000;
    border-radius: 8px;
    position: relative;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10;
  }
  .remote-video { width: 100%; height: 100%; object-fit: contain; }
  .empty-state { color: #64748b; }
  .error-msg { background: #7f1d1d; color: #fca5a5; padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem; }

  .local-pip {
    position: absolute;
    bottom: 20px;
    left: 20px;
    width: 140px;
    height: 105px;
    background: #1e293b;
    border: 2px solid #2dd4bf;
    border-radius: 8px;
    overflow: hidden;
    z-index: 20;
  }
  .local-canvas { width: 100%; height: 100%; object-fit: cover; transform: scaleX(-1); }

  .asl-badge {
    position: absolute;
    top: 20px;
    right: 20px;
    background: rgba(45, 212, 191, 0.9);
    color: #0f172a;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-weight: bold;
    display: flex;
    flex-direction: column;
    align-items: center;
    z-index: 20;
  }
  .asl-text { font-size: 1.2rem; }
  .asl-conf { font-size: 0.75rem; opacity: 0.8; }

  .id-bar { display: flex; gap: 1rem; margin-bottom: 1rem; font-size: 0.8rem; color: #64748b; }
  .id-tag { background: #1e293b; padding: 0.2rem 0.5rem; border-radius: 4px; border: 1px solid #334155; }

  .chat-messages {
    flex: 1;
    background: #1e293b;
    border-radius: 8px;
    padding: 0.75rem;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    margin-bottom: 1rem;
  }
  .chat-empty { text-align: center; color: #64748b; margin-top: 2rem; font-style: italic; }

  .message { display: flex; gap: 0.5rem; align-items: flex-start; }
  .message.sys { justify-content: center; }
  .sys-text { font-size: 0.75rem; color: #64748b; }

  .avatar {
    width: 30px;
    height: 30px;
    border-radius: 50%;
    background: #2dd4bf;
    color: #0f172a;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 0.8rem;
    flex-shrink: 0;
  }
  .bubble { flex: 1; }
  .sender { font-size: 0.75rem; color: #94a3b8; margin-bottom: 2px; }
  .text { font-size: 0.9rem; line-height: 1.4; word-break: break-word; }

  .chat-input-area { display: flex; height: 40px; }
  .chat-input {
    flex: 1;
    background: #1e293b;
    border: 1px solid #334155;
    color: white;
    padding: 0.5rem;
    border-radius: 6px;
  }
  .chat-input:focus { outline: 1px solid #2dd4bf; }
`;