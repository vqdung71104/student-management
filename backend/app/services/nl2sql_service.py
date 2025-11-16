"""
NL2SQL Service sử dụng ViT5 (Vietnamese T5) để chuyển câu hỏi tiếng Việt thành SQL
"""
import json
import os
from typing import Dict, List, Optional, Tuple
import re


class NL2SQLService:
    """
    Service chuyển đổi Natural Language sang SQL sử dụng ViT5
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize NL2SQL Service
        
        Args:
            model_path: Path to fine-tuned ViT5 model (optional)
        """
        print("   Initializing NL2SQL Service...")
        
        self.training_data = self._load_training_data()
        self.schema = self.training_data.get("schema", {})
        self.examples = self.training_data.get("training_examples", [])
        
        # Build intent to SQL mapping
        self.intent_sql_map = self._build_intent_sql_map()
        
        # Try to load ViT5 model
        self.model = None
        self.tokenizer = None
        self.has_vit5 = False
        
        if model_path:
            self._load_vit5_model(model_path)
        
        print(f"   NL2SQL Service initialized with {len(self.examples)} examples")
        print(f"   ViT5 Model: {'Loaded' if self.has_vit5 else 'Not loaded (using rule-based fallback)'}")
    
    def _load_training_data(self) -> Dict:
        """Load NL2SQL training data"""
        data_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "nl2sql_training_data.json"
        )
        
        try:
            with open(data_path, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"   Training data not found at {data_path}")
            return {"schema": {}, "training_examples": []}
    
    def _build_intent_sql_map(self) -> Dict[str, List[Dict]]:
        """Build mapping from intent to SQL queries"""
        intent_map = {}
        
        for example in self.examples:
            intent = example.get("intent")
            if intent not in intent_map:
                intent_map[intent] = []
            intent_map[intent].append(example)
        
        return intent_map
    
    def _load_vit5_model(self, model_path: str):
        """Load fine-tuned ViT5 model"""
        try:
            from transformers import T5ForConditionalGeneration, T5Tokenizer
            
            print(f"📦 Loading ViT5 model from {model_path}...")
            
            self.tokenizer = T5Tokenizer.from_pretrained(model_path)
            self.model = T5ForConditionalGeneration.from_pretrained(model_path)
            
            # Move to GPU if available
            import torch
            if torch.cuda.is_available():
                self.model = self.model.cuda()
                print("   Using GPU")
            else:
                print("   Using CPU")
            
            self.has_vit5 = True
            print("   ViT5 model loaded successfully")
            
        except ImportError:
            print("   transformers library not installed. Using rule-based fallback.")
        except Exception as e:
            print(f"   Failed to load ViT5 model: {e}")
    
    def _normalize_question(self, question: str) -> str:
        """Normalize question for better matching"""
        # Convert to lowercase
        question = question.lower().strip()
        
        # Remove punctuation
        question = re.sub(r'[?!.,;:]', '', question)
        
        return question
    
    def _extract_entities(self, question: str) -> Dict[str, str]:
        """Extract entities from question (subject names, class IDs, etc.)"""
        entities = {}
        
        # Extract class IDs (e.g., 161084, 123456)
        class_id_match = re.search(r'\blớp\s+(\d{6})\b', question, re.IGNORECASE)
        if class_id_match:
            entities['class_id'] = class_id_match.group(1)
        
        # Extract subject IDs (e.g., IT4040, MAT1234, MI1114, EM1180Q)
        subject_id_match = re.search(r'\b([A-Z]{2,4}\d{4}[A-Z]?)\b', question)
        if subject_id_match:
            entities['subject_id'] = subject_id_match.group(1)
        
        # Extract subject names (e.g., "Giải tích 1", "Đại số", "Lý thuyết điều khiển tự động")
        # Try to extract after keywords, match until end of string or special words
        # Ordered by specificity - more specific patterns first
        subject_patterns = [
            # Patterns with "của môn" or "của học phần"
            r'(?:các lớp|lớp|thông tin lớp|thông tin các lớp)\s+của\s+môn(?:\s+học)?\s+([A-Z]{2,4}\d{4}[A-Z]?|[^,\?\.]+?)(?:\s*$|,|\?|\.)',
            r'(?:các lớp|lớp|thông tin lớp|thông tin các lớp)\s+của\s+học phần\s+([A-Z]{2,4}\d{4}[A-Z]?|[^,\?\.]+?)(?:\s*$|,|\?|\.)',
            
            # Patterns without "của" - "các lớp môn/học phần [name]"
            r'(?:các lớp|thông tin các lớp)\s+môn(?:\s+học)?\s+([A-Z]{2,4}\d{4}[A-Z]?|[^,\?\.]+?)(?:\s*$|,|\?|\.)',
            r'(?:các lớp|thông tin các lớp)\s+học phần\s+([A-Z]{2,4}\d{4}[A-Z]?|[^,\?\.]+?)(?:\s*$|,|\?|\.)',
            
            # Patterns "lớp môn/học phần [name]" (singular)
            r'lớp\s+môn(?:\s+học)?\s+([A-Z]{2,4}\d{4}[A-Z]?|[^,\?\.]+?)(?:\s*$|,|\?|\.)',
            r'lớp\s+học phần\s+([A-Z]{2,4}\d{4}[A-Z]?|[^,\?\.]+?)(?:\s*$|,|\?|\.)',
            
            # Patterns "các lớp [name]" - direct subject name after "các lớp"
            # Match Vietnamese proper noun: capital letter + any chars till end (e.g., "Giải tích I", "Mác - Lênin")
            r'(?:các lớp|cho tôi các lớp|thông tin các lớp)\s+([A-ZĐĂÂÊÔƠƯ].+)$',
            
            # Generic patterns - last resort
            r'môn(?:\s+học)?\s+([A-Z]{2,4}\d{4}[A-Z]?|[^,\?\.]+?)(?:\s*$|,|\?|\.)',
            r'học phần\s+([A-Z]{2,4}\d{4}[A-Z]?|[^,\?\.]+?)(?:\s*$|,|\?|\.)',
        ]
        
        # Stop words that should NOT be captured as subject names
        stop_words = ['gì', 'nào', 'nào đó', 'nào phù hợp', 'nào tốt', 'nào hay']
        
        for pattern in subject_patterns:
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                
                # Skip if extracted is a stop word or contains only stop words
                if extracted.lower() in stop_words:
                    continue
                if any(stop in extracted.lower() for stop in ['gì', 'nào']):
                    # Only skip if it's JUST the stop word, not part of a real subject name
                    if len(extracted.split()) <= 2:
                        continue
                
                # Check if it's a subject_id (already extracted above)
                if not re.match(r'^[A-Z]{2,4}\d{4}[A-Z]?$', extracted):
                    entities['subject_name'] = extracted
                    break
        
        # Extract day of week
        day_mapping = {
            'thứ 2': 'Monday',
            'thứ hai': 'Monday',
            'thứ 3': 'Tuesday',
            'thứ ba': 'Tuesday',
            'thứ 4': 'Wednesday',
            'thứ tư': 'Wednesday',
            'thứ 5': 'Thursday',
            'thứ năm': 'Thursday',
            'thứ 6': 'Friday',
            'thứ sáu': 'Friday',
            'thứ 7': 'Saturday',
            'thứ bảy': 'Saturday',
            'chủ nhật': 'Sunday',
        }
        
        for vn_day, en_day in day_mapping.items():
            if vn_day in question.lower():
                if 'study_days' not in entities:
                    entities['study_days'] = []
                entities['study_days'].append(en_day)
        
        # Extract time of day (morning/afternoon)
        if 'sáng' in question:
            entities['time_period'] = 'morning'
        elif 'chiều' in question or 'trưa' in question:
            entities['time_period'] = 'afternoon'
        
        return entities
    
    def _find_best_match(self, question: str, intent: str) -> Optional[Dict]:
        """Find best matching SQL template from examples"""
        normalized_q = self._normalize_question(question)
        
        # Get examples for this intent
        intent_examples = self.intent_sql_map.get(intent, [])
        
        if not intent_examples:
            return None
        
        # Key phrases to boost matching for class queries
        class_keywords = ['các lớp', 'lớp', 'danh sách lớp', 'xem lớp']
        subject_keywords = ['môn', 'học phần', 'của môn', 'của học phần']
        
        # Calculate similarity with each example
        best_match = None
        best_score = 0
        
        for example in intent_examples:
            example_q = self._normalize_question(example['question'])
            
            # Simple word overlap similarity
            q_words = set(normalized_q.split())
            ex_words = set(example_q.split())
            
            if not q_words or not ex_words:
                continue
            
            overlap = len(q_words & ex_words)
            score = overlap / max(len(q_words), len(ex_words))
            
            # Boost score if key phrases match
            for keyword in class_keywords:
                if keyword in normalized_q and keyword in example_q:
                    score += 0.2
                    break
            
            for keyword in subject_keywords:
                if keyword in normalized_q and keyword in example_q:
                    score += 0.1
                    break
            
            if score > best_score:
                best_score = score
                best_match = example
        
        print(f"   Best match score: {best_score:.2f} - Example: {best_match['question'] if best_match else 'None'}")
        
        # Return if similarity is above threshold
        if best_score > 0.25:
            return best_match
        
        # If no good match, return first example as fallback
        return intent_examples[0] if intent_examples else None
    
    def _customize_sql(self, sql_template: str, question: str, entities: Dict) -> str:
        """Customize SQL template with extracted entities"""
        sql = sql_template
        
        # Replace class_id if found
        if 'class_id' in entities:
            # Match and preserve prefix (c. or nothing)
            def replace_class_id(match):
                prefix = match.group(1) or ''
                return f"{prefix}class_id = '{entities['class_id']}'"
            
            sql = re.sub(
                r"(c\.)?class_id = '\d+'",
                replace_class_id,
                sql
            )
        
        # Replace subject_id if found
        if 'subject_id' in entities:
            # Match and preserve prefix (s. or nothing)
            def replace_subject_id(match):
                prefix = match.group(1) or ''
                return f"{prefix}subject_id = '{entities['subject_id']}'"
            
            sql = re.sub(
                r"(s\.)?subject_id = '[A-Z]{2,4}\d{4}[A-Z]?'",
                replace_subject_id,
                sql
            )
        
        # Replace subject_name if found
        if 'subject_name' in entities:
            subject_name = entities['subject_name']
            # Match and preserve prefix (s. or nothing)
            def replace_subject_name(match):
                prefix = match.group(1) or ''
                return f"{prefix}subject_name LIKE '%{subject_name}%'"
            
            sql = re.sub(
                r"(s\.)?subject_name LIKE '%[^']+%'",
                replace_subject_name,
                sql
            )
        
        # Customize by study days
        if 'study_days' in entities:
            days = entities['study_days']
            day_conditions = ' OR '.join([f"c.study_date LIKE '%{day}%'" for day in days])
            # Replace existing day conditions
            sql = re.sub(
                r"c\.study_date LIKE '%\w+%'(?: OR c\.study_date LIKE '%\w+%')*",
                day_conditions,
                sql
            )
        
        # Customize by time period
        if 'time_period' in entities:
            if entities['time_period'] == 'morning':
                if "c.study_time_start" not in sql:
                    sql += " AND c.study_time_start < '12:00:00'"
            elif entities['time_period'] == 'afternoon':
                if "c.study_time_start" not in sql:
                    sql += " AND c.study_time_start >= '12:00:00'"
        
        return sql
    
    async def generate_sql(
        self,
        question: str,
        intent: str,
        student_id: Optional[int] = None
    ) -> Dict:
        """
        Generate SQL query from natural language question
        
        Args:
            question: Natural language question
            intent: Detected intent
            student_id: Student ID (for authenticated queries)
            
        Returns:
            Dict containing SQL query, parameters, and metadata
        """
        print(f"  NL2SQL generate_sql called:")
        print(f"  Question: {question}")
        print(f"  Intent: {intent}")
        print(f"  Student ID: {student_id}")
        
        # Extract entities from question
        entities = self._extract_entities(question)
        print(f"  Entities: {entities}")
        
        # If ViT5 model is available, use it
        if self.has_vit5:
            result = await self._generate_with_vit5(question, intent, student_id, entities)
        else:
            # Otherwise, use rule-based approach
            result = self._generate_rule_based(question, intent, student_id, entities)
        
        print(f"   Generated SQL: {result.get('sql')}")
        print(f"   Method: {result.get('method')}")
        
        return result
    
    async def _generate_with_vit5(
        self,
        question: str,
        intent: str,
        student_id: Optional[int],
        entities: Dict
    ) -> Dict:
        """Generate SQL using ViT5 model"""
        import torch
        
        # Prepare input for ViT5
        # Format: "intent: <intent> | question: <question> | schema: <schema_info>"
        schema_info = self._get_relevant_schema(intent)
        input_text = f"intent: {intent} | question: {question} | schema: {schema_info}"
        
        # Tokenize
        inputs = self.tokenizer(
            input_text,
            return_tensors="pt",
            max_length=512,
            truncation=True
        )
        
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}
        
        # Generate SQL
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=256,
                num_beams=5,
                early_stopping=True
            )
        
        # Decode
        generated_sql = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Replace parameters
        if "{student_id}" in generated_sql:
            if student_id:
                generated_sql = generated_sql.replace("{student_id}", str(student_id))
            else:
                # If student_id is required but not provided, return error
                return {
                    "sql": None,
                    "method": "vit5",
                    "intent": intent,
                    "entities": entities,
                    "error": "Authentication required: student_id is missing",
                    "requires_auth": True
                }
        
        # Customize with entities
        generated_sql = self._customize_sql(generated_sql, question, entities)
        
        return {
            "sql": generated_sql,
            "method": "vit5",
            "intent": intent,
            "entities": entities,
            "requires_auth": "{student_id}" in generated_sql or student_id is not None
        }
    
    def _generate_rule_based(
        self,
        question: str,
        intent: str,
        student_id: Optional[int],
        entities: Dict
    ) -> Dict:
        """Generate SQL using rule-based approach (fallback)"""
        # Find best matching example
        match = self._find_best_match(question, intent)
        
        if not match:
            return {
                "sql": None,
                "method": "rule_based",
                "intent": intent,
                "entities": entities,
                "error": "No matching SQL template found",
                "requires_auth": False
            }
        
        # Get SQL template
        sql_template = match['sql']
        requires_auth = match['requires_auth']
        
        # Replace student_id if needed
        if "{student_id}" in sql_template:
            if student_id is not None:
                sql_template = sql_template.replace("{student_id}", str(student_id))
            else:
                # If student_id is required but not provided, return error
                print(f"   student_id is required but not provided for intent: {intent}")
                return {
                    "sql": None,
                    "method": "rule_based",
                    "intent": intent,
                    "entities": entities,
                    "error": "Bạn cần đăng nhập để xem thông tin này",
                    "requires_auth": True
                }
        
        # Customize SQL with entities
        final_sql = self._customize_sql(sql_template, question, entities)
        
        return {
            "sql": final_sql,
            "method": "rule_based",
            "intent": intent,
            "entities": entities,
            "template_match": match['question'],
            "requires_auth": requires_auth
        }
    
    def _get_relevant_schema(self, intent: str) -> str:
        """Get relevant schema information for the intent"""
        # Map intents to relevant tables
        intent_tables = {
            "grade_view": ["students", "learned_subjects"],
            "student_info": ["students", "learned_subjects"],
            "subject_info": ["subjects"],
            "class_info": ["classes", "subjects"],
            "schedule_view": ["class_registers", "classes", "subjects"],
            "subject_registration_suggestion": ["subjects", "learned_subjects"],
            "class_registration_suggestion": ["classes", "subjects", "class_registers"],
        }
        
        relevant_tables = intent_tables.get(intent, [])
        
        schema_str = ""
        for table in relevant_tables:
            if table in self.schema:
                cols = ", ".join(self.schema[table]["columns"])
                schema_str += f"{table}({cols}); "
        
        return schema_str.strip()
    
    def get_example_queries(self, intent: str) -> List[Dict]:
        """Get example queries for an intent"""
        return self.intent_sql_map.get(intent, [])
    
    def get_schema_info(self) -> Dict:
        """Get database schema information"""
        return self.schema


# For testing
if __name__ == "__main__":
    import asyncio
    
    async def test():
        service = NL2SQLService()
        
        test_cases = [
            ("xem điểm", "grade_view", 1),
            ("các môn bị D", "student_info", 1),
            ("môn tiên quyết của IT4040", "subject_info", None),
            ("danh sách các lớp môn Đại số", "class_info", None),
            ("lịch học", "schedule_view", 1),
        ]
        
        print("\n" + "="*70)
        print("   TESTING NL2SQL SERVICE")
        print("="*70)
        
        for question, intent, student_id in test_cases:
            result = await service.generate_sql(question, intent, student_id)
            
            print(f"\n   Question: \"{question}\"")
            print(f"   Intent: {intent}")
            print(f"   SQL: {result.get('sql', 'None')}")
            print(f"🔧 Method: {result.get('method')}")
            if result.get('entities'):
                print(f"🏷️  Entities: {result['entities']}")
        
        print("\n" + "="*70)
    
    asyncio.run(test())
