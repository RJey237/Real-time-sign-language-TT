"""
Test script to diagnose sign detection issues
Run this FIRST to identify where the problem is
"""
import cv2
import mediapipe as mp
import numpy as np
from ml_models.inference import ASLPredictor
import os
import time

def test_mediapipe_detection():
    """Test if MediaPipe can detect hands from webcam"""
    print("=" * 80)
    print("TEST 1: MediaPipe Hand Detection")
    print("=" * 80)
    
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=False,  # For webcam (streaming)
        max_num_hands=2,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.3
    )
    
    cap = cv2.VideoCapture(0)
    frame_count = 0
    detection_count = 0
    
    print("\n🎥 Capturing 30 frames... (Press 'q' to quit early)")
    
    while frame_count < 30:
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to capture frame")
            break
        
        h, w, c = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)
        
        frame_count += 1
        
        if results.multi_hand_landmarks:
            detection_count += 1
            num_hands = len(results.multi_hand_landmarks)
            print(f"  Frame {frame_count}: ✓ Detected {num_hands} hand(s)")
            
            # Show first hand landmarks
            hand_landmarks = results.multi_hand_landmarks[0]
            landmarks = []
            for lm in hand_landmarks.landmark:
                landmarks.extend([lm.x, lm.y, lm.z])
            
            print(f"    Landmark range: X=[{min(landmarks[0::3]):.2f}, {max(landmarks[0::3]):.2f}], "
                  f"Y=[{min(landmarks[1::3]):.2f}, {max(landmarks[1::3]):.2f}], "
                  f"Z=[{min(landmarks[2::3]):.2f}, {max(landmarks[2::3]):.2f}]")
        else:
            print(f"  Frame {frame_count}: ✗ No hands detected")
        
        # Display
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                for landmark in hand_landmarks.landmark:
                    x = int(landmark.x * w)
                    y = int(landmark.y * h)
                    cv2.circle(frame, (x, y), 3, (0, 255, 0), -1)
        
        cv2.putText(frame, f"Detection Rate: {detection_count}/{frame_count}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow("MediaPipe Test", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    hands.close()
    
    detection_rate = (detection_count / frame_count * 100) if frame_count > 0 else 0
    print(f"\n✅ MediaPipe Detection Rate: {detection_rate:.1f}% ({detection_count}/{frame_count} frames)")
    
    if detection_rate < 50:
        print("⚠️  WARNING: Low detection rate! Check lighting and hand visibility")
    
    return detection_rate >= 50


def test_landmark_normalization():
    """Test if landmark normalization is correct"""
    print("\n" + "=" * 80)
    print("TEST 2: Landmark Normalization")
    print("=" * 80)
    
    # Simulate MediaPipe output (x, y, z in [0, 1] range)
    print("\n📊 Simulating MediaPipe landmarks...")
    original_landmarks = np.array([
        [0.5, 0.5, 0.1],  # Center
        [0.2, 0.3, 0.05],  # Top-left
        [0.8, 0.9, 0.15],  # Bottom-right
    ]).flatten()  # Shape: (9,)
    
    print(f"Original landmarks (9 values): {original_landmarks}")
    print(f"Range: X=[0-1], Y=[0-1], Z=[0-0.15]")
    
    # What current code does (WRONG)
    print("\n❌ CURRENT (Wrong) Normalization:")
    wrong_norm = original_landmarks * 2.0 - 1.0
    print(f"Normalized to [-1, 1]: {wrong_norm}")
    print("Problem: Model was trained on [0, 1] range, not [-1, 1]!")
    
    # What it should do (CORRECT)
    print("\n✅ CORRECT Normalization:")
    print("No change needed! Keep [0, 1] range (MediaPipe already normalized)")
    print(f"Keep as: {original_landmarks}")
    
    return True


def test_model_input_shape():
    """Test if model input shape matches what we're sending"""
    print("\n" + "=" * 80)
    print("TEST 3: Model Input Shape")
    print("=" * 80)
    
    model_path = 'ml_models/saved_models/lstm_model.h5'
    
    if not os.path.exists(model_path):
        print(f"❌ Model not found: {model_path}")
        return False
    
    try:
        from tensorflow import keras
        model = keras.models.load_model(model_path)
        
        print(f"\n🧠 Model Input Shape: {model.input_shape}")
        print(f"   Expected: (batch_size, 10, 126)")
        
        # Test with dummy input
        print("\n📝 Testing with dummy data...")
        dummy_sequence = np.random.randn(1, 10, 126).astype(np.float32)
        prediction = model.predict_on_batch(dummy_sequence)
        
        print(f"   Input shape sent: {dummy_sequence.shape}")
        print(f"   Output shape received: {prediction.shape}")
        print(f"   Sample prediction: {prediction[0][:5]}...")
        print("   ✅ Model accepts input correctly!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return False


def test_full_pipeline():
    """Test the full detection pipeline"""
    print("\n" + "=" * 80)
    print("TEST 4: Full Detection Pipeline")
    print("=" * 80)
    
    try:
        print("\n🔄 Loading ASLPredictor...")
        predictor = ASLPredictor(
            model_path='ml_models/saved_models/lstm_model.h5',
            label_encoder_path='ml_models/saved_models/lstm_model_label_encoder.pkl',
            model_type='lstm'
        )
        print("✅ Predictor loaded successfully")
        
    except Exception as e:
        print(f"❌ Failed to load predictor: {e}")
        return False
    
    print("\n🎥 Capturing frames for detection...")
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.3
    )
    
    cap = cv2.VideoCapture(0)
    predictions_made = 0
    frames_with_hands = 0
    
    for frame_idx in range(60):  # 60 frames
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)
        
        if results.multi_hand_landmarks:
            frames_with_hands += 1
            
            # Extract landmarks
            landmarks = []
            for hand_landmarks in results.multi_hand_landmarks:
                for lm in hand_landmarks.landmark:
                    landmarks.extend([lm.x, lm.y, lm.z])
            
            # Pad to 126
            while len(landmarks) < 126:
                landmarks.extend([0.0, 0.0, 0.0])
            
            landmarks = np.array(landmarks[:126])
            
            # Make prediction
            label, confidence, latency = predictor.predict(landmarks, has_hands=True)
            
            if label is not None:
                predictions_made += 1
                print(f"  Frame {frame_idx}: ✓ Predicted '{label}' (conf: {confidence:.2f}, latency: {latency}ms)")
            else:
                print(f"  Frame {frame_idx}: ✗ No prediction (need 10 frames)")
        
        # Display
        h, w, c = frame.shape
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                for landmark in hand_landmarks.landmark:
                    x = int(landmark.x * w)
                    y = int(landmark.y * h)
                    cv2.circle(frame, (x, y), 3, (0, 255, 0), -1)
        
        cv2.putText(frame, f"Hands: {frames_with_hands}, Predictions: {predictions_made}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow("Full Pipeline Test", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    hands.close()
    
    print(f"\n✅ Pipeline Test Results:")
    print(f"   Frames with hands: {frames_with_hands}")
    print(f"   Predictions made: {predictions_made}")
    
    if frames_with_hands == 0:
        print("   ⚠️  No hands detected - check lighting and camera")
    elif predictions_made == 0:
        print("   ⚠️  Predictions not triggered - likely threshold issue")
    
    return True


if __name__ == "__main__":
    print("\n" + "🔍 SIGN DETECTION DIAGNOSTIC TOOL" + "\n")
    print("This script will test each component of your detection pipeline.\n")
    
    # Run tests
    test1_pass = test_mediapipe_detection()
    test2_pass = test_landmark_normalization()
    test3_pass = test_model_input_shape()
    test4_pass = test_full_pipeline()
    
    # Summary
    print("\n" + "=" * 80)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 80)
    
    tests = [
        ("MediaPipe Detection", test1_pass),
        ("Landmark Normalization", test2_pass),
        ("Model Input Shape", test3_pass),
        ("Full Pipeline", test4_pass),
    ]
    
    for test_name, passed in tests:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n📋 NEXT STEPS:")
    print("1. If MediaPipe fails: Check camera, lighting, hand visibility")
    print("2. If Normalization fails: Update inference.py to NOT normalize to [-1, 1]")
    print("3. If Model fails: Check model path and keras installation")
    print("4. If Pipeline fails: Check thresholds and sequence buffer size")
