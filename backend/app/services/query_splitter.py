"""
Query Splitter – Rule-based Compound Query Decomposer

Tách câu hỏi phức hợp (compound query) thành các sub-query đơn lẻ dựa trên:
1. Phát hiện nhiều intent markers khác nhau trong cùng 1 câu
2. Tìm vị trí conjunction nằm giữa hai vùng có intent khác nhau
3. Chỉ tách khi 2 phía có dominant intent KHÁC NHAU

Ví dụ:
  "xem điểm các môn trượt, và gợi ý đăng ký học lại ưu tiên lịch 2-4-6"
  → SubQuery("xem điểm các môn trượt")          intent=learned_subjects_view
  → SubQuery("gợi ý đăng ký học lại ưu tiên 2-4-6")  intent=class_registration_suggestion

Không tách khi cùng intent:
  "thông tin lớp MI1114 và IT3080"  → 1 sub-query, multi-entity extraction handles it
  "điểm môn IT3080 và IT3081"       → 1 sub-query
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# Intent marker dictionary  (lowercase Vietnamese phrases → intent tag)
# Each entry: phrase → (intent_tag, weight)
# ─────────────────────────────────────────────────────────────────────────────
_MARKERS: Dict[str, Tuple[str, float]] = {
    # grade_view
    "xem điểm":              ("grade_view", 2.0),
    "điểm thi":              ("grade_view", 1.5),
    "điểm số":               ("grade_view", 1.5),
    "điểm các môn":          ("grade_view", 2.0),
    "điểm môn":              ("grade_view", 1.5),
    "kết quả học tập":       ("grade_view", 2.0),
    "kết quả thi":           ("grade_view", 1.5),
    "điểm cpa":              ("grade_view", 2.0),
    "gpa":                   ("grade_view", 2.0),
    "cpa":                   ("grade_view", 2.0),
    "điểm trung bình":       ("grade_view", 2.0),
    "điểm tích lũy":         ("grade_view", 2.0),

    # learned_subjects_view
    "môn trượt":             ("learned_subjects_view", 2.5),
    "môn rớt":               ("learned_subjects_view", 2.5),
    "môn đã học":            ("learned_subjects_view", 2.0),
    "môn đã qua":            ("learned_subjects_view", 2.0),
    "môn chưa qua":          ("learned_subjects_view", 2.0),
    "môn học lại":           ("learned_subjects_view", 2.0),
    "môn nợ":                ("learned_subjects_view", 2.0),
    "kết quả các môn":       ("learned_subjects_view", 1.5),
    "các môn đã đăng ký":    ("learned_subjects_view", 1.5),

    # subject_info
    "thông tin môn":         ("subject_info", 2.0),
    "thông tin học phần":    ("subject_info", 2.0),
    "mô tả môn":             ("subject_info", 1.5),
    "số tín chỉ":            ("subject_info", 1.0),
    "tín chỉ môn":           ("subject_info", 1.5),

    # class_info
    "thông tin lớp":         ("class_info", 2.0),
    "các lớp":               ("class_info", 1.5),
    "danh sách lớp":         ("class_info", 2.0),
    "lịch lớp":              ("class_info", 1.5),
    "lớp học của môn":       ("class_info", 2.0),

    # schedule_view (student's own registered schedule)
    "thời khóa biểu":        ("schedule_view", 2.5),
    "tkb của tôi":           ("schedule_view", 2.5),
    "lịch học của tôi":      ("schedule_view", 2.5),
    "lịch của tôi":          ("schedule_view", 2.0),
    "môn đã đăng ký":        ("schedule_view", 2.0),
    "lớp đã đăng ký":        ("schedule_view", 2.0),

    # subject_registration_suggestion
    "gợi ý môn":             ("subject_registration_suggestion", 2.5),
    "nên học môn nào":       ("subject_registration_suggestion", 2.5),
    "môn nào nên học":       ("subject_registration_suggestion", 2.5),
    "môn phù hợp":           ("subject_registration_suggestion", 2.0),
    "đề xuất môn":           ("subject_registration_suggestion", 2.0),
    "học kỳ này học gì":     ("subject_registration_suggestion", 2.5),

    # class_registration_suggestion
    "gợi ý lớp":             ("class_registration_suggestion", 2.5),
    "gợi ý đăng ký lớp":    ("class_registration_suggestion", 3.0),
    "gợi ý đăng ký":        ("class_registration_suggestion", 2.5),
    "đăng ký lớp nào":      ("class_registration_suggestion", 2.5),
    "lớp nào phù hợp":      ("class_registration_suggestion", 2.0),
    "lớp phù hợp":          ("class_registration_suggestion", 2.0),
    "học lại":               ("class_registration_suggestion", 2.0),
    "học lại môn":           ("class_registration_suggestion", 2.5),
    "ưu tiên lịch":          ("class_registration_suggestion", 2.0),
    "sắp xếp lịch":          ("class_registration_suggestion", 2.0),
    "thời gian học":         ("class_registration_suggestion", 1.0),
}

# Conjunctions that can be split points — ordered longest first to avoid sub-match
_SPLIT_CONJUNCTIONS = [
    ", ngoài ra",
    "ngoài ra",
    ", thêm nữa",
    "thêm nữa",
    ", đồng thời",
    "đồng thời",
    ", và",
    " và ",
    "; ",
    ", còn",
    " còn ",
]

# Minimum marker score each side needs before we consider a split
_MIN_SIDE_SCORE = 1.0


# ─────────────────────────────────────────────────────────────────────────────
# Data model
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SubQuery:
    text: str
    detected_intent: Optional[str] = None   # best-guess (may be None)
    intent_score: float = 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Splitter
# ─────────────────────────────────────────────────────────────────────────────

class QuerySplitter:
    """
    Rule-based compound query splitter.

    Usage:
        splitter = QuerySplitter()
        parts = splitter.split("xem điểm môn trượt, và gợi ý lớp học lại")
        # → [SubQuery("xem điểm môn trượt"), SubQuery("gợi ý lớp học lại")]
    """

    def __init__(self):
        # Pre-compile sorted patterns (longest match first)
        sorted_markers = sorted(_MARKERS.keys(), key=len, reverse=True)
        self._marker_re = re.compile(
            '|'.join(re.escape(m) for m in sorted_markers),
            re.IGNORECASE,
        )

    # ── Public ────────────────────────────────────────────────────────────────

    def split(self, text: str) -> List[SubQuery]:
        """
        Split *text* into sub-queries.

        Returns a list with always ≥1 element.
        If no valid split point found → returns [SubQuery(text)].
        """
        text = text.strip()
        lower = text.lower()

        # Extract distinct intents that appear in the whole text
        global_scores = self._score_intents(lower)
        distinct_intents = [i for i, s in global_scores.items() if s >= _MIN_SIDE_SCORE]

        # Try each conjunction from left to right, pick first valid split
        candidates: List[Tuple[int, int, str]] = []  # (start, end, conj)
        for conj in _SPLIT_CONJUNCTIONS:
            idx = lower.find(conj)
            while idx != -1:
                candidates.append((idx, idx + len(conj), conj))
                idx = lower.find(conj, idx + 1)

        # Sort candidates by position
        candidates.sort(key=lambda x: x[0])

        # For each candidate position, check if left/right have different dominant intents
        parts: List[SubQuery] = []
        remaining = text
        remaining_lower = lower
        offset = 0

        for start, end, conj in candidates:
            # Adjust for already-consumed prefix
            adj_start = start - offset
            adj_end   = end   - offset
            if adj_start <= 0 or adj_end >= len(remaining):
                continue

            left_text  = remaining[:adj_start].strip()
            right_text = remaining[adj_end:].strip()

            if not left_text or not right_text:
                continue

            left_intent  = self._dominant_intent(left_text.lower())
            right_intent = self._dominant_intent(right_text.lower())

            # Valid split: both sides have markers
            if (left_intent is not None and right_intent is not None):
                parts.append(SubQuery(
                    text=left_text,
                    detected_intent=left_intent,
                    intent_score=self._score_intents(left_text.lower()).get(left_intent, 0),
                ))
                # Continue searching in the right part
                remaining = right_text
                remaining_lower = right_text.lower()
                offset = end  # track absolute offset for remaining candidates
                # Restart scan on the remaining segment
                break

        # Add whatever is left
        if remaining.strip():
            rem_intent = self._dominant_intent(remaining_lower)
            parts.append(SubQuery(
                text=remaining.strip(),
                detected_intent=rem_intent,
                intent_score=self._score_intents(remaining_lower).get(rem_intent, 0) if rem_intent else 0,
            ))

        # If we never split (no valid boundary), return original
        if len(parts) <= 1:
            best = distinct_intents[0] if distinct_intents else None
            return [SubQuery(text, detected_intent=best,
                             intent_score=global_scores.get(best, 0) if best else 0)]

        return parts

    # ── Internal ──────────────────────────────────────────────────────────────

    def _score_intents(self, lower_text: str) -> Dict[str, float]:
        """Return {intent: cumulative_weight} for all markers found."""
        scores: Dict[str, float] = {}
        for match in self._marker_re.finditer(lower_text):
            phrase = match.group(0).lower()
            intent, weight = _MARKERS.get(phrase, (None, 0))
            if intent:
                scores[intent] = scores.get(intent, 0) + weight
        return scores

    def _dominant_intent(self, lower_text: str) -> Optional[str]:
        """Return the highest-scoring intent in *lower_text*, or None."""
        scores = self._score_intents(lower_text)
        if not scores:
            return None
        best = max(scores, key=lambda k: scores[k])
        return best if scores[best] >= _MIN_SIDE_SCORE else None


# ─────────────────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────────────────

_splitter_instance: Optional[QuerySplitter] = None


def get_query_splitter() -> QuerySplitter:
    global _splitter_instance
    if _splitter_instance is None:
        _splitter_instance = QuerySplitter()
    return _splitter_instance
