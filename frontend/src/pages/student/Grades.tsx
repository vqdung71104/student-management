import { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import AddGradeForm from '../../components/AddGradeForm'
import GradeExcelUpload from '../../components/GradeExcelUpload'

interface Grade {
  id: number
  subject_code: string  // Mã HP như "IT3080" (từ Subject.subject_id)
  subject_name: string
  credits: number
  semester: string
  attendance_score?: number
  midterm_score?: number
  final_score?: number
  total_score?: number
  letter_grade?: string
  gpa_4?: number
}

interface SemesterGPA {
  semester: string
  gpa_10: number
  gpa_4: number
  total_credits: number
  completed_credits: number
}

const Grades = () => {
  const { userInfo } = useAuth()
  const [grades, setGrades] = useState<Grade[]>([])
  const [semesterGPAs, setSemesterGPAs] = useState<SemesterGPA[]>([])
  const [overallGPAData, setOverallGPAData] = useState({
    gpa_10: '0.00',
    gpa_4: '0.00', 
    total_credits: 0
  })
  const [loading, setLoading] = useState(true)
  const [selectedSemester, setSelectedSemester] = useState('all')
  const [showAddForm, setShowAddForm] = useState(false)
  const [showExcelUpload, setShowExcelUpload] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [deletingId, setDeletingId] = useState<number | null>(null)

  useEffect(() => {
    fetchGrades()
  }, [])

  const fetchGrades = async () => {
    setLoading(true)
    try {
      if (!userInfo?.student_id) {
        console.log('No student_id found in userInfo:', userInfo)
        setLoading(false)
        return
      }

      console.log('Fetching academic details for student:', userInfo.student_id)
      
      // Lấy thông tin chi tiết học tập từ API
      const response = await fetch(`http://localhost:8000/api/students/${userInfo.student_id}/academic-details`)
      console.log('Response status:', response.status)
      
      if (response.ok) {
        const data = await response.json()
        console.log('Academic details response:', data)
        
        // Chuyển đổi learned_subjects thành định dạng grades
        const gradesData = (data.learned_subjects || []).map((subject: any) => ({
          id: subject.id,
          subject_code: subject.subject_code || 'N/A', // Mã HP từ Subject.subject_id (backend đã trả về)
          subject_name: subject.subject_name,
          credits: subject.credits,
          semester: subject.semester,
          attendance_score: null, // Not available in current API
          midterm_score: subject.midterm_score,
          final_score: subject.final_score,
          total_score: subject.total_score,
          letter_grade: subject.letter_grade,
          gpa_4: null // Can calculate from letter_grade if needed
        }))
        
        console.log('Processed grades data:', gradesData)
        setGrades(gradesData)
        
        // Chuyển đổi semester_gpas thành định dạng frontend expect
        const semesterGPAsData = (data.semester_gpas || []).map((semGpa: any) => ({
          semester: semGpa.semester,
          gpa_10: semGpa.gpa || 0, // API trả về 'gpa', frontend expect 'gpa_10'
          gpa_4: semGpa.gpa ? (semGpa.gpa * 4 / 10).toFixed(2) : '0.00', // Convert 10-scale to 4-scale
          total_credits: semGpa.total_credits || 0,
          completed_credits: semGpa.total_credits || 0 // Assume all credits are completed
        }))
        
        console.log('Processed semester GPAs data:', semesterGPAsData)
        setSemesterGPAs(semesterGPAsData)
        
        // Set overall GPA data from API response
        setOverallGPAData({
          gpa_10: data.overall_gpa?.toFixed(2) || '0.00',
          gpa_4: data.overall_gpa ? (data.overall_gpa * 4 / 10).toFixed(2) : '0.00',
          total_credits: data.total_credits || 0
        })
      } else {
        const errorText = await response.text()
        console.error('Failed to fetch academic details:', response.status, errorText)
        setGrades([])
        setSemesterGPAs([])
      }
    } catch (error) {
      console.error('Error fetching grades:', error)
      setGrades([])
      setSemesterGPAs([])
    }
    setLoading(false)
  }

  const handleAddGrade = async (data: { subject_code: string; semester: string; letter_grade: string }) => {
    setSubmitting(true)
    try {
      const response = await fetch('http://localhost:8000/api/learned-subjects/create-new-learned-subject', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          student_id: userInfo?.student_id,
          subject_id: data.subject_code,  // Đổi từ data.subject_id sang data.subject_code
          semester: data.semester,
          letter_grade: data.letter_grade
        })
      })

      if (response.ok) {
        const result = await response.json()
        alert(`✅ ${result.message}`)
        setShowAddForm(false)
        fetchGrades() // Refresh data
      } else {
        const error = await response.json()
        alert(`❌ Lỗi: ${error.detail}`)
      }
    } catch (error) {
      console.error('Error adding grade:', error)
      alert('❌ Có lỗi xảy ra khi thêm môn học')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDeleteGrade = async (gradeId: number, subjectName: string) => {
    // Hộp thoại xác nhận
    const confirmed = window.confirm(
      `Bạn có chắc chắn muốn xóa môn học "${subjectName}" không?\n\nHành động này không thể hoàn tác.`
    )
    
    if (!confirmed) return

    setDeletingId(gradeId)
    try {
      const response = await fetch(`http://localhost:8000/api/learned-subjects/${gradeId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        alert('✅ Đã xóa môn học thành công!')
        fetchGrades() // Refresh data
      } else {
        const error = await response.json()
        alert(`❌ Lỗi: ${error.detail || 'Không thể xóa môn học'}`)
      }
    } catch (error) {
      console.error('Error deleting grade:', error)
      alert('❌ Có lỗi xảy ra khi xóa môn học')
    } finally {
      setDeletingId(null)
    }
  }

  const getLetterGradeColor = (grade: string) => {
    switch (grade) {
      case 'A+':
      case 'A':
        return 'bg-green-100 text-green-800'
      case 'B+':
      case 'B':
        return 'bg-blue-100 text-blue-800'
      case 'C+':
      case 'C':
        return 'bg-yellow-100 text-yellow-800'
      case 'D+':
      case 'D':
        return 'bg-orange-100 text-orange-800'
      case 'F':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const filteredGrades = selectedSemester === 'all' 
    ? grades 
    : grades.filter(grade => grade.semester === selectedSemester)

  const semesters = Array.from(new Set(grades.map(grade => grade.semester))).sort().reverse()
  
  // Use overallGPAData instead of calculating from semesterGPAs

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    )
  }
  

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Xem điểm</h1>
        <div className="flex items-center space-x-4">
          <div className="text-sm text-gray-600">
            Sinh viên: {userInfo?.student_name}
          </div>
          <button
            onClick={() => setShowAddForm(true)}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition flex items-center space-x-2"
          >
            <span>➕</span>
            <span>Thêm môn học</span>
          </button>
          <button
            onClick={() => setShowExcelUpload(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center space-x-2"
          >
            <span>📊</span>
            <span>Upload Excel</span>
          </button>
        </div>
      </div>

      {/* GPA Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Điểm tổng kết</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600">Điểm CPA:</span>
              <span className="font-bold text-blue-600">{overallGPAData.gpa_10}</span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-gray-600">Tổng tín chỉ:</span>
              <span className="font-bold text-gray-900">{overallGPAData.total_credits}</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Học kỳ hiện tại</h3>
          {semesterGPAs.length > 0 && (
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">Học kỳ:</span>
                <span className="font-bold">{semesterGPAs[semesterGPAs.length - 1].semester}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">GPA:</span>
                <span className="font-bold text-green-600">{semesterGPAs[semesterGPAs.length - 1].gpa_10}</span>
              </div>
              
            </div>
          )}
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Thống kê</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600">Số môn đã học:</span>
              <span className="font-bold">{grades.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Số học kỳ:</span>
              <span className="font-bold">{semesterGPAs.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Điểm cao nhất:</span>
              <span className="font-bold text-green-600">
                {Math.max(...grades.map(g => g.total_score || 0)).toFixed(1)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Semester Filter */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center space-x-4">
          <label className="text-sm font-medium text-gray-700">Lọc theo học kỳ:</label>
          <select
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            value={selectedSemester}
            onChange={(e) => setSelectedSemester(e.target.value)}
          >
            <option value="all">Tất cả học kỳ</option>
            {semesters.map(semester => (
              <option key={semester} value={semester}>Học kỳ {semester}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Grades Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Mã môn
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tên môn học
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Số tín chỉ
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Điểm chữ
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Học kỳ
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Thao tác
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredGrades.map((grade) => (
                <tr key={grade.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {grade.subject_code}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {grade.subject_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-center">
                    {grade.credits}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    {grade.letter_grade && (
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getLetterGradeColor(grade.letter_grade)}`}>
                        {grade.letter_grade}
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-center">
                    {grade.semester}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <button
                      onClick={() => handleDeleteGrade(grade.id, grade.subject_name)}
                      disabled={deletingId === grade.id}
                      className={`px-3 py-1 text-xs font-medium rounded-lg transition ${
                        deletingId === grade.id
                          ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                          : 'bg-red-100 text-red-700 hover:bg-red-200 hover:text-red-800'
                      }`}
                      title="Xóa môn học"
                    >
                      {deletingId === grade.id ? '⏳' : '🗑️ Xóa'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {filteredGrades.length === 0 && (
          <div className="text-center py-8">
            <p className="text-gray-500">Chưa có điểm số nào</p>
          </div>
        )}
      </div>

      {/* Modals */}
      {showAddForm && (
        <AddGradeForm
          onSubmit={handleAddGrade}
          onClose={() => setShowAddForm(false)}
          loading={submitting}
        />
      )}

      {showExcelUpload && (
        <GradeExcelUpload
          onClose={() => setShowExcelUpload(false)}
          onSuccess={() => {
            setShowExcelUpload(false)
            fetchGrades() // Refresh data after successful upload
          }}
        />
      )}
    </div>
  )
}

export default Grades
