"""
NL2SQL Service sử dụng rule-based để chuyển câu hỏi tiếng Việt thành SQL
"""
import json
import os
from typing import Dict, List, Optional, Tuple
import re

# FuzzyMatcher — import lazy để tránh circular imports
def _get_fuzzy_matcher():
    try:
        from app.services.fuzzy_matcher import FuzzyMatcher
        return FuzzyMatcher
    except ImportError:
        return None


class NL2SQLService:
    """
    Service chuyển đổi Natural Language sang SQL (rule-based only)
    """
    def __init__(self):
        """
        Initialize NL2SQL Service (rule-based only)
        """
        print("   Initializing NL2SQL Service (rule-based only)...")
        self.training_data = self._load_training_data()
        self.schema = self.training_data.get("schema", {})
        self.examples = self.training_data.get("training_examples", [])
        self.intent_sql_map = self._build_intent_sql_map()
        print(f"   NL2SQL Service initialized with {len(self.examples)} examples (rule-based only)")
    
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
    
    def _extract_entities(self, question: str) -> Dict[str, str]:
        """Extract entities from question (subject names, class IDs, etc.)"""
        entities = {}
        
        # Extract class IDs (e.g., 161084, 123456)
        class_id_match = re.search(r'\blớp\s+(\d{6})\b', question, re.IGNORECASE)
        if class_id_match:
            entities['class_id'] = class_id_match.group(1)
        
        # Extract subject IDs (e.g., IT4040, MAT1234, MI1114, EM1180Q)
        # Use findall to capture ALL codes in the question (for multi-subject queries)
        subject_id_matches = re.findall(r'\b([A-Z]{2,4}\d{3,5}[A-Z]?)\b', question)
        if subject_id_matches:
            # Deduplicate while preserving order
            seen = []
            for s in subject_id_matches:
                if s not in seen:
                    seen.append(s)
            subject_id_matches = seen
            entities['subject_id'] = subject_id_matches[0]   # compat: first code
            if len(subject_id_matches) > 1:
                entities['subject_ids'] = subject_id_matches  # full list for IN query
        
        # Extract subject names (e.g., "Giải tích 1", "Đại số", "Lý thuyết điều khiển tự động")
        # Try to extract after keywords, match until end of string or special words
        # Ordered by specificity - more specific patterns first
        subject_patterns = [
            # Patterns with "của môn" or "của học phần"
            r'(?:các lớp|lớp|thông tin lớp|thông tin các lớp|danh sách lớp)\s+của\s+môn(?:\s+học)?\s+([A-Z]{2,4}\d{4}[A-Z]?|[^,\?\.]+?)(?:\s*$|,|\?|\.)',
            r'(?:các lớp|lớp|thông tin lớp|thông tin các lớp|danh sách lớp)\s+của\s+học phần\s+([A-Z]{2,4}\d{4}[A-Z]?|[^,\?\.]+?)(?:\s*$|,|\?|\.)',
            
            # Patterns without "của" - "các lớp môn/học phần [name]"
            r'(?:các lớp|thông tin các lớp|danh sách lớp|danh sách các lớp)\s+môn(?:\s+học)?\s+([A-Z]{2,4}\d{4}[A-Z]?|[^,\?\.]+?)(?:\s*$|,|\?|\.)',
            r'(?:các lớp|thông tin các lớp|danh sách lớp|danh sách các lớp)\s+học phần\s+([A-Z]{2,4}\d{4}[A-Z]?|[^,\?\.]+?)(?:\s*$|,|\?|\.)',
            
            # Patterns "lớp môn/học phần [name]" (singular)
            r'lớp\s+môn(?:\s+học)?\s+([A-Z]{2,4}\d{4}[A-Z]?|[^,\?\.]+?)(?:\s*$|,|\?|\.)',
            r'lớp\s+học phần\s+([A-Z]{2,4}\d{4}[A-Z]?|[^,\?\.]+?)(?:\s*$|,|\?|\.)',
            
            # Patterns "thông tin lớp [name]" - direct subject name
            r'thông tin\s+lớp\s+([A-ZĐĂÂÊÔƠƯ][^,\?\.]+?)(?:\s*$|,|\?|\.)',
            
            # Patterns "các lớp [name]" - direct subject name after "các lớp"
            # Match Vietnamese proper noun: capital letter + any chars till end (e.g., "Giải tích I", "Mác - Lênin")
            r'(?:các lớp|cho tôi các lớp|thông tin các lớp|danh sách các lớp)\s+([A-ZĐĂÂÊÔƠƯ].+?)(?:\s*$|,|\?|\.)',
            
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

        # Multi-subject list extraction for same intent, e.g.:
        # "điểm các môn giải tích 1, giải tích 2; đại số tuyến tính"
        list_names = self._extract_subject_name_list(question)
        if len(list_names) > 1:
            entities['subject_names'] = list_names
            if 'subject_name' not in entities:
                entities['subject_name'] = list_names[0]
        
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
        
        # Extract building and room (classroom info)
        # Format: "tòa D9", "phòng 401", "D9-401", "D9 401", etc.
        building = None
        room = None
        
        # Pattern 1: "tòa [TÊNÒA]" (e.g., "tòa D9", "tòa A")
        toa_match = re.search(r'tòa\s+([A-Z]\d+|[A-Z]{1,2})', question, re.IGNORECASE)
        if toa_match:
            building = toa_match.group(1).upper()
        
        # Pattern 2: "phòng [SỐ]" (e.g., "phòng 401", "phòng 402")
        phong_match = re.search(r'phòng\s+(\d{2,4})', question, re.IGNORECASE)
        if phong_match:
            room = phong_match.group(1)
        
        # Pattern 3: "[TÒA]-[PHÒNG]" format (e.g., "D9-401", "A1-201", "D9 401", "D9401")
        # This covers both "D9-401" and "D9 401" formats
        classroom_format_match = re.search(r'(?:học\s+ở|ở\s+)?([A-Z]\d+)[\s\-]+(\d{2,4})', question, re.IGNORECASE)
        if classroom_format_match and not building and not room:
            building = classroom_format_match.group(1).upper()
            room = classroom_format_match.group(2)
        
        # Store building and room separately for SQL customization
        if building:
            entities['building'] = building
        if room:
            entities['room'] = room
        
        return entities

    def _extract_subject_name_list(self, question: str) -> List[str]:
        """Extract list of subject names from comma/semicolon/conjunction separated input."""
        q = question.strip()
        if not q:
            return []

        lower = q.lower()

        anchor_patterns = [
            r'(?:điểm\s+các\s+môn|điểm\s+môn|xem\s+điểm\s+các\s+môn|xem\s+điểm\s+môn)\s+(.+)$',
            r'(?:các\s+lớp\s+của\s+các\s+môn|các\s+lớp\s+của\s+môn|các\s+lớp\s+môn|thông\s+tin\s+các\s+lớp\s+môn|danh\s+sách\s+các\s+lớp\s+môn)\s+(.+)$',
            r'(?:môn|học\s+phần|lớp)\s+(.+)$',
        ]

        tail = None
        for pat in anchor_patterns:
            m = re.search(pat, lower, flags=re.IGNORECASE)
            if m:
                tail = m.group(1).strip()
                break

        if not tail:
            return []

        # Stop at time/day clauses to avoid leaking scheduling constraints into subject names
        tail = re.split(
            r'\b(?:học\s+vào|vào\s+thứ|thứ\s+\d|thứ\s+(?:hai|ba|tư|năm|sáu|bảy)|chủ\s+nhật|buổi|lúc|từ\s+\d|đến\s+\d|kỳ\s+này|hiện\s+tại)\b',
            tail,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0].strip()

        if not re.search(r'[;,]|\s+và\s+|\s+hoặc\s+', tail, flags=re.IGNORECASE):
            return []

        raw_parts = re.split(r'[;,]|\s+và\s+|\s+hoặc\s+', tail, flags=re.IGNORECASE)
        names: List[str] = []
        for part in raw_parts:
            p = part.strip(' .')
            if not p:
                continue
            p = re.sub(r'^(?:môn|học\s+phần|lớp|các\s+môn|các\s+lớp|của)\s+', '', p, flags=re.IGNORECASE).strip()
            if not p or p in {'gì', 'nào'}:
                continue
            if p not in names:
                names.append(p)

        return names
    
    def _find_best_match(self, question: str, intent: str) -> Optional[Dict]:
        """Find best matching SQL template from examples"""
        normalized_q = self._normalize_question(question)
        
        # Get examples for this intent
        intent_examples = self.intent_sql_map.get(intent, [])
        
        if not intent_examples:
            return None
        
        # Extract entities to understand query structure
        entities = self._extract_entities(question)
        has_subject_name = 'subject_name' in entities
        has_subject_id = 'subject_id' in entities
        has_class_id = 'class_id' in entities
        
        # Key phrases to boost matching for class queries
        class_keywords = ['các lớp', 'lớp', 'danh sách lớp', 'xem lớp', 'thông tin lớp']
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
            
            # IMPORTANT: Penalize mismatched query types
            # If user asks about subject_name but example uses class_id, reduce score
            example_sql = example.get('sql', '')
            if has_subject_name or has_subject_id:
                # User is asking by subject, prefer templates with subject filters
                if "subject_name LIKE" in example_sql or "subject_id =" in example_sql:
                    score += 0.3  # Boost templates that filter by subject
                elif "class_id =" in example_sql:
                    score -= 0.5  # Penalize templates that only filter by class_id
            
            if has_class_id:
                # User is asking by class_id, prefer templates with class_id
                if "class_id =" in example_sql:
                    score += 0.3
                else:
                    score -= 0.2
            
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
        """
        Customize SQL template with extracted entities.

        Logic:
        - subject_id có sẵn (regex) → thay vào subject_id placeholder
        - subject_id từ fuzzy ("auto_mapped") → thay subject_name LIKE bằng subject_id filter
        - Chỉ có subject_name → thay LIKE placeholder
        - Thêm DISTINCT khi JOIN để tránh duplicate rows
        """
        sql = sql_template

        # ── 1. DISTINCT: tránh duplicate rows khi JOIN ─────────────────────────
        if re.search(r'\bJOIN\b', sql, re.IGNORECASE) and 'DISTINCT' not in sql.upper():
            sql = re.sub(r'\bSELECT\b', 'SELECT DISTINCT', sql, count=1, flags=re.IGNORECASE)

        # ── 2. class_id ─────────────────────────────────────────────────────────
        if 'class_id' in entities:
            def replace_class_id(match):
                prefix = match.group(1) or ''
                return f"{prefix}class_id = '{entities['class_id']}'"
            sql = re.sub(r"(c\.)?class_id = '\d+'", replace_class_id, sql)

        # ── 3. subject_id / subject_ids ──────────────────────────────────────────
        if 'subject_id' in entities:
            subject_ids_list = entities.get('subject_ids', [entities['subject_id']])
            subj_id = entities['subject_id']  # first / only

            # Build SQL fragment: = 'X' for single, IN('X','Y') for multiple
            def _make_filter(col_prefix: str = 's') -> str:
                if len(subject_ids_list) > 1:
                    ids_str = ', '.join(f"'{s}'" for s in subject_ids_list)
                    return f"{col_prefix}.subject_id IN ({ids_str})"
                return f"{col_prefix}.subject_id = '{subj_id}'"

            # 3a. Thay subject_id placeholder trong template nếu có
            new_sql = re.sub(
                r"(s\.)?subject_id\s*=\s*'[^']*'",
                lambda m: _make_filter('s'),
                sql,
                flags=re.IGNORECASE
            )

            if new_sql != sql:
                sql = new_sql
                # Xóa subject_name LIKE thừa nếu vẫn còn
                sql = re.sub(r"\s+AND\s+(s\.)?subject_name\s+LIKE\s+'%[^']+%'",
                             '', sql, flags=re.IGNORECASE)
                sql = re.sub(r"(s\.)?subject_name\s+LIKE\s+'%[^']+%'\s+AND\s+",
                             '', sql, flags=re.IGNORECASE)
            else:
                # 3b. Template dùng subject_name LIKE → thay bằng subject_id
                has_like = bool(re.search(
                    r"(s\.)?subject_name\s+LIKE\s+'%[^']+%'", sql, re.IGNORECASE
                ))
                # Cũng có thể template dùng ls.subject_name LIKE (learned_subjects)
                has_ls_like = bool(re.search(
                    r"ls\.subject_name\s+LIKE\s+'%[^']+%'", sql, re.IGNORECASE
                ))

                if has_like or has_ls_like:
                    # Đảm bảo có JOIN subjects nếu query liên quan đến learned_subjects hoặc classes
                    if not re.search(r'JOIN\s+subjects', sql, re.IGNORECASE):
                        sql = re.sub(
                            r'(FROM\s+(?:learned_subjects|classes)\s+(?:ls|c))(\s)',
                            r'\1 JOIN subjects s ON \1.subject_id = s.id\2',
                            sql, flags=re.IGNORECASE
                        )
                    # Thay tất cả dạng subject_name LIKE bằng s.subject_id / IN
                    sql = re.sub(
                        r"(?:ls|s|c)?\.?subject_name\s+LIKE\s+'%[^']+%'",
                        lambda m: _make_filter('s'),
                        sql, flags=re.IGNORECASE
                    )
                    # Thêm DISTINCT do vừa thêm JOIN
                    if 'DISTINCT' not in sql.upper():
                        sql = re.sub(r'\bSELECT\b', 'SELECT DISTINCT', sql,
                                     count=1, flags=re.IGNORECASE)
                else:
                    # Template không có filter môn nào → thêm vào WHERE 
                    # NHƯNG CHỈ THÊM NẾU CÂU TRUY VẤN CÓ BẢNG subjects HOẶC ĐƯỢC THÊM VÀO JOIN
                    if not re.search(r'JOIN\s+subjects', sql, re.IGNORECASE):
                        sql = re.sub(
                            r'(FROM\s+(?:learned_subjects|classes|subject_registers)\s+(?:ls|c|sr))(\s)',
                            r'\1 JOIN subjects s ON \1.subject_id = s.id\2',
                            sql, flags=re.IGNORECASE
                        )
                    
                    if re.search(r'\bsubjects\s+s\b', sql, re.IGNORECASE) or bool(re.search(r'JOIN\s+subjects\b', sql, re.IGNORECASE)):
                        if re.search(r'\bWHERE\b', sql, re.IGNORECASE):
                            sql = re.sub(
                                r'(\bWHERE\b\s+)',
                                lambda m: f"WHERE {_make_filter('s')} AND ",
                                sql, count=1, flags=re.IGNORECASE
                            )
                        else:
                            sql += f" WHERE {_make_filter('s')}"

        elif 'subject_name' in entities:
            # Chỉ có subject_name (không có subject_id) → dùng LIKE
            subject_name = entities['subject_name']

            def replace_subject_name(match):
                prefix = match.group(1) or ''
                return f"{prefix}subject_name LIKE '%{subject_name}%'"

            sql = re.sub(
                r"(s\.|ls\.)?subject_name LIKE '%[^']+'%'",  # typo-safe
                replace_subject_name, sql, flags=re.IGNORECASE
            )
            # Fallback: pattern không có ngoặc đóng
            sql = re.sub(
                r"(s\.|ls\.)?subject_name LIKE '%[^']+%'",
                replace_subject_name, sql, flags=re.IGNORECASE
            )
        else:
            # Không có entity môn → xóa filter khỏi template
            sql = re.sub(
                r"WHERE\s+(s\.)?subject_name\s+LIKE\s+'%[^']+%'\s*$",
                "", sql, flags=re.IGNORECASE
            )
            sql = re.sub(
                r"(WHERE\s+.+?)\s+AND\s+(s\.)?subject_name\s+LIKE\s+'%[^']+%'",
                r"\1", sql, flags=re.IGNORECASE
            )
            sql = re.sub(
                r"WHERE\s+(s\.)?subject_name\s+LIKE\s+'%[^']+%'\s+AND\s+",
                "WHERE ", sql, flags=re.IGNORECASE
            )

        # ── 4. building and room (classroom filter) ──────────────────────────────────
        # Format: "tòa-phòng" (e.g., "D9-401")
        if 'building' in entities or 'room' in entities:
            building = entities.get('building')
            room = entities.get('room')
            
            if building and room:
                # Both specified: exact format "D9-401"
                classroom_filter = f"c.classroom = '{building}-{room}'"
            elif building:
                # Only building: "D9-%"
                classroom_filter = f"c.classroom LIKE '{building}-%'"
            elif room:
                # Only room: "%-401"
                classroom_filter = f"c.classroom LIKE '%-{room}'"
            else:
                classroom_filter = None
            
            if classroom_filter:
                # Try to replace existing classroom filter in WHERE clause
                if "c.classroom" in sql:
                    sql = re.sub(
                        r"c\.classroom\s*(?:=|LIKE)\s*'[^']*'",
                        classroom_filter,
                        sql,
                        flags=re.IGNORECASE
                    )
                else:
                    # Add classroom filter to WHERE clause
                    if re.search(r'\bWHERE\b', sql, re.IGNORECASE):
                        sql = re.sub(
                            r'(\bWHERE\b\s+)',
                            lambda m: f"{m.group(0)}{classroom_filter} AND ",
                            sql,
                            count=1,
                            flags=re.IGNORECASE
                        )
                    else:
                        sql += f" WHERE {classroom_filter}"
        
        # ── 5. study_days ────────────────────────────────────────────────────────
        if 'study_days' in entities:
            days = entities['study_days']
            day_conditions = ' OR '.join([f"c.study_date LIKE '%{day}%'" for day in days])
            sql = re.sub(
                r"c\.study_date LIKE '%\w+%'(?: OR c\.study_date LIKE '%\w+%')*",
                day_conditions, sql
            )

        # ── 6. time_period ───────────────────────────────────────────────────────
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
        student_id: Optional[int] = None,
        db=None
    ) -> Dict:
        """
        Generate SQL query from natural language question (rule-based only)
        """
        print(f"  NL2SQL generate_sql called (rule-based only):")
        print(f"  Question: {question}")
        print(f"  Intent: {intent}")
        print(f"  Student ID: {student_id}")
        # Extract entities từ question (regex-based)
        entities = self._extract_entities(question)
        print(f"  Entities (raw): {entities}")
        result = self._generate_rule_based(question, intent, student_id, entities)
        print(f"   Generated SQL: {result.get('sql')}")
        print(f"   Method: {result.get('method')}")
        return result

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
            "student_info": ["students", "courses", "semester_gpa"],
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
