import React, { useEffect, useRef, useState } from 'react';

const HOST = typeof window !== 'undefined' ? window.location.hostname : 'localhost'
const BACKEND_HOST = HOST === 'localhost' ? '127.0.0.1' : HOST
const WS_PROTOCOL = window.location.protocol === 'https:' ? 'wss:' : 'ws:';

export default function VideoChat({ targetId, myId, isConnected }) {
  const localVideoRef = useRef(null);
  const remoteVideoRef = useRef(null);
  const wsRef = useRef(null);
  const [localStream, setLocalStream] = useState(null);
  const [videoActive, setVideoActive] = useState(false);
  const [error, setError] = useState(null);
  const [wsStatus, setWsStatus] = useState('idle');
  const canvasRef = useRef(null);
  const animationFrameRef = useRef(null);

  // Start local video stream
  useEffect(() => {
    if (!videoActive || !targetId || !myId) {
      console.log('Video prerequisites not met:', { videoActive, targetId, myId });
      return;
    }

    console.log('Starting video with:', { targetId, myId });

    const startVideo = async () => {
      try {
        console.log('Requesting camera access...');
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 640 }, height: { ideal: 480 } },
          audio: false
        });
        console.log('Camera stream acquired:', stream);
        setLocalStream(stream);
        if (localVideoRef.current) {
          localVideoRef.current.srcObject = stream;
          console.log('Video stream attached to element');
        }
        setError(null);
      } catch (err) {
        console.error('Camera error:', err);
        setError(`Camera access failed: ${err.message}`);
        setVideoActive(false);
      }
    };

    startVideo();

    return () => {
      console.log('Cleaning up video stream');
      if (localStream) {
        localStream.getTracks().forEach(track => track.stop());
      }
    };
  }, [videoActive, targetId, myId]);

  // WebSocket for video frames
  useEffect(() => {
    if (!videoActive || !targetId || !myId || !localStream) {
      console.log('WS prerequisites not met:', { videoActive, targetId, myId, hasStream: !!localStream });
      return;
    }

    const wsUrl = `${WS_PROTOCOL}//${BACKEND_HOST}:8000/ws/video/${targetId}/?self=${myId}`;
    console.log('Connecting to WebSocket:', wsUrl);
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('Video WebSocket connected');
      setWsStatus('connected');
      startSendingFrames();
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'frame' && data.frame_data) {
          displayRemoteFrame(data.frame_data);
        }
      } catch (err) {
        console.error('Video message error:', err);
      }
    };

    ws.onerror = (err) => {
      console.error('Video WebSocket error:', err);
      setWsStatus('error');
      setError('Video connection error: ' + err.message);
    };

    ws.onclose = () => {
      console.log('Video WebSocket closed');
      setWsStatus('closed');
    };

    return () => {
      console.log('Closing WebSocket');
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [videoActive, targetId, myId, localStream]);

  const startSendingFrames = () => {
    console.log('Starting frame transmission...');
    let lastSendTime = 0;
    const MIN_FRAME_INTERVAL = 100; // ~10 FPS
    
    const sendFrame = () => {
      if (!localVideoRef.current || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        if (wsRef.current?.readyState !== WebSocket.OPEN) {
          console.log('WS not ready:', wsRef.current?.readyState);
        }
        animationFrameRef.current = requestAnimationFrame(sendFrame);
        return;
      }

      const now = Date.now();
      if (now - lastSendTime < MIN_FRAME_INTERVAL) {
        animationFrameRef.current = requestAnimationFrame(sendFrame);
        return;
      }

      const video = localVideoRef.current;
      const canvas = canvasRef.current;
      if (!canvas || !video.videoWidth) {
        console.log('Canvas or video not ready:', { canvas: !!canvas, videoWidth: video.videoWidth });
        animationFrameRef.current = requestAnimationFrame(sendFrame);
        return;
      }

      try {
        const ctx = canvas.getContext('2d');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0);

        // Send as base64
        const frameData = canvas.toDataURL('image/jpeg', 0.7);
        wsRef.current.send(JSON.stringify({
          type: 'frame',
          frame_data: frameData
        }));
        lastSendTime = now;
      } catch (err) {
        console.error('Error sending frame:', err);
      }

      animationFrameRef.current = requestAnimationFrame(sendFrame);
    };

    animationFrameRef.current = requestAnimationFrame(sendFrame);
  };

  const displayRemoteFrame = (frameDataUrl) => {
    if (remoteVideoRef.current) {
      const img = new Image();
      img.src = frameDataUrl;
      img.onload = () => {
        remoteVideoRef.current.width = img.width;
        remoteVideoRef.current.height = img.height;
        const ctx = remoteVideoRef.current.getContext('2d');
        ctx.clearRect(0, 0, remoteVideoRef.current.width, remoteVideoRef.current.height);
        ctx.drawImage(img, 0, 0);
      };
      img.onerror = () => {
        console.error('Failed to load frame image');
      };
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h3>📹 Video Chat</h3>
        {!videoActive ? (
          <button 
            onClick={() => setVideoActive(true)} 
            style={styles.startBtn}
            disabled={!targetId || !myId}
          >
            Start Video
          </button>
        ) : (
          <button onClick={() => setVideoActive(false)} style={styles.stopBtn}>
            Stop Video
          </button>
        )}
      </div>

      {error && <div style={styles.error}>{error}</div>}

      {wsStatus !== 'idle' && (
        <div style={styles.debugInfo}>
          WS Status: <strong>{wsStatus}</strong> | Camera: <strong>{localStream ? 'ON' : 'OFF'}</strong>
        </div>
      )}

      {!targetId || !myId ? (
        <div style={styles.info}>Enter both your ID and peer's ID to start video</div>
      ) : videoActive ? (
        <div style={styles.videoGrid}>
          <div style={styles.videoBox}>
            <div style={styles.label}>Your Camera</div>
            <video
              ref={localVideoRef}
              autoPlay
              playsInline
              muted
              style={styles.video}
            />
          </div>
          <div style={styles.videoBox}>
            <div style={styles.label}>Peer's Camera</div>
            <canvas
              ref={remoteVideoRef}
              style={styles.video}
            />
          </div>
        </div>
      ) : null}

      <canvas ref={canvasRef} style={{ display: 'none' }} />
    </div>
  );
}

