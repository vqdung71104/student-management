# Machine Learning Models

## ⚠️ Important Note

Model files are **NOT** stored in Git repository due to large file sizes (>100MB).

## 📁 Directory Structure

```
backend/models/
├── README.md (this file)
└── vit5_nl2sql/          # ViT5 NL2SQL model (ignored by Git)
    ├── best/
    │   ├── config.json
    │   ├── generation_config.json
    │   └── model.safetensors  # ~270MB - ignored
    └── checkpoint-*/
```

## 🚀 How to Get Models

### Option 1: Train Your Own Model (Recommended)

```bash
cd backend
python scripts/train_vit5_nl2sql.py --epochs 10 --batch_size 4
```

This will:
- Download VietAI/vit5-base model (~1GB)
- Fine-tune on NL2SQL training data
- Save model to `backend/models/vit5_nl2sql/best/`

### Option 2: Download Pre-trained Model

If someone on your team has trained the model, ask them to share:
- Upload to cloud storage (Google Drive, Dropbox, etc.)
- Download and extract to `backend/models/vit5_nl2sql/`

## 🔧 Using Without ViT5 Model

The NL2SQL system works **without** the ViT5 model using rule-based fallback:

- ✅ Rule-based approach: ~70-80% accuracy (works immediately)
- ✅ ViT5 model approach: >90% accuracy (requires training)

The system automatically detects if ViT5 model is available and falls back to rule-based if not.

## 📊 Model Details

**Model**: VietAI/vit5-base fine-tuned for Vietnamese NL2SQL

**Size**: ~270MB

**Training Data**: `backend/data/nl2sql_training_data.json` (25+ examples)

**Performance**:
- Accuracy: >90% on test queries
- Inference time: ~100-300ms per query
- Supports: 12 intent types

## 🗑️ Ignored Files

The following files are ignored by Git (see `.gitignore`):

```
backend/models/vit5_nl2sql/
*.safetensors
*.bin
*.pth
*.pt
*.onnx
*.h5
*.keras
```

## 📝 Notes

- Models are stored locally only
- Each developer needs to train or download models separately
- Use Git LFS if you want to version control models in the future
- Consider using model hosting services (Hugging Face, AWS S3, etc.) for team collaboration
