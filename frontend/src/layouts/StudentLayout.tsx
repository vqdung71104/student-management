import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import type { ReactNode } from 'react'

interface StudentLayoutProps {
  children: ReactNode
}

const StudentLayout = ({ children }: StudentLayoutProps) => {
  const navigate = useNavigate()
  const location = useLocation()
  const { logout, userInfo } = useAuth()
  const [chatbotOpen, setChatbotOpen] = useState(false)
  const [notifications, setNotifications] = useState([
    { id: 1, title: 'Thông báo đăng ký học kỳ 2024.1', content: 'Thời gian đăng ký từ 15/01 đến 30/01/2024', isRead: false, time: '2 giờ trước' },
    { id: 2, title: 'Kết quả học tập kỳ 2023.2', content: 'Kết quả đã được cập nhật', isRead: true, time: '1 ngày trước' },
    { id: 3, title: 'Học bổng khuyến khích học tập', content: 'Mở đăng ký học bổng cho sinh viên xuất sắc', isRead: false, time: '3 ngày trước' }
  ])
  const [notificationOpen, setNotificationOpen] = useState(false)
  const [studyMenuOpen, setStudyMenuOpen] = useState(false)
  const [projectMenuOpen, setProjectMenuOpen] = useState(false)
  const [scholarshipMenuOpen, setScholarshipMenuOpen] = useState(false)
  const [integratedStudyMenuOpen, setIntegratedStudyMenuOpen] = useState(false)
  const [supportMenuOpen, setSupportMenuOpen] = useState(false)
  const [registrationMenuOpen, setRegistrationMenuOpen] = useState(false)

  const unreadCount = notifications.filter(n => !n.isRead).length

  const navigateTo = (path: string) => {
    navigate(path)
    setStudyMenuOpen(false)
    setProjectMenuOpen(false)
    setScholarshipMenuOpen(false)
    setIntegratedStudyMenuOpen(false)
    setSupportMenuOpen(false)
    setRegistrationMenuOpen(false)
    setNotificationOpen(false)
  }

  const toggleChatbot = () => {
    setChatbotOpen(!chatbotOpen)
  }

  const markNotificationAsRead = (id: number) => {
    setNotifications(notifications.map(n => 
      n.id === id ? { ...n, isRead: true } : n
    ))
  }

  const isActive = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(path + '/')
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-lg border-b border-gray-200">
        <div className="container mx-auto px-4 py-3">
          <div className="flex justify-between items-center">
            {/* Logo */}
            <button 
              onClick={() => navigate('/student')}
              className="flex items-center space-x-3 hover:opacity-80 transition-opacity duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-lg p-1"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              <h1 className="text-xl font-bold text-gray-800">STUDENT PORTAL</h1>
            </button>

            {/* Navigation Menu */}
            <div className="hidden md:flex items-center space-x-2">
              {/* Học tập */}
              <div className="relative">
                <button 
                  className={`px-3 py-2 rounded-lg font-medium transition-all duration-200 flex items-center space-x-1 ${
                    isActive('/student/schedule') || isActive('/student/grades') || isActive('/student/curriculum')
                      ? 'bg-blue-600 text-white shadow-lg' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  onMouseEnter={() => setStudyMenuOpen(true)}
                  onMouseLeave={() => setStudyMenuOpen(true)}
                >
                  <span>📚 Học tập</span>
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {studyMenuOpen && (
                  <div 
                    className="absolute top-full left-0 mt-1 w-48 bg-white rounded-lg shadow-xl border border-gray-200 py-2 z-50"
                    onMouseEnter={() => setStudyMenuOpen(true)}
                    onMouseLeave={() => setStudyMenuOpen(false)}
                  >
                    <button onClick={() => navigateTo('/student/schedule')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      📅 Thời khóa biểu
                    </button>
                    <button onClick={() => navigateTo('/student/grades')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      📊 Xem điểm
                    </button>
                    <button onClick={() => navigateTo('/student/curriculum')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      📖 Chương trình đào tạo
                    </button>
                  </div>
                )}
              </div>

              {/* Đăng ký học tập */}
              <div className="relative">
                <button 
                  className={`px-3 py-2 rounded-lg font-medium transition-all duration-200 flex items-center space-x-1 ${
                    isActive('/student/subject-registration') || isActive('/student/class-registration')
                      ? 'bg-blue-600 text-white shadow-lg' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  onMouseEnter={() => setRegistrationMenuOpen(true)}
                  onMouseLeave={() => setRegistrationMenuOpen(true)}
                >
                  <span>📝 Đăng ký học tập</span>
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {registrationMenuOpen && (
                  <div 
                    className="absolute top-full left-0 mt-1 w-52 bg-white rounded-lg shadow-xl border border-gray-200 py-2 z-50"
                    onMouseEnter={() => setRegistrationMenuOpen(true)}
                    onMouseLeave={() => setRegistrationMenuOpen(false)}
                  >
                    <button onClick={() => navigateTo('/student/subject-registration')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      📚 Đăng ký học phần
                    </button>
                    <button onClick={() => navigateTo('/student/class-registration')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      🏫 Đăng ký lớp
                    </button>
                  </div>
                )}
              </div>

              {/* Đồ án */}
              <div className="relative">
                <button 
                  className={`px-3 py-2 rounded-lg font-medium transition-all duration-200 flex items-center space-x-1 ${
                    isActive('/student/projects')
                      ? 'bg-blue-600 text-white shadow-lg' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  onMouseEnter={() => setProjectMenuOpen(true)}
                  onMouseLeave={() => setProjectMenuOpen(true)}
                >
                  <span>💼 Đồ án</span>
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {projectMenuOpen && (
                  <div 
                    className="absolute top-full left-0 mt-1 w-56 bg-white rounded-lg shadow-xl border border-gray-200 py-2 z-50"
                    onMouseEnter={() => setProjectMenuOpen(true)}
                    onMouseLeave={() => setProjectMenuOpen(false)}
                  >
                    <button onClick={() => navigateTo('/student/projects')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      📋 Danh sách đồ án
                    </button>
                    <button onClick={() => navigateTo('/student/projects')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      📝 Đăng ký nguyện vọng
                    </button>
                    <button onClick={() => navigateTo('/student/projects')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      🎯 Định hướng đề tài
                    </button>
                    <button onClick={() => navigateTo('/student/projects')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      🏢 DS Doanh nghiệp
                    </button>
                    <button onClick={() => navigateTo('/student/projects')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      🔍 Kiểm tra trùng lặp
                    </button>
                  </div>
                )}
              </div>

              {/* Biểu mẫu */}
              <button 
                className={`px-3 py-2 rounded-lg font-medium transition-all duration-200 ${
                  isActive('/student/forms')
                    ? 'bg-blue-600 text-white shadow-lg' 
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
                onClick={() => navigateTo('/student/forms')}
              >
                📄 Biểu mẫu
              </button>

              {/* Học bổng */}
              <div className="relative">
                <button 
                  className={`px-3 py-2 rounded-lg font-medium transition-all duration-200 flex items-center space-x-1 ${
                    isActive('/student/scholarships')
                      ? 'bg-blue-600 text-white shadow-lg' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  onMouseEnter={() => setScholarshipMenuOpen(true)}
                  onMouseLeave={() => setScholarshipMenuOpen(true)}
                >
                  <span>💰 Học bổng</span>
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {scholarshipMenuOpen && (
                  <div 
                    className="absolute top-full left-0 mt-1 w-52 bg-white rounded-lg shadow-xl border border-gray-200 py-2 z-50"
                    onMouseEnter={() => setScholarshipMenuOpen(true)}
                    onMouseLeave={() => setScholarshipMenuOpen(false)}
                  >
                    <button onClick={() => navigateTo('/student/scholarships')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      📝 Đăng ký học bổng
                    </button>
                    <button onClick={() => navigateTo('/student/scholarships')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      📏 Điều kiện xét học bổng
                    </button>
                  </div>
                )}
              </div>

              {/* Học tích hợp */}
              <div className="relative">
                <button 
                  className={`px-3 py-2 rounded-lg font-medium transition-all duration-200 flex items-center space-x-1 ${
                    location.pathname.includes('integrated')
                      ? 'bg-blue-600 text-white shadow-lg' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  onMouseEnter={() => setIntegratedStudyMenuOpen(true)}
                  onMouseLeave={() => setIntegratedStudyMenuOpen(true)}
                >
                  <span>🎓 Học tích hợp</span>
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {integratedStudyMenuOpen && (
                  <div className="absolute top-full left-0 mt-1 w-48 bg-white rounded-lg shadow-xl border border-gray-200 py-2 z-50"
                    onMouseEnter={() => setIntegratedStudyMenuOpen(true)}
                    onMouseLeave={() => setIntegratedStudyMenuOpen(false)}
                  >
                    <button onClick={() => navigateTo('/student')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      👨‍💼 Kỹ sư chuyên sâu
                    </button>
                    <button onClick={() => navigateTo('/student')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      🎯 Thạc sỹ
                    </button>
                  </div>
                )}
              </div>

              {/* NCKH */}
              <button 
                className={`px-3 py-2 rounded-lg font-medium transition-all duration-200 ${
                  location.pathname === '/student/research'
                    ? 'bg-blue-600 text-white shadow-lg' 
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
                onClick={() => navigateTo('/student')}
              >
                🔬 NCKH
              </button>

              {/* CT Trao đổi */}
              <button 
                className={`px-3 py-2 rounded-lg font-medium transition-all duration-200 ${
                  location.pathname === '/student/exchange'
                    ? 'bg-blue-600 text-white shadow-lg' 
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
                onClick={() => navigateTo('/student')}
              >
                🌍 CT Trao đổi
              </button>

              {/* Hỗ trợ */}
              <div className="relative">
                <button 
                  className={`px-3 py-2 rounded-lg font-medium transition-all duration-200 flex items-center space-x-1 ${
                    location.pathname.includes('/student/support')
                      ? 'bg-blue-600 text-white shadow-lg' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  onMouseEnter={() => setSupportMenuOpen(true)}
                  onMouseLeave={() => setSupportMenuOpen(true)}
                >
                  <span>❓ Hỗ trợ</span>
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {supportMenuOpen && (
                  <div 
                    className="absolute top-full left-0 mt-1 w-52 bg-white rounded-lg shadow-xl border border-gray-200 py-2 z-50"
                    onMouseEnter={() => setSupportMenuOpen(true)}
                    onMouseLeave={() => setSupportMenuOpen(false)}
                  >
                    <button onClick={() => navigateTo('/student/support/user-guide')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      📖 Hướng dẫn sử dụng
                    </button>
                    <button onClick={() => navigateTo('/student/support/faq')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      ❓ Những câu hỏi thường gặp
                    </button>
                    <button onClick={() => navigateTo('/student/support/feedback')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      💬 Phản hồi và góp ý
                    </button>
                  </div>
                )}
              </div>

              {/* Notification Bell */}
              <div className="relative">
                <button 
                  className={`p-2 rounded-lg transition-all duration-200 relative ${
                    notificationOpen 
                      ? 'bg-red-500 text-white shadow-lg' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  onClick={() => setNotificationOpen(!notificationOpen)}
                >
                  🔔
                  {unreadCount > 0 && (
                    <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                      {unreadCount}
                    </span>
                  )}
                </button>
                {notificationOpen && (
                  <div className="absolute top-full right-0 mt-2 w-80 bg-white rounded-lg shadow-xl border border-gray-200 py-2 z-50 max-h-96 overflow-y-auto">
                    <div className="px-4 py-2 border-b border-gray-200">
                      <h3 className="font-semibold text-gray-800">Thông báo</h3>
                    </div>
                    {notifications.map(notification => (
                      <div 
                        key={notification.id}
                        className={`px-4 py-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100 ${!notification.isRead ? 'bg-blue-50' : ''}`}
                        onClick={() => markNotificationAsRead(notification.id)}
                      >
                        <h4 className="text-sm font-medium text-gray-900">{notification.title}</h4>
                        <p className="text-xs text-gray-600 mt-1">{notification.content}</p>
                        <p className="text-xs text-gray-400 mt-1">{notification.time}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Logout Button */}
            <button
              onClick={logout}
              className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-all duration-200 font-medium"
            >
              🚪 Đăng xuất
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-grow container mx-auto px-4 py-6">
        {children}
      </main>

      {/* Chatbot */}
      {chatbotOpen && (
        <div className="fixed bottom-4 right-4 w-80 bg-white rounded-lg shadow-xl border border-gray-200 z-50">
          <div className="bg-blue-600 rounded-t-lg p-4 cursor-pointer" onClick={toggleChatbot}>
            <div className="flex justify-between items-center text-white">
              <div className="flex items-center space-x-2">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
                <h3 className="font-medium">Trợ lý học tập</h3>
              </div>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
          </div>
          <div className="p-4">
            <p className="text-gray-600 text-sm">
              Xin chào {userInfo?.student_name || 'bạn'}! Tôi có thể giúp gì cho bạn?
            </p>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="bg-gray-800 text-white py-8">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <h3 className="text-lg font-semibold mb-3">Liên hệ</h3>
              <ul className="text-sm text-gray-400 space-y-2">
                <li>📞 Hotline: 024.3868.3008</li>
                <li>✉️ Email: registry@hust.edu.vn</li>
                <li>🏢 Phòng Đào tạo</li>
              </ul>
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-3">Thông tin</h3>
              <div className="text-sm text-gray-400 space-y-1">
                <p>Trường Đại học Bách khoa Hà Nội</p>
                <p>Địa chỉ: Số 1 Đại Cồ Việt, Hai Bà Trưng, Hà Nội</p>
              </div>
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-3">Trợ giúp</h3>
              <ul className="text-sm text-gray-400 space-y-2">
                <li><a href="#" className="hover:text-white transition">Hướng dẫn sử dụng</a></li>
                <li><a href="#" className="hover:text-white transition">Câu hỏi thường gặp</a></li>
                <li><a href="#" className="hover:text-white transition">Quy định đăng ký học phần</a></li>
              </ul>
            </div>
          </div>
          <div className="mt-6 pt-4 border-t border-gray-700 text-center text-sm text-gray-400">
            <p>© 2023 Hệ thống đăng ký học tập. Bản quyền thuộc về Trường Đại học.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default StudentLayout
