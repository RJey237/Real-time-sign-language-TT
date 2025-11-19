import time

class ASLPredictor:
    """Real-time ASL prediction"""
    
    def __init__(self, model_path, label_encoder_path, model_type='lstm'):
        self.model_type = model_type
        
        if model_type == 'lstm' or model_type == 'gru':
            self.model = keras.models.load_model(model_path)
            with open(label_encoder_path, 'rb') as f:
                self.label_encoder = pickle.load(f)
            self.sequence_buffer = []
            self.sequence_length = 10
        else:
            with open(model_path, 'rb') as f:
                data = pickle.load(f)
                self.model = data['model']
                self.label_encoder = data['label_encoder']
    
    def predict(self, landmarks):
        """Predict ASL sign from landmarks"""
        start_time = time.time()
        
        if self.model_type == 'lstm' or self.model_type == 'gru':
            # Add to sequence buffer
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
            predicted_idx = np.argmax(predictions)
            predicted_label = self.label_encoder.inverse_transform([predicted_idx])[0]
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