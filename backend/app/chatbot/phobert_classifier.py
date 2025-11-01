"""
PhoBERT-based Intent Classifier cho tiếng Việt
Sử dụng Sentence Transformers với model Vietnamese SBERT
"""
import json
import os
from typing import Dict, List, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class PhoBERTIntentClassifier:
    """
    Intent classifier sử dụng PhoBERT embeddings với semantic similarity
    """
    
    def __init__(self):
        """Initialize PhoBERT model và load intents"""
        print("🔄 Loading PhoBERT model...")
        
        # Sử dụng Vietnamese SBERT model
        try:
            self.model = SentenceTransformer('keepitreal/vietnamese-sbert')
            print("✅ Loaded Vietnamese SBERT model")
        except Exception as e:
            print(f"⚠️ Failed to load Vietnamese SBERT, using multilingual model: {e}")
            # Fallback to multilingual model
            self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
        self.intents = self._load_intents()
        self.intent_embeddings = {}
        self._precompute_intent_embeddings()
        
        # Thresholds cho confidence levels
        self.thresholds = {
            "high": 0.65,      # Similarity > 0.65 = high confidence
            "medium": 0.45,    # Similarity > 0.45 = medium confidence
            "low": 0.0         # Còn lại = low confidence
        }
        
        print(f"✅ PhoBERT classifier initialized with {len(self.intents.get('intents', []))} intents")
    
    def _load_intents(self) -> Dict:
        """Load intents từ file JSON"""
        intents_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "intents.json"
        )
        
        try:
            with open(intents_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Không tìm thấy file intents.json tại {intents_path}")
            return {"intents": []}
    
    def _precompute_intent_embeddings(self):
        """
        Tính trước embeddings cho tất cả patterns trong mỗi intent
        Sử dụng average embedding cho mỗi intent
        """
        print("🔄 Precomputing intent embeddings...")
        
        for intent in self.intents.get("intents", []):
            tag = intent["tag"]
            patterns = intent["patterns"]
            
            if not patterns:
                continue
            
            # Encode tất cả patterns
            patterns_embeddings = self.model.encode(
                patterns,
                convert_to_tensor=False,
                show_progress_bar=False
            )
            
            # Tính average embedding cho intent này
            avg_embedding = np.mean(patterns_embeddings, axis=0)
            
            self.intent_embeddings[tag] = {
                "embedding": avg_embedding,
                "patterns": patterns,
                "description": intent.get("description", "")
            }
        
        print(f"✅ Precomputed embeddings for {len(self.intent_embeddings)} intents")
    
    async def classify_intent(self, user_message: str) -> Dict[str, any]:
        """
        Phân loại intent của user message bằng semantic similarity
        
        Args:
            user_message: Tin nhắn từ user
            
        Returns:
            Dict với keys: intent, description, confidence, similarity_score
        """
        try:
            # Encode user message
            user_embedding = self.model.encode(
                [user_message],
                convert_to_tensor=False,
                show_progress_bar=False
            )[0]
            
            # Tính similarity với tất cả intents
            similarities = {}
            for intent_tag, intent_data in self.intent_embeddings.items():
                similarity = cosine_similarity(
                    [user_embedding],
                    [intent_data["embedding"]]
                )[0][0]
                
                similarities[intent_tag] = {
                    "score": float(similarity),
                    "description": intent_data["description"]
                }
            
            # Tìm intent có similarity cao nhất
            best_intent = max(similarities.items(), key=lambda x: x[1]["score"])
            best_intent_tag = best_intent[0]
            best_score = best_intent[1]["score"]
            
            # Xác định confidence level
            if best_score >= self.thresholds["high"]:
                confidence = "high"
            elif best_score >= self.thresholds["medium"]:
                confidence = "medium"
            else:
                confidence = "low"
                best_intent_tag = "unknown"
            
            return {
                "intent": best_intent_tag,
                "description": similarities[best_intent_tag]["description"] if best_intent_tag != "unknown" else "Ý định không xác định",
                "confidence": confidence,
                "similarity_score": best_score,
                "method": "phobert"
            }
            
        except Exception as e:
            print(f"❌ Lỗi khi phân loại intent với PhoBERT: {str(e)}")
            return {
                "intent": "unknown",
                "description": "Không thể xác định ý định",
                "confidence": "low",
                "similarity_score": 0.0,
                "method": "phobert",
                "error": str(e)
            }
    
    def get_all_similarities(self, user_message: str) -> List[Tuple[str, float]]:
        """
        Lấy similarity scores cho tất cả intents (để debugging)
        
        Returns:
            List of (intent_tag, similarity_score) sorted by score descending
        """
        user_embedding = self.model.encode(
            [user_message],
            convert_to_tensor=False,
            show_progress_bar=False
        )[0]
        
        similarities = []
        for intent_tag, intent_data in self.intent_embeddings.items():
            similarity = cosine_similarity(
                [user_embedding],
                [intent_data["embedding"]]
            )[0][0]
            
            similarities.append((intent_tag, float(similarity)))
        
        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities
    
    def get_intent_friendly_name(self, intent_tag: str) -> str:
        """
        Chuyển intent tag thành tên dễ hiểu cho người dùng
        """
        intent_names = {
            "registration_guide": "hướng dẫn đăng ký học phần",
            "subject_registration_suggestion": "gợi ý đăng ký học phần",
            "class_registration_suggestion": "gợi ý đăng ký lớp học",
            "view_grades": "xem kết quả học tập",
            "scholarship_info": "tìm hiểu thông tin học bổng",
            "schedule_inquiry": "tra cứu lịch học",
            "course_info": "hỏi thông tin môn học",
            "subject_info": "hỏi thông tin học phần",
            "greeting": "chào hỏi",
            "thanks": "cảm ơn",
            "unknown": "đặt câu hỏi"
        }
        
        return intent_names.get(intent_tag, "trao đổi")
