import React, { useState, useEffect } from 'react'

interface FAQ {
  id: number
  question: string
  answer: string
  is_active: boolean
  order_index: number
  created_at: string
  updated_at?: string
}

const FAQManagement: React.FC = () => {
  const [faqs, setFaqs] = useState<FAQ[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingFaq, setEditingFaq] = useState<FAQ | null>(null)
  const [formData, setFormData] = useState({
    question: '',
    answer: '',
    is_active: true,
    order_index: 0
  })

  useEffect(() => {
    fetchFAQs()
  }, [])

  const fetchFAQs = async () => {
    try {
      setLoading(true)
      const response = await fetch('http://localhost:8000/faq?active_only=false')
      
      if (response.ok) {
        const data = await response.json()
        setFaqs(data)
      } else {
        console.error('Failed to fetch FAQs')
      }
    } catch (error) {
      console.error('Error fetching FAQs:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    try {
      const url = editingFaq 
        ? `http://localhost:8000/faq/${editingFaq.id}`
        : 'http://localhost:8000/faq'
      
      const method = editingFaq ? 'PUT' : 'POST'

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      })

      if (response.ok) {
        setShowForm(false)
        setEditingFaq(null)
        setFormData({ question: '', answer: '', is_active: true, order_index: 0 })
        fetchFAQs()
        alert(editingFaq ? 'Cập nhật FAQ thành công!' : 'Tạo FAQ thành công!')
      } else {
        alert('Có lỗi xảy ra')
      }
    } catch (error) {
      console.error('Error saving FAQ:', error)
      alert('Có lỗi xảy ra')
    }
  }

  const deleteFAQ = async (faqId: number) => {
    if (!confirm('Bạn có chắc chắn muốn xóa FAQ này?')) return

    try {
      const response = await fetch(`http://localhost:8000/faq/${faqId}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        fetchFAQs()
        alert('Xóa FAQ thành công!')
      }
    } catch (error) {
      console.error('Error deleting FAQ:', error)
    }
  }

  const startEdit = (faq: FAQ) => {
    setEditingFaq(faq)
    setFormData({
      question: faq.question,
      answer: faq.answer,
      is_active: faq.is_active,
      order_index: faq.order_index
    })
    setShowForm(true)
  }

  const startCreate = () => {
    setEditingFaq(null)
    setFormData({ question: '', answer: '', is_active: true, order_index: 0 })
    setShowForm(true)
  }

  const cancelForm = () => {
    setShowForm(false)
    setEditingFaq(null)
    setFormData({ question: '', answer: '', is_active: true, order_index: 0 })
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-md">
        <div className="bg-blue-600 text-white p-6 rounded-t-lg flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold">Quản lý FAQ</h1>
            <p className="text-blue-100 mt-1">Quản lý những câu hỏi thường gặp</p>
          </div>
          <button
            onClick={startCreate}
            className="bg-white text-blue-600 px-4 py-2 rounded-lg hover:bg-gray-100 font-medium"
          >
            + Thêm FAQ mới
          </button>
        </div>

        <div className="p-6">
          {showForm && (
            <div className="bg-gray-50 p-6 rounded-lg mb-6">
              <h3 className="text-lg font-semibold mb-4">
                {editingFaq ? 'Cập nhật FAQ' : 'Tạo FAQ mới'}
              </h3>
              
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Câu hỏi *
                  </label>
                  <input
                    type="text"
                    value={formData.question}
                    onChange={(e) => setFormData(prev => ({ ...prev, question: e.target.value }))}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Nhập câu hỏi..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Câu trả lời *
                  </label>
                  <textarea
                    value={formData.answer}
                    onChange={(e) => setFormData(prev => ({ ...prev, answer: e.target.value }))}
                    required
                    rows={4}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Nhập câu trả lời..."
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Thứ tự hiển thị
                    </label>
                    <input
                      type="number"
                      value={formData.order_index}
                      onChange={(e) => setFormData(prev => ({ ...prev, order_index: parseInt(e.target.value) || 0 }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      min="0"
                    />
                  </div>

                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="is_active"
                      checked={formData.is_active}
                      onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor="is_active" className="ml-2 block text-sm text-gray-900">
                      Hiển thị công khai
                    </label>
                  </div>
                </div>

                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={cancelForm}
                    className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                  >
                    Hủy
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    {editingFaq ? 'Cập nhật' : 'Tạo mới'}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* FAQ List */}
          <div className="space-y-4">
            {faqs.map((faq) => (
              <div key={faq.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <h3 className="font-medium text-gray-900">{faq.question}</h3>
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        faq.is_active 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {faq.is_active ? 'Hiển thị' : 'Ẩn'}
                      </span>
                      <span className="text-xs text-gray-500">
                        Thứ tự: {faq.order_index}
                      </span>
                    </div>
                    <p className="text-gray-700 text-sm">{faq.answer}</p>
                    <p className="text-xs text-gray-500 mt-2">
                      Tạo: {new Date(faq.created_at).toLocaleDateString('vi-VN')}
                    </p>
                  </div>
                  
                  <div className="flex space-x-2 ml-4">
                    <button
                      onClick={() => startEdit(faq)}
                      className="text-blue-600 hover:text-blue-800 text-sm"
                    >
                      Sửa
                    </button>
                    <button
                      onClick={() => deleteFAQ(faq.id)}
                      className="text-red-600 hover:text-red-800 text-sm"
                    >
                      Xóa
                    </button>
                  </div>
                </div>
              </div>
            ))}

            {faqs.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                Chưa có FAQ nào. Hãy tạo FAQ đầu tiên!
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default FAQManagement