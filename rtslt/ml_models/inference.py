import time
import pickle
import os
import numpy as np
from tensorflow import keras

DEFAULT_CLASSES = [
    'A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z',
    'del','nothing','space'
]


class ASLPredictor:
    """Real-time ASL prediction"""
    
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
        else:
            with open(model_path, 'rb') as f:
                data = pickle.load(f)
                self.model = data['model']
                self.label_encoder = data['label_encoder']
    
    def predict(self, landmarks, has_hands=True):
        """Predict ASL sign from landmarks. Only predicts if hands are detected."""
        start_time = time.time()
        
        # Reset buffer if no hands detected
        if not has_hands:
            self.reset_sequence()
            return None, 0.0, 0
        
        if self.model_type == 'lstm' or self.model_type == 'gru':
            # Add to sequence buffer only if hands are detected
            self.sequence_buffer.append(landmarks)
            if len(self.sequence_buffer) > self.sequence_length:
                self.sequence_buffer.pop(0)
            
            # Need full sequence
            if len(self.sequence_buffer) < self.sequence_length:
                return None, 0.0, 0
            
            # Predict
            sequence = np.array([self.sequence_buffer])
            predictions = self.model.predict(sequence, verbose=0)
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
        else:
            # Static prediction (MLP)
            landmarks = landmarks.reshape(1, -1)
            predicted_idx = self.model.predict(landmarks)[0]
            predicted_label = self.label_encoder.inverse_transform([predicted_idx])[0]
            
            # Get confidence (for sklearn, use predict_proba)
            if hasattr(self.model, 'predict_proba'):
                probs = self.model.predict_proba(landmarks)
                confidence = float(np.max(probs))
            else:
                confidence = 1.0
        
        latency = int((time.time() - start_time) * 1000)  # ms
        
        return predicted_label, confidence, latency
    
    def reset_sequence(self):
        """Reset sequence buffer"""
        if self.model_type in ['lstm', 'gru']:
            self.sequence_buffer = []