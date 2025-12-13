"""
Test Schedule Combination Generator
"""
from datetime import time
from app.services.schedule_combination_service import ScheduleCombinationGenerator


def test_time_conflict_detection():
    """Test time conflict detection"""
    generator = ScheduleCombinationGenerator()
    
    print("=" * 60)
    print("TEST 1: Time Conflict Detection")
    print("=" * 60)
    
    # Test 1: No conflict (different days)
    classes1 = [
        {
            'class_id': '001',
            'subject_id': 'IT3170',
            'study_date': 'Monday',
            'study_time_start': time(9, 0),
            'study_time_end': time(11, 0)
        },
        {
            'class_id': '002',
            'subject_id': 'SSH1131',
            'study_date': 'Tuesday',
            'study_time_start': time(9, 0),
            'study_time_end': time(11, 0)
        }
    ]
    
    has_conflict = generator.has_time_conflicts(classes1)
    print(f"\nTest 1.1: Different days")
    print(f"  Class 1: Monday 09:00-11:00")
    print(f"  Class 2: Tuesday 09:00-11:00")
    print(f"  Has conflict: {has_conflict}")
    assert not has_conflict, "Should NOT have conflict (different days)"
    print("  ✅ PASS")
    
    # Test 2: Conflict (same day, overlap)
    classes2 = [
        {
            'class_id': '001',
            'subject_id': 'IT3170',
            'study_date': 'Monday',
            'study_time_start': time(9, 0),
            'study_time_end': time(11, 0)
        },
        {
            'class_id': '002',
            'subject_id': 'SSH1131',
            'study_date': 'Monday',
            'study_time_start': time(10, 30),
            'study_time_end': time(12, 30)
        }
    ]
    
    has_conflict = generator.has_time_conflicts(classes2)
    print(f"\nTest 1.2: Same day with overlap")
    print(f"  Class 1: Monday 09:00-11:00")
    print(f"  Class 2: Monday 10:30-12:30")
    print(f"  Has conflict: {has_conflict}")
    assert has_conflict, "Should have conflict (overlap)"
    print("  ✅ PASS")
    
    # Test 3: No conflict (same day, no overlap)
    classes3 = [
        {
            'class_id': '001',
            'subject_id': 'IT3170',
            'study_date': 'Monday',
            'study_time_start': time(9, 0),
            'study_time_end': time(11, 0)
        },
        {
            'class_id': '002',
            'subject_id': 'SSH1131',
            'study_date': 'Monday',
            'study_time_start': time(13, 0),
            'study_time_end': time(15, 0)
        }
    ]
    
    has_conflict = generator.has_time_conflicts(classes3)
    print(f"\nTest 1.3: Same day without overlap")
    print(f"  Class 1: Monday 09:00-11:00")
    print(f"  Class 2: Monday 13:00-15:00")
    print(f"  Has conflict: {has_conflict}")
    assert not has_conflict, "Should NOT have conflict (different times)"
    print("  ✅ PASS")
    
    # Test 4: Multiple days
    classes4 = [
        {
            'class_id': '001',
            'subject_id': 'IT3170',
            'study_date': 'Monday,Wednesday',
            'study_time_start': time(9, 0),
            'study_time_end': time(11, 0)
        },
        {
            'class_id': '002',
            'subject_id': 'SSH1131',
            'study_date': 'Wednesday,Friday',
            'study_time_start': time(10, 0),
            'study_time_end': time(12, 0)
        }
    ]
    
    has_conflict = generator.has_time_conflicts(classes4)
    print(f"\nTest 1.4: Multiple days with conflict on Wednesday")
    print(f"  Class 1: Monday,Wednesday 09:00-11:00")
    print(f"  Class 2: Wednesday,Friday 10:00-12:00")
    print(f"  Has conflict: {has_conflict}")
    assert has_conflict, "Should have conflict on Wednesday"
    print("  ✅ PASS")


