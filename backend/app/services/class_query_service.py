"""
Class Query Service – Builds SQLAlchemy queries from ClassQueryConstraints.

Không dùng raw SQL text được tạo bởi NL2SQL.
Thay vào đó, dùng ORM + whitelist-field filtering để:
  - An toàn (no injection)
  - Nhanh (dùng index)
  - Dễ debug

Sử dụng FuzzyMatcher để resolve subject_names → subject_ids trước khi query.
"""
from __future__ import annotations

import re
from datetime import time as dtime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.models.class_model import Class
from app.models.subject_model import Subject
from app.models.class_register_model import ClassRegister
from app.services.constraint_extractor import ClassQueryConstraints, DaySessionConstraint


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _to_time(t_str: Optional[str]) -> Optional[dtime]:
    """Convert "08:25" → datetime.time(8, 25)."""
    if not t_str:
        return None
    try:
        h, m = t_str.split(":")
        return dtime(int(h), int(m))
    except Exception:
        return None


def _timedelta_to_time(td) -> Optional[dtime]:
    """MySQL TIME column returns timedelta; convert to datetime.time."""
    if isinstance(td, dtime):
        return td
    if isinstance(td, timedelta):
        total = int(td.total_seconds())
        h, rem = divmod(total, 3600)
        m = rem // 60
        return dtime(h, m)
    if isinstance(td, str):
        s = td.strip()
        # Some drivers can surface TIME/INTERVAL-like strings, e.g. "PT30300S".
        m = re.match(r'^PT(\d+)S$', s)
        if m:
            total = int(m.group(1))
            h, rem = divmod(total, 3600)
            mn = rem // 60
            if 0 <= h <= 23:
                return dtime(h, mn)
        # Fallback for plain HH:MM(:SS)
        m2 = re.match(r'^(\d{1,2}):(\d{2})(?::\d{2})?$', s)
        if m2:
            h = int(m2.group(1))
            mn = int(m2.group(2))
            if 0 <= h <= 23 and 0 <= mn <= 59:
                return dtime(h, mn)
    return None


