import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import type { ReactNode } from 'react'

interface AdminLayoutProps {
  children: ReactNode
}

const AdminLayout = ({ children }: AdminLayoutProps) => {
  const navigate = useNavigate()
  const location = useLocation()
  const { logout } = useAuth()
  const [subjectMenuOpen, setSubjectMenuOpen] = useState(false)
  const [settingsMenuOpen, setSettingsMenuOpen] = useState(false)
  const [language, setLanguage] = useState<'vi' | 'en'>('vi')
  const [chatbotOpen, setChatbotOpen] = useState(false)

  const texts = {
    vi: {
      dashboard: 'Bảng điều khiển',
      studentManagement: 'Quản lý sinh viên',
      subjectManagement: 'Quản lý học phần',
      settings: 'Cài đặt',
      chatbotSupport: 'Chatbot hỗ trợ',
      create: 'Tạo mới',
      update: 'Cập nhật',
      delete: 'Xóa',
      get: 'Danh sách',
      updateSchedule: 'Cập nhật thời khóa biểu',
      updateSubjects: 'Cập nhật danh sách học phần',
      languageSettings: 'Cài đặt ngôn ngữ',
      changePassword: 'Đổi mật khẩu',
      logout: 'Đăng xuất'
    },
    en: {
      dashboard: 'Dashboard',
      studentManagement: 'Student Management',
      subjectManagement: 'Subject Management',
      settings: 'Settings',
      chatbotSupport: 'Chatbot Support',
      create: 'Create',
      update: 'Update',
      delete: 'Delete',
      get: 'List',
      updateSchedule: 'Update Schedule',
      updateSubjects: 'Update Subject List',
      languageSettings: 'Language Settings',
      changePassword: 'Change Password',
      logout: 'Logout'
    }
  }

  const t = texts[language]

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
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-lg border-b border-gray-200">
        <div className="container mx-auto px-4 py-3">
          <div className="flex justify-between items-center">
            {/* Logo và Title */}
            <div className="flex items-center space-x-3">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <h1 className="text-xl font-bold text-gray-800">ADMIN PORTAL</h1>
            </div>

            {/* Navigation Menu */}
            <div className="hidden md:flex items-center space-x-4">
              {/* Dashboard Button */}
              <button 
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                  isActive('/admin') && location.pathname === '/admin'
                    ? 'bg-blue-600 text-white shadow-lg' 
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
                onClick={() => navigateTo('/admin')}
              >
                📊 {t.dashboard}
              </button>

              {/* Student Management Button */}
              <button 
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                  isActive('/admin/students')
                    ? 'bg-blue-600 text-white shadow-lg' 
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
                onClick={() => navigateTo('/admin/students')}
              >
                👥 {t.studentManagement}
              </button>

              {/* Subject Management Dropdown */}
              <div className="relative">
                <button 
                  className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 flex items-center space-x-2 ${
                    isActive('/admin/schedule') || isActive('/admin/subjects')
                      ? 'bg-blue-600 text-white shadow-lg' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  onClick={() => setSubjectMenuOpen(!subjectMenuOpen)}
                >
                  <span>📚 {t.subjectManagement}</span>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {subjectMenuOpen && (
                  <div className="absolute top-full left-0 mt-2 w-64 bg-white rounded-lg shadow-xl border border-gray-200 py-2 z-50">
                    <button onClick={() => navigateTo('/admin/schedule-update')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      📅 {t.updateSchedule}
                    </button>
                    <button onClick={() => navigateTo('/admin/subjects')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      📄 {t.updateSubjects}
                    </button>
                  </div>
                )}
              </div>

              {/* Settings Dropdown */}
              <div className="relative">
                <button 
                  className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 flex items-center space-x-2 ${
                    isActive('/admin/settings')
                      ? 'bg-blue-600 text-white shadow-lg' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  onClick={() => setSettingsMenuOpen(!settingsMenuOpen)}
                >
                  <span>⚙️ {t.settings}</span>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {settingsMenuOpen && (
                  <div className="absolute top-full left-0 mt-2 w-64 bg-white rounded-lg shadow-xl border border-gray-200 py-2 z-50">
                    <button onClick={() => navigateTo('/admin/settings')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      🌐 {t.languageSettings}
                    </button>
                    <button onClick={() => navigateTo('/admin/settings')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      🔐 {t.changePassword}
                    </button>
                  </div>
                )}
              </div>

              {/* Chatbot Support Button */}
              <button 
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                  chatbotOpen 
                    ? 'bg-green-600 text-white shadow-lg' 
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
                onClick={toggleChatbot}
              >
                🤖 {t.chatbotSupport}
              </button>
            </div>

            {/* Logout Button */}
            <button
              onClick={logout}
              className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-all duration-200 font-medium"
            >
              🚪 {t.logout}
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
