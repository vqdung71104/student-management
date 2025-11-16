"""
TF-IDF Intent Classifier cho tiếng Việt
Sử dụng TF-IDF Vectorizer, Cosine Similarity và Word2Vec Embeddings
Phase 2: TF-IDF + Word2Vec Semantic Embeddings
"""
import json
import os
import re
from typing import Dict, List, Tuple, Optional
import numpy as np
from pathlib import Path

# Scikit-learn imports for Phase 1
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Gensim imports for Phase 2
from gensim.models import Word2Vec
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)


class TfidfIntentClassifier:
    """
    Intent classifier sử dụng TF-IDF Vectorizer, Cosine Similarity và Word2Vec
    
    Phase 2: TF-IDF + Word2Vec Semantic Embeddings
    - TfidfVectorizer cho statistical feature extraction
    - Word2Vec cho semantic understanding
    - cosine_similarity từ sklearn.metrics.pairwise
    - Weighted scoring với TF-IDF + Semantic + Keyword
    
    Công nghệ sử dụng:
    - TfidfVectorizer: Chuyển đổi text thành vector TF-IDF (statistical features)
    - Word2Vec: Học word embeddings từ training data (semantic features)
    - cosine_similarity: Tính độ tương đồng giữa các vector
    
    Parameters trong TfidfVectorizer:
    - ngram_range: Khoảng n-gram (mặc định (1,3) - từ unigram đến trigram)
    - max_features: Số lượng features tối đa (mặc định 5000)
    - analyzer: 'word' hoặc 'char' (mặc định 'word')
    - lowercase: Chuyển về chữ thường (mặc định True)
    - min_df: Minimum document frequency (mặc định 1)
    - max_df: Maximum document frequency (mặc định 1.0)
    
    Parameters trong Word2Vec:
    - vector_size: Kích thước của word vectors (mặc định 100)
    - window: Kích thước context window (mặc định 5)
    - min_count: Tần suất tối thiểu của từ (mặc định 1)
    - workers: Số threads cho training (mặc định 4)
    - sg: Skip-gram (1) hoặc CBOW (0) (mặc định 1)
    
    Ví dụ sử dụng:
    ```python
    # Khởi tạo classifier
    classifier = TfidfIntentClassifier()
    
    # Phân loại intent
    result = await classifier.classify_intent("tôi nên đăng ký môn gì")
    # Output: {
    #   "intent": "subject_registration_suggestion",
    #   "confidence": "high",
    #   "confidence_score": 0.85,
    #   "method": "tfidf_cosine",
    #   ...
    # }
    
    # Lấy tất cả độ tương đồng
    similarities = classifier.get_all_similarities("xem điểm")
    # Output: [("grade_view", 0.92), ("student_info", 0.45), ...]
    ```
    
    Phân tích cú pháp:
    1. Normalization: Chuẩn hóa text (lowercase, remove punctuation, synonyms)
    2. Tokenization: Tách từ bằng whitespace
    3. TF-IDF Vectorization: Chuyển text thành vector TF-IDF (statistical)
    4. Word2Vec Embedding: Chuyển text thành semantic vector
    5. Cosine Similarity: Tính độ tương đồng cosine
    6. Keyword Matching: Tăng điểm cho các từ khóa xuất hiện
    7. Scoring: Kết hợp TF-IDF (50%) + Semantic (30%) + Keyword (20%)
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize TF-IDF Intent Classifier
        
        Args:
            config_path: Đường dẫn đến file config (optional)
        """
        print("🔧 Initializing TF-IDF Intent Classifier (Phase 3 - Fine-tuned)...")
        
        # Load config
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "data",
                "rasa_config.json"
            )
        
        self.config = self._load_config(config_path)
        self.intents = self._load_intents()
        
        # Vietnamese synonyms for better matching
        self.synonyms = {
            "đăng ký": ["dang ky", "dk", "đk", "dang ki", "đăng kí"],
            "môn học": ["mon hoc", "môn", "mon", "học phần", "hoc phan", "hp"],
            "lớp học": ["lop hoc", "lớp", "lop", "class", "lớp học phần"],
            "điểm": ["diem", "điểm số", "diem so", "grade", "score", "điểm thi"],
            "lịch": ["lich", "thời khóa biểu", "thoi khoa bieu", "tkb", "schedule"],
            "xem": ["view", "check", "kiểm tra", "kiem tra", "tra cứu", "tra cuu"],
            "học": ["hoc", "study", "learn"],
            "nên": ["nen", "should", "phải", "phai", "cần", "can"],
            "gì": ["gi", "what", "gì đây", "gi day"],
            "nào": ["nao", "which"],
            "như thế nào": ["nhu the nao", "ra sao", "thế nào", "the nao"],
            "hướng dẫn": ["huong dan", "guide", "chỉ dẫn", "chi dan", "hddn"],
            "cảm ơn": ["cam on", "thank", "thanks", "cám ơn", "thank you"],
            "chào": ["chao", "hello", "hi", "xin chào", "xin chao"],
        }
        
        # TF-IDF Vectorizer (Phase 1 configuration)
        self.tfidf_vectorizer = None
        self.intent_tfidf_matrix = None
        self.intent_labels = []
        self.intent_patterns_map = {}
        self.intent_keywords_map = {}
        
        # Word2Vec Model (Phase 2 configuration)
        self.word2vec_model = None
        self.intent_embeddings_map = {}
        
        # Thresholds cho confidence levels
        self.thresholds = self.config.get("thresholds", {
            "high_confidence": 0.60,
            "medium_confidence": 0.40,
            "low_confidence": 0.25
        })
        
        # Initialize TF-IDF components
        self._initialize_tfidf()
        
        # Initialize Word2Vec embeddings (Phase 2)
        self._initialize_word_embeddings()
        
        print(f"✅ TF-IDF + Word2Vec classifier initialized with {len(self.intents.get('intents', []))} intents")
        print(f" TF-IDF Matrix shape: {self.intent_tfidf_matrix.shape if self.intent_tfidf_matrix is not None else 'N/A'}")
        print(f" Vocabulary size: {len(self.tfidf_vectorizer.vocabulary_) if self.tfidf_vectorizer else 0}")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration từ file JSON"""
        try:
            with open(config_path, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️  Config file not found at {config_path}, using default config")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default TF-IDF configuration"""
        return {
            "language": "vi",
            "tfidf_params": {
                "ngram_range": [1, 3],  # Unigram to trigram
                "max_features": 5000,    # Maximum vocabulary size
                "analyzer": "word",      # Word-level analysis
                "lowercase": True,       # Convert to lowercase
                "min_df": 1,            # Minimum document frequency
                "max_df": 1.0,          # Maximum document frequency
                "sublinear_tf": True    # Apply sublinear tf scaling (1 + log(tf))
            },
            "word2vec_params": {
                "vector_size": 150,     # Dimensionality of word vectors (optimized)
                "window": 7,            # Context window size (optimized)
                "min_count": 1,         # Minimum word frequency
                "workers": 4,           # Number of threads
                "sg": 1,                # Skip-gram (1) or CBOW (0)
                "epochs": 20,           # Training epochs (optimized)
                "negative": 10,         # Negative sampling
                "ns_exponent": 0.75,    # Smooth negative sampling
                "alpha": 0.025,         # Initial learning rate
                "min_alpha": 0.0001     # Final learning rate
            },
            "scoring_weights": {
                "tfidf": 0.5,      # 50% weight on TF-IDF similarity
                "semantic": 0.3,   # 30% weight on semantic similarity (Word2Vec)
                "keyword": 0.2     # 20% weight on keyword matching
            },
            "thresholds": {
                "high_confidence": 0.60,
                "medium_confidence": 0.40,
                "low_confidence": 0.25
            }
        }
    
    def _load_intents(self) -> Dict:
        """Load intents từ file JSON"""
        intents_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "intents.json"
        )
        
        try:
            with open(intents_path, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f" Intents file not found at {intents_path}")
            return {"intents": []}
    
    def _normalize_vietnamese(self, text: str) -> str:
        """
        Chuẩn hóa Vietnamese text
        
        Các bước xử lý:
        1. Lowercase
        2. Remove punctuation (giữ lại chữ cái tiếng Việt)
        3. Remove extra whitespace
        4. Apply synonyms mapping
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        
        Ví dụ:
            Input: "Tôi nên ĐĂNG KÝ môn gì???"
            Output: "tôi nên đăng ký môn gì"
        """
        text = text.lower().strip()
        
        # Remove punctuation but keep Vietnamese characters
        text = re.sub(r'[^\w\sàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Apply synonyms - replace variants with canonical forms
        for canonical, variants in self.synonyms.items():
            for variant in variants:
                # Use word boundary to avoid partial replacements
                text = re.sub(r'\b' + re.escape(variant) + r'\b', canonical, text)
        
        return text.strip()
    
    def _augment_short_patterns(self, patterns: List[str]) -> List[str]:
        """
        Tự động tạo short variants từ long patterns
        
        Phase 3 Enhancement: Generate short patterns from long ones
        
        Args:
            patterns: Original patterns
            
        Returns:
            Augmented patterns list
        
        Ví dụ:
            Input: ["xem điểm của tôi", "cho tôi xem điểm"]
            Output: [
                "xem điểm của tôi",
                "cho tôi xem điểm",
                "điểm của tôi",     # Remove prefix
                "xem điểm",         # Remove suffix
                "điểm"              # Keep only keyword
            ]
        """
        augmented = list(patterns)
        
        # Common prefixes/suffixes to remove
        prefixes = ["xem", "cho", "tôi", "muốn", "cần", "em", "hãy", "cho tôi"]
        suffixes = ["của tôi", "tôi", "em", "ạ", "nhé", "được không"]
        stopwords = ["của", "cho", "muốn", "cần", "được", "không"]
        
        for pattern in patterns[:]:
            words = pattern.lower().split()
            
            if len(words) > 2:
                # Remove first word if it's a common prefix
                if words[0] in prefixes:
                    variant = " ".join(words[1:])
                    if variant not in [p.lower() for p in augmented]:
                        augmented.append(variant)
                
                # Remove last words if they're common suffixes
                suffix_text = " ".join(words[-2:]) if len(words) > 2 else words[-1]
                if suffix_text in suffixes or words[-1] in suffixes:
                    variant = " ".join(words[:-1]) if words[-1] in suffixes else " ".join(words[:-2])
                    if variant and variant not in [p.lower() for p in augmented]:
                        augmented.append(variant)
                
                # Keep only keywords (remove stopwords)
                keywords = [w for w in words if w not in stopwords and w not in prefixes and w not in suffixes]
                if len(keywords) >= 1 and len(keywords) < len(words):
                    variant = " ".join(keywords)
                    if variant not in [p.lower() for p in augmented]:
                        augmented.append(variant)
        
        return augmented
    
    def _calculate_adaptive_weights(self, message: str) -> Dict[str, float]:
        """
        Calculate adaptive scoring weights based on message characteristics
        
        Phase 3 Enhancement: Different weights for different query lengths
        
        Args:
            message: User message
            
        Returns:
            Dict with weights for tfidf, semantic, keyword
        
        Strategy:
        - Short queries (≤3 words): Rely more on keyword matching
        - Medium queries (4-8 words): Balanced approach
        - Long queries (>8 words): Rely more on semantic understanding
        
        Ví dụ:
            "điểm" (1 word) → {tfidf: 0.3, semantic: 0.2, keyword: 0.5}
            "xem điểm của tôi" (4 words) → {tfidf: 0.5, semantic: 0.3, keyword: 0.2}
            "tôi muốn xem điểm học kỳ này của mình" (8+ words) → {tfidf: 0.3, semantic: 0.5, keyword: 0.2}
        """
        normalized = self._normalize_vietnamese(message)
        msg_len = len(normalized.split())
        
        if msg_len <= 3:
            # Short query → keyword is king
            return {
                "tfidf": 0.3,
                "semantic": 0.2,
                "keyword": 0.5
            }
        elif msg_len <= 8:
            # Medium → balanced (similar to default)
            return {
                "tfidf": 0.5,
                "semantic": 0.3,
                "keyword": 0.2
            }
        else:
            # Long → semantic is more important
            return {
                "tfidf": 0.3,
                "semantic": 0.5,
                "keyword": 0.2
            }
    
    def _calculate_exact_match_bonus(self, message: str, intent_tag: str) -> float:
        """
        Calculate bonus score for exact or near-exact pattern matches
        
        Phase 3 Enhancement: Boost confidence for exact matches
        
        Args:
            message: User message
            intent_tag: Intent tag
            
        Returns:
            Bonus score (0.0 to 0.2)
        
        Ví dụ:
            Message: "điểm của tôi"
            Pattern: "điểm của tôi" → Bonus 0.2 (exact match)
            Pattern: "xem điểm của tôi" → Bonus 0.1 (partial match)
            Pattern: "điểm học kỳ này" → Bonus 0.0 (no match)
        """
        normalized_msg = self._normalize_vietnamese(message)
        patterns = self.intent_patterns_map.get(intent_tag, [])
        
        for pattern in patterns:
            # Exact match
            if normalized_msg == pattern:
                return 0.2
            # Message is substring of pattern
            elif normalized_msg in pattern:
                return 0.15
            # Pattern is substring of message
            elif pattern in normalized_msg:
                return 0.1
        
        return 0.0
    
    def _apply_confidence_boost(self, message: str, best_result: Dict) -> Dict:
        """
        Apply confidence boost based on strong signals
        
        Phase 3 Enhancement: Boost confidence when we have strong indicators
        
        Args:
            message: User message
            best_result: Best classification result
            
        Returns:
            Updated result with boosted score
        
        Boost conditions:
        1. High keyword match (≥0.8) → +0.15
        2. High TF-IDF (≥0.7) → +0.1
        3. Short query with good keyword match → +0.2
        4. High semantic similarity (≥0.8) → +0.1
        
        Ví dụ:
            "điểm của tôi"
            - keyword_score = 1.0 → boost +0.15
            - short query (3 words) + keyword ≥0.6 → boost +0.2
            - Total boost: +0.35
            - Final score: 0.45 + 0.35 = 0.80 (HIGH)
        """
        score = best_result["score"]
        boost_amount = 0.0
        boost_reasons = []
        
        # 1. High keyword match
        if best_result.get("keyword", 0) >= 0.8:
            boost_amount += 0.15
            boost_reasons.append("high_keyword")
        
        # 2. High TF-IDF
        if best_result.get("tfidf", 0) >= 0.7:
            boost_amount += 0.1
            boost_reasons.append("high_tfidf")
        
        # 3. Short query with good keyword match
        normalized = self._normalize_vietnamese(message)
        msg_len = len(normalized.split())
        if msg_len <= 3 and best_result.get("keyword", 0) >= 0.6:
            boost_amount += 0.2
            boost_reasons.append("short_query_keyword")
        
        # 4. High semantic similarity
        if best_result.get("semantic", 0) >= 0.8:
            boost_amount += 0.1
            boost_reasons.append("high_semantic")
        
        # Apply boost (cap at 1.0)
        boosted_score = min(1.0, score + boost_amount)
        
        return {
            **best_result,
            "score": boosted_score,
            "original_score": score,
            "boost_applied": boost_amount,
            "boost_reasons": boost_reasons
        }
    
    def _initialize_tfidf(self):
        """
        Initialize TF-IDF Vectorizer and fit on training patterns
        
        Phase 1: TF-IDF Only
        
        Quy trình:
        1. Collect all patterns from intents.json
        2. Augment patterns with synonym variations
        3. Normalize all patterns
        4. Initialize TfidfVectorizer with configured parameters
        5. Fit vectorizer on all patterns
        6. Transform patterns to TF-IDF matrix
        7. Store intent labels and keywords
        
        TF-IDF Formula:
        - TF (Term Frequency): số lần xuất hiện của từ trong document
        - IDF (Inverse Document Frequency): log(N / df) 
          N = tổng số documents, df = số documents chứa từ đó
        - TF-IDF = TF × IDF
        
        Ví dụ:
        Pattern: "tôi nên đăng ký môn gì"
        TF-IDF vector: [0.0, 0.45, 0.0, 0.32, ..., 0.51]
                        ^      ^           ^          ^
                        word1  đăng        môn        gì
        """
        print("🔄 Initializing TF-IDF components...")
        
        all_patterns = []
        intent_labels = []
        intent_patterns_map = {}
        intent_keywords_map = {}
        
        for intent in self.intents.get("intents", []):
            tag = intent["tag"]
            patterns = intent["patterns"]
            
            # Phase 3: Augment with short patterns first
            augmented_patterns = self._augment_short_patterns(patterns)
            
            # Then augment with synonym variations
            base_patterns = list(augmented_patterns)
            
            for pattern in base_patterns[:]:
                # Create variations by replacing synonyms
                for canonical, variants in self.synonyms.items():
                    if canonical in pattern.lower():
                        for variant in variants[:2]:  # Add up to 2 variations per synonym
                            variation = re.sub(
                                r'\b' + re.escape(canonical) + r'\b',
                                variant,
                                pattern.lower()
                            )
                            if variation not in [p.lower() for p in augmented_patterns]:
                                augmented_patterns.append(variation)
            
            # Normalize patterns
            normalized_patterns = [self._normalize_vietnamese(p) for p in augmented_patterns]
            
            # Store patterns and labels
            for norm_pattern in normalized_patterns:
                all_patterns.append(norm_pattern)
                intent_labels.append(tag)
            
            intent_patterns_map[tag] = normalized_patterns
            
            # Extract keywords (unique words from patterns)
            keywords = set()
            for pattern in normalized_patterns:
                words = pattern.split()
                keywords.update(words)
            intent_keywords_map[tag] = keywords
        
        # Initialize TfidfVectorizer with configured parameters
        tfidf_params = self.config.get("tfidf_params", {})
        ngram_range = tuple(tfidf_params.get("ngram_range", [1, 3]))
        max_features = tfidf_params.get("max_features", 5000)
        analyzer = tfidf_params.get("analyzer", "word")
        lowercase = tfidf_params.get("lowercase", True)
        min_df = tfidf_params.get("min_df", 1)
        max_df = tfidf_params.get("max_df", 1.0)
        sublinear_tf = tfidf_params.get("sublinear_tf", True)
        
        self.tfidf_vectorizer = TfidfVectorizer(
            ngram_range=ngram_range,
            max_features=max_features,
            analyzer=analyzer,
            lowercase=lowercase,
            min_df=min_df,
            max_df=max_df,
            sublinear_tf=sublinear_tf,
            token_pattern=r'\b\w+\b'  # Match word boundaries
        )
        
        # Fit and transform patterns
        if all_patterns:
            self.intent_tfidf_matrix = self.tfidf_vectorizer.fit_transform(all_patterns)
            self.intent_labels = intent_labels
            self.intent_patterns_map = intent_patterns_map
            self.intent_keywords_map = intent_keywords_map
            
            print(f" TF-IDF initialized:")
            print(f"   - Total patterns: {len(all_patterns)}")
            print(f"   - Vocabulary size: {len(self.tfidf_vectorizer.vocabulary_)}")
            print(f"   - N-gram range: {ngram_range}")
            print(f"   - Max features: {max_features}")
            print(f"   - Matrix shape: {self.intent_tfidf_matrix.shape}")
        else:
            print("  No patterns found to initialize TF-IDF")
    
    def _initialize_word_embeddings(self):
        """
        Initialize Word2Vec model từ training patterns
        
        Phase 2: Word2Vec Semantic Embeddings
        
        Quy trình:
        1. Collect all patterns và tokenize thành sentences (list of words)
        2. Train Word2Vec model trên tất cả patterns
        3. Tính sentence embeddings cho mỗi intent (average of word vectors)
        4. Store embeddings cho từng intent
        
        Word2Vec Algorithm:
        - Skip-gram: Dự đoán context words từ center word
        - CBOW: Dự đoán center word từ context words
        - Output: Dense vectors cho mỗi word (vector_size dimensions)
        
        Ví dụ:
        Sentences: [
            ["tôi", "nên", "đăng", "ký", "môn", "gì"],
            ["tôi", "muốn", "đăng", "ký", "lớp", "học"]
        ]
        
        Word vectors:
        - "tôi": [0.23, -0.45, 0.12, ..., 0.67]
        - "đăng": [0.34, 0.21, -0.33, ..., 0.11]
        - "ký": [0.31, 0.18, -0.29, ..., 0.09]
        
        Sentence embedding (average):
        - [0.29, -0.02, -0.17, ..., 0.29]
        """
        print("🔄 Initializing Word2Vec embeddings...")
        
        # Collect sentences for training
        sentences = []
        intent_sentences_map = {}
        
        for intent in self.intents.get("intents", []):
            tag = intent["tag"]
            patterns = intent["patterns"]
            
            intent_sentences = []
            for pattern in patterns:
                # Normalize và tokenize
                normalized = self._normalize_vietnamese(pattern)
                words = normalized.split()
                if words:
                    sentences.append(words)
                    intent_sentences.append(words)
            
            intent_sentences_map[tag] = intent_sentences
        
        # Train Word2Vec model
        if sentences:
            w2v_params = self.config.get("word2vec_params", {})
            vector_size = w2v_params.get("vector_size", 150)
            window = w2v_params.get("window", 7)
            min_count = w2v_params.get("min_count", 1)
            workers = w2v_params.get("workers", 4)
            sg = w2v_params.get("sg", 1)
            epochs = w2v_params.get("epochs", 20)
            negative = w2v_params.get("negative", 10)
            ns_exponent = w2v_params.get("ns_exponent", 0.75)
            alpha = w2v_params.get("alpha", 0.025)
            min_alpha = w2v_params.get("min_alpha", 0.0001)
            
            self.word2vec_model = Word2Vec(
                sentences=sentences,
                vector_size=vector_size,
                window=window,
                min_count=min_count,
                workers=workers,
                sg=sg,
                epochs=epochs,
                negative=negative,
                ns_exponent=ns_exponent,
                alpha=alpha,
                min_alpha=min_alpha,
                seed=42
            )
            
            # Compute intent embeddings (average of all pattern embeddings)
            for tag, intent_sents in intent_sentences_map.items():
                embeddings = []
                for sent in intent_sents:
                    sent_embedding = self._get_sentence_embedding(sent)
                    if sent_embedding is not None:
                        embeddings.append(sent_embedding)
                
                if embeddings:
                    # Average all pattern embeddings for this intent
                    avg_embedding = np.mean(embeddings, axis=0)
                    self.intent_embeddings_map[tag] = avg_embedding
            
            print(f" Word2Vec initialized:")
            print(f"   - Total sentences: {len(sentences)}")
            print(f"   - Vocabulary size: {len(self.word2vec_model.wv)}")
            print(f"   - Vector size: {vector_size}")
            print(f"   - Window: {window}")
            print(f"   - Algorithm: {'Skip-gram' if sg == 1 else 'CBOW'}")
            print(f"   - Intent embeddings: {len(self.intent_embeddings_map)}")
        else:
            print("⚠️  No sentences found to train Word2Vec")
    
    def _get_sentence_embedding(self, words: List[str]) -> Optional[np.ndarray]:
        """
        Tính sentence embedding bằng cách average word vectors
        
        Args:
            words: List of words in sentence
            
        Returns:
            Sentence embedding vector (numpy array) hoặc None nếu không có word nào trong vocabulary
        
        Formula:
        sentence_embedding = (1/n) × Σ(word_vector_i) for i in [1, n]
        
        Ví dụ:
        Words: ["tôi", "nên", "đăng", "ký"]
        
        Word vectors:
        - "tôi": [0.2, 0.5, -0.3]
        - "nên": [0.1, 0.3, 0.2]
        - "đăng": [0.4, -0.1, 0.1]
        - "ký": [0.3, 0.2, -0.2]
        
        Sentence embedding:
        - Average: [(0.2+0.1+0.4+0.3)/4, (0.5+0.3-0.1+0.2)/4, (-0.3+0.2+0.1-0.2)/4]
        - Result: [0.25, 0.225, -0.05]
        """
        if not self.word2vec_model or not words:
            return None
        
        word_vectors = []
        for word in words:
            if word in self.word2vec_model.wv:
                word_vectors.append(self.word2vec_model.wv[word])
        
        if not word_vectors:
            return None
        
        # Average of all word vectors
        sentence_embedding = np.mean(word_vectors, axis=0)
        return sentence_embedding
    
    def _semantic_similarity(self, message: str) -> List[Tuple[str, float]]:
        """
        Tính semantic similarity sử dụng Word2Vec embeddings
        
        Args:
            message: User message
            
        Returns:
            List of tuples (intent_tag, semantic_similarity_score) cho mỗi intent
        
        Quy trình:
        1. Normalize message
        2. Tokenize thành words
        3. Tính sentence embedding (average word vectors)
        4. Tính cosine similarity với intent embeddings
        5. Return sorted scores
        
        Cosine Similarity:
        similarity = (A · B) / (||A|| × ||B||)
        
        Ví dụ:
        Message: "tôi muốn học môn gì"
        Message embedding: [0.25, 0.30, -0.10, ...]
        
        Intent "subject_registration_suggestion":
        Intent embedding: [0.28, 0.32, -0.12, ...]
        
        Cosine similarity: 0.95 (rất cao - nghĩa tương đồng)
        
        Intent "greeting":
        Intent embedding: [-0.50, 0.10, 0.80, ...]
        
        Cosine similarity: 0.15 (thấp - nghĩa khác nhau)
        """
        if not self.word2vec_model or not self.intent_embeddings_map:
            return []
        
        # Get message embedding
        normalized_message = self._normalize_vietnamese(message)
        words = normalized_message.split()
        message_embedding = self._get_sentence_embedding(words)
        
        if message_embedding is None:
            return []
        
        # Calculate cosine similarity with each intent embedding
        similarities = []
        for intent_tag, intent_embedding in self.intent_embeddings_map.items():
            # Reshape for sklearn cosine_similarity
            msg_vec = message_embedding.reshape(1, -1)
            intent_vec = intent_embedding.reshape(1, -1)
            
            similarity = cosine_similarity(msg_vec, intent_vec)[0][0]
            similarities.append((intent_tag, float(similarity)))
        
        # Sort by similarity score
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities
    
    def _calculate_tfidf_similarity(self, message: str) -> List[Tuple[str, float]]:
        """
        Tính TF-IDF cosine similarity giữa message và tất cả patterns
        
        Args:
            message: User message
            
        Returns:
            List of tuples (intent_tag, similarity_score) cho mỗi intent
        
        Quy trình:
        1. Normalize message
        2. Transform message thành TF-IDF vector
        3. Tính cosine similarity với tất cả pattern vectors
        4. Aggregate scores theo intent (lấy max score cho mỗi intent)
        
        Cosine Similarity Formula:
        similarity = (A · B) / (||A|| × ||B||)
        
        Ví dụ:
        Message: "tôi nên học môn gì"
        Pattern: "tôi nên đăng ký môn gì" 
        Cosine similarity: 0.85 (cao vì nhiều từ giống nhau)
        """
        normalized_message = self._normalize_vietnamese(message)
        
        # Transform message to TF-IDF vector
        message_tfidf = self.tfidf_vectorizer.transform([normalized_message])
        
        # Calculate cosine similarity with all patterns
        similarities = cosine_similarity(message_tfidf, self.intent_tfidf_matrix)[0]
        
        # Aggregate by intent (take maximum similarity for each intent)
        intent_scores = {}
        for idx, (label, score) in enumerate(zip(self.intent_labels, similarities)):
            if label not in intent_scores or score > intent_scores[label]:
                intent_scores[label] = float(score)
        
        # Sort by score
        sorted_scores = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_scores
    
    def _calculate_keyword_score(self, message: str, intent_tag: str) -> float:
        """
        Tính keyword matching score
        
        Args:
            message: User message
            intent_tag: Intent tag
            
        Returns:
            Keyword matching score (0.0 to 1.0)
        
        Formula:
        keyword_score = (số từ khóa match / tổng số từ trong message)
        
        Ví dụ:
        Message: "tôi nên đăng ký môn gì" (5 words)
        Keywords: {"tôi", "nên", "đăng ký", "môn", "học phần", "gì"}
        Match: {"tôi", "nên", "đăng ký", "môn", "gì"} (5 matches)
        Score: 5/5 = 1.0
        """
        normalized_message = self._normalize_vietnamese(message)
        message_words = set(normalized_message.split())
        
        if not message_words:
            return 0.0
        
        intent_keywords = self.intent_keywords_map.get(intent_tag, set())
        
        if not intent_keywords:
            return 0.0
        
        # Calculate overlap
        matches = message_words & intent_keywords
        keyword_score = len(matches) / len(message_words)
        
        return keyword_score
    
    def _calculate_pattern_score(self, message: str, intent_tag: str) -> float:
        """
        Tính pattern matching score (exact pattern overlap)
        
        Args:
            message: User message
            intent_tag: Intent tag
            
        Returns:
            Pattern matching score (0.0 to 1.0)
        
        Formula:
        pattern_score = max(overlap_ratio) for all patterns
        overlap_ratio = (số từ match / số từ trong pattern)
        
        Ví dụ:
        Message: "tôi nên học môn gì"
        Pattern: "tôi nên đăng ký môn gì"
        Overlap: {"tôi", "nên", "môn", "gì"} (4 words)
        Pattern length: 5 words
        Score: 4/5 = 0.8
        """
        normalized_message = self._normalize_vietnamese(message)
        message_words = set(normalized_message.split())
        
        patterns = self.intent_patterns_map.get(intent_tag, [])
        
        max_score = 0.0
        for pattern in patterns:
            pattern_words = set(pattern.split())
            if pattern_words:
                overlap = message_words & pattern_words
                overlap_ratio = len(overlap) / len(pattern_words)
                if overlap_ratio > max_score:
                    max_score = overlap_ratio
        
        return max_score
    
    async def classify_intent(self, message: str) -> Dict:
        """
        Phân loại intent của message sử dụng TF-IDF và Cosine Similarity
        
        Args:
            message: User message cần phân loại
            
        Returns:
            Dict chứa:
            - intent: Intent tag
            - confidence: "high", "medium", hoặc "low"
            - confidence_score: Điểm số (0.0 to 1.0)
            - method: "tfidf_cosine"
            - tfidf_score: TF-IDF similarity score
            - keyword_score: Keyword matching score
            - pattern_score: Pattern matching score
            - all_scores: Top 5 intent scores
        
        Scoring Formula (Phase 2):
        final_score = (tfidf_score × 0.5) + (semantic_score × 0.3) + (keyword_score × 0.2)
        
        Ví dụ phân tích:
        
        Input: "tôi nên đăng ký môn gì"
        
        Bước 1: Normalize
        → "tôi nên đăng ký môn gì"
        
        Bước 2: TF-IDF Transform
        → Vector: [0.0, 0.45, 0.0, 0.32, ..., 0.51]
        
        Bước 3: TF-IDF Cosine Similarity
        → subject_registration_suggestion: 0.87
        → class_registration_suggestion: 0.45
        → subject_info: 0.32
        
        Bước 4: Word2Vec Semantic Similarity
        → Message embedding: [0.25, 0.30, -0.10, ...]
        → subject_registration_suggestion embedding: [0.28, 0.32, -0.12, ...]
        → Semantic similarity: 0.92
        
        Bước 5: Keyword Matching
        → Match: {"tôi", "nên", "đăng ký", "môn", "gì"}
        → Score: 5/5 = 1.0
        
        Bước 6: Final Score
        → 0.87 × 0.5 + 0.92 × 0.3 + 1.0 × 0.2 = 0.911
        
        Output: {
            "intent": "subject_registration_suggestion",
            "confidence": "high",
            "confidence_score": 0.911,
            "method": "tfidf_word2vec_hybrid"
        }
        """
        if not message or not message.strip():
            return {
                "intent": "out_of_scope",
                "confidence": "low",
                "confidence_score": 0.0,
                "method": "tfidf_word2vec_hybrid",
                "message": "Empty message"
            }
        
        try:
            # Phase 3: Use adaptive weights based on message length
            weights = self._calculate_adaptive_weights(message)
            
            # Calculate TF-IDF similarities
            tfidf_scores = self._calculate_tfidf_similarity(message)
            
            # Calculate semantic similarities (Word2Vec)
            semantic_scores_list = self._semantic_similarity(message)
            semantic_scores = {tag: score for tag, score in semantic_scores_list}
            
            # Calculate combined scores for each intent
            combined_scores = []
            
            for intent_tag, tfidf_score in tfidf_scores:
                # Calculate keyword score
                keyword_score = self._calculate_keyword_score(message, intent_tag)
                
                # Get semantic score for this intent
                semantic_score = semantic_scores.get(intent_tag, 0.0)
                
                # Phase 3: Calculate exact match bonus
                exact_bonus = self._calculate_exact_match_bonus(message, intent_tag)
                
                # Combined weighted score (Phase 3: TF-IDF + Semantic + Keyword + Exact Match Bonus)
                combined_score = (
                    tfidf_score * weights["tfidf"] +
                    semantic_score * weights["semantic"] +
                    keyword_score * weights["keyword"] +
                    exact_bonus
                )
                
                combined_scores.append({
                    "intent": intent_tag,
                    "score": combined_score,
                    "tfidf": tfidf_score,
                    "semantic": semantic_score,
                    "keyword": keyword_score,
                    "exact_bonus": exact_bonus
                })
            
            # Sort by combined score
            combined_scores.sort(key=lambda x: x["score"], reverse=True)
            
            if combined_scores:
                best_result = combined_scores[0]
                
                # Phase 3: Apply confidence boost
                best_result = self._apply_confidence_boost(message, best_result)
                
                best_intent = best_result["intent"]
                best_score = best_result["score"]
                
                second_best_score = combined_scores[1]["score"] if len(combined_scores) > 1 else 0.0
                margin = best_score - second_best_score
                
                # Determine confidence level
                if best_score >= self.thresholds["high_confidence"] and margin > 0.1:
                    confidence = "high"
                elif best_score >= self.thresholds["medium_confidence"] and margin > 0.05:
                    confidence = "medium"
                elif best_score >= self.thresholds["low_confidence"]:
                    confidence = "low"
                else:
                    best_intent = "out_of_scope"
                    confidence = "low"
                
                return {
                    "intent": best_intent,
                    "confidence": confidence,
                    "confidence_score": float(best_score),
                    "method": "tfidf_word2vec_hybrid_phase3",
                    "tfidf_score": float(best_result["tfidf"]),
                    "semantic_score": float(best_result["semantic"]),
                    "keyword_score": float(best_result["keyword"]),
                    "exact_bonus": float(best_result.get("exact_bonus", 0.0)),
                    "boost_applied": float(best_result.get("boost_applied", 0.0)),
                    "boost_reasons": best_result.get("boost_reasons", []),
                    "original_score": float(best_result.get("original_score", best_score)),
                    "adaptive_weights": self._calculate_adaptive_weights(message),
                    "margin": float(margin),
                    "all_scores": combined_scores[:5]
                }
            
            return {
                "intent": "out_of_scope",
                "confidence": "low",
                "confidence_score": 0.0,
                "method": "tfidf_word2vec_hybrid",
                "all_scores": []
            }
                
        except Exception as e:
            print(f" Error during classification: {e}")
            import traceback
            traceback.print_exc()
            return {
                "intent": "out_of_scope",
                "confidence": "low",
                "confidence_score": 0.0,
                "method": "tfidf_word2vec_hybrid",
                "error": str(e)
            }
    
    def get_all_similarities(self, message: str) -> List[Tuple[str, float]]:
        """
        Get similarity scores với tất cả intents
        
        Args:
            message: User message
            
        Returns:
            List of tuples (intent_name, similarity_score) sorted by score
        """
        try:
            tfidf_scores = self._calculate_tfidf_similarity(message)
            return tfidf_scores
        except Exception as e:
            print(f" Error getting similarities: {e}")
            return []
    
    def get_config(self) -> Dict:
        """Get current configuration"""
        return self.config.copy()
    
    def get_stats(self) -> Dict:
        """
        Get classifier statistics
        
        Returns:
            Dict với thông tin về classifier
        """
        return {
            "total_intents": len(self.intents.get("intents", [])),
            "method": "tfidf_word2vec_hybrid_phase3",
            "phase": "3 - Fine-tuned with Adaptive Weights + Confidence Boost",
            "tfidf_vocabulary_size": len(self.tfidf_vectorizer.vocabulary_) if self.tfidf_vectorizer else 0,
            "word2vec_vocabulary_size": len(self.word2vec_model.wv) if self.word2vec_model else 0,
            "tfidf_matrix_shape": str(self.intent_tfidf_matrix.shape) if self.intent_tfidf_matrix is not None else "N/A",
            "word2vec_vector_size": self.word2vec_model.wv.vector_size if self.word2vec_model else 0,
            "intent_embeddings_count": len(self.intent_embeddings_map),
            "thresholds": self.thresholds,
            "tfidf_params": self.config.get("tfidf_params", {}),
            "word2vec_params": self.config.get("word2vec_params", {}),
            "scoring_weights": self.config.get("scoring_weights", {})
        }
    
    def get_intent_friendly_name(self, intent_tag: str) -> str:
        """
        Chuyển intent tag thành tên dễ hiểu cho người dùng
        
        Args:
            intent_tag: Tag của intent
            
        Returns:
            Tên dễ hiểu của intent
        """
        intent_names = {
            "greeting": "chào hỏi",
            "thanks": "cảm ơn",
            "goodbye": "tạm biệt",
            "registration_guide": "hướng dẫn đăng ký học phần",
            "subject_registration_suggestion": "gợi ý đăng ký học phần",
            "class_registration_suggestion": "gợi ý đăng ký lớp học",
            "class_list": "xem danh sách lớp",
            "class_info": "xem thông tin lớp học",
            "subject_info": "xem thông tin học phần",
            "registration_time": "hỏi thời gian đăng ký",
            "retake_priority": "hỏi về ưu tiên học lại",
            "grade_view": "xem điểm số",
            "student_info": "xem thông tin sinh viên",
            "schedule_view": "xem thời khóa biểu",
            "schedule_info": "xem lịch học tạm thời",
            "prerequisite_check": "kiểm tra môn tiên quyết",
            "course_info": "hỏi thông tin khóa học",
            "department_info": "hỏi thông tin khoa",
            "tuition_info": "hỏi về học phí",
            "scholarship_info": "hỏi về học bổng",
            "exam_schedule": "hỏi lịch thi",
            "credit_info": "hỏi về tín chỉ",
            "facilities_info": "hỏi về cơ sở vật chất",
            "out_of_scope": "hỏi câu hỏi khác",
            "unknown": "đặt câu hỏi"
        }
        
        return intent_names.get(intent_tag, "trao đổi")


# For testing
if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("\n" + "="*80)
        print("🧪 TESTING TF-IDF + WORD2VEC INTENT CLASSIFIER (Phase 3 - Fine-tuned)")
        print("="*80)
        
        classifier = TfidfIntentClassifier()
        
        test_messages = [
            "Xin chào!",
            "điểm",  # Test Phase 3: very short query
            "điểm của tôi",  # Test Phase 3: short query with keyword
            "xem điểm",  # Test Phase 3: short query
            "Tôi nên đăng ký môn gì?",
            "Tôi nên đăng ký học phần gì?",
            "Lớp nào phù hợp với tôi?",
            "Thông tin học phần",
            "Tôi muốn học môn nào tốt nhất?",  # Test semantic understanding
            "lịch học của tôi",  # Test Phase 3: exact match
            "Cảm ơn!"
        ]
        
        print("\n" + "="*80)
        print("📝 TEST MESSAGES")
        print("="*80)
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n[{i}] Message: \"{message}\"")
            result = await classifier.classify_intent(message)
            
            print(f"    ✅ Intent: {result['intent']}")
            print(f"    🎯 Confidence: {result['confidence']} ({result['confidence_score']:.4f})")
            print(f"    🔧 Method: {result['method']}")
            
            if 'tfidf_score' in result:
                print(f"    📊 TF-IDF: {result['tfidf_score']:.4f}")
                print(f"    🧠 Semantic (W2V): {result.get('semantic_score', 0.0):.4f}")
                print(f"    🔑 Keyword: {result['keyword_score']:.4f}")
                print(f"    ⭐ Exact Bonus: {result.get('exact_bonus', 0.0):.4f}")
                print(f"    🚀 Boost Applied: {result.get('boost_applied', 0.0):.4f}")
                if result.get('boost_reasons'):
                    print(f"       Reasons: {', '.join(result['boost_reasons'])}")
                print(f"    ⚖️  Weights: TF={result.get('adaptive_weights', {}).get('tfidf', 0.5):.1f} " +
                      f"S={result.get('adaptive_weights', {}).get('semantic', 0.3):.1f} " +
                      f"K={result.get('adaptive_weights', {}).get('keyword', 0.2):.1f}")
            
            if result.get('all_scores'):
                print(f"    📈 Top 3 scores:")
                for j, score_info in enumerate(result['all_scores'][:3], 1):
                    print(f"       {j}. {score_info['intent']}: {score_info['score']:.4f} " +
                          f"(TF:{score_info['tfidf']:.2f}, S:{score_info['semantic']:.2f}, K:{score_info['keyword']:.2f})")
        
        # Print stats
        print("\n" + "="*80)
        print("📊 CLASSIFIER STATISTICS")
        print("="*80)
        stats = classifier.get_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        print("\n" + "="*80)
    
    asyncio.run(test())
