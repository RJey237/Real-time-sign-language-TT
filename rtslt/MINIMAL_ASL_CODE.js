/**
 * MINIMAL EXAMPLE: Add this to your existing MediaPipe setup
 * 
 * This is the MINIMAL code needed to send landmarks to the ASL backend.
 * Add this to your App.jsx or UnifiedVideoChat.jsx
 */

// ============================================================================
// STEP 1: Add this WebSocket connection code
// ============================================================================

let aslWebSocket = null;

function connectASLWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const host = window.location.host;
  const url = `${protocol}://${host}/ws/asl/`;
  
  console.log('[ASL] Connecting to:', url);
  aslWebSocket = new WebSocket(url);
  
  aslWebSocket.onopen = () => {
    console.log('[ASL] Connected!');
  };
  
  aslWebSocket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'prediction') {
      console.log(`[ASL] DETECTED: ${data.label} (${(data.confidence * 100).toFixed(1)}%)`);
      // UPDATE YOUR UI HERE with data.label
    } else {
      console.log('[ASL]', data);
    }
  };
  
  aslWebSocket.onerror = (e) => console.error('[ASL] Error:', e);
}

// ============================================================================
// STEP 2: Add this function to extract landmarks from MediaPipe results
// ============================================================================

function extractLandmarks(results) {
  if (!results.multiHandLandmarks || results.multiHandLandmarks.length === 0) {
    return null; // No hands
  }
  
  const landmarks = [];
  
  // Process up to 2 hands
  for (let h = 0; h < 2; h++) {
    if (h < results.multiHandLandmarks.length) {
      // Hand detected - extract its 21 landmarks (x, y, z each)
      const hand = results.multiHandLandmarks[h];
      for (let i = 0; i < 21; i++) {
        landmarks.push(hand[i].x);
        landmarks.push(hand[i].y);
        landmarks.push(hand[i].z);
      }
    } else {
      // No hand here - fill with zeros
      for (let i = 0; i < 63; i++) {
        landmarks.push(0);
      }
    }
  }
  
  return landmarks; // Should be 126 values
}

// ============================================================================
// STEP 3: Add this function to send landmarks
// ============================================================================

let lastSendTime = 0;

function sendLandmarks(results) {
  if (!aslWebSocket || aslWebSocket.readyState !== WebSocket.OPEN) {
    return;
  }
  
  // Throttle to ~20 Hz (send every 50ms)
  const now = Date.now();
  if (now - lastSendTime < 50) {
    return;
  }
  
  const landmarks = extractLandmarks(results);
  const hasHands = landmarks !== null;
  
  const message = {
    type: 'landmarks',
    landmarks: landmarks || Array(126).fill(0),
    has_hands: hasHands
  };
  
  aslWebSocket.send(JSON.stringify(message));
  lastSendTime = now;
}

// ============================================================================
// STEP 4: In your React component - call these functions
// ============================================================================

/*
  In your App.jsx or UnifiedVideoChat.jsx:

  useEffect(() => {
    // Connect to ASL on mount
    connectASLWebSocket();
    
    return () => {
      if (aslWebSocket) aslWebSocket.close();
    };
  }, []);

  // In your Hands.onResults() callback:
  hands.onResults((results) => {
    // ... your existing drawing code ...
    
    // ADD THIS LINE:
    sendLandmarks(results);
  });
*/

// ============================================================================
// Expected Console Output:
// ============================================================================

/*
[ASL] Connecting to: wss://192.168.100.201:8000/ws/asl/
[ASL] Connected!
[ASL] DETECTED: A (98.5%)
[ASL] DETECTED: B (99.2%)
[ASL] DETECTED: space (97.1%)
*/
