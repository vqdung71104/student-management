import re

# Test simple pattern first
simple = r'các lớp\s+(.+)$'
pattern = r'(?:các lớp|cho tôi các lớp|thông tin các lớp)\s+([A-ZĐĂÂÊÔƠƯ][a-zđăâêôơưA-ZĐĂÂÊÔƠƯ\s\d\-]+)$'

test_cases = [
    "các lớp Giải tích II",
    "cho tôi các lớp Giải tích III",
    "các lớp Đại số tuyến tính",
    "các lớp Triết học Mác - Lênin",
]

print("Testing SIMPLE pattern:", simple)
for test in test_cases:
    match = re.search(simple, test, re.IGNORECASE)
    print(f"  '{test}' -> {match.group(1) if match else 'NO MATCH'}")

print("\n" + "="*60)
print("Testing COMPLEX pattern:", pattern)
for test in test_cases:
    match = re.search(pattern, test, re.IGNORECASE)
    print(f"  '{test}' -> {match.group(1) if match else 'NO MATCH'}")
