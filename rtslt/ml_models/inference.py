import time
import pickle
import os
import numpy as np
from tensorflow import keras
from collections import deque

DEFAULT_CLASSES = [
    'A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z',
    'del','nothing','space'
]


class ASLPredictor:
    """Real-time ASL prediction with improved accuracy"""
    
    def __init__(self, model_path, label_encoder_path=None, model_type='lstm'):
        self.model_type = model_type
        
        if model_type == 'lstm' or model_type == 'gru':
            self.model = keras.models.load_model(model_path)
            self.label_encoder = None
            self.classes = None
            # Try to load label encoder if provided or common paths
            encoder_paths = []
            if label_encoder_path:
                encoder_paths.append(label_encoder_path)
            # common fallback locations
            encoder_paths.extend([
                'ml_models/saved_models/lstm_model_label_encoder.pkl',
                'ml_models/saved_models/label_encoder.pkl'
            ])
            for p in encoder_paths:
                if os.path.exists(p):
                    try:
                        with open(p, 'rb') as f:
                            self.label_encoder = pickle.load(f)
                        break
                    except Exception:
                        pass
            # If encoder missing, derive classes from dataset or default
            if self.label_encoder is None:
                # Use relative path or os.path.join to avoid backslash issues
                dataset_dir = os.path.join('data', 'asl_alphabet', 'asl_alphabet_train')
                if os.path.isdir(dataset_dir):
                    try:
                        labels = [d for d in os.listdir(dataset_dir) if os.path.isdir(os.path.join(dataset_dir, d))]
                        self.classes = sorted(labels)
                    except Exception:
                        self.classes = DEFAULT_CLASSES
                else:
                    self.classes = DEFAULT_CLASSES
            self.sequence_buffer = []
            self.sequence_length = 10
            # Prediction smoothing: track last N predictions for voting
            self.prediction_history = deque(maxlen=3)
            self.last_predicted_label = None
            self.same_prediction_count = 0
        else:
            with open(model_path, 'rb') as f:
                data = pickle.load(f)
                self.model = data['model']
                self.label_encoder = data['label_encoder']
    
    def _normalize_landmarks(self, landmarks):
        """Normalize landmarks for consistent model input"""
        landmarks = np.array(landmarks, dtype=np.float32)
        
        # Reshape if needed (should be 42 values for 21 keypoints * 2 coords)
        if landmarks.size == 42:
            landmarks = landmarks.reshape(21, 2)
        elif landmarks.size == 126:
            landmarks = landmarks.reshape(42, 3)  # For 2 hands
        
        # Normalize to [-1, 1] range based on typical hand positions
        # Assuming coordinates are in [0, 1] range from MediaPipe
        landmarks = landmarks * 2.0 - 1.0
        
        # Flatten back
        return landmarks.flatten()
    
    def predict(self, landmarks, has_hands=True):
        """Predict ASL sign from landmarks with improved accuracy"""
        start_time = time.time()
        
        # Reset buffer if no hands detected
        if not has_hands:
            self.reset_sequence()
            self.prediction_history.clear()
            self.same_prediction_count = 0
            self.last_predicted_label = None
            return None, 0.0, 0
        
        if self.model_type == 'lstm' or self.model_type == 'gru':
            # Normalize landmarks for better model accuracy
            landmarks = self._normalize_landmarks(landmarks)
            
            # Add to sequence buffer only if hands are detected
            self.sequence_buffer.append(landmarks)
            if len(self.sequence_buffer) > self.sequence_length:
                self.sequence_buffer.pop(0)
            
            # Need full sequence
            if len(self.sequence_buffer) < self.sequence_length:
                return None, 0.0, 0
            
            # Predict with optimized batch prediction
            sequence = np.array([self.sequence_buffer])
            predictions = self.model.predict_on_batch(sequence)
            confidence = float(np.max(predictions))
            predicted_idx = int(np.argmax(predictions))
            
            if self.label_encoder is not None:
                predicted_label = self.label_encoder.inverse_transform([predicted_idx])[0]
            else:
                # Fallback mapping
                if self.classes and 0 <= predicted_idx < len(self.classes):
                    predicted_label = self.classes[predicted_idx]
                else:
                    predicted_label = str(predicted_idx)
            
            # Add to history for smoothing
            self.prediction_history.append((predicted_label, confidence))
            
            # Only return prediction if:
            # 1. High confidence (>0.65)
            # 2. Same label appears at least 2 times in recent history (voting)
            label_counts = {}
            avg_confidence = 0
            for label, conf in self.prediction_history:
                label_counts[label] = label_counts.get(label, 0) + 1
                avg_confidence += conf
            avg_confidence /= len(self.prediction_history)
            
            # Check if current prediction is stable
            if confidence > 0.65 and label_counts.get(predicted_label, 0) >= 2 and avg_confidence > 0.65:
                # If same as last prediction, increment counter
                if predicted_label == self.last_predicted_label:
                    self.same_prediction_count += 1
                else:
                    self.same_prediction_count = 1
                    self.last_predicted_label = predicted_label
                
                # Return prediction after 2 consecutive matches
                if self.same_prediction_count >= 2:
                    latency = int((time.time() - start_time) * 1000)
                    return predicted_label, avg_confidence, latency
            else:
                # Reset counter if prediction changed or confidence dropped
                if predicted_label != self.last_predicted_label:
                    self.same_prediction_count = 0
                    self.last_predicted_label = None
        
        latency = int((time.time() - start_time) * 1000)
        return None, 0.0, latency
    
    def reset_sequence(self):
        """Reset sequence buffer"""
        if self.model_type in ['lstm', 'gru']:
            self.sequence_buffer = []