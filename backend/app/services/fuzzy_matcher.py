"""
Fuzzy Matching Service for Subject and Class Names
Sử dụng rapidfuzz để tìm môn học / lớp học gần đúng từ input của user

Features:
- Bỏ dấu tiếng Việt trước khi so sánh (giải tích == giai tich)
- Ngưỡng tự động map: score >= AUTO_MAP_THRESHOLD
- Dưới ngưỡng: trả về top-k candidates để hỏi lại
- Cache danh sách từ DB, refresh theo TTL
"""
import unicodedata
import re
from typing import List, Optional, Tuple, Dict, Set
from datetime import datetime, timedelta
from dataclasses import dataclass


# ============================================================
# Thresholds
# ============================================================
AUTO_MAP_THRESHOLD = 80   # score >= 80 → tự động map
SUGGEST_THRESHOLD = 50    # score >= 50 → đưa vào candidates để hỏi lại
TOP_K = 3                 # số candidates trả về khi dưới ngưỡng
CACHE_TTL_MINUTES = 30    # thời gian cache danh sách môn/lớp


@dataclass
class FuzzyMatch:
    """Kết quả một lần fuzzy match"""
    subject_id: str         # mã môn (subject_id), ví dụ IT3080
    subject_name: str       # tên đầy đủ
    score: float            # 0-100
    auto_mapped: bool       # True nếu score >= AUTO_MAP_THRESHOLD


@dataclass
class FuzzyClassMatch:
    """Kết quả fuzzy match cho lớp học"""
    class_id: str
    class_name: str
    subject_id: str
    subject_name: str
    score: float
    auto_mapped: bool


