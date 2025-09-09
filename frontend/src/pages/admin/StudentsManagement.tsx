import { useState, useEffect } from 'react'

interface Student {
  id: number
  student_id: string
  student_name: string
  enrolled_year: number
  course_id: number
  training_level: string
  learning_status: string
  gender: string
  classes?: string
  newest_semester?: string
  department_id?: string
  email: string
  // Auto-calculated fields
  cpa: number
  failed_subjects_number: number
  study_subjects_number: number
  total_failed_credits: number
  total_learned_credits: number
  year_level: string
  warning_level: string
  level_3_warning_number: number
}

interface StudentFormData {
  student_id: string
  student_name: string
  enrolled_year: number
  course_id: number
  training_level: string
  learning_status: string
  gender: string
  classes?: string
  newest_semester?: string
  department_id?: string
}

const StudentsManagement = () => {
  const [students, setStudents] = useState<Student[]>([])
  const [loading, setLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [filter, setFilter] = useState('all')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showViewModal, setShowViewModal] = useState(false)
  const [selectedStudent, setSelectedStudent] = useState<Student | null>(null)
  const [formData, setFormData] = useState<StudentFormData>({
    student_id: '',
    student_name: '',
    enrolled_year: new Date().getFullYear(),
    course_id: 1,
    training_level: 'Cử nhân',
    learning_status: 'Đang học',
    gender: 'Nam',
    classes: '',
    newest_semester: '',
    department_id: '',
  })

  useEffect(() => {
    fetchStudents()
  }, [])

  const fetchStudents = async () => {
    setLoading(true)
    try {
      const response = await fetch('http://localhost:8000/students')
      if (response.ok) {
        const data = await response.json()
        setStudents(data)
      } else {
        console.error('Failed to fetch students')
        setStudents([])
      }
    } catch (error) {
      console.error('Error fetching students:', error)
      setStudents([])
    }
    setLoading(false)
  }

  const handleCreateStudent = async () => {
    try {
      const response = await fetch('http://localhost:8000/students/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })
      
      if (response.ok) {
        setShowCreateModal(false)
        fetchStudents()
        resetForm()
        alert('Tạo sinh viên thành công!')
      } else {
        alert('Có lỗi khi tạo sinh viên')
      }
    } catch (error) {
      console.error('Error creating student:', error)
      alert('Có lỗi khi tạo sinh viên')
    }
  }

  const handleUpdateStudent = async () => {
    if (!selectedStudent) return
    
    try {
      const response = await fetch(`http://localhost:8000/students/${selectedStudent.student_id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })
      
      if (response.ok) {
        setShowEditModal(false)
        fetchStudents()
        resetForm()
        alert('Cập nhật sinh viên thành công!')
      } else {
        alert('Có lỗi khi cập nhật sinh viên')
      }
    } catch (error) {
      console.error('Error updating student:', error)
      alert('Có lỗi khi cập nhật sinh viên')
    }
  }

  const handleDeleteStudent = async (studentId: String) => {
    if (!confirm('Bạn có chắc chắn muốn xóa sinh viên này?')) return
    
    try {
      const response = await fetch(`http://localhost:8000/students/${studentId}`, {
        method: 'DELETE',
      })
      
      if (response.ok) {
        fetchStudents()
        alert('Xóa sinh viên thành công!')
      } else {
        alert('Có lỗi khi xóa sinh viên')
      }
    } catch (error) {
      console.error('Error deleting student:', error)
      alert('Có lỗi khi xóa sinh viên')
    }
  }

  const resetForm = () => {
    setFormData({
      student_id: '',
      student_name: '',
      enrolled_year: new Date().getFullYear(),
      course_id: 1,
      training_level: 'Cử nhân',
      learning_status: 'Đang học',
      gender: 'Nam',
      classes: '',
      newest_semester: '',
      department_id: '',
    })
  }

  const openCreateModal = () => {
    resetForm()
    setShowCreateModal(true)
  }

  const openEditModal = (student: Student) => {
    setSelectedStudent(student)
    setFormData({
      student_id: student.student_id,
      student_name: student.student_name,
      enrolled_year: student.enrolled_year,
      course_id: student.course_id,
      training_level: student.training_level,
      learning_status: student.learning_status,
      gender: student.gender,
      classes: student.classes || '',
      newest_semester: student.newest_semester || '',
      department_id: student.department_id || '',
    })
    setShowEditModal(true)
  }

  const openViewModal = (student: Student) => {
    setSelectedStudent(student)
    setShowViewModal(true)
  }

  const filteredStudents = students.filter(student => {
    const matchesSearch = student.student_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         student.student_id.includes(searchTerm) ||
                         student.email.toLowerCase().includes(searchTerm.toLowerCase())
    
    if (filter === 'all') return matchesSearch
    return matchesSearch && student.learning_status === filter
  })

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
        <h1 className="text-3xl font-bold text-gray-900">Quản lý sinh viên</h1>
        <button 
          onClick={openCreateModal}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          ➕ Thêm sinh viên
        </button>
      </div>

      {/* Search and Filter */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Tìm kiếm theo tên, mã sinh viên, email..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <select
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          >
            <option value="all">Tất cả trạng thái</option>
            <option value="Đang học">Đang học</option>
            <option value="Bảo lưu">Bảo lưu</option>
            <option value="Thôi học">Thôi học</option>
            <option value="Buộc thôi học">Buộc thôi học</option>
          </select>
        </div>
      </div>

      {/* Students Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Mã SV
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Họ tên
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Email
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Trường/Viện
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Khoá
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Trạng thái
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Thao tác
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredStudents.map((student) => (
                <tr key={student.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {student.student_id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {student.student_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {student.email}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {student.department_id || 'Chưa phân Trường/Viện'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {student.course_id || 'Chưa phân khóa'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      student.learning_status === 'Đang học'
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {student.learning_status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                    <button 
                      onClick={() => openViewModal(student)}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      👁️ Xem
                    </button>
                    <button 
                      onClick={() => openEditModal(student)}
                      className="text-yellow-600 hover:text-yellow-900"
                    >
                      ✏️ Sửa
                    </button>
                    <button 
                      onClick={() => handleDeleteStudent(student.student_id)}
                      className="text-red-600 hover:text-red-900"
                    >
                      🗑️ Xóa
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {filteredStudents.length === 0 && (
          <div className="text-center py-8">
            <p className="text-gray-500">Không tìm thấy sinh viên nào</p>
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Thêm sinh viên mới</h2>
            <div className="space-y-4">
              <input
                type="text"
                placeholder="Mã sinh viên"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.student_id}
                onChange={(e) => setFormData({...formData, student_id: e.target.value})}
              />
              <input
                type="text"
                placeholder="Họ tên"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.student_name}
                onChange={(e) => setFormData({...formData, student_name: e.target.value})}
              />
              <input
                type="number"
                placeholder="Năm nhập học"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.enrolled_year}
                onChange={(e) => setFormData({...formData, enrolled_year: parseInt(e.target.value)})}
              />
              <input
                type="number"
                placeholder="Mã khóa học"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.course_id}
                onChange={(e) => setFormData({...formData, course_id: parseInt(e.target.value)})}
              />
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.training_level}
                onChange={(e) => setFormData({...formData, training_level: e.target.value})}
              >
                <option value="Cử nhân">Cử nhân</option>
                <option value="Kỹ sư">Kỹ sư</option>
                <option value="Thạc sỹ">Thạc sỹ</option>
                <option value="Tiến sỹ">Tiến sỹ</option>
              </select>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.learning_status}
                onChange={(e) => setFormData({...formData, learning_status: e.target.value})}
              >
                <option value="Đang học">Đang học</option>
                <option value="Bảo lưu">Bảo lưu</option>
                <option value="Thôi học">Thôi học</option>
                <option value="Buộc thôi học">Buộc thôi học</option>
              </select>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.gender}
                onChange={(e) => setFormData({...formData, gender: e.target.value})}
              >
                <option value="Nam">Nam</option>
                <option value="Nữ">Nữ</option>
              </select>
              <input
                type="text"
                placeholder="Lớp (tùy chọn)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.classes}
                onChange={(e) => setFormData({...formData, classes: e.target.value})}
              />
              <input
                type="text"
                placeholder="Học kỳ mới nhất (tùy chọn)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.newest_semester}
                onChange={(e) => setFormData({...formData, newest_semester: e.target.value})}
              />
              <input
                type="text"
                placeholder="Mã Trường/Viện (tùy chọn)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.department_id}
                onChange={(e) => setFormData({...formData, department_id: e.target.value})}
              />
            </div>
            <div className="flex justify-end space-x-2 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Hủy
              </button>
              <button
                onClick={handleCreateStudent}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Tạo
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Sửa thông tin sinh viên</h2>
            <div className="space-y-4">
              <input
                type="text"
                placeholder="Mã sinh viên"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.student_id}
                onChange={(e) => setFormData({...formData, student_id: e.target.value})}
              />
              <input
                type="text"
                placeholder="Họ tên"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.student_name}
                onChange={(e) => setFormData({...formData, student_name: e.target.value})}
              />
              <input
                type="number"
                placeholder="Năm nhập học"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.enrolled_year}
                onChange={(e) => setFormData({...formData, enrolled_year: parseInt(e.target.value)})}
              />
              <input
                type="number"
                placeholder="Mã khóa học"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.course_id}
                onChange={(e) => setFormData({...formData, course_id: parseInt(e.target.value)})}
              />
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.training_level}
                onChange={(e) => setFormData({...formData, training_level: e.target.value})}
              >
                <option value="Cử nhân">Cử nhân</option>
                <option value="Kỹ sư">Kỹ sư</option>
                <option value="Thạc sỹ">Thạc sỹ</option>
                <option value="Tiến sỹ">Tiến sỹ</option>
              </select>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.learning_status}
                onChange={(e) => setFormData({...formData, learning_status: e.target.value})}
              >
                <option value="Đang học">Đang học</option>
                <option value="Bảo lưu">Bảo lưu</option>
                <option value="Thôi học">Thôi học</option>
                <option value="Buộc thôi học">Buộc thôi học</option>
              </select>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.gender}
                onChange={(e) => setFormData({...formData, gender: e.target.value})}
              >
                <option value="Nam">Nam</option>
                <option value="Nữ">Nữ</option>
              </select>
              <input
                type="text"
                placeholder="Lớp (tùy chọn)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.classes}
                onChange={(e) => setFormData({...formData, classes: e.target.value})}
              />
              <input
                type="text"
                placeholder="Học kỳ mới nhất (tùy chọn)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.newest_semester}
                onChange={(e) => setFormData({...formData, newest_semester: e.target.value})}
              />
              <input
                type="text"
                placeholder="Mã Trường/Viện (tùy chọn)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.department_id}
                onChange={(e) => setFormData({...formData, department_id: e.target.value})}
              />
            </div>
            <div className="flex justify-end space-x-2 mt-6">
              <button
                onClick={() => setShowEditModal(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Hủy
              </button>
              <button
                onClick={handleUpdateStudent}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Cập nhật
              </button>
            </div>
          </div>
        </div>
      )}

      {/* View Modal */}
      {showViewModal && selectedStudent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Thông tin sinh viên</h2>
            <div className="space-y-3">
              <div><strong>Mã sinh viên:</strong> {selectedStudent.student_id}</div>
              <div><strong>Họ tên:</strong> {selectedStudent.student_name}</div>
              <div><strong>Email:</strong> {selectedStudent.email}</div>
              <div><strong>Năm nhập học:</strong> {selectedStudent.enrolled_year}</div>
              <div><strong>Trường/Viện:</strong> {selectedStudent.department_id || 'Chưa phân Trường/Viện'}</div>
              <div><strong>Khóa:</strong> {selectedStudent.course_id}</div>
              <div><strong>Bậc đào tạo:</strong> {selectedStudent.training_level}</div>
              <div><strong>Trạng thái học tập:</strong> {selectedStudent.learning_status}</div>
              <div><strong>Giới tính:</strong> {selectedStudent.gender}</div>
              <div><strong>Lớp:</strong> {selectedStudent.classes || 'Chưa có'}</div>
              <div><strong>CPA:</strong> {selectedStudent.cpa}</div>
              <div><strong>Năm học:</strong> {selectedStudent.year_level}</div>
              <div><strong>Mức cảnh báo:</strong> {selectedStudent.warning_level}</div>
            </div>
            <div className="flex justify-end mt-6">
              <button
                onClick={() => setShowViewModal(false)}
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default StudentsManagement
