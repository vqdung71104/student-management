"""
Hybrid Intent Classifier - Kết hợp PhoBERT và Gemini AI
Sử dụng PhoBERT làm primary, Gemini làm fallback
"""
import asyncio
from typing import Dict
from app.chatbot.phobert_classifier import PhoBERTIntentClassifier
from app.chatbot.intent_classifier import IntentClassifier


class HybridIntentClassifier:
    """
    Hybrid classifier kết hợp PhoBERT (semantic similarity) 
    và Gemini AI (generative AI) để tối ưu độ chính xác
    """
    
    def __init__(self, use_phobert: bool = True, use_gemini: bool = True):
        """
        Initialize hybrid classifier
        
        Args:
            use_phobert: Có sử dụng PhoBERT không (default: True)
            use_gemini: Có sử dụng Gemini không (default: True)
        """
        self.use_phobert = use_phobert
        self.use_gemini = use_gemini
        
        # Initialize classifiers
        self.phobert_classifier = None
        self.gemini_classifier = None
        
        if self.use_phobert:
            try:
                print("   Initializing PhoBERT classifier...")
                self.phobert_classifier = PhoBERTIntentClassifier()
                print("   PhoBERT classifier ready")
            except Exception as e:
                print(f"   PhoBERT initialization failed: {e}")
                self.use_phobert = False
        
        if self.use_gemini:
            try:
                print("   Initializing Gemini classifier...")
                self.gemini_classifier = IntentClassifier()
                print("   Gemini classifier ready")
            except Exception as e:
                print(f"   Gemini initialization failed: {e}")
                self.use_gemini = False
        
        # Strategy configuration
        self.strategy = self._determine_strategy()
        print(f"   Using strategy: {self.strategy}")
    
    def _determine_strategy(self) -> str:
        """Xác định strategy dựa trên classifiers available"""
        if self.use_phobert and self.use_gemini:
            return "hybrid"  # PhoBERT primary, Gemini fallback
        elif self.use_phobert:
            return "phobert_only"
        elif self.use_gemini:
            return "gemini_only"
        else:
            return "none"
    
    async def classify_intent(self, user_message: str) -> Dict[str, any]:
        """
        Phân loại intent với hybrid approach
        
        Strategy:
        1. Thử PhoBERT trước (nhanh, semantic)
        2. Nếu confidence thấp, dùng Gemini (chậm nhưng chính xác hơn)
        3. Ensemble voting nếu cả 2 đều available
        
        Args:
            user_message: Tin nhắn từ user
            
        Returns:
            Dict với keys: intent, description, confidence, method
        """
        
        if self.strategy == "none":
            return {
                "intent": "unknown",
                "description": "Không có classifier nào available",
                "confidence": "low",
                "method": "none"
            }
        
        elif self.strategy == "phobert_only":
            return await self.phobert_classifier.classify_intent(user_message)
        
        elif self.strategy == "gemini_only":
            return await self.gemini_classifier.classify_intent(user_message)
        
        elif self.strategy == "hybrid":
            return await self._hybrid_classification(user_message)
    
    async def _hybrid_classification(self, user_message: str) -> Dict[str, any]:
        """
        Hybrid classification strategy:
        1. PhoBERT first (fast)
        2. If low confidence -> Gemini fallback
        3. Ensemble voting if needed
        """
        
        # Step 1: Try PhoBERT first (nhanh)
        phobert_result = await self.phobert_classifier.classify_intent(user_message)
        
        # Nếu PhoBERT có high confidence, dùng luôn
        if phobert_result["confidence"] == "high":
            return phobert_result
        
        # Step 2: PhoBERT có medium confidence -> Kiểm tra với Gemini
        if phobert_result["confidence"] == "medium":
            # Run both in parallel
            gemini_result = await self.gemini_classifier.classify_intent(user_message)
            
            # Nếu cả 2 đồng ý về intent
            if phobert_result["intent"] == gemini_result["intent"]:
                return {
                    **phobert_result,
                    "confidence": "high",  # Upgrade to high
                    "method": "hybrid_consensus"
                }
            
            # Nếu Gemini có high confidence, tin Gemini
            if gemini_result["confidence"] == "high":
                return {
                    **gemini_result,
                    "method": "gemini_override"
                }
            
            # Còn lại, tin PhoBERT (vì semantic similarity thường đáng tin)
            return {
                **phobert_result,
                "method": "phobert_medium"
            }
        
        # Step 3: PhoBERT có low confidence -> Dùng Gemini
        gemini_result = await self.gemini_classifier.classify_intent(user_message)
        
        # Nếu Gemini cũng low confidence -> unknown
        if gemini_result["confidence"] == "low":
            return {
                "intent": "unknown",
                "description": "Không thể xác định ý định",
                "confidence": "low",
                "method": "hybrid_both_low"
            }
        
        # Tin Gemini
        return {
            **gemini_result,
            "method": "gemini_fallback"
        }
    
    async def classify_with_details(self, user_message: str) -> Dict[str, any]:
        """
        Phân loại với thông tin chi tiết từ cả 2 classifiers (để debugging)
        """
        results = {}
        
        if self.use_phobert:
            results["phobert"] = await self.phobert_classifier.classify_intent(user_message)
        
        if self.use_gemini:
            results["gemini"] = await self.gemini_classifier.classify_intent(user_message)
        
        # Final result từ hybrid strategy
        results["final"] = await self.classify_intent(user_message)
        
        return results
    
    def get_intent_friendly_name(self, intent_tag: str) -> str:
        """
        Chuyển intent tag thành tên dễ hiểu cho người dùng
        """
        if self.phobert_classifier:
            return self.phobert_classifier.get_intent_friendly_name(intent_tag)
        elif self.gemini_classifier:
            return self.gemini_classifier.get_intent_friendly_name(intent_tag)
        else:
            return intent_tag
