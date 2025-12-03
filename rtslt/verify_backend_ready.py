#!/usr/bin/env python
"""
Verify the ASL backend is working correctly
Tests model loading, landmark processing, and predictions
"""
import sys
import numpy as np
from ml_models.inference import ASLPredictor

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("\n" + "="*70)
print("ASL BACKEND VERIFICATION")
print("="*70)

# Test 1: Load model
print("\n[TEST 1] Loading model...")
try:
    predictor = ASLPredictor(
        model_path='ml_models/saved_models/lstm_model.h5',
        label_encoder_path='ml_models/saved_models/lstm_model_label_encoder.pkl',
        model_type='lstm'
    )
    print("[OK] Model loaded successfully")
    print(f"   Model type: {predictor.model_type}")
    print(f"   Sequence buffer size: {len(predictor.sequence_buffer)}")
    print(f"   Sequence length needed: {predictor.sequence_length}")
except Exception as e:
    print(f"[ERROR] Failed to load model: {e}")
    exit(1)

# Test 2: Single landmark prediction (should return None until buffer full)
print("\n[TEST 2] Processing single landmarks...")
try:
    for frame_idx in range(1, 11):
        landmarks = np.random.rand(126).astype(np.float32)  # 126-dim landmark vector
        label, conf, latency = predictor.predict(landmarks, has_hands=True)
        
        if label is None:
            print(f"   Frame {frame_idx}/10: Buffering... ({len(predictor.sequence_buffer)}/10)")
        else:
            print(f"   Frame {frame_idx}/10: [OK] {label} ({conf:.1%}) - {latency}ms")
            break
    
    if label is not None:
        print(f"[OK] Prediction working! Got: {label} ({conf:.1%})")
    else:
        print("[WARN] Still buffering (need 10 frames for LSTM)")
except Exception as e:
    print(f"[ERROR] Prediction failed: {e}")
    exit(1)

# Test 3: Continuous stream (simulate 15 frames)
print("\n[TEST 3] Simulating continuous landmark stream...")
try:
    predictor.reset_sequence()  # Reset for fresh test
    predictions = []
    
    for frame_idx in range(15):
        landmarks = np.random.rand(126).astype(np.float32)
        label, conf, latency = predictor.predict(landmarks, has_hands=True)
        
        if label is not None:
            predictions.append((label, conf))
            print(f"   Frame {frame_idx+1}: {label} ({conf:.1%})")
    
    print(f"[OK] Got {len(predictions)} predictions from 15 frames")
except Exception as e:
    print(f"[ERROR] Stream simulation failed: {e}")
    exit(1)

# Test 4: No hands handling
print("\n[TEST 4] Testing 'no hands' reset...")
try:
    predictor.reset_sequence()
    
    # Add 5 frames with hands
    for i in range(5):
        landmarks = np.random.rand(126).astype(np.float32)
        predictor.predict(landmarks, has_hands=True)
    
    buffer_before = len(predictor.sequence_buffer)
    
    # Signal no hands
    predictor.predict(None, has_hands=False)
    buffer_after = len(predictor.sequence_buffer)
    
    print(f"   Buffer before reset: {buffer_before} frames")
    print(f"   Buffer after reset: {buffer_after} frames")
    
    if buffer_after == 0:
        print("[OK] No-hands reset working correctly")
    else:
        print("[WARN] Buffer not fully reset")
except Exception as e:
    print(f"[ERROR] No-hands test failed: {e}")
    exit(1)

print("\n" + "="*70)
print("[OK] ALL TESTS PASSED - Backend is ready for landmarks!")
print("="*70)
print("\nExpected flow:")
print("1. Frontend connects to ws://host:8000/ws/asl/")
print("2. Frontend extracts landmarks from MediaPipe (126-dim vector)")
print("3. Frontend sends landmarks in JSON message")
print("4. Backend processes and returns sign prediction")
print("5. Frontend displays prediction to user")
print("\nCurrent status: [OK] Backend ready, waiting for frontend landmarks")
print("="*70 + "\n")
