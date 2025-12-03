/**
 * REFERENCE IMPLEMENTATION: How to send landmarks to ASL prediction WebSocket
 * 
 * This shows the EXACT code needed in your frontend to send hand landmarks
 * to the backend for real-time ASL sign detection.
 * 
 * Key points:
 * 1. Extract landmarks from MediaPipe
 * 2. Flatten them to 126-dim array
 * 3. Send to ASL WebSocket endpoint
 * 4. Listen for prediction responses
 */

class ASLLandmarkSender {
  constructor() {
    this.aslWebSocket = null;
    this.landmarkBuffer = [];
    this.maxBufferSize = 10;
    this.throttleMs = 50; // Send every 50ms max
    this.lastSendTime = 0;
    this.shouldSendLandmarks = true;
    
    console.log('[ASL] Initializing ASL Landmark Sender');
  }

  /**
   * Connect to the ASL WebSocket endpoint
   * Call this ONCE during app initialization
   */
  connectToASLWebSocket() {
    // Use WSS (secure) if HTTPS, WS if HTTP
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const host = window.location.host; // 192.168.100.201:8000
    const url = `${protocol}://${host}/ws/asl/`;
    
    console.log(`[ASL] Connecting to ${url}`);
    
    this.aslWebSocket = new WebSocket(url);
    
    this.aslWebSocket.onopen = () => {
      console.log('[ASL] Connected to ASL WebSocket');
    };
    
    this.aslWebSocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'prediction') {
        console.log(`[ASL] PREDICTION: ${data.label} (${(data.confidence * 100).toFixed(1)}%)`);
        this.onPredictionReceived(data);
      } else if (data.type === 'connection') {
        console.log(`[ASL] ${data.message}`);
      } else if (data.type === 'error') {
        console.error(`[ASL] Error: ${data.message}`);
      }
    };
    
    this.aslWebSocket.onerror = (error) => {
      console.error('[ASL] WebSocket error:', error);
    };
    
    this.aslWebSocket.onclose = () => {
      console.log('[ASL] Disconnected from ASL WebSocket');
    };
  }

  /**
   * Extract 126-dimensional landmark vector from MediaPipe hands results
   * 
   * @param {MediaPipeResults} results - Results from Hands.onResults()
   * @returns {Array<number>} 126-dim array or null if no hands
   */
  extractLandmarks(results) {
    if (!results.multiHandLandmarks || results.multiHandLandmarks.length === 0) {
      return null; // No hands detected
    }

    const landmarks = [];

    // Expected: 2 hands max, 21 landmarks per hand, 3 coords (x, y, z) per landmark
    // = 2 * 21 * 3 = 126 dimensions
    
    for (let handIdx = 0; handIdx < 2; handIdx++) {
      if (handIdx < results.multiHandLandmarks.length) {
        // Hand detected
        const handLandmarks = results.multiHandLandmarks[handIdx];
        for (let i = 0; i < 21; i++) {
          const lm = handLandmarks[i];
          landmarks.push(lm.x);
          landmarks.push(lm.y);
          landmarks.push(lm.z);
        }
      } else {
        // Hand NOT detected - fill with zeros
        for (let i = 0; i < 21 * 3; i++) {
          landmarks.push(0);
        }
      }
    }

    return landmarks; // Should be exactly 126 values
  }

  /**
   * Send landmarks to ASL WebSocket
   * Call this in your MediaPipe onResults callback
   * 
   * @param {MediaPipeResults} results - From Hands.onResults()
   */
  sendLandmarks(results) {
    if (!this.aslWebSocket || this.aslWebSocket.readyState !== WebSocket.OPEN) {
      return; // Not connected
    }

    const now = Date.now();
    if (now - this.lastSendTime < this.throttleMs) {
      return; // Too soon, throttle
    }

    const landmarks = this.extractLandmarks(results);
    const hasHands = landmarks !== null;
    
    if (!hasHands) {
      landmarks = Array(126).fill(0); // Send zeros if no hands
    }

    const message = {
      type: 'landmarks',
      landmarks: landmarks,
      has_hands: hasHands
    };

    try {
      this.aslWebSocket.send(JSON.stringify(message));
      this.lastSendTime = now;
      
      // Uncomment for debugging:
      // console.log(`[ASL] Sent landmarks (has_hands: ${hasHands})`);
    } catch (error) {
      console.error('[ASL] Error sending landmarks:', error);
    }
  }

  /**
   * Handle prediction received from backend
   * Override this in your app to display/use predictions
   */
  onPredictionReceived(data) {
    const { label, confidence, latency } = data;
    console.log(`[ASL] Sign detected: ${label} (${(confidence * 100).toFixed(1)}%) - latency: ${latency}ms`);
    
    // TODO: Update your UI with the prediction
    // Example:
    // document.getElementById('prediction-label').textContent = label;
    // document.getElementById('prediction-confidence').textContent = `${(confidence * 100).toFixed(1)}%`;
  }

  /**
   * Reset the ASL buffer (call when hands are not detected)
   */
  reset() {
    if (!this.aslWebSocket || this.aslWebSocket.readyState !== WebSocket.OPEN) {
      return;
    }

    const message = { type: 'reset' };
    try {
      this.aslWebSocket.send(JSON.stringify(message));
      console.log('[ASL] Reset sent');
    } catch (error) {
      console.error('[ASL] Error sending reset:', error);
    }
  }

  /**
   * Disconnect from ASL WebSocket
   */
  disconnect() {
    if (this.aslWebSocket) {
      this.aslWebSocket.close();
      this.aslWebSocket = null;
    }
  }
}

// ============================================================================
// EXAMPLE USAGE IN YOUR APP
// ============================================================================

/*
// In your App.jsx or main component:

import { useEffect, useRef } from 'react';

export default function App() {
  const aslSender = useRef(new ASLLandmarkSender());

  useEffect(() => {
    // 1. Connect to ASL WebSocket on app load
    aslSender.current.connectToASLWebSocket();

    return () => {
      // Cleanup on unmount
      aslSender.current.disconnect();
    };
  }, []);

  // 2. In your MediaPipe Hands callback:
  const handleMediaPipeResults = (results) => {
    // ... existing MediaPipe code ...

    // Send landmarks to ASL for prediction
    aslSender.current.sendLandmarks(results);
  };

  // 3. Set up MediaPipe Hands:
  useEffect(() => {
    const hands = new Hands({
      locateFile: (file) => {
        return `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`;
      },
    });

    hands.setOptions({
      maxNumHands: 2,
      modelComplexity: 1,
      minDetectionConfidence: 0.5,
      minTrackingConfidence: 0.5,
    });

    hands.onResults(handleMediaPipeResults);

    // ... camera setup ...
  }, []);

  return (
    <div>
      {/* Your existing UI */}
      <div id="prediction-label">Waiting for sign...</div>
      <div id="prediction-confidence"></div>
    </div>
  );
}
*/
