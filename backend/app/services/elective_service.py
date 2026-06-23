from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional, TypedDict

from sqlalchemy.orm import Session

from app.models.course_model import Course
from app.models.learned_subject_model import LearnedSubject
from app.models.student_model import Student
from app.models.subject_model import Subject


DEFAULT_COURSE_ID = "IT-E6"
MODULE_1_ID = "module_1"
MODULE_2_ID = "module_2"
PASSING_EXCLUDED_GRADES = {"F"}


@dataclass(frozen=True)
class ElectiveModule:
    module_id: str
    module_name: str
    subject_ids: tuple[str, ...]


class StudentChoiceValidationResult(TypedDict):
    is_valid: bool
    warning_message: str


class ElectiveProgressResult(TypedDict, total=False):
    course_id: str
    target_module: dict[str, Any]
    completed_module: Optional[dict[str, Any]]
    modules: list[dict[str, Any]]
    elective_subject_ids: list[str]
    target_subject_ids: list[str]
    excluded_subject_ids: list[str]
    alternatives: list[dict[str, Any]]


def _default_config_path() -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(current_dir), "rules", "elective_modules_config.json")


def _normalize_subject_id(subject_id: Optional[str]) -> str:
    return str(subject_id or "").strip().upper()


def _normalize_course_id(course_id: Optional[str]) -> str:
    return str(course_id or "").strip().upper()


def _passing_subject_ids_from_completed(completed_subjects: Mapping[str, Mapping[str, Any]]) -> set[str]:
    passed: set[str] = set()
    for subject_id, data in completed_subjects.items():
        grade = str(data.get("grade") or data.get("letter_grade") or "").strip().upper()
        if grade and grade not in PASSING_EXCLUDED_GRADES:
            passed.add(_normalize_subject_id(subject_id))
    return passed


def _passing_subject_ids_from_learned(learned_subjects: Iterable[LearnedSubject]) -> set[str]:
    passed: set[str] = set()
    for learned in learned_subjects:
        grade = str(getattr(learned, "letter_grade", "") or "").strip().upper()
        subject = getattr(learned, "subject", None)
        subject_id = getattr(subject, "subject_id", None)
        if grade and grade not in PASSING_EXCLUDED_GRADES and subject_id:
            passed.add(_normalize_subject_id(subject_id))
    return passed


