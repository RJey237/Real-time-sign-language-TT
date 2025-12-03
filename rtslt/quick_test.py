"""
Quick test of sign detection - Run this to verify fixes work
"""
import cv2
import mediapipe as mp
import numpy as np
import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ml_models.inference import ASLPredictor

def quick_test():
    print("=" * 80)
    print("QUICK SIGN DETECTION TEST")
    print("=" * 80)
    print("\n✅ FIXES APPLIED:")
    print("  1. Removed [-1, 1] normalization (now keeps [0, 1])")
    print("  2. Lowered confidence threshold from 0.65 to 0.5")
    print("  3. Removed strict voting requirement (now 1 match instead of 2)")
    print("  4. WebSocket threshold lowered to 0.5\n")
    
    # Load model and MediaPipe
    print("📥 Loading model and MediaPipe...")
    try:
        predictor = ASLPredictor(
            model_path='ml_models/saved_models/baseline_mlp.pkl',
            label_encoder_path=None,  # Encoder is inside pickle
            model_type='mlp'
        )
        print("✅ Model loaded\n")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return
    
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.3
    )
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Cannot open camera!")
        return
    
    print("🎥 Camera opened. Starting detection...")
    print("   Try different hand signs (A, B, C, etc.)")
    print("   Press 'q' to exit\n")
    
    frame_count = 0
    prediction_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        h, w, c = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)
        
        frame_count += 1
        status_text = ""
        
        if results.multi_hand_landmarks:
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
                prediction_count += 1
                status_text = f"✅ {label} ({confidence:.2f})"
                print(f"Frame {frame_count}: PREDICTED '{label}' confidence={confidence:.2f}")
            else:
                status_text = "⏳ Buffering... (need 10 frames)"
            
            # Draw landmarks
            for hand_landmarks in results.multi_hand_landmarks:
                for landmark in hand_landmarks.landmark:
                    x = int(landmark.x * w)
                    y = int(landmark.y * h)
                    cv2.circle(frame, (x, y), 4, (0, 255, 0), -1)
        else:
            status_text = "🔍 No hands detected"
        
        # Display info
        cv2.putText(frame, status_text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0) if "✅" in status_text else (0, 165, 255), 2)
        cv2.putText(frame, f"Frames: {frame_count} | Predictions: {prediction_count}", (10, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
        
        cv2.imshow("Sign Detection", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    hands.close()
    
    print(f"\n{'='*80}")
    print(f"✅ Test complete!")
    print(f"   Total frames: {frame_count}")
    print(f"   Predictions made: {prediction_count}")
    print(f"   Success rate: {prediction_count/max(frame_count, 1)*100:.1f}%")
    print(f"{'='*80}")
    
    if prediction_count == 0:
        print("\n⚠️  No predictions made. Try:")
        print("   • Better lighting")
        print("   • Clearer hand gestures")
        print("   • Hold hand in view for 2+ seconds")
    elif prediction_count < frame_count * 0.1:
        print("\n⚠️  Low prediction rate. Model might need retraining on live data")
    else:
        print("\n✅ Detection working! Signs are being recognized")

if __name__ == "__main__":
    quick_test()
