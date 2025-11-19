import json
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio

class ASLConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time ASL translation"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.predictor = None
    
    async def connect(self):
        await self.accept()
        
        # Initialize predictor
        try:
            # Use the trained model
            self.predictor = ASLPredictor(
                model_path='ml_models/saved_models/lstm_model.h5',
                label_encoder_path='ml_models/saved_models/label_encoder.pkl',
                model_type='lstm'
            )
            
            await self.send(text_data=json.dumps({
                'type': 'connection',
                'status': 'connected',
                'message': 'ASL Translator ready'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Failed to load model: {str(e)}'
            }))
    
    async def disconnect(self, close_code):
        pass
    
    async def receive(self, text_data):
        """Receive landmarks from client and send prediction"""
        try:
            data = json.loads(text_data)
            
            if data['type'] == 'landmarks':
                landmarks = np.array(data['landmarks'])
                
                # Make prediction
                label, confidence, latency = self.predictor.predict(landmarks)
                
                if label is not None:
                    await self.send(text_data=json.dumps({
                        'type': 'prediction',
                        'label': label,
                        'confidence': confidence,
                        'latency': latency
                    }))
            
            elif data['type'] == 'reset':
                self.predictor.reset_sequence()
                await self.send(text_data=json.dumps({
                    'type': 'reset_confirmed'
                }))
        
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