class FuzzyMatcher:
    """
    Fuzzy Matching cho subjects và classes.

    Được khởi tạo với database session, tự load và cache danh sách môn/lớp.

    Usage:
        matcher = FuzzyMatcher(db)
        result = matcher.match_subject("giai tich 1")
        if result.auto_mapped:
            print(f"Tự động map đến: {result.subject_id}")
        else:
            # score thấp, hỏi lại user
            candidates = matcher.get_subject_candidates("giai tich 1")
            ask_user(candidates)
    """

    def __init__(self, db=None):
        """
        Args:
            db: SQLAlchemy Session (optional)
                Nếu None, cache sẽ trống cho đến khi gọi refresh_cache(db)
        """
        # Cache
        self._subjects: List[Tuple[str, str, Set[int]]] = []      # [(subject_id, subject_name, {course_ids})]
        self._subjects_norm: List[Tuple[str, str]] = []  # [(subject_id, normalized_name)]
        self._classes: List[Dict] = []                   # list of class dicts
        self._classes_norm: List[Tuple[str, Dict]] = [] # [(normalized_name, class_dict)]
        self._last_refresh: Optional[datetime] = None

        if db is not None:
            self.refresh_cache(db)

    # ----------------------------------------------------------
    # Cache management
    # ----------------------------------------------------------

    def refresh_cache(self, db) -> None:
        """Load lại danh sách subjects và classes từ DB"""
        try:
            from app.models.subject_model import Subject
            from app.models.class_model import Class
            from app.models.course_subject_model import CourseSubject
            from sqlalchemy.orm import joinedload

            # Load subjects with relation to course_subjects
            sq = (
                db.query(Subject.subject_id, Subject.subject_name, CourseSubject.course_id)
                .outerjoin(CourseSubject, Subject.id == CourseSubject.subject_id)
                .all()
            )
            
            subj_dict = {}
            for sid, sname, cid in sq:
                if sid not in subj_dict:
                    subj_dict[sid] = {"name": sname or '', "courses": set()}
                if cid is not None:
                    subj_dict[sid]["courses"].add(cid)
                    
            self._subjects = []
            for sid, data in subj_dict.items():
                self._subjects.append((sid, data["name"], data["courses"]))
                
            self._subjects_norm = [
                (sid, self._normalize(data["name"]))
                for sid, data in subj_dict.items()
            ]

            # Load classes with subject_name and course_ids join
            classes_rows = (
                db.query(Class, Subject.subject_id, Subject.subject_name, CourseSubject.course_id)
                .join(Subject, Class.subject_id == Subject.id)
                .outerjoin(CourseSubject, Subject.id == CourseSubject.subject_id)
                .all()
            )
            
            cls_dict = {}
            for cls, subj_code, subj_name, course_id in classes_rows:
                if cls.class_id not in cls_dict:
                    cls_dict[cls.class_id] = {
                        "class_id": cls.class_id,
                        "class_name": cls.class_name or '',
                        "subject_id": subj_code,
                        "subject_name": subj_name or '',
                        "course_ids": set()
                    }
                if course_id is not None:
                    cls_dict[cls.class_id]["course_ids"].add(course_id)

            self._classes = list(cls_dict.values())
            self._classes_norm = []
            for cd in self._classes:
                norm_name = self._normalize(cd["class_name"])
                self._classes_norm.append((norm_name, cd))

            self._last_refresh = datetime.now()
            print(f"✅ [FuzzyMatcher] Cache refreshed: {len(self._subjects)} subjects, {len(self._classes)} classes")

        except Exception as e:
            print(f"⚠️ [FuzzyMatcher] Failed to load cache: {e}")

    def _is_cache_stale(self) -> bool:
        if self._last_refresh is None:
            return True
        return datetime.now() - self._last_refresh > timedelta(minutes=CACHE_TTL_MINUTES)

    def ensure_fresh(self, db) -> None:
        """Tự động refresh cache nếu hết TTL"""
        if self._is_cache_stale() and db is not None:
            self.refresh_cache(db)

    # ----------------------------------------------------------
    # Normalization
    # ----------------------------------------------------------

    def _normalize(self, text: str) -> str:
        """
        Chuẩn hóa text để so sánh:
        1. Replace đ/Đ → d (không có combining char trong NFD)
        2. NFD decompose + bỏ combining chars (giải tích → giai tich)
        3. Lowercase
        4. Loại ký tự đặc biệt, giữ chữ cái ASCII và số
        5. Rút gọn khoảng trắng

        Ví dụ:
            "Giải Tích 1"  → "giai tich 1"
            "Đại số"       → "dai so"
            "Cơ sở dữ liệu" → "co so du lieu"
            "lập trình hướng đối tượng" → "lap trinh huong doi tuong"
        """
        if not text:
            return ''

        # Bước 1: Xử lý đặc biệt cho đ/Đ — không có combining char trong NFD
        # nên phải replace thủ công trước
        text = text.replace('đ', 'd').replace('Đ', 'D')

        # Bước 2: NFD decompose → tách base char + combining diacritics
        # Ví dụ: 'ă' → 'a' + combining breve
        text = unicodedata.normalize('NFD', text)

        # Bước 3: Loại bỏ tất cả combining characters (dấu huyền, sắc, nặng, hỏi, ngã,
        # mũ, trăng, breve, horn...) để lấy base characters
        text = ''.join(c for c in text if not unicodedata.combining(c))

        # Bước 4: Lowercase
        text = text.lower()

        # Bước 5: Chỉ giữ chữ ASCII và số, thay phần còn lại bằng space
        text = re.sub(r'[^a-z0-9\s]', ' ', text)

        # Bước 6: Rút gọn whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    # ----------------------------------------------------------
    # Subject matching
    # ----------------------------------------------------------

    def match_subject(
        self,
        query: str,
        db=None,
        threshold: int = AUTO_MAP_THRESHOLD,
        preferred_course_id: Optional[int] = None
    ) -> Optional[FuzzyMatch]:
        """
        Tìm môn học khớp nhất với query.

        Args:
            query: Tên môn user nhập (có thể sai chính tả, không dấu)
            db: DB session để refresh cache nếu cần
            threshold: Ngưỡng auto-map (mặc định AUTO_MAP_THRESHOLD = 80)
            preferred_course_id: ID khóa học ưu tiên (để giải quyết trùng tên)

        Returns:
            FuzzyMatch tốt nhất nếu score >= SUGGEST_THRESHOLD,
            None nếu không tìm được gì.

        Ví dụ:
            match_subject("giai tich") → FuzzyMatch(subject_id="MI1114", score=92, auto_mapped=True)
            match_subject("abc xyz")   → None
        """
        if not query or not query.strip():
            return None

        if db is not None:
            self.ensure_fresh(db)

        if not self._subjects_norm:
            return None

        try:
            from rapidfuzz import process, fuzz

            normalized_query = self._normalize(query)
            # Danh sách tên đã normalize để so sánh
            name_list = [name for _, name in self._subjects_norm]
            id_list = [sid for sid, _ in self._subjects_norm]

            # Dùng extract (lấy nhiều kết quả) để có thể boost score
            results = process.extract(
                normalized_query,
                name_list,
                scorer=fuzz.WRatio,
                limit=10,
                score_cutoff=SUGGEST_THRESHOLD
            )

            if not results:
                return None

            # Course-first strategy:
            # 1) Nếu có preferred_course_id và tồn tại ứng viên trong course đó,
            #    chỉ chọn trong tập ứng viên này.
            # 2) Nếu không có ứng viên trong course, fallback về toàn bộ kết quả như cũ.
            if preferred_course_id is not None:
                in_course_results = []
                for matched_name, score, idx in results:
                    course_ids = self._subjects[idx][2]
                    if preferred_course_id in course_ids:
                        in_course_results.append((matched_name, score, idx))
                candidates = in_course_results if in_course_results else results
            else:
                candidates = results

            best_match = None
            best_score = -1

            for matched_name, score, idx in candidates:
                course_ids = self._subjects[idx][2]
                
                adjusted_score = score
                if preferred_course_id is not None and preferred_course_id in course_ids:
                    # Let score go above 100 temporarily to break ties definitively
                    adjusted_score = score + 10
                
                if adjusted_score > best_score:
                    best_score = adjusted_score
                    best_match = (matched_name, score, idx) # Store original score for final result

            if best_match is None:
                return None

            matched_name, original_score, idx = best_match
            # Clamp final score
            final_score = min(original_score + 10 if preferred_course_id is not None and preferred_course_id in self._subjects[idx][2] else original_score, 100)
            subject_id = id_list[idx]
            original_name = self._subjects[idx][1]

            return FuzzyMatch(
                subject_id=subject_id,
                subject_name=original_name,
                score=final_score,
                auto_mapped=final_score >= threshold
            )

        except ImportError:
            print("⚠️ [FuzzyMatcher] rapidfuzz not installed, falling back to None")
            return None
        except Exception as e:
            print(f"⚠️ [FuzzyMatcher] match_subject error: {e}")
            return None

    def get_subject_candidates(
        self,
        query: str,
        db=None,
        top_k: int = TOP_K,
        preferred_course_id: Optional[int] = None
    ) -> List[FuzzyMatch]:
        """
        Trả về top-k candidates để hỏi lại user khi không auto-map.

        Args:
            query: Tên môn user nhập
            db: DB session
            top_k: Số candidates muốn trả về

        Returns:
            List[FuzzyMatch] sorted by score desc, chỉ gồm score >= SUGGEST_THRESHOLD
        """
        if not query or not query.strip():
            return []

        if db is not None:
            self.ensure_fresh(db)

        if not self._subjects_norm:
            return []

        try:
            from rapidfuzz import process, fuzz

            normalized_query = self._normalize(query)
            name_list = [name for _, name in self._subjects_norm]

            results = process.extract(
                normalized_query,
                name_list,
                scorer=fuzz.WRatio,
                limit=max(top_k * 5, top_k),
                score_cutoff=SUGGEST_THRESHOLD
            )

            if preferred_course_id is not None:
                in_course_results = []
                for matched_name, score, idx in results:
                    course_ids = self._subjects[idx][2]
                    if preferred_course_id in course_ids:
                        in_course_results.append((matched_name, score, idx))
                selected_results = in_course_results if in_course_results else results
            else:
                selected_results = results

            candidates = []
            for matched_name, score, idx in selected_results[:top_k]:
                subject_id = self._subjects_norm[idx][0]
                original_name = self._subjects[idx][1]
                candidates.append(FuzzyMatch(
                    subject_id=subject_id,
                    subject_name=original_name,
                    score=score,
                    auto_mapped=score >= AUTO_MAP_THRESHOLD
                ))

            return candidates

        except ImportError:
            return []
        except Exception as e:
            print(f"⚠️ [FuzzyMatcher] get_subject_candidates error: {e}")
            return []

    def match_subject_by_id(self, subject_id_query: str, db=None, preferred_course_id: Optional[int] = None) -> Optional[FuzzyMatch]:
        """
        Fuzzy match theo subject_id (mã môn), ví dụ "IT308" → "IT3080"

        Hữu ích khi user gõ sai mã môn.
        """
        if not subject_id_query:
            return None

        if db is not None:
            self.ensure_fresh(db)

        try:
            from rapidfuzz import process, fuzz

            query_norm = subject_id_query.upper().strip()
            id_list = [sid for sid, _ in self._subjects]

            results = process.extract(
                query_norm,
                id_list,
                scorer=fuzz.WRatio,
                limit=10,
                score_cutoff=SUGGEST_THRESHOLD
            )

            if not results:
                return None

            if preferred_course_id is not None:
                in_course_results = []
                for matched_id, score, idx in results:
                    course_ids = self._subjects[idx][2]
                    if preferred_course_id in course_ids:
                        in_course_results.append((matched_id, score, idx))
                candidates = in_course_results if in_course_results else results
            else:
                candidates = results

            matched_id, score, idx = max(candidates, key=lambda x: x[1])
            original_name = self._subjects[idx][1]

            return FuzzyMatch(
                subject_id=matched_id,
                subject_name=original_name,
                score=score,
                auto_mapped=score >= AUTO_MAP_THRESHOLD
            )

        except ImportError:
            return None
        except Exception as e:
            print(f"⚠️ [FuzzyMatcher] match_subject_by_id error: {e}")
            return None

    # ----------------------------------------------------------
    # Class matching
    # ----------------------------------------------------------

    def match_class(self, query: str, db=None, preferred_course_id: Optional[int] = None) -> Optional[FuzzyClassMatch]:
        """
        Tìm lớp học khớp nhất với query (tên lớp hoặc class_id).

        Returns:
            FuzzyClassMatch tốt nhất, hoặc None
        """
        if not query or not query.strip():
            return None

        if db is not None:
            self.ensure_fresh(db)

        if not self._classes_norm:
            return None

        try:
            from rapidfuzz import process, fuzz

            normalized_query = self._normalize(query)
            name_list = [name for name, _ in self._classes_norm]

            results = process.extract(
                normalized_query,
                name_list,
                scorer=fuzz.WRatio,
                limit=10,
                score_cutoff=SUGGEST_THRESHOLD
            )

            if not results:
                return None

            best_match = None
            best_score = -1
            best_idx = -1

            for matched_name, score, idx in results:
                cls_dict = self._classes_norm[idx][1]
                course_ids = cls_dict.get("course_ids", set())
                
                adjusted_score = score
                if preferred_course_id is not None and preferred_course_id in course_ids:
                    adjusted_score = score + 10
                
                if adjusted_score > best_score:
                    best_score = adjusted_score
                    best_match = (matched_name, score, idx)

            if best_match is None:
                return None

            matched_name, original_score, idx = best_match
            course_ids = self._classes_norm[idx][1].get("course_ids", set())
            final_score = min(original_score + 10 if preferred_course_id is not None and preferred_course_id in course_ids else original_score, 100)
            cls_dict = self._classes_norm[idx][1]

            return FuzzyClassMatch(
                class_id=cls_dict["class_id"],
                class_name=cls_dict["class_name"],
                subject_id=cls_dict["subject_id"],
                subject_name=cls_dict["subject_name"],
                score=final_score,
                auto_mapped=final_score >= AUTO_MAP_THRESHOLD
            )

        except ImportError:
            return None
        except Exception as e:
            print(f"⚠️ [FuzzyMatcher] match_class error: {e}")
            return None

    def get_class_candidates(
        self,
        query: str,
        db=None,
        top_k: int = TOP_K
    ) -> List[FuzzyClassMatch]:
        """Top-k class candidates cho một query"""
        if not query or not query.strip():
            return []

        if db is not None:
            self.ensure_fresh(db)

        if not self._classes_norm:
            return []

        try:
            from rapidfuzz import process, fuzz

            normalized_query = self._normalize(query)
            name_list = [name for name, _ in self._classes_norm]

            results = process.extract(
                normalized_query,
                name_list,
                scorer=fuzz.WRatio,
                limit=top_k,
                score_cutoff=SUGGEST_THRESHOLD
            )

            candidates = []
            for matched_name, score, idx in results:
                cls_dict = self._classes_norm[idx][1]
                candidates.append(FuzzyClassMatch(
                    class_id=cls_dict["class_id"],
                    class_name=cls_dict["class_name"],
                    subject_id=cls_dict["subject_id"],
                    subject_name=cls_dict["subject_name"],
                    score=score,
                    auto_mapped=score >= AUTO_MAP_THRESHOLD
                ))

            return candidates

        except ImportError:
            return []
        except Exception as e:
            print(f"⚠️ [FuzzyMatcher] get_class_candidates error: {e}")
            return []

    # ----------------------------------------------------------
    # Utility
    # ----------------------------------------------------------

    def format_candidates_prompt(self, candidates: List[FuzzyMatch]) -> str:
        """
        Format danh sách candidates thành câu hỏi cho user.

        Ví dụ output:
             Bạn muốn hỏi về môn nào?
            1. Giải tích 1 (MI1114)
            2. Giải tích 2 (MI1124)
            3. Đại số (MI1134)
            Hãy nhập số (1/2/3) hoặc nhập lại tên môn.
        """
        if not candidates:
            return " Không tìm thấy môn học phù hợp. Vui lòng nhập lại tên môn."

        lines = ["Bạn muốn hỏi về môn nào?\n"]
        for i, c in enumerate(candidates, 1):
            lines.append(f"  {i}. {c.subject_name} ({c.subject_id})")
        lines.append("\nHãy nhập số (1/2/3) hoặc nhập lại tên môn.")

        return "\n".join(lines)

    @property
    def subject_count(self) -> int:
        return len(self._subjects)

    @property
    def class_count(self) -> int:
        return len(self._classes)


# ============================================================
# Module-level singleton (per DB session lifecycle)
# ============================================================
# NOTE: FuzzyMatcher được khởi tạo per-request với db session từ Depends(get_db)
# Không dùng global singleton vì db session không thread-safe across requests.
# Tuy nhiên cache nội bộ (_subjects, _classes) là read-only sau refresh
# nên an toàn để dùng chung qua một wrapper factory nếu cần.
