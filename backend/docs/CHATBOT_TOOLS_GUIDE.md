# Chatbot Tools and Libraries - Detailed Guide

##  Mục lục

1. [Rasa NLU Framework](#rasa-nlu-framework)
2. [scikit-learn (TF-IDF & Cosine Similarity)](#scikit-learn)
3. [Underthesea (Vietnamese NLP)](#underthesea)
4. [Transformers (ViT5)](#transformers-vit5)
5. [Regular Expressions (Entity Extraction)](#regular-expressions)
6. [SQLAlchemy (Database ORM)](#sqlalchemy)

---

## 1. Rasa NLU Framework

### 1.1. Giới thiệu

**Rasa NLU** là framework mã nguồn mở để xây dựng hệ thống hiểu ngôn ngữ tự nhiên (Natural Language Understanding). Được sử dụng cho intent classification và entity extraction.

**Website**: https://rasa.com/docs/rasa/nlu/

### 1.2. Cài đặt

```bash
pip install rasa==3.6.0
```

### 1.3. Thành phần chính

#### Pipeline Components

```python
pipeline = [
    {
        "name": "WhitespaceTokenizer",
        # Tách từ dựa trên khoảng trắng
        # Input: "xin chào bạn"
        # Output: ["xin", "chào", "bạn"]
    },
    {
        "name": "RegexFeaturizer",
        # Trích xuất features từ regex patterns
        # Ví dụ: nhận diện email, số điện thoại, mã môn học
    },
    {
        "name": "LexicalSyntacticFeaturizer",
        # Features từ đặc điểm từ vựng và cú pháp
        # Ví dụ: prefix, suffix, uppercase, digits
    },
    {
        "name": "CountVectorsFeaturizer",
        # Character n-grams để xử lý typo
        "analyzer": "char_wb",      # Character n-grams at word boundaries
        "min_ngram": 1,              # Minimum n-gram size
        "max_ngram": 4               # Maximum n-gram size
        # Ví dụ: "hello" -> ["h", "he", "hel", "hell", "e", "el", "ell", ...]
    },
    {
        "name": "DIETClassifier",
        # Dual Intent Entity Transformer
        # Deep learning model cho intent classification
        "epochs": 200                # Số epoch training
    }
]
```

### 1.4. Training Data Format

**File**: `rasa_training_data.yml`

```yaml
version: "3.1"
nlu:
  - intent: class_info
    examples: |
      - các lớp môn Giải tích
      - các lớp của môn IT4040
      - lớp học vào thứ 2
      - cho tôi các lớp thuộc học phần MI1114
      
  - intent: schedule_view
    examples: |
      - lịch học của tôi
      - các môn đã đăng ký
      - môn học kỳ này
      - xem thời khóa biểu
```

### 1.5. Sử dụng trong code

```python
from rasa.nlu.model import Interpreter, Trainer
from rasa.nlu.training_data import load_data
from rasa.nlu import config as rasa_config

# 1. Load training data
training_data = load_data("data/rasa_training_data.yml")

# 2. Create trainer
trainer = Trainer(rasa_config.load("data/rasa_nlu_config.yml"))

# 3. Train model
interpreter = trainer.train(training_data)

# 4. Save model
interpreter.persist("models/nlu")

# 5. Load and use model
interpreter = Interpreter.load("models/nlu")
result = interpreter.parse("các lớp môn Giải tích")
   
# Output:
# {
#     "intent": {
#         "name": "class_info",
#         "confidence": 0.987
#     },
#     "entities": [],
#     "text": "các lớp môn Giải tích"
# }
```

### 1.6. Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `epochs` | int | Số lần training qua toàn bộ data | 200 |
| `min_ngram` | int | Kích thước n-gram tối thiểu | 1 |
| `max_ngram` | int | Kích thước n-gram tối đa | 4 |
| `analyzer` | str | Loại analyzer (char, word, char_wb) | "char_wb" |

### 1.7. Ví dụ thực tế

```python
# Input
message = "các lớp môn giải tích"

# Step 1: Tokenization
tokens = ["các", "lớp", "môn", "giải", "tích"]

# Step 2: Character n-grams
ngrams = {
    "các": ["c", "cá", "các", "á", "ác"],
    "lớp": ["l", "lớ", "lớp", "ớ", "ớp"],
    ...
}

# Step 3: Feature extraction
features = [0.2, 0.5, 0.1, ...]  # Feature vector

# Step 4: DIET Classification
# Neural network predicts intent probabilities
probabilities = {
    "class_info": 0.92,
    "subject_info": 0.05,
    "schedule_view": 0.03
}

# Output
result = {
    "intent": "class_info",
    "confidence": 0.92
}
```

---

## 2. scikit-learn (TF-IDF & Cosine Similarity)

### 2.1. Giới thiệu

**scikit-learn** là thư viện machine learning cho Python. Sử dụng TF-IDF và Cosine Similarity cho fallback intent classification.

**Website**: https://scikit-learn.org/

### 2.2. Cài đặt

```bash
pip install scikit-learn==1.3.0
```

### 2.3. TF-IDF Vectorizer

**TF-IDF** (Term Frequency-Inverse Document Frequency) chuyển đổi text thành vector số.

#### Cách hoạt động

```python
from sklearn.feature_extraction.text import TfidfVectorizer

# Example documents
documents = [
    "các lớp môn giải tích",
    "các lớp của môn IT4040",
    "lịch học của tôi"
]

# Create vectorizer
vectorizer = TfidfVectorizer(
    tokenizer=word_tokenize,  # Vietnamese tokenizer
    ngram_range=(1, 3),       # Unigram, bigram, trigram
    max_features=5000,        # Top 5000 features
    lowercase=True,
    norm='l2'                 # L2 normalization
)

# Fit and transform
tfidf_matrix = vectorizer.fit_transform(documents)

# Result: Sparse matrix [3 x vocabulary_size]
# Each row is a document represented as TF-IDF vector
```

#### TF-IDF Formula

```
TF-IDF(t, d) = TF(t, d) × IDF(t)

where:
- TF(t, d) = frequency of term t in document d
- IDF(t) = log(N / df(t))
- N = total number of documents
- df(t) = number of documents containing term t
```

#### Ví dụ tính toán

```python
# Document: "các lớp môn giải tích"
# Vocabulary: ["các", "lớp", "môn", "giải", "tích"]

# Term frequencies:
TF = {
    "các": 1/5,   # 0.2
    "lớp": 1/5,   # 0.2
    "môn": 1/5,   # 0.2
    "giải": 1/5,  # 0.2
    "tích": 1/5   # 0.2
}

# Inverse document frequency (assume 100 docs total):
IDF = {
    "các": log(100/50) = 0.69,   # Common word
    "lớp": log(100/30) = 1.20,
    "môn": log(100/40) = 0.92,
    "giải": log(100/5) = 3.00,   # Rare word -> high IDF
    "tích": log(100/5) = 3.00
}

# TF-IDF scores:
TF_IDF = {
    "các": 0.2 × 0.69 = 0.138,
    "lớp": 0.2 × 1.20 = 0.240,
    "môn": 0.2 × 0.92 = 0.184,
    "giải": 0.2 × 3.00 = 0.600,  # High score!
    "tích": 0.2 × 3.00 = 0.600
}

# Final vector: [0.138, 0.240, 0.184, 0.600, 0.600]
```

### 2.4. Cosine Similarity

Đo độ tương đồng giữa hai vector.

```python
from sklearn.metrics.pairwise import cosine_similarity

# Two vectors
vec1 = [0.2, 0.5, 0.3]
vec2 = [0.1, 0.6, 0.2]

# Compute similarity
similarity = cosine_similarity([vec1], [vec2])[0][0]
# Result: 0.97 (very similar)
```

#### Formula

```
cosine_similarity(A, B) = (A · B) / (||A|| × ||B||)

where:
- A · B = dot product of A and B
- ||A|| = magnitude of vector A
- ||B|| = magnitude of vector B
```

#### Ví dụ tính toán

```python
# Vector A: [1, 2, 3]
# Vector B: [2, 3, 4]

# Dot product: 1×2 + 2×3 + 3×4 = 2 + 6 + 12 = 20
dot_product = 20

# Magnitude A: sqrt(1² + 2² + 3²) = sqrt(14) = 3.74
magnitude_A = 3.74

# Magnitude B: sqrt(2² + 3² + 4²) = sqrt(29) = 5.39
magnitude_B = 5.39

# Cosine similarity: 20 / (3.74 × 5.39) = 20 / 20.16 = 0.992
similarity = 0.992  # Very similar!
```

### 2.5. Sử dụng trong Intent Classification

```python
class FallbackClassifier:
    def __init__(self, intents_data):
        # Build training data
        self.intent_patterns = {}
        for intent in intents_data["intents"]:
            tag = intent["tag"]
            patterns = intent["patterns"]
            self.intent_patterns[tag] = patterns
        
        # Flatten all patterns
        all_patterns = []
        self.pattern_to_intent = []
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                all_patterns.append(pattern)
                self.pattern_to_intent.append(intent)
        
        # Create TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            tokenizer=word_tokenize,
            ngram_range=(1, 3),
            max_features=5000
        )
        
        # Fit on patterns
        self.pattern_vectors = self.vectorizer.fit_transform(all_patterns)
    
    def classify(self, message):
        # Transform message
        message_vector = self.vectorizer.transform([message])
        
        # Compute similarities with all patterns
        similarities = cosine_similarity(
            message_vector, 
            self.pattern_vectors
        )[0]
        
        # Find best match
        best_idx = np.argmax(similarities)
        best_score = similarities[best_idx]
        best_intent = self.pattern_to_intent[best_idx]
        
        return {
            "intent": best_intent,
            "score": best_score
        }
```

### 2.6. Ví dụ đầy đủ

```python
# Input
message = "cho tôi xem các lớp môn giải tích"

# Step 1: Tokenization
tokens = ["cho", "tôi", "xem", "các", "lớp", "môn", "giải", "tích"]

# Step 2: TF-IDF Vectorization
message_vector = [0.15, 0.32, 0.28, 0.42, 0.51, 0.38, 0.65, 0.71, ...]

# Step 3: Compare with all patterns
patterns = {
    "các lớp môn Giải tích": [0.12, 0.28, 0.19, 0.45, 0.52, 0.41, 0.68, 0.73, ...],
    "lịch học của tôi": [0.08, 0.18, 0.35, 0.22, 0.15, 0.28, 0.10, 0.12, ...],
    ...
}

# Step 4: Cosine similarities
similarities = {
    "các lớp môn Giải tích": 0.92,  # Best match!
    "lịch học của tôi": 0.35,
    ...
}

# Step 5: Result
result = {
    "intent": "class_info",
    "score": 0.92,
    "confidence": "high"
}
```

---

## 3. Underthesea (Vietnamese NLP)

### 3.1. Giới thiệu

**Underthesea** là thư viện xử lý ngôn ngữ tự nhiên tiếng Việt. Được sử dụng cho word tokenization.

**Website**: https://github.com/undertheseanlp/underthesea

### 3.2. Cài đặt

```bash
pip install underthesea==6.8.0
```

### 3.3. Word Tokenization

Tách từ tiếng Việt (Vietnamese word segmentation).

```python
from underthesea import word_tokenize

# Example 1: Simple sentence
text = "tôi muốn xem lớp học"
tokens = word_tokenize(text)
# Output: ["tôi", "muốn", "xem", "lớp_học"]

# Example 2: Complex sentence
text = "các lớp của môn Lập trình hướng đối tượng"
tokens = word_tokenize(text)
# Output: ["các", "lớp", "của", "môn", "Lập_trình", "hướng", "đối_tượng"]

# Example 3: With format option
tokens = word_tokenize(text, format="text")
# Output: "các lớp của môn Lập_trình hướng đối_tượng"
```

### 3.4. Tại sao cần word tokenization?

Tiếng Việt có nhiều từ đa âm tiết (compound words):

```python
# Without tokenization
"lập trình hướng đối tượng"  # 5 words or 2 words?

# With tokenization
["Lập_trình", "hướng", "đối_tượng"]  # Clear: 3 meaningful units

# Benefits:
# 1. Better TF-IDF features
# 2. Correct word boundaries
# 3. Preserve meaning of compound words
```

### 3.5. Ví dụ thực tế

```python
# Scenario: Intent classification
query = "các lớp học kỳ này"

# Without tokenization
basic_tokens = query.split()
# Result: ["các", "lớp", "học", "kỳ", "này"]
# Problem: "học kỳ" (semester) split incorrectly

# With underthesea
proper_tokens = word_tokenize(query)
# Result: ["các", "lớp", "học_kỳ", "này"]
# Better: "học_kỳ" kept as one unit

# Impact on TF-IDF:
# - "học_kỳ" treated as single meaningful term
# - Better feature representation
# - More accurate similarity matching
```

### 3.6. Parameters

```python
word_tokenize(
    text,                    # Input text
    format="text"|"dict",   # Output format
    fixed_words=[],          # Custom compound words
    remove_accent=False      # Keep diacritics
)
```

### 3.7. Integration với TF-IDF

```python
from underthesea import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer

# Custom tokenizer function
def vietnamese_tokenizer(text):
    return word_tokenize(text, format="text").split()

# Create vectorizer with Vietnamese tokenizer
vectorizer = TfidfVectorizer(
    tokenizer=vietnamese_tokenizer,  # Use underthesea
    ngram_range=(1, 3),
    max_features=5000
)

# Now Vietnamese text is properly tokenized!
```

---

## 4. Transformers (ViT5)

### 4.1. Giới thiệu

**Transformers** là thư viện của Hugging Face cho pre-trained models. **ViT5** là Vietnamese T5 model cho text generation.

**Website**: https://huggingface.co/VietAI/vit5-base

### 4.2. Cài đặt

```bash
pip install transformers==4.35.0
pip install torch==2.0.0
```

### 4.3. ViT5 Model

T5 (Text-to-Text Transfer Transformer) - tất cả tasks đều là text-to-text.

```python
from transformers import T5ForConditionalGeneration, T5Tokenizer

# Load pre-trained model
model_name = "VietAI/vit5-base"
tokenizer = T5Tokenizer.from_pretrained(model_name)
model = T5ForConditionalGeneration.from_pretrained(model_name)
```

### 4.4. Fine-tuning cho NL2SQL

```python
# Training data format
training_examples = [
    {
        "question": "các lớp môn Giải tích",
        "sql": "SELECT c.class_id, c.class_name FROM classes c ..."
    },
    ...
]

# Prepare data
inputs = []
targets = []
for example in training_examples:
    # Add prefix for task identification
    input_text = f"nl2sql: {example['question']}"
    target_text = example['sql']
    
    inputs.append(input_text)
    targets.append(target_text)

# Tokenize
input_encodings = tokenizer(
    inputs, 
    padding=True, 
    truncation=True,
    max_length=128,
    return_tensors="pt"
)

target_encodings = tokenizer(
    targets,
    padding=True,
    truncation=True,
    max_length=256,
    return_tensors="pt"
)

# Training
from transformers import Trainer, TrainingArguments

training_args = TrainingArguments(
    output_dir="./models/vit5-nl2sql",
    num_train_epochs=10,
    per_device_train_batch_size=8,
    save_steps=100,
    logging_steps=10
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    tokenizer=tokenizer
)

trainer.train()
```

### 4.5. Inference

```python
# Load fine-tuned model
tokenizer = T5Tokenizer.from_pretrained("./models/vit5-nl2sql")
model = T5ForConditionalGeneration.from_pretrained("./models/vit5-nl2sql")

# Generate SQL
question = "các lớp môn Giải tích"
input_text = f"nl2sql: {question}"

# Tokenize
inputs = tokenizer(
    input_text,
    return_tensors="pt",
    max_length=128,
    truncation=True
)

# Generate
outputs = model.generate(
    inputs["input_ids"],
    max_length=256,
    num_beams=5,              # Beam search
    early_stopping=True,
    temperature=0.8           # Creativity
)

# Decode
sql = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(sql)
# Output: "SELECT c.class_id, c.class_name FROM classes c ..."
```

### 4.6. Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `max_length` | int | Maximum sequence length | 256 |
| `num_beams` | int | Beam search width | 5 |
| `temperature` | float | Sampling temperature (0-1) | 0.8 |
| `early_stopping` | bool | Stop when beam sequences done | True |
| `no_repeat_ngram_size` | int | Prevent n-gram repetition | 3 |

---

## 5. Regular Expressions (Entity Extraction)

### 5.1. Giới thiệu

**Regular expressions** (regex) cho pattern matching và entity extraction.

**Docs**: https://docs.python.org/3/library/re.html

### 5.2. Patterns cho chatbot

```python
import re

# Subject ID: IT4040, MI1114, EM1180Q
SUBJECT_ID = r'\b([A-Z]{2,4}\d{4}[A-Z]?)\b'

# Class ID: 161084 (6 digits)
CLASS_ID = r'\blớp\s+(\d{6})\b'

# Subject name: Extract after keywords
SUBJECT_NAME = r'các lớp của môn ([^,\?\.]+?)(?:\s*$|,|\?|\.)'
```

### 5.3. Extraction examples

```python
# Example 1: Subject ID with optional suffix
text = "các lớp của môn EM1180Q"
match = re.search(r'\b([A-Z]{2,4}\d{4}[A-Z]?)\b', text)
if match:
    subject_id = match.group(1)
    # Result: "EM1180Q"

# Example 2: Subject name
text = "lớp của học phần Lý thuyết điều khiển tự động"
patterns = [
    r'lớp của học phần ([^,\?\.]+?)(?:\s*$|,|\?|\.)',
    r'môn ([^,\?\.]+?)(?:\s*$|,|\?|\.)',
]
for pattern in patterns:
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        subject_name = match.group(1).strip()
        # Result: "Lý thuyết điều khiển tự động"
        break

# Example 3: Multiple entities
text = "lớp 161084 môn IT4040 vào thứ 2"

# Extract class_id
class_match = re.search(r'\blớp\s+(\d{6})\b', text)
class_id = class_match.group(1) if class_match else None

# Extract subject_id
subject_match = re.search(r'\b([A-Z]{2,4}\d{4}[A-Z]?)\b', text)
subject_id = subject_match.group(1) if subject_match else None

# Result: {"class_id": "161084", "subject_id": "IT4040"}
```

### 5.4. Pattern explanation

```python
# Pattern: r'\b([A-Z]{2,4}\d{4}[A-Z]?)\b'

\b          # Word boundary
(           # Capture group
  [A-Z]     # Uppercase letter
  {2,4}     # 2-4 times (IT, MI, EM, MATH)
  \d        # Digit
  {4}       # Exactly 4 times
  [A-Z]?    # Optional uppercase suffix (Q in EM1180Q)
)
\b          # Word boundary

# Matches: IT4040, MI1114, EM1180Q, MATH1234
# Doesn't match: it4040 (lowercase), IT40 (too short)
```

---

## 6. SQLAlchemy (Database ORM)

### 6.1. Giới thiệu

**SQLAlchemy** là Python SQL toolkit và ORM.

**Website**: https://www.sqlalchemy.org/

### 6.2. Cài đặt

```bash
pip install sqlalchemy==2.0.0
pip install pymysql==1.1.0
```

### 6.3. Connection

```python
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Create engine
DATABASE_URL = "mysql+pymysql://user:pass@localhost/student_db"
engine = create_engine(DATABASE_URL, echo=True)

# Create session
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()
```

### 6.4. Execute SQL

```python
from sqlalchemy import text

# Simple query
sql = "SELECT * FROM students WHERE id = :student_id"
result = db.execute(text(sql), {"student_id": 1})
row = result.fetchone()

# Fetch all
sql = "SELECT * FROM classes WHERE subject_id = :subject_id"
result = db.execute(text(sql), {"subject_id": 101})
rows = result.fetchall()

# Convert to dict
columns = result.keys()
data = [dict(zip(columns, row)) for row in rows]
```

### 6.5. ORM Models

```python
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True)
    student_name = Column(String(255))
    email = Column(String(255))
    cpa = Column(Float)

# Query using ORM
student = db.query(Student).filter(Student.id == 1).first()
print(student.student_name)
```

---

## 7. Tổng kết

### 7.1. Tool Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| API | FastAPI | REST endpoints |
| Intent | Rasa NLU + scikit-learn | Classification |
| Tokenization | Underthesea | Vietnamese word segmentation |
| NL2SQL | Custom + ViT5 | SQL generation |
| Entity | Regex | Pattern matching |
| Database | SQLAlchemy | ORM and queries |

### 7.2. Performance

| Component | Time | Accuracy |
|-----------|------|----------|
| Intent Classification | ~60ms | 95-100% |
| Entity Extraction | ~5ms | 90-95% |
| SQL Generation | ~10ms | 70-80% (rule-based) |
| Database Query | ~50ms | 100% |
| **Total** | **~125ms** | **85-90%** |

---

**Document version**: 1.0
**Last updated**: November 13, 2025
