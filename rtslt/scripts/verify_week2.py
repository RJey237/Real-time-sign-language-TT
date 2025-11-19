"""
Verify Week 2 completion
"""
import os

def check_week2_completion():
    print("=" * 60)
    print("WEEK 2 COMPLETION CHECK")
    print("=" * 60)
    
    checks = {
        "Code Files": [
            "ml_models/train_baseline.py",
            "ml_models/train_lstm.py",
            "ml_models/train_all.py",
            "ml_models/data_preprocessing.py",
            "ml_models/inference.py"
        ],
        "Trained Models": [
            "ml_models/saved_models/baseline_mlp.pkl",
            "ml_models/saved_models/lstm_model.h5",
            "ml_models/saved_models/label_encoder.pkl"
        ],
        "Documentation": [
            "README.md",
            "ROADMAP.md"
        ]
    }
    
    total = 0
    completed = 0
    
    for category, files in checks.items():
        print(f"\n{category}:")
        for file in files:
            total += 1
            if os.path.exists(file):
                print(f"  ✓ {file}")
                completed += 1
            else:
                print(f"  ✗ {file} (MISSING)")
    
    print(f"\n{'=' * 60}")
    print(f"Completion: {completed}/{total} ({completed/total*100:.1f}%)")
    print(f"{'=' * 60}")
    
    if completed < total:
        print("\n⚠️  Action Required:")
        print("Run: python ml_models/train_all.py")
    else:
        print("\n✅ Week 2 Complete!")

if __name__ == "__main__":
    check_week2_completion()