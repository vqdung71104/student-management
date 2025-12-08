"""
Chatbot Service - Business logic for chatbot interactions
Integrates Rule Engine for intelligent subject/class suggestions
"""
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.rules.subject_suggestion_rules import SubjectSuggestionRuleEngine
from app.rules.class_suggestion_rules import ClassSuggestionRuleEngine


class ChatbotService:
    """
    Service layer for chatbot functionality
    Handles integration between intent classification, rule engine, and NL2SQL
    """
    
    def __init__(self, db: Session):
        """
        Initialize chatbot service
        
        Args:
            db: Database session
        """
        self.db = db
        self.subject_rule_engine = SubjectSuggestionRuleEngine(db)
        self.class_rule_engine = ClassSuggestionRuleEngine(db)
    
    async def process_subject_suggestion(
        self, 
        student_id: int,
        question: str,
        max_credits: Optional[int] = None
    ) -> Dict:
        """
        Process subject suggestion request using rule engine
        
        Args:
            student_id: Student ID
            question: User's question (for context)
            max_credits: Optional max credits override
        
        Returns:
            Dict with text response, intent, confidence, and structured data
        """
        try:
            # Validate student_id
            if not student_id:
                return {
                    "text": "⚠️ Vui lòng đăng nhập để nhận gợi ý đăng ký học phần.",
                    "intent": "subject_registration_suggestion",
                    "confidence": "high",
                    "data": None,
                    "requires_auth": True
                }
            
            # Use rule engine to get subject suggestions
            result = self.subject_rule_engine.suggest_subjects(student_id, max_credits)
            
            # Format human-readable response
            text_response = self.subject_rule_engine.format_suggestion_response(result)
            
            # Return structured response
            return {
                "text": text_response,
                "intent": "subject_registration_suggestion",
                "confidence": "high",
                "data": result['suggested_subjects'],
                "summary": result['summary'],
                "metadata": {
                    "total_credits": result['total_credits'],
                    "meets_minimum": result['meets_minimum'],
                    "min_credits_required": result['min_credits_required'],
                    "max_credits_allowed": result['max_credits_allowed'],
                    "current_semester": result['current_semester'],
                    "student_semester_number": result['student_semester_number'],
                    "student_cpa": result['student_cpa'],
                    "warning_level": result['warning_level']
                },
                "rule_engine_used": True
            }
            
        except ValueError as e:
            # Student not found or invalid data
            return {
                "text": f"❌ Lỗi: {str(e)}",
                "intent": "subject_registration_suggestion",
                "confidence": "high",
                "data": None,
                "error": str(e)
            }
        except Exception as e:
            # Unexpected error
            return {
                "text": f"❌ Xin lỗi, đã xảy ra lỗi khi gợi ý học phần: {str(e)}",
                "intent": "subject_registration_suggestion",
                "confidence": "low",
                "data": None,
                "error": str(e)
            }
    
    async def process_class_suggestion(
        self,
        student_id: int,
        question: str,
        subject_id: Optional[str] = None
    ) -> Dict:
        """
        Process class suggestion request with intelligent filtering
        
        This method is ONLY called when intent = "class_registration_suggestion"
        It extracts user preferences from the question and applies smart filtering:
        - Time preferences (morning/afternoon/evening)
        - Avoid early start / late end
        - Avoid specific days (Saturday, Sunday, etc.)
        - Teacher preferences
        - Continuous classes
        
        Args:
            student_id: Student ID
            question: User's question (used for preference extraction)
            subject_id: Optional specific subject ID to filter
        
        Returns:
            Dict with text response and class suggestions
        """
        try:
            print(f"🎯 [CLASS_SUGGESTION] Processing for student {student_id}")
            print(f"📝 [CLASS_SUGGESTION] Question: {question}")
            
            # Validate student_id
            if not student_id:
                return {
                    "text": "⚠️ Vui lòng đăng nhập để nhận gợi ý đăng ký lớp học.",
                    "intent": "class_registration_suggestion",
                    "confidence": "high",
                    "data": None,
                    "requires_auth": True
                }
            
            # Extract preferences from question
            preferences = self._extract_preferences_from_question(question)
            print(f"⚙️ [CLASS_SUGGESTION] Extracted preferences: {preferences}")
            
            # First, get subject suggestions from rule engine
            subject_result = self.subject_rule_engine.suggest_subjects(student_id)
            
            # Get list of suggested subjects
            suggested_subjects = subject_result['suggested_subjects']
            
            # Extract specific subject from question if not provided
            if not subject_id:
                subject_keyword = self._extract_subject_from_question(question)
                if subject_keyword:
                    print(f"📚 [CLASS_SUGGESTION] Extracted subject keyword: {subject_keyword}")
                    # Try to find matching subject in suggested_subjects
                    for subj in suggested_subjects:
                        subj_id = subj.get('subject_id', '')
                        subj_name = subj.get('subject_name', '').lower()
                        # Match by ID prefix or name
                        if (subj_id.startswith(subject_keyword) or 
                            subject_keyword.lower() in subj_name):
                            subject_id = subj_id
                            print(f"✅ [CLASS_SUGGESTION] Matched to subject: {subject_id}")
                            break
            
            # Filter by subject_id if found
            if subject_id:
                original_count = len(suggested_subjects)
                suggested_subjects = [
                    s for s in suggested_subjects 
                    if s['subject_id'] == subject_id
                ]
                
                if not suggested_subjects:
                    return {
                        "text": f"⚠️ Môn {subject_id} không nằm trong danh sách gợi ý cho bạn.",
                        "intent": "class_registration_suggestion",
                        "confidence": "high",
                        "data": None
                    }
                print(f"🔍 [CLASS_SUGGESTION] Filtered from {original_count} to {len(suggested_subjects)} subjects")
            else:
                # Limit to top 5 subjects
                suggested_subjects = suggested_subjects[:5]
            
            # Get subject IDs
            subject_ids = [subj['id'] for subj in suggested_subjects]
            
            # Use ClassSuggestionRuleEngine to get smart suggestions with preferences
            class_suggestion_result = self.class_rule_engine.suggest_classes(
                student_id=student_id,
                subject_ids=subject_ids,
                preferences=preferences,
                registered_classes=[],  # TODO: Get from database
                min_suggestions=5
            )
            
            suggested_classes = class_suggestion_result['suggested_classes']
            
            # Add priority reasons from subject suggestions
            subject_reasons = {subj['subject_id']: subj.get('priority_reason', '') 
                              for subj in suggested_subjects}
            
            # Format classes for response
            classes = []
            for cls in suggested_classes:
                classes.append({
                    "class_id": cls['class_id'],
                    "class_name": cls['class_name'],
                    "classroom": cls['classroom'],
                    "study_date": cls['study_date'],
                    "study_time_start": cls['study_time_start'].strftime('%H:%M') if hasattr(cls.get('study_time_start'), 'strftime') else str(cls.get('study_time_start', '')),
                    "study_time_end": cls['study_time_end'].strftime('%H:%M') if hasattr(cls.get('study_time_end'), 'strftime') else str(cls.get('study_time_end', '')),
                    "teacher_name": cls.get('teacher_name', ''),
                    "subject_id": cls.get('subject_id', ''),
                    "subject_name": cls.get('subject_name', ''),
                    "credits": cls.get('credits', 0),
                    "registered_students": cls.get('registered_count', 0),
                    "max_students": cls.get('max_students', 0),
                    "seats_available": cls.get('available_slots', 0),
                    "priority_reason": subject_reasons.get(cls.get('subject_id', ''), ''),
                    "preference_score": cls.get('preference_score', 0),
                    "violation_count": cls.get('violation_count', 0),
                    "violations": cls.get('violations', []),
                    "fully_satisfies": cls.get('fully_satisfies_preferences', False)
                })
            
            # Format response text
            text_response = self._format_class_suggestions(
                classes, 
                suggested_subjects,
                subject_result
            )
            
            return {
                "text": text_response,
                "intent": "class_registration_suggestion",
                "confidence": "high",
                "data": classes,
                "metadata": {
                    "total_subjects": len(suggested_subjects),
                    "total_classes": len(classes),
                    "student_cpa": subject_result['student_cpa'],
                    "current_semester": subject_result['current_semester']
                },
                "rule_engine_used": True
            }
            
        except Exception as e:
            return {
                "text": f"❌ Xin lỗi, đã xảy ra lỗi khi gợi ý lớp học: {str(e)}",
                "intent": "class_registration_suggestion",
                "confidence": "low",
                "data": None,
                "error": str(e)
            }
    
    def _extract_preferences_from_question(self, question: str) -> Dict:
        """
        Extract class preferences from user's question
        
        Args:
            question: User's question
        
        Returns:
            Dict with preferences
        """
        question_lower = question.lower()
        preferences = {}
        
        # Time period preferences
        if any(word in question_lower for word in ['sáng', 'buổi sáng', 'morning']):
            preferences['time_period'] = 'morning'
        elif any(word in question_lower for word in ['chiều', 'buổi chiều', 'afternoon']):
            preferences['time_period'] = 'afternoon'
        elif any(word in question_lower for word in ['tối', 'buổi tối', 'evening']):
            preferences['time_period'] = 'evening'
        
        # Avoid early start
        if any(phrase in question_lower for phrase in ['không muốn học sớm', 'tránh học sớm', 'không học sớm']):
            preferences['avoid_early_start'] = True
        
        # Avoid late end
        if any(phrase in question_lower for phrase in [
            'không muốn học muộn', 'tránh học muộn', 'không học muộn',
            'không muốn học đến', 'kết thúc sớm', 'tan sớm',
            'không học đến 17', 'không học đến 18', 'không học đến 19'
        ]):
            preferences['avoid_late_end'] = True
        
        # Prefer specific days (positive preference - "muốn học vào thứ X")
        prefer_days = []
        if any(phrase in question_lower for phrase in ['muốn học vào thứ 2', 'học vào thứ 2', 'thứ 2', 'học thứ 2']):
            if 'không' not in question_lower and 'tránh' not in question_lower:
                prefer_days.append('Monday')
        if any(phrase in question_lower for phrase in ['muốn học vào thứ 3', 'học vào thứ 3', 'học thứ 3']):
            if 'không' not in question_lower and 'tránh' not in question_lower:
                prefer_days.append('Tuesday')
        if any(phrase in question_lower for phrase in ['muốn học vào thứ 4', 'học vào thứ 4', 'học thứ 4']):
            if 'không' not in question_lower and 'tránh' not in question_lower:
                prefer_days.append('Wednesday')
        if any(phrase in question_lower for phrase in ['muốn học vào thứ 5', 'học vào thứ 5', 'học thứ 5', 'vào thứ 5']):
            if 'không' not in question_lower and 'tránh' not in question_lower:
                prefer_days.append('Thursday')
        if any(phrase in question_lower for phrase in ['muốn học vào thứ 6', 'học vào thứ 6', 'học thứ 6']):
            if 'không' not in question_lower and 'tránh' not in question_lower:
                prefer_days.append('Friday')
        if any(phrase in question_lower for phrase in ['muốn học vào thứ 7', 'học vào thứ 7', 'học thứ 7']):
            if 'không' not in question_lower and 'tránh' not in question_lower:
                prefer_days.append('Saturday')
        if any(phrase in question_lower for phrase in ['muốn học chủ nhật', 'học chủ nhật']):
            if 'không' not in question_lower and 'tránh' not in question_lower:
                prefer_days.append('Sunday')
        
        if prefer_days:
            preferences['prefer_days'] = prefer_days
        
        # Avoid specific days (negative preference - "không muốn học thứ X")
        avoid_days = []
        if any(phrase in question_lower for phrase in ['không học thứ 7', 'tránh thứ 7', 'không thứ 7']):
            avoid_days.append('Saturday')
        if any(phrase in question_lower for phrase in ['không học chủ nhật', 'tránh chủ nhật', 'không chủ nhật']):
            avoid_days.append('Sunday')
        if any(phrase in question_lower for phrase in ['không học thứ 2', 'tránh thứ 2']):
            avoid_days.append('Monday')
        if any(phrase in question_lower for phrase in ['không học thứ 3', 'tránh thứ 3']):
            avoid_days.append('Tuesday')
        if any(phrase in question_lower for phrase in ['không học thứ 4', 'tránh thứ 4']):
            avoid_days.append('Wednesday')
        if any(phrase in question_lower for phrase in ['không học thứ 5', 'tránh thứ 5']):
            avoid_days.append('Thursday')
        if any(phrase in question_lower for phrase in ['không học thứ 6', 'tránh thứ 6']):
            avoid_days.append('Friday')
        
        if avoid_days:
            preferences['avoid_days'] = avoid_days
        
        # Continuous classes preference
        if any(phrase in question_lower for phrase in ['học liên tục', 'liên tục']):
            preferences['prefer_continuous'] = True
        
        return preferences
    
    def _extract_subject_from_question(self, question: str) -> Optional[str]:
        """
        Extract specific subject ID from user's question
        
        Examples:
            - "gợi ý lớp Tiếng Nhật" → "JP"
            - "lớp tiếng anh nào" → "ENG"
            - "môn lập trình mạng" → "IT3170"
            - "môn SSH1131" → "SSH1131"
        
        Args:
            question: User's question
        
        Returns:
            Subject ID or None if not found
        """
        question_lower = question.lower()
        
        # Common subject mappings
        subject_keywords = {
            # Languages
            'tiếng nhật': 'JP',
            'tiếng anh': 'ENG',
            'japanese': 'JP',
            'english': 'ENG',
            
            # Common subjects
            'lập trình mạng': 'IT3170',
            'cơ sở dữ liệu': 'IT3080',
            'toán': 'MI',
            'vật lý': 'PH',
            'hóa học': 'CH',
            'sinh học': 'BI',
            'triết học': 'PHI',
            'chủ nghĩa xã hội': 'SSH',
            
            # Generic patterns
            'cnxh': 'SSH',
            'xã hội': 'SSH',
        }
        
        # Try to match keywords
        for keyword, subject_prefix in subject_keywords.items():
            if keyword in question_lower:
                # If user mentions this subject, find it in recommended subjects
                return subject_prefix
        
        # Try to extract subject code pattern (e.g., IT3170, SSH1131, JP2126)
        import re
        # Pattern: Letters followed by numbers
        pattern = r'\b([A-Z]{2,4}\d{3,4})\b'
        match = re.search(pattern, question.upper())
        if match:
            return match.group(1)
        
        return None
    
    def _format_class_suggestions(
        self,
        classes: List[Dict],
        subjects: List[Dict],
        subject_result: Dict
    ) -> str:
        """
        Format class suggestions into human-readable text
        
        Args:
            classes: List of available classes
            subjects: List of suggested subjects
            subject_result: Result from rule engine
        
        Returns:
            Formatted text response
        """
        response = []
        
        # Header
        response.append("🏫 GỢI Ý LỚP HỌC THÔNG MINH")
        response.append("=" * 60)
        
        # Student info
        response.append(f"\n📊 Thông tin sinh viên:")
        response.append(f"  • Kỳ học: {subject_result['current_semester']}")
        response.append(f"  • CPA: {subject_result['student_cpa']:.2f}")
        
        # Show applied preferences if any
        has_preferences = False
        for cls in classes:
            if cls.get('violation_count', 0) >= 0:
                has_preferences = True
                break
        
        if has_preferences:
            response.append(f"\n⚙️ Đã áp dụng bộ lọc thông minh:")
            fully_satisfied = len([c for c in classes if c.get('fully_satisfies', False)])
            with_violations = len([c for c in classes if not c.get('fully_satisfies', False)])
            response.append(f"  • Lớp thỏa mãn hoàn toàn: {fully_satisfied} lớp ✅")
            if with_violations > 0:
                response.append(f"  • Lớp có vi phạm tiêu chí: {with_violations} lớp ⚠️")
        
        if not classes:
            response.append("\n⚠️ Hiện tại không có lớp nào khả dụng cho các môn được gợi ý.")
            response.append("\nCác môn được gợi ý:")
            for subj in subjects:
                response.append(f"  • {subj['subject_id']} - {subj['subject_name']}")
            return "\n".join(response)
        
        # Group classes by subject
        classes_by_subject = {}
        for cls in classes:
            subject_id = cls['subject_id']
            if subject_id not in classes_by_subject:
                classes_by_subject[subject_id] = []
            classes_by_subject[subject_id].append(cls)
        
        # Display classes grouped by subject
        response.append(f"\n📚 Tìm thấy {len(classes)} lớp cho {len(classes_by_subject)} môn:\n")
        
        for idx, (subject_id, subject_classes) in enumerate(classes_by_subject.items(), 1):
            first_class = subject_classes[0]
            priority_reason = first_class.get('priority_reason', '')
            
            response.append(f"{idx}. {subject_id} - {first_class['subject_name']} ({first_class['credits']} TC)")
            if priority_reason:
                response.append(f"   💡 {priority_reason}")
            response.append(f"   Có {len(subject_classes)} lớp khả dụng:")
            
            for cls in subject_classes[:3]:  # Show max 3 classes per subject
                time_info = ""
                if cls['study_time_start'] and cls['study_time_end']:
                    time_info = f"{cls['study_time_start']}-{cls['study_time_end']}"
                
                # Add satisfaction badge
                fully_satisfied = cls.get('fully_satisfies', False)
                violation_count = cls.get('violation_count', 0)
                badge = "✅" if fully_satisfied else (f"⚠️" if violation_count > 0 else "")
                
                class_line = f"     • {cls['class_id']}: {cls['study_date']} {time_info} "
                class_line += f"- Phòng {cls['classroom']} - GV: {cls['teacher_name']} "
                class_line += f"({cls['seats_available']} chỗ trống) {badge}"
                
                response.append(class_line)
                
                # Show violations if any
                if violation_count > 0 and cls.get('violations'):
                    violations_str = ', '.join(cls['violations'][:2])
                    response.append(f"       ⚠️ {violations_str}")
            
            if len(subject_classes) > 3:
                response.append(f"     ... và {len(subject_classes) - 3} lớp khác")
            
            response.append("")
        
        response.append("💡 Ghi chú:")
        response.append("   ✅ = Thỏa mãn hoàn toàn tiêu chí")
        response.append("   ⚠️ = Có vi phạm tiêu chí nhưng vẫn khả dụng")
        
        return "\n".join(response)
