# Chatbot Documentation

Tài liệu chi tiết về hệ thống chatbot của Student Management System.

##  Tài liệu có sẵn

### 1. Technical Documentation
**File**: [CHATBOT_TECHNICAL_DOCUMENTATION.md](./CHATBOT_TECHNICAL_DOCUMENTATION.md)

Tài liệu kỹ thuật tổng quan về chatbot:
- Kiến trúc hệ thống (6 bước xử lý)
- Các thành phần chính
- Luồng xử lý end-to-end
- 12 intents được hỗ trợ
- Cấu trúc dữ liệu training
- Performance metrics (125ms average, 95% accuracy)

**Phù hợp cho**: Developers, System Architects

---

### 2. Tools and Libraries Guide
**File**: [CHATBOT_TOOLS_GUIDE.md](./CHATBOT_TOOLS_GUIDE.md)

Hướng dẫn chi tiết về các công cụ và thư viện:
- **Rasa NLU**: Intent classification framework
- **scikit-learn**: TF-IDF và Cosine Similarity
- **Underthesea**: Vietnamese word tokenization
- **Transformers (ViT5)**: Optional NL2SQL model
- **Regular Expressions**: Entity extraction patterns
- **SQLAlchemy**: Database ORM

Mỗi công cụ có:
- Giới thiệu và purpose
- Cài đặt
- Parameters và options
- Code examples
- Use cases thực tế

**Phù hợp cho**: Developers muốn hiểu sâu về tools

---

### 3. Examples Analysis
**File**: [CHATBOT_EXAMPLES_ANALYSIS.md](./CHATBOT_EXAMPLES_ANALYSIS.md)

Phân tích từng bước chi tiết của 5 examples:

#### Example 1: Simple Class Query
```
"các lớp môn Giải tích"
→ Intent: class_info (0.923 confidence)
→ Entity: subject_name="Giải tích"
→ SQL: SELECT ... WHERE subject_name LIKE '%Giải tích%'
→ Result: 5 classes found
Time: 125ms
```

#### Example 2: Complex Subject Name
```
"lớp của học phần Lý thuyết điều khiển tự động"
→ Extract long compound name
→ Handle Vietnamese diacritics
→ Database LIKE matching
```

#### Example 3: Class Suggestion with Filtering
```
"kỳ này nên học lớp nào"
→ Filter by subject_registers
→ Exclude learned_subjects (except F/I)
→ Add student CPA to response
→ Result: Smart suggestions
Time: 180ms
```

#### Example 4: Schedule Query with Auth
```
"lịch học của tôi"
→ Requires student_id
→ JOIN class_registers
→ Return authenticated data
```

#### Example 5: Multi-Entity Query
```
"lớp 161084 môn IT4040 vào thứ 2"
→ Extract 3 entities
→ Multiple SQL filters
→ Precise results
```

**Phù hợp cho**: Developers muốn hiểu logic xử lý

---

### 4. Enhanced Class Suggestion
**File**: [ENHANCED_CLASS_SUGGESTION.md](./ENHANCED_CLASS_SUGGESTION.md)

Tài liệu về tính năng gợi ý lớp học thông minh:
- SQL filtering logic
- subject_registers integration
- learned_subjects exclusion
- CPA display
- Test results

**Phù hợp cho**: Developers làm việc với suggestion features

---

### 5. NL2SQL README
**File**: [NL2SQL_README.md](./NL2SQL_README.md)

Hướng dẫn về hệ thống NL2SQL:
- Rule-based approach (default)
- ViT5 model training (optional)
- Training data structure
- SQL template matching
- Entity replacement

**Phù hợp cho**: Developers làm việc với SQL generation

---

### 6. Preference Extraction ⭐ NEW
**File**: [PREFERENCE_EXTRACTION.md](./PREFERENCE_EXTRACTION.md)

Tài liệu về context-aware negation detection và active negative filtering:
- **Context-Aware Negation**: Kiểm tra phủ định trong cửa sổ 20 ký tự
- **Positive vs Negative Preferences**: `time_period` vs `avoid_time_periods`
- **Active Negative Filtering**: Loại bỏ tích cực thay vì bỏ qua
- **Filter Priority**: Negative filters applied FIRST
- **Bug Fixes**: Global negation check → Context-aware
- **Test Coverage**: 16/16 tests passing

Examples:
```
"không muốn học buổi sáng" → avoid_time_periods: ['morning']
"không muốn học thứ 5" → avoid_days: ['Thursday']
"không sáng, học thứ 5" → both extracted correctly
```

**Phù hợp cho**: Developers làm việc với preference extraction và class filtering

---

### 7. Chatbot Flow Documentation
**File**: [app/rules/docs/CHATBOT_FLOW.md](../app/rules/docs/CHATBOT_FLOW.md)

Tài liệu chi tiết về luồng xử lý chatbot:
- Intent classification flow
- Subject suggestion flow
- Class suggestion flow (với preferences)
- Preference extraction table
- Test cases (6+ scenarios)
- Recent updates log

**Phù hợp cho**: Developers cần hiểu end-to-end flow

---

##  Test Files

### Trong thư mục `app/tests/`

#### 1. Intent Classification Test
**File**: `test_intent_classification.py`

Tests:
- 40+ test cases cho các intent
- Accuracy measurement
- Confidence distribution
- Performance timing
- Edge cases (typos, mixed language, long text)

Run:
```bash
cd backend
python app/tests/test_intent_classification.py
```

Expected output:
```
✓ Accuracy: 95-100%
✓ High confidence: 85%+
✓ Average time: ~60ms
```

---

#### 2. NL2SQL Service Test
**File**: `test_nl2sql_service.py`

Tests:
- Entity extraction (15+ patterns)
- SQL generation accuracy
- SQL customization
- Template matching
- Performance (100 queries)

