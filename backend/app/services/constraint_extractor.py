"""
Constraint Extractor – Rule-based + Regex parser for Vietnamese class/subject queries.

Chuyển câu hỏi tiếng Việt thành ClassQueryConstraints (Pydantic model),
dùng làm ngôn ngữ trung gian cho ClassQueryService và ScheduleOptimizer.

Ví dụ:
    "các lớp MI1114 học vào thứ 2"
    → ClassQueryConstraints(subject_codes=["MI1114"], days=["Monday"])

    "lớp bóng đá, cầu lông, hoặc bóng bàn học vào thứ 3,4,5 buổi sáng từ 9h"
    → ClassQueryConstraints(subject_names=["bóng đá","cầu lông","bóng bàn"],
                             subject_logic="OR", days=["Tuesday","Wednesday","Thursday"],
                             session="morning", time_from="09:00")
"""
from __future__ import annotations
import re
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


# ──────────────────────────────────────────────────────────────────────────────
# Mappings
# ──────────────────────────────────────────────────────────────────────────────

DAY_MAP: Dict[str, str] = {
    "thứ 2":   "Monday",
    "thứ hai": "Monday",
    "t2":      "Monday",
    "thứ 3":   "Tuesday",
    "thứ ba":  "Tuesday",
    "t3":      "Tuesday",
    "thứ 4":   "Wednesday",
    "thứ tư":  "Wednesday",
    "t4":      "Wednesday",
    "thứ 5":   "Thursday",
    "thứ năm": "Thursday",
    "t5":      "Thursday",
    "thứ 6":   "Friday",
    "thứ sáu": "Friday",
    "t6":      "Friday",
    "thứ 7":   "Saturday",
    "thứ bảy": "Saturday",
    "t7":      "Saturday",
    "chủ nhật":"Sunday",
    "cn":      "Sunday",
}

# Keywords that indicate "physical education / thể thao" subjects
PE_KEYWORDS = {
    "thể": "Giáo dục thể chất",
    "thể chất": "Giáo dục thể chất",
    "gdtc": "Giáo dục thể chất",
    "bóng đá": "Bóng đá",
    "bóng chuyền": "Bóng chuyền",
    "bóng bàn": "Bóng bàn",
    "cầu lông": "Cầu lông",
    "bơi": "Bơi lội",
    "bơi lội": "Bơi lội",
    "cầu lông": "Cầu lông",
    "bóng rổ": "Bóng rổ",
    "điền kinh": "Điền kinh",
    "thể dục": "Thể dục",
    "võ": "Võ thuật",
    "judo": "Judo",
}

# Keywords that indicate "Marxism / philosophy / triết" subjects
PHIL_KEYWORDS = {
    "triết": "Triết học Mác-Lênin",
    "triết học": "Triết học Mác-Lênin",
    "mác": "Triết học Mác-Lênin",
    "mác lênin": "Triết học Mác-Lênin",
    "chủ nghĩa xã hội": "Chủ nghĩa xã hội khoa học",
    "cnxh": "Chủ nghĩa xã hội khoa học",
    "kinh tế chính trị": "Kinh tế chính trị Mác-Lênin",
    "lịch sử đảng": "Lịch sử Đảng",
}


# ──────────────────────────────────────────────────────────────────────────────
# Output model
# ──────────────────────────────────────────────────────────────────────────────

class DaySessionConstraint(BaseModel):
    """Ràng buộc thứ + buổi cụ thể.  Ví dụ: chiều thứ 2,3,4; sáng thứ 3,5,6"""
    days: List[str] = Field(default_factory=list)   # ["Monday","Tuesday"]
    session: Optional[str] = None                    # "morning"|"afternoon"|None


