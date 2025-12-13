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
        Process class suggestion request with interactive preference collection
        
        This method is ONLY called when intent = "class_registration_suggestion"
        
        NEW FLOW:
        1. Check if there's an active conversation state
        2. If yes, parse user response and update preferences
        3. If preferences incomplete, ask next question
        4. If preferences complete, generate class suggestions (3-5 per subject)
        
        Args:
            student_id: Student ID
            question: User's question (used for preference extraction)
            subject_id: Optional specific subject ID to filter
        
        Returns:
            Dict with text response and class suggestions OR next question
        """
        try:
            from app.services.conversation_state import get_conversation_manager
            from app.services.preference_service import PreferenceCollectionService
            
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
            
            # Initialize services
            conv_manager = get_conversation_manager()
            pref_service = PreferenceCollectionService()
            
            # Check for active conversation
            state = conv_manager.get_state(student_id)
            
            if state and state.stage == 'collecting':
                # User is answering a preference question
                print(f"🔄 [CONVERSATION] Continuing conversation for student {student_id}")
                print(f"📋 [CONVERSATION] Current question: {state.current_question.key if state.current_question else None}")
                
                # Parse user response
                if state.current_question:
                    state.preferences = pref_service.parse_user_response(
                        response=question,
                        question_key=state.current_question.key,
                        current_preferences=state.preferences
                    )
                    state.questions_asked.append(state.current_question.key)
                    print(f"✅ [CONVERSATION] Updated preferences: {state.preferences.dict()}")
                
                # Check if preferences are complete
                if state.preferences.is_complete():
                    print(f"✨ [CONVERSATION] Preferences complete! Generating suggestions...")
                    state.stage = 'completed'
                    conv_manager.save_state(state)
                    
                    # Generate class suggestions
                    return await self._generate_class_suggestions_with_preferences(
                        student_id=student_id,
                        preferences=state.preferences,
                        subject_id=subject_id
                    )
                else:
                    # Ask next question
                    next_question = pref_service.get_next_question(state.preferences)
                    state.current_question = next_question
                    conv_manager.save_state(state)
                    
                    return {
                        "text": next_question.question,
                        "intent": "class_registration_suggestion",
                        "confidence": "high",
                        "data": None,
                        "conversation_state": "collecting",
                        "question_type": next_question.type,
                        "question_options": next_question.options
                    }
            
            else:
                # New conversation - extract initial preferences
                print(f"🆕 [CONVERSATION] Starting new preference collection")
                
                initial_preferences = pref_service.extract_initial_preferences(question)
                print(f"⚙️ [INITIAL] Extracted preferences: {initial_preferences.dict()}")
                
                # Create new conversation state
                from app.services.conversation_state import ConversationState
                import uuid
                state = ConversationState(
                    student_id=student_id,
                    session_id=str(uuid.uuid4()),
                    intent='class_registration_suggestion'
                )
                state.preferences = initial_preferences
                
                # Check if preferences are already complete
                if state.preferences.is_complete():
                    print(f"✨ [INITIAL] Preferences already complete from initial question!")
                    state.stage = 'completed'
                    conv_manager.save_state(state)
                    
                    # Generate class suggestions immediately
                    return await self._generate_class_suggestions_with_preferences(
                        student_id=student_id,
                        preferences=state.preferences,
                        subject_id=subject_id
                    )
                else:
                    # Start collecting missing preferences
                    state.stage = 'collecting'
                    next_question = pref_service.get_next_question(state.preferences)
                    state.current_question = next_question
                    conv_manager.save_state(state)
                    
                    # Show what we extracted + ask first question
                    extracted_summary = ""
                    if any([
                        initial_preferences.day.prefer_days,
                        initial_preferences.day.avoid_days,
                        initial_preferences.time.time_period,
                        initial_preferences.time.avoid_time_periods
                    ]):
                        extracted_summary = f"\n\n✅ Tôi đã hiểu một số sở thích từ câu hỏi của bạn:\n{pref_service.format_preference_summary(initial_preferences)}\n"
                    
                    return {
                        "text": f"Để gợi ý chính xác nhất, tôi cần biết thêm về sở thích của bạn.{extracted_summary}\n{next_question.question}",
                        "intent": "class_registration_suggestion",
                        "confidence": "high",
                        "data": None,
                        "conversation_state": "collecting",
                        "question_type": next_question.type,
                        "question_options": next_question.options
                    }
        
        except Exception as e:
            print(f"❌ [CLASS_SUGGESTION] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "text": f"⚠️ Có lỗi xảy ra: {str(e)}",
                "intent": "class_registration_suggestion",
                "confidence": "high",
                "data": None
            }
    
    async def _generate_class_suggestions_with_preferences(
        self,
        student_id: int,
        preferences,
        subject_id: Optional[str] = None
    ) -> Dict:
        """
        Generate class suggestions with collected preferences
        Return 3-5 classes per subject
        """
        try:
            from app.services.preference_service import PreferenceCollectionService
            pref_service = PreferenceCollectionService()
            
            print(f"🎯 [GENERATING] Creating suggestions with preferences")
            print(f"📋 [PREFERENCES] {preferences.dict()}")
            
            # Convert preferences to dict for rule engine
            preferences_dict = preferences.to_dict()
            print(f"⚙️ [CLASS_SUGGESTION] Preferences dict: {preferences_dict}")
            
            # First, get subject suggestions from rule engine
            subject_result = self.subject_rule_engine.suggest_subjects(student_id)
            
            # Get list of suggested subjects
            suggested_subjects = subject_result['suggested_subjects']
            print(f"📊 [SUBJECT_SUGGESTION] Total subjects from rule engine: {len(suggested_subjects)}")
            print(f"📊 [SUBJECT_SUGGESTION] Total credits: {subject_result.get('total_credits', 0)}")
            print(f"📊 [SUBJECT_SUGGESTION] Max credits allowed: {subject_result.get('max_credits_allowed', 0)}")
            
            # Filter by subject_id if provided
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
            # NOTE: Không limit số môn, sử dụng tất cả môn mà rule engine gợi ý
            # để đảm bảo đủ số tín chỉ theo max_credits_allowed
            
            total_suggested_credits = sum(subj.get('credits', 0) for subj in suggested_subjects)
            print(f"📚 [CLASS_SUGGESTION] Using {len(suggested_subjects)} subjects ({total_suggested_credits} credits)")
            
            # Get subject IDs
            subject_ids = [subj['id'] for subj in suggested_subjects]
            
            # NEW: Get 3-5 classes per subject for combination generation
            classes_by_subject = {}
            
            # Import preference filter for early pruning
            from app.services.preference_filter import PreferenceFilter
            pref_filter = PreferenceFilter()
            
            for subj in suggested_subjects:
                # Get classes for this specific subject
                subject_classes = self.class_rule_engine.suggest_classes(
                    student_id=student_id,
                    subject_ids=[subj['id']],
                    preferences=preferences_dict,
                    registered_classes=[],
                    min_suggestions=3  # Get at least 3 classes
                )
                
                # Apply preference filter BEFORE combination (Early Pruning Optimization)
                all_classes = subject_classes['suggested_classes']
                print(f"📚 [SUBJECT {subj['subject_id']}] Got {len(all_classes)} classes before filtering")
                
                # Filter by preferences to reduce combination space
                filtered_classes = pref_filter.filter_by_preferences(
                    classes=all_classes,
                    preferences=preferences_dict,
                    strict=False  # Soft filter to keep some diversity
                )
                
                # Take top 3-5 classes after filtering
                subject_suggested = filtered_classes[:5]
                print(f"  ✅ After preference filter: {len(subject_suggested)} classes")
                
                # Get filter statistics
                if len(all_classes) > 0:
                    stats = pref_filter.get_filter_stats(len(all_classes), len(filtered_classes))
                    print(f"  📊 Filter efficiency: {stats['efficiency_gain']}")
                
                # Store by subject_id for combination generation
                classes_by_subject[subj['subject_id']] = subject_suggested
            
            # Generate schedule combinations
            from app.services.schedule_combination_service import ScheduleCombinationGenerator
            combo_generator = ScheduleCombinationGenerator()
            
            print(f"🔄 [COMBINATIONS] Generating schedule combinations...")
            combinations = combo_generator.generate_combinations(
                classes_by_subject=classes_by_subject,
                preferences=preferences_dict,
                max_combinations=100
            )
            
            # Return top 3 combinations
            top_combinations = combinations[:3]
            print(f"✅ [COMBINATIONS] Returning top {len(top_combinations)} combinations")
            
            # Add priority reasons from subject suggestions
            subject_reasons = {subj['subject_id']: subj.get('priority_reason', '') 
                              for subj in suggested_subjects}
            
            # Format combinations for response
            formatted_combinations = []
            
            for idx, combo in enumerate(top_combinations, 1):
                formatted_classes = []
                
                for cls in combo['classes']:
                    formatted_classes.append({
                        "class_id": cls['class_id'],
                        "class_name": cls['class_name'],
                        "classroom": cls['classroom'],
                        "study_date": cls['study_date'],
                        "study_week": cls.get('study_week', []),  # Add study_week field
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
                    })
                
                formatted_combinations.append({
                    "combination_id": idx,
                    "score": combo['score'],
                    "recommended": idx == 1,  # First is recommended
                    "classes": formatted_classes,
                    "metrics": combo['metrics']
                })
            
            # Format response text with combinations
            preference_summary = pref_service.format_preference_summary(preferences)
            text_response = self._format_schedule_combinations(
                formatted_combinations,
                suggested_subjects,
                subject_result,
                preference_summary
            )
            
            # Clear conversation state after generating suggestions
            from app.services.conversation_state import get_conversation_manager
            get_conversation_manager().delete_state(student_id)
            
            return {
                "text": text_response,
                "intent": "class_registration_suggestion",
                "confidence": "high",
                "data": formatted_combinations,
                "metadata": {
                    "total_subjects": len(suggested_subjects),
                    "total_combinations": len(top_combinations),
                    "student_cpa": subject_result['student_cpa'],
                    "current_semester": subject_result['current_semester'],
                    "preferences_applied": preferences_dict
                },
                "rule_engine_used": True,
                "conversation_state": "completed"
            }
            
        except Exception as e:
            print(f"❌ [GENERATING] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "text": f"❌ Xin lỗi, đã xảy ra lỗi khi gợi ý lớp học: {str(e)}",
                "intent": "class_registration_suggestion",
                "confidence": "low",
                "data": None,
                "error": str(e)
            }
    
    def _extract_preferences_from_question(self, question: str) -> Dict:
        """
        Extract class preferences from user's question with context-aware negation handling
        
        Args:
            question: User's question
        
        Returns:
            Dict with preferences
        """
        import re
        
        question_lower = question.lower()
        preferences = {}
        
        # Helper function to check if a pattern has negation before it
        def has_negation_before(text: str, pattern: str, max_distance: int = 20) -> bool:
            """Check if pattern is preceded by negation words within max_distance characters"""
            pattern_pos = text.find(pattern)
            if pattern_pos == -1:
                return False
            
            # Look back for negation words
            start_pos = max(0, pattern_pos - max_distance)
            preceding_text = text[start_pos:pattern_pos]
            
            negation_words = ['không', 'tránh', 'chẳng', 'không muốn', 'ko']
            return any(neg in preceding_text for neg in negation_words)
        
        # ========== TIME PERIOD PREFERENCES ==========
        # Check for NEGATIVE time preferences first (more specific)
        # "không muốn học buổi sáng" → Find afternoon classes
        
        avoid_time_periods = []
        
        # Morning - check for negation
        morning_patterns = ['sáng', 'buổi sáng', 'morning']
        for pattern in morning_patterns:
            if pattern in question_lower:
                if has_negation_before(question_lower, pattern):
                    # "không muốn học buổi sáng" → avoid morning, prefer afternoon
                    avoid_time_periods.append('morning')
                    break
                else:
                    # "muốn học buổi sáng" → prefer morning
                    preferences['time_period'] = 'morning'
                    break
        
        # Afternoon
        afternoon_patterns = ['chiều', 'buổi chiều', 'afternoon']
        if not preferences.get('time_period'):
            for pattern in afternoon_patterns:
                if pattern in question_lower:
                    if has_negation_before(question_lower, pattern):
                        avoid_time_periods.append('afternoon')
                        break
                    else:
                        preferences['time_period'] = 'afternoon'
                        break
        
        
        
        # If user avoids certain time periods, we need to handle this in filtering
        # Store as a separate field so ClassSuggestionRuleEngine can filter properly
        if avoid_time_periods:
            preferences['avoid_time_periods'] = avoid_time_periods
        
        # ========== AVOID EARLY/LATE ==========
        # Avoid early start
        if any(phrase in question_lower for phrase in [
            'không muốn học sớm', 'tránh học sớm', 'không học sớm',
            'không sớm', 'tránh sớm'
        ]):
            preferences['avoid_early_start'] = True
        
        # Avoid late end
        if any(phrase in question_lower for phrase in [
            'không muốn học muộn', 'tránh học muộn', 'không học muộn',
            'không muốn học đến', 'kết thúc sớm', 'tan sớm',
            'không học đến 17', 'không học đến 18', 'không học đến 19',
            'không học buổi tối', 'không học tối'
        ]):
            preferences['avoid_late_end'] = True
        
        # ========== WEEKDAY PREFERENCES ==========
        # Define day mappings
        day_mappings = {
            'thứ 2': 'Monday',
            'thứ hai': 'Monday',
            't2': 'Monday',
            'thứ 3': 'Tuesday',
            'thứ ba': 'Tuesday',
            't3': 'Tuesday',
            'thứ 4': 'Wednesday',
            'thứ tư': 'Wednesday',
            't4': 'Wednesday',
            'thứ 5': 'Thursday',
            'thứ năm': 'Thursday',
            't5': 'Thursday',
            'thứ 6': 'Friday',
            'thứ sáu': 'Friday',
            't6': 'Friday',
            'thứ 7': 'Saturday',
            'thứ bảy': 'Saturday',
            't7': 'Saturday',
            'chủ nhật': 'Sunday',
            'cn': 'Sunday'
        }
        
        prefer_days = []
        avoid_days = []
        
        for day_pattern, english_day in day_mappings.items():
            if day_pattern in question_lower:
                # Check context around this day mention
                # Look for positive indicators
                positive_contexts = [
                    f'học vào {day_pattern}',
                    f'vào {day_pattern}',
                    f'học {day_pattern}',
                    f'muốn {day_pattern}',
                    f'{day_pattern}'  # Just mentioning the day
                ]
                
                # Look for negative indicators (more specific first)
                negative_contexts = [
                    f'không học {day_pattern}',
                    f'tránh {day_pattern}',
                    f'không {day_pattern}',
                    f'ko {day_pattern}',
                    f'không muốn học {day_pattern}',
                    f'không muốn {day_pattern}'
                ]
                
                # Check negative first (more specific)
                is_negative = any(neg_ctx in question_lower for neg_ctx in negative_contexts)
                
                if is_negative:
                    avoid_days.append(english_day)
                else:
                    # Check if it's in a positive context
                    is_positive = any(pos_ctx in question_lower for pos_ctx in positive_contexts)
                    if is_positive:
                        prefer_days.append(english_day)
        
        if prefer_days:
            preferences['prefer_days'] = list(set(prefer_days))  # Remove duplicates
        
        if avoid_days:
            preferences['avoid_days'] = list(set(avoid_days))  # Remove duplicates
        
        # ========== CONTINUOUS CLASSES ==========
        if any(phrase in question_lower for phrase in ['học liên tục', 'liên tục', 'học dồn']):
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
    
    def _format_class_suggestions_with_preferences(
        self,
        classes: List[Dict],
        subjects: List[Dict],
        subject_result: Dict,
        preference_summary: str
    ) -> str:
        """
        Format class suggestions with preference summary
        
        Args:
            classes: List of available classes (3-5 per subject)
            subjects: List of suggested subjects
            subject_result: Result from rule engine
            preference_summary: Formatted preference summary
        
        Returns:
            Formatted text response with preferences
        """
        response = []
        
        # Header
        response.append("🎯 GỢI Ý LỚP HỌC THÔNG MINH")
        response.append("=" * 60)
        
        # Student info
        response.append(f"\n📊 Thông tin sinh viên:")
        response.append(f"  • Kỳ học: {subject_result['current_semester']}")
        response.append(f"  • CPA: {subject_result['student_cpa']:.2f}")
        
        # Show collected preferences
        response.append(f"\n{preference_summary}")
        
        if not classes:
            response.append("\n⚠️ Hiện tại không có lớp nào thỏa mãn tất cả tiêu chí của bạn.")
            response.append("\nCác môn được gợi ý:")
            for subj in subjects:
                response.append(f"  • {subj['subject_id']} - {subj['subject_name']}")
            return "\n".join(response)
        
        # Group classes by subject
        classes_by_subject = {}
        for cls in classes:
            subj_id = cls['subject_id']
            if subj_id not in classes_by_subject:
                classes_by_subject[subj_id] = []
            classes_by_subject[subj_id].append(cls)
        
        response.append(f"\n📚 Tìm thấy {len(classes)} lớp từ {len(classes_by_subject)} môn:")
        response.append("")
        
        # Show classes grouped by subject
        for idx, subj in enumerate(subjects, 1):
            subj_id = subj['subject_id']
            subj_classes = classes_by_subject.get(subj_id, [])
            
            if not subj_classes:
                continue
            
            response.append(f"{idx}. {subj_id} - {subj['subject_name']} ({subj['credits']} TC)")
            if subj.get('priority_reason'):
                response.append(f"   💡 {subj['priority_reason']}")
            
            response.append(f"   Có {len(subj_classes)} lớp phù hợp:")
            
            for cls in subj_classes:
                badge = "✅" if cls.get('fully_satisfies', False) else "⚠️"
                response.append(f"   {badge} {cls['class_id']}: {cls['study_date']} {cls['study_time_start']}-{cls['study_time_end']}")
                response.append(f"      📍 Phòng {cls['classroom']} - {cls['teacher_name'] if cls['teacher_name'] else 'Chưa có GV'}")
                response.append(f"      👥 {cls['seats_available']} chỗ trống / {cls['max_students']}")
                
                # Show violations if any
                if cls.get('violations'):
                    for violation in cls['violations']:
                        response.append(f"      ⚠️ {violation}")
            
            response.append("")
        
        response.append("💡 Ghi chú:")
        response.append("   ✅ = Thỏa mãn hoàn toàn tiêu chí")
        response.append("   ⚠️ = Có vi phạm tiêu chí nhưng vẫn khả dụng")
        
        return "\n".join(response)
    
    def _format_schedule_combinations(
        self,
        combinations: List[Dict],
        subjects: List[Dict],
        subject_result: Dict,
        preference_summary: str
    ) -> str:
        """
        Format schedule combinations with metrics and recommendations
        
        Args:
            combinations: List of schedule combinations
            subjects: List of suggested subjects
            subject_result: Result from rule engine
            preference_summary: Formatted preference summary
        
        Returns:
            Formatted text response
        """
        response = []
        
        # Header
        response.append("🎯 GỢI Ý LỊCH HỌC THÔNG MINH")
        response.append("=" * 60)
        
        # Student info
        response.append(f"\n📊 Thông tin sinh viên:")
        response.append(f"  • Kỳ học: {subject_result['current_semester']}")
        response.append(f"  • CPA: {subject_result['student_cpa']:.2f}")
        
        # Show collected preferences
        response.append(f"\n{preference_summary}")
        
        if not combinations:
            response.append("\n⚠️ Không tìm thấy lịch học nào thỏa mãn tất cả tiêu chí.")
            response.append("Vui lòng thử lại với tiêu chí linh hoạt hơn.")
            return "\n".join(response)
        
        response.append(f"\n✨ Đã tạo {len(combinations)} phương án lịch học tối ưu:\n")
        
        # Show each combination
        for combo in combinations:
            badge = "🔵" if combo['combination_id'] == 1 else "🟢" if combo['combination_id'] == 2 else "🟡"
            recommended = " ⭐ KHUYÊN DÙNG" if combo['recommended'] else ""
            
            response.append(f"{badge} PHƯƠNG ÁN {combo['combination_id']} (Điểm: {combo['score']:.0f}/100){recommended}")
            
            # Metrics
            m = combo['metrics']
            response.append(f"  📊 Tổng quan:")
            response.append(f"    • {m['total_classes']} môn học - {m['total_credits']} tín chỉ")
            response.append(f"    • Học {m['study_days']} ngày/tuần (Nghỉ {m['free_days']} ngày)")
            response.append(f"    • Trung bình {m['average_daily_hours']:.1f} giờ/ngày")
            if m.get('earliest_start') and m.get('latest_end'):
                response.append(f"    • Giờ học: {m['earliest_start']} - {m['latest_end']}")
            if m['continuous_study_days'] > 0:
                response.append(f"    • {m['continuous_study_days']} ngày học liên tục (>5h)")
            
            response.append(f"\n  📚 Danh sách lớp:")
            
            # Group by subject for display
            for cls in combo['classes']:
                response.append(f"    • {cls['subject_id']} - {cls['subject_name']} ({cls['credits']} TC)")
                response.append(f"      📍 Lớp {cls['class_id']}: {cls['study_date']} {cls['study_time_start']}-{cls['study_time_end']}")
                response.append(f"      🏫 Phòng {cls['classroom']} - {cls['teacher_name'] if cls['teacher_name'] else 'TBA'}")
                response.append(f"      👥 {cls['seats_available']}/{cls['max_students']} chỗ trống")
                
                if cls.get('priority_reason'):
                    response.append(f"      💡 {cls['priority_reason']}")
            
            response.append("")
        
        response.append("💡 Lưu ý:")
        response.append("  • ⭐ = Phương án được khuyên dùng nhất")
        response.append("  • Tất cả phương án đều KHÔNG XUNG ĐỘT thời gian")
        response.append("  • Mỗi môn chỉ có 1 lớp trong phương án")
        
        return "\n".join(response)
    
    def _format_class_suggestions(
        self,
        classes: List[Dict],
        subjects: List[Dict],
        subject_result: Dict
    ) -> str:
        """
        Format class suggestions into human-readable text (legacy method)
        
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
