"""
Test script để kiểm tra chatbot intent classification
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from app.chatbot.intent_classifier import IntentClassifier

# Load environment variables
load_dotenv()


async def test_chatbot():
    """Test các câu hỏi mẫu với chatbot"""
    
    print("   Testing Chatbot Intent Classification with Google Gemini\n")
    print("=" * 70)
    
    # Initialize classifier
    try:
        classifier = IntentClassifier()
        print("   Intent Classifier initialized successfully!")
        print(f"   Loaded {len(classifier.intents.get('intents', []))} intents\n")
    except Exception as e:
        print(f"  Error initializing classifier: {e}")
        return
    
    # Test messages
    test_messages = [
        "xin chào",
        "Trời đẹp quá",  # Unknown intent
    ]
    
    print("   Testing messages:\n")
    
    for i, message in enumerate(test_messages, 1):
        print(f"{i}. User: \"{message}\"")
        
        try:
            result = await classifier.classify_intent(message)
            
            intent = result["intent"]
            confidence = result["confidence"]
            
            # Format response như trong chatbot_routes.py
            if confidence == "high" and intent != "unknown":
                if intent == "greeting":
                    response = "Xin chào! Mình là trợ lý ảo của hệ thống quản lý sinh viên."
                elif intent == "thanks":
                    response = "Rất vui được giúp đỡ bạn!"
                else:
                    friendly_name = classifier.get_intent_friendly_name(intent)
                    response = f"Bạn định {friendly_name} phải không?"
            else:
                response = "Mình chưa hiểu rõ câu hỏi của bạn, bạn vui lòng diễn giải lại được không?"
            
            print(f"   Bot: \"{response}\"")
            print(f"   [Intent: {intent}, Confidence: {confidence}]")
            
        except Exception as e:
            print(f"     Error: {e}")
        
        print()
    
    print("=" * 70)
    print("   Test completed!")


if __name__ == "__main__":
    # Check if API key exists
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your_google_api_key_here":
        print("  ERROR: GOOGLE_API_KEY chưa được cấu hình trong .env file")
        print("   Vui lòng:")
        print("   1. Truy cập: https://aistudio.google.com/app/api-keys")
        print("   2. Tạo API key")
        print("   3. Thêm vào backend/.env: GOOGLE_API_KEY=your_key_here")
        sys.exit(1)
    
    asyncio.run(test_chatbot())
