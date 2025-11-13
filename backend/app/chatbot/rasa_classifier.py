"""
Rasa NLU Intent Classifier cho tiếng Việt
Sử dụng Rasa NLU framework để phân loại intent
"""
import json
import os
from typing import Dict, List, Tuple, Optional
import yaml
import numpy as np
from pathlib import Path


class RasaIntentClassifier:
    """
    Intent classifier sử dụng Rasa NLU framework
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize Rasa NLU classifier
        
        Args:
            config_path: Path to rasa config file (optional)
        """
        print("   Initializing Rasa NLU classifier...")
        
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
            "đăng ký": ["dang ky", "dk", "đk"],
            "môn học": ["mon hoc", "môn", "mon", "học phần", "hoc phan"],
            "lớp học": ["lop hoc", "lớp", "lop", "class"],
            "điểm": ["diem", "điểm số", "diem so", "grade", "score"],
            "lịch": ["lich", "thời khóa biểu", "thoi khoa bieu", "tkb", "schedule"],
            "xem": ["view", "check", "kiểm tra", "kiem tra"],
            "học": ["hoc", "study", "learn"],
            "nên": ["nen", "should", "phải", "phai"],
            "gì": ["gi", "what", "gì đây", "gi day"],
            "nào": ["nao", "which"],
            "như thế nào": ["nhu the nao", "ra sao", "thế nào", "the nao"],
            "hướng dẫn": ["huong dan", "guide", "chỉ dẫn", "chi dan"],
            "cảm ơn": ["cam on", "thank", "thanks", "cám ơn"],
            "chào": ["chao", "hello", "hi", "xin chào", "xin chao"],
        }
        
        # Load or initialize Rasa components
        self._initialize_rasa_components()
        
        # Thresholds cho confidence levels
        self.thresholds = self.config.get("thresholds", {
            "high_confidence": 0.60,
            "medium_confidence": 0.40,
            "low_confidence": 0.25
        })
        
        print(f"   Rasa classifier initialized with {len(self.intents.get('intents', []))} intents")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load Rasa configuration từ file JSON"""
        try:
            with open(config_path, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"   Config file not found at {config_path}, using default config")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default Rasa configuration"""
        return {
            "language": "vi",
            "pipeline": [
                {"name": "WhitespaceTokenizer"},
                {"name": "RegexFeaturizer"},
                {"name": "LexicalSyntacticFeaturizer"},
                {"name": "CountVectorsFeaturizer", "analyzer": "char_wb", "min_ngram": 1, "max_ngram": 4},
                {"name": "DIETClassifier", "epochs": 200}
            ],
            "thresholds": {
                "high_confidence": 0.70,
                "medium_confidence": 0.50,
                "low_confidence": 0.30
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
            print(f"   Intents file not found at {intents_path}")
            return {"intents": []}
    
    def _initialize_rasa_components(self):
        """Initialize Rasa NLU components"""
        try:
            from rasa.nlu.model import Interpreter
            from rasa.nlu.training_data import load_data
            from rasa.nlu import config as rasa_config
            from rasa.nlu.model import Trainer
            
            self.has_rasa = True
            
            # Convert intents to Rasa training format
            training_data = self._convert_to_rasa_format()
            
            # Save training data to temporary file
            training_data_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "data",
                "rasa_training_data.yml"
            )
            
            with open(training_data_path, "w", encoding="utf-8") as f:
                yaml.dump(training_data, f, allow_unicode=True)
            
            # Create config file for Rasa
            rasa_config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "data",
                "rasa_nlu_config.yml"
            )
            
            config_data = {
                "language": self.config.get("language", "vi"),
                "pipeline": self.config.get("pipeline", [])
            }
            
            with open(rasa_config_path, "w", encoding="utf-8") as f:
                yaml.dump(config_data, f, allow_unicode=True)
            
            # Train or load model
            model_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "models",
                "rasa"
            )
            
            # Check if model exists
            if os.path.exists(model_dir) and os.listdir(model_dir):
                print("📦 Loading existing Rasa model...")
                # Find the latest model
                models = [f for f in os.listdir(model_dir) if f.endswith('.tar.gz')]
                if models:
                    latest_model = os.path.join(model_dir, sorted(models)[-1])
                    self.interpreter = Interpreter.load(latest_model)
                    print("   Rasa model loaded successfully")
                else:
                    self._train_rasa_model(training_data_path, rasa_config_path, model_dir)
            else:
                self._train_rasa_model(training_data_path, rasa_config_path, model_dir)
                
        except ImportError:
            print("   Rasa not installed. Using fallback similarity-based classification.")
            self.has_rasa = False
            self._initialize_fallback()
    
    def _train_rasa_model(self, training_data_path: str, config_path: str, model_dir: str):
        """Train new Rasa model"""
        from rasa.nlu.training_data import load_data
        from rasa.nlu import config as rasa_config
        from rasa.nlu.model import Trainer
        
        print("🏋️ Training new Rasa model (this may take a while)...")
        
        # Ensure model directory exists
        os.makedirs(model_dir, exist_ok=True)
        
        training_data = load_data(training_data_path)
        trainer = Trainer(rasa_config.load(config_path))
        trainer.train(training_data)
        model_directory = trainer.persist(model_dir)
        
        from rasa.nlu.model import Interpreter
        self.interpreter = Interpreter.load(model_directory)
        
        print("   Rasa model trained successfully")
    
    def _convert_to_rasa_format(self) -> Dict:
        """Convert intents.json to Rasa NLU training format"""
        nlu_data = {
            "version": "3.1",
            "nlu": []
        }
        
        for intent in self.intents.get("intents", []):
            intent_data = {
                "intent": intent["tag"],
                "examples": "- " + "\n- ".join(intent["patterns"])
            }
            nlu_data["nlu"].append(intent_data)
        
        return nlu_data
    
    def _normalize_vietnamese(self, text: str) -> str:
        """Normalize Vietnamese text for better matching"""
        import re
        
        text = text.lower().strip()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove punctuation but keep Vietnamese characters
        text = re.sub(r'[^\w\sàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', '', text)
        
        # Apply synonyms - replace with canonical forms
        for canonical, variants in self.synonyms.items():
            for variant in variants:
                # Use word boundary to avoid partial replacements
                text = re.sub(r'\b' + re.escape(variant) + r'\b', canonical, text)
        
        return text.strip()
    
    def _extract_features(self, text: str) -> Dict[str, float]:
        """Extract multiple types of features from text"""
        from collections import Counter
        
        features = Counter()
        normalized = self._normalize_vietnamese(text)
        
        # 1. Word-level features (most important for Vietnamese)
        words = normalized.split()
        for word in words:
            if len(word) > 0:
                features[f"word_{word}"] += 1.0
        
        # 2. Character bigrams (helps with typos)
        for i in range(len(normalized) - 1):
            if normalized[i] != ' ' and normalized[i+1] != ' ':
                bigram = normalized[i:i+2]
                features[f"char2_{bigram}"] += 0.5
        
        # 3. Character trigrams (better context)
        for i in range(len(normalized) - 2):
            if ' ' not in normalized[i:i+3]:
                trigram = normalized[i:i+3]
                features[f"char3_{trigram}"] += 0.3
        
        # 4. Word bigrams (phrase matching)
        for i in range(len(words) - 1):
            bigram = f"{words[i]}_{words[i+1]}"
            features[f"word2_{bigram}"] += 2.0  # Higher weight for phrases
        
        return features
    
    def _calculate_cosine_similarity(self, features1: Dict[str, float], features2: Dict[str, float]) -> float:
        """Calculate cosine similarity between two feature vectors"""
        # Get all unique features
        all_features = set(features1.keys()) | set(features2.keys())
        
        if not all_features:
            return 0.0
        
        # Calculate dot product and magnitudes
        dot_product = 0.0
        mag1 = 0.0
        mag2 = 0.0
        
        for feature in all_features:
            val1 = features1.get(feature, 0.0)
            val2 = features2.get(feature, 0.0)
            
            dot_product += val1 * val2
            mag1 += val1 * val1
            mag2 += val2 * val2
        
        # Avoid division by zero
        if mag1 == 0.0 or mag2 == 0.0:
            return 0.0
        
        return dot_product / (np.sqrt(mag1) * np.sqrt(mag2))
    
    def _initialize_fallback(self):
        """Initialize enhanced fallback similarity-based classifier"""
        from collections import Counter
        
        print("   Initializing enhanced fallback classifier...")
        
        self.intent_vectors = {}
        self.intent_keywords = {}
        
        for intent in self.intents.get("intents", []):
            tag = intent["tag"]
            patterns = intent["patterns"]
            
            # Augment patterns with variations
            augmented_patterns = list(patterns)
            
            # Add synonym variations to patterns
            for pattern in patterns[:]:  # Iterate over copy
                # Create variations by replacing synonyms
                for canonical, variants in self.synonyms.items():
                    if canonical in pattern.lower():
                        for variant in variants[:2]:  # Add up to 2 variations per synonym
                            import re
                            variation = re.sub(
                                r'\b' + re.escape(canonical) + r'\b',
                                variant,
                                pattern.lower()
                            )
                            if variation not in [p.lower() for p in augmented_patterns]:
                                augmented_patterns.append(variation)
            
            # Extract features from all patterns (including augmented)
            all_features = Counter()
            
            for pattern in augmented_patterns:
                pattern_features = self._extract_features(pattern)
                # Combine features from all patterns
                for feature, weight in pattern_features.items():
                    all_features[feature] += weight
            
            # Normalize by number of patterns (TF-IDF like)
            num_patterns = len(augmented_patterns)
            for feature in all_features:
                all_features[feature] /= np.sqrt(num_patterns)  # Use sqrt for better scaling
            
            self.intent_vectors[tag] = dict(all_features)
            
            # Extract keywords (words that appear in patterns)
            keywords = set()
            for pattern in augmented_patterns:
                words = self._normalize_vietnamese(pattern).split()
                keywords.update(words)
            self.intent_keywords[tag] = keywords
        
        print(f"   Enhanced fallback classifier initialized with augmented patterns")
    
    def _fallback_classify(self, message: str) -> Dict:
        """Enhanced fallback classification using multiple features and cosine similarity"""
        # Extract features from message
        message_features = self._extract_features(message)
        message_words = set(self._normalize_vietnamese(message).split())
        
        # Calculate similarity with each intent
        similarities = []
        
        for intent in self.intents.get("intents", []):
            tag = intent["tag"]
            intent_features = self.intent_vectors.get(tag, {})
            intent_keywords = self.intent_keywords.get(tag, set())
            
            # 1. Cosine similarity based on features
            cosine_sim = self._calculate_cosine_similarity(message_features, intent_features)
            
            # 2. Keyword overlap bonus (important for intent matching)
            if message_words and intent_keywords:
                keyword_overlap = len(message_words & intent_keywords) / len(message_words)
                keyword_boost = keyword_overlap * 0.3  # 30% boost for keyword matches
            else:
                keyword_boost = 0.0
            
            # 3. Pattern matching bonus - check if any pattern words are in message
            pattern_match_score = 0.0
            for pattern in intent["patterns"]:
                pattern_words = set(self._normalize_vietnamese(pattern).split())
                if pattern_words:
                    overlap_ratio = len(message_words & pattern_words) / len(pattern_words)
                    if overlap_ratio > pattern_match_score:
                        pattern_match_score = overlap_ratio
            
            pattern_boost = pattern_match_score * 0.2  # 20% boost for pattern matches
            
            # Combined score with weighted components
            combined_score = (
                cosine_sim * 0.5 +           # 50% weight on feature similarity
                keyword_boost +               # 30% max from keyword overlap
                pattern_boost                 # 20% max from pattern matching
            )
            
            similarities.append((tag, combined_score))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        if similarities:
            best_intent, best_score = similarities[0]
            second_best_score = similarities[1][1] if len(similarities) > 1 else 0.0
            
            # Check confidence with margin (difference between top 2 scores)
            margin = best_score - second_best_score
            
            # Adjust thresholds based on score and margin
            adjusted_high_threshold = self.thresholds["high_confidence"] * 0.7  # Lower threshold for fallback
            adjusted_medium_threshold = self.thresholds["medium_confidence"] * 0.6
            adjusted_low_threshold = self.thresholds["low_confidence"] * 0.5
            
            # Determine confidence level with margin consideration
            if best_score >= adjusted_high_threshold and margin > 0.1:
                confidence = "high"
            elif best_score >= adjusted_medium_threshold and margin > 0.05:
                confidence = "medium"
            elif best_score >= adjusted_low_threshold:
                confidence = "low"
            else:
                best_intent = "out_of_scope"
                confidence = "low"
            
            return {
                "intent": best_intent,
                "confidence": confidence,
                "confidence_score": float(best_score),
                "method": "enhanced_fallback",
                "margin": float(margin),
                "all_scores": [{"intent": tag, "score": float(score)} for tag, score in similarities[:5]]
            }
        
        return {
            "intent": "out_of_scope",
            "confidence": "low",
            "confidence_score": 0.0,
            "method": "enhanced_fallback",
            "margin": 0.0,
            "all_scores": []
        }
    
    async def classify_intent(self, message: str) -> Dict:
        """
        Classify intent của message sử dụng Rasa NLU
        
        Args:
            message: User message cần phân loại
            
        Returns:
            Dict chứa intent, confidence, và các thông tin khác
        """
        if not message or not message.strip():
            return {
                "intent": "out_of_scope",
                "confidence": "low",
                "confidence_score": 0.0,
                "method": "rasa_nlu",
                "message": "Empty message"
            }
        
        try:
            if self.has_rasa:
                # Use Rasa NLU interpreter
                result = self.interpreter.parse(message)
                
                intent_data = result.get("intent", {})
                intent_name = intent_data.get("name", "out_of_scope")
                confidence_score = intent_data.get("confidence", 0.0)
                
                # Determine confidence level based on thresholds
                if confidence_score >= self.thresholds["high_confidence"]:
                    confidence = "high"
                elif confidence_score >= self.thresholds["medium_confidence"]:
                    confidence = "medium"
                elif confidence_score >= self.thresholds["low_confidence"]:
                    confidence = "low"
                else:
                    intent_name = "out_of_scope"
                    confidence = "low"
                
                # Get all intent rankings
                all_scores = []
                for intent_rank in result.get("intent_ranking", [])[:5]:
                    all_scores.append({
                        "intent": intent_rank.get("name"),
                        "score": float(intent_rank.get("confidence", 0.0))
                    })
                
                return {
                    "intent": intent_name,
                    "confidence": confidence,
                    "confidence_score": float(confidence_score),
                    "method": "rasa_nlu",
                    "all_scores": all_scores
                }
            else:
                # Use fallback classifier
                return self._fallback_classify(message)
                
        except Exception as e:
            print(f"  Error during classification: {e}")
            # Fallback to simple classification
            return self._fallback_classify(message)
    
    def get_all_similarities(self, message: str) -> List[Tuple[str, float]]:
        """
        Get similarity scores với tất cả intents
        
        Args:
            message: User message
            
        Returns:
            List of tuples (intent_name, similarity_score) sorted by score
        """
        try:
            if self.has_rasa:
                result = self.interpreter.parse(message)
                intent_ranking = result.get("intent_ranking", [])
                
                return [(
                    intent_rank.get("name"),
                    float(intent_rank.get("confidence", 0.0))
                ) for intent_rank in intent_ranking]
            else:
                result = self._fallback_classify(message)
                return [(score["intent"], score["score"]) for score in result.get("all_scores", [])]
                
        except Exception as e:
            print(f"  Error getting similarities: {e}")
            return []
    
    def train(self, force_retrain: bool = False):
        """
        Train or retrain the Rasa model
        
        Args:
            force_retrain: If True, force retraining even if model exists
        """
        if not self.has_rasa:
            print("   Rasa not installed. Cannot train model.")
            return
        
        print("🏋️ Training Rasa model...")
        
        training_data_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "rasa_training_data.yml"
        )
        
        rasa_config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "rasa_nlu_config.yml"
        )
        
        model_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "models",
            "rasa"
        )
        
        self._train_rasa_model(training_data_path, rasa_config_path, model_dir)
    
    def get_config(self) -> Dict:
        """Get current configuration"""
        return self.config.copy()
    
    def get_stats(self) -> Dict:
        """Get classifier statistics"""
        return {
            "total_intents": len(self.intents.get("intents", [])),
            "has_rasa": self.has_rasa,
            "method": "rasa_nlu" if self.has_rasa else "fallback_ngram",
            "thresholds": self.thresholds,
            "config": self.config
        }
    
    def get_intent_friendly_name(self, intent_tag: str) -> str:
        """
        Chuyển intent tag thành tên dễ hiểu cho người dùng
        
        Args:
            intent_tag: Tag của intent
            
        Returns:
            Tên dễ hiểu của intent
        """
        # Mapping intent tags to friendly Vietnamese names
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
        classifier = RasaIntentClassifier()
        
        test_messages = [
            "Xin chào!",
            "Tôi nên đăng ký môn gì?",
            "Lớp nào phù hợp với tôi?",
            "Xem điểm",
            "Cảm ơn!"
        ]
        
        print("\n" + "="*70)
        print("   TESTING RASA CLASSIFIER")
        print("="*70)
        
        for message in test_messages:
            result = await classifier.classify_intent(message)
            print(f"\n   Message: \"{message}\"")
            print(f"   Intent: {result['intent']}")
            print(f"   Confidence: {result['confidence']} ({result['confidence_score']:.4f})")
            print(f"🔧 Method: {result['method']}")
        
        # Print stats
        print("\n" + "="*70)
        print("   CLASSIFIER STATS")
        print("="*70)
        stats = classifier.get_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")
    
    asyncio.run(test())
