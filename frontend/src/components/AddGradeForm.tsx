import { useState } from 'react'

interface AddGradeFormProps {
  onSubmit: (data: { subject_code: string; semester: string; letter_grade: string }) => void
  onClose: () => void
  loading?: boolean
}

const AddGradeForm = ({ onSubmit, onClose, loading = false }: AddGradeFormProps) => {
  const [formData, setFormData] = useState({
    subject_code: '',
    semester: '',
    letter_grade: ''
  })
  const [errors, setErrors] = useState<{ [key: string]: string }>({})

  const gradeOptions = ['A+', 'A', 'B+', 'B', 'C+', 'C', 'D+', 'D', 'F']

  const validate = () => {
    const newErrors: { [key: string]: string } = {}
    
    if (!formData.subject_code.trim()) {
      newErrors.subject_code = 'Vui lòng nhập mã học phần'
    }
    
    if (!formData.semester.trim()) {
      newErrors.semester = 'Vui lòng nhập học kỳ (ví dụ: 20241)'
    } else if (!/^\d{5}$/.test(formData.semester)) {
      newErrors.semester = 'Học kỳ phải có định dạng 5 chữ số (ví dụ: 20241)'
    }
    
    if (!formData.letter_grade) {
      newErrors.letter_grade = 'Vui lòng chọn điểm'
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (validate()) {
      onSubmit(formData)
    }
  }

  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    // Clear error when user types
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }))
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="bg-green-600 text-white p-4 flex justify-between items-center rounded-t-lg">
          <h3 className="text-lg font-semibold">   Thêm môn học mới</h3>
          <button onClick={onClose} className="text-white hover:text-gray-200" disabled={loading}>
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6">
          <div className="space-y-4">
            {/* Subject Code */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Mã học phần <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.subject_code}
                onChange={(e) => handleChange('subject_code', e.target.value.toUpperCase())}
                placeholder="Ví dụ: IT4062E"
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 ${
                  errors.subject_code ? 'border-red-500' : 'border-gray-300'
                }`}
                disabled={loading}
              />
              {errors.subject_code && (
                <p className="mt-1 text-sm text-red-600">{errors.subject_code}</p>
              )}
            </div>

            {/* Semester */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Học kỳ <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.semester}
                onChange={(e) => handleChange('semester', e.target.value)}
                placeholder="Ví dụ: 20241"
                maxLength={5}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 ${
                  errors.semester ? 'border-red-500' : 'border-gray-300'
                }`}
                disabled={loading}
              />
              {errors.semester && (
                <p className="mt-1 text-sm text-red-600">{errors.semester}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">
                Định dạng: YYYYS (Năm 4 chữ số + Học kỳ 1 chữ số, ví dụ: 20241 = HK1 năm 2024)
              </p>
            </div>

            {/* Letter Grade */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Điểm tổng kết <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.letter_grade}
                onChange={(e) => handleChange('letter_grade', e.target.value)}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 ${
                  errors.letter_grade ? 'border-red-500' : 'border-gray-300'
                }`}
                disabled={loading}
              >
                <option value="">-- Chọn điểm --</option>
                {gradeOptions.map(grade => (
                  <option key={grade} value={grade}>
                    {grade} {grade === 'F' ? '(Rớt)' : ''}
                  </option>
                ))}
              </select>
              {errors.letter_grade && (
                <p className="mt-1 text-sm text-red-600">{errors.letter_grade}</p>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end space-x-3 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition"
              disabled={loading}
            >
              Hủy
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={loading}
            >
              {loading ? (
                <span className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Đang xử lý...
                </span>
              ) : (
                'Thêm môn học'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default AddGradeForm
