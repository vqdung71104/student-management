"""
Chatbot Service - Business logic for chatbot interactions
Integrates Rule Engine for intelligent subject/class suggestions
"""
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.rules.subject_suggestion_rules import SubjectSuggestionRuleEngine


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
        self.rule_engine = SubjectSuggestionRuleEngine(db)
    
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
            
            # Run rule engine to get suggestions
            result = self.rule_engine.suggest_subjects(
                student_id=student_id,
                max_credits=max_credits
            )
            
            # Format human-readable response
            text_response = self.rule_engine.format_suggestion_response(result)
            
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
        Process class suggestion request
        Suggests classes for recommended subjects or a specific subject
        
        Args:
            student_id: Student ID
            question: User's question
            subject_id: Optional specific subject ID to filter
        
        Returns:
            Dict with text response and class suggestions
        """
        try:
            # Validate student_id
            if not student_id:
                return {
                    "text": "⚠️ Vui lòng đăng nhập để nhận gợi ý đăng ký lớp học.",
                    "intent": "class_registration_suggestion",
                    "confidence": "high",
                    "data": None,
                    "requires_auth": True
                }
            
            # First, get subject suggestions from rule engine
            subject_result = self.rule_engine.suggest_subjects(student_id)
            
            # Get list of suggested subjects
            suggested_subjects = subject_result['suggested_subjects']
            
            # Filter by subject_id if provided
            if subject_id:
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
            else:
                # Limit to top 5 subjects
                suggested_subjects = suggested_subjects[:5]
            
            # Query available classes for these subjects
            from sqlalchemy import text
            
            classes = []
            for subject in suggested_subjects:
                class_query = """
                    SELECT 
                        c.id,
                        c.class_id,
                        c.class_name,
                        c.classroom,
                        c.study_date,
                        c.study_time_start,
                        c.study_time_end,
                        c.teacher_name,
                        s.subject_id,
                        s.subject_name,
                        s.credits,
                        COUNT(cr.student_id) as registered_students,
                        c.max_student_number
                    FROM classes c
                    JOIN subjects s ON c.subject_id = s.id
                    LEFT JOIN class_registers cr ON c.id = cr.class_id
                    WHERE s.id = :subject_db_id
                    GROUP BY c.id, c.class_id, c.class_name, c.classroom, 
                             c.study_date, c.study_time_start, c.study_time_end,
                             c.teacher_name, s.subject_id, s.subject_name, s.credits,
                             c.max_student_number
                    HAVING COUNT(cr.student_id) < c.max_student_number
                    ORDER BY c.class_id
                """
                
                result = self.db.execute(
                    text(class_query),
                    {"subject_db_id": subject['id']}
                )
                
                class_rows = result.fetchall()
                
                for row in class_rows:
                    classes.append({
                        "class_id": row[1],
                        "class_name": row[2],
                        "classroom": row[3],
                        "study_date": row[4],
                        "study_time_start": str(row[5]) if row[5] else None,
                        "study_time_end": str(row[6]) if row[6] else None,
                        "teacher_name": row[7],
                        "subject_id": row[8],
                        "subject_name": row[9],
                        "credits": row[10],
                        "registered_students": row[11],
                        "max_students": row[12],
                        "seats_available": row[12] - row[11],
                        "priority_reason": subject.get('priority_reason', '')
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
        response.append("🏫 GỢI Ý LỚP HỌC")
        response.append("=" * 60)
        
        # Student info
        response.append(f"\n📊 Thông tin:")
        response.append(f"  • Kỳ học: {subject_result['current_semester']}")
        response.append(f"  • CPA: {subject_result['student_cpa']:.2f}")
        
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
                
                response.append(
                    f"     • {cls['class_id']}: {cls['study_date']} {time_info} "
                    f"- Phòng {cls['classroom']} - GV: {cls['teacher_name']} "
                    f"({cls['seats_available']} chỗ trống)"
                )
            
            if len(subject_classes) > 3:
                response.append(f"     ... và {len(subject_classes) - 3} lớp khác")
            
            response.append("")
        
        response.append("💡 Tip: Chọn lớp phù hợp với thời khóa biểu của bạn!")
        
        return "\n".join(response)
