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
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false)

  const unreadCount = notifications.filter(n => !n.isRead).length

  const handleLogoutClick = () => {
    setShowLogoutConfirm(true)
  }

  const handleConfirmLogout = () => {
    setShowLogoutConfirm(false)
    logout()
  }

  const handleCancelLogout = () => {
    setShowLogoutConfirm(false)
  }

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
    <div className="min-h-screen w-screen flex flex-col bg-gray-50 overflow-x-hidden">
      {/* Header */}
      <header className="bg-blue-600 shadow-sm border-b border-blue-700 w-full">
        <div className="w-full max-w-none px-4 py-2">
          <div className="flex justify-between items-center w-full min-w-full">
            {/* Logo */}
            <button 
              onClick={() => navigate('/student')}
              className="flex items-center space-x-2 hover:opacity-90 transition-opacity duration-200 focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-blue-600 rounded-lg p-2 bg-white bg-opacity-10"
            >
              <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center">
                <span className="text-blue-600 font-bold text-sm">SP</span>
              </div>
              <h1 className="text-base font-bold text-white">STUDENT PORTAL</h1>
            </button>

            {/* Navigation Menu */}
            <div className="hidden md:flex items-center flex-1 justify-end mr-4">
              <div className="flex items-center space-x-1">
                {/* Học tập */}
                <div className="relative">
                  <button 
                    className={`h-8 px-3 text-xs font-medium transition-all duration-200 flex items-center space-x-1 whitespace-nowrap rounded ${
                      isActive('/student/schedule') || isActive('/student/grades') || isActive('/student/curriculum')
                        ? 'bg-blue-700 text-white' 
                        : 'bg-blue-600 text-blue-100 hover:bg-blue-700 hover:text-white'
                    }`}
                    onMouseEnter={() => setStudyMenuOpen(true)}
                    onMouseLeave={() => setStudyMenuOpen(true)}
                  >
                    <span>📚</span>
                    <span className="hidden lg:inline">Học tập</span>
                    <svg className="w-2 h-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  {studyMenuOpen && (
                    <div 
                      className="absolute top-full left-0 mt-1 w-44 bg-white rounded-md shadow-lg border border-gray-200 py-1 z-50"
                      onMouseEnter={() => setStudyMenuOpen(true)}
                      onMouseLeave={() => setStudyMenuOpen(false)}
                    >
                      <button onClick={() => navigateTo('/student/schedule')} className="block w-full px-3 py-1.5 text-xs text-gray-700 hover:bg-blue-50 text-left">
                        📅 Thời khóa biểu
                      </button>
                      <button onClick={() => navigateTo('/student/grades')} className="block w-full px-3 py-1.5 text-xs text-gray-700 hover:bg-blue-50 text-left">
                        📊 Xem điểm
                      </button>
                      <button onClick={() => navigateTo('/student/curriculum')} className="block w-full px-3 py-1.5 text-xs text-gray-700 hover:bg-blue-50 text-left">
                        📖 Chương trình đào tạo
                      </button>
                    </div>
                  )}
                </div>

                {/* Đăng ký học tập */}
                <div className="relative">
                  <button 
                    className={`h-8 px-3 text-xs font-medium transition-all duration-200 flex items-center space-x-1 whitespace-nowrap rounded ${
                      isActive('/student/subject-registration') || isActive('/student/class-registration')
                        ? 'bg-blue-700 text-white' 
                        : 'bg-blue-600 text-blue-100 hover:bg-blue-700 hover:text-white'
                    }`}
                    onMouseEnter={() => setRegistrationMenuOpen(true)}
                    onMouseLeave={() => setRegistrationMenuOpen(true)}
                  >
                    <span>📝</span>
                    <span className="hidden lg:inline">Đăng ký học tập</span>
                    <svg className="w-2 h-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  {registrationMenuOpen && (
                    <div 
                      className="absolute top-full left-0 mt-1 w-44 bg-white rounded-md shadow-lg border border-gray-200 py-1 z-50"
                      onMouseEnter={() => setRegistrationMenuOpen(true)}
                      onMouseLeave={() => setRegistrationMenuOpen(false)}
                    >
                      <button onClick={() => navigateTo('/student/subject-registration')} className="block w-full px-3 py-1.5 text-xs text-gray-700 hover:bg-blue-50 text-left">
                        📚 Đăng ký học phần
                      </button>
                      <button onClick={() => navigateTo('/student/class-registration')} className="block w-full px-3 py-1.5 text-xs text-gray-700 hover:bg-blue-50 text-left">
                        🏫 Đăng ký lớp
                      </button>
                    </div>
                  )}
                </div>

                {/* Biểu mẫu */}
                <button 
                  className={`h-8 px-3 text-xs font-medium transition-all duration-200 whitespace-nowrap rounded flex items-center space-x-1 ${
                    isActive('/student/forms')
                      ? 'bg-blue-700 text-white' 
                      : 'bg-blue-600 text-blue-100 hover:bg-blue-700 hover:text-white'
                  }`}
                  onClick={() => navigateTo('/student/forms')}
                >
                  <span>📄</span>
                  <span className="hidden lg:inline">Biểu mẫu</span>
                </button>

                {/* Học bổng */}
                <div className="relative">
                  <button 
                    className={`h-8 px-3 text-xs font-medium transition-all duration-200 flex items-center space-x-1 whitespace-nowrap rounded ${
                      isActive('/student/scholarships')
                        ? 'bg-blue-700 text-white' 
                        : 'bg-blue-600 text-blue-100 hover:bg-blue-700 hover:text-white'
                    }`}
                    onMouseEnter={() => setScholarshipMenuOpen(true)}
                    onMouseLeave={() => setScholarshipMenuOpen(true)}
                  >
                    <span>🏆</span>
                    <span className="hidden lg:inline">Học bổng</span>
                    <svg className="w-2 h-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  {scholarshipMenuOpen && (
                    <div 
                      className="absolute top-full left-0 mt-1 w-48 bg-white rounded-md shadow-lg border border-gray-200 py-1 z-50"
                      onMouseEnter={() => setScholarshipMenuOpen(true)}
                      onMouseLeave={() => setScholarshipMenuOpen(false)}
                    >
                      <button onClick={() => navigateTo('/student/scholarships')} className="block w-full px-3 py-1.5 text-xs text-gray-700 hover:bg-blue-50 text-left">
                        📝 Đăng ký học bổng
                      </button>
                      <button onClick={() => navigateTo('/student/scholarships')} className="block w-full px-3 py-1.5 text-xs text-gray-700 hover:bg-blue-50 text-left">
                        📏 Điều kiện xét học bổng
                      </button>
                    </div>
                  )}
                </div>

                {/* Hỗ trợ */}
                <div className="relative">
                  <button 
                    className={`h-8 px-3 text-xs font-medium transition-all duration-200 flex items-center space-x-1 whitespace-nowrap rounded ${
                      location.pathname.includes('/student/support')
                        ? 'bg-blue-700 text-white' 
                        : 'bg-blue-600 text-blue-100 hover:bg-blue-700 hover:text-white'
                    }`}
                    onMouseEnter={() => setSupportMenuOpen(true)}
                    onMouseLeave={() => setSupportMenuOpen(true)}
                  >
                    <span>❓</span>
                    <span className="hidden lg:inline">Hỗ trợ</span>
                    <svg className="w-2 h-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  {supportMenuOpen && (
                    <div 
                      className="absolute top-full left-0 mt-1 w-52 bg-white rounded-md shadow-lg border border-gray-200 py-1 z-50"
                      onMouseEnter={() => setSupportMenuOpen(true)}
                      onMouseLeave={() => setSupportMenuOpen(false)}
                    >
                      <button onClick={() => navigateTo('/student/support/user-guide')} className="block w-full px-3 py-1.5 text-xs text-gray-700 hover:bg-blue-50 text-left">
                        📖 Hướng dẫn sử dụng
                      </button>
                      <button onClick={() => navigateTo('/student/support/faq')} className="block w-full px-3 py-1.5 text-xs text-gray-700 hover:bg-blue-50 text-left">
                        ❓ Những câu hỏi thường gặp
                      </button>
                      <button onClick={() => navigateTo('/student/support/feedback')} className="block w-full px-3 py-1.5 text-xs text-gray-700 hover:bg-blue-50 text-left">
                        💬 Phản hồi và góp ý
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Mobile menu và User actions */}
            <div className="flex items-center space-x-2">
              {/* Mobile Menu Button */}
              <button 
                className="md:hidden h-8 w-8 rounded-md flex items-center justify-center bg-blue-600 text-blue-100 hover:bg-blue-700 hover:text-white transition-all duration-200"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>

              {/* Notification Bell */}
              <div className="relative">
                <button 
                  className={`h-8 w-8 rounded-md flex items-center justify-center text-xs transition-all duration-200 relative ${
                    notificationOpen 
                      ? 'bg-blue-700 text-white' 
                      : 'bg-blue-600 text-blue-100 hover:bg-blue-700 hover:text-white'
                  }`}
                  onClick={() => setNotificationOpen(!notificationOpen)}
                >
                  🔔
                  {unreadCount > 0 && (
                    <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-4 w-4 flex items-center justify-center">
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

              {/* Logout Button */}
              <button
                onClick={handleLogoutClick}
                className="h-8 px-3 bg-blue-500 text-white rounded-md hover:bg-blue-400 border border-blue-300 transition-all duration-200 text-xs font-medium flex items-center space-x-1 shadow-sm hover:shadow-md"
              >
                <span>👤</span>
                <span className="hidden lg:inline">Đăng xuất</span>
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-blue-500 border-t border-blue-700 w-full">
            <div className="w-full px-4 py-2 space-y-1">
              <button onClick={() => { navigateTo('/student/schedule'); setMobileMenuOpen(false); }} className="block w-full text-left px-3 py-2 text-sm text-blue-100 hover:bg-blue-600 rounded">
                📚 Học tập
              </button>
              <button onClick={() => { navigateTo('/student/subject-registration'); setMobileMenuOpen(false); }} className="block w-full text-left px-3 py-2 text-sm text-blue-100 hover:bg-blue-600 rounded">
                📝 Đăng ký học tập
              </button>
              <button onClick={() => { navigateTo('/student/forms'); setMobileMenuOpen(false); }} className="block w-full text-left px-3 py-2 text-sm text-blue-100 hover:bg-blue-600 rounded">
                📄 Biểu mẫu
              </button>
              <button onClick={() => { navigateTo('/student/scholarships'); setMobileMenuOpen(false); }} className="block w-full text-left px-3 py-2 text-sm text-blue-100 hover:bg-blue-600 rounded">
                🏆 Học bổng
              </button>
              <button onClick={() => { navigateTo('/student/support/faq'); setMobileMenuOpen(false); }} className="block w-full text-left px-3 py-2 text-sm text-blue-100 hover:bg-blue-600 rounded">
                ❓ Hỗ trợ
              </button>
            </div>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="flex-grow w-full max-w-none px-4 py-6 overflow-x-hidden">
        <div className="w-full max-w-none">
          {children}
        </div>
      </main>

      {/* Logout Confirmation Modal */}
      {showLogoutConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl border border-gray-200 p-6 max-w-sm mx-4">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center">
                <span className="text-orange-600 text-xl">⚠️</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-900">Xác nhận đăng xuất</h3>
            </div>
            <p className="text-gray-600 mb-6">
              Bạn có chắc chắn muốn đăng xuất khỏi hệ thống không?
            </p>
            <div className="flex space-x-3">
              <button
                onClick={handleCancelLogout}
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition-colors duration-200 font-medium"
              >
                Hủy
              </button>
              <button
                onClick={handleConfirmLogout}
                className="flex-1 px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 transition-colors duration-200 font-medium"
              >
                Đăng xuất
              </button>
            </div>
          </div>
        </div>
      )}

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
            <div className="mt-4 space-y-2">
              <button className="w-full text-left p-2 bg-gray-100 rounded hover:bg-gray-200 text-sm">
                💬 Hướng dẫn đăng ký học phần
              </button>
              <button className="w-full text-left p-2 bg-gray-100 rounded hover:bg-gray-200 text-sm">
                📊 Xem kết quả học tập
              </button>
              <button className="w-full text-left p-2 bg-gray-100 rounded hover:bg-gray-200 text-sm">
                🏆 Thông tin học bổng
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Floating Chatbot Button */}
      <button
        onClick={toggleChatbot}
        className="fixed bottom-4 right-4 bg-blue-600 text-white p-3 rounded-full shadow-lg hover:bg-blue-700 transition-all duration-200 z-40"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
        </svg>
      </button>
    </div>
  )
}

export default StudentLayout