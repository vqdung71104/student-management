import { useState, useEffect, useRef } from 'react'
import * as XLSX from 'xlsx'

interface Student {
  id: number
  student_name: string
  email: string
  course_id: number
  department_id: number
  // Auto-calculated fields
  cpa?: number
  credits_accumulated?: number
  credits_registered?: number
  credits_passed?: number
  failed_subjects_number?: number
  study_subjects_number?: number
  total_failed_credits?: number
  total_learned_credits?: number
  year_level?: string
  warning_level?: string
  level_3_warning_number?: number
}

interface StudentFormData {
  student_name: string
  email: string
  password: string
  course_id: number
  department_id: number
}

const StudentsManagement = () => {
  const [students, setStudents] = useState<Student[]>([])
  const [loading, setLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showViewModal, setShowViewModal] = useState(false)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [selectedStudent, setSelectedStudent] = useState<Student | null>(null)
  const [formData, setFormData] = useState<StudentFormData>({
    student_name: '',
    email: '',
    password: '',
    course_id: 1,
    department_id: 1,
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
      const response = await fetch(`http://localhost:8000/students/${selectedStudent.id}`, {
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

  const handleDeleteStudent = async (studentId: number) => {
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
      student_name: '',
      email: '',
      password: '',
      course_id: 1,
      department_id: 1,
    })
  }

  const openCreateModal = () => {
    resetForm()
    setShowCreateModal(true)
  }

  const openEditModal = (student: Student) => {
    setSelectedStudent(student)
    setFormData({
      student_name: student.student_name,
      email: student.email,
      password: '', // Don't populate password for security
      course_id: student.course_id,
      department_id: student.department_id,
    })
    setShowEditModal(true)
  }

  const openViewModal = (student: Student) => {
    setSelectedStudent(student)
    setShowViewModal(true)
  }

  const filteredStudents = students.filter(student => {
    const matchesSearch = student.student_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         student.id.toString().includes(searchTerm) ||
                         student.email.toLowerCase().includes(searchTerm.toLowerCase())
    
    return matchesSearch // Removed learning_status filter since field no longer exists
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
        <div className="flex space-x-2">
          <button 
            onClick={() => setShowUploadModal(true)}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
          >
            📊 Upload Excel
          </button>
          <button 
            onClick={openCreateModal}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            ➕ Thêm sinh viên
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Tìm kiếm theo tên, ID, email..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* Students Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ID
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
                  CPA
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
                    {student.id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {student.student_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {student.email}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {student.department_id || 'N/A'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {student.course_id || 'N/A'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {student.cpa ? student.cpa.toFixed(2) : 'N/A'}
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
                      onClick={() => handleDeleteStudent(student.id)}
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
                placeholder="Họ tên"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.student_name}
                onChange={(e) => setFormData({...formData, student_name: e.target.value})}
              />
              <input
                type="email"
                placeholder="Email"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
              />
              <input
                type="password"
                placeholder="Mật khẩu"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
              />
              <input
                type="number"
                placeholder="Mã khóa học (Course ID)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.course_id}
                onChange={(e) => setFormData({...formData, course_id: parseInt(e.target.value)})}
              />
              <input
                type="number"
                placeholder="Mã Trường/Viện (Department ID)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.department_id}
                onChange={(e) => setFormData({...formData, department_id: parseInt(e.target.value)})}
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
                placeholder="Họ tên"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.student_name}
                onChange={(e) => setFormData({...formData, student_name: e.target.value})}
              />
              <input
                type="email"
                placeholder="Email"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
              />
              <input
                type="password"
                placeholder="Mật khẩu mới (để trống nếu không thay đổi)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
              />
              <input
                type="number"
                placeholder="Mã khóa học (Course ID)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.course_id}
                onChange={(e) => setFormData({...formData, course_id: parseInt(e.target.value)})}
              />
              <input
                type="number"
                placeholder="Mã Trường/Viện (Department ID)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.department_id}
                onChange={(e) => setFormData({...formData, department_id: parseInt(e.target.value)})}
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
              <div><strong>ID:</strong> {selectedStudent.id}</div>
              <div><strong>Họ tên:</strong> {selectedStudent.student_name}</div>
              <div><strong>Email:</strong> {selectedStudent.email}</div>
              <div><strong>Trường/Viện ID:</strong> {selectedStudent.department_id}</div>
              <div><strong>Khóa học ID:</strong> {selectedStudent.course_id}</div>
              <div><strong>CPA:</strong> {selectedStudent.cpa ? selectedStudent.cpa.toFixed(2) : 'Chưa có'}</div>
              <div><strong>Tín chỉ tích lũy:</strong> {selectedStudent.credits_accumulated || 0}</div>
              <div><strong>Tín chỉ đã đăng ký:</strong> {selectedStudent.credits_registered || 0}</div>
              <div><strong>Tín chỉ đã qua:</strong> {selectedStudent.credits_passed || 0}</div>
              <div><strong>Năm học:</strong> {selectedStudent.year_level || 'Chưa xác định'}</div>
              <div><strong>Mức cảnh báo:</strong> {selectedStudent.warning_level || 'Không'}</div>
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

      {showUploadModal && (
        <StudentUploadModal 
          onClose={() => setShowUploadModal(false)} 
          onSuccess={() => {
            fetchStudents()
            setShowUploadModal(false)
          }} 
        />
      )}
    </div>
  )
}

// Component StudentUploadModal
const StudentUploadModal = ({ onClose, onSuccess }: { onClose: () => void, onSuccess: () => void }) => {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0])
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
    }
  }

  const processExcelFile = async (file: File): Promise<any[]> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const data = new Uint8Array(e.target?.result as ArrayBuffer)
          const workbook = XLSX.read(data, { type: 'array' })
          const worksheet = workbook.Sheets[workbook.SheetNames[0]]
          const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 })
          
          // Tìm dòng header có chứa các cột cần thiết
          let headerRowIndex = -1
          for (let i = 0; i < jsonData.length; i++) {
            const row = jsonData[i] as any[]
            if (row.some(cell => 
              cell && (
                String(cell).toLowerCase().includes('họ và tên') || 
                String(cell).toLowerCase().includes('mssv') ||
                String(cell).toLowerCase().includes('năm nhập học') ||
                String(cell).toLowerCase().includes('giới tính') ||
                String(cell).toLowerCase().includes('ngành học')
              )
            )) {
              headerRowIndex = i
              break
            }
          }

          if (headerRowIndex === -1) {
            throw new Error('Không tìm thấy header có các cột: Họ và tên, MSSV, Năm nhập học')
          }

          const headers = jsonData[headerRowIndex] as any[]
          const students: any[] = []

          // Tìm index của các cột cần thiết
          const nameIndex = headers.findIndex((h: any) => 
            h && String(h).toLowerCase().includes('họ và tên')
          )
          const emailIndex = headers.findIndex((h: any) => 
            h && String(h).toLowerCase().includes('email')
          )
          const courseIndex = headers.findIndex((h: any) => 
            h && String(h).toLowerCase().includes('ngành học')
          )
          const departmentIndex = headers.findIndex((h: any) => 
            h && String(h).toLowerCase().includes('trường/viện')
          )

          if (nameIndex === -1 || emailIndex === -1) {
            throw new Error('Không tìm thấy các cột bắt buộc: Họ và tên, Email')
          }

          // Xử lý dữ liệu từ các dòng sau header
          for (let i = headerRowIndex + 1; i < jsonData.length; i++) {
            const row = jsonData[i] as any[]
            
            if (row && row.length > 0 && row[nameIndex] && row[emailIndex]) {
              // Map course code to course_id
              const courseCode = courseIndex !== -1 ? String(row[courseIndex] || '').trim() : 'IT-E6'
              let courseId = 1 // Default to IT-E6 course
              if (courseCode === 'IT-E6') {
                courseId = 1
              }

              const departmentId = departmentIndex !== -1 ? parseInt(String(row[departmentIndex] || '1').trim()) : 1

              const student = {
                student_name: String(row[nameIndex] || '').trim(),
                email: String(row[emailIndex] || '').trim(),
                password: 'default123', // Default password for bulk upload
                course_id: courseId,
                department_id: departmentId
              }

              if (student.student_name && student.email) {
                students.push(student)
              }
            }
          }

          resolve(students)
        } catch (error) {
          reject(error)
        }
      }
      reader.onerror = () => reject(new Error('Không thể đọc file'))
      reader.readAsArrayBuffer(file)
    })
  }

  const handleUpload = async () => {
    if (!file) {
      alert('Vui lòng chọn file Excel')
      return
    }

    setLoading(true)
    try {
      const students = await processExcelFile(file)
      
      if (students.length === 0) {
        alert('Không tìm thấy dữ liệu sinh viên hợp lệ trong file')
        setLoading(false)
        return
      }

      // Log dữ liệu để debug
      console.log('Processed students data:', students)

      // Gửi từng sinh viên lên server
      let successCount = 0
      let errorCount = 0
      
      for (const student of students) {
        console.log('Sending student:', student)
        try {
          const response = await fetch('http://localhost:8000/students/', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(student)
          })
          
          if (response.ok) {
            successCount++
            console.log(`✓ Tạo thành công sinh viên ${student.student_name}`)
          } else {
            const errorText = await response.text()
            if (errorText.includes('email đã tồn tại') || errorText.includes('duplicate key')) {
              console.log(`⚠ Sinh viên ${student.student_name} (${student.email}) đã tồn tại, bỏ qua`)
            } else {
              errorCount++
              console.error(`✗ Lỗi khi tạo sinh viên ${student.student_name}:`, errorText)
            }
          }
        } catch (error) {
          errorCount++
          console.error(`✗ Lỗi khi tạo sinh viên ${student.student_name}:`, error)
        }
      }

      const duplicateCount = students.length - successCount - errorCount
      let message = `Hoàn thành! Tạo thành công ${successCount} sinh viên`
      if (duplicateCount > 0) {
        message += `, bỏ qua ${duplicateCount} sinh viên đã tồn tại`
      }
      if (errorCount > 0) {
        message += `, lỗi ${errorCount} sinh viên`
      }
      alert(message)
      
      if (successCount > 0) {
        onSuccess()
      }
      onClose()
    } catch (error) {
      console.error('Error processing file:', error)
      alert('Có lỗi khi xử lý file: ' + (error as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white p-6 rounded-lg max-w-md w-full mx-4">
        <h3 className="text-xl font-bold mb-4">Upload danh sách sinh viên</h3>
        
        <div 
          className={`border-2 border-dashed rounded-lg p-6 text-center ${
            dragActive ? 'border-blue-400 bg-blue-50' : 'border-gray-300'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          {file ? (
            <div className="text-green-600">
              <p>📁 {file.name}</p>
              <p className="text-sm text-gray-500 mt-1">
                Kích thước: {(file.size / 1024).toFixed(1)} KB
              </p>
            </div>
          ) : (
            <div>
              <p className="text-gray-600 mb-2">
                Kéo thả file Excel vào đây hoặc
              </p>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              >
                Chọn file
              </button>
              <p className="text-sm text-gray-500 mt-2">
                Hỗ trợ file .xlsx, .xls
              </p>
            </div>
          )}
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept=".xlsx,.xls"
          onChange={handleFileChange}
          className="hidden"
        />

        <div className="mt-4 text-sm text-gray-600">
          <p className="font-semibold mb-1">Yêu cầu định dạng Excel:</p>
          <ul className="text-xs">
            <li>• Họ và tên (bắt buộc)</li>
            <li>• Email (bắt buộc)</li>
            <li>• Mã ngành/Course ID (tùy chọn, mặc định: 1)</li>
            <li>• Mã Trường/Viện/Department ID (tùy chọn, mặc định: 1)</li>
            <li>• Mật khẩu mặc định: default123</li>
          </ul>
        </div>

        <div className="flex justify-end space-x-2 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 border rounded hover:bg-gray-50"
            disabled={loading}
          >
            Hủy
          </button>
          <button
            onClick={handleUpload}
            disabled={!file || loading}
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            {loading ? 'Đang xử lý...' : 'Upload'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default StudentsManagement
