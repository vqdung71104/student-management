from app.services.text_preprocessor import TextPreprocessor

p = TextPreprocessor()

test_cases = [
    # Original tests
    "xin chai",
    "gogle",
    "t2 và t4",
    "thws 4",
    "báo cái",
    
    # New spelling error tests
    "chuwong trinh",
    "dichj",
    "ddaayf đủ",
    "đầy đỷ",
    "hown thua",
    "hon thua",
    "thangws thua",
    "xem diem",
    "kiem tra",
    "goi y lop hoc",
    "dang ky mon hoc",
    "thong tin sinh vien",
    "huong dan dang nhap",
    
    # Complex cases
    "toi muon xem diem mon IT3170",
    "goi y lop hoc t2 va t4",
    "chuwong trinh hoc tap day du",
]

print("\n" + "="*80)
print("TESTING TEXT PREPROCESSING WITH SPELL CORRECTION")
print("="*80 + "\n")

for test in test_cases:
    result = p.preprocess(test, verbose=False)
    status = "[OK]" if result != test else "[NO CHANGE]"
    print(f"{status:12} {test:40} → {result}")

print("\n" + "="*80)
