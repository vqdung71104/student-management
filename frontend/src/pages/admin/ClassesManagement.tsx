import { useState, useEffect } from 'react'

interface Subject {
  id: number
  subject_id: string
  subject_name: string
  credits: number
  duration: number
  tuition_fee: number
  english_subject_name: string
  weight: number
  conditional_subjects?: string
  department: {
    id: string
    name: string
  }
}

interface Class {
  id: number
  subject_id: number
  class_id: string
  class_name: string
  linked_class_ids?: string[]
  class_type?: string
  classroom?: string
  study_date?: string
  study_time_start?: string
  study_time_end?: string
  max_student_number?: number
  teacher_name?: string
  study_week: number[]
  subject: Subject
}

interface ClassFormData {
  subject_id: number
  class_id: string
  class_name: string
  linked_class_ids?: string[]
  class_type?: string
  classroom?: string
  study_date?: string
  study_time_start?: string
  study_time_end?: string
  max_student_number?: number
  teacher_name?: string
  study_week: number[]
}

const ClassesManagement = () => {
  const [classes, setClasses] = useState<Class[]>([])
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [loading, setLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showViewModal, setShowViewModal] = useState(false)
  const [selectedClass, setSelectedClass] = useState<Class | null>(null)
  const [formData, setFormData] = useState<ClassFormData>({
    subject_id: 1,
    class_id: '',
    class_name: '',
    linked_class_ids: [],
    class_type: 'Lý thuyết',
    classroom: '',
    study_date: '',
    study_time_start: '09:00',
    study_time_end: '10:50',
    max_student_number: 50,
    teacher_name: '',
    study_week: [1],
  })

  useEffect(() => {
    fetchClasses()
    fetchSubjects()
  }, [])

  const fetchClasses = async () => {
    setLoading(true)
    try {
      const response = await fetch('http://localhost:8000/classes')
      if (response.ok) {
        const data = await response.json()
        setClasses(data)
      } else {
        console.error('Failed to fetch classes')
        setClasses([])
      }
    } catch (error) {
      console.error('Error fetching classes:', error)
      setClasses([])
    }
    setLoading(false)
  }

  const fetchSubjects = async () => {
    try {
      const response = await fetch('http://localhost:8000/subjects')
      if (response.ok) {
        const data = await response.json()
        setSubjects(data)
      }
    } catch (error) {
      console.error('Error fetching subjects:', error)
    }
  }

  const handleCreateClass = async () => {
    try {
      const response = await fetch('http://localhost:8000/classes/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })
      
      if (response.ok) {
        setShowCreateModal(false)
        fetchClasses()
        resetForm()
        alert('Tạo lớp học thành công!')
      } else {
        alert('Có lỗi khi tạo lớp học')
      }
    } catch (error) {
      console.error('Error creating class:', error)
      alert('Có lỗi khi tạo lớp học')
    }
  }

  const handleUpdateClass = async () => {
    if (!selectedClass) return
    
    try {
      const response = await fetch(`http://localhost:8000/classes/${selectedClass.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })
      
      if (response.ok) {
        setShowEditModal(false)
        fetchClasses()
        resetForm()
        alert('Cập nhật lớp học thành công!')
      } else {
        alert('Có lỗi khi cập nhật lớp học')
      }
    } catch (error) {
      console.error('Error updating class:', error)
      alert('Có lỗi khi cập nhật lớp học')
    }
  }

  const handleDeleteClass = async (classId: number) => {
    if (!confirm('Bạn có chắc chắn muốn xóa lớp học này?')) return
    
    try {
      const response = await fetch(`http://localhost:8000/classes/${classId}`, {
        method: 'DELETE',
      })
      
      if (response.ok) {
        fetchClasses()
        alert('Xóa lớp học thành công!')
      } else {
        alert('Có lỗi khi xóa lớp học')
      }
    } catch (error) {
      console.error('Error deleting class:', error)
      alert('Có lỗi khi xóa lớp học')
    }
  }

  const resetForm = () => {
    setFormData({
      subject_id: 1,
      class_id: '',
      class_name: '',
      linked_class_ids: [],
      class_type: 'Lý thuyết',
      classroom: '',
      study_date: '',
      study_time_start: '09:00',
      study_time_end: '10:50',
      max_student_number: 50,
      teacher_name: '',
      study_week: [1],
    })
  }

  const openCreateModal = () => {
    resetForm()
    setShowCreateModal(true)
  }

  const openEditModal = (classItem: Class) => {
    setSelectedClass(classItem)
    setFormData({
      subject_id: classItem.subject_id,
      class_id: classItem.class_id,
      class_name: classItem.class_name,
      linked_class_ids: classItem.linked_class_ids || [],
      class_type: classItem.class_type || 'Lý thuyết',
      classroom: classItem.classroom || '',
      study_date: classItem.study_date || '',
      study_time_start: classItem.study_time_start || '09:00',
      study_time_end: classItem.study_time_end || '10:50',
      max_student_number: classItem.max_student_number || 50,
      teacher_name: classItem.teacher_name || '',
      study_week: classItem.study_week || [1],
    })
    setShowEditModal(true)
  }

  const openViewModal = (classItem: Class) => {
    setSelectedClass(classItem)
    setShowViewModal(true)
  }

  const filteredClasses = classes.filter(classItem => 
    classItem.class_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    classItem.class_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    classItem.subject.subject_name.toLowerCase().includes(searchTerm.toLowerCase())
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
        <h1 className="text-3xl font-bold text-gray-900">Quản lý lớp học</h1>
        <button 
          onClick={openCreateModal}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          ➕ Thêm lớp học
        </button>
      </div>

      {/* Search */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <input
          type="text"
          placeholder="Tìm kiếm theo tên lớp, mã lớp, học phần..."
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {/* Classes Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredClasses.map((classItem) => (
          <div key={classItem.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {classItem.class_name}
                </h3>
                <div className="space-y-2">
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Mã lớp:</span> {classItem.class_id}
                  </p>
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Học phần:</span> {classItem.subject.subject_name}
                  </p>
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Phòng học:</span> {classItem.classroom || 'Chưa phân phòng'}
                  </p>
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Thời gian:</span> {classItem.study_time_start} - {classItem.study_time_end}
                  </p>
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Ngày học:</span> {classItem.study_date || 'Chưa xác định'}
                  </p>
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Giảng viên:</span> {classItem.teacher_name || 'Chưa phân công'}
                  </p>
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Sĩ số tối đa:</span> {classItem.max_student_number}
                  </p>
                </div>
              </div>
            </div>
            
            <div className="flex justify-end space-x-2 mt-4 pt-4 border-t border-gray-200">
              <button 
                onClick={() => openViewModal(classItem)}
                className="px-3 py-1 text-sm text-blue-600 hover:text-blue-900 hover:bg-blue-50 rounded transition"
              >
                👁️ Xem
              </button>
              <button 
                onClick={() => openEditModal(classItem)}
                className="px-3 py-1 text-sm text-yellow-600 hover:text-yellow-900 hover:bg-yellow-50 rounded transition"
              >
                ✏️ Sửa
              </button>
              <button 
                onClick={() => handleDeleteClass(classItem.id)}
                className="px-3 py-1 text-sm text-red-600 hover:text-red-900 hover:bg-red-50 rounded transition"
              >
                🗑️ Xóa
              </button>
            </div>
          </div>
        ))}
      </div>

      {filteredClasses.length === 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <p className="text-gray-500">Không tìm thấy lớp học nào</p>
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-screen overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">Thêm lớp học mới</h2>
            <div className="space-y-4">
              <input
                type="text"
                placeholder="Mã lớp"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.class_id}
                onChange={(e) => setFormData({...formData, class_id: e.target.value})}
              />
              <input
                type="text"
                placeholder="Tên lớp"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.class_name}
                onChange={(e) => setFormData({...formData, class_name: e.target.value})}
              />
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.subject_id}
                onChange={(e) => setFormData({...formData, subject_id: parseInt(e.target.value)})}
              >
                <option value="">Chọn học phần</option>
                {subjects.map((subject) => (
                  <option key={subject.id} value={subject.id}>
                    {subject.subject_name} ({subject.subject_id})
                  </option>
                ))}
              </select>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.class_type}
                onChange={(e) => setFormData({...formData, class_type: e.target.value})}
              >
                <option value="Lý thuyết">Lý thuyết</option>
                <option value="Thực hành">Thực hành</option>
                <option value="Bài tập">Bài tập</option>
                <option value="Thí nghiệm">Thí nghiệm</option>
              </select>
              <input
                type="text"
                placeholder="Phòng học"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.classroom}
                onChange={(e) => setFormData({...formData, classroom: e.target.value})}
              />
              <input
                type="text"
                placeholder="Ngày học (VD: Monday,Friday)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.study_date}
                onChange={(e) => setFormData({...formData, study_date: e.target.value})}
              />
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="time"
                  placeholder="Giờ bắt đầu"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  value={formData.study_time_start}
                  onChange={(e) => setFormData({...formData, study_time_start: e.target.value})}
                />
                <input
                  type="time"
                  placeholder="Giờ kết thúc"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  value={formData.study_time_end}
                  onChange={(e) => setFormData({...formData, study_time_end: e.target.value})}
                />
              </div>
              <input
                type="number"
                placeholder="Sĩ số tối đa"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.max_student_number}
                onChange={(e) => setFormData({...formData, max_student_number: parseInt(e.target.value)})}
              />
              <input
                type="text"
                placeholder="Giảng viên"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.teacher_name}
                onChange={(e) => setFormData({...formData, teacher_name: e.target.value})}
              />
              <input
                type="text"
                placeholder="Tuần học (VD: 1,2,3,4,5)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.study_week.join(',')}
                onChange={(e) => setFormData({...formData, study_week: e.target.value.split(',').map(w => parseInt(w.trim())).filter(w => !isNaN(w))})}
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
                onClick={handleCreateClass}
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
          <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-screen overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">Sửa thông tin lớp học</h2>
            <div className="space-y-4">
              <input
                type="text"
                placeholder="Mã lớp"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.class_id}
                onChange={(e) => setFormData({...formData, class_id: e.target.value})}
              />
              <input
                type="text"
                placeholder="Tên lớp"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.class_name}
                onChange={(e) => setFormData({...formData, class_name: e.target.value})}
              />
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.subject_id}
                onChange={(e) => setFormData({...formData, subject_id: parseInt(e.target.value)})}
              >
                <option value="">Chọn học phần</option>
                {subjects.map((subject) => (
                  <option key={subject.id} value={subject.id}>
                    {subject.subject_name} ({subject.subject_id})
                  </option>
                ))}
              </select>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.class_type}
                onChange={(e) => setFormData({...formData, class_type: e.target.value})}
              >
                <option value="Lý thuyết">Lý thuyết</option>
                <option value="Thực hành">Thực hành</option>
                <option value="Bài tập">Bài tập</option>
                <option value="Thí nghiệm">Thí nghiệm</option>
              </select>
              <input
                type="text"
                placeholder="Phòng học"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.classroom}
                onChange={(e) => setFormData({...formData, classroom: e.target.value})}
              />
              <input
                type="text"
                placeholder="Ngày học (VD: Monday,Friday)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.study_date}
                onChange={(e) => setFormData({...formData, study_date: e.target.value})}
              />
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="time"
                  placeholder="Giờ bắt đầu"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  value={formData.study_time_start}
                  onChange={(e) => setFormData({...formData, study_time_start: e.target.value})}
                />
                <input
                  type="time"
                  placeholder="Giờ kết thúc"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  value={formData.study_time_end}
                  onChange={(e) => setFormData({...formData, study_time_end: e.target.value})}
                />
              </div>
              <input
                type="number"
                placeholder="Sĩ số tối đa"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.max_student_number}
                onChange={(e) => setFormData({...formData, max_student_number: parseInt(e.target.value)})}
              />
              <input
                type="text"
                placeholder="Giảng viên"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.teacher_name}
                onChange={(e) => setFormData({...formData, teacher_name: e.target.value})}
              />
              <input
                type="text"
                placeholder="Tuần học (VD: 1,2,3,4,5)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.study_week.join(',')}
                onChange={(e) => setFormData({...formData, study_week: e.target.value.split(',').map(w => parseInt(w.trim())).filter(w => !isNaN(w))})}
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
                onClick={handleUpdateClass}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Cập nhật
              </button>
            </div>
          </div>
        </div>
      )}

      {/* View Modal */}
      {showViewModal && selectedClass && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Thông tin lớp học</h2>
            <div className="space-y-3">
              <div><strong>Mã lớp:</strong> {selectedClass.class_id}</div>
              <div><strong>Tên lớp:</strong> {selectedClass.class_name}</div>
              <div><strong>Học phần:</strong> {selectedClass.subject.subject_name} ({selectedClass.subject.subject_id})</div>
              <div><strong>Loại lớp:</strong> {selectedClass.class_type || 'Chưa xác định'}</div>
              <div><strong>Phòng học:</strong> {selectedClass.classroom || 'Chưa phân phòng'}</div>
              <div><strong>Ngày học:</strong> {selectedClass.study_date || 'Chưa xác định'}</div>
              <div><strong>Thời gian:</strong> {selectedClass.study_time_start} - {selectedClass.study_time_end}</div>
              <div><strong>Sĩ số tối đa:</strong> {selectedClass.max_student_number}</div>
              <div><strong>Giảng viên:</strong> {selectedClass.teacher_name || 'Chưa phân công'}</div>
              <div><strong>Tuần học:</strong> {selectedClass.study_week.join(', ')}</div>
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

export default ClassesManagement
