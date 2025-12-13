"""
Test Time Conflict Detection
Tests the absolute rule: No two classes can have overlapping schedules
"""
import pytest
from datetime import timedelta, time
from app.services.schedule_combination_service import ScheduleCombinationGenerator


class TestTimeConflictDetection:
    """Test suite for schedule conflict detection"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.generator = ScheduleCombinationGenerator()
    
    # ==================== NO CONFLICT CASES ====================
    
    def test_no_conflict_different_weeks(self):
        """Test: No conflict when classes are in different weeks"""
        class1 = {
            'class_id': '101',
            'study_week': [1, 2, 3],
            'study_date': 'Monday',
            'study_time_start': timedelta(seconds=36000),  # 10:00
            'study_time_end': timedelta(seconds=43200)     # 12:00
        }
        class2 = {
            'class_id': '102',
            'study_week': [4, 5, 6],
            'study_date': 'Monday',
            'study_time_start': timedelta(seconds=36000),  # 10:00
            'study_time_end': timedelta(seconds=43200)     # 12:00
        }
        
        result = self.generator.has_time_conflicts([class1, class2])
        assert result == False, "Classes in different weeks should NOT conflict"
    
    def test_no_conflict_different_days(self):
        """Test: No conflict when classes are on different days"""
        class1 = {
            'class_id': '101',
            'study_week': [1, 2, 3],
            'study_date': 'Monday',
            'study_time_start': timedelta(seconds=36000),  # 10:00
            'study_time_end': timedelta(seconds=43200)     # 12:00
        }
        class2 = {
            'class_id': '102',
            'study_week': [1, 2, 3],
            'study_date': 'Tuesday',
            'study_time_start': timedelta(seconds=36000),  # 10:00
            'study_time_end': timedelta(seconds=43200)     # 12:00
        }
        
        result = self.generator.has_time_conflicts([class1, class2])
        assert result == False, "Classes on different days should NOT conflict"
    
    def test_no_conflict_adjacent_times(self):
        """Test: No conflict when classes are adjacent (one ends when other starts)"""
        class1 = {
            'class_id': '101',
            'study_week': [1, 2, 3],
            'study_date': 'Monday',
            'study_time_start': timedelta(seconds=36000),  # 10:00
            'study_time_end': timedelta(seconds=43200)     # 12:00
        }
        class2 = {
            'class_id': '102',
            'study_week': [1, 2, 3],
            'study_date': 'Monday',
            'study_time_start': timedelta(seconds=43200),  # 12:00
            'study_time_end': timedelta(seconds=50400)     # 14:00
        }
        
        result = self.generator.has_time_conflicts([class1, class2])
        assert result == False, "Adjacent classes should NOT conflict"
    
    def test_no_conflict_separate_times_same_day(self):
        """Test: No conflict when classes are clearly separated in time"""
        class1 = {
            'class_id': '101',
            'study_week': [1, 2, 3],
            'study_date': 'Wednesday',
            'study_time_start': timedelta(seconds=28800),  # 08:00
            'study_time_end': timedelta(seconds=36000)     # 10:00
        }
        class2 = {
            'class_id': '102',
            'study_week': [1, 2, 3],
            'study_date': 'Wednesday',
            'study_time_start': timedelta(seconds=50400),  # 14:00
            'study_time_end': timedelta(seconds=57600)     # 16:00
        }
        
        result = self.generator.has_time_conflicts([class1, class2])
        assert result == False, "Separated classes should NOT conflict"
    
    def test_no_conflict_partial_week_overlap_different_days(self):
        """Test: Partial week overlap but different days"""
        class1 = {
            'class_id': '101',
            'study_week': [1, 2, 3, 4, 5],
            'study_date': 'Monday,Wednesday',
            'study_time_start': timedelta(seconds=36000),  # 10:00
            'study_time_end': timedelta(seconds=43200)     # 12:00
        }
        class2 = {
            'class_id': '102',
            'study_week': [3, 4, 5, 6, 7],
            'study_date': 'Tuesday,Thursday',
            'study_time_start': timedelta(seconds=36000),  # 10:00
            'study_time_end': timedelta(seconds=43200)     # 12:00
        }
        
        result = self.generator.has_time_conflicts([class1, class2])
        assert result == False, "Classes with overlapping weeks but different days should NOT conflict"
    
    # ==================== CONFLICT CASES ====================
    
    def test_conflict_same_start_time(self):
        """Test: CONFLICT when classes start at same time"""
        class1 = {
            'class_id': '101',
            'study_week': [1, 2, 3],
            'study_date': 'Wednesday',
            'study_time_start': timedelta(seconds=24300),  # 06:45
            'study_time_end': timedelta(seconds=33000)     # 09:10
        }
        class2 = {
            'class_id': '102',
            'study_week': [1, 2, 3],
            'study_date': 'Wednesday',
            'study_time_start': timedelta(seconds=24300),  # 06:45
            'study_time_end': timedelta(seconds=29700)     # 08:15
        }
        
        result = self.generator.has_time_conflicts([class1, class2])
        assert result == True, "Classes starting at same time SHOULD conflict"
    
    def test_conflict_start_time_overlap(self):
        """Test: CONFLICT when class2 starts during class1"""
        class1 = {
            'class_id': '101',
            'study_week': [1, 2, 3, 4, 5, 6],
            'study_date': 'Monday',
            'study_time_start': timedelta(seconds=36900),  # 10:15
            'study_time_end': timedelta(seconds=50400)     # 14:00
        }
        class2 = {
            'class_id': '102',
            'study_week': [1, 2, 3, 4, 5, 6, 7],
            'study_date': 'Monday',
            'study_time_start': timedelta(seconds=30300),  # 08:25
            'study_time_end': timedelta(seconds=42300)     # 11:45
        }
        
        result = self.generator.has_time_conflicts([class1, class2])
        assert result == True, "Class2 starting during class1 SHOULD conflict"
    
    def test_conflict_end_time_overlap(self):
        """Test: CONFLICT when class2 ends during class1"""
        class1 = {
            'class_id': '101',
            'study_week': [1, 2, 3],
            'study_date': 'Friday',
            'study_time_start': timedelta(seconds=36000),  # 10:00
            'study_time_end': timedelta(seconds=50400)     # 14:00
        }
        class2 = {
            'class_id': '102',
            'study_week': [1, 2, 3],
            'study_date': 'Friday',
            'study_time_start': timedelta(seconds=28800),  # 08:00
            'study_time_end': timedelta(seconds=43200)     # 12:00
        }
        
        result = self.generator.has_time_conflicts([class1, class2])
        assert result == True, "Class2 ending during class1 SHOULD conflict"
    
    def test_conflict_class2_covers_class1(self):
        """Test: CONFLICT when class2 completely covers class1"""
        class1 = {
            'class_id': '101',
            'study_week': [1, 2, 3],
            'study_date': 'Wednesday',
            'study_time_start': timedelta(seconds=36000),  # 10:00
            'study_time_end': timedelta(seconds=43200)     # 12:00
        }
        class2 = {
            'class_id': '102',
            'study_week': [1, 2, 3],
            'study_date': 'Wednesday',
            'study_time_start': timedelta(seconds=32400),  # 09:00
            'study_time_end': timedelta(seconds=50400)     # 14:00
        }
        
        result = self.generator.has_time_conflicts([class1, class2])
        assert result == True, "Class2 covering class1 completely SHOULD conflict"
    
    def test_conflict_multiple_days_overlap(self):
        """Test: CONFLICT when classes share multiple days"""
        class1 = {
            'class_id': '101',
            'study_week': [1, 2, 3],
            'study_date': 'Monday,Wednesday,Friday',
            'study_time_start': timedelta(seconds=36000),  # 10:00
            'study_time_end': timedelta(seconds=43200)     # 12:00
        }
        class2 = {
            'class_id': '102',
            'study_week': [1, 2, 3],
            'study_date': 'Wednesday,Thursday',
            'study_time_start': timedelta(seconds=39600),  # 11:00
            'study_time_end': timedelta(seconds=46800)     # 13:00
        }
        
        result = self.generator.has_time_conflicts([class1, class2])
        assert result == True, "Classes overlapping on Wednesday SHOULD conflict"
    
    def test_conflict_partial_week_overlap_same_day(self):
        """Test: CONFLICT with partial week overlap but same day"""
        class1 = {
            'class_id': '101',
            'study_week': [1, 2, 3, 4, 5],
            'study_date': 'Tuesday',
            'study_time_start': timedelta(seconds=36000),  # 10:00
            'study_time_end': timedelta(seconds=43200)     # 12:00
        }
        class2 = {
            'class_id': '102',
            'study_week': [4, 5, 6, 7],
            'study_date': 'Tuesday',
            'study_time_start': timedelta(seconds=39600),  # 11:00
            'study_time_end': timedelta(seconds=46800)     # 13:00
        }
        
        result = self.generator.has_time_conflicts([class1, class2])
        assert result == True, "Overlapping weeks [4,5] with same day and time SHOULD conflict"
    
    # ==================== EDGE CASES ====================
    
    def test_no_conflict_empty_study_week(self):
        """Test: Handle empty study_week gracefully"""
        class1 = {
            'class_id': '101',
            'study_week': [],
            'study_date': 'Monday',
            'study_time_start': timedelta(seconds=36000),  # 10:00
            'study_time_end': timedelta(seconds=43200)     # 12:00
        }
        class2 = {
            'class_id': '102',
            'study_week': [1, 2, 3],
            'study_date': 'Monday',
            'study_time_start': timedelta(seconds=36000),  # 10:00
            'study_time_end': timedelta(seconds=43200)     # 12:00
        }
        
        result = self.generator.has_time_conflicts([class1, class2])
        assert result == False, "Empty study_week should result in no conflict"
    
    def test_no_conflict_none_study_week(self):
        """Test: Handle None study_week gracefully"""
        class1 = {
            'class_id': '101',
            'study_week': None,
            'study_date': 'Monday',
            'study_time_start': timedelta(seconds=36000),  # 10:00
            'study_time_end': timedelta(seconds=43200)     # 12:00
        }
        class2 = {
            'class_id': '102',
            'study_week': [1, 2, 3],
            'study_date': 'Monday',
            'study_time_start': timedelta(seconds=36000),  # 10:00
            'study_time_end': timedelta(seconds=43200)     # 12:00
        }
        
        result = self.generator.has_time_conflicts([class1, class2])
        assert result == False, "None study_week should result in no conflict"
    
    def test_multiple_classes_no_conflict(self):
        """Test: Multiple classes with no conflicts"""
        classes = [
            {
                'class_id': '101',
                'study_week': [1, 2, 3],
                'study_date': 'Monday',
                'study_time_start': timedelta(seconds=28800),  # 08:00
                'study_time_end': timedelta(seconds=36000)     # 10:00
            },
            {
                'class_id': '102',
                'study_week': [1, 2, 3],
                'study_date': 'Monday',
                'study_time_start': timedelta(seconds=36000),  # 10:00
                'study_time_end': timedelta(seconds=43200)     # 12:00
            },
            {
                'class_id': '103',
                'study_week': [1, 2, 3],
                'study_date': 'Monday',
                'study_time_start': timedelta(seconds=50400),  # 14:00
                'study_time_end': timedelta(seconds=57600)     # 16:00
            }
        ]
        
        result = self.generator.has_time_conflicts(classes)
        assert result == False, "Multiple non-overlapping classes should NOT conflict"
    
    def test_multiple_classes_with_conflict(self):
        """Test: Multiple classes where at least one pair conflicts"""
        classes = [
            {
                'class_id': '101',
                'study_week': [1, 2, 3],
                'study_date': 'Wednesday',
                'study_time_start': timedelta(seconds=28800),  # 08:00
                'study_time_end': timedelta(seconds=36000)     # 10:00
            },
            {
                'class_id': '102',
                'study_week': [1, 2, 3],
                'study_date': 'Wednesday',
                'study_time_start': timedelta(seconds=36000),  # 10:00
                'study_time_end': timedelta(seconds=43200)     # 12:00
            },
            {
                'class_id': '103',
                'study_week': [1, 2, 3],
                'study_date': 'Wednesday',
                'study_time_start': timedelta(seconds=39600),  # 11:00 - CONFLICTS with 102
                'study_time_end': timedelta(seconds=46800)     # 13:00
            }
        ]
        
        result = self.generator.has_time_conflicts(classes)
        assert result == True, "Multiple classes with at least one conflict SHOULD return True"
    
    # ==================== REAL WORLD SCENARIOS ====================
    
    def test_real_scenario_conflict_from_logs(self):
        """Test: Real conflict scenario from user logs"""
        # Nguyên lý hệ điều hành - 161316
        class1 = {
            'class_id': '161316',
            'study_week': [1, 2, 3, 4, 5, 6],
            'study_date': 'Wednesday',
            'study_time_start': timedelta(seconds=51000),  # 14:10
            'study_time_end': timedelta(seconds=63000)     # 17:30
        }
        # Tiếng Nhật chuyên ngành 1 - 161326
        class2 = {
            'class_id': '161326',
            'study_week': [1, 2, 3, 4, 5, 6],
            'study_date': 'Wednesday',
            'study_time_start': timedelta(seconds=51000),  # 14:10
            'study_time_end': timedelta(seconds=63000)     # 17:30
        }
        
        result = self.generator.has_time_conflicts([class1, class2])
        assert result == True, "Real scenario: 161316 and 161326 SHOULD conflict"
    
    def test_real_scenario_morning_wednesday_conflict(self):
        """Test: Multiple classes on Wednesday morning"""
        classes = [
            # Chủ nghĩa xã hội khoa học - 164501
            {
                'class_id': '164501',
                'study_week': [1, 2, 3, 4, 5, 6],
                'study_date': 'Wednesday',
                'study_time_start': timedelta(seconds=24300),  # 06:45
                'study_time_end': timedelta(seconds=33000)     # 09:10
            },
            # Mạng máy tính - 161318
            {
                'class_id': '161318',
                'study_week': [1, 2, 3, 4, 5, 6],
                'study_date': 'Wednesday',
                'study_time_start': timedelta(seconds=33600),  # 09:20
                'study_time_end': timedelta(seconds=42300)     # 11:45
            },
            # Triết học Mác - Lênin - 164342
            {
                'class_id': '164342',
                'study_week': [1, 2, 3, 4, 5, 6],
                'study_date': 'Wednesday',
                'study_time_start': timedelta(seconds=24300),  # 06:45 - CONFLICTS with 164501
                'study_time_end': timedelta(seconds=29700)     # 08:15
            }
        ]
        
        result = self.generator.has_time_conflicts(classes)
        assert result == True, "164501 and 164342 both start at 06:45 on Wednesday SHOULD conflict"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