def _row_to_dict(row, registered_count: int) -> Dict:
    """Convert a (Class, Subject, count) result to plain dict."""
    cls: Class   = row[0]
    subj: Subject = row[1]

    start = _timedelta_to_time(cls.study_time_start)
    end   = _timedelta_to_time(cls.study_time_end)

    return {
        "id":               cls.id,
        "class_id":         cls.class_id,
        "class_name":       cls.class_name or "",
        "classroom":        cls.classroom or "",
        "study_date":       cls.study_date or "",
        "study_time_start": start,
        "study_time_end":   end,
        "study_week":       cls.study_week or [],
        "teacher_name":     cls.teacher_name or "",
        "subject_id":       subj.subject_id,
        "subject_name":     subj.subject_name or "",
        "credits":          subj.credits or 0,
        "registered_count": registered_count,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Service
# ──────────────────────────────────────────────────────────────────────────────

class ClassQueryService:
    """
    Resolves ClassQueryConstraints → DB rows for classes.

    Usage:
        svc = ClassQueryService(db)
        rows = svc.query(constraints)
    """

    MORNING_START = dtime(6, 0)
    MORNING_END   = dtime(12, 0)
    AFTERNOON_START = dtime(12, 0)
    AFTERNOON_END   = dtime(20, 0)

    def __init__(self, db: Session):
        self.db = db
        self._fuzzy: Optional[object] = None   # lazy init

    # ── Public ────────────────────────────────────────────────────────────────

    def query(
        self,
        constraints: ClassQueryConstraints,
        include_full: bool = False,
    ) -> List[Dict]:
        """
        Execute DB query from constraints.

        Args:
            constraints: Parsed ClassQueryConstraints
            include_full: If True, also return classes with no seats left

        Returns:
            List of class dicts
        """
        # 1. Resolve subject names → subject_ids via fuzzy
        resolved_ids = self._resolve_subjects(constraints)

        has_non_subject_filters = any([
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

        # 2. If no subject filter at all, return empty (too broad)
        if not resolved_ids and not has_non_subject_filters:
            return []

        # 3. Base ORM query
        q = (
            self.db.query(Class, Subject)
            .join(Subject, Class.subject_id == Subject.id)
        )

        # 4. Subject filter (optional if user only asks by room/time/day)
        if resolved_ids:
            q = q.filter(Subject.subject_id.in_(resolved_ids))

        

        # 5. Execute and build dicts
        rows = q.all()

        # Build registered count map
        cnt_map: Dict[int, int] = {}
        for cls, _ in rows:
            # we'll compute from subq via extra query if needed
            cnt_map[cls.id] = 0

        # Re-fetch registered counts
        reg_counts = (
            self.db.query(ClassRegister.class_id, func.count(ClassRegister.id))
            .filter(ClassRegister.class_id.in_([cls.id for cls, _ in rows]))
            .group_by(ClassRegister.class_id)
            .all()
        )
        for class_id, cnt in reg_counts:
            cnt_map[class_id] = cnt

        result_dicts = [_row_to_dict(row, cnt_map.get(row[0].id, 0)) for row in rows]

        # 6. Post-filter by time/day (done in Python for portability with LIKE study_date)
        result_dicts = self._apply_time_day_filters(result_dicts, constraints)

        return result_dicts

    def query_for_suggestion(
        self,
        constraints: ClassQueryConstraints,
        subject_ids_from_rules: List[str],
    ) -> Dict[str, List[Dict]]:
        """
        Query classes grouped by subject_id, used by ScheduleOptimizer.

        Args:
            constraints: Hard/soft constraints
            subject_ids_from_rules: subject_ids suggested by SubjectSuggestionRuleEngine

        Returns:
            { subject_id: [class_dict, ...] }
        """
        # Start from rule-engine suggestions; also add must-have subjects
        all_ids = list(dict.fromkeys(subject_ids_from_rules))

        # Resolve must-include from constraints
        must_ids = self._resolve_must_include(constraints)
        for mid in must_ids:
            if mid not in all_ids:
                all_ids.insert(0, mid)   # prepend so they're prioritised

        if not all_ids:
            return {}

        # Base query – no seat filter here (optimizer decides)
        q = (
            self.db.query(Class, Subject)
            .join(Subject, Class.subject_id == Subject.id)
            .filter(Subject.subject_id.in_(all_ids))
        )
        rows = q.all()

        cnt_map = self._fetch_reg_counts([cls.id for cls, _ in rows])
        raw_dicts = [_row_to_dict(row, cnt_map.get(row[0].id, 0)) for row in rows]

        # Apply hard time filters
        filtered = self._apply_hard_filters(raw_dicts, constraints)

        # Group by subject_id
        grouped: Dict[str, List[Dict]] = {}
        for cls_dict in filtered:
            sid = cls_dict["subject_id"]
            grouped.setdefault(sid, []).append(cls_dict)

        return grouped

    # ── Subject resolving ─────────────────────────────────────────────────────

    def _get_fuzzy(self):
        if self._fuzzy is None:
            try:
                from app.services.fuzzy_matcher import FuzzyMatcher
                self._fuzzy = FuzzyMatcher(self.db)
            except Exception as e:
                print(f"⚠️ [ClassQueryService] FuzzyMatcher unavailable: {e}")
                self._fuzzy = None
        return self._fuzzy

    def _resolve_subjects(self, c: ClassQueryConstraints) -> List[str]:
        """Return list of subject_ids to query."""
        ids: List[str] = list(c.subject_codes)   # start with explicitly provided codes

        # Also honour already-resolved ids
        ids.extend(c.resolved_subject_ids)

        fuzzy = self._get_fuzzy()
        if fuzzy:
            for name in c.subject_names:
                match = fuzzy.match_subject(name, db=self.db)
                if match:
                    print(f"🔍 [ClassQueryService] '{name}' → '{match.subject_id}' (score={match.score:.0f})")
                    if match.subject_id not in ids:
                        ids.append(match.subject_id)
                    # If score < AUTO_MAP_THRESHOLD, still include but flag uncertain
                else:
                    print(f"⚠️ [ClassQueryService] No fuzzy match for '{name}'")

        return list(dict.fromkeys(ids))  # deduplicate

    def _resolve_must_include(self, c: ClassQueryConstraints) -> List[str]:
        """Resolve must-include subject names/codes to subject_ids."""
        ids = list(c.must_include_subject_codes)
        fuzzy = self._get_fuzzy()
        if fuzzy:
            for name in c.must_include_subject_names:
                match = fuzzy.match_subject(name, db=self.db)
                if match and match.subject_id not in ids:
                    ids.append(match.subject_id)
        return ids

    # ── Filtering ─────────────────────────────────────────────────────────────

    def _class_days(self, cls_dict: Dict) -> List[str]:
        """Parse study_date 'Monday,Wednesday' → ['Monday','Wednesday']."""
        sd = cls_dict.get("study_date", "")
        if not sd:
            return []
        return [d.strip() for d in sd.split(",") if d.strip()]

    def _apply_time_day_filters(
        self, classes: List[Dict], c: ClassQueryConstraints
    ) -> List[Dict]:
        """Apply all time/day filters."""
        result = []
        for cls in classes:
            if self._passes_filters(cls, c):
                result.append(cls)
        return result

    def _apply_hard_filters(
        self, classes: List[Dict], c: ClassQueryConstraints
    ) -> List[Dict]:
        """Apply only hard constraints (for optimizer candidate generation)."""
        result = []
        for cls in classes:
            if self._passes_hard_constraints(cls, c):
                result.append(cls)
        return result

    def _passes_filters(self, cls: Dict, c: ClassQueryConstraints) -> bool:
        """Return True if class passes all filters."""
        return self._passes_hard_constraints(cls, c)

    def _passes_hard_constraints(self, cls: Dict, c: ClassQueryConstraints) -> bool:
        """
        Check hard constraints:
        - Day filter
        - Session filter  
        - Exact time
        - Time range / from
        - Avoid start/end times
        - Day-session combinations
        """
        cls_days = self._class_days(cls)
        start    = cls.get("study_time_start")
        end      = cls.get("study_time_end")
        classroom = (cls.get("classroom") or "").upper().strip()

        # ── Classroom filter (exact / building / room) ──────────────────────
        if c.classroom_exact:
            if classroom != c.classroom_exact.upper():
                return False
        else:
            if c.building_code:
                if not classroom.startswith(f"{c.building_code.upper()}-"):
                    return False
            if c.room_code:
                # Primary format in DB is building-room, e.g. D9-401
                # Keep a fallback for records that may store only room text.
                if not (classroom.endswith(f"-{c.room_code}") or re.search(rf'\b{re.escape(c.room_code)}\b', classroom)):
                    return False

        # ── Day filter (top-level c.days) ────────────────────────────────────
        if c.days:
            if not any(d in c.days for d in cls_days):
                return False

        # ── Day-session combination constraints ──────────────────────────────
        if c.day_session_constraints:
            allowed = set()
            for dsc in c.day_session_constraints:
                for d in (dsc.days if dsc.days else cls_days):
                    allowed.add((d, dsc.session))

            # class must have at least one (day, session) pair in allowed
            cls_ok = False
            for d in cls_days:
                session_ok = True
                matching_sessions = [
                    dsc.session for dsc in c.day_session_constraints
                    if d in dsc.days or not dsc.days
                ]
                if not matching_sessions:
                    # day not mentioned in any dsc → not allowed
                    session_ok = False
                else:
                    for sess in matching_sessions:
                        if sess is None or self._session_matches(start, sess):
                            cls_ok = True
                            break
                if cls_ok:
                    break

            # If day_session_constraints given, strict: class must satisfy at least one
            if c.day_session_constraints and not cls_ok:
                # Last resort: if c.days is also set, check that
                if c.days and not any(d in c.days for d in cls_days):
                    return False

        # ── Session (top-level) ───────────────────────────────────────────────
        if c.session and not c.day_session_constraints:
            if not self._session_matches(start, c.session):
                return False

        # ── Exact start time ─────────────────────────────────────────────────
        if c.start_time_exact:
            t = _to_time(c.start_time_exact)
            if t and (start is None or start != t):
                return False

        # ── Exact end time ───────────────────────────────────────────────────
        if c.end_time_exact:
            t = _to_time(c.end_time_exact)
            if t and (end is None or end != t):
                return False

        # ── Time range ───────────────────────────────────────────────────────
        if c.time_range:
            t_from = _to_time(c.time_range[0])
            t_to   = _to_time(c.time_range[1])
            if start is None or end is None:
                return False
            if t_from and start and start < t_from:
                return False
            if t_to and end and end > t_to:
                return False

        # ── Time from ────────────────────────────────────────────────────────
        if c.time_from:
            t_from = _to_time(c.time_from)
            if t_from and (start is None or start < t_from):
                return False

        # ── Avoid start times ────────────────────────────────────────────────
        for avoid_t in c.avoid_start_times:
            t = _to_time(avoid_t)
            if t and start == t:
                return False

        # ── Avoid end times ──────────────────────────────────────────────────
        for avoid_t in c.avoid_end_times:
            t = _to_time(avoid_t)
            if t and end == t:
                return False

        return True

    def _session_matches(self, start: Optional[dtime], session: str) -> bool:
        if start is None:
            return True
        if session == "morning":
            return start < self.MORNING_END
        if session == "afternoon":
            return start >= self.AFTERNOON_START
        return True

    # ── DB helpers ────────────────────────────────────────────────────────────

    def _fetch_reg_counts(self, class_ids: List[int]) -> Dict[int, int]:
        if not class_ids:
            return {}
        rows = (
            self.db.query(ClassRegister.class_id, func.count(ClassRegister.id))
            .filter(ClassRegister.class_id.in_(class_ids))
            .group_by(ClassRegister.class_id)
            .all()
        )
        return {r[0]: r[1] for r in rows}