class ElectiveModuleService:
    """Config-backed elective module rules for graduation and suggestions."""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or _default_config_path()
        self._courses = self._load_config(self.config_path)

    def _load_config(self, config_path: str) -> dict[str, list[ElectiveModule]]:
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                raw_config = json.load(f)
        except FileNotFoundError:
            return {}

        courses: dict[str, list[ElectiveModule]] = {}
        for course in raw_config.get("courses", []):
            course_id = _normalize_course_id(course.get("course_id"))
            if not course_id:
                continue

            modules: list[ElectiveModule] = []
            for module in course.get("modules", []):
                module_id = str(module.get("module_id") or "").strip()
                module_name = str(module.get("module_name") or module_id).strip()
                subject_ids = tuple(
                    _normalize_subject_id(subject_id)
                    for subject_id in module.get("subject_ids", [])
                    if _normalize_subject_id(subject_id)
                )
                if module_id and subject_ids:
                    modules.append(
                        ElectiveModule(
                            module_id=module_id,
                            module_name=module_name,
                            subject_ids=subject_ids,
                        )
                    )

            if modules:
                courses[course_id] = modules
        return courses

    def get_modules_for_course(self, course_id: Optional[str]) -> list[ElectiveModule]:
        return list(self._courses.get(_normalize_course_id(course_id), []))

    def get_student_course_code(self, db_session: Session, student_id: int) -> Optional[str]:
        row = (
            db_session.query(Course.course_id)
            .join(Student, Student.course_id == Course.id)
            .filter(Student.id == student_id)
            .first()
        )
        return row[0] if row else None

    def analyze_progress(
        self,
        course_id: Optional[str],
        passed_subject_ids: Iterable[str],
    ) -> ElectiveProgressResult:
        modules = self.get_modules_for_course(course_id)
        passed = {_normalize_subject_id(subject_id) for subject_id in passed_subject_ids}
        if not modules:
            return {
                "course_id": _normalize_course_id(course_id),
                "target_module": {},
                "completed_module": None,
                "modules": [],
                "elective_subject_ids": [],
                "target_subject_ids": [],
                "excluded_subject_ids": [],
                "alternatives": [],
            }

        module_progress = []
        for index, module in enumerate(modules):
            subject_set = set(module.subject_ids)
            passed_in_module = sorted(subject_set & passed, key=module.subject_ids.index)
            missing_subject_ids = [sid for sid in module.subject_ids if sid not in passed]
            module_progress.append(
                {
                    "module_id": module.module_id,
                    "module_name": module.module_name,
                    "subject_ids": list(module.subject_ids),
                    "passed_subject_ids": passed_in_module,
                    "missing_subject_ids": missing_subject_ids,
                    "passed_count": len(passed_in_module),
                    "total_count": len(module.subject_ids),
                    "is_completed": not missing_subject_ids,
                    "_config_index": index,
                }
            )

        completed_modules = [item for item in module_progress if item["is_completed"]]
        target_module = sorted(
            module_progress,
            key=lambda item: (-item["passed_count"], item["_config_index"]),
        )[0]
        completed_module = None
        if completed_modules:
            completed_module = sorted(
                completed_modules,
                key=lambda item: (-item["passed_count"], item["_config_index"]),
            )[0]
            target_module = completed_module

        elective_subject_ids = sorted(
            {subject_id for module in modules for subject_id in module.subject_ids}
        )
        target_subject_ids = set(target_module["subject_ids"])
        excluded_subject_ids = sorted(set(elective_subject_ids) - target_subject_ids)

        alternatives = []
        for module in module_progress:
            if module["module_id"] == target_module["module_id"]:
                continue
            alternatives.append(
                {
                    "module_id": module["module_id"],
                    "module_name": module["module_name"],
                    "passed_count": module["passed_count"],
                    "total_count": module["total_count"],
                    "missing_subject_ids": module["missing_subject_ids"],
                    "swap_out_subject_ids": [
                        sid
                        for sid in target_module["missing_subject_ids"]
                        if sid not in module["subject_ids"]
                    ],
                    "swap_in_subject_ids": [
                        sid
                        for sid in module["missing_subject_ids"]
                        if sid not in target_subject_ids
                    ],
                }
            )

        for module in module_progress:
            module.pop("_config_index", None)

        return {
            "course_id": _normalize_course_id(course_id),
            "target_module": target_module,
            "completed_module": completed_module,
            "modules": module_progress,
            "elective_subject_ids": elective_subject_ids,
            "target_subject_ids": list(target_module["subject_ids"]),
            "excluded_subject_ids": excluded_subject_ids,
            "alternatives": alternatives,
        }

    def analyze_student_progress(
        self,
        db_session: Session,
        student_id: int,
        completed_subjects: Optional[Mapping[str, Mapping[str, Any]]] = None,
    ) -> ElectiveProgressResult:
        course_id = self.get_student_course_code(db_session, student_id)
        if completed_subjects is None:
            learned_subjects = (
                db_session.query(LearnedSubject)
                .join(Subject, LearnedSubject.subject_id == Subject.id)
                .filter(LearnedSubject.student_id == student_id)
                .all()
            )
            passed_subject_ids = _passing_subject_ids_from_learned(learned_subjects)
        else:
            passed_subject_ids = _passing_subject_ids_from_completed(completed_subjects)
        return self.analyze_progress(course_id, passed_subject_ids)

    def recognized_subject_ids_for_cpa(
        self,
        course_id: Optional[str],
        learned_subjects: Iterable[LearnedSubject],
    ) -> Optional[set[str]]:
        learned_list = list(learned_subjects)
        progress = self.analyze_progress(
            course_id,
            _passing_subject_ids_from_learned(learned_list),
        )
        if not progress.get("completed_module"):
            return None

        elective_subject_ids = set(progress.get("elective_subject_ids", []))
        target_subject_ids = set(progress.get("target_subject_ids", []))
        recognized: set[str] = set()
        for learned in learned_list:
            subject = getattr(learned, "subject", None)
            subject_id = _normalize_subject_id(getattr(subject, "subject_id", None))
            if not subject_id:
                continue
            if subject_id in elective_subject_ids and subject_id not in target_subject_ids:
                continue
            recognized.add(subject_id)
        return recognized

    def filter_subjects_for_target_module(
        self,
        course_id: Optional[str],
        subjects: Iterable[dict[str, Any]],
        completed_subjects: Mapping[str, Mapping[str, Any]],
    ) -> tuple[list[dict[str, Any]], ElectiveProgressResult]:
        progress = self.analyze_progress(
            course_id,
            _passing_subject_ids_from_completed(completed_subjects),
        )
        excluded = set(progress.get("excluded_subject_ids", []))
        if not excluded:
            return list(subjects), progress

        filtered: list[dict[str, Any]] = []
        for subject in subjects:
            subject_id = _normalize_subject_id(subject.get("subject_id"))
            if subject_id in excluded:
                continue
            item = dict(subject)
            if subject_id in set(progress.get("target_subject_ids", [])):
                item["elective_module_id"] = progress["target_module"].get("module_id")
                item["elective_module_name"] = progress["target_module"].get("module_name")
            filtered.append(item)
        return filtered, progress


