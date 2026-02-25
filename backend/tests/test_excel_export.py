"""
Test script for Excel Export Service
Run this to verify Excel generation works correctly
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.excel_export_service import ExcelExportService


def test_excel_export():
    """Test Excel export with sample data"""
    
    # Sample combination data (similar to chatbot response)
    sample_combination = {
        "combination_id": 1,
        "score": 145.58,
        "recommended": True,
        "metrics": {
            "total_classes": 4,
            "total_credits": 7,
            "study_days": 2,
            "free_days": 5,
            "average_daily_hours": 8.2,
            "earliest_start": "06:45",
            "latest_end": "17:30",
            "continuous_study_days": 2
        },
        "classes": [
            {
                "class_id": "166141",
                "class_name": "Tiếng Nhật 8",
                "subject_name": "Tiếng Nhật 8",
                "study_time_start": "08:25",
                "study_time_end": "10:05",
                "study_date": "Wednesday",
                "study_week": [25, 26, 27, 28, 29, 30, 31, 32, 34, 35, 36, 37, 38, 39, 40, 41, 42],
                "classroom": "C7-217",
                "teacher_name": "TBA",
                "priority_reason": "Matches semester 8"
            },
            {
                "class_id": "166138",
                "class_name": "Kỹ năng ITSS học bằng tiếng Nhật 2",
                "subject_name": "Kỹ năng ITSS học bằng tiếng Nhật 2",
                "study_time_start": "14:10",
                "study_time_end": "17:30",
                "study_date": "Wednesday",
                "study_week": [25, 26, 27, 28, 29, 30, 31, 32, 34, 35, 36, 37, 38, 39, 40, 41, 42],
                "classroom": "B1-201",
                "teacher_name": "TBA",
                "priority_reason": "Matches semester 8"
            },
            {
                "class_id": "167910",
                "class_name": "Quản trị phát triển phần mềm",
                "subject_name": "Quản trị phát triển phần mềm",
                "study_time_start": "12:30",
                "study_time_end": "14:00",
                "study_date": "Thursday",
                "study_week": [25, 26, 27, 28, 29, 30, 31, 32, 34, 35, 36, 37, 38, 39, 40, 41, 42],
                "classroom": "D9-402",
                "teacher_name": "TBA",
                "priority_reason": "Matches semester 8"
            },
            {
                "class_id": "168499",
                "class_name": "Nhập môn Khoa học dữ liệu",
                "subject_name": "Nhập môn Khoa học dữ liệu",
                "study_time_start": "06:45",
                "study_time_end": "09:10",
                "study_date": "Thursday",
                "study_week": [25, 26, 27, 28, 29, 30, 31, 32, 34, 35, 36, 37, 38, 39, 40, 41, 42],
                "classroom": "TC-307",
                "teacher_name": "TBA",
                "priority_reason": "Matches semester 8"
            }
        ]
    }
    
    sample_student_info = {
        "semester": 8,
        "cpa": 3.45
    }
    
    print("🧪 Testing Excel Export Service...")
    print(f"📊 Combination ID: {sample_combination['combination_id']}")
    print(f"📚 Classes: {len(sample_combination['classes'])}")
    
    try:
        # Create service
        excel_service = ExcelExportService()
        
        # Generate Excel
        excel_file = excel_service.generate_excel(sample_combination, sample_student_info)
        
        # Save to file
        output_path = "test_output.xlsx"
        with open(output_path, "wb") as f:
            f.write(excel_file.getvalue())
        
        print(f"✅ Excel file generated successfully!")
        print(f"📁 Saved to: {output_path}")
        print(f"📏 File size: {len(excel_file.getvalue())} bytes")
        print("\n💡 You can now:")
        print("   1. Open the file in Microsoft Excel")
        print("   2. Upload to Google Drive and open with Google Sheets")
        print("   3. Upload to OneDrive and open with Excel Online")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_excel_export()