def test_schedule_metrics():
    """Test schedule metrics calculation"""
    generator = ScheduleCombinationGenerator()
    
    print("\n" + "=" * 60)
    print("TEST 2: Schedule Metrics")
    print("=" * 60)
    
    classes = [
        {
            'class_id': '001',
            'subject_id': 'IT3170',
            'subject_name': 'Lập trình mạng',
            'study_date': 'Monday,Wednesday',
            'study_time_start': time(9, 0),
            'study_time_end': time(11, 25),
            'credits': 3
        },
        {
            'class_id': '002',
            'subject_id': 'SSH1131',
            'subject_name': 'Tư tưởng HCM',
            'study_date': 'Tuesday',
            'study_time_start': time(13, 0),
            'study_time_end': time(15, 25),
            'credits': 2
        },
        {
            'class_id': '003',
            'subject_id': 'IT3080',
            'subject_name': 'Cơ sở dữ liệu',
            'study_date': 'Thursday,Friday',
            'study_time_start': time(7, 0),
            'study_time_end': time(9, 25),
            'credits': 3
        }
    ]
    
    metrics = generator.calculate_schedule_metrics(classes)
    
    print(f"\nClasses:")
    for cls in classes:
        print(f"  • {cls['subject_id']}: {cls['study_date']} {cls['study_time_start']}-{cls['study_time_end']}")
    
    print(f"\nMetrics:")
    print(f"  Total credits: {metrics['total_credits']}")
    print(f"  Total classes: {metrics['total_classes']}")
    print(f"  Study days: {metrics['study_days']}")
    print(f"  Free days: {metrics['free_days']}")
    print(f"  Continuous study days: {metrics['continuous_study_days']}")
    print(f"  Average daily hours: {metrics['average_daily_hours']:.2f}")
    print(f"  Earliest start: {metrics['earliest_start']}")
    print(f"  Latest end: {metrics['latest_end']}")
    
    assert metrics['total_credits'] == 8
    assert metrics['total_classes'] == 3
    assert metrics['study_days'] == 5  # Mon, Tue, Wed, Thu, Fri
    assert metrics['free_days'] == 2  # Sat, Sun
    print("  ✅ PASS")


def test_combination_generation():
    """Test full combination generation"""
    generator = ScheduleCombinationGenerator()
    
    print("\n" + "=" * 60)
    print("TEST 3: Combination Generation")
    print("=" * 60)
    
    # Create mock classes by subject
    classes_by_subject = {
        'IT3170': [
            {
                'id': 1,
                'class_id': '161084',
                'subject_id': 'IT3170',
                'subject_name': 'Lập trình mạng',
                'study_date': 'Monday,Wednesday',
                'study_time_start': time(9, 0),
                'study_time_end': time(11, 25),
                'credits': 3,
                'available_slots': 30,
                'max_students': 50
            },
            {
                'id': 2,
                'class_id': '161085',
                'subject_id': 'IT3170',
                'subject_name': 'Lập trình mạng',
                'study_date': 'Tuesday,Thursday',
                'study_time_start': time(13, 0),
                'study_time_end': time(15, 25),
                'credits': 3,
                'available_slots': 25,
                'max_students': 50
            }
        ],
        'SSH1131': [
            {
                'id': 3,
                'class_id': '164489',
                'subject_id': 'SSH1131',
                'subject_name': 'Tư tưởng HCM',
                'study_date': 'Monday',
                'study_time_start': time(9, 0),
                'study_time_end': time(11, 25),
                'credits': 2,
                'available_slots': 150,
                'max_students': 150
            },
            {
                'id': 4,
                'class_id': '164490',
                'subject_id': 'SSH1131',
                'subject_name': 'Tư tưởng HCM',
                'study_date': 'Friday',
                'study_time_start': time(7, 0),
                'study_time_end': time(9, 25),
                'credits': 2,
                'available_slots': 50,
                'max_students': 50
            }
        ]
    }
    
    preferences = {
        'prefer_days': ['Monday', 'Tuesday'],
        'time_period': 'morning',
        'prefer_free_days': True
    }
    
    print(f"\nGenerating combinations from 2 subjects...")
    print(f"  IT3170: {len(classes_by_subject['IT3170'])} classes")
    print(f"  SSH1131: {len(classes_by_subject['SSH1131'])} classes")
    
    combinations = generator.generate_combinations(
        classes_by_subject=classes_by_subject,
        preferences=preferences,
        max_combinations=100
    )
    
    print(f"\n✅ Generated {len(combinations)} valid combinations")
    
    if combinations:
        print(f"\nTop 3 combinations:")
        for idx, combo in enumerate(combinations[:3], 1):
            print(f"\n  {idx}. Score: {combo['score']:.1f}")
            print(f"     Metrics: {combo['metrics']['total_classes']} classes, " +
                  f"{combo['metrics']['study_days']} study days, " +
                  f"{combo['metrics']['free_days']} free days")
            print(f"     Classes:")
            for cls in combo['classes']:
                print(f"       • {cls['class_id']}: {cls['study_date']} {cls['study_time_start']}-{cls['study_time_end']}")


if __name__ == '__main__':
    test_time_conflict_detection()
    test_schedule_metrics()
    test_combination_generation()
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 60)
