"""
Sample data để test các API StudentDRL và StudentProjects
"""

sample_drl_data = [
    {
        "student_id": "21110001",
        "semester": 1,
        "drl_score": 85
    },
    {
        "student_id": "21110001", 
        "semester": 2,
        "drl_score": 78
    },
    {
        "student_id": "21110002",
        "semester": 1,
        "drl_score": 92
    },
    {
        "student_id": "21110002",
        "semester": 2,
        "drl_score": 88
    }
]

sample_projects_data = [
    {
        "student_id": "21110001",
        "subject_id": "IT001",
        "type": "ASSIGNMENT",
        "teacher_name": "Nguyễn Văn A",
        "topic": "Xây dựng website bán hàng với Laravel",
        "scores": 85,
        "status": "COMPLETED"
    },
    {
        "student_id": "21110001",
        "subject_id": "IT002",
        "type": "PROJECT", 
        "teacher_name": "Trần Thị B",
        "topic": "Ứng dụng quản lý thư viện với Java Swing",
        "scores": None,
        "status": "IN_PROGRESS"
    },
    {
        "student_id": "21110002",
        "subject_id": "IT003",
        "type": "THESIS",
        "teacher_name": "Lê Văn C", 
        "topic": "Nghiên cứu thuật toán machine learning trong dự đoán giá chứng khoán",
        "scores": None,
        "status": "PENDING"
    }
]

# Test requests để gửi POST API
test_drl_requests = """
# Test tạo điểm rèn luyện
curl -X POST "http://localhost:8000/student-drl/" \\
     -H "Content-Type: application/json" \\
     -d '{"student_id": "21110001", "semester": 1, "drl_score": 85}'

# Test lấy tất cả điểm rèn luyện
curl -X GET "http://localhost:8000/student-drl/"

# Test lấy điểm rèn luyện theo student_id
curl -X GET "http://localhost:8000/student-drl/?student_id=21110001"

# Test lấy tóm tắt điểm rèn luyện của sinh viên
curl -X GET "http://localhost:8000/student-drl/student/21110001/summary"
"""

test_projects_requests = """
# Test tạo đồ án/dự án
curl -X POST "http://localhost:8000/student-projects/" \\
     -H "Content-Type: application/json" \\
     -d '{"student_id": "21110001", "subject_id": "IT001", "type": "ASSIGNMENT", "teacher_name": "Nguyễn Văn A", "topic": "Xây dựng website bán hàng với Laravel"}'

# Test lấy tất cả đồ án/dự án
curl -X GET "http://localhost:8000/student-projects/"

# Test lấy đồ án/dự án theo student_id
curl -X GET "http://localhost:8000/student-projects/?student_id=21110001"

# Test chấm điểm cho đồ án/dự án
curl -X PATCH "http://localhost:8000/student-projects/1/grade?scores=85"

# Test lấy tóm tắt đồ án/dự án của sinh viên  
curl -X GET "http://localhost:8000/student-projects/student/21110001/summary"
"""