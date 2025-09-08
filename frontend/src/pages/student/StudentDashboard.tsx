import { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { useNavigate } from 'react-router-dom'

const StudentDashboard = () => {
  const { userInfo } = useAuth()
  const navigate = useNavigate()
  const [quickStats, setQuickStats] = useState({
    currentGPA: 0,
    totalCredits: 0,
    completedSubjects: 0,
    upcomingExams: 0
  })
  const [recentGrades, setRecentGrades] = useState<Array<{subject: string, score: number, grade: string}>>([])
  const [upcomingSchedule, setUpcomingSchedule] = useState<Array<{subject: string, time: string, room: string, day: string}>>([])

  useEffect(() => {
    const fetchDashboardData = async () => {
      if (!userInfo?.student_id) return
      
      try {
        // Lấy thông tin chi tiết học tập
        const response = await fetch(`http://localhost:8000/students/${userInfo.student_id}/academic-details`)
        if (response.ok) {
          const data = await response.json()
          console.log('Academic details data:', data) // Debug log
          
          setQuickStats({
            currentGPA: data.overall_gpa || 0,
            totalCredits: data.total_credits || 0,
            completedSubjects: data.learned_subjects?.length || 0,
            upcomingExams: 0 // Tạm thời để 0, có thể cập nhật sau
          })

          // Lấy điểm gần đây (3 môn cuối)
          const recentGradesData = data.learned_subjects
            ?.slice(-3)
            ?.map((subject: any) => ({
              subject: subject.subject_name,
              score: subject.total_score || 0,
              grade: subject.letter_grade || 'F'
            })) || []
          
          setRecentGrades(recentGradesData)
        } else {
          console.error('Failed to fetch academic details, status:', response.status)
        }

        // Lấy lịch học tuần này
        const scheduleResponse = await fetch(`http://localhost:8000/class-registers/student/${userInfo.student_id}`)
        if (scheduleResponse.ok) {
          const classRegisters = await scheduleResponse.json()
          console.log('Class registers data:', classRegisters) // Debug log
          
          // Lấy thông tin chi tiết 3 lớp đầu tiên cho tuần này
          const upcomingData = await Promise.all(
            classRegisters.slice(0, 3).map(async (register: any) => {
              try {
                const classResponse = await fetch(`http://localhost:8000/classes/${register.class_id}`)
                if (classResponse.ok) {
                  const classData = await classResponse.json()
                  
                  const subjectResponse = await fetch(`http://localhost:8000/subjects/${classData.subject_id}`)
                  if (subjectResponse.ok) {
                    const subjectData = await subjectResponse.json()
                    
                    const daysOfWeek = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7']
                    
                    return {
                      subject: subjectData.subject_name,
                      time: `${classData.start_time || '07:00'}-${classData.end_time || '08:50'}`,
                      room: classData.room || 'TBA',
                      day: daysOfWeek[classData.day_of_week] || 'T2'
                    }
                  }
                }
              } catch (error) {
                console.error('Error fetching class details:', error)
              }
              return null
            })
          )
          
          setUpcomingSchedule(upcomingData.filter(item => item !== null))
        } else {
          console.error('Failed to fetch class registers, status:', scheduleResponse.status)
        }
      } catch (error) {
        console.error('Error fetching dashboard data:', error)
      }
    }

    fetchDashboardData()
  }, [userInfo])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Chào mừng, {userInfo?.student_name}!
          </h1>
          <p className="text-gray-600 mt-1">
            Mã sinh viên: {userInfo?.student_id} | Học kỳ: 2023-2024.2
          </p>
        </div>
        <div className="text-sm text-gray-500">
          Hôm nay: {new Date().toLocaleDateString('vi-VN', { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
          })}
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-3 bg-blue-100 rounded-lg">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">GPA hiện tại</p>
              <p className="text-2xl font-bold text-gray-900">{quickStats.currentGPA}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-3 bg-green-100 rounded-lg">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">Tổng tín chỉ</p>
              <p className="text-2xl font-bold text-gray-900">{quickStats.totalCredits}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-3 bg-yellow-100 rounded-lg">
              <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">Môn đã hoàn thành</p>
              <p className="text-2xl font-bold text-gray-900">{quickStats.completedSubjects}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-3 bg-red-100 rounded-lg">
              <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">Kỳ thi sắp tới</p>
              <p className="text-2xl font-bold text-gray-900">{quickStats.upcomingExams}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Grades */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Điểm số gần đây</h2>
            <button 
              onClick={() => navigate('/student/grades')}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              Xem tất cả →
            </button>
          </div>
          <div className="space-y-3">
            {recentGrades.map((grade, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-gray-900">{grade.subject}</p>
                  <p className="text-xs text-gray-600">Điểm tổng kết</p>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-gray-900">{grade.score}</p>
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    grade.grade === 'A' ? 'bg-green-100 text-green-800' :
                    grade.grade === 'B+' || grade.grade === 'B' ? 'bg-blue-100 text-blue-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}>
                    {grade.grade}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Upcoming Schedule */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Lịch học tuần này</h2>
            <button 
              onClick={() => navigate('/student/schedule')}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              Xem thời khóa biểu →
            </button>
          </div>
          <div className="space-y-3">
            {upcomingSchedule.map((schedule, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-gray-900">{schedule.subject}</p>
                  <p className="text-xs text-gray-600">{schedule.day} • {schedule.time}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-blue-600">📍 {schedule.room}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Thao tác nhanh</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button 
            onClick={() => navigate('/student/schedule')}
            className="p-4 text-center border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <div className="text-2xl mb-2">📅</div>
            <p className="text-sm font-medium text-gray-900">Thời khóa biểu</p>
          </button>
          <button 
            onClick={() => navigate('/student/grades')}
            className="p-4 text-center border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <div className="text-2xl mb-2">📊</div>
            <p className="text-sm font-medium text-gray-900">Xem điểm</p>
          </button>
          <button 
            onClick={() => navigate('/student/curriculum')}
            className="p-4 text-center border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <div className="text-2xl mb-2">📖</div>
            <p className="text-sm font-medium text-gray-900">Chương trình đào tạo</p>
          </button>
          <button 
            onClick={() => navigate('/student/forms')}
            className="p-4 text-center border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <div className="text-2xl mb-2">📄</div>
            <p className="text-sm font-medium text-gray-900">Biểu mẫu</p>
          </button>
        </div>
      </div>

      {/* Announcements */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Thông báo mới</h2>
        <div className="space-y-4">
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h3 className="text-sm font-medium text-blue-900 mb-1">
              📢 Thông báo đăng ký học kỳ 2024.1
            </h3>
            <p className="text-sm text-blue-800 mb-2">
              Thời gian đăng ký từ 15/01 đến 30/01/2024. Sinh viên vui lòng đăng ký theo đúng thời gian quy định.
            </p>
            <p className="text-xs text-blue-600">2 giờ trước</p>
          </div>
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
            <h3 className="text-sm font-medium text-green-900 mb-1">
              🎓 Học bổng khuyến khích học tập
            </h3>
            <p className="text-sm text-green-800 mb-2">
              Mở đăng ký học bổng cho sinh viên có kết quả học tập xuất sắc trong học kỳ vừa qua.
            </p>
            <p className="text-xs text-green-600">3 ngày trước</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default StudentDashboard
