import React, { useState, useEffect } from 'react'

interface Feedback {
  id: number
  email: string
  subject: string
  feedback: string
  suggestions?: string
  status: 'pending' | 'resolved'
  created_at: string
  updated_at?: string
}

const FeedbackManagement: React.FC = () => {
  const [feedbacks, setFeedbacks] = useState<Feedback[]>([])
  const [loading, setLoading] = useState(true)
  const [filterStatus, setFilterStatus] = useState<'all' | 'pending' | 'resolved'>('all')
  const [selectedFeedbacks, setSelectedFeedbacks] = useState<number[]>([])
  const [showDetails, setShowDetails] = useState<number | null>(null)

  const subjectMap = {
    'bug': 'Báo lỗi hệ thống',
    'feature': 'Đề xuất tính năng mới',
    'ui': 'Giao diện người dùng',
    'performance': 'Hiệu suất hệ thống',
    'content': 'Nội dung thông tin',
    'other': 'Khác'
  }

  const statusMap = {
    'pending': 'Chưa xử lý',
    'resolved': 'Đã xử lý'
  }

  useEffect(() => {
    fetchFeedbacks()
  }, [filterStatus])

  const fetchFeedbacks = async () => {
    try {
      setLoading(true)
      const statusParam = filterStatus === 'all' ? '' : `?status=${filterStatus}`
      const response = await fetch(`http://localhost:8000/feedback${statusParam}`)
      
      if (response.ok) {
        const data = await response.json()
        setFeedbacks(data)
      } else {
        console.error('Failed to fetch feedbacks')
      }
    } catch (error) {
      console.error('Error fetching feedbacks:', error)
    } finally {
      setLoading(false)
    }
  }

  const updateFeedbackStatus = async (feedbackId: number, status: 'pending' | 'resolved') => {
    try {
      const response = await fetch(`http://localhost:8000/feedback/${feedbackId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status })
      })

      if (response.ok) {
        fetchFeedbacks()
      }
    } catch (error) {
      console.error('Error updating feedback:', error)
    }
  }

  const bulkUpdateStatus = async (status: 'pending' | 'resolved') => {
    if (selectedFeedbacks.length === 0) {
      alert('Vui lòng chọn ít nhất một phản hồi')
      return
    }

    try {
      const response = await fetch('http://localhost:8000/feedback/bulk-update', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          feedback_ids: selectedFeedbacks,
          status
        })
      })

      if (response.ok) {
        setSelectedFeedbacks([])
        fetchFeedbacks()
        alert(`Đã cập nhật ${selectedFeedbacks.length} phản hồi`)
      }
    } catch (error) {
      console.error('Error bulk updating:', error)
    }
  }

  const deleteFeedback = async (feedbackId: number) => {
    if (!confirm('Bạn có chắc chắn muốn xóa phản hồi này?')) return

    try {
      const response = await fetch(`http://localhost:8000/feedback/${feedbackId}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        fetchFeedbacks()
      }
    } catch (error) {
      console.error('Error deleting feedback:', error)
    }
  }

  const toggleSelectFeedback = (feedbackId: number) => {
    setSelectedFeedbacks(prev => 
      prev.includes(feedbackId) 
        ? prev.filter(id => id !== feedbackId)
        : [...prev, feedbackId]
    )
  }

  const selectAllFeedbacks = () => {
    if (selectedFeedbacks.length === feedbacks.length) {
      setSelectedFeedbacks([])
    } else {
      setSelectedFeedbacks(feedbacks.map(f => f.id))
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-md">
        <div className="bg-blue-600 text-white p-6 rounded-t-lg">
          <h1 className="text-2xl font-bold">Quản lý phản hồi</h1>
          <p className="text-blue-100 mt-1">Xử lý phản hồi từ sinh viên</p>
        </div>

        <div className="p-6">
          {/* Filters and Actions */}
          <div className="flex justify-between items-center mb-6">
            <div className="flex items-center space-x-4">
              <label className="text-sm font-medium text-gray-700">Lọc theo trạng thái:</label>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value as any)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">Tất cả</option>
                <option value="pending">Chưa xử lý</option>
                <option value="resolved">Đã xử lý</option>
              </select>
            </div>

            {selectedFeedbacks.length > 0 && (
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600">
                  Đã chọn {selectedFeedbacks.length} phản hồi
                </span>
                <button
                  onClick={() => bulkUpdateStatus('resolved')}
                  className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
                >
                  Đánh dấu đã xử lý
                </button>
                <button
                  onClick={() => bulkUpdateStatus('pending')}
                  className="px-3 py-1 bg-yellow-600 text-white text-sm rounded hover:bg-yellow-700"
                >
                  Đánh dấu chưa xử lý
                </button>
              </div>
            )}
          </div>

          {/* Feedback Table */}
          <div className="overflow-x-auto">
            <table className="min-w-full table-auto">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left">
                    <input
                      type="checkbox"
                      checked={selectedFeedbacks.length === feedbacks.length && feedbacks.length > 0}
                      onChange={selectAllFeedbacks}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Chủ đề
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Trạng thái
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Ngày tạo
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Hành động
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {feedbacks.map((feedback) => (
                  <React.Fragment key={feedback.id}>
                    <tr className="hover:bg-gray-50">
                      <td className="px-4 py-4">
                        <input
                          type="checkbox"
                          checked={selectedFeedbacks.includes(feedback.id)}
                          onChange={() => toggleSelectFeedback(feedback.id)}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                      </td>
                      <td className="px-4 py-4 text-sm text-gray-900">{feedback.email}</td>
                      <td className="px-4 py-4 text-sm text-gray-900">
                        {subjectMap[feedback.subject as keyof typeof subjectMap]}
                      </td>
                      <td className="px-4 py-4">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          feedback.status === 'resolved' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {statusMap[feedback.status]}
                        </span>
                      </td>
                      <td className="px-4 py-4 text-sm text-gray-900">
                        {new Date(feedback.created_at).toLocaleDateString('vi-VN')}
                      </td>
                      <td className="px-4 py-4 text-sm space-x-2">
                        <button
                          onClick={() => setShowDetails(showDetails === feedback.id ? null : feedback.id)}
                          className="text-blue-600 hover:text-blue-800"
                        >
                          {showDetails === feedback.id ? 'Ẩn' : 'Chi tiết'}
                        </button>
                        <button
                          onClick={() => updateFeedbackStatus(
                            feedback.id, 
                            feedback.status === 'pending' ? 'resolved' : 'pending'
                          )}
                          className={`${
                            feedback.status === 'pending' 
                              ? 'text-green-600 hover:text-green-800' 
                              : 'text-yellow-600 hover:text-yellow-800'
                          }`}
                        >
                          {feedback.status === 'pending' ? 'Đánh dấu đã xử lý' : 'Đánh dấu chưa xử lý'}
                        </button>
                        <button
                          onClick={() => deleteFeedback(feedback.id)}
                          className="text-red-600 hover:text-red-800"
                        >
                          Xóa
                        </button>
                      </td>
                    </tr>
                    {showDetails === feedback.id && (
                      <tr>
                        <td colSpan={6} className="px-4 py-4 bg-gray-50">
                          <div className="space-y-3">
                            <div>
                              <h4 className="font-medium text-gray-900">Phản ánh:</h4>
                              <p className="text-gray-700 mt-1">{feedback.feedback}</p>
                            </div>
                            {feedback.suggestions && (
                              <div>
                                <h4 className="font-medium text-gray-900">Đóng góp:</h4>
                                <p className="text-gray-700 mt-1">{feedback.suggestions}</p>
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>

            {feedbacks.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                Không có phản hồi nào
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default FeedbackManagement