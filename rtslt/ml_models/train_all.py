"""
Main training script for ASL Translator
Run this file to train all models
"""

import sys
import os
import pickle
from sklearn.model_selection import train_test_split

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_models.data_preprocessing import LandmarkExtractor, augment_landmarks
from ml_models.train_baseline import train_baseline_model

# Import improved LSTM trainer
from train_improved_lstm import train_improved_lstm


def main():
    """Main training pipeline"""
    print("=" * 80)
    print("ASL TRANSLATOR - TRAINING PIPELINE")
    print("=" * 80)
    
    # Create directories if they don't exist
    os.makedirs('ml_models/saved_models', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    # Step 1: Extract landmarks from dataset
    print("\n[1/4] Extracting landmarks from dataset...")
    print("Make sure you have downloaded the ASL Alphabet dataset to 'data/asl_alphabet/'")
    
    # Check if processed data already exists
    if os.path.exists('data/processed_data.pkl'):
        print("Found existing processed data. Loading...")
        with open('data/processed_data.pkl', 'rb') as f:
            data = pickle.load(f)
            X, y = data['X'], data['y']
        print(f"Loaded {len(X)} samples")
    else:
        print("Processing dataset (this may take a while)...")
        extractor = LandmarkExtractor()
        X, y = extractor.process_dataset(
            data_dir=r'D:\New folder\General\University\4.1\Computer vision\project\Real-time-sign-language-TT\rtslt\data\asl_alphabet\asl_alphabet_train',
            output_file='data/processed_data.pkl'
        )
        extractor.close()
        print(f"Extracted {len(X)} samples")
    
    # Step 2: Split data
    print("\n[2/4] Splitting data into train/test sets...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"Train samples: {len(X_train)}")
    print(f"Test samples: {len(X_test)}")
    
    # Step 3: Train baseline model
    print("\n[3/4] Training baseline MLP model...")
    mlp, le_baseline, baseline_acc = train_baseline_model(
        X_train, y_train, X_test, y_test,
        model_path='ml_models/saved_models/baseline_mlp.pkl'
    )
    print(f"✓ Baseline model saved to 'ml_models/saved_models/baseline_mlp.pkl'")
    
    # Step 4: Train improved LSTM model
    print("\n[4/4] Training improved LSTM model...")
    print("This will take longer (20-40 minutes depending on your hardware)...")
    lstm, le_lstm, history = train_improved_lstm(
        X, y,
        sequence_length=10,
        model_path='ml_models/saved_models/lstm_model.h5'
    )
    print(f"✓ Improved LSTM model saved to 'ml_models/saved_models/lstm_model.h5'")
    encoder_path = 'ml_models/saved_models/lstm_model_label_encoder.pkl'
    print(f"✓ Label encoder saved to '{encoder_path}'")
    
    # Summary
    print("\n" + "=" * 80)
    print("TRAINING COMPLETE!")
    print("=" * 80)
    print(f"📊 Baseline MLP Accuracy: {baseline_acc:.2%}")
    print(f"📊 Improved LSTM Accuracy: {history.history['val_accuracy'][-1]:.2%}")
    print("\n📁 Models saved in: ml_models/saved_models/")
    print("\n🚀 Next step: Run 'python manage.py runserver' to start the web app")
    print("=" * 80)


if __name__ == "__main__":
    main()