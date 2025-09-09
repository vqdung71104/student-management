import { useState, useEffect } from 'react'

interface Department {
  id: string
  name: string
}

interface Subject {
  id: number
  subject_id: string
  subject_name: string
  duration: number
  credits: number
  tuition_fee: number
  english_subject_name: string
  weight: number
  conditional_subjects?: string
  department: Department
}

interface SubjectFormData {
  subject_id: string
  subject_name: string
  duration: number
  credits: number
  tuition_fee: number
  english_subject_name: string
  weight: number
  conditional_subjects?: string
  department_id: string
}

const SubjectsManagement = () => {
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [loading, setLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showViewModal, setShowViewModal] = useState(false)
  const [selectedSubject, setSelectedSubject] = useState<Subject | null>(null)
  const [formData, setFormData] = useState<SubjectFormData>({
    subject_id: '',
    subject_name: '',
    duration: 15,
    credits: 1,
    tuition_fee: 0,
    english_subject_name: '',
    weight: 1.0,
    conditional_subjects: '',
    department_id: '',
  })

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

  const handleCreateSubject = async () => {
    try {
      const response = await fetch('http://localhost:8000/subjects/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })
      
      if (response.ok) {
        setShowCreateModal(false)
        fetchSubjects()
        resetForm()
        alert('Tạo học phần thành công!')
      } else {
        alert('Có lỗi khi tạo học phần')
      }
    } catch (error) {
      console.error('Error creating subject:', error)
      alert('Có lỗi khi tạo học phần')
    }
  }

  const handleUpdateSubject = async () => {
    if (!selectedSubject) return
    
    try {
      const response = await fetch(`http://localhost:8000/subjects/${selectedSubject.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })
      
      if (response.ok) {
        setShowEditModal(false)
        fetchSubjects()
        resetForm()
        alert('Cập nhật học phần thành công!')
      } else {
        alert('Có lỗi khi cập nhật học phần')
      }
    } catch (error) {
      console.error('Error updating subject:', error)
      alert('Có lỗi khi cập nhật học phần')
    }
  }

  const handleDeleteSubject = async (subjectId: number) => {
    if (!confirm('Bạn có chắc chắn muốn xóa học phần này?')) return
    
    try {
      const response = await fetch(`http://localhost:8000/subjects/${subjectId}`, {
        method: 'DELETE',
      })
      
      if (response.ok) {
        fetchSubjects()
        alert('Xóa học phần thành công!')
      } else {
        alert('Có lỗi khi xóa học phần')
      }
    } catch (error) {
      console.error('Error deleting subject:', error)
      alert('Có lỗi khi xóa học phần')
    }
  }

  const resetForm = () => {
    setFormData({
      subject_id: '',
      subject_name: '',
      duration: 15,
      credits: 1,
      tuition_fee: 0,
      english_subject_name: '',
      weight: 1.0,
      conditional_subjects: '',
      department_id: '',
    })
  }

  const openCreateModal = () => {
    resetForm()
    setShowCreateModal(true)
  }

  const openEditModal = (subject: Subject) => {
    setSelectedSubject(subject)
    setFormData({
      subject_id: subject.subject_id,
      subject_name: subject.subject_name,
      duration: subject.duration,
      credits: subject.credits,
      tuition_fee: subject.tuition_fee,
      english_subject_name: subject.english_subject_name,
      weight: subject.weight,
      conditional_subjects: subject.conditional_subjects || '',
      department_id: subject.department.id,
    })
    setShowEditModal(true)
  }

  const openViewModal = (subject: Subject) => {
    setSelectedSubject(subject)
    setShowViewModal(true)
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
        <h1 className="text-3xl font-bold text-gray-900">Quản lý học phần</h1>
        <button 
          onClick={openCreateModal}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          ➕ Thêm học phần
        </button>
      </div>

      {/* Search */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <input
          type="text"
          placeholder="Tìm kiếm theo tên học phần, mã học phần, khoa..."
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
                    <span className="font-medium">Mã học phần:</span> {subject.subject_id}
                  </p>
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Số tín chỉ:</span> {subject.credits}
                  </p>
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Thời lượng:</span> {subject.duration} tuần
                  </p>
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Học phí:</span> {subject.tuition_fee.toLocaleString()} VNĐ
                  </p>
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Khoa:</span> {subject.department.name}
                  </p>
                  {subject.conditional_subjects && (
                    <p className="text-sm text-gray-600">
                      <span className="font-medium">Học phần tiên quyết:</span> {subject.conditional_subjects}
                    </p>
                  )}
                </div>
                <p className="text-sm text-gray-700 mt-3">
                  <span className="font-medium">Tên tiếng Anh:</span> {subject.english_subject_name}
                </p>
              </div>
            </div>
            
            <div className="flex justify-end space-x-2 mt-4 pt-4 border-t border-gray-200">
              <button 
                onClick={() => openViewModal(subject)}
                className="px-3 py-1 text-sm text-blue-600 hover:text-blue-900 hover:bg-blue-50 rounded transition"
              >
                👁️ Xem
              </button>
              <button 
                onClick={() => openEditModal(subject)}
                className="px-3 py-1 text-sm text-yellow-600 hover:text-yellow-900 hover:bg-yellow-50 rounded transition"
              >
                ✏️ Sửa
              </button>
              <button 
                onClick={() => handleDeleteSubject(subject.id)}
                className="px-3 py-1 text-sm text-red-600 hover:text-red-900 hover:bg-red-50 rounded transition"
              >
                🗑️ Xóa
              </button>
            </div>
          </div>
        ))}
      </div>

      {filteredSubjects.length === 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <p className="text-gray-500">Không tìm thấy học phần nào</p>
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-screen overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">Thêm học phần mới</h2>
            <div className="space-y-4">
              <input
                type="text"
                placeholder="Mã học phần"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.subject_id}
                onChange={(e) => setFormData({...formData, subject_id: e.target.value})}
              />
              <input
                type="text"
                placeholder="Tên học phần"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.subject_name}
                onChange={(e) => setFormData({...formData, subject_name: e.target.value})}
              />
              <input
                type="text"
                placeholder="Tên tiếng Anh"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.english_subject_name}
                onChange={(e) => setFormData({...formData, english_subject_name: e.target.value})}
              />
              <input
                type="number"
                placeholder="Số tín chỉ"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.credits}
                onChange={(e) => setFormData({...formData, credits: parseInt(e.target.value)})}
              />
              <input
                type="number"
                placeholder="Thời lượng (tuần)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.duration}
                onChange={(e) => setFormData({...formData, duration: parseInt(e.target.value)})}
              />
              <input
                type="number"
                placeholder="Học phí"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.tuition_fee}
                onChange={(e) => setFormData({...formData, tuition_fee: parseFloat(e.target.value)})}
              />
              <input
                type="number"
                step="0.1"
                placeholder="Hệ số (weight)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.weight}
                onChange={(e) => setFormData({...formData, weight: parseFloat(e.target.value)})}
              />
              <input
                type="text"
                placeholder="Mã khoa"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.department_id}
                onChange={(e) => setFormData({...formData, department_id: e.target.value})}
              />
              <input
                type="text"
                placeholder="Học phần tiên quyết (tùy chọn)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.conditional_subjects}
                onChange={(e) => setFormData({...formData, conditional_subjects: e.target.value})}
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
                onClick={handleCreateSubject}
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
            <h2 className="text-xl font-bold mb-4">Sửa thông tin học phần</h2>
            <div className="space-y-4">
              <input
                type="text"
                placeholder="Mã học phần"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.subject_id}
                onChange={(e) => setFormData({...formData, subject_id: e.target.value})}
              />
              <input
                type="text"
                placeholder="Tên học phần"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.subject_name}
                onChange={(e) => setFormData({...formData, subject_name: e.target.value})}
              />
              <input
                type="text"
                placeholder="Tên tiếng Anh"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.english_subject_name}
                onChange={(e) => setFormData({...formData, english_subject_name: e.target.value})}
              />
              <input
                type="number"
                placeholder="Số tín chỉ"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.credits}
                onChange={(e) => setFormData({...formData, credits: parseInt(e.target.value)})}
              />
              <input
                type="number"
                placeholder="Thời lượng (tuần)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.duration}
                onChange={(e) => setFormData({...formData, duration: parseInt(e.target.value)})}
              />
              <input
                type="number"
                placeholder="Học phí"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.tuition_fee}
                onChange={(e) => setFormData({...formData, tuition_fee: parseFloat(e.target.value)})}
              />
              <input
                type="number"
                step="0.1"
                placeholder="Hệ số (weight)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.weight}
                onChange={(e) => setFormData({...formData, weight: parseFloat(e.target.value)})}
              />
              <input
                type="text"
                placeholder="Mã khoa"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.department_id}
                onChange={(e) => setFormData({...formData, department_id: e.target.value})}
              />
              <input
                type="text"
                placeholder="Học phần tiên quyết (tùy chọn)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={formData.conditional_subjects}
                onChange={(e) => setFormData({...formData, conditional_subjects: e.target.value})}
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
                onClick={handleUpdateSubject}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Cập nhật
              </button>
            </div>
          </div>
        </div>
      )}

      {/* View Modal */}
      {showViewModal && selectedSubject && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Thông tin học phần</h2>
            <div className="space-y-3">
              <div><strong>Mã học phần:</strong> {selectedSubject.subject_id}</div>
              <div><strong>Tên học phần:</strong> {selectedSubject.subject_name}</div>
              <div><strong>Tên tiếng Anh:</strong> {selectedSubject.english_subject_name}</div>
              <div><strong>Số tín chỉ:</strong> {selectedSubject.credits}</div>
              <div><strong>Thời lượng:</strong> {selectedSubject.duration} tuần</div>
              <div><strong>Học phí:</strong> {selectedSubject.tuition_fee.toLocaleString()} VNĐ</div>
              <div><strong>Hệ số:</strong> {selectedSubject.weight}</div>
              <div><strong>Khoa:</strong> {selectedSubject.department.name}</div>
              <div><strong>Học phần tiên quyết:</strong> {selectedSubject.conditional_subjects || 'Không có'}</div>
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

export default SubjectsManagement