const styles = {
  container: {
    padding: '1rem',
    backgroundColor: '#1e2d3d',
    borderRadius: '8px',
    marginBottom: '1rem',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1rem',
  },
  startBtn: {
    padding: '0.5rem 1rem',
    backgroundColor: '#10b981',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.9rem',
  },
  stopBtn: {
    padding: '0.5rem 1rem',
    backgroundColor: '#ef4444',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.9rem',
  },
  error: {
    padding: '0.5rem',
    backgroundColor: '#7f1d1d',
    color: '#fca5a5',
    borderRadius: '4px',
    marginBottom: '1rem',
    fontSize: '0.9rem',
  },
  info: {
    padding: '1rem',
    backgroundColor: '#1b4965',
    color: '#90e0ef',
    borderRadius: '4px',
    marginTop: '1rem',
    fontSize: '0.9rem',
    textAlign: 'center',
  },
  debugInfo: {
    padding: '0.5rem',
    backgroundColor: '#1b1f35',
    color: '#94a3b8',
    borderRadius: '4px',
    marginTop: '0.5rem',
    fontSize: '0.8rem',
    fontFamily: 'monospace',
  },
  videoGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '1rem',
    marginTop: '1rem',
  },
  videoBox: {
    backgroundColor: '#0b1220',
    borderRadius: '8px',
    overflow: 'hidden',
    border: '1px solid #334155',
    position: 'relative',
  },
  video: {
    width: '100%',
    height: '300px',
    objectFit: 'cover',
    backgroundColor: '#000',
    display: 'block',
  },
  label: {
    position: 'absolute',
    top: '0.5rem',
    left: '0.5rem',
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    color: '#e5e7eb',
    padding: '0.25rem 0.5rem',
    borderRadius: '4px',
    fontSize: '0.8rem',
    zIndex: 10,
  },
};
