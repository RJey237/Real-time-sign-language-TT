"""
LSTM/GRU model training for sequence classification
"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.utils import to_categorical
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import numpy as np
import pickle


def create_lstm_model(input_shape, num_classes):
    """Create LSTM model for sequence classification"""
    
    model = keras.Sequential([
        layers.Input(shape=input_shape),
        
        # LSTM layers
        layers.LSTM(128, return_sequences=True),
        layers.Dropout(0.3),
        layers.LSTM(64, return_sequences=True),
        layers.Dropout(0.3),
        layers.LSTM(32),
        layers.Dropout(0.3),
        
        # Dense layers
        layers.Dense(64, activation='relu'),
        layers.Dropout(0.3),
        layers.Dense(num_classes, activation='softmax')
    ])
    
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    return model


def prepare_sequences(X, y, sequence_length=10):
    """Convert static landmarks to sequences"""
    X_seq = []
    y_seq = []
    
    # Encode labels
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    unique_labels = np.unique(y_encoded)
    
    print(f"Creating sequences of length {sequence_length}...")
    
    # Group by labels and create sequences
    for label_idx in unique_labels:
        indices = np.where(y_encoded == label_idx)[0]
        
        # Create sequences by sliding window
        for i in range(len(indices) - sequence_length + 1):
            seq_indices = indices[i:i+sequence_length]
            X_seq.append(X[seq_indices])
            y_seq.append(label_idx)
    
    return np.array(X_seq), np.array(y_seq), le


def train_lstm_model(X, y, sequence_length=10, model_path='lstm_model.h5'):
    """Train LSTM model"""
    
    print("\nPreparing sequences...")
    # Prepare sequences
    X_seq, y_seq, le = prepare_sequences(X, y, sequence_length)
    
    print(f"Total sequences: {len(X_seq)}")
    print(f"Sequence shape: {X_seq.shape}")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X_seq, y_seq, test_size=0.2, random_state=42, stratify=y_seq
    )
    
    # One-hot encode labels
    num_classes = len(le.classes_)
    y_train_cat = to_categorical(y_train, num_classes)
    y_test_cat = to_categorical(y_test, num_classes)
    
    print(f"Train sequences: {len(X_train)}")
    print(f"Test sequences: {len(X_test)}")
    print(f"Number of classes: {num_classes}")
    
    # Create model
    input_shape = (sequence_length, X.shape[1])
    model = create_lstm_model(input_shape, num_classes)
    
    print("\nModel Architecture:")
    model.summary()
    
    # Callbacks
    early_stop = keras.callbacks.EarlyStopping(
        monitor='val_loss',
        patience=15,
        restore_best_weights=True,
        verbose=1
    )
    
    reduce_lr = keras.callbacks.ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=5,
        min_lr=1e-6,
        verbose=1
    )
    
    # Train
    print("\nTraining LSTM model...")
    history = model.fit(
        X_train, y_train_cat,
        validation_data=(X_test, y_test_cat),
        epochs=100,
        batch_size=32,
        callbacks=[early_stop, reduce_lr],
        verbose=1
    )
    
    # Evaluate
    test_loss, test_acc = model.evaluate(X_test, y_test_cat, verbose=0)
    
    print(f"\n{'='*60}")
    print(f"LSTM Test Accuracy: {test_acc:.4f} ({test_acc*100:.2f}%)")
    print(f"{'='*60}")
    
    # Save model
    model.save(model_path)
    print(f"Model saved to: {model_path}")
    
    # Save label encoder
    encoder_path = model_path.replace('.h5', '_label_encoder.pkl')
    with open(encoder_path, 'wb') as f:
        pickle.dump(le, f)
    print(f"Label encoder saved to: {encoder_path}")
    
    return model, le, history