def get_suggested_subjects_by_module(
    db_session: Session,
    module_id: str,
    course_id: str = DEFAULT_COURSE_ID,
) -> list[Subject]:
    service = ElectiveModuleService()
    modules = service.get_modules_for_course(course_id)
    target_module = next((module for module in modules if module.module_id == module_id), None)
    if target_module is None:
        allowed_modules = ", ".join(module.module_id for module in modules) or "none"
        raise ValueError(
            f"Unknown elective module '{module_id}' for course '{course_id}'. "
            f"Expected one of: {allowed_modules}."
        )

    subjects = (
        db_session.query(Subject)
        .filter(Subject.subject_id.in_(target_module.subject_ids))
        .all()
    )
    subject_order = {
        subject_id: index for index, subject_id in enumerate(target_module.subject_ids)
    }

    return sorted(
        subjects,
        key=lambda subject: subject_order.get(subject.subject_id, len(subject_order)),
    )


def validate_student_choices(
    current_learned_subject_ids: list[str],
    target_subject_id: str,
    course_id: str = DEFAULT_COURSE_ID,
) -> StudentChoiceValidationResult:
    service = ElectiveModuleService()
    modules = service.get_modules_for_course(course_id)
    normalized_target = _normalize_subject_id(target_subject_id)

    target_unique_modules = _unique_modules_for_subject(modules, normalized_target)
    if not target_unique_modules:
        return {"is_valid": True, "warning_message": ""}

    learned_unique_modules = {
        module.module_id
        for subject_id in current_learned_subject_ids
        for module in _unique_modules_for_subject(modules, _normalize_subject_id(subject_id))
    }
    conflicting_module_ids = learned_unique_modules - {
        module.module_id for module in target_unique_modules
    }

    if not conflicting_module_ids:
        return {"is_valid": True, "warning_message": ""}

    target_module = target_unique_modules[0]
    conflicting_module = next(
        module for module in modules if module.module_id in conflicting_module_ids
    )

    return {
        "is_valid": False,
        "warning_message": (
            f"{normalized_target} belongs only to {target_module.module_name}, but the student "
            f"has already completed at least one subject that belongs only to "
            f"{conflicting_module.module_name}. Graduation requires all subjects from one "
            "elective module, not a mix of unique subjects from both modules. Registering "
            "this subject may waste tuition fees and study time because it will not count "
            "toward the chosen module's graduation GPA credits."
        ),
    }


def _unique_modules_for_subject(
    modules: list[ElectiveModule],
    subject_id: str,
) -> list[ElectiveModule]:
    subject_modules = [module for module in modules if subject_id in module.subject_ids]
    if len(subject_modules) == 1:
        return subject_modules
    return []


__all__ = [
    "DEFAULT_COURSE_ID",
    "ElectiveModule",
    "ElectiveModuleService",
    "MODULE_1_ID",
    "MODULE_2_ID",
    "StudentChoiceValidationResult",
    "get_suggested_subjects_by_module",
    "validate_student_choices",
]
