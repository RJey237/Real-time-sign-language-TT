# Git Workflow Guide for ASL Translator

## 🔒 What NOT to Commit (Already in .gitignore)

### ❌ Large Dataset Files

```
data/asl_alphabet/          # ~1GB of images
data/asl_alphabet_test/
data/wlasl/
*.pkl                       # Processed data files
processed_data.pkl
```

**Why?** Too large for Git (1GB+). Team members should download separately.

### ❌ Trained Models

```
ml_models/saved_models/     # All trained models
*.h5                        # Keras/TensorFlow models
*.pkl                       # Scikit-learn models
baseline_mlp.pkl
lstm_model.h5
label_encoder.pkl
```

**Why?** Models are 50-500MB each. Should be trained locally or shared via cloud storage.

### ❌ Virtual Environments

```
venv/
newenv/
env/
.venv/
```

**Why?** Environment should be recreated using `requirements.txt`

### ❌ Cache & Temporary Files

```
__pycache__/
*.pyc
*.log
db.sqlite3
.DS_Store
Thumbs.db
```

**Why?** Auto-generated, system-specific files.

---

## ✅ What TO Commit

### ✓ Source Code

```
ml_models/
├── __init__.py
├── data_preprocessing.py
├── train_baseline.py
├── train_lstm.py
├── train_all.py
├── inference.py
└── saved_models/.gitkeep    # Keep folder structure
```

### ✓ Django Project Files

```
rtslt/
├── __init__.py
├── settings.py
├── urls.py
├── asgi.py
└── wsgi.py

translator/
├── consumers.py
├── routing.py
├── views.py
└── models.py
```

### ✓ Frontend Code

```
static/
├── css/style.css
└── js/mediapipe_handler.js

templates/
└── translator/index.html
```

### ✓ Configuration Files

```
requirements.txt
.gitignore
README.md
ROADMAP.md
manage.py
```

### ✓ Documentation

```
README.md
ROADMAP.md
docs/
LICENSE
```

---

## 📋 Git Commands Cheat Sheet

### Initial Setup

```powershell
# 1. Copy .gitignore content to your project
# (from the artifact I created)

# 2. Initialize Git
git init

# 3. Add all files (respecting .gitignore)
git add .

# 4. Check what will be committed
git status

# 5. Make initial commit
git commit -m "Initial commit: Project structure and source code"

# 6. Add remote repository
git remote add origin https://github.com/RJey237/Real-time-sign-language-TT.git

# 7. Push to GitHub
git branch -M main
git push -u origin main
```

### Daily Workflow

```powershell
# Before making changes
git pull origin main

# Check status
git status

# Add specific files
git add ml_models/train_all.py
git add translator/consumers.py

# Or add all changed files
git add .

# Commit with message
git commit -m "Add: LSTM model training with data augmentation"

# Push to remote
git push origin main
```

### Useful Commands

```powershell
# See what's ignored
git status --ignored

# See file size
git ls-files -z | xargs -0 du -h | sort -h

# Remove file from git but keep locally
git rm --cached filename

# Remove entire folder from git
git rm -r --cached data/

# View commit history
git log --oneline

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Discard local changes
git checkout -- filename
```

---

## 🚀 Setup Instructions for Team Members

### For Team Member Cloning the Repository

```powershell
# 1. Clone repository
git clone https://github.com/RJey237/Real-time-sign-language-TT.git
cd Real-time-sign-language-TT

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download dataset separately
# Go to: https://www.kaggle.com/datasets/grassknoted/asl-alphabet
# Extract to: data/asl_alphabet/

# 5. Train models locally
python ml_models/train_all.py

# 6. Run server
python manage.py runserver
```

---

## 📦 Sharing Large Files (Alternative Solutions)

Since datasets and models are too large for Git, use these alternatives:

### Option 1: Cloud Storage Links

Add to README.md:

```markdown
## Dataset & Model Downloads

**Datasets:**
- ASL Alphabet: [Kaggle Link](https://www.kaggle.com/datasets/grassknoted/asl-alphabet)
- WLASL: [Official Site](https://dxli94.github.io/WLASL/)

**Pre-trained Models:**
- Baseline MLP: [Google Drive](your-link-here)
- LSTM Model: [Google Drive](your-link-here)

Extract to `ml_models/saved_models/`
```

