"""
Simple camera test - no models needed
"""
import cv2

print("Testing camera access...")
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Camera NOT opened!")
    print("   Possible causes:")
    print("   1. Camera is in use by another application")
    print("   2. Camera driver not installed")
    print("   3. No webcam available")
    print("   4. Wrong camera index (try 1, 2, etc. instead of 0)")
else:
    print("✅ Camera opened successfully!")
    print(f"   Resolution: {cap.get(cv2.CAP_PROP_FRAME_WIDTH)} x {cap.get(cv2.CAP_PROP_FRAME_HEIGHT)}")
    
    # Try to capture a frame
    for i in range(5):
        ret, frame = cap.read()
        if ret:
            print(f"   Frame {i+1}: ✅ Captured")
        else:
            print(f"   Frame {i+1}: ❌ Failed")
    
    cap.release()
    print("\n✅ Camera test complete!")
