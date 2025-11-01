"""
Script kiểm tra cài đặt PhoBERT và dependencies
"""
import sys

print("="*70)
print("🔍 CHECKING PHOBERT INSTALLATION")
print("="*70)

# 1. Check Python version
print(f"\n1️⃣ Python version: {sys.version}")
if sys.version_info < (3, 8):
    print("   ❌ Python >= 3.8 required")
else:
    print("   ✅ Python version OK")

# 2. Check required packages
packages_to_check = [
    "transformers",
    "sentence_transformers", 
    "torch",
    "sklearn",
    "numpy",
    "google.generativeai"
]


# 2. Check CUDA availability
try:
    import torch
    print(f"\n2. PyTorch:")
    print(f"   Version: {torch.__version__}")
    print(f"   CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"   CUDA version: {torch.version.cuda}")
    else:
        print("   ℹ️  Running on CPU (slower but OK)")
except Exception as e:
    print(f"   ⚠️  {e}")

# 3. Test sentence-transformers
print(f"\n3️⃣ Testing Sentence Transformers:")
try:
    from sentence_transformers import SentenceTransformer
    print("   Attempting to load Vietnamese SBERT...")
    
    # Try Vietnamese model
    try:
        model = SentenceTransformer('keepitreal/vietnamese-sbert')
        print("   ✅ Vietnamese SBERT loaded successfully")
        
        # Test encoding
        test_text = "Xin chào"
        embedding = model.encode([test_text])
        print(f"   ✅ Test encoding successful (shape: {embedding.shape})")
        
    except Exception as e:
        print(f"   ⚠️  Vietnamese SBERT failed: {e}")
        print("   Trying multilingual fallback...")
        
        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        print("   ✅ Multilingual model loaded successfully")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

# 4. Check Google AI
print(f"\n4️⃣ Testing Google Generative AI:")
try:
    import os
    from dotenv import load_dotenv
    import google.generativeai as genai
    
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key or api_key == "your_google_api_key_here":
        print("   ⚠️  GOOGLE_API_KEY not configured in .env")
    else:
        print("   ✅ GOOGLE_API_KEY found")
        
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('models/gemini-pro')
            print("   ✅ Gemini model initialized")
        except Exception as e:
            print(f"   ⚠️  Gemini error: {e}")
            
except Exception as e:
    print(f"   ❌ Error: {e}")

# 5. Check intents.json
print(f"\n5️⃣ Checking intents.json:")
try:
    import json
    import os
    
    intents_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "intents.json"
    )
    
    with open(intents_path, "r", encoding="utf-8") as f:
        intents_data = json.load(f)
    
    num_intents = len(intents_data.get("intents", []))
    print(f"   ✅ intents.json found with {num_intents} intents")
    
    for intent in intents_data.get("intents", []):
        print(f"      - {intent['tag']}: {len(intent['patterns'])} patterns")
        
except Exception as e:
    print(f"   ❌ Error loading intents.json: {e}")

# 6. Test classifiers
print(f"\n6️⃣ Testing Classifiers:")
try:
    print("   Testing PhoBERT classifier...")
    from app.chatbot.phobert_classifier import PhoBERTIntentClassifier
    phobert = PhoBERTIntentClassifier()
    print("   ✅ PhoBERT classifier initialized")
    
except Exception as e:
    print(f"   ❌ PhoBERT error: {e}")
    import traceback
    traceback.print_exc()

try:
    print("   Testing Gemini classifier...")
    from app.chatbot.intent_classifier import IntentClassifier
    gemini = IntentClassifier()
    print("   ✅ Gemini classifier initialized")
    
except Exception as e:
    print(f"   ❌ Gemini error: {e}")

try:
    print("   Testing Hybrid classifier...")
    from app.chatbot.hybrid_classifier import HybridIntentClassifier
    hybrid = HybridIntentClassifier(use_phobert=True, use_gemini=True)
    print("   ✅ Hybrid classifier initialized")
    
except Exception as e:
    print(f"   ❌ Hybrid error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("✅ CHECK COMPLETE!")
print("="*70)
print("\nIf all checks passed, you can:")
print("1. Run: uvicorn main:app --reload --host localhost --port 8000")
print("2. Test: python test_phobert.py")
print("="*70)
