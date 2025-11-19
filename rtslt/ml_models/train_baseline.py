"""
Baseline MLP model training
"""

from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import pickle
import numpy as np


def train_baseline_model(X_train, y_train, X_test, y_test, model_path='baseline_mlp.pkl'):
    """Train baseline MLP model"""
    
    print("\nTraining MLP Classifier...")
    print(f"Input shape: {X_train.shape}")
    print(f"Number of classes: {len(np.unique(y_train))}")
    
    # Encode labels
    le = LabelEncoder()
    y_train_encoded = le.fit_transform(y_train)
    y_test_encoded = le.transform(y_test)
    
    # Train MLP
    mlp = MLPClassifier(
        hidden_layer_sizes=(256, 128, 64),
        activation='relu',
        solver='adam',
        max_iter=500,
        random_state=42,
        verbose=True,
        early_stopping=True,
        validation_fraction=0.1
    )
    
    mlp.fit(X_train, y_train_encoded)
    
    # Evaluate
    y_pred = mlp.predict(X_test)
    accuracy = accuracy_score(y_test_encoded, y_pred)
    
    print(f"\n{'='*60}")
    print(f"Baseline MLP Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
    print(f"{'='*60}")
    
    print("\nClassification Report:")
    print(classification_report(y_test_encoded, y_pred, 
                               target_names=le.classes_, 
                               zero_division=0))
    
    # Save model
    with open(model_path, 'wb') as f:
        pickle.dump({'model': mlp, 'label_encoder': le}, f)
    
    return mlp, le, accuracy