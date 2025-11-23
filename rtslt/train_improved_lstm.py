"""
Improved LSTM model training for ASL recognition - TRAINING SCRIPT
Run this to retrain the model with better architecture and performance
"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.utils import to_categorical
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import numpy as np
import pickle
import os
from ml_models.data_preprocessing import LandmarkExtractor, augment_landmarks


def create_improved_lstm_model(input_shape, num_classes):
    """Create improved LSTM model with better architecture"""
    
    model = keras.Sequential([
        layers.Input(shape=input_shape),
        
        # First LSTM block - Bidirectional
        layers.Bidirectional(layers.LSTM(256, return_sequences=True)),
        layers.BatchNormalization(),
        layers.Dropout(0.4),
        
        # Second LSTM block - Bidirectional
        layers.Bidirectional(layers.LSTM(128, return_sequences=True)),
        layers.BatchNormalization(),
        layers.Dropout(0.4),
        
        # Third LSTM block
        layers.LSTM(64),
        layers.BatchNormalization(),
        layers.Dropout(0.3),
        
        # Dense layers with better capacity
        layers.Dense(256, activation='relu'),
        layers.BatchNormalization(),
        layers.Dropout(0.4),
        
        layers.Dense(128, activation='relu'),
        layers.BatchNormalization(),
        layers.Dropout(0.3),
        
        layers.Dense(num_classes, activation='softmax')
    ])
    
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.0005),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    return model


def prepare_sequences_augmented(X, y, sequence_length=10, augment=True):
    """Prepare sequences with optional augmentation for better generalization"""
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
        
        # Create sequences by sliding window with stride
        stride = 2 if len(indices) > 100 else 1  # Use stride for larger datasets
        for i in range(0, len(indices) - sequence_length + 1, stride):
            seq_indices = indices[i:i+sequence_length]
            X_seq.append(X[seq_indices])
            y_seq.append(label_idx)
            
            # Augment each sequence
            if augment:
                for aug_idx in range(3):  # Create 3 augmented versions
                    aug_seq = []
                    for frame in X[seq_indices]:
                        aug_frames = augment_landmarks(frame, num_augmentations=1)
                        aug_seq.append(aug_frames[1])  # Use augmented version
                    X_seq.append(np.array(aug_seq))
                    y_seq.append(label_idx)
    
    return np.array(X_seq), np.array(y_seq), le


def train_improved_lstm(X, y, sequence_length=10, model_path='ml_models/saved_models/lstm_model.h5'):
    """Train improved LSTM model"""
    
    print("\n" + "="*70)
    print("IMPROVED LSTM TRAINING FOR ASL RECOGNITION")
    print("="*70)
    
    print(f"\nInput data shape: {X.shape}")
    print(f"Number of samples: {len(X)}")
    print(f"Number of classes: {len(np.unique(y))}")
    
    print("\nPreparing sequences with augmentation...")
    X_seq, y_seq, le = prepare_sequences_augmented(X, y, sequence_length, augment=True)
    
    print(f"Total sequences after augmentation: {len(X_seq)}")
    print(f"Sequence shape: {X_seq.shape}")
    print(f"Classes: {le.classes_}")
    
    # Split data with stratification
    X_train, X_test, y_train, y_test = train_test_split(
        X_seq, y_seq, test_size=0.15, random_state=42, stratify=y_seq
    )
    
    # Further split train into train/val
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.15, random_state=42, stratify=y_train
    )
    
    # One-hot encode labels
    num_classes = len(le.classes_)
    y_train_cat = to_categorical(y_train, num_classes)
    y_val_cat = to_categorical(y_val, num_classes)
    y_test_cat = to_categorical(y_test, num_classes)
    
    print(f"\nTrain sequences: {len(X_train)}")
    print(f"Val sequences: {len(X_val)}")
    print(f"Test sequences: {len(X_test)}")
    print(f"Number of classes: {num_classes}")
    
    # Create model
    input_shape = (sequence_length, X.shape[1])
    model = create_improved_lstm_model(input_shape, num_classes)
    
    print("\nImproved Model Architecture:")
    model.summary()
    
    # Callbacks
    early_stop = keras.callbacks.EarlyStopping(
        monitor='val_loss',
        patience=20,
        restore_best_weights=True,
        verbose=1
    )
    
    reduce_lr = keras.callbacks.ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=8,
        min_lr=1e-7,
        verbose=1
    )
    
    # Create output directory if needed
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    
    model_checkpoint = keras.callbacks.ModelCheckpoint(
        model_path,
        monitor='val_accuracy',
        save_best_only=True,
        verbose=1
    )
    
    # Train
    print("\n" + "="*70)
    print("Training improved LSTM model...")
    print("="*70)
    history = model.fit(
        X_train, y_train_cat,
        validation_data=(X_val, y_val_cat),
        epochs=200,
        batch_size=16,
        callbacks=[early_stop, reduce_lr, model_checkpoint],
        verbose=1
    )
    
    # Load best model
    model = keras.models.load_model(model_path)
    
    # Evaluate on test set
    print("\n" + "="*70)
    print("EVALUATION")
    print("="*70)
    
    val_loss, val_acc = model.evaluate(X_val, y_val_cat, verbose=0)
    test_loss, test_acc = model.evaluate(X_test, y_test_cat, verbose=0)
    
    print(f"\nValidation Accuracy: {val_acc:.4f} ({val_acc*100:.2f}%)")
    print(f"Test Accuracy: {test_acc:.4f} ({test_acc*100:.2f}%)")
    
    # Per-class accuracy
    print("\nPer-class accuracy:")
    y_pred = model.predict(X_test, verbose=0)
    y_pred_labels = np.argmax(y_pred, axis=1)
    
    for i, class_name in enumerate(le.classes_):
        mask = y_test == i
        if mask.sum() > 0:
            class_acc = (y_pred_labels[mask] == i).mean()
            print(f"  {class_name}: {class_acc:.4f} ({class_acc*100:.2f}%)")
    
    print("\n" + "="*70)
    print(f"✓ Model saved to: {model_path}")
    print("="*70)
    
    # Save label encoder
    encoder_path = model_path.replace('.h5', '_label_encoder.pkl')
    with open(encoder_path, 'wb') as f:
        pickle.dump(le, f)
    print(f"✓ Label encoder saved to: {encoder_path}")
    
    return model, le, history


if __name__ == '__main__':
    # Load data
    print("\nLoading training data...")
    data_file = 'ml_models/saved_models/landmarks_data.pkl'
    
    if not os.path.exists(data_file):
        print(f"\nExtracting landmarks from dataset...")
        extractor = LandmarkExtractor()
        X, y = extractor.process_dataset(
            'data/asl_alphabet/asl_alphabet_train',
            data_file
        )
        extractor.close()
    else:
        with open(data_file, 'rb') as f:
            data = pickle.load(f)
            X, y = data['X'], data['y']
        print(f"Loaded {len(X)} samples from {data_file}")
    
    # Train improved model
    model, le, history = train_improved_lstm(
        X, y,
        sequence_length=10,
        model_path='ml_models/saved_models/lstm_model.h5'
    )
    
    print("\n✓ Training complete!")