Run:
```bash
python app/tests/test_nl2sql_service.py
```

Expected output:
```
✓ Entity extraction: 90%+
✓ SQL generation: 70-80% (rule-based)
✓ Average time: ~10ms/query
```

---

#### 3. Integration Test
**File**: `test_chatbot_integration.py`

End-to-end tests:
- 9 complete scenarios
- Timing breakdown per step
- Concurrent requests test (50 concurrent)
- Error handling scenarios

Run:
```bash
python app/tests/test_chatbot_integration.py
```

Expected output:
```
✓ Pass rate: 85%+
✓ Average response: ~125ms
✓ Throughput: 40+ requests/second
```

---

## Performance Benchmarks

### Component Performance

| Component | Time | Accuracy |
|-----------|------|----------|
| Intent Classification | 60ms | 95-100% |
| Entity Extraction | 5ms | 90-95% |
| SQL Generation | 10ms | 70-80% (rule-based) |
| Database Query | 50ms | 100% |
| **Total** | **125ms** | **85-90%** |

### Intent Classification

| Method | Accuracy | Speed |
|--------|----------|-------|
| Rasa NLU | 85-90% | ~50ms |
| TF-IDF Fallback | 95-100% | ~10ms |
| Combined | 95-100% | ~60ms |

### SQL Generation

| Method | Accuracy | Speed |
|--------|----------|-------|
| Rule-based | 70-80% | ~5ms |
| ViT5 (optional) | >90% | ~200ms |

---

##  Quick Start

### 1. Đọc tài liệu tổng quan
```bash
# Hiểu kiến trúc và luồng xử lý
cat docs/CHATBOT_TECHNICAL_DOCUMENTATION.md
```

### 2. Học về tools
```bash
# Chi tiết về Rasa, TF-IDF, Underthesea, etc.
cat docs/CHATBOT_TOOLS_GUIDE.md
```

### 3. Xem examples
```bash
# Phân tích từng bước của 5 ví dụ
cat docs/CHATBOT_EXAMPLES_ANALYSIS.md
```

### 4. Chạy tests
```bash
cd backend

# Test intent classification
python app/tests/test_intent_classification.py

# Test NL2SQL
python app/tests/test_nl2sql_service.py

# Test end-to-end
python app/tests/test_chatbot_integration.py
```

---

##  Supported Intents

1. **greeting** - Chào hỏi
2. **thanks** - Cảm ơn
3. **grade_view** - Xem điểm tổng quan (CPA, tín chỉ)
4. **learned_subjects_view** - Xem điểm chi tiết từng môn
5. **student_info** - Thông tin sinh viên
6. **subject_info** - Thông tin học phần
7. **class_info** - Thông tin lớp học
8. **schedule_view** - Lịch học đã đăng ký
9. **subject_registration_suggestion** - Gợi ý môn đăng ký
10. **class_registration_suggestion** - Gợi ý lớp đăng ký ⭐ **With Smart Preferences**
    - Time preferences: "muốn học sáng", "không muốn học chiều"
    - Day preferences: "muốn học thứ 5", "không học thứ 7"
    - Context-aware negation detection
    - Active negative filtering

---

## Configuration Files

### Training Data
- `backend/data/intents.json` - Intent patterns (19+ patterns per intent)
- `backend/data/nl2sql_training_data.json` - SQL templates (27+ examples)
- `backend/data/rasa_config.json` - Rasa configuration
- `backend/data/rasa_nlu_config.yml` - Rasa pipeline config

### Models
- `backend/models/nlu/` - Trained Rasa models (auto-generated)
- `backend/models/vit5-nl2sql/` - Fine-tuned ViT5 (optional)

---

##  Debugging

### Enable Debug Logging

```python
# In chatbot_routes.py
print(f" DEBUG: student_id = {student_id}")
print(f" DEBUG: intent = {intent}, confidence = {confidence}")
print(f" DEBUG: entities = {entities}")
print(f" DEBUG: SQL = {sql}")
```

### Check Logs

```bash
# Uvicorn logs
tail -f logs/uvicorn.log

# Search for errors
grep "ERROR" logs/uvicorn.log
```

### Test Specific Query

```python
from app.chatbot.rasa_classifier import RasaIntentClassifier
import asyncio

classifier = RasaIntentClassifier()
result = asyncio.run(classifier.classify_intent("các lớp môn Giải tích"))
print(result)
```

---

##  Further Reading

### External Resources

1. **Rasa Documentation**: https://rasa.com/docs/rasa/
2. **scikit-learn TF-IDF**: https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction
3. **Underthesea**: https://github.com/undertheseanlp/underthesea
4. **ViT5 Model**: https://huggingface.co/VietAI/vit5-base
5. **SQLAlchemy ORM**: https://docs.sqlalchemy.org/

### Internal Documentation

- `backend/README.md` - Backend setup
- `backend/scripts/README.md` - Utility scripts
- `backend/models/README.md` - Model management

---

##  Recent Updates

### December 8, 2025
- ✅ **Context-Aware Negation Detection**: Fixed global negation bug
- ✅ **Active Negative Filtering**: Added `avoid_time_periods` field
- ✅ **Filter Priority**: Negative filters applied before positive filters
- ✅ **Bug Fix**: `avoid_time_periods` now properly checked in `suggest_classes()`
- ✅ **Test Coverage**: 16/16 tests passing for preference extraction
- 📄 **New Documentation**: [PREFERENCE_EXTRACTION.md](./PREFERENCE_EXTRACTION.md)

---

##  Contributors

- AI/ML Team: Intent classification, NL2SQL
- Backend Team: API integration, database
- QA Team: Testing, validation

---

##  License

Internal documentation for Student Management System.

**Last updated**: December 8, 2025
