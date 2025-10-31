"""
Script để list tất cả các model có sẵn trong Google AI
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("❌ GOOGLE_API_KEY không được cấu hình")
    exit(1)

genai.configure(api_key=api_key)

print("📋 Danh sách các models có sẵn:\n")

for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"✅ {model.name}")
        print(f"   Display Name: {model.display_name}")
        print(f"   Description: {model.description}")
        print(f"   Methods: {', '.join(model.supported_generation_methods)}")
        print()
