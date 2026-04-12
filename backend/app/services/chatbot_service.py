"""
Chatbot Service - Business logic for chatbot interactions
Integrates Rule Engine for intelligent subject/class suggestions
"""
from typing import Dict, List, Optional, Tuple
import re
from datetime import time as dtime, timedelta
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

        # FuzzyMatcher — dùng để resolve tên môn khi user gõ sai / thiếu dấu
        try:
            from app.services.fuzzy_matcher import FuzzyMatcher
            self._fuzzy_matcher = FuzzyMatcher(db)
            print(f"✅ [ChatbotService] FuzzyMatcher loaded: {self._fuzzy_matcher.subject_count} subjects")
        except Exception as e:
            print(f"⚠️ [ChatbotService] FuzzyMatcher not available: {e}")
            self._fuzzy_matcher = None

    def _has_class_data(self) -> bool:
        from app.models.class_model import Class
        return self.db.query(Class.id).first() is not None

    def _class_data_notice_text(self) -> str:
        return "⚠️ Hiện tại chưa có thông tin lớp học trong hệ thống."

    def _source_selection_question_text(self) -> str:
        return "Bạn muốn đăng ký theo học phần bạn đã đăng ký hay học phần hệ thống gợi ý?"

    def _normalize_subject_source_choice(self, value: Optional[str]) -> str:
        """Return canonical subject source and never None for response metadata."""
        if value in {"registered", "suggested"}:
            return value
        return "suggested"

    def _parse_subject_source_choice(self, answer: str) -> Optional[str]:
        txt = (answer or "").lower().strip()

        registered_patterns = [
            "đã đăng ký", "da dang ky", "hoc phan da dang ky", "1", "đăng ký rồi", "dang ky roi"
        ]
        suggested_patterns = [
            "gợi ý", "goi y", "hệ thống", "he thong", "2", "đề xuất", "de xuat"
        ]

        if any(p in txt for p in registered_patterns):
            return "registered"
        if any(p in txt for p in suggested_patterns):
            return "suggested"
        return None

    def _append_supplemental_keys(self, state, keys: List[str]):
        if not keys:
            return
        existing = set(getattr(state, 'supplemental_preference_keys', []) or [])
        for key in keys:
            if key not in existing:
                existing.add(key)
        state.supplemental_preference_keys = sorted(existing)

    def _friendly_preference_label(self, key: str) -> str:
        labels = {
            'day': 'Ngày học',
            'time': 'Thời gian học',
            'continuous': 'Học liên tục',
            'free_days': 'Ngày nghỉ',
            'specific': 'Yêu cầu cụ thể',
        }
        return labels.get(key, key)

    def _friendly_question_hint(self, key: str) -> str:
        hints = {
            'day': 'Ví dụ: Thứ 2, Thứ 4, Thứ 6',
            'time': 'Ví dụ: Học sớm, học muộn, hoặc không quan trọng',
            'continuous': 'Ví dụ: Có, không, hoặc không quan trọng',
            'free_days': 'Ví dụ: Muốn nghỉ nhiều ngày hơn hoặc không quan trọng',
            'specific': 'Ví dụ: Giáo viên yêu thích, mã lớp cụ thể, hoặc trả lời không',
        }
        return hints.get(key, '')

    def _build_preference_snapshot(self, preferences) -> List[Dict]:
        snapshot: List[Dict] = []

        if preferences.day.prefer_days or preferences.day.avoid_days or preferences.day.is_not_important:
            day_value = []
            if preferences.day.prefer_days:
                day_value.append(f"Ưu tiên: {', '.join(preferences.day.prefer_days)}")
            if preferences.day.avoid_days:
                day_value.append(f"Tránh: {', '.join(preferences.day.avoid_days)}")
            if preferences.day.is_not_important:
                day_value.append('Không quan trọng')
            snapshot.append({
                'key': 'day',
                'label': self._friendly_preference_label('day'),
                'value': '; '.join(day_value) if day_value else 'Đã ghi nhận',
                'status': 'đã có thông tin',
            })

        if (
            preferences.time.time_period
            or preferences.time.avoid_time_periods
            or preferences.time.prefer_early_start
            or preferences.time.prefer_late_start
            or preferences.time.avoid_early_start
            or preferences.time.avoid_late_end
            or preferences.time.is_not_important
        ):
            time_value = []
            if preferences.time.time_period:
                time_value.append('Buổi sáng' if preferences.time.time_period == 'morning' else 'Buổi chiều')
            if preferences.time.avoid_time_periods:
                avoided = ['Buổi sáng' if period == 'morning' else 'Buổi chiều' for period in preferences.time.avoid_time_periods]
                time_value.append(f"Tránh: {', '.join(avoided)}")
            if preferences.time.prefer_early_start:
                time_value.append('Ưu tiên học sớm')
            if preferences.time.prefer_late_start:
                time_value.append('Ưu tiên học muộn')
            if preferences.time.is_not_important:
                time_value.append('Không quan trọng')
            snapshot.append({
                'key': 'time',
                'label': self._friendly_preference_label('time'),
                'value': '; '.join(time_value) if time_value else 'Đã ghi nhận',
                'status': 'đã có thông tin',
            })

        if preferences.continuous.has_answer or preferences.continuous.prefer_continuous or preferences.continuous.is_not_important:
            if preferences.continuous.is_not_important:
                continuous_value = 'Không quan trọng'
            elif preferences.continuous.prefer_continuous:
                continuous_value = 'Ưu tiên học liên tục'
            else:
                continuous_value = 'Không muốn học liên tục'
            snapshot.append({
                'key': 'continuous',
                'label': self._friendly_preference_label('continuous'),
                'value': continuous_value,
                'status': 'đã có thông tin',
            })

        if preferences.free_days.has_answer or preferences.free_days.prefer_free_days or preferences.free_days.is_not_important:
            if preferences.free_days.is_not_important:
                free_days_value = 'Không quan trọng'
            elif preferences.free_days.prefer_free_days:
                free_days_value = 'Ưu tiên nghỉ nhiều ngày hơn'
            else:
                free_days_value = 'Không ưu tiên nghỉ nhiều ngày'
            snapshot.append({
                'key': 'free_days',
                'label': self._friendly_preference_label('free_days'),
                'value': free_days_value,
                'status': 'đã có thông tin',
            })

        if preferences.specific.has_answer or preferences.specific.preferred_teachers or getattr(preferences.specific, 'specific_subjects', None) or preferences.specific.specific_class_ids or preferences.specific.specific_times:
            specific_parts = []
            if preferences.specific.preferred_teachers:
                specific_parts.append(f"Giáo viên: {', '.join(preferences.specific.preferred_teachers)}")
            if getattr(preferences.specific, 'specific_subjects', None):
                specific_parts.append(f"Học phần: {', '.join(preferences.specific.specific_subjects)}")
            if preferences.specific.specific_class_ids:
                specific_parts.append(f"Mã lớp: {', '.join(preferences.specific.specific_class_ids)}")
            if preferences.specific.specific_times:
                specific_parts.append('Có yêu cầu thời gian cụ thể')
            if not specific_parts:
                specific_parts.append('Không có yêu cầu cụ thể thêm')
            snapshot.append({
                'key': 'specific',
                'label': self._friendly_preference_label('specific'),
                'value': '; '.join(specific_parts),
                'status': 'đã có thông tin',
            })

        return snapshot

    def _build_class_suggestion_metadata(
        self,
        preferences,
        conversation_stage: str,
        current_question: Optional[Dict] = None,
        subject_source: str = 'suggested',
        subject_ids_seed: Optional[List[int]] = None,
        nlq_constraints_dict: Optional[Dict] = None,
        state=None,
        next_step: str = 'ask_next_question',
        message: Optional[str] = None,
    ) -> Dict:
        subject_source_labels = {
            'registered': 'Học phần đã đăng ký',
            'suggested': 'Học phần hệ thống gợi ý',
        }
        missing_keys = preferences.get_missing_preferences()
        missing_items = [
            {
                'key': key,
                'label': self._friendly_preference_label(key),
                'hint': self._friendly_question_hint(key),
            }
            for key in missing_keys
        ]
        captured_items = self._build_preference_snapshot(preferences)

        auto_captured_keys = []
        if state is not None:
            auto_captured_keys = list(getattr(state, 'supplemental_preference_keys', []) or [])

        completed_count = max(0, 5 - len(missing_keys))
        progress_percent = int((completed_count / 5) * 100) if 5 else 0

        metadata = {
            'ui': {
                'title': 'Mình đã nhận được một phần yêu cầu của bạn',
                'subtitle': 'Các thông tin đã có sẽ được giữ lại, phần còn thiếu mình sẽ hỏi tiếp để không làm bạn nhập lại.',
                'status': 'Đang xử lý gợi ý lớp học',
            },
            'conversation': {
                'stage': conversation_stage,
                'next_step': next_step,
                'progress': {
                    'completed': completed_count,
                    'total': 5,
                    'percent': progress_percent,
                },
                'source_choice': subject_source_labels.get(
                    self._normalize_subject_source_choice(subject_source),
                    subject_source_labels['suggested'],
                ),
                'subject_ids_seed_count': len(subject_ids_seed or []),
            },
            'preferences': {
                'captured': captured_items,
                'missing': missing_items,
                'auto_captured_keys': auto_captured_keys,
                'summary': preferences.to_dict(),
            },
            'notes': [
                'Thông tin trong cùng câu trả lời được tự động ghi nhận.',
                'Nếu bạn bổ sung thêm ý mới, hệ thống sẽ cập nhật mà không hỏi lại phần đã có.',
            ],
        }

        if nlq_constraints_dict:
            metadata['conversation']['nlq_constraints'] = {
                'days': nlq_constraints_dict.get('days', []),
                'session': nlq_constraints_dict.get('session'),
                'time_from': nlq_constraints_dict.get('time_from'),
                'subject_codes': nlq_constraints_dict.get('subject_codes', []),
            }

        if current_question:
            metadata['conversation']['current_question'] = {
                'key': current_question.key,
                'label': self._friendly_preference_label(current_question.key),
                'question': current_question.question,
                'options': current_question.options,
                'type': current_question.type,
            }
        elif next_step == 'choose_subject_source':
            metadata['conversation']['current_question'] = {
                'key': 'subject_source',
                'label': 'Nguồn học phần',
                'question': self._source_selection_question_text(),
                'options': ['Học phần đã đăng ký', 'Học phần hệ thống gợi ý'],
                'type': 'single_choice',
            }

        if message:
            metadata['ui']['message'] = message

        return metadata

    def _build_friendly_error_metadata(self, message: str) -> Dict:
        return {
            'ui': {
                'title': 'Mình gặp một lỗi nhỏ khi xử lý yêu cầu',
                'subtitle': 'Bạn có thể thử lại, mình sẽ giữ cách trả lời ngắn gọn và rõ ràng hơn.',
                'status': 'Không thể hoàn tất ngay lúc này',
                'message': message,
            }
        }

    def _merge_constraints_into_preferences(self, preferences, constraints_dict: Optional[Dict]) -> List[str]:
        """Map extracted NL constraints into preference categories to avoid re-asking."""
        if not constraints_dict:
            return []

        captured: List[str] = []
        day_map = {
            'monday': 'Monday',
            'tuesday': 'Tuesday',
            'wednesday': 'Wednesday',
            'thursday': 'Thursday',
            'friday': 'Friday',
            'saturday': 'Saturday',
            'sunday': 'Sunday',
        }

        days = constraints_dict.get('days') or []
        if isinstance(days, list):
            day_changed = False
            for day in days:
                if not day:
                    continue
                normalized = day_map.get(str(day).strip().lower())
                if normalized and normalized not in preferences.day.prefer_days:
                    preferences.day.prefer_days.append(normalized)
                    day_changed = True
            if day_changed:
                preferences.day.has_answer = True
                captured.append('day')

        session = (constraints_dict.get('session') or '').strip().lower()
        if session in ('morning', 'afternoon') and not preferences.time.time_period:
            preferences.time.time_period = session
            preferences.time.has_answer = True
            captured.append('time')

        if constraints_dict.get('time_from') or constraints_dict.get('start_time_exact') or constraints_dict.get('avoid_start_times') or constraints_dict.get('avoid_end_times'):
            preferences.time.has_answer = True
            if 'time' not in captured:
                captured.append('time')

        return captured

    def _is_valid_preference_answer(self, question_key: str, before: Dict, after: Dict, answer: str) -> bool:
        """Check whether a user answer actually updates expected preference fields."""
        normalized_answer = (answer or "").strip().lower()

        if question_key == 'day':
            before_day = before.get('day', {})
            after_day = after.get('day', {})
            return bool(
                after_day.get('prefer_days')
                or after_day.get('avoid_days')
                or after_day.get('is_not_important')
                or after_day.get('has_answer')
                or before_day != after_day
            )

        if question_key == 'time':
            after_time = after.get('time', {})
            return bool(
                after_time.get('time_period')
                or after_time.get('avoid_time_periods')
                or
                after_time.get('prefer_early_start')
                or after_time.get('prefer_late_start')
                or after_time.get('is_not_important')
                or after_time.get('has_answer')
            )

        if question_key == 'continuous':
            after_cont = after.get('continuous', {})
            negative_markers = ['2', 'không', 'ko', 'khong', 'khoảng nghỉ']
            return bool(
                after_cont.get('has_answer')
                or
                after_cont.get('prefer_continuous')
                or after_cont.get('is_not_important')
                or any(marker in normalized_answer for marker in negative_markers)
            )

        if question_key == 'free_days':
            after_free = after.get('free_days', {})
            negative_markers = ['2', 'không', 'ko', 'khong', 'học đều']
            return bool(
                after_free.get('has_answer')
                or
                after_free.get('prefer_free_days')
                or after_free.get('is_not_important')
                or any(marker in normalized_answer for marker in negative_markers)
            )

        if question_key == 'specific':
            after_specific = after.get('specific', {})
            no_specific_markers = [
                'không có yêu cầu',
                'khong co yeu cau',
                'không yêu cầu gì',
                'khong yeu cau gi',
                'không cần yêu cầu',
                'khong can yeu cau',
                'không cần gì thêm',
                'khong can gi them',
            ]
            return bool(
                after_specific.get('preferred_teachers')
                or after_specific.get('specific_subjects')
                or after_specific.get('specific_class_ids')
                or after_specific.get('specific_times')
                or (after_specific.get('has_answer') and any(marker in normalized_answer for marker in no_specific_markers))
            )

        return before != after

    def _build_retry_question_text(self, question_key: str, original_question: str) -> str:
        hints = {
            'day': "Mình chưa đọc được ngày học. Bạn có thể nhập kiểu: 'Thứ 2, Thứ 3, Thứ 4' hoặc 't2,t3,t4'.",
            'time': "Mình chưa hiểu lựa chọn. Bạn trả lời: 1 (học sớm), 2 (học muộn), hoặc 3 (không quan trọng).",
            'continuous': "Bạn trả lời: 1 (có), 2 (không), hoặc 3 (không quan trọng).",
            'free_days': "Bạn trả lời: 1 (có), 2 (không), hoặc 3 (không quan trọng).",
            'specific': "Bạn có thể nêu giáo viên/mã lớp cụ thể, hoặc trả lời 'không'.",
        }
        hint = hints.get(question_key, "Bạn vui lòng trả lời lại theo đúng câu hỏi.")
        return f"{hint}\n\n{original_question}"

    def _is_schedule_advice_query(self, question: str) -> bool:
        txt = (question or "").lower()
        trigger_a = any(k in txt for k in ["thời khóa biểu", "thoi khoa bieu", "lịch học", "lich hoc"])
        trigger_b = any(k in txt for k in ["nên", "nen", "cần", "can"]) and any(
            k in txt for k in ["đăng ký thêm", "dang ky them", "thêm môn", "them mon"]
        )
        return trigger_a and trigger_b

    def _get_registered_subject_ids(self, student_id: int) -> List[int]:
        from app.models.subject_register_model import SubjectRegister
        rows = self.db.query(SubjectRegister.subject_id).filter(SubjectRegister.student_id == student_id).all()
        return list({r[0] for r in rows if r and r[0] is not None})

    def _parse_days(self, study_date: Optional[str]) -> List[str]:
        if not study_date:
            return []
        return [d.strip() for d in study_date.split(',') if d.strip()]

    def _to_time_obj(self, value) -> Optional[dtime]:
        if value is None:
            return None
        if isinstance(value, dtime):
            return value
        if isinstance(value, timedelta):
            total_seconds = int(value.total_seconds())
            hours, rem = divmod(total_seconds, 3600)
            minutes = rem // 60
            if 0 <= hours <= 23:
                return dtime(hours, minutes)
            return None
        if isinstance(value, str):
            parts = value.split(':')
            if len(parts) >= 2:
                try:
                    return dtime(int(parts[0]), int(parts[1]))
                except Exception:
                    return None
        return None

    def _has_time_overlap(self, a_start: Optional[dtime], a_end: Optional[dtime], b_start: Optional[dtime], b_end: Optional[dtime]) -> bool:
        if not a_start or not a_end or not b_start or not b_end:
            return False
        return a_start < b_end and b_start < a_end

    def _has_schedule_overlap(self, a: Dict, b: Dict) -> bool:
        days_a = set(a.get('days', []))
        days_b = set(b.get('days', []))
        if not days_a.intersection(days_b):
            return False

        weeks_a = set(a.get('weeks', []))
        weeks_b = set(b.get('weeks', []))
        if weeks_a and weeks_b and not weeks_a.intersection(weeks_b):
            return False

        return self._has_time_overlap(a.get('start_time'), a.get('end_time'), b.get('start_time'), b.get('end_time'))

    def _grade_ge_b(self, letter_grade: Optional[str]) -> bool:
        if not letter_grade:
            return False
        return letter_grade.strip().upper() in {"A+", "A", "B+", "B"}

    def _format_class_brief(self, cls: Dict) -> str:
        return f"{cls.get('class_id', 'N/A')} ({cls.get('subject_code', 'N/A')})"

    def _to_time_text(self, value) -> str:
        if value is None:
            return "N/A"
        if isinstance(value, dtime):
            return value.strftime("%H:%M")
        if isinstance(value, timedelta):
            total_seconds = int(value.total_seconds())
            hours, rem = divmod(total_seconds, 3600)
            minutes = rem // 60
            if 0 <= hours <= 23:
                return f"{hours:02d}:{minutes:02d}"
        return str(value)

    def _aggregate_classes_for_text(self, classes: List[Dict]) -> List[Dict]:
        """Aggregate rows with same class_id into one logical class for text rendering."""
        from collections import OrderedDict

        groups: "OrderedDict[str, Dict]" = OrderedDict()
        for cls in classes:
            class_code = str(cls.get("class_id", "N/A"))
            group = groups.get(class_code)
            if not group:
                group = {
                    "class_id": cls.get("class_id", "N/A"),
                    "subject_id": cls.get("subject_id") or cls.get("subject_code", "N/A"),
                    "subject_name": cls.get("subject_name", ""),
                    "credits": cls.get("credits", 0),
                    "classroom": cls.get("classroom") or "TBA",
                    "teacher_name": cls.get("teacher_name") or "TBA",
                    "priority_reason": cls.get("priority_reason", ""),
                    "seats_available": cls.get("seats_available"),
                    "fully_satisfies": cls.get("fully_satisfies", False),
                    "violation_count": cls.get("violation_count", 0),
                    "violations": list(cls.get("violations", []) or []),
                    "slots": [],
                }
                groups[class_code] = group

            slot = f"{cls.get('study_date') or 'N/A'} {self._to_time_text(cls.get('study_time_start'))}-{self._to_time_text(cls.get('study_time_end'))}"
            if slot not in group["slots"]:
                group["slots"].append(slot)

            if (group.get("teacher_name") in ("", "TBA", "Chưa có GV")) and cls.get("teacher_name"):
                group["teacher_name"] = cls.get("teacher_name")
            if (group.get("classroom") in ("", "TBA", "N/A")) and cls.get("classroom"):
                group["classroom"] = cls.get("classroom")
            if not group.get("priority_reason") and cls.get("priority_reason"):
                group["priority_reason"] = cls.get("priority_reason")
            if group.get("seats_available") is None and cls.get("seats_available") is not None:
                group["seats_available"] = cls.get("seats_available")
            group["fully_satisfies"] = bool(group.get("fully_satisfies")) or bool(cls.get("fully_satisfies"))
            group["violation_count"] = max(group.get("violation_count", 0), cls.get("violation_count", 0) or 0)
            for v in (cls.get("violations") or []):
                if v not in group["violations"]:
                    group["violations"].append(v)

        return list(groups.values())

    def _audit_and_recommend_schedule(self, student_id: int) -> Dict:
        from collections import defaultdict
        from app.models.student_model import Student
        from app.models.class_register_model import ClassRegister
        from app.models.class_model import Class
        from app.models.subject_model import Subject
        from app.models.course_subject_model import CourseSubject
        from app.models.learned_subject_model import LearnedSubject

        student = self.db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return {
                "text": "❌ Không tìm thấy thông tin sinh viên.",
                "intent": "modify_schedule",
                "confidence": "high",
                "data": None,
            }

        registered_rows = (
            self.db.query(ClassRegister, Class, Subject)
            .join(Class, ClassRegister.class_id == Class.id)
            .join(Subject, Class.subject_id == Subject.id)
            .filter(ClassRegister.student_id == student_id)
            .all()
        )

        registered_classes: List[Dict] = []
        for reg, cls, subj in registered_rows:
            registered_classes.append({
                "register_id": reg.id,
                "class_db_id": cls.id,
                "class_id": cls.class_id,
                "class_name": cls.class_name,
                "subject_db_id": subj.id,
                "subject_code": subj.subject_id,
                "subject_name": subj.subject_name,
                "credits": subj.credits or 0,
                "days": self._parse_days(cls.study_date),
                "weeks": list(cls.study_week or []),
                "start_time": self._to_time_obj(cls.study_time_start),
                "end_time": self._to_time_obj(cls.study_time_end),
            })

        course_subject_ids = {
            row[0] for row in self.db.query(CourseSubject.subject_id).filter(CourseSubject.course_id == student.course_id).all()
        }

        learned_rows = self.db.query(LearnedSubject.subject_id, LearnedSubject.letter_grade).filter(
            LearnedSubject.student_id == student_id
        ).all()
        learned_ge_b_subjects = {sid for sid, grade in learned_rows if sid is not None and self._grade_ge_b(grade)}

        drop_reasons: Dict[int, List[str]] = defaultdict(list)

        for cls in registered_classes:
            if cls["subject_db_id"] not in course_subject_ids:
                drop_reasons[cls["class_db_id"]].append("Học phần không thuộc chương trình đào tạo")
            if cls["subject_db_id"] in learned_ge_b_subjects:
                drop_reasons[cls["class_db_id"]].append("Bạn đã học học phần này với điểm từ B trở lên")

        # Duplicate subject should be detected only when student has different class_id groups
        # for the same subject, not multiple rows of the same class_id.
        by_subject = defaultdict(list)
        for cls in registered_classes:
            by_subject[cls["subject_db_id"]].append(cls)
        for _, items in by_subject.items():
            distinct_class_codes = sorted({str(i.get("class_id", "N/A")) for i in items})
            if len(distinct_class_codes) > 1:
                all_class_ids = ", ".join(distinct_class_codes)
                for cls in items:
                    drop_reasons[cls["class_db_id"]].append(f"Đăng ký trùng học phần với các lớp: {all_class_ids}")

        for i in range(len(registered_classes)):
            for j in range(i + 1, len(registered_classes)):
                a = registered_classes[i]
                b = registered_classes[j]
                if str(a.get("class_id")) == str(b.get("class_id")):
                    # Same logical class split into multiple sessions - not a conflict.
                    continue
                if self._has_schedule_overlap(a, b):
                    drop_reasons[a["class_db_id"]].append(
                        f"Xung đột lịch với lớp {b.get('class_id', 'N/A')} ({b.get('subject_code', 'N/A')})"
                    )
                    drop_reasons[b["class_db_id"]].append(
                        f"Xung đột lịch với lớp {a.get('class_id', 'N/A')} ({a.get('subject_code', 'N/A')})"
                    )

        drop_lines: List[str] = []
        class_by_id = {c["class_db_id"]: c for c in registered_classes}
        reasons_by_class_code: Dict[str, List[str]] = defaultdict(list)
        sample_by_class_code: Dict[str, Dict] = {}
        for class_db_id, reasons in drop_reasons.items():
            cls = class_by_id.get(class_db_id)
            if not cls:
                continue
            class_code = str(cls.get("class_id", "N/A"))
            sample_by_class_code[class_code] = cls
            reasons_by_class_code[class_code].extend(reasons)

        for class_code, reasons in reasons_by_class_code.items():
            sample_cls = sample_by_class_code[class_code]
            uniq_reasons = list(dict.fromkeys(reasons))
            drop_lines.append(f"- {self._format_class_brief(sample_cls)}: " + "; ".join(uniq_reasons))

        registered_subject_ids = {c["subject_db_id"] for c in registered_classes}

        # Credits should not be multiplied by the number of weekly sessions.
        # Count each subject once.
        subject_credit_map: Dict[int, int] = {}
        for c in registered_classes:
            sid = c.get("subject_db_id")
            if sid is not None and sid not in subject_credit_map:
                subject_credit_map[sid] = c.get("credits", 0) or 0
        current_credits = sum(subject_credit_map.values())
        target_credits = 28

        needed_subject_ids = [
            sid for sid in course_subject_ids
            if sid not in learned_ge_b_subjects and sid not in registered_subject_ids
        ]

        candidate_rows = (
            self.db.query(Class, Subject)
            .join(Subject, Class.subject_id == Subject.id)
            .filter(Class.subject_id.in_(needed_subject_ids))
            .all()
            if needed_subject_ids else []
        )

        candidates_by_subject: Dict[int, List[Dict]] = defaultdict(list)
        for cls, subj in candidate_rows:
            candidates_by_subject[subj.id].append({
                "class_db_id": cls.id,
                "class_id": cls.class_id,
                "class_name": cls.class_name,
                "subject_db_id": subj.id,
                "subject_code": subj.subject_id,
                "subject_name": subj.subject_name,
                "credits": subj.credits or 0,
                "days": self._parse_days(cls.study_date),
                "weeks": list(cls.study_week or []),
                "start_time": self._to_time_obj(cls.study_time_start),
                "end_time": self._to_time_obj(cls.study_time_end),
            })

        selected_new_classes: List[Dict] = []
        occupied = list(registered_classes)

        if current_credits < target_credits:
            for subject_id in sorted(candidates_by_subject.keys()):
                options = sorted(candidates_by_subject[subject_id], key=lambda x: str(x.get("class_id", "")))
                chosen = None
                for option in options:
                    if any(self._has_schedule_overlap(option, occ) for occ in occupied):
                        continue
                    chosen = option
                    break
                if chosen:
                    selected_new_classes.append(chosen)
                    occupied.append(chosen)
                    current_credits += chosen.get("credits", 0)
                    if current_credits >= target_credits:
                        break

        add_lines = []
        seen_add_class_codes = set()
        for cls in selected_new_classes:
            code = str(cls.get("class_id", "N/A"))
            if code in seen_add_class_codes:
                continue
            seen_add_class_codes.add(code)
            add_lines.append(f"- {self._format_class_brief(cls)}: {cls.get('subject_name', '')}")

        sections = []
        if drop_lines:
            sections.append("Lớp nên xem xét bỏ:\n" + "\n".join(drop_lines))
        if add_lines:
            sections.append("Lớp có thể đăng ký thêm:\n" + "\n".join(add_lines))

        if not sections:
            final_text = "Thời khóa biểu của bạn rất ổn, không có xung đột thời gian, không còn học phần nào cần đăng ký."
        else:
            final_text = "\n\n".join(sections)

        return {
            "text": final_text,
            "intent": "class_registration_suggestion",
            "confidence": "high",
            "data": [{
                "consider_drop": drop_lines,
                "suggest_add": add_lines,
            }],
        }
    
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
        conversation_id: Optional[int] = None,
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
            conversation_id: Conversation ID for conversation-scoped state
            subject_id: Optional specific subject ID to filter
        
        Returns:
            Dict with text response and class suggestions OR next question
        """
        try:
            from app.services.conversation_state import get_conversation_state_manager
            from app.services.preference_service import PreferenceCollectionService
            
            print(f"🎯 [CLASS_SUGGESTION] Processing for student {student_id}, conversation {conversation_id}")
            print(f"📝 [CLASS_SUGGESTION] Question: {question}")

            if self._is_schedule_advice_query(question):
                print("🔍 [CLASS_SUGGESTION] Schedule audit mode activated")
                return self._audit_and_recommend_schedule(student_id)
            
            # Validate student_id
            if not student_id:
                return {
                    "text": "⚠️ Vui lòng đăng nhập để nhận gợi ý đăng ký lớp học.",
                    "intent": "class_registration_suggestion",
                    "confidence": "high",
                    "data": None,
                    "requires_auth": True,
                    "metadata": self._build_friendly_error_metadata("Bạn cần đăng nhập để tiếp tục nhận gợi ý lớp học.")
                }
            
            # Initialize services
            conv_manager = get_conversation_state_manager()
            pref_service = PreferenceCollectionService()
            class_data_notice = self._class_data_notice_text() if not self._has_class_data() else ""
            
            # Check for active conversation
            if conversation_id is None:
                return {
                    "text": "⚠️ Thiếu conversation_id để xử lý gợi ý lớp học. Vui lòng thử lại từ cuộc trò chuyện hiện tại.",
                    "intent": "class_registration_suggestion",
                    "confidence": "high",
                    "data": None,
                    "requires_auth": True,
                    "metadata": self._build_friendly_error_metadata("Thiếu conversation_id cho trạng thái hội thoại hiện tại.")
                }

            state = conv_manager.get_state(conversation_id)
            
            if state and state.stage == 'choose_subject_source':
                selected_source = self._parse_subject_source_choice(question)
                if not selected_source:
                    text = self._source_selection_question_text()
                    if class_data_notice:
                        text = f"{class_data_notice}\n\n{text}"
                    return {
                        "text": text,
                        "intent": "class_registration_suggestion",
                        "confidence": "high",
                        "data": None,
                        "conversation_state": "collecting",
                        "question_type": "single_choice",
                        "question_options": ["Học phần đã đăng ký", "Học phần hệ thống gợi ý"],
                        "metadata": self._build_class_suggestion_metadata(
                            preferences=state.preferences,
                            conversation_stage=state.stage,
                            current_question=None,
                            subject_source=self._normalize_subject_source_choice(getattr(state, 'subject_source_choice', None)),
                            subject_ids_seed=getattr(state, 'subject_ids_seed', []),
                            nlq_constraints_dict=getattr(state, 'nlq_constraints', None),
                            state=state,
                            next_step='choose_subject_source',
                            message='Mình cần bạn chọn nguồn học phần trước khi gợi ý lớp học.',
                        )
                    }

                state.subject_source_choice = selected_source
                if selected_source == 'registered':
                    selected_subject_ids = self._get_registered_subject_ids(student_id)
                    state.subject_ids_seed = selected_subject_ids
                    if not selected_subject_ids:
                        state.subject_source_choice = 'suggested'
                        warning_text = "⚠️ Bạn chưa đăng ký học phần, vui lòng đăng ký học phần trước."
                    else:
                        warning_text = ""
                else:
                    state.subject_ids_seed = []
                    warning_text = ""

                state.stage = 'collecting'
                next_question = pref_service.get_next_question(state.preferences)
                state.current_question = next_question
                conv_manager.save_state(state)

                prefix_parts = []
                if class_data_notice:
                    prefix_parts.append(class_data_notice)
                if warning_text:
                    prefix_parts.append(warning_text)
                prefix_text = "\n\n".join(prefix_parts)
                next_text = next_question.question if next_question else "Bạn còn yêu cầu gì cụ thể cho lớp học không?"

                return {
                    "text": (f"{prefix_text}\n\n{next_text}" if prefix_text else next_text),
                    "intent": "class_registration_suggestion",
                    "confidence": "high",
                    "data": None,
                    "conversation_state": "collecting",
                    "question_type": next_question.type if next_question else "free_text",
                    "question_options": next_question.options if next_question else None,
                    "metadata": self._build_class_suggestion_metadata(
                        preferences=state.preferences,
                        conversation_stage=state.stage,
                        current_question=next_question,
                        subject_source=self._normalize_subject_source_choice(getattr(state, 'subject_source_choice', None)),
                        subject_ids_seed=getattr(state, 'subject_ids_seed', []),
                        nlq_constraints_dict=getattr(state, 'nlq_constraints', None),
                        state=state,
                        next_step='ask_next_question',
                        message='Mình đã ghi nhận phần trả lời của bạn và sẽ hỏi nốt phần còn thiếu.',
                    )
                }

            if state and state.stage == 'collecting':
                # User is answering a preference question
                print(f"🔄 [CONVERSATION] Continuing conversation for student {student_id}")
                print(f"📋 [CONVERSATION] Current question: {state.current_question.key if state.current_question else None}")
                
                # Parse user response
                if state.current_question:
                    before_preferences = state.preferences.dict()
                    state.preferences = pref_service.parse_user_response(
                        response=question,
                        question_key=state.current_question.key,
                        current_preferences=state.preferences
                    )

                    # Capture extra preferences embedded in the same answer text.
                    state.preferences, supplemental_keys = pref_service.merge_supplemental_preferences(
                        response=question,
                        current_preferences=state.preferences,
                        skip_keys={state.current_question.key},
                    )
                    self._append_supplemental_keys(state, supplemental_keys)

                    after_preferences = state.preferences.dict()

                    if not self._is_valid_preference_answer(
                        state.current_question.key,
                        before_preferences,
                        after_preferences,
                        question,
                    ):
                        retry_text = self._build_retry_question_text(
                            state.current_question.key,
                            state.current_question.question,
                        )
                        conv_manager.save_state(state)
                        return {
                            "text": retry_text,
                            "intent": "class_registration_suggestion",
                            "confidence": "high",
                            "data": None,
                            "conversation_state": "collecting",
                            "question_type": state.current_question.type,
                            "question_options": state.current_question.options,
                            "metadata": self._build_class_suggestion_metadata(
                                preferences=state.preferences,
                                conversation_stage=state.stage,
                                current_question=state.current_question,
                                subject_source=self._normalize_subject_source_choice(getattr(state, 'subject_source_choice', None)),
                                subject_ids_seed=getattr(state, 'subject_ids_seed', []),
                                nlq_constraints_dict=getattr(state, 'nlq_constraints', None),
                                state=state,
                                next_step='retry_current_question',
                                message='Mình chưa đọc rõ câu trả lời vừa rồi, bạn trả lời lại ngắn gọn theo gợi ý bên dưới nhé.',
                            ),
                        }

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
                        subject_id=subject_id,
                        nlq_constraints_dict=getattr(state, 'nlq_constraints', None),
                        subject_source=self._normalize_subject_source_choice(getattr(state, 'subject_source_choice', None)),
                        subject_ids_seed=getattr(state, 'subject_ids_seed', []),
                        conversation_stage='completed',
                        conversation_state=state,
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
                        "question_options": next_question.options,
                        "metadata": self._build_class_suggestion_metadata(
                            preferences=state.preferences,
                            conversation_stage=state.stage,
                            current_question=next_question,
                            subject_source=self._normalize_subject_source_choice(getattr(state, 'subject_source_choice', None)),
                            subject_ids_seed=getattr(state, 'subject_ids_seed', []),
                            nlq_constraints_dict=getattr(state, 'nlq_constraints', None),
                            state=state,
                            next_step='ask_next_question',
                            message='Mình đã tự động lấy được một phần thông tin từ câu bạn vừa gửi.',
                        ),
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
                    conversation_id=conversation_id,
                    intent='class_registration_suggestion'
                )
                state.preferences = initial_preferences
                state.subject_source_choice = 'suggested'
                state.subject_ids_seed = []
                state.supplemental_preference_keys = []

                # If user directly answers source choice without prior state,
                # continue class-suggestion flow instead of forcing re-ask.
                direct_source_choice = self._parse_subject_source_choice(question)

                # Extract hard constraints (time/day) from initial message
                try:
                    from app.services.constraint_extractor import get_constraint_extractor
                    _extractor = get_constraint_extractor()
                    _constraints = _extractor.extract(question, query_type="class_registration_suggestion")
                    state.nlq_constraints = _constraints.dict()
                    constraint_keys = self._merge_constraints_into_preferences(
                        preferences=state.preferences,
                        constraints_dict=state.nlq_constraints,
                    )
                    self._append_supplemental_keys(state, constraint_keys)
                    print(f"🔒 [CONSTRAINTS] Extracted: days={_constraints.days} session={_constraints.session} avoid_start={_constraints.avoid_start_times}")
                except Exception as _ce:
                    print(f"⚠️ [CONSTRAINTS] Extract failed: {_ce}")
                    state.nlq_constraints = None
                
                # Check if preferences are already complete
                if state.preferences.is_complete():
                    print(f"✨ [INITIAL] Preferences already complete from initial question!")
                    state.stage = 'completed'
                    conv_manager.save_state(state)
                    
                    # Generate class suggestions immediately
                    return await self._generate_class_suggestions_with_preferences(
                        student_id=student_id,
                        preferences=state.preferences,
                        subject_id=subject_id,
                        nlq_constraints_dict=state.nlq_constraints,
                        subject_source=self._normalize_subject_source_choice(getattr(state, 'subject_source_choice', None)),
                        subject_ids_seed=getattr(state, 'subject_ids_seed', []),
                        conversation_stage='completed',
                        conversation_state=state,
                    )
                else:
                    if direct_source_choice:
                        state.subject_source_choice = direct_source_choice
                        if direct_source_choice == 'registered':
                            selected_subject_ids = self._get_registered_subject_ids(student_id)
                            state.subject_ids_seed = selected_subject_ids
                            if not selected_subject_ids:
                                state.subject_source_choice = 'suggested'
                                warning_text = "⚠️ Bạn chưa đăng ký học phần, vui lòng đăng ký học phần trước."
                            else:
                                warning_text = ""
                        else:
                            state.subject_ids_seed = []
                            warning_text = ""

                        state.stage = 'collecting'
                        next_question = pref_service.get_next_question(state.preferences)
                        state.current_question = next_question
                        conv_manager.save_state(state)

                        next_text = next_question.question if next_question else "Bạn còn yêu cầu gì cụ thể cho lớp học không?"
                        if warning_text:
                            next_text = f"{warning_text}\n\n{next_text}"
                        if class_data_notice:
                            next_text = f"{class_data_notice}\n\n{next_text}"

                        return {
                            "text": next_text,
                            "intent": "class_registration_suggestion",
                            "confidence": "high",
                            "data": None,
                            "conversation_state": "collecting",
                            "question_type": next_question.type if next_question else "free_text",
                            "question_options": next_question.options if next_question else None,
                            "metadata": self._build_class_suggestion_metadata(
                                preferences=state.preferences,
                                conversation_stage=state.stage,
                                current_question=next_question,
                                subject_source=self._normalize_subject_source_choice(getattr(state, 'subject_source_choice', None)),
                                subject_ids_seed=getattr(state, 'subject_ids_seed', []),
                                nlq_constraints_dict=state.nlq_constraints,
                                state=state,
                                next_step='ask_next_question',
                                message='Mình đã nhận được thêm thông tin từ câu của bạn.',
                            ),
                        }

                    # Start with source selection question before preference questions
                    state.stage = 'choose_subject_source'
                    state.current_question = None
                    conv_manager.save_state(state)

                    question_text = self._source_selection_question_text()
                    if class_data_notice:
                        question_text = f"{class_data_notice}\n\n{question_text}"

                    return {
                        "text": question_text,
                        "intent": "class_registration_suggestion",
                        "confidence": "high",
                        "data": None,
                        "conversation_state": "collecting",
                        "question_type": "single_choice",
                        "question_options": ["Học phần đã đăng ký", "Học phần hệ thống gợi ý"],
                        "metadata": self._build_class_suggestion_metadata(
                            preferences=state.preferences,
                            conversation_stage=state.stage,
                            current_question=None,
                            subject_source=self._normalize_subject_source_choice(getattr(state, 'subject_source_choice', None)),
                            subject_ids_seed=getattr(state, 'subject_ids_seed', []),
                            nlq_constraints_dict=state.nlq_constraints,
                            state=state,
                            next_step='choose_subject_source',
                            message='Mình cần xác nhận nguồn học phần trước khi đi tiếp.',
                        ),
                    }
        
        except Exception as e:
            print(f"❌ [CLASS_SUGGESTION] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "text": f"⚠️ Có lỗi xảy ra: {str(e)}",
                "intent": "class_registration_suggestion",
                "confidence": "high",
                "data": None,
                "metadata": self._build_friendly_error_metadata("Đã có lỗi khi xử lý gợi ý lớp học. Bạn thử gửi lại câu hỏi nhé.")
            }

    async def process_modify_schedule(self, student_id: int, question: str) -> Dict:
        """
        Dedicated intent handler for timetable adjustment/audit.

        This runs schedule audit logic and returns:
        - classes to consider dropping + reasons
        - classes to consider adding (until 28 credits target)
        """
        try:
            if not student_id:
                return {
                    "text": "⚠️ Vui lòng đăng nhập để được tư vấn điều chỉnh thời khóa biểu.",
                    "intent": "modify_schedule",
                    "confidence": "high",
                    "data": None,
                    "requires_auth": True,
                }

            result = self._audit_and_recommend_schedule(student_id)
            result["intent"] = "modify_schedule"
            return result
        except Exception as e:
            print(f"❌ [MODIFY_SCHEDULE] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "text": f"⚠️ Có lỗi xảy ra khi phân tích thời khóa biểu: {str(e)}",
                "intent": "modify_schedule",
                "confidence": "low",
                "data": None,
                "error": str(e),
            }
    
    async def _generate_class_suggestions_with_preferences(
        self,
        student_id: int,
        preferences,
        subject_id: Optional[str] = None,
        nlq_constraints_dict: Optional[Dict] = None,
        subject_source: str = "suggested",
        subject_ids_seed: Optional[List[int]] = None,
        conversation_stage: str = "completed",
        conversation_state=None,
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
            
            from app.models.subject_model import Subject

            # First, get subject candidates based on source
            subject_result = self.subject_rule_engine.suggest_subjects(student_id)

            if subject_source == 'registered' and subject_ids_seed:
                registered_subject_rows = (
                    self.db.query(Subject)
                    .filter(Subject.id.in_(subject_ids_seed))
                    .all()
                )
                suggested_subjects = [
                    {
                        "id": s.id,
                        "subject_id": s.subject_id,
                        "subject_name": s.subject_name,
                        "credits": s.credits or 0,
                        "priority_reason": "Theo học phần bạn đã đăng ký"
                    }
                    for s in registered_subject_rows
                ]
                if not suggested_subjects:
                    suggested_subjects = subject_result['suggested_subjects']
            else:
                suggested_subjects = subject_result['suggested_subjects']

            # Merge user-requested specific subjects into candidate list.
            specific_subject_inputs = list(getattr(preferences.specific, 'specific_subjects', []) or [])
            if specific_subject_inputs:
                additional_subjects = []
                for raw_value in specific_subject_inputs:
                    token = (raw_value or '').strip()
                    if not token:
                        continue

                    is_subject_code = bool(re.fullmatch(r'[A-Z]{2,4}\d{3,4}', token.upper()))
                    if is_subject_code:
                        matches = (
                            self.db.query(Subject)
                            .filter(Subject.subject_id.ilike(token.upper()))
                            .all()
                        )
                    else:
                        matches = (
                            self.db.query(Subject)
                            .filter(Subject.subject_name.ilike(f"%{token}%"))
                            .all()
                        )

                    if not matches and is_subject_code:
                        matches = (
                            self.db.query(Subject)
                            .filter(Subject.subject_id.ilike(f"{token.upper()}%"))
                            .all()
                        )

                    for subject_row in matches:
                        additional_subjects.append(
                            {
                                "id": subject_row.id,
                                "subject_id": subject_row.subject_id,
                                "subject_name": subject_row.subject_name,
                                "credits": subject_row.credits or 0,
                                "priority_reason": "Theo học phần bạn yêu cầu cụ thể",
                            }
                        )

                if additional_subjects:
                    merged_subjects: Dict[int, Dict] = {}
                    specific_subject_ids: set[int] = set()
                    for subject_item in suggested_subjects + additional_subjects:
                        subject_pk = subject_item.get('id')
                        if subject_pk is None:
                            continue

                        if subject_item.get('priority_reason') == 'Theo học phần bạn yêu cầu cụ thể':
                            specific_subject_ids.add(subject_pk)

                        if subject_pk not in merged_subjects:
                            merged_subjects[subject_pk] = subject_item
                            continue

                        if subject_item.get('priority_reason') == 'Theo học phần bạn yêu cầu cụ thể':
                            merged_subjects[subject_pk]['priority_reason'] = subject_item['priority_reason']

                    suggested_subjects = sorted(
                        merged_subjects.values(),
                        key=lambda item: 0 if item.get('id') in specific_subject_ids else 1,
                    )
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
                        "data": None,
                        "metadata": self._build_class_suggestion_metadata(
                            preferences=preferences,
                            conversation_stage=conversation_stage,
                            current_question=None,
                            subject_source=subject_source,
                            subject_ids_seed=subject_ids_seed,
                            nlq_constraints_dict=nlq_constraints_dict,
                            state=conversation_state,
                            next_step='done',
                            message=f'Hiện tại mình chưa tìm thấy gợi ý phù hợp riêng cho môn {subject_id}.',
                        )
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
                    min_suggestions=2  # Reduce candidate size to speed up response
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

                # Apply hard constraints from NL query (exact time/day/session)
                if nlq_constraints_dict:
                    try:
                        from app.services.constraint_extractor import ClassQueryConstraints
                        from app.services.class_query_service import ClassQueryService
                        _c = ClassQueryConstraints(**nlq_constraints_dict)
                        _svc = ClassQueryService(self.db)
                        _hard = _svc._apply_hard_filters(filtered_classes, _c)
                        if _hard:  # Only replace if result non-empty
                            filtered_classes = _hard
                            print(f"  🔒 After hard constraints: {len(filtered_classes)} classes")
                    except Exception as _he:
                        print(f"  ⚠️ Hard constraint filter error: {_he}")

                # Keep top candidates per subject to limit combination explosion
                subject_suggested = filtered_classes[:4]
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
                max_combinations=40
            )

            if not combinations:
                from app.services.conversation_state import get_conversation_state_manager
                get_conversation_state_manager().delete_state(conversation_state.conversation_id or conversation_id)
                return {
                    "text": "⚠️ Hiện chưa tìm được tổ hợp lớp phù hợp với điều kiện hiện tại. Bạn có thể nới lỏng một số tiêu chí để mình gợi ý tốt hơn.",
                    "intent": "class_registration_suggestion",
                    "confidence": "high",
                    "data": [],
                    "metadata": {
                        "total_subjects": len(suggested_subjects),
                        "total_combinations": 0,
                        "preferences_applied": preferences_dict,
                        "ui": {
                            "title": "Mình chưa tìm được tổ hợp phù hợp",
                            "subtitle": "Bạn có thể nới một vài tiêu chí để mình gợi ý dễ hơn.",
                            "status": "Không có tổ hợp phù hợp",
                        },
                        "conversation": {
                            "stage": conversation_stage,
                            "next_step": "adjust_preferences",
                            "source_choice": subject_source,
                        },
                        "preferences": {
                            "captured": self._build_preference_snapshot(preferences),
                            "missing": [
                                {
                                    'key': key,
                                    'label': self._friendly_preference_label(key),
                                    'hint': self._friendly_question_hint(key),
                                }
                                for key in preferences.get_missing_preferences()
                            ],
                            "auto_captured_keys": list(getattr(conversation_state, 'supplemental_preference_keys', []) or []),
                        },
                    },
                    "rule_engine_used": True,
                    "conversation_state": "completed"
                }
            
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
            from app.services.conversation_state import get_conversation_state_manager
            get_conversation_state_manager().delete_state(conversation_state.conversation_id or conversation_id)
            
            return {
                "text": text_response,
                "intent": "class_registration_suggestion",
                "confidence": "high",
                "data": formatted_combinations,
                "metadata": {
                    **self._build_class_suggestion_metadata(
                        preferences=preferences,
                        conversation_stage=conversation_stage,
                        current_question=None,
                        subject_source=subject_source,
                        subject_ids_seed=subject_ids_seed,
                        nlq_constraints_dict=nlq_constraints_dict,
                        state=conversation_state,
                        next_step='done',
                        message='Mình đã tổng hợp các gợi ý lớp học phù hợp nhất cho bạn.',
                    ),
                    "result": {
                        "total_subjects": len(suggested_subjects),
                        "total_combinations": len(top_combinations),
                        "student_cpa": subject_result['student_cpa'],
                        "current_semester": subject_result['current_semester'],
                        "preferences_applied": preferences_dict,
                    }
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
                "metadata": self._build_friendly_error_metadata("Mình gặp lỗi khi tạo danh sách lớp gợi ý. Bạn thử lại nhé."),
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
        Extract specific subject ID from user's question.

        Priority:
        1. Static keyword dict (nhanh nhất)
        2. Regex subject code pattern (IT3170, SSH1131...)
        3. Fuzzy matching fallback (trích xuất tên môn từ câu hỏi, dùng rapidfuzz)

        Examples:
            - "gợi ý lớp Tiếng Nhật" → "JP"
            - "lớp tiếng anh nào" → "ENG"
            - "môn lập trình mạng" → "IT3170"
            - "môn SSH1131" → "SSH1131"
            - "môn giai tich 1" → fuzzy → "MI1114"
        """
        question_lower = question.lower()

        # ——— 1. Static keyword shortcuts (fastest path) ————————————————
        subject_keywords = {
            'tiếng nhật': 'JP',
            'tiếng anh': 'ENG',
            'japanese': 'JP',
            'english': 'ENG',
            'lập trình mạng': 'IT3170',
            'cơ sở dữ liệu': 'IT3080',
            'toán': 'MI',
            'vật lý': 'PH',
            'hóa học': 'CH',
            'sinh học': 'BI',
            'triết học': 'PHI',
            'chủ nghĩa xã hội': 'SSH',
            'cnxh': 'SSH',
            'xã hội': 'SSH',
        }
        for keyword, subject_prefix in subject_keywords.items():
            if keyword in question_lower:
                return subject_prefix

        # ——— 2. Regex: mã môn dạng IT3170, SSH1131, JP2126 ————————————
        import re
        pattern = r'\b([A-Z]{2,4}\d{3,4})\b'
        code_match = re.search(pattern, question.upper())
        if code_match:
            return code_match.group(1)

        # ——— 3. Fuzzy Matching Fallback —————————————————————————————
        # Trích xuất tên môn từ câu hỏi sau keyword "môn", "lớp", "học phần"
        subject_name_patterns = [
            r'(?:môn|lớp|học phần)\s+học\s+([^\?\.,]+)',
            r'(?:môn|lớp|học phần)\s+([^\?\.,]{3,})',
            r'(?:gợi ý|dăng ký|đăng ký)\s+(?:lớp|môn)(?:\s+học)?\s+([^\?\.,]{3,})',
        ]
        extracted_name = None
        for pat in subject_name_patterns:
            m = re.search(pat, question_lower)
            if m:
                candidate = m.group(1).strip()
                # Loại "gì", "nào" (question words)
                if not re.match(r'^(g\u00ec|n\u00e0o|n\u00e0o\s)', candidate):
                    extracted_name = candidate
                    break

        if extracted_name and self._fuzzy_matcher:
            try:
                fuzzy_result = self._fuzzy_matcher.match_subject(extracted_name)
                if fuzzy_result and fuzzy_result.auto_mapped:
                    print(f"🔍 [CHATBOT_SERVICE FUZZY] '{extracted_name}' → '{fuzzy_result.subject_id}' (score={fuzzy_result.score:.0f})")
                    return fuzzy_result.subject_id
                elif fuzzy_result:
                    print(f"⚠️ [CHATBOT_SERVICE FUZZY] '{extracted_name}' score={fuzzy_result.score:.0f} < threshold, no auto-map")
            except Exception as e:
                print(f"⚠️ [CHATBOT_SERVICE FUZZY] Error: {e}")
        # —————————————————————————————————————————————————————————

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

            # Render logical classes (same class_id with multiple sessions -> one class)
            logical_classes = self._aggregate_classes_for_text(combo['classes'])
            for cls in logical_classes:
                response.append(f"    • {cls['subject_id']} - {cls['subject_name']} ({cls['credits']} TC)")
                response.append(f"      Lớp {cls['class_id']} ({len(cls['slots'])} buổi/tuần)")
                for slot in cls['slots']:
                    response.append(f"        - {slot}")
                response.append(f"      Phòng {cls['classroom']} - {cls['teacher_name'] if cls['teacher_name'] else 'TBA'}")

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
            logical_classes = self._aggregate_classes_for_text(subject_classes)
            if not logical_classes:
                response.append(f"{idx}. {subject_id} - Chưa có lớp khả dụng")
                response.append("")
                continue

            first_class = logical_classes[0]
            priority_reason = first_class.get('priority_reason', '')
            
            response.append(f"{idx}. {subject_id} - {first_class['subject_name']} ({first_class['credits']} TC)")
            if priority_reason:
                response.append(f"   💡 {priority_reason}")
            response.append(f"   Có {len(logical_classes)} lớp khả dụng:")
            
            for cls in logical_classes[:3]:  # Show max 3 logical classes per subject
                time_info = "; ".join(cls.get('slots', []))
                
                # Add satisfaction badge
                fully_satisfied = cls.get('fully_satisfies', False)
                violation_count = cls.get('violation_count', 0)
                badge = "✅" if fully_satisfied else (f"⚠️" if violation_count > 0 else "")
                
                class_line = f"     • {cls['class_id']} ({len(cls.get('slots', []))} buổi/tuần): {time_info} "
                class_line += f"- Phòng {cls['classroom']} - GV: {cls['teacher_name']} "
                class_line += f"({cls['seats_available']} chỗ trống) {badge}"
                
                response.append(class_line)
                
                # Show violations if any
                if violation_count > 0 and cls.get('violations'):
                    violations_str = ', '.join(cls['violations'][:2])
                    response.append(f"       ⚠️ {violations_str}")
            
            if len(logical_classes) > 3:
                response.append(f"     ... và {len(logical_classes) - 3} lớp khác")
            
            response.append("")
        
        response.append("💡 Ghi chú:")
        response.append("   ✅ = Thỏa mãn hoàn toàn tiêu chí")
        response.append("   ⚠️ = Có vi phạm tiêu chí nhưng vẫn khả dụng")
        
        return "\n".join(response)

    # ─────────────────────────────────────────────────────────────────────────
    # Streaming processing method
    # ─────────────────────────────────────────────────────────────────────────

    async def process_query_with_streaming(
        self,
        normalized_text: str,
        student_id: Optional[int],
        conversation_id: Optional[int],
        intent: str,
        confidence: str,
    ):
        """
        Generator để streaming response từng giai đoạn xử lý
        Yield StreamChunk objects cho từng status update
        """
        from datetime import datetime
        from app.schemas.chatbot_schema import StreamChunk

        # Phase 1: Preprocessing complete (returned from caller)
        yield StreamChunk(
            type="status",
            stage="preprocessing",
            message="✓ Chuẩn hóa dữ liệu hoàn tất",
        )

        # Phase 2: Intent classification complete (returned from caller)
        yield StreamChunk(
            type="status",
            stage="classification",
            message=f"✓ Phân loại: {intent} ({confidence})",
        )

        # Phase 3: Query processing start
        yield StreamChunk(
            type="status",
            stage="query",
            message="🔄 Đang truy vấn cơ sở dữ liệu...",
        )

        # Phase 4: Process based on intent
        result_data = None
        result_text = ""

        if intent in ("subject_registration_suggestion", "class_registration_suggestion", "modify_schedule"):
            # Rule engine path
            if intent == "subject_registration_suggestion":
                result = await self.process_subject_suggestion(
                    student_id=student_id,
                    question=normalized_text,
                )
            elif intent == "modify_schedule":
                result = await self.process_modify_schedule(
                    student_id=student_id,
                    question=normalized_text,
                )
            else:
                result = await self.process_class_suggestion(
                    student_id=student_id,
                    question=normalized_text,
                    conversation_id=conversation_id,
                )

            result_data = result.get("data")
            if result_data is not None and not isinstance(result_data, list):
                if isinstance(result_data, dict):
                    result_data = [result_data]
                else:
                    result_data = [{"value": result_data}]

            result_text = result.get("text", "")
            intent = result.get("intent", intent)
            confidence = result.get("confidence", confidence)

            # Stream progress
            if result_data:
                yield StreamChunk(
                    type="data",
                    stage="query",
                    message=f"✓ Lấy được {len(result_data)} kết quả",
                    partial_data=result_data[:5] if len(result_data) > 5 else result_data,
                    data_count=len(result_data),
                    total_count=len(result_data),
                )

        elif intent == "class_info":
            # Constraint extractor path
            try:
                from app.services.constraint_extractor import get_constraint_extractor
                from app.services.class_query_service import ClassQueryService

                extractor = get_constraint_extractor()
                constraints = extractor.extract(normalized_text, query_type="class_info")

                has_structured_filters = any([
                    bool(constraints.subject_codes),
                    bool(constraints.subject_names),
                    bool(constraints.class_ids),
                    bool(constraints.class_names),
                    bool(constraints.subject_ids),
                    bool(constraints.days),
                    bool(constraints.session),
                    bool(constraints.day_session_constraints),
                    bool(constraints.start_time_exact),
                    bool(constraints.end_time_exact),
                    bool(constraints.time_range),
                    bool(constraints.time_from),
                    bool(constraints.classroom_exact),
                    bool(constraints.building_code),
                    bool(constraints.room_code),
                ])

                if has_structured_filters:
                    svc = ClassQueryService(self.db)
                    rows = svc.query(constraints)

                    import datetime as dt
                    for r in rows:
                        if isinstance(r.get("study_time_start"), dt.time):
                            r["study_time_start"] = r["study_time_start"].strftime("%H:%M")
                        if isinstance(r.get("study_time_end"), dt.time):
                            r["study_time_end"] = r["study_time_end"].strftime("%H:%M")

                    result_data = rows
                    result_text = (
                        f"✅ Tìm thấy {len({str(r.get('class_id')) for r in rows if r.get('class_id') is not None}) or len(rows)} lớp học phù hợp."
                        if rows
                        else "Không tìm thấy dữ liệu phù hợp với câu hỏi của bạn."
                    )

                    if result_data:
                        yield StreamChunk(
                            type="data",
                            stage="query",
                            message=f"✓ Lấy được {len(result_data)} lớp học",
                            partial_data=result_data[:10],
                            data_count=len(result_data),
                            total_count=len(result_data),
                        )

            except Exception as ce:
                print(f"⚠️ Constraint extractor error: {ce}")

        else:
            # NL2SQL path for other intents
            try:
                from app.services.nl2sql_service import NL2SQLService

                nl2sql_service = NL2SQLService()
                sql_result = await nl2sql_service.generate_sql(
                    question=normalized_text,
                    intent=intent,
                    student_id=student_id,
                    db=self.db,
                )

                sql_query = sql_result.get("sql")
                if sql_query:
                    from sqlalchemy import text

                    result_rows = self.db.execute(text(sql_query))
                    rows = result_rows.fetchall()
                    if rows:
                        columns = result_rows.keys()
                        result_data = [dict(zip(columns, row)) for row in rows]
                    else:
                        result_data = []

                    result_text = f"✅ Tìm thấy {len(result_data)} kết quả" if result_data else "Không tìm thấy dữ liệu phù hợp."

                    if result_data:
                        yield StreamChunk(
                            type="data",
                            stage="query",
                            message=f"✓ Lấy được {len(result_data)} bản ghi",
                            partial_data=result_data[:10],
                            data_count=len(result_data),
                            total_count=len(result_data),
                        )

            except Exception as e:
                print(f"⚠️ NL2SQL error: {e}")
                result_text = "Xin lỗi, không thể xử lý câu hỏi của bạn lúc này."

        # Phase 5: Complete - send full response
        yield StreamChunk(
            type="done",
            stage="complete",
            text=result_text or "Hoàn tất xử lý",
            intent=intent,
            confidence=confidence,
            data=result_data,
        )
