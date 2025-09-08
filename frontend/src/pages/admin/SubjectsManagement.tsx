import { useState, useEffect } from 'react'

interface Subject {
  id: number
  subject_id: string
  subject_name: string
  credits: number
  department_id?: number
  description?: string
  conditional_subjects?: string
}

const SubjectsManagement = () => {
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [loading, setLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    fetchSubjects()
  }, [])

  const fetchSubjects = async () => {
    setLoading(true)
    try {
      const response = await fetch('http://localhost:8000/subjects')
      if (response.ok) {
        const data = await response.json()
        setSubjects(data)
      } else {
        console.error('Failed to fetch subjects')
        setSubjects([])
      }
    } catch (error) {
      console.error('Error fetching subjects:', error)
      setSubjects([])
    }
    setLoading(false)
  }

  const filteredSubjects = subjects.filter(subject => 
    subject.subject_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    subject.subject_id.toLowerCase().includes(searchTerm.toLowerCase())
  )

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
        <h1 className="text-3xl font-bold text-gray-900">Quản lý môn học</h1>
        <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
          ➕ Thêm môn học
        </button>
      </div>

      {/* Search */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <input
          type="text"
          placeholder="Tìm kiếm theo tên môn học, mã môn, khoa..."
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {/* Subjects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredSubjects.map((subject) => (
          <div key={subject.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {subject.subject_name}
                </h3>
                <div className="space-y-2">
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Mã môn:</span> {subject.subject_id}
                  </p>
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Số tín chỉ:</span> {subject.credits}
                  </p>
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Khoa:</span> {subject.department_id || 'Chưa phân khoa'}
                  </p>
                  {subject.conditional_subjects && (
                    <p className="text-sm text-gray-600">
                      <span className="font-medium">Môn tiên quyết:</span> {subject.conditional_subjects}
                    </p>
                  )}
                </div>
                <p className="text-sm text-gray-700 mt-3">
                  {subject.description || 'Chưa có mô tả'}
                </p>
              </div>
            </div>
            
            <div className="flex justify-end space-x-2 mt-4 pt-4 border-t border-gray-200">
              <button className="px-3 py-1 text-sm text-blue-600 hover:text-blue-900 hover:bg-blue-50 rounded transition">
                👁️ Xem
              </button>
              <button className="px-3 py-1 text-sm text-yellow-600 hover:text-yellow-900 hover:bg-yellow-50 rounded transition">
                ✏️ Sửa
              </button>
              <button className="px-3 py-1 text-sm text-red-600 hover:text-red-900 hover:bg-red-50 rounded transition">
                🗑️ Xóa
              </button>
            </div>
          </div>
        ))}
      </div>

      {filteredSubjects.length === 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <p className="text-gray-500">Không tìm thấy môn học nào</p>
        </div>
      )}
    </div>
  )
}

export default SubjectsManagement
