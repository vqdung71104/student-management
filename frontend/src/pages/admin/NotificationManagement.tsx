import { useState } from 'react'
import { useNotifications } from '../../hooks/useNotifications'

interface NotificationFormData {
  title: string
  content: string
}

const NotificationManagement = () => {
  const { notifications, loading, refresh, formatDate } = useNotifications()
  const [showForm, setShowForm] = useState(false)
  const [editingNotification, setEditingNotification] = useState<any>(null)
  const [formData, setFormData] = useState<NotificationFormData>({ title: '', content: '' })
  const [selectedNotification, setSelectedNotification] = useState<any>(null)
  const [submitting, setSubmitting] = useState(false)

  const resetForm = () => {
    setFormData({ title: '', content: '' })
    setEditingNotification(null)
    setShowForm(false)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.title.trim() || !formData.content.trim()) return

    setSubmitting(true)
    try {
      const url = editingNotification 
        ? `http://127.0.0.1:8000/notifications/${editingNotification.id}`
        : 'http://127.0.0.1:8000/notifications'
      
      const method = editingNotification ? 'PUT' : 'POST'
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })

      if (response.ok) {
        resetForm()
        refresh()
      } else {
        alert('Có lỗi xảy ra khi lưu thông báo')
      }
    } catch (error) {
      alert('Có lỗi xảy ra khi lưu thông báo')
    } finally {
      setSubmitting(false)
    }
  }

  const handleEdit = (notification: any) => {
    setEditingNotification(notification)
    setFormData({
      title: notification.title,
      content: notification.content
    })
    setShowForm(true)
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Bạn có chắc chắn muốn xóa thông báo này?')) return

    try {
      const response = await fetch(`http://127.0.0.1:8000/notifications/${id}`, {
        method: 'DELETE',
      })

      if (response.ok) {
        refresh()
      } else {
        alert('Có lỗi xảy ra khi xóa thông báo')
      }
    } catch (error) {
      alert('Có lỗi xảy ra khi xóa thông báo')
    }
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Quản lý thông báo</h1>
        <button
          onClick={() => setShowForm(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors duration-200"
        >
          Tạo thông báo mới
        </button>
      </div>

      {/* Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl border border-gray-200 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold text-gray-900">
                  {editingNotification ? 'Chỉnh sửa thông báo' : 'Tạo thông báo mới'}
                </h2>
                <button
                  onClick={resetForm}
                  className="text-gray-400 hover:text-gray-600 text-xl"
                >
                  ✕
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Tiêu đề *
                  </label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Nhập tiêu đề thông báo..."
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Nội dung *
                  </label>
                  <textarea
                    value={formData.content}
                    onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                    rows={6}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Nhập nội dung thông báo... (Có thể chứa URL)"
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Bạn có thể thêm link trực tiếp vào nội dung (http:// hoặc https://)
                  </p>
                </div>

                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={resetForm}
                    className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition-colors duration-200"
                  >
                    Hủy
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors duration-200"
                  >
                    {submitting ? 'Đang lưu...' : editingNotification ? 'Cập nhật' : 'Tạo mới'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Notification Detail Modal */}
      {selectedNotification && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl border border-gray-200 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <h1 className="text-xl font-bold text-gray-900 pr-4">{selectedNotification.title}</h1>
                <button
                  onClick={() => setSelectedNotification(null)}
                  className="text-gray-400 hover:text-gray-600 text-xl"
                >
                  ✕
                </button>
              </div>
              
              <div className="flex flex-col sm:flex-row sm:justify-between text-xs text-gray-500 mb-4 space-y-1 sm:space-y-0">
                <span>Tạo ngày: {formatDate(selectedNotification.created_at)}</span>
                {selectedNotification.updated_at !== selectedNotification.created_at && (
                  <span>Chỉnh sửa ngày: {formatDate(selectedNotification.updated_at)}</span>
                )}
              </div>
              
              <div className="prose max-w-none mb-6">
                <div 
                  className="text-gray-700 whitespace-pre-wrap"
                  dangerouslySetInnerHTML={{ 
                    __html: selectedNotification.content.replace(/\n/g, '<br>').replace(
                      /(https?:\/\/[^\s]+)/g, 
                      '<a href="$1" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 underline">$1</a>'
                    )
                  }}
                />
              </div>
              
              <div className="flex justify-between">
                <div className="space-x-2">
                  <button
                    onClick={() => {
                      setSelectedNotification(null)
                      handleEdit(selectedNotification)
                    }}
                    className="px-4 py-2 bg-yellow-500 text-white rounded-md hover:bg-yellow-600 transition-colors duration-200"
                  >
                    Chỉnh sửa
                  </button>
                  <button
                    onClick={() => {
                      setSelectedNotification(null)
                      handleDelete(selectedNotification.id)
                    }}
                    className="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 transition-colors duration-200"
                  >
                    Xóa
                  </button>
                </div>
                <button
                  onClick={() => setSelectedNotification(null)}
                  className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 transition-colors duration-200"
                >
                  Đóng
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Notifications List */}
      <div className="bg-white rounded-lg shadow border border-gray-200">
        {loading ? (
          <div className="p-8 text-center">
            <p className="text-gray-500">Đang tải thông báo...</p>
          </div>
        ) : notifications.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-gray-500">Chưa có thông báo nào</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {notifications.map((notification) => (
              <div key={notification.id} className="p-4 hover:bg-gray-50">
                <div className="flex justify-between items-start">
                  <div 
                    className="flex-1 cursor-pointer"
                    onClick={() => setSelectedNotification(notification)}
                  >
                    <h3 className="font-medium text-gray-900 hover:text-blue-600">
                      {notification.title}
                    </h3>
                    <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                      {notification.content}
                    </p>
                    <div className="flex space-x-4 mt-2 text-xs text-gray-500">
                      <span>Tạo: {formatDate(notification.created_at)}</span>
                      {notification.updated_at !== notification.created_at && (
                        <span>Sửa: {formatDate(notification.updated_at)}</span>
                      )}
                    </div>
                  </div>
                  <div className="flex space-x-2 ml-4">
                    <button
                      onClick={() => handleEdit(notification)}
                      className="text-yellow-600 hover:text-yellow-800 text-sm"
                    >
                      Sửa
                    </button>
                    <button
                      onClick={() => handleDelete(notification.id)}
                      className="text-red-600 hover:text-red-800 text-sm"
                    >
                      Xóa
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default NotificationManagement