import { useState } from 'react'
import type { FormTemplate, FormField } from '../../pages/student/Forms'

interface FormModalProps {
  form: FormTemplate
  onClose: () => void
  onSubmit: (data: Record<string, string>) => void
}

const FormModal = ({ form, onClose, onSubmit }: FormModalProps) => {
  const [formData, setFormData] = useState<Record<string, string>>({})
  const [errors, setErrors] = useState<Record<string, string>>({})

  const handleInputChange = (fieldId: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [fieldId]: value
    }))
    
    // Clear error when user starts typing
    if (errors[fieldId]) {
      setErrors(prev => ({
        ...prev,
        [fieldId]: ''
      }))
    }
  }

  const validateForm = () => {
    const newErrors: Record<string, string> = {}
    
    form.fields.forEach(field => {
      if (field.required && !formData[field.id]?.trim()) {
        newErrors[field.id] = 'Trường này là bắt buộc'
      }
    })
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (validateForm()) {
      onSubmit(formData)
    }
  }

  const renderField = (field: FormField) => {
    switch (field.type) {
      case 'textarea':
        return (
          <textarea
            id={field.id}
            value={formData[field.id] || ''}
            onChange={(e) => handleInputChange(field.id, e.target.value)}
            placeholder={field.placeholder}
            rows={3}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none ${
              errors[field.id] ? 'border-red-300' : 'border-gray-300'
            }`}
          />
        )
      
      case 'select':
        return (
          <select
            id={field.id}
            value={formData[field.id] || ''}
            onChange={(e) => handleInputChange(field.id, e.target.value)}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors[field.id] ? 'border-red-300' : 'border-gray-300'
            }`}
          >
            <option value="">-- Chọn --</option>
            {field.options?.map(option => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        )
      
      default:
        return (
          <input
            type={field.type}
            id={field.id}
            value={formData[field.id] || ''}
            onChange={(e) => handleInputChange(field.id, e.target.value)}
            placeholder={field.placeholder}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors[field.id] ? 'border-red-300' : 'border-gray-300'
            }`}
          />
        )
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[95vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-red-600">{form.title}</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto" style={{ maxHeight: 'calc(90vh - 140px)' }}>
          {/* Full Description */}
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <p className="text-gray-700 text-sm leading-relaxed">
              {form.fullDescription}
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {form.fields.map(field => (
              <div key={field.id}>
                <label 
                  htmlFor={field.id} 
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  {field.label}
                  {field.required && <span className="text-red-500 ml-1">*</span>}
                </label>
                {renderField(field)}
                {errors[field.id] && (
                  <p className="text-red-500 text-sm mt-1">{errors[field.id]}</p>
                )}
              </div>
            ))}
          </form>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 p-6 border-t border-gray-200">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Thoát
          </button>
          <button
            onClick={handleSubmit}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Xem đơn
          </button>
        </div>
      </div>
    </div>
  )
}

export default FormModal
