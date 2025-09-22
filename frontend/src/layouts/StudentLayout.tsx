import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useStudentLanguage } from '../pages/student/useStudentLanguage'
import { useNotifications } from '../hooks/useNotifications'
import type { ReactNode } from 'react'

interface StudentLayoutProps {
  children: ReactNode
}

const StudentLayout = ({ children }: StudentLayoutProps) => {
  const navigate = useNavigate()
  const location = useLocation()
  const { logout, userInfo } = useAuth()
  const { language, changeLanguage, t } = useStudentLanguage()
  const { notifications, loading, hasMore, loadMore, formatDate } = useNotifications()
  const [chatbotOpen, setChatbotOpen] = useState(false)
  const [notificationOpen, setNotificationOpen] = useState(false)
  const [studyMenuOpen, setStudyMenuOpen] = useState(false)
  const [scholarshipMenuOpen, setScholarshipMenuOpen] = useState(false)
  const [supportMenuOpen, setSupportMenuOpen] = useState(false)
  const [registrationMenuOpen, setRegistrationMenuOpen] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false)
  const [selectedNotification, setSelectedNotification] = useState<any>(null)

  // Since new notification system doesn't have isRead, we show all notifications
  const unreadCount = notifications.length > 0 ? notifications.length : 0

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
    setScholarshipMenuOpen(false)
    setSupportMenuOpen(false)
    setRegistrationMenuOpen(false)
    setNotificationOpen(false)
  }

  const toggleChatbot = () => {
    setChatbotOpen(!chatbotOpen)
  }

  const handleNotificationClick = (notification: any) => {
    setSelectedNotification(notification)
  }

  const isActive = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(path + '/')
  }

  return (
    <div className="min-h-screen w-screen flex flex-col bg-gray-50 overflow-x-hidden">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 w-full">
        <div className="w-full max-w-none px-4 py-2">
          <div className="flex justify-between items-center w-full min-w-full">
            {/* Logo */}
            <button 
              onClick={() => navigate('/student')}
              className="flex items-center space-x-2 hover:opacity-90 transition-opacity duration-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 focus:ring-offset-white rounded-lg p-2 bg-gray-50"
            >
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-sm">SP</span>
              </div>
              <h1 className="text-base font-bold text-gray-800">STUDENT PORTAL</h1>
            </button>

            {/* Navigation Menu */}
            <div className="hidden md:flex items-center flex-1 justify-end mr-4">
              <div className="flex items-center space-x-1">
                {/* Học tập */}
                <div className="relative">
                  <button 
                    className={`h-8 px-3 text-xs font-medium transition-all duration-200 flex items-center space-x-1 whitespace-nowrap rounded ${
                      isActive('/student/schedule') || isActive('/student/grades') || isActive('/student/curriculum')
                        ? 'bg-blue-600 text-white' 
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                    onMouseEnter={() => setStudyMenuOpen(true)}
                    onMouseLeave={() => setStudyMenuOpen(true)}
                  >
                    <span>📚</span>
                    <span className="hidden lg:inline">{t.study}</span>
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
                        📅 {t.schedule}
                      </button>
                      <button onClick={() => navigateTo('/student/grades')} className="block w-full px-3 py-1.5 text-xs text-gray-700 hover:bg-blue-50 text-left">
                        📊 {t.grades}
                      </button>
                      <button onClick={() => navigateTo('/student/curriculum')} className="block w-full px-3 py-1.5 text-xs text-gray-700 hover:bg-blue-50 text-left">
                        📖 {t.curriculum}
                      </button>
                    </div>
                  )}
                </div>

                {/* Đăng ký học tập */}
                <div className="relative">
                  <button 
                    className={`h-8 px-3 text-xs font-medium transition-all duration-200 flex items-center space-x-1 whitespace-nowrap rounded ${
                      isActive('/student/subject-registration') || isActive('/student/class-registration')
                        ? 'bg-blue-600 text-white' 
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                    onMouseEnter={() => setRegistrationMenuOpen(true)}
                    onMouseLeave={() => setRegistrationMenuOpen(true)}
                  >
                    <span>📝</span>
                    <span className="hidden lg:inline">{t.registration}</span>
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
                        📚 {t.subjectRegistration}
                      </button>
                      <button onClick={() => navigateTo('/student/class-registration')} className="block w-full px-3 py-1.5 text-xs text-gray-700 hover:bg-blue-50 text-left">
                        🏫 {t.classRegistration}
                      </button>
                    </div>
                  )}
                </div>

                {/* Biểu mẫu */}
                <button 
                  className={`h-8 px-3 text-xs font-medium transition-all duration-200 whitespace-nowrap rounded flex items-center space-x-1 ${
                    isActive('/student/forms')
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  onClick={() => navigateTo('/student/forms')}
                >
                  <span>📄</span>
                  <span className="hidden lg:inline">{t.forms}</span>
                </button>

                {/* Học bổng */}
                <div className="relative">
                  <button 
                    className={`h-8 px-3 text-xs font-medium transition-all duration-200 flex items-center space-x-1 whitespace-nowrap rounded ${
                      isActive('/student/scholarships')
                        ? 'bg-blue-600 text-white' 
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                    onMouseEnter={() => setScholarshipMenuOpen(true)}
                    onMouseLeave={() => setScholarshipMenuOpen(true)}
                  >
                    <span>🏆</span>
                    <span className="hidden lg:inline">{t.scholarships}</span>
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
                        ? 'bg-blue-600 text-white' 
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                    onMouseEnter={() => setSupportMenuOpen(true)}
                    onMouseLeave={() => setSupportMenuOpen(true)}
                  >
                    <span>❓</span>
                    <span className="hidden lg:inline">{t.support}</span>
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
                        📖 {t.userGuide}
                      </button>
                      <button onClick={() => navigateTo('/student/support/faq')} className="block w-full px-3 py-1.5 text-xs text-gray-700 hover:bg-blue-50 text-left">
                        ❓ {t.faq}
                      </button>
                      <button onClick={() => navigateTo('/student/support/feedback')} className="block w-full px-3 py-1.5 text-xs text-gray-700 hover:bg-blue-50 text-left">
                        💬 {t.feedback}
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* Language Switcher */}
              <div className="relative flex items-center bg-white border border-gray-300 h-8 rounded-none">
                {/* Sliding background */}
                <div
                  className={`absolute top-0 bottom-0 w-1/2 bg-blue-100 border-blue-200 transition-transform duration-300 ease-in-out ${
                    language === 'vi' ? 'translate-x-full' : 'translate-x-0'
                  }`}
                />
                
                {/* EN Button */}
                <button
                  onClick={() => changeLanguage('en')}
                  className={`relative z-10 flex-1 h-full px-3 text-xs font-medium transition-colors duration-300 rounded-none ${
                    language === 'en'
                      ? 'text-blue-700 font-semibold'
                      : 'text-gray-600 hover:text-gray-800'
                  }`}
                >
                  EN
                </button>
                
                {/* VI Button */}
                <button
                  onClick={() => changeLanguage('vi')}
                  className={`relative z-10 flex-1 h-full px-3 text-xs font-medium transition-colors duration-300 rounded-none ${
                    language === 'vi'
                      ? 'text-blue-700 font-semibold'
                      : 'text-gray-600 hover:text-gray-800'
                  }`}
                >
                  VI
                </button>
              </div>
            </div>

            {/* Mobile menu và User actions */}
            <div className="flex items-center space-x-2">
              {/* Mobile Menu Button */}
              <button 
                className="md:hidden h-8 w-8 rounded-md flex items-center justify-center bg-gray-200 text-gray-700 hover:bg-gray-300 hover:text-gray-800 transition-all duration-200"
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
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
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
                      <h3 className="font-semibold text-gray-800">Thông báo hệ thống</h3>
                    </div>
                    {notifications.length === 0 ? (
                      <div className="px-4 py-6 text-center text-gray-500">
                        <p>Chưa có thông báo nào</p>
                      </div>
                    ) : (
                      <>
                        {notifications.map(notification => (
                          <div 
                            key={notification.id}
                            className="px-4 py-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100"
                            onClick={() => handleNotificationClick(notification)}
                          >
                            <h4 className="text-sm font-medium text-gray-900">{notification.title}</h4>
                            <p className="text-xs text-gray-600 mt-1 line-clamp-2">{notification.content}</p>
                            <div className="flex justify-between items-center mt-2">
                              <p className="text-xs text-gray-400">Tạo: {formatDate(notification.created_at)}</p>
                              {notification.updated_at !== notification.created_at && (
                                <p className="text-xs text-gray-400">Sửa: {formatDate(notification.updated_at)}</p>
                              )}
                            </div>
                          </div>
                        ))}
                        {hasMore && (
                          <div className="px-4 py-2">
                            <button 
                              onClick={loadMore}
                              disabled={loading}
                              className="w-full text-center text-blue-600 hover:text-blue-800 text-sm font-medium py-2"
                            >
                              {loading ? 'Đang tải...' : 'Xem thêm'}
                            </button>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                )}
              </div>

              {/* Logout Button */}
              <button
                onClick={handleLogoutClick}
                className="h-8 px-3 bg-gray-500 text-white rounded-md hover:bg-gray-400 border border-gray-300 transition-all duration-200 text-xs font-medium flex items-center space-x-1 shadow-sm hover:shadow-md"
              >
                <span>👤</span>
                <span className="hidden lg:inline">{t.logout}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-gray-100 border-t border-gray-300 w-full">
            <div className="w-full px-4 py-2 space-y-1">
              <button onClick={() => { navigateTo('/student/schedule'); setMobileMenuOpen(false); }} className="block w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-200 rounded">
                📚 {t.study}
              </button>
              <button onClick={() => { navigateTo('/student/subject-registration'); setMobileMenuOpen(false); }} className="block w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-200 rounded">
                📝 {t.registration}
              </button>
              <button onClick={() => { navigateTo('/student/forms'); setMobileMenuOpen(false); }} className="block w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-200 rounded">
                📄 {t.forms}
              </button>
              <button onClick={() => { navigateTo('/student/scholarships'); setMobileMenuOpen(false); }} className="block w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-200 rounded">
                🏆 {t.scholarships}
              </button>
              <button onClick={() => { navigateTo('/student/support/faq'); setMobileMenuOpen(false); }} className="block w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-200 rounded">
                ❓ {t.support}
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
              
              <div className="prose max-w-none">
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
              
              <div className="mt-6 flex justify-end">
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