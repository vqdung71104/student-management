"""
Diagnostic test for Rule 5/6 behavior in subject suggestion flow.

Run exactly:
    cd backend
    venv/Scripts/activate
    python tests/test_rule5_rule6_diagnosis.py
"""
import os
import sys
from collections import Counter


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
sys.path.insert(0, BACKEND_DIR)

from app.db.database import SessionLocal  # noqa: E402
from app.rules.subject_suggestion_rules import SubjectSuggestionRuleEngine  # noqa: E402
from sqlalchemy import text  # noqa: E402


def _sum_credits(rows):
    total = 0.0
    for row in rows:
        try:
            total += float(row.get("credits") or 0)
        except (TypeError, ValueError):
            pass
    return total


def run_diagnosis(student_id: int = 1):
    db = SessionLocal()
    try:
        engine = SubjectSuggestionRuleEngine(db)

        current_semester = engine.get_current_semester()
        student_sem_no = engine.calculate_student_semester_number(student_id, current_semester)
        student_data = engine.get_student_data(student_id)
        min_credits, max_credits = engine.get_credit_limits(
            warning_level=student_data["warning_level"],
            current_semester=current_semester,
            student_semester_number=student_sem_no,
            has_foreign_lang_requirement=False,
        )

        available = engine.get_available_subjects(student_id, current_semester)
        available_ids = {str(s.get("subject_id") or "").upper() for s in available}

        pe_list = {str(x).upper() for x in engine.PHYSICAL_EDUCATION_SUBJECTS}
        supp_list = {str(x).upper() for x in engine.SUPPLEMENTARY_SUBJECTS}
        available_pe_ids = sorted([sid for sid in available_ids if sid in pe_list])
        available_supp_ids = sorted([sid for sid in available_ids if sid in supp_list])

        course_rows = db.execute(
            text(
                """
                SELECT s.subject_id
                FROM students st
                JOIN course_subjects cs ON st.course_id = cs.course_id
                JOIN subjects s ON s.id = cs.subject_id
                WHERE st.id = :student_id
                """
            ),
            {"student_id": student_id},
        ).fetchall()
        course_ids = {str(r[0]).upper() for r in course_rows if r and r[0]}
        course_pe_ids = sorted([sid for sid in course_ids if sid in pe_list])
        course_supp_ids = sorted([sid for sid in course_ids if sid in supp_list])

        failed, rem1 = engine.rule_1_filter_failed_subjects(available, student_data)
        prev_unlearned, rem2 = engine.rule_2_filter_previous_semester_unlearned(rem1, student_sem_no, student_data)
        sem_match, rem3 = engine.rule_2_filter_semester_match(rem2, student_sem_no, student_data)
        political, rem4 = engine.rule_3_filter_political_subjects(rem3, student_data)
        pe_candidates, rem5 = engine.rule_4_filter_physical_education(rem4, student_data)
        supp_candidates, rem6 = engine.rule_5_filter_supplementary_subjects(rem5, student_data)

        result = engine.suggest_subjects(student_id)
        summary = result.get("summary", {}) or {}
        pe_in_summary = summary.get("physical_education", []) or []
        supp_in_summary = summary.get("supplementary", []) or []

        selected_before_pe = failed + prev_unlearned + sem_match + political
        credits_before_pe = _sum_credits(selected_before_pe)
        credits_left_before_pe = max_credits - credits_before_pe

        completed = student_data["completed_subjects"]
        eligible_pe_ids = engine._eligible_pe_subject_ids()
        pe_completed_count = sum(
            1
            for sid, data in completed.items()
            if sid in eligible_pe_ids and data.get("grade") != engine.FAILED_GRADE and not engine._is_optional_pe_subject(data)
        )
        pe_needed_count = max(engine.PE_REQUIRED - pe_completed_count, 0)

        print("=" * 90)
        print("RULE 5/6 DIAGNOSIS")
        print("=" * 90)
        print(f"student_id={student_id}")
        print(f"current_semester={current_semester} | student_semester={student_sem_no}")
        print(f"warning_level={student_data['warning_level']} | cpa={student_data['cpa']:.2f}")
        print(f"credit_limits: min={min_credits}, max={max_credits}")
        print(f"available_subjects={len(available)}")
        print(f"available PE IDs count={len(available_pe_ids)} | sample={available_pe_ids[:10]}")
        print(f"available SUPP IDs count={len(available_supp_ids)} | sample={available_supp_ids[:10]}")
        print(f"course PE IDs count={len(course_pe_ids)} | sample={course_pe_ids[:10]}")
        print(f"course SUPP IDs count={len(course_supp_ids)} | sample={course_supp_ids[:10]}")
        print("-" * 90)
        print(f"credits_before_rule5(PE)={credits_before_pe:g} | credits_left={credits_left_before_pe:g}")
        print(f"failed={len(failed)}, prev_unlearned={len(prev_unlearned)}, sem_match={len(sem_match)}, political={len(political)}")
        print("-" * 90)
        print(f"PE completed={pe_completed_count}/{engine.PE_REQUIRED}, needed={pe_needed_count}")
        print(f"PE candidates from rule function={len(pe_candidates)}")
        print(f"PE actually included in summary['physical_education']={len(pe_in_summary)}")
        print(f"Supplementary candidates from rule function={len(supp_candidates)}")
        print(f"Supplementary actually included in summary['supplementary']={len(supp_in_summary)}")
        print("-" * 90)
        print("Summary keys returned by suggest_subjects():")
        print(list(summary.keys()))
        print("Has key 'pe_subjects'?:", "pe_subjects" in summary)
        print("Has key 'Supplementary_subjects'?:", "Supplementary_subjects" in summary)
        print("-" * 90)

        pe_cand_ids = [s.get("subject_id") for s in pe_candidates]
        pe_sum_ids = [s.get("subject_id") for s in pe_in_summary]
        supp_cand_ids = [s.get("subject_id") for s in supp_candidates]
        supp_sum_ids = [s.get("subject_id") for s in supp_in_summary]

        missing_pe = [sid for sid in pe_cand_ids if sid not in pe_sum_ids]
        missing_supp = [sid for sid in supp_cand_ids if sid not in supp_sum_ids]

        print("PE candidate IDs:", pe_cand_ids[:20])
        print("PE summary IDs  :", pe_sum_ids[:20])
        print("Missing PE IDs  :", missing_pe[:20])
        print("-" * 90)
        print("SUPP candidate IDs:", supp_cand_ids[:20])
        print("SUPP summary IDs  :", supp_sum_ids[:20])
        print("Missing SUPP IDs  :", missing_supp[:20])
        print("-" * 90)

        # Quick reason probe: missing mostly due to credit cap
        reason_counter = Counter()
        total_credits_progress = credits_before_pe
        for subj in pe_candidates[:pe_needed_count]:
            c = float(subj.get("credits") or 0)
            if total_credits_progress + c <= max_credits:
                total_credits_progress += c
            else:
                reason_counter["pe_over_credit_limit"] += 1
        for subj in supp_candidates[:engine.SUPPLEMENTARY_REQUIRED]:
            c = float(subj.get("credits") or 0)
            if total_credits_progress + c <= max_credits:
                total_credits_progress += c
            else:
                reason_counter["supp_over_credit_limit"] += 1

        print("Reason probe:", dict(reason_counter))
        print("=" * 90)
        print("CONCLUSION HINTS")
        if pe_candidates and not pe_in_summary:
            print("- PE candidates exist but none selected: likely blocked by max credit or PE needed count = 0.")
        if supp_candidates and not supp_in_summary:
            print("- Supplementary candidates exist but none selected: likely blocked by max credit after earlier rules.")
        if not pe_candidates:
            print("- No PE candidates from rule function: likely already completed PE requirement or none in available subjects.")
        if not supp_candidates:
            print("- No supplementary candidates from rule function: likely already completed requirement or none in available subjects.")
        if "pe_subjects" not in summary and "Supplementary_subjects" not in summary:
            print("- Naming mismatch confirmed: summary uses 'physical_education' and 'supplementary'.")
        print("=" * 90)

    finally:
        db.close()


if __name__ == "__main__":
    sid = 1
    if len(sys.argv) > 1:
        try:
            sid = int(sys.argv[1])
        except ValueError:
            pass
    run_diagnosis(sid)
