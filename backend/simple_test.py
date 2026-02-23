import sys
sys.path.insert(0, 'c:\\Users\\Admin\\student-management\\backend')

from app.services.text_preprocessor import TextPreprocessor

p = TextPreprocessor()

tests = [
    'chuwong trinh',
    'dichj', 
    'ddaayf',
    'hown thua',
    'thangws thua',
    'xem diem',
    'day du'
]

for t in tests:
    result = p.preprocess(t)
    print(f"{t:30} -> {result}")