class ClassQueryConstraints(BaseModel):
    """
    Cấu trúc ràng buộc truy vấn lớp học đã được chuẩn hóa.
    Dùng làm ngôn ngữ trung gian giữa NL → DB query / optimizer.
    """

    # ── Entity filters ──────────────────────────────────────────────────────
    subject_codes: List[str] = Field(default_factory=list)
    # Mã môn đã resolve (e.g. "MI1114").  Điền sau fuzzy-match.
    resolved_subject_ids: List[str] = Field(default_factory=list)

    # Raw subject name fragments for fuzzy matching
    subject_names: List[str] = Field(default_factory=list)

    # Direct class-table filters (for class_info)
    class_ids: List[str] = Field(default_factory=list)
    class_names: List[str] = Field(default_factory=list)
    subject_ids: List[int] = Field(default_factory=list)

    # OR or AND between multiple entries in subject_codes/names
    subject_logic: str = "OR"   # "OR" | "AND"

    # Semester filter: "current" | None
    semester: Optional[str] = None

    # ── Time filters (global, apply to all days) ────────────────────────────
    days: List[str] = Field(default_factory=list)           # ["Monday","Tuesday"]
    session: Optional[str] = None                           # "morning"|"afternoon"
    start_time_exact: Optional[str] = None                  # "08:25"
    end_time_exact: Optional[str] = None                    # "10:15"
    time_from: Optional[str] = None                         # "09:00" (>= from)
    time_until: Optional[str] = None                        # "11:45" (<= until)
    time_range: Optional[Tuple[str, str]] = None            # ("08:25","10:15")

    # ── Classroom filters (classroom format: "D9-401") ──────────────────
    classroom_exact: Optional[str] = None                   # "D9-401"
    building_code: Optional[str] = None                     # "D9"
    room_code: Optional[str] = None                         # "401"

    # Per-session-per-day constraints (parsed from "chiều thứ 2,3,4 và sáng thứ 3,5,6")
    day_session_constraints: List[DaySessionConstraint] = Field(default_factory=list)

    # ── Hard constraints (class_registration_suggestion) ───────────────────
    avoid_start_times: List[str] = Field(default_factory=list)   # ["06:45","17:30"]
    avoid_end_times: List[str] = Field(default_factory=list)
    must_include_subject_names: List[str] = Field(default_factory=list)
    # courses explicitly required in schedule (by subject_name fragment)
    must_include_subject_codes: List[str] = Field(default_factory=list)

    max_gap_minutes: Optional[int] = None      # max idle gap between classes on same day
    min_periods_per_day: Optional[int] = None  # min teaching periods per study day
    max_daily_hours: Optional[float] = None

    # ── Soft preferences ────────────────────────────────────────────────────
    prefer_start_times: List[str] = Field(default_factory=list)  # ["10:15"]
    prefer_free_days: bool = False
    prefer_continuous: bool = False

    # ── Query type ──────────────────────────────────────────────────────────
    # "class_info" → just list classes
    # "class_registration_suggestion" → full optimization
    query_type: str = "class_info"


# ──────────────────────────────────────────────────────────────────────────────
# Parser
# ──────────────────────────────────────────────────────────────────────────────

