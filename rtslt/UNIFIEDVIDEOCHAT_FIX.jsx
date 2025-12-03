/**
 * EXACT CODE TO ADD TO UnifiedVideoChat.jsx
 * 
 * This is the complete fixed useEffect for ASL WebSocket
 * Replace the existing one with this version that includes debug logging
 */

// FIND THIS SECTION IN UnifiedVideoChat.jsx:
/*
  useEffect(() => {
    if (!joined || !videoActive) return;
    const wsUrl = `${WS_BASE}/ws/asl/`;
    const aslWs = new WebSocket(wsUrl);
    wsASLRef.current = aslWs;
    aslWs.onmessage = (evt) => {
*/

// REPLACE IT WITH THIS:

useEffect(() => {
  if (!joined || !videoActive) return;
  
  const wsUrl = `${WS_BASE}/ws/asl/`;
  console.log('[ASL] Connecting to:', wsUrl);
  
  const aslWs = new WebSocket(wsUrl);
  wsASLRef.current = aslWs;
  
  // ADD THESE HANDLERS:
  aslWs.onopen = () => {
    console.log('[ASL] ✓ Connected to WebSocket');
  };
  
  aslWs.onerror = (error) => {
    console.error('[ASL] ✗ Connection error:', error);
  };
  
  aslWs.onclose = () => {
    console.log('[ASL] Connection closed');
  };
  
  // KEEP THIS EXISTING HANDLER:
  aslWs.onmessage = (evt) => {
    try {
      const data = JSON.parse(evt.data);
      if (data.type === 'prediction') {
        console.log(`[ASL] ✓ PREDICTION RECEIVED: ${data.label} (${(data.confidence * 100).toFixed(1)}%)`);
        setLocalPrediction({ label: data.label, confidence: data.confidence });
        
        // Forward to chat WebSocket so peer sees it too
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
      console.error('[ASL] Parse error:', err);
    }
  };
  
  return () => { 
    if (aslWs && aslWs.readyState === WebSocket.OPEN) {
      aslWs.close();
    }
  };
}, [joined, videoActive, ws]);


// ============================================================================
// SECOND CHANGE: ADD LOGGING TO onResults FUNCTION
// ============================================================================

// FIND THIS IN THE onResults FUNCTION:
/*
    const now = performance.now();
    if (now - lastSentLandmarksRef.current > 100) {
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
*/

// REPLACE WITH THIS (ADDS 2 CONSOLE.LOG STATEMENTS):

    const now = performance.now();
    if (now - lastSentLandmarksRef.current > 100) {
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
        
        // ADD THIS DEBUG LINE:
        console.log(`[ASL] Landmarks ready (${all.length} hands), WS state: ${wsASLRef.current?.readyState}`);
        
        if (wsASLRef.current && wsASLRef.current.readyState === WebSocket.OPEN) {
          console.log(`[ASL] → Sending ${flat.length} landmark values...`);
          wsASLRef.current.send(JSON.stringify({ type: 'landmarks', landmarks: flat.slice(0, 126), has_hands: true }));
        } else {
          console.log(`[ASL] ✗ WebSocket not ready (state=${wsASLRef.current?.readyState})`);
        }
      } else {
        // No hands detected
        if (wsASLRef.current && wsASLRef.current.readyState === WebSocket.OPEN) {
          console.log(`[ASL] No hands - sending reset signal`);
          wsASLRef.current.send(JSON.stringify({ type: 'landmarks', landmarks: [], has_hands: false }));
        }
      }
      lastSentLandmarksRef.current = now;
    }


// ============================================================================
// EXPECTED BROWSER CONSOLE OUTPUT AFTER ADDING THESE LOGS
// ============================================================================

/*
When app loads:
  [ASL] Connecting to: wss://192.168.100.201:8000/ws/asl/

When connection succeeds:
  [ASL] ✓ Connected to WebSocket

When you show hand to camera (every 100ms):
  [ASL] Landmarks ready (1 hands), WS state: 1
  [ASL] → Sending 126 landmark values...

When backend sends prediction (every ~1 second):
  [ASL] ✓ PREDICTION RECEIVED: A (98.5%)
  [ASL] ✓ PREDICTION RECEIVED: B (99.2%)
  [ASL] ✓ PREDICTION RECEIVED: space (97.1%)

Expected pattern:
  [ASL] Connecting to: wss://...
  [ASL] ✓ Connected to WebSocket
  [ASL] Landmarks ready (1 hands), WS state: 1
  [ASL] → Sending 126 landmark values...
  [ASL] Landmarks ready (1 hands), WS state: 1
  [ASL] → Sending 126 landmark values...
  [ASL] Landmarks ready (1 hands), WS state: 1
  [ASL] → Sending 126 landmark values...
  [ASL] → Sending 126 landmark values...
  [ASL] ✓ PREDICTION RECEIVED: C (45.8%)
  [ASL] Landmarks ready (1 hands), WS state: 1
  [ASL] → Sending 126 landmark values...
  [ASL] ✓ PREDICTION RECEIVED: C (99.9%)
*/

// ============================================================================
// TROUBLESHOOTING BASED ON CONSOLE OUTPUT
// ============================================================================

/*
SCENARIO 1: Connection never shows "✓ Connected"
  Problem: WebSocket connection failing
  Check:
    - Is backend running? (python manage.py runserver)
    - Is port 8000 accessible?
    - Browser console for SSL/CORS errors
    - Is the IP/port correct in WS_BASE?

SCENARIO 2: Shows "✓ Connected" but no landmark sending
  Problem: onResults not being called or all.length = 0
  Check:
    - Is camera on? (button should say "Stop Camera")
    - Are hands visible? (should see green lines in video)
    - Is videoActive state true?

SCENARIO 3: Shows landmarks sending but no predictions
  Problem: Backend not receiving/processing landmarks
  Check:
    - Run: python verify_backend_ready.py (should pass)
    - Check Django server logs for [ASL] messages
    - Verify model is loading correctly

SCENARIO 4: Shows all green checkmarks but no UI update
  Problem: Prediction received but UI not updating
  Check:
    - Check if localPrediction state is being set
    - Check CSS - might be overlapping/hidden
    - Check if setLocalPrediction is working
*/
