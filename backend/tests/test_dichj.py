"""
Quick test to verify text preprocessing works correctly
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.text_preprocessor import TextPreprocessor

# Create new instance to ensure fresh load
preprocessor = TextPreprocessor()

# Test cases
test_input = "xem điểm môn Xây dựng chương trình dichj"
result = preprocessor.preprocess(test_input, verbose=True)

print("\n" + "="*80)
print("FINAL RESULT:")
print("="*80)
print(f"Input:  {test_input}")
print(f"Output: {result}")
print("="*80)

# Check if 'dichj' was corrected
if 'dichj' in result:
    print("\n❌ ERROR: 'dichj' was NOT corrected!")
elif 'dịch' in result:
    print("\n✅ SUCCESS: 'dichj' was corrected to 'dịch'")
else:
    print("\n⚠️  WARNING: Neither 'dichj' nor 'dịch' found in result")