### Option 2: Git LFS (Large File Storage)

```powershell
# Install Git LFS
# Download from: https://git-lfs.github.com/

# Track large files
git lfs install
git lfs track "*.h5"
git lfs track "*.pkl"

# Add .gitattributes
git add .gitattributes
git commit -m "Add Git LFS tracking"
```

**Note:** Git LFS has storage limits on free plans.

### Option 3: DVC (Data Version Control)

```powershell
# Install DVC
pip install dvc

# Initialize DVC
dvc init

# Add data to DVC
dvc add data/asl_alphabet

# Commit .dvc files (small)
git add data/.gitignore data/asl_alphabet.dvc
git commit -m "Add dataset with DVC"

# Push data to remote storage (S3, Google Drive, etc.)
dvc remote add -d storage s3://mybucket/path
dvc push
```

---

## 📊 Repository Structure in Git

```
Real-time-sign-language-TT/        (COMMITTED)
├── .gitignore                     ✓ Committed
├── README.md                      ✓ Committed
├── requirements.txt               ✓ Committed
├── manage.py                      ✓ Committed
│
├── data/                          ✗ Not committed (in .gitignore)
│   ├── .gitkeep                   ✓ Committed (preserves folder)
│   └── asl_alphabet/              ✗ Download separately
│
├── ml_models/                     ✓ Committed
│   ├── __init__.py                ✓ Committed
│   ├── train_all.py               ✓ Committed
│   ├── train_baseline.py          ✓ Committed
│   ├── train_lstm.py              ✓ Committed
│   ├── inference.py               ✓ Committed
│   ├── data_preprocessing.py      ✓ Committed
│   └── saved_models/              ✗ Not committed
│       └── .gitkeep               ✓ Committed
│
├── translator/                    ✓ Committed (all files)
├── static/                        ✓ Committed (all files)
├── templates/                     ✓ Committed (all files)
│
├── venv/                          ✗ Not committed
├── __pycache__/                   ✗ Not committed
└── db.sqlite3                     ✗ Not committed
```

---

## 🔍 Verify Your .gitignore is Working

```powershell
# Check what will be committed
git status

# Should NOT see:
# - data/asl_alphabet/
# - venv/
# - __pycache__/
# - *.h5
# - *.pkl
# - db.sqlite3

# Check what's being ignored
git status --ignored

# Should see all the large files listed as ignored
```

---

## 🆘 Troubleshooting

### Problem: Accidentally committed large files

```powershell
# Remove from git but keep locally
git rm --cached -r data/
git commit -m "Remove data folder from git"
git push origin main
```

### Problem: Repository is too large

```powershell
# Check repository size
git count-objects -vH

# Clean git history (nuclear option - use carefully!)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch data/*" \
  --prune-empty --tag-name-filter cat -- --all
```

### Problem: Want to share models with team

**Best solution:** Use Google Drive/Dropbox

```markdown
# In README.md
## Pre-trained Models

Download from: [Google Drive Link]
Extract to: `ml_models/saved_models/`
```

---

## 📝 Commit Message Guidelines

Use clear, descriptive commit messages:

```
✓ Good:
- "Add: LSTM model with sequence length optimization"
- "Fix: WebSocket connection handling in consumers.py"
- "Update: MediaPipe integration with error handling"
- "Docs: Add dataset download instructions"

✗ Bad:
- "update"
- "fix stuff"
- "asdasd"
- "commit"
```

### Commit Message Format:

```
<type>: <subject>

<body>
```

**Types:**

* `Add:` - New feature or file
* `Fix:` - Bug fix
* `Update:` - Modify existing feature
* `Refactor:` - Code refactoring
* `Docs:` - Documentation changes
* `Test:` - Add or update tests
* `Style:` - Code style changes (formatting)

---

## ✅ Final Checklist Before Push

* [ ] `.gitignore` is in place
* [ ] No large files in `git status`
* [ ] `requirements.txt` is up to date
* [ ] README.md has setup instructions
* [ ] Sensitive data (API keys) is not committed
* [ ] Code is tested locally
* [ ] Commit message is descriptive

---

## 🔗 Useful Resources

* [Git Documentation](https://git-scm.com/doc)
* [GitHub Guides](https://guides.github.com/)
* [Git LFS](https://git-lfs.github.com/)
* [DVC Documentation](https://dvc.org/doc)
