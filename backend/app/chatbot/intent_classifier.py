"""
Intent Classifier sử dụng Google Gemini AI để phân loại ý định người dùng
"""
import json
import os
from typing import Dict, Optional
import google.generativeai as genai


class IntentClassifier:
    """
    Phân loại intent của user message sử dụng Google Gemini API
    """
    
    def __init__(self):
        """Initialize Google Gemini client với API key từ environment variable"""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY không được cấu hình trong .env")
        
        genai.configure(api_key=api_key)
        # Sử dụng model name đầy đủ với API version
        self.model = genai.GenerativeModel('models/gemini-2.5-flash-lite-preview-09-2025')
        self.intents = self._load_intents()
    
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
            print(f"Không tìm thấy file intents.json tại {intents_path}")
            return {"intents": []}
    
    def _build_intent_prompt(self, user_message: str) -> str:
        """Xây dựng prompt cho GPT để phân loại intent"""
        
        # Tạo danh sách các intent và ví dụ
        intent_descriptions = []
        for intent in self.intents.get("intents", []):
            tag = intent["tag"]
            description = intent["description"]
            examples = ", ".join(intent["patterns"][:3])  # Lấy 3 ví dụ đầu
            intent_descriptions.append(
                f"- {tag}: {description}\n  Ví dụ: {examples}"
            )
        
        intents_text = "\n".join(intent_descriptions)
        
        prompt = f"""Bạn là trợ lý phân loại ý định (intent classification) cho hệ thống tư vấn học tập sinh viên.

Các intent có sẵn:
{intents_text}

Nhiệm vụ: Phân tích câu hỏi của sinh viên và xác định intent phù hợp nhất.

Câu hỏi của sinh viên: "{user_message}"

Hãy trả về ĐÚNG 1 trong các giá trị sau:
- Nếu câu hỏi rõ ràng thuộc 1 intent: trả về tên intent (ví dụ: "registration_guide")
- Nếu không hiểu hoặc không khớp intent nào: trả về "unknown"

Chỉ trả về TÊN INTENT, không giải thích."""

        return prompt
    
    async def classify_intent(self, user_message: str) -> Dict[str, str]:
        """
        Phân loại intent của user message
        
        Args:
            user_message: Tin nhắn từ user
            
        Returns:
            Dict với keys: intent, description, confidence
        """
        try:
            # Gọi Google Gemini API
            prompt = self._build_intent_prompt(user_message)
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Thấp để có kết quả ổn định
                    max_output_tokens=20,
                )
            )
            
            # Lấy intent từ response
            predicted_intent = response.text.strip().lower()
            
            # Tìm description của intent
            intent_info = self._get_intent_info(predicted_intent)
            
            return {
                "intent": predicted_intent,
                "description": intent_info["description"],
                "confidence": "high" if predicted_intent != "unknown" else "low"
            }
            
        except Exception as e:
            print(f"Lỗi khi phân loại intent: {str(e)}")
            return {
                "intent": "unknown",
                "description": "Không thể xác định ý định",
                "confidence": "low"
            }
    
    def _get_intent_info(self, intent_tag: str) -> Dict[str, str]:
        """Lấy thông tin chi tiết của intent"""
        for intent in self.intents.get("intents", []):
            if intent["tag"] == intent_tag:
                return {
                    "tag": intent["tag"],
                    "description": intent["description"]
                }
        
        return {
            "tag": "unknown",
            "description": "Ý định không xác định"
        }
    
    def get_intent_friendly_name(self, intent_tag: str) -> str:
        """
        Chuyển intent tag thành tên dễ hiểu cho người dùng
        """
        intent_names = {
            "registration_guide": "hướng dẫn đăng ký học phần",
            "view_grades": "xem kết quả học tập",
            "scholarship_info": "tìm hiểu thông tin học bổng",
            "schedule_inquiry": "tra cứu lịch học",
            "course_info": "hỏi thông tin môn học",
            "greeting": "chào hỏi",
            "thanks": "cảm ơn",
            "unknown": "đặt câu hỏi"
        }
        
        return intent_names.get(intent_tag, "trao đổi")
