/**
 * DIAGNOSTIC: Check if ASL WebSocket is connecting
 * 
 * Add this to UnifiedVideoChat.jsx to debug the ASL connection
 */

// In the useEffect where ASLRef is created, add this logging:

useEffect(() => {
  if (!joined || !videoActive) return;
  
  const wsUrl = `${WS_BASE}/ws/asl/`;
  console.log(`[ASL-DEBUG] Attempting to connect to: ${wsUrl}`);
  console.log(`[ASL-DEBUG] WS_BASE: ${WS_BASE}`);
  console.log(`[ASL-DEBUG] joined: ${joined}, videoActive: ${videoActive}`);
  
  const aslWs = new WebSocket(wsUrl);
  wsASLRef.current = aslWs;
  
  aslWs.onopen = () => {
    console.log(`[ASL-DEBUG] WebSocket CONNECTED to ${wsUrl}`);
  };
  
  aslWs.onmessage = (evt) => {
    try {
      const data = JSON.parse(evt.data);
      console.log(`[ASL-DEBUG] Received message:`, data);
      
      if (data.type === 'prediction') {
        console.log(`[ASL-DEBUG] Got prediction: ${data.label} (${data.confidence})`);
        setLocalPrediction({ label: data.label, confidence: data.confidence });
        
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({
            type: 'asl_prediction',
            label: data.label,
            confidence: data.confidence
          }));
        }
        
        window.dispatchEvent(new CustomEvent('asl-prediction-local', {
          detail: { label: data.label, confidence: data.confidence }
        }));
      }
    } catch (err) {
      console.error(`[ASL-DEBUG] Error parsing message:`, err);
    }
  };
  
  aslWs.onerror = (error) => {
    console.error(`[ASL-DEBUG] WebSocket ERROR:`, error);
  };
  
  aslWs.onclose = () => {
    console.log(`[ASL-DEBUG] WebSocket CLOSED`);
  };
  
  return () => {
    if (aslWs && aslWs.readyState === WebSocket.OPEN) {
      console.log(`[ASL-DEBUG] Closing ASL WebSocket`);
      aslWs.close();
    }
  };
}, [joined, videoActive, ws]);


// Also add logging to the landmark sending:

const onResults = (results) => {
  // ... existing code ...
  
  const now = performance.now();
  if (now - lastSentLandmarksRef.current > 100) {
    if (all.length > 0) {
      const flat = [];
      for (let h = 0; h < Math.min(2, all.length); h++) {
        const lm = all[h];
        for (let i = 0; i < lm.length; i++) {
          flat.push(lm[i].x, lm[i].y, lm[i].z ?? 0);
        }
      }
      while (flat.length < 126) flat.push(0);
      
      if (wsASLRef.current) {
        console.log(`[ASL-DEBUG] ASL WS state: ${wsASLRef.current.readyState} (OPEN=1), sending landmarks...`);
      } else {
        console.log(`[ASL-DEBUG] wsASLRef.current is null/undefined`);
      }
      
      if (wsASLRef.current && wsASLRef.current.readyState === WebSocket.OPEN) {
        console.log(`[ASL-DEBUG] Sending ${flat.length} landmarks, has_hands: true`);
        wsASLRef.current.send(JSON.stringify({ 
          type: 'landmarks', 
          landmarks: flat.slice(0, 126), 
          has_hands: true 
        }));
      } else {
        console.log(`[ASL-DEBUG] WebSocket not ready (state: ${wsASLRef.current?.readyState})`);
      }
    } else {
      console.log(`[ASL-DEBUG] No hands detected`);
      if (wsASLRef.current && wsASLRef.current.readyState === WebSocket.OPEN) {
        wsASLRef.current.send(JSON.stringify({ 
          type: 'landmarks', 
          landmarks: [], 
          has_hands: false 
        }));
      }
    }
    lastSentLandmarksRef.current = now;
  }
};
