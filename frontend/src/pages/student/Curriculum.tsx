import { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'

interface CurriculumSubject {
  subject_id: string
  subject_name: string
  credits: number
  letter_grade: string | null
  semester: string | null
  is_completed: boolean
}

interface CurriculumData {
  course_id: string
  course_name: string
  subjects: CurriculumSubject[]
  total_subjects: number
  completed_subjects: number
}

const Curriculum = () => {
  const { userInfo } = useAuth()
  const [curriculumData, setCurriculumData] = useState<CurriculumData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchCurriculum()
  }, [])

  const fetchCurriculum = async () => {
    setLoading(true)
    try {
      if (!userInfo?.id) {
        console.log('No student id found in userInfo:', userInfo)
        setLoading(false)
        return
      }

      console.log('Fetching curriculum for student:', userInfo.id)
      
      const response = await fetch(`http://localhost:8000/courses/${userInfo.id}/curriculum`)
      console.log('Response status:', response.status)
      
      if (response.ok) {
        const data = await response.json()
        console.log('Curriculum response:', data)
        setCurriculumData(data)
      } else {
        const errorText = await response.text()
        console.error('Failed to fetch curriculum:', response.status, errorText)
        setCurriculumData(null)
      }
    } catch (error) {
      console.error('Error fetching curriculum:', error)
      setCurriculumData(null)
    }
    setLoading(false)
  }

  const getLetterGradeColor = (grade: string | null) => {
    if (!grade) return 'bg-gray-100 text-gray-600'
    
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
        return 'bg-gray-100 text-gray-600'
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  if (!curriculumData) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Chương trình đào tạo</h1>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <p className="text-gray-600">Không thể tải dữ liệu chương trình đào tạo.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Chương trình đào tạo</h1>
      </div>

      {/* Course Information */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Thông tin khóa học</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <p className="text-sm text-gray-600">Mã khóa học</p>
            <p className="font-semibold text-gray-900">{curriculumData.course_id}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Tên khóa học</p>
            <p className="font-semibold text-gray-900">{curriculumData.course_name}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Tiến độ</p>
            <p className="font-semibold text-blue-600">
              {curriculumData.completed_subjects}/{curriculumData.total_subjects} môn
              <span className="text-sm text-gray-500 ml-2">
                ({Math.round((curriculumData.completed_subjects / curriculumData.total_subjects) * 100)}%)
              </span>
            </p>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Tiến độ học tập</h3>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div 
            className="bg-blue-600 h-3 rounded-full transition-all duration-300"
            style={{ 
              width: `${(curriculumData.completed_subjects / curriculumData.total_subjects) * 100}%` 
            }}
          ></div>
        </div>
        <div className="flex justify-between text-sm text-gray-600 mt-2">
          <span>Đã hoàn thành: {curriculumData.completed_subjects} môn</span>
          <span>Còn lại: {curriculumData.total_subjects - curriculumData.completed_subjects} môn</span>
        </div>
      </div>

      {/* Subjects Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Danh sách môn học</h3>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Mã môn học
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tên môn học
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tín chỉ
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Điểm chữ
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Học kỳ
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Trạng thái
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {curriculumData.subjects.map((subject, index) => (
                <tr key={subject.subject_id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {subject.subject_id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {subject.subject_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {subject.credits}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {subject.letter_grade ? (
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getLetterGradeColor(subject.letter_grade)}`}>
                        {subject.letter_grade}
                      </span>
                    ) : (
                      <span className="text-gray-400 text-sm">Chưa có</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {subject.semester || 'Chưa học'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {subject.is_completed ? (
                      <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                        Đã hoàn thành
                      </span>
                    ) : (
                      <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">
                        Chưa hoàn thành
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default Curriculum
