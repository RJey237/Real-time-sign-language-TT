import json
import asyncio
import numpy as np
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from asgiref.sync import sync_to_async
from urllib.parse import parse_qs
from ml_models.inference import ASLPredictor
from .models import UserProfile, ChatMessage

class ASLConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time ASL translation"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.predictor = None
        self.current_id = None
    
    async def connect(self):
        # Get current user's ID from query string
        try:
            qs = parse_qs((self.scope.get('query_string') or b'').decode())
            self.current_id = qs.get('self', [None])[0]
        except Exception:
            pass
        
        await self.accept()
        
        # Initialize predictor
        try:
            # Use the trained model
            self.predictor = ASLPredictor(
                model_path='ml_models/saved_models/lstm_model.h5',
                label_encoder_path='ml_models/saved_models/lstm_model_label_encoder.pkl',
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
        """Receive landmarks from client and send prediction to chat room"""
        try:
            data = json.loads(text_data)
            
            if data['type'] == 'landmarks':
                has_hands = data.get('has_hands', True)
                
                # If no hands detected, reset buffer and don't predict
                if not has_hands:
                    self.predictor.reset_sequence()
                    return
                
                landmarks = np.array(data['landmarks'])
                
                # Make prediction
                label, confidence, latency = self.predictor.predict(landmarks, has_hands=True)
                
                if label is not None and confidence > 0.70:  # Higher threshold for better accuracy
                    # Send to chat room for broadcasting
                    if self.current_id:
                        # Create room name based on sorted IDs (same as ChatConsumer)
                        # For now, just send back to client and let chat handle broadcasting
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


class ChatConsumer(AsyncWebsocketConsumer):
    """Simple chat consumer joining a room derived from two user random IDs.
    Connect to ws/chat/<target_random_id>/ while authenticated.
    """

    async def connect(self):
        self.scope_user = self.scope.get('user')
        target_id = self.scope['url_route']['kwargs'].get('target_id')
        if not target_id:
            await self.close()
            return
        # Resolve current user's random id (or anonymous); allow override via ?self=
        self.current_id = None
        try:
            qs = parse_qs((self.scope.get('query_string') or b'').decode())
            override = qs.get('self', [None])[0]
            if override:
                self.current_id = override
        except Exception:
            pass
        if not self.current_id:
            self.current_id = await self._get_current_random_id()
        # Create symmetric room name
        ids = sorted([self.current_id or 'anon', target_id])
        self.room_name = f"chat_{ids[0]}_{ids[1]}"
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()
        # notify join
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': 'chat.message',
                'sender': await self._get_username(),
                'text': '[joined]'
            }
        )

    async def disconnect(self, close_code):
        if hasattr(self, 'room_name'):
            await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data or '{}')
            if data.get('type') == 'message':
                text = data.get('text', '')
                sender_name = await self._get_username()
                # Optionally persist
                await self._persist_message(text)
                await self.channel_layer.group_send(
                    self.room_name,
                    {
                        'type': 'chat.message',
                        'sender': sender_name,
                        'text': text
                    }
                )
            elif data.get('type') == 'prediction' or data.get('type') == 'asl_prediction':
                label = data.get('label')
                confidence = float(data.get('confidence') or 0.0)
                await self.channel_layer.group_send(
                    self.room_name,
                    {
                        'type': 'asl.prediction',
                        'label': label,
                        'confidence': confidence,
                    }
                )
        except Exception as e:
            await self.send(text_data=json.dumps({'type': 'error', 'message': str(e)}))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'sender': event['sender'],
            'text': event['text']
        }))

    async def asl_prediction(self, event):
        """Send ASL prediction to client"""
        await self.send(text_data=json.dumps({
            'type': 'asl_prediction',
            'label': event.get('label'),
            'confidence': event.get('confidence'),
        }))

    @sync_to_async
    def _get_current_random_id(self):
        user = self.scope.get('user')
        if user and not isinstance(user, AnonymousUser) and user.is_authenticated:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            return profile.random_id
        return None

    @sync_to_async
    def _get_username(self):
        user = self.scope.get('user')
        if user and not isinstance(user, AnonymousUser) and user.is_authenticated:
            return user.username
        return 'anonymous'

    @sync_to_async
    def _persist_message(self, text: str):
        user = self.scope.get('user')
        if user and not isinstance(user, AnonymousUser) and user.is_authenticated:
            ChatMessage.objects.create(room=self.room_name, sender=user, text=text)


class VideoConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for video streaming between two peers"""

    async def connect(self):
        self.scope_user = self.scope.get('user')
        target_id = self.scope['url_route']['kwargs'].get('target_id')
        if not target_id:
            await self.close()
            return
        
        # Resolve current user's random id
        self.current_id = None
        try:
            qs = parse_qs((self.scope.get('query_string') or b'').decode())
            override = qs.get('self', [None])[0]
            if override:
                self.current_id = override
        except Exception:
            pass
        
        if not self.current_id:
            self.current_id = await self._get_current_random_id()
        
        # Store target and current IDs
        self.target_id = target_id
        
        # Create symmetric room name
        ids = sorted([self.current_id or 'anon', target_id])
        self.room_name = f"video_{ids[0]}_{ids[1]}"
        
        print(f"[Video] {self.current_id} connecting to room {self.room_name} (targeting {target_id})")
        
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_name'):
            print(f"[Video] {self.current_id} disconnecting from room {self.room_name}")
            await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        """Receive video frame and relay ONLY to the other peer"""
        try:
            if text_data:
                data = json.loads(text_data)
                if data.get('type') == 'frame':
                    frame_data = data.get('frame_data')
                    print(f"[Video] {self.current_id} → {self.target_id}: Sending frame in room {self.room_name}")
                    # Send to group - video_frame handler will filter to appropriate peer
                    await self.channel_layer.group_send(
                        self.room_name,
                        {
                            'type': 'video.frame',
                            'frame_data': frame_data,
                            'sender_id': self.current_id,
                            'target_id': self.target_id
                        }
                    )
        except Exception as e:
            print(f"[Video Error] {e}")
            await self.send(text_data=json.dumps({'type': 'error', 'message': str(e)}))

    async def video_frame(self, event):
        """Relay video frame ONLY if this client is the TARGET (receiver)"""
        sender_id = event.get('sender_id')
        target_id = event.get('target_id')
        
        # Send frame only if:
        # - This is not the sender themselves (current_id != sender_id)
        # - AND this client is expecting frames from that sender (target_id == sender_id)
        if sender_id != self.current_id and target_id == self.current_id:
            print(f"[Video] {self.current_id} receiving frame from {sender_id}")
            await self.send(text_data=json.dumps({
                'type': 'frame',
                'frame_data': event['frame_data']
            }))
        elif sender_id == self.current_id:
            print(f"[Video] {self.current_id} ignoring own frame")
        else:
            print(f"[Video] {self.current_id} filtering out frame: not expecting from {sender_id} (expected {target_id})")

    @sync_to_async
    def _get_current_random_id(self):
        user = self.scope.get('user')
        if user and not isinstance(user, AnonymousUser) and user.is_authenticated:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            return profile.random_id
        return None
