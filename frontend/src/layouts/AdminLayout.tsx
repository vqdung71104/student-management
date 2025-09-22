import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useLanguage } from '../pages/admin/useLanguage'
import type { ReactNode } from 'react'

interface AdminLayoutProps {
  children: ReactNode
}

const AdminLayout = ({ children }: AdminLayoutProps) => {
  const navigate = useNavigate()
  const location = useLocation()
  const { logout } = useAuth()
  const { language, changeLanguage, t } = useLanguage()
  const [subjectMenuOpen, setSubjectMenuOpen] = useState(false)
  const [settingsMenuOpen, setSettingsMenuOpen] = useState(false)
  const [chatbotOpen, setChatbotOpen] = useState(false)
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false)

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
    setSubjectMenuOpen(false)
    setSettingsMenuOpen(false)
  }

  const toggleChatbot = () => {
    setChatbotOpen(!chatbotOpen)
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
              onClick={() => navigate('/admin')}
              className="flex items-center space-x-2 hover:opacity-90 transition-opacity duration-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 focus:ring-offset-white rounded-lg p-2 bg-gray-50"
            >
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-sm">AP</span>
              </div>
              <h1 className="text-base font-bold text-gray-800">ADMIN PORTAL</h1>
            </button>

            {/* Navigation Menu */}
            <div className="hidden md:flex items-center flex-1 justify-end mr-4">
              <div className="flex items-center space-x-1">
                {/* Dashboard */}
                <button 
                  className={`h-8 px-3 text-xs font-medium transition-all duration-200 whitespace-nowrap rounded flex items-center space-x-1 ${
                    isActive('/admin') && location.pathname === '/admin'
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  onClick={() => navigateTo('/admin')}
                >
                  <span>📊</span>
                  <span className="hidden lg:inline">{t.dashboard}</span>
                </button>

                {/* Student Management */}
                <button 
                  className={`h-8 px-3 text-xs font-medium transition-all duration-200 whitespace-nowrap rounded flex items-center space-x-1 ${
                    isActive('/admin/students')
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  onClick={() => navigateTo('/admin/students')}
                >
                  <span>👥</span>
                  <span className="hidden lg:inline">{t.studentManagement}</span>
                </button>

                {/* Subject Management */}
                <div className="relative">
                  <button 
                    className={`h-8 px-3 text-xs font-medium transition-all duration-200 flex items-center space-x-1 whitespace-nowrap rounded ${
                      isActive('/admin/schedule') || isActive('/admin/subjects')
                        ? 'bg-blue-600 text-white' 
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                    onMouseEnter={() => setSubjectMenuOpen(true)}
                    onMouseLeave={() => setSubjectMenuOpen(true)}
                  >
                    <span>📚</span>
                    <span className="hidden lg:inline">{t.subjectManagement}</span>
                    <svg className="w-2 h-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  {subjectMenuOpen && (
                    <div 
                      className="absolute top-full left-0 mt-1 w-52 bg-white rounded-md shadow-lg border border-gray-200 py-1 z-50"
                      onMouseEnter={() => setSubjectMenuOpen(true)}
                      onMouseLeave={() => setSubjectMenuOpen(false)}
                    >
                      <button onClick={() => navigateTo('/admin/schedule-update')} className="block w-full px-3 py-1.5 text-xs text-gray-700 hover:bg-blue-50 text-left">
                        📅 {t.updateSchedule}
                      </button>
                      <button onClick={() => navigateTo('/admin/subjects')} className="block w-full px-3 py-1.5 text-xs text-gray-700 hover:bg-blue-50 text-left">
                        📄 {t.updateSubjects}
                      </button>
                    </div>
                  )}
                </div>

                {/* Settings */}
                <div className="relative">
                  <button 
                    className={`h-8 px-3 text-xs font-medium transition-all duration-200 flex items-center space-x-1 whitespace-nowrap rounded ${
                      isActive('/admin/settings')
                        ? 'bg-blue-600 text-white' 
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                    onMouseEnter={() => setSettingsMenuOpen(true)}
                    onMouseLeave={() => setSettingsMenuOpen(true)}
                  >
                    <span>⚙️</span>
                    <span className="hidden lg:inline">{t.settings}</span>
                    <svg className="w-2 h-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  {settingsMenuOpen && (
                    <div 
                      className="absolute top-full left-0 mt-1 w-52 bg-white rounded-md shadow-lg border border-gray-200 py-1 z-50"
                      onMouseEnter={() => setSettingsMenuOpen(true)}
                      onMouseLeave={() => setSettingsMenuOpen(false)}
                    >
                      <button onClick={() => navigateTo('/admin/feedback')} className="block w-full px-3 py-1.5 text-xs text-gray-700 hover:bg-blue-50 text-left">
                        💬 Trả lời phản hồi
                      </button>
                      <button onClick={() => navigateTo('/admin/faq')} className="block w-full px-3 py-1.5 text-xs text-gray-700 hover:bg-blue-50 text-left">
                        ❓ Quản lý FAQ
                      </button>
                      <button onClick={() => navigateTo('/admin/notifications')} className="block w-full px-3 py-1.5 text-xs text-gray-700 hover:bg-blue-50 text-left">
                        📢 Quản lý thông báo
                      </button>
                      <button onClick={() => navigateTo('/admin/settings')} className="block w-full px-3 py-1.5 text-xs text-gray-700 hover:bg-blue-50 text-left">
                        🔐 {t.changePassword}
                      </button>
                    </div>
                  )}
                </div>

                {/* Chatbot Support */}
                <button 
                  className={`h-8 px-3 text-xs font-medium transition-all duration-200 whitespace-nowrap rounded flex items-center space-x-1 ${
                    chatbotOpen 
                      ? 'bg-green-600 text-white' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  onClick={toggleChatbot}
                >
                  <span>🤖</span>
                  <span className="hidden lg:inline">{t.chatbotSupport}</span>
                </button>

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
              Bạn có chắc chắn muốn đăng xuất khỏi hệ thống quản trị không?
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
                className="flex-1 px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 transition-colors duration-200 font-medium"
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
                <h3 className="font-medium">Trợ lý quản trị</h3>
              </div>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
          </div>
          <div className="p-4">
            <p className="text-gray-600 text-sm">
              Xin chào Admin! Tôi có thể giúp gì cho bạn?
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

export default AdminLayout
