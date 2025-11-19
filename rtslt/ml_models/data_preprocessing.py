"""
Data preprocessing and landmark extraction using MediaPipe
"""

import numpy as np
import cv2
import mediapipe as mp
import os
import pickle
from tqdm import tqdm


class LandmarkExtractor:
    """Extract hand landmarks using MediaPipe"""
    
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=True,
            max_num_hands=2,
            min_detection_confidence=0.5
        )
    
    def extract_landmarks(self, image_path):
        """Extract landmarks from an image"""
        image = cv2.imread(image_path)
        if image is None:
            return None
        
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.hands.process(image_rgb)
        
        if not results.multi_hand_landmarks:
            return None
        
        landmarks = []
        for hand_landmarks in results.multi_hand_landmarks:
            for landmark in hand_landmarks.landmark:
                landmarks.extend([landmark.x, landmark.y, landmark.z])
        
        # Pad or truncate to fixed size (21 landmarks * 3 coords = 63 features per hand)
        while len(landmarks) < 126:  # 2 hands max
            landmarks.extend([0.0, 0.0, 0.0])
        
        return np.array(landmarks[:126])
    
    def process_dataset(self, data_dir, output_file):
        """Process entire dataset and save landmarks"""
        X = []
        y = []
        
        # Check if data_dir exists
        if not os.path.exists(data_dir):
            raise FileNotFoundError(f"Dataset directory not found: {data_dir}")
        
        # Get all label folders
        labels = [d for d in os.listdir(data_dir) 
                 if os.path.isdir(os.path.join(data_dir, d))]
        
        if len(labels) == 0:
            raise ValueError(f"No label folders found in {data_dir}")
        
        print(f"Found {len(labels)} classes: {sorted(labels)}")
        
        # Process each label
        for label in tqdm(sorted(labels), desc="Processing labels"):
            label_dir = os.path.join(data_dir, label)
            
            image_files = [f for f in os.listdir(label_dir) 
                          if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            
            for img_file in tqdm(image_files, desc=f"  {label}", leave=False):
                img_path = os.path.join(label_dir, img_file)
                landmarks = self.extract_landmarks(img_path)
                
                if landmarks is not None:
                    X.append(landmarks)
                    y.append(label)
        
        X = np.array(X)
        y = np.array(y)
        
        # Save processed data
        with open(output_file, 'wb') as f:
            pickle.dump({'X': X, 'y': y}, f)
        
        print(f"\n✓ Processed {len(X)} samples from {len(np.unique(y))} classes")
        return X, y
    
    def close(self):
        self.hands.close()


def augment_landmarks(landmarks, num_augmentations=5):
    """Data augmentation for landmark coordinates"""
    augmented = [landmarks]
    
    for _ in range(num_augmentations):
        aug = landmarks.copy()
        
        # Add noise
        noise = np.random.normal(0, 0.02, aug.shape)
        aug += noise
        
        # Random rotation (around z-axis)
        angle = np.random.uniform(-15, 15) * np.pi / 180
        for i in range(0, len(aug), 3):
            x, y, z = aug[i], aug[i+1], aug[i+2]
            aug[i] = x * np.cos(angle) - y * np.sin(angle)
            aug[i+1] = x * np.sin(angle) + y * np.cos(angle)
        
        # Random scaling
        scale = np.random.uniform(0.9, 1.1)
        aug *= scale
        
        augmented.append(aug)
    
    return np.array(augmented)