class ConstraintExtractor:
    """
    Rule-based + regex extractor: Vietnamese text → ClassQueryConstraints.

    Không dùng model, không tốn phí API.  Covers ~90% câu hỏi thực tế.
    """

    # ── compiled regex patterns ─────────────────────────────────────────────
    _RE_SUBJECT_CODE = re.compile(r'\b([A-Z]{2,4}\d{3,5}[A-Z]?)\b')

    # Time patterns: "8h25", "08:25", "8h", "8g25", "8 giờ 25"
    _RE_TIME = re.compile(
        r'\b(\d{1,2})'
        r'(?:[hgH:](\d{2})?)?'
        r'(?:\s*(?:giờ|h|g)\s*(\d{2}))?'
        r'\b'
    )
    _RE_TIME_STRICT = re.compile(
        r'(\d{1,2})[hgH:](\d{2})?(?:\s*(?:phút|p))?'
    )
    _RE_TIME_RANGE = re.compile(
        r'(\d{1,2}[hg:]\d{0,2})\s*(?:đến|tới|-)\s*(\d{1,2}[hg:]\d{0,2})'
    )
    _RE_GAP = re.compile(r'(?:khoảng cách|nghỉ|gap)[^0-9]*(\d+)\s*(?:phút|p|min)')
    _RE_MIN_PERIODS = re.compile(r'(?:ít nhất|tối thiểu|không ít hơn|dưới)\s*(\d+)\s*(?:tiết|buổi|lớp)')
    _RE_MAX_GAP_GENERIC = re.compile(r'không\s+(?:quá|hơn)\s+(\d+)\s*(?:phút|p|min)')

    def __init__(self):
        # Build compiled day pattern sorted longest-first to avoid partial match
        day_keys = sorted(DAY_MAP.keys(), key=len, reverse=True)
        pattern = '|'.join(re.escape(k) for k in day_keys)
        self._re_day = re.compile(f'({pattern})', re.IGNORECASE)

        # Build list of PE / phil keyword patterns
        self._pe_re = re.compile(
            '|'.join(re.escape(k) for k in sorted(PE_KEYWORDS.keys(), key=len, reverse=True)),
            re.IGNORECASE
        )
        self._phil_re = re.compile(
            '|'.join(re.escape(k) for k in sorted(PHIL_KEYWORDS.keys(), key=len, reverse=True)),
            re.IGNORECASE
        )

    # ── Public API ──────────────────────────────────────────────────────────

    def extract(self, text: str, query_type: str = "class_info") -> ClassQueryConstraints:
        """
        Main entry point.  Returns ClassQueryConstraints from text.
        """
        c = ClassQueryConstraints(query_type=query_type)
        text_lower = text.lower().strip()

        # 1. Subject codes (regex)
        c.subject_codes = self._extract_subject_codes(text)

        # 2. Subject name fragments (NL keywords → candidates for fuzzy)
        c.subject_names, c.subject_logic = self._extract_subject_names(text, text_lower, c.subject_codes)

        # 2.1 Direct class-table filters (class_id/class_name/subject_id)
        c.class_ids, c.class_names, c.subject_ids = self._extract_class_table_filters(text, text_lower)

        # 3. Semester
        if re.search(r'\bkỳ này\b|\bhiện tại\b|\bkỳ hiện\b', text_lower):
            c.semester = "current"

        # 4. Days + session (handles complex "chiều thứ 2,3,4 và sáng thứ 3,5,6")
        c.day_session_constraints = self._extract_day_session_groups(text_lower)

        # Flatten: if only one group with no session conflict → fill top-level fields
        all_days: List[str] = []
        sessions_seen = set()
        for dsc in c.day_session_constraints:
            all_days.extend(dsc.days)
            if dsc.session:
                sessions_seen.add(dsc.session)
        c.days = list(dict.fromkeys(all_days))   # deduplicate preserving order

        if len(sessions_seen) == 1:
            c.session = sessions_seen.pop()
        # If multiple sessions, keep day_session_constraints and leave c.session=None

        # 5. Exact/range times
        c.start_time_exact, c.end_time_exact = self._extract_exact_times(text_lower)
        c.time_range = self._extract_time_range(text_lower)
        c.time_from = self._extract_time_from(text_lower)

        # 5.1 Classroom filters (tòa/phòng)
        c.classroom_exact, c.building_code, c.room_code = self._extract_classroom_filters(text_lower)

        # 6. Avoid times (không học lúc 6h45, không kết thúc lúc 17h30)
        c.avoid_start_times, c.avoid_end_times = self._extract_avoid_times(text_lower)

        # 7. Must-include subjects (phải có lớp X)
        must_names, must_codes = self._extract_must_include(text_lower)
        c.must_include_subject_names = must_names
        c.must_include_subject_codes = must_codes

        # 8. Gap / period constraints
        c.max_gap_minutes = self._extract_max_gap(text_lower)
        c.min_periods_per_day = self._extract_min_periods(text_lower)

        # 9. Soft preferences
        c.prefer_start_times = self._extract_prefer_start_times(text_lower)
        c.prefer_free_days = bool(re.search(r'ngày nghỉ|ngày tự do|tối đa.*nghỉ', text_lower))
        c.prefer_continuous = bool(re.search(r'học liên tục|liên tục|học dồn', text_lower))

        return c

    # ── Private helpers ─────────────────────────────────────────────────────

    def _extract_subject_codes(self, text: str) -> List[str]:
        """Extract subject codes like IT3080, MI1114."""
        return list(dict.fromkeys(self._RE_SUBJECT_CODE.findall(text.upper())))

    def _extract_subject_names(
        self, text: str, text_lower: str, existing_codes: List[str]
    ) -> Tuple[List[str], str]:
        """
        Extract subject name fragments for fuzzy matching.
        Returns (names, logic)  where logic is "OR" or "AND".

        Strategy:
        1. Check PE keywords (bóng đá, thể, cầu lông…)
        2. Check philosophy keywords (triết…)
        3. Detect subject name after "môn", "lớp", "học phần" keywords
        4. Determine OR/AND logic
        """
        names: List[str] = []

        # -- Special domain shortcuts
        for m in self._pe_re.finditer(text_lower):
            kw = m.group(0).lower()
            canonical = PE_KEYWORDS.get(kw, kw)
            if canonical not in names:
                names.append(canonical)

        for m in self._phil_re.finditer(text_lower):
            kw = m.group(0).lower()
            canonical = PHIL_KEYWORDS.get(kw, kw)
            if canonical not in names:
                names.append(canonical)

        # -- General: extract phrase after "môn"/"lớp"/"học phần"
        # Only if no code was extracted and no domain keyword matched
        if not existing_codes and not names:
            candidates: List[str] = []

            # Priority pattern: explicit multi-list for same intent
            list_patterns = [
                r'(?:điểm\s+các\s+môn|điểm\s+môn|xem\s+điểm\s+các\s+môn|xem\s+điểm\s+môn)\s+([^\?\.\n]+)',
                r'(?:các\s+lớp\s+của\s+các\s+môn|các\s+lớp\s+của\s+môn|các\s+lớp\s+môn|thông\s+tin\s+các\s+lớp\s+môn|danh\s+sách\s+các\s+lớp\s+môn)\s+([^\?\.\n]+)',
                r'(?:môn|học\s+phần|lớp)\s+([^\?\.\n]+)',
            ]

            for pat in list_patterns:
                m = re.search(pat, text_lower)
                if not m:
                    continue
                tail = m.group(1).strip()
                tail = re.split(
                    r'\b(?:học\s+vào|học\s+ở|ở\s+[a-z]\d{0,2}(?:\s*[-\s]\s*\d{2,4})?|ở\s+tòa|ở\s+phòng|vào\s+thứ|thứ\s+\d|thứ\s+(?:hai|ba|tư|năm|sáu|bảy)|chủ\s+nhật|buổi|lúc|bắt\s+đầu|kết\s+thúc|tan\s+học|thời\s+gian|từ\s+\d|đến\s+\d|phòng\s+\d{2,4}|tòa\s+[a-z]\d*)\b',
                    tail,
                    maxsplit=1,
                )[0].strip()

                # Remove trailing punctuation / connectors after cut.
                tail = re.sub(r'[\s,;:\-]+$', '', tail).strip()
                tail = re.sub(r'\s+(?:học|xem|tìm)$', '', tail).strip()
                candidates = [
                    re.sub(r'^(?:môn|học\s+phần|lớp|các\s+môn|các\s+lớp|của)\s+', '', p.strip())
                    for p in re.split(r'[;,]|\s+và\s+|\s+hoặc\s+', tail)
                    if p.strip()
                ]
                if candidates:
                    break

            # Fallback legacy behavior if no candidate found above
            if not candidates:
                patterns = [
                    r'(?:môn|học phần)\s+(?:học\s+)?([^\?,\.\n]+?)(?:\s+học\s+|\s+vào\s+|$)',
                    r'lớp\s+(?:học\s+)?([^\?,\.\n]+?)(?:\s+học\s+|\s+vào\s+|$)',
                ]
                for pat in patterns:
                    m = re.search(pat, text_lower)
                    if m:
                        candidates = [m.group(1).strip()]
                        break

            for candidate in candidates:
                if not candidate:
                    continue
                candidate = candidate.strip()

                # Skip generic / noise fragments that are not subject names
                if candidate in {"học", "lớp", "môn", "học phần", "thông tin"}:
                    continue
                # Likely class_id token, not a subject name (e.g. 762021, C12345)
                if re.match(r'^[a-z]?\d{4,}$', candidate, re.IGNORECASE):
                    continue
                if re.match(r'^(?:ở|phòng|phong|tòa|toa)\b', candidate):
                    continue
                if re.search(r'\b(?:thời gian|bắt đầu|kết thúc|lúc\s+\d|\d{1,2}[hg:]\d{0,2})\b', candidate):
                    continue

                # filter out day tokens
                if self._re_day.search(candidate):
                    continue
                if candidate not in names:
                    names.append(candidate)

        # -- Multi-subject: split by comma/và/hoặc
        # Also handle inline lists like "bóng đá, cầu lông, bóng bàn"
        # (already captured above via PE_KEYWORDS)

        # Determine logic
        logic = "OR" if re.search(r'\bhoặc\b', text_lower) else "AND"

        return names, logic

    def _extract_class_table_filters(self, text: str, text_lower: str) -> Tuple[List[str], List[str], List[int]]:
        """
        Extract direct filters for classes table:
        - class_id: 'lớp 762021', 'class_id 762021', 'mã lớp 762021'
        - class_name: 'class_name ...', 'tên lớp ...'
        - subject_id: 'subject_id 123', 'id học phần 123'
        """
        class_ids: List[str] = []
        class_names: List[str] = []
        subject_ids: List[int] = []

        # class_id via explicit labels
        for m in re.finditer(r'(?:class[_\s-]*id|mã\s+lớp)\s*[:#-]?\s*([a-z0-9_-]{2,})', text, re.IGNORECASE):
            val = m.group(1).strip().upper()
            if val and val not in class_ids:
                class_ids.append(val)

        # class_id via natural phrase: "lớp 762021" or "lớp C12345"
        for m in re.finditer(r'\blớp\s+([a-z]?\d{4,}|[a-z]{1,3}\d{3,})\b', text_lower, re.IGNORECASE):
            val = m.group(1).strip().upper()
            if val and val not in class_ids:
                class_ids.append(val)

        # class_name via explicit labels
        for m in re.finditer(r'(?:class[_\s-]*name|tên\s+lớp)\s*[:#-]?\s*([^\?\n\.]+)', text, re.IGNORECASE):
            name = m.group(1).strip(" ,;:-")
            if name and name.lower() not in {"lớp", "class", "name"} and name not in class_names:
                class_names.append(name)

        # subject_id in classes table (integer FK)
        for m in re.finditer(r'(?:subject[_\s-]*id|id\s*học\s*phần|id\s*môn)\s*[:#-]?\s*(\d+)', text_lower, re.IGNORECASE):
            sid = int(m.group(1))
            if sid not in subject_ids:
                subject_ids.append(sid)

        return class_ids, class_names, subject_ids

    def _extract_day_session_groups(self, text: str) -> List[DaySessionConstraint]:
        """
        Parse complex day+session phrases like:
            "chiều thứ 2,3,4 và sáng thứ 3,5,6"
            "thứ 2 và thứ 4"
            "thứ 3,4,5 buổi sáng"

        Returns list of DaySessionConstraint.
        """
        groups: List[DaySessionConstraint] = []

        # Pattern 1: "(buổi)? sáng/chiều thứ N1,N2,N3 (và ...)"
        session_patterns = [
            # "chiều thứ 2,3,4" or "buổi sáng thứ 2 và thứ 4"
            r'(sáng|chiều|buổi\s+sáng|buổi\s+chiều)\s+([thứ\s\d,và]+)',
            # "thứ 2,3,4 buổi sáng"
            r'([thứ\s\d,và]+)\s+(sáng|chiều|buổi\s+sáng|buổi\s+chiều)',
        ]

        consumed_spans: list = []

        for pattern in session_patterns:
            for m in re.finditer(pattern, text, re.IGNORECASE):
                # Avoid re-using the same span
                if any(m.start() < e and m.end() > s for s, e in consumed_spans):
                    continue

                raw1, raw2 = m.group(1).strip(), m.group(2).strip()
                # Determine which group is session and which is days
                session_raw = raw1 if re.search(r'sáng|chiều', raw1) else raw2
                days_raw    = raw2 if re.search(r'sáng|chiều', raw1) else raw1

                session = self._session_from_raw(session_raw)
                days    = self._parse_days_from_raw(days_raw)

                if days:
                    groups.append(DaySessionConstraint(days=days, session=session))
                    consumed_spans.append((m.start(), m.end()))

        # Pattern 2: plain day list (no session)
        if not groups:
            days = self._parse_days_from_raw(text)
            session = self._single_session(text)
            if days:
                groups.append(DaySessionConstraint(days=days, session=session))

        # Fallback: no days found at all, but session mentioned
        if not groups:
            session = self._single_session(text)
            if session:
                groups.append(DaySessionConstraint(days=[], session=session))

        return groups

    def _session_from_raw(self, raw: str) -> Optional[str]:
        raw = raw.lower()
        if 'sáng' in raw:
            return 'morning'
        if 'chiều' in raw:
            return 'afternoon'
        return None

    def _single_session(self, text: str) -> Optional[str]:
        if re.search(r'\bsáng\b', text):
            return 'morning'
        if re.search(r'\bchiều\b', text):
            return 'afternoon'
        return None

    def _parse_days_from_raw(self, raw: str) -> List[str]:
        """Extract distinct English day names from a raw Vietnamese substring."""
        days: List[str] = []
        # 1. Detect "thứ N,M,K" patterns first
        # e.g. "thứ 2,3,4" or "thứ 2 và thứ 4"
        chunk_pattern = re.compile(
            r'thứ\s+(\d(?:\s*[,và]\s*\d)*)',
            re.IGNORECASE
        )
        for m in chunk_pattern.finditer(raw):
            digits = re.findall(r'\d', m.group(0))
            for d in digits:
                day = self._digit_to_day(d)
                if day and day not in days:
                    days.append(day)

        # 2. Named days (thứ hai, thứ ba…)
        for m in self._re_day.finditer(raw):
            key = m.group(0).lower()
            day = DAY_MAP.get(key)
            if day and day not in days:
                days.append(day)

        return days

    def _digit_to_day(self, digit: str) -> Optional[str]:
        mapping = {
            '2': 'Monday', '3': 'Tuesday', '4': 'Wednesday',
            '5': 'Thursday', '6': 'Friday', '7': 'Saturday', '8': 'Sunday'
        }
        return mapping.get(digit)

    def _parse_time_str(self, raw: str) -> Optional[str]:
        """
        Convert "8h25", "8:25", "8h", "8g25", "10h15" → "08:25" / "10:15"
        """
        return self._extract_time_from_raw(raw)

    def _normalize_time_hhmm(self, hour: int, minute: int) -> Optional[str]:
        """
        Normalize to HH:MM and apply business rule:
        - Inputs in 00:00..06:59 are interpreted as afternoon (add 12 hours).

        Examples:
            8h25   -> 08:25
            9h15   -> 09:15
            4h     -> 16:00
            3h20   -> 15:20
            10:12  -> 10:12
        """
        if minute < 0 or minute > 59:
            return None

        # Convert 00:00..06:00 to PM for class queries (user shorthand).
        # Keep 06:01+ as morning to avoid breaking real early classes (e.g. 06:45).
        if 0 <= hour < 6 or (hour == 6 and minute == 0):
            hour += 12

        if hour < 0 or hour > 23:
            return None

        return f"{hour:02d}:{minute:02d}"

    def _extract_time_from_raw(self, raw: str) -> Optional[str]:
        """Extract a time token and convert."""
        raw = raw.strip()
        m = self._RE_TIME_STRICT.search(raw)
        if not m:
            return None

        h = int(m.group(1))
        mn = int(m.group(2)) if m.group(2) else 0
        return self._normalize_time_hhmm(h, mn)

    def _extract_exact_times(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract start/end times from phrases like:
            "lúc 8h25"  → start="08:25"
            "từ 8h25 đến 10h15" → handled by time_range
            "8h25 đến 10h15"    → handled by time_range
        Returns (start_time_exact, end_time_exact)
        """
        start_t = None
        end_t   = None

        # "lúc X" or "vào X" or "bắt đầu lúc X" or "thời gian bắt đầu X"
        for m in re.finditer(
            r'(?:lúc|vào lúc|học lúc|học vào lúc|bắt đầu|bắt đầu lúc|bắt đầu vào|thời gian bắt đầu(?:\s+lúc)?)\s+(\d{1,2}[hg:]\d{0,2})',
            text
        ):
            # Skip "kết thúc lúc X" so it won't be treated as start time.
            prev_context = text[max(0, m.start() - 20):m.start()]
            if re.search(r'kết\s+thúc\s*$', prev_context):
                continue
            t = self._extract_time_from_raw(m.group(1))
            if t and start_t is None:
                start_t = t

        # "kết thúc lúc X" / "đến X" / "thời gian kết thúc X"
        for m in re.finditer(
            r'(?:kết thúc|kết thúc lúc|kết thúc vào|tan lúc|học đến|thời gian kết thúc(?:\s+lúc)?|đến lúc|đến)\s+(\d{1,2}[hg:]\d{0,2})',
            text
        ):
            t = self._extract_time_from_raw(m.group(1))
            if t and end_t is None:
                end_t = t

        return start_t, end_t

    def _extract_classroom_filters(self, text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extract classroom constraints from phrases like:
            "học ở C7-114", "ở D9 401", "tòa D9", "phòng 402"
        Returns: (classroom_exact, building_code, room_code)
        """
        classroom_exact: Optional[str] = None
        building_code: Optional[str] = None
        room_code: Optional[str] = None

        # Exact classroom format with dash/space: D9-401 / D9 401 / C7-114
        exact = re.search(r'\b([a-z]\d{0,2})\s*[-\s]\s*(\d{2,4})\b', text, re.IGNORECASE)
        if exact:
            building_code = exact.group(1).upper()
            room_code = exact.group(2)
            classroom_exact = f"{building_code}-{room_code}"
            return classroom_exact, building_code, room_code

        # Building only: tòa D9 / toa D9
        b_match = re.search(r'(?:tòa|toa)\s+([a-z]\d{0,2})\b', text, re.IGNORECASE)
        if b_match:
            building_code = b_match.group(1).upper()

        # Room only: phòng 402 / phong 402
        r_match = re.search(r'(?:phòng|phong)\s+(\d{2,4})\b', text, re.IGNORECASE)
        if r_match:
            room_code = r_match.group(1)

        # Fallback: "ở D9" without keyword tòa
        if not building_code:
            b_fallback = re.search(r'\bở\s+([a-z]\d{0,2})\b', text, re.IGNORECASE)
            if b_fallback:
                building_code = b_fallback.group(1).upper()

        return classroom_exact, building_code, room_code

    def _extract_time_range(self, text: str) -> Optional[Tuple[str, str]]:
        """Extract "8h25 đến 10h15" → ("08:25","10:15")."""
        m = self._RE_TIME_RANGE.search(text)
        if m:
            t1 = self._extract_time_from_raw(m.group(1))
            t2 = self._extract_time_from_raw(m.group(2))
            if t1 and t2:
                return (t1, t2)
        return None

    def _extract_time_from(self, text: str) -> Optional[str]:
        """Extract "từ 9h" / "từ 9h30" → "09:00"."""
        m = re.search(r'từ\s+(\d{1,2}[hg:]\d{0,2})', text)
        if m:
            return self._extract_time_from_raw(m.group(1))
        return None

    def _extract_avoid_times(self, text: str) -> Tuple[List[str], List[str]]:
        """
        Extract times to avoid:
            "không học lớp bắt đầu lúc 6h45" → avoid_start=["06:45"]
            "không học lớp kết thúc lúc 17h30" → avoid_end=["17:30"]
            "không học lớp kết thúc lúc 5h30" → avoid_end=["05:30"]
        """
        avoid_start: List[str] = []
        avoid_end:   List[str] = []

        start_pats = [
            r'không\s+(?:học\s+)?(?:lớp\s+)?bắt\s+đầu\s+(?:lúc\s+)?(\d{1,2}[hg:]\d{0,2})',
            r'tránh\s+(?:lớp\s+)?bắt\s+đầu\s+(?:lúc\s+)?(\d{1,2}[hg:]\d{0,2})',
            r'không\s+bắt\s+đầu\s+(?:lúc\s+)?(\d{1,2}[hg:]\d{0,2})',
        ]
        end_pats = [
            r'không\s+(?:học\s+)?(?:lớp\s+)?kết\s+thúc\s+(?:lúc\s+)?(\d{1,2}[hg:]\d{0,2})',
            r'tránh\s+(?:lớp\s+)?kết\s+thúc\s+(?:lúc\s+)?(\d{1,2}[hg:]\d{0,2})',
            r'không\s+kết\s+thúc\s+(?:lúc\s+)?(\d{1,2}[hg:]\d{0,2})',
            r'không\s+học\s+đến\s+(\d{1,2}[hg:]\d{0,2})',
        ]

        for pat in start_pats:
            for m in re.finditer(pat, text, re.IGNORECASE):
                t = self._extract_time_from_raw(m.group(1))
                if t and t not in avoid_start:
                    avoid_start.append(t)

        for pat in end_pats:
            for m in re.finditer(pat, text, re.IGNORECASE):
                t = self._extract_time_from_raw(m.group(1))
                if t and t not in avoid_end:
                    avoid_end.append(t)

        return avoid_start, avoid_end

    def _extract_must_include(self, text: str) -> Tuple[List[str], List[str]]:
        """
        Extract must-have subjects:
            "phải có lớp bóng đá"  → names=["Bóng đá"]
            "bắt buộc có IT3080"   → codes=["IT3080"]
        """
        names: List[str] = []
        codes: List[str] = []

        patterns = [
            r'(?:phải có|bắt buộc có|bắt buộc đăng ký|phải đăng ký)\s+(?:lớp\s+|môn\s+)?(.+?)(?:\s*,|\s*\.|$)',
        ]
        for pat in patterns:
            for m in re.finditer(pat, text, re.IGNORECASE):
                fragment = m.group(1).strip()
                # Check if it's a subject code
                code_m = self._RE_SUBJECT_CODE.match(fragment.upper())
                if code_m:
                    codes.append(code_m.group(1))
                else:
                    # Look for PE / special keywords
                    found = False
                    for kw, canonical in PE_KEYWORDS.items():
                        if kw in fragment.lower():
                            names.append(canonical)
                            found = True
                            break
                    if not found:
                        for kw, canonical in PHIL_KEYWORDS.items():
                            if kw in fragment.lower():
                                names.append(canonical)
                                found = True
                                break
                    if not found:
                        names.append(fragment)

        return names, codes

    def _extract_max_gap(self, text: str) -> Optional[int]:
        """Extract max gap between consecutive classes (minutes)."""
        for pat in [self._RE_GAP, self._RE_MAX_GAP_GENERIC]:
            m = pat.search(text)
            if m:
                return int(m.group(1))
        return None

    def _extract_min_periods(self, text: str) -> Optional[int]:
        """
        Extract min periods per day.
        'không có hôm nào học dưới 3 tiết' → 3
        """
        # "không ... dưới N tiết"
        m = re.search(
            r'(?:không\s+có\s+hôm\s+nào\s+học\s+dưới|ít nhất|tối thiểu)\s*(\d+)\s*(?:tiết|buổi)',
            text
        )
        if m:
            return int(m.group(1))
        return None

    def _extract_prefer_start_times(self, text: str) -> List[str]:
        """Extract preferred start times: 'ưu tiên học lúc 10h15' → ["10:15"]."""
        times: List[str] = []
        for m in re.finditer(
            r'(?:ưu tiên|thích|muốn)\s+(?:học\s+)?(?:lúc\s+|vào\s+)?(\d{1,2}[hg:]\d{0,2})',
            text
        ):
            t = self._extract_time_from_raw(m.group(1))
            if t and t not in times:
                times.append(t)
        return times


# ──────────────────────────────────────────────────────────────────────────────
# Singleton
# ──────────────────────────────────────────────────────────────────────────────

_extractor: Optional[ConstraintExtractor] = None

def get_constraint_extractor() -> ConstraintExtractor:
    global _extractor
    if _extractor is None:
        _extractor = ConstraintExtractor()
    return _extractor
