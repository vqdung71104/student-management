import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './assets/css/main.css'
import './assets/css/component.css'
import './assets/css/chatbot.css'

interface AppAdminProps {
  onLogout: () => void
}

function AppAdmin({ onLogout }: AppAdminProps) {
  const navigate = useNavigate()
  const [currentPage, setCurrentPage] = useState('dashboard')
  const [chatbotOpen, setChatbotOpen] = useState(false)
  const [studentMenuOpen, setStudentMenuOpen] = useState(false)
  const [subjectMenuOpen, setSubjectMenuOpen] = useState(false)
  const [infoManagementMenuOpen, setInfoManagementMenuOpen] = useState(false)
  const [settingsMenuOpen, setSettingsMenuOpen] = useState(false)
  const [language, setLanguage] = useState('vi')
  const [chatMessages, setChatMessages] = useState([
    {
      type: 'bot',
      content: language === 'vi' 
        ? 'Xin chào Admin! Tôi là trợ lý quản trị hệ thống. Tôi có thể giúp gì cho bạn hôm nay?'
        : 'Hello Admin! I am the system administrator assistant. How can I help you today?'
    },
    {
      type: 'bot',
      content: language === 'vi'
        ? 'Tôi có thể giúp bạn:\n• Quản lý sinh viên và khóa học\n• Xem báo cáo thống kê\n• Cấu hình hệ thống\n• Hỗ trợ kỹ thuật'
        : 'I can help you with:\n• Student and course management\n• View statistical reports\n• System configuration\n• Technical support'
    }
  ])
  const [chatInput, setChatInput] = useState('')

  const texts = {
    vi: {
      dashboard: 'Bảng điều khiển',
      studentManagement: 'Quản lý sinh viên',
      subjectManagement: 'Quản lý môn học',
      infoManagement: 'Quản lý thông tin',
      scholarshipManagement: 'Quản lý học bổng',
      internshipManagement: 'Quản lý thực tập',
      projectManagement: 'Quản lý đồ án',
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
      infoManagement: 'Information Management',
      scholarshipManagement: 'Scholarship Management',
      internshipManagement: 'Internship Management',
      projectManagement: 'Project Management',
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

  const t = texts[language as 'vi' | 'en']

  const showAdminPage = (page: string) => {
    setCurrentPage(page)
    setStudentMenuOpen(false)
    setSubjectMenuOpen(false)
    setInfoManagementMenuOpen(false)
    setSettingsMenuOpen(false)
  }

  const toggleChatbot = () => {
    setChatbotOpen(!chatbotOpen)
  }

  const sendChatMessage = () => {
    if (chatInput.trim()) {
      setChatMessages([...chatMessages, { type: 'user', content: chatInput }])
      setChatInput('')
      // Simulate bot response
      setTimeout(() => {
        setChatMessages(prev => [...prev, { 
          type: 'bot', 
          content: 'Cảm ơn bạn đã gửi tin nhắn. Tôi sẽ phản hồi sớm nhất có thể!' 
        }])
      }, 1000)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      sendChatMessage()
    }
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
                  currentPage === 'dashboard' 
                    ? 'bg-blue-600 text-white shadow-lg' 
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
                onClick={() => showAdminPage('dashboard')}
              >
                   {t.dashboard}
              </button>

              {/* Student Management Dropdown */}
              <div className="relative">
                <button 
                  className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 flex items-center space-x-2 ${
                    currentPage.includes('student') 
                      ? 'bg-blue-600 text-white shadow-lg' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  onClick={() => setStudentMenuOpen(!studentMenuOpen)}
                >
                  <span>👥 {t.studentManagement}</span>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {studentMenuOpen && (
                  <div className="absolute top-full left-0 mt-2 w-64 bg-white rounded-lg shadow-xl border border-gray-200 py-2 z-50">
                    <button onClick={() => showAdminPage('student-create')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                       {t.create}
                    </button>
                    <button onClick={() => showAdminPage('student-update')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                         {t.update}
                    </button>
                    <button onClick={() => showAdminPage('student-delete')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                        {t.delete}
                    </button>
                    <button onClick={() => showAdminPage('student-list')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                         {t.get}
                    </button>
                  </div>
                )}
              </div>

              {/* Subject Management Dropdown */}
              <div className="relative">
                <button 
                  className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 flex items-center space-x-2 ${
                    currentPage.includes('subject') || currentPage.includes('schedule')
                      ? 'bg-blue-600 text-white shadow-lg' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  onClick={() => setSubjectMenuOpen(!subjectMenuOpen)}
                >
                  <span>   {t.subjectManagement}</span>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {subjectMenuOpen && (
                  <div className="absolute top-full left-0 mt-2 w-64 bg-white rounded-lg shadow-xl border border-gray-200 py-2 z-50">
                    <button onClick={() => showAdminPage('schedule-update')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                         {t.updateSchedule}
                    </button>
                    <button onClick={() => showAdminPage('subjects-upload')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                         {t.updateSubjects}
                    </button>
                  </div>
                )}
              </div>

              {/* Information Management Dropdown */}
              <div className="relative">
                <button 
                  className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 flex items-center space-x-2 ${
                    currentPage.includes('scholarship') || currentPage.includes('internship') || currentPage.includes('project')
                      ? 'bg-blue-600 text-white shadow-lg' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  onClick={() => setInfoManagementMenuOpen(!infoManagementMenuOpen)}
                >
                  <span>   {t.infoManagement}</span>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {infoManagementMenuOpen && (
                  <div className="absolute top-full left-0 mt-2 w-64 bg-white rounded-lg shadow-xl border border-gray-200 py-2 z-50">
                    <button 
                      onClick={() => {
                        setInfoManagementMenuOpen(false)
                        navigate('/admin/scholarships')
                      }} 
                      className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left"
                    >
                         {t.scholarshipManagement}
                    </button>
                    <button 
                      onClick={() => {
                        setInfoManagementMenuOpen(false)
                        // TODO: Tạo route cho internship management
                        alert('Đang phát triển...')
                      }} 
                      className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left"
                    >
                         {t.internshipManagement}
                    </button>
                    <button 
                      onClick={() => {
                        setInfoManagementMenuOpen(false)
                        // TODO: Tạo route cho project management
                        alert('Đang phát triển...')
                      }} 
                      className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left"
                    >
                         {t.projectManagement}
                    </button>
                  </div>
                )}
              </div>

              {/* Settings Dropdown */}
              <div className="relative">
                <button 
                  className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 flex items-center space-x-2 ${
                    currentPage.includes('settings') || currentPage.includes('language') || currentPage.includes('password')
                      ? 'bg-blue-600 text-white shadow-lg' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  onClick={() => setSettingsMenuOpen(!settingsMenuOpen)}
                >
                  <span> {t.settings}</span>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {settingsMenuOpen && (
                  <div className="absolute top-full left-0 mt-2 w-64 bg-white rounded-lg shadow-xl border border-gray-200 py-2 z-50">
                    <button onClick={() => showAdminPage('language-settings')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                       {t.languageSettings}
                    </button>
                    <button onClick={() => showAdminPage('change-password')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                       {t.changePassword}
                    </button>
                  </div>
                )}
              </div>

              {/* Chatbot Support Button 
              <button 
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                  chatbotOpen 
                    ? 'bg-green-600 text-white shadow-lg' 
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
                onClick={toggleChatbot}
              >
                 {t.chatbotSupport}
              </button>*/}
            </div>

            {/* Logout Button */}
            <button
              onClick={onLogout}
              className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-all duration-200 font-medium"
            >
                 {t.logout}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-grow container mx-auto px-4 py-6">
        {/* Dashboard Page */}
        <div className={`page ${currentPage === 'dashboard' ? '' : 'hidden'}`}>
          <h2 className="text-2xl font-bold mb-6">Dashboard</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center">
                <div className="p-3 rounded-full bg-blue-100 text-blue-600">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Tổng sinh viên</p>
                  <p className="text-2xl font-semibold text-gray-900">1,234</p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center">
                <div className="p-3 rounded-full bg-green-100 text-green-600">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Tổng khóa học</p>
                  <p className="text-2xl font-semibold text-gray-900">89</p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center">
                <div className="p-3 rounded-full bg-yellow-100 text-yellow-600">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Đăng ký hôm nay</p>
                  <p className="text-2xl font-semibold text-gray-900">156</p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center">
                <div className="p-3 rounded-full bg-purple-100 text-purple-600">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Tỷ lệ hoàn thành</p>
                  <p className="text-2xl font-semibold text-gray-900">87%</p>
                </div>
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold mb-4">Hoạt động gần đây</h3>
              <div className="space-y-3">
                <div className="flex items-start space-x-3 p-3 bg-blue-50 rounded-lg">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                  <div>
                    <p className="text-sm font-medium">Sinh viên mới đăng ký: Nguyễn Văn A</p>
                    <p className="text-xs text-gray-600">2 phút trước</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3 p-3 bg-green-50 rounded-lg">
                  <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                  <div>
                    <p className="text-sm font-medium">Khóa học mới được tạo: Lập trình Web</p>
                    <p className="text-xs text-gray-600">15 phút trước</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3 p-3 bg-yellow-50 rounded-lg">
                  <div className="w-2 h-2 bg-yellow-500 rounded-full mt-2"></div>
                  <div>
                    <p className="text-sm font-medium">Báo cáo thống kê được cập nhật</p>
                    <p className="text-xs text-gray-600">1 giờ trước</p>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold mb-4">Thống kê nhanh</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Sinh viên đăng ký hôm nay</span>
                  <span className="text-sm font-medium">156</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Khóa học đang mở</span>
                  <span className="text-sm font-medium">45</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Giảng viên đang hoạt động</span>
                  <span className="text-sm font-medium">23</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Lớp học đã đầy</span>
                  <span className="text-sm font-medium">12</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Students Management Page */}
        <div className={`page ${currentPage === 'students' ? '' : 'hidden'}`}>
          <h2 className="text-2xl font-bold mb-6">Quản lý sinh viên</h2>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Danh sách sinh viên</h3>
              <button 
                onClick={() => showAdminPage('add-student')}
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition"
              >
                Thêm sinh viên
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">MSSV</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Họ tên</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Trường/Viện</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Trạng thái</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Thao tác</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">2021001</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">Nguyễn Văn A</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">nguyenvana@email.com</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">CNTT</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                        Đang học
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button className="text-blue-600 hover:text-blue-900 mr-2">Sửa</button>
                      <button className="text-red-600 hover:text-red-900">Xóa</button>
                    </td>
                  </tr>
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">2021002</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">Trần Thị B</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">tranthib@email.com</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">CNTT</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                        Đang học
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button className="text-blue-600 hover:text-blue-900 mr-2">Sửa</button>
                      <button className="text-red-600 hover:text-red-900">Xóa</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Add Student Page */}
        <div className={`page ${currentPage === 'add-student' ? '' : 'hidden'}`}>
          <div className="flex items-center mb-6">
            <button 
              onClick={() => showAdminPage('students')}
              className="mr-4 text-blue-600 hover:text-blue-800"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <h2 className="text-2xl font-bold">Thêm sinh viên mới</h2>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <form className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Họ và tên *
                  </label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Nhập họ và tên"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email *
                  </label>
                  <input
                    type="email"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Nhập email"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Số điện thoại
                  </label>
                  <input
                    type="tel"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Nhập số điện thoại"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Khóa học *
                  </label>
                  <select className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" required>
                    <option value="">Chọn khóa học</option>
                    <option value="1">Khóa 2021 - Công nghệ thông tin</option>
                    <option value="2">Khóa 2022 - Công nghệ thông tin</option>
                    <option value="3">Khóa 2023 - Công nghệ thông tin</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Địa chỉ
                  </label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Nhập địa chỉ"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Ngày sinh
                  </label>
                  <input
                    type="date"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              
              <div className="bg-blue-50 p-4 rounded-lg">
                <h3 className="text-sm font-medium text-blue-800 mb-2">   Thông tin đăng nhập tự động</h3>
                <p className="text-sm text-blue-700">
                  Khi tạo sinh viên mới, hệ thống sẽ tự động tạo tài khoản đăng nhập với:
                </p>
                <ul className="text-sm text-blue-700 mt-2 list-disc list-inside">
                  <li><strong>Tên đăng nhập:</strong> Mã sinh viên (được tạo tự động)</li>
                  <li><strong>Mật khẩu mặc định:</strong> 123456</li>
                </ul>
                <p className="text-xs text-blue-600 mt-2">
                     Sinh viên có thể đổi mật khẩu sau khi đăng nhập lần đầu.
                </p>
              </div>

              <div className="flex justify-end space-x-4">
                <button
                  type="button"
                  onClick={() => showAdminPage('students')}
                  className="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition"
                >
                  Tạo sinh viên & Tài khoản
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* Courses Management Page */}
        <div className={`page ${currentPage === 'courses' ? '' : 'hidden'}`}>
          <h2 className="text-2xl font-bold mb-6">Quản lý khóa học</h2>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Danh sách khóa học</h3>
              <button className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition">
                Thêm khóa học
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Mã khóa</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tên khóa học</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Trường/Viện</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Năm bắt đầu</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Thao tác</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">CNTT2021</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">Công nghệ thông tin</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">CNTT</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">2021</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button className="text-blue-600 hover:text-blue-900 mr-2">Sửa</button>
                      <button className="text-red-600 hover:text-red-900">Xóa</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Subjects Management Page */}
        <div className={`page ${currentPage === 'subjects' ? '' : 'hidden'}`}>
          <h2 className="text-2xl font-bold mb-6">Quản lý môn học</h2>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Danh sách môn học</h3>
              <button className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition">
                Thêm môn học
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Mã môn học</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tên môn học</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Số tín chỉ</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Loại</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Thao tác</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">IT4060</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">Trí tuệ nhân tạo</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">3</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Bắt buộc</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button className="text-blue-600 hover:text-blue-900 mr-2">Sửa</button>
                      <button className="text-red-600 hover:text-red-900">Xóa</button>
                    </td>
                  </tr>
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">IT3150</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">Cấu trúc dữ liệu và giải thuật</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">4</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Bắt buộc</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button className="text-blue-600 hover:text-blue-900 mr-2">Sửa</button>
                      <button className="text-red-600 hover:text-red-900">Xóa</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Classes Management Page */}
        <div className={`page ${currentPage === 'classes' ? '' : 'hidden'}`}>
          <h2 className="text-2xl font-bold mb-6">Quản lý lớp học</h2>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Danh sách lớp học</h3>
              <button className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition">
                Thêm lớp học
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Mã lớp</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Môn học</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Giảng viên</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sĩ số</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Thao tác</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">IT4060-01</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">Trí tuệ nhân tạo</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">TS. Nguyễn Văn C</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">45/50</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button className="text-blue-600 hover:text-blue-900 mr-2">Sửa</button>
                      <button className="text-red-600 hover:text-red-900">Xóa</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Reports Page */}
        <div className={`page ${currentPage === 'reports' ? '' : 'hidden'}`}>
          <h2 className="text-2xl font-bold mb-6">Báo cáo</h2>
          <div className="bg-white rounded-lg shadow-md p-6">
            <p className="text-gray-600">Các báo cáo thống kê sẽ được hiển thị ở đây...</p>
          </div>
        </div>

        {/* Settings Page */}
        <div className={`page ${currentPage === 'settings' ? '' : 'hidden'}`}>
          <h2 className="text-2xl font-bold mb-6">Cài đặt hệ thống</h2>
          <div className="bg-white rounded-lg shadow-md p-6">
            <p className="text-gray-600">Cài đặt hệ thống sẽ được hiển thị ở đây...</p>
          </div>
        </div>

        {/* Language Settings Page */}
        <div className={`page ${currentPage === 'language-settings' ? '' : 'hidden'}`}>
          <h2 className="text-2xl font-bold mb-6">{t.languageSettings}</h2>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Chọn ngôn ngữ / Select Language</h3>
              <div className="space-y-2">
                <label className="flex items-center space-x-3">
                  <input
                    type="radio"
                    name="language"
                    value="vi"
                    checked={language === 'vi'}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="form-radio text-blue-600"
                  />
                  <span>🇻🇳 Tiếng Việt</span>
                </label>
                <label className="flex items-center space-x-3">
                  <input
                    type="radio"
                    name="language"
                    value="en"
                    checked={language === 'en'}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="form-radio text-blue-600"
                  />
                  <span>🇺🇸 English</span>
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* Change Password Page */}
        <div className={`page ${currentPage === 'change-password' ? '' : 'hidden'}`}>
          <h2 className="text-2xl font-bold mb-6">{t.changePassword}</h2>
          <div className="bg-white rounded-lg shadow-md p-6">
            <form className="max-w-md space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {language === 'vi' ? 'Mật khẩu hiện tại' : 'Current Password'} *
                </label>
                <input
                  type="password"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder={language === 'vi' ? 'Nhập mật khẩu hiện tại' : 'Enter current password'}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {language === 'vi' ? 'Mật khẩu mới' : 'New Password'} *
                </label>
                <input
                  type="password"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder={language === 'vi' ? 'Nhập mật khẩu mới' : 'Enter new password'}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {language === 'vi' ? 'Xác nhận mật khẩu mới' : 'Confirm New Password'} *
                </label>
                <input
                  type="password"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder={language === 'vi' ? 'Xác nhận mật khẩu mới' : 'Confirm new password'}
                  required
                />
              </div>
              <button
                type="submit"
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition"
              >
                {language === 'vi' ? 'Cập nhật mật khẩu' : 'Update Password'}
              </button>
            </form>
          </div>
        </div>

        {/* Student Create Page */}
        <div className={`page ${currentPage === 'student-create' ? '' : 'hidden'}`}>
          <h2 className="text-2xl font-bold mb-6">{t.create} {language === 'vi' ? 'Sinh viên' : 'Student'}</h2>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <h3 className="text-sm font-medium text-blue-800 mb-2"> {language === 'vi' ? 'Thông báo tài khoản' : 'Account Information'}</h3>
              <p className="text-sm text-blue-700">
                {language === 'vi' 
                  ? 'Tài khoản đăng nhập sẽ được tạo tự động với email sinh viên và mật khẩu mặc định: 123456'
                  : 'Login account will be automatically created with student email and default password: 123456'
                }
              </p>
            </div>
            <form className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {language === 'vi' ? 'Mã sinh viên' : 'Student ID'} *
                  </label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder={language === 'vi' ? 'Nhập mã sinh viên' : 'Enter student ID'}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {language === 'vi' ? 'Họ và tên' : 'Full Name'} *
                  </label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder={language === 'vi' ? 'Nhập họ và tên' : 'Enter full name'}
                    required
                  />
                </div>
              </div>
              <button
                type="submit"
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition"
              >
                {language === 'vi' ? 'Tạo sinh viên và tài khoản' : 'Create Student and Account'}
              </button>
            </form>
          </div>
        </div>

        {/* Student List Page with Filters */}
        <div className={`page ${currentPage === 'student-list' ? '' : 'hidden'}`}>
          <h2 className="text-2xl font-bold mb-6">{language === 'vi' ? 'Danh sách sinh viên' : 'Student List'}</h2>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-4">{language === 'vi' ? 'Bộ lọc' : 'Filters'}</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
                <select className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                  <option value="">{language === 'vi' ? 'Tất cả Trường/Viện' : 'All Departments'}</option>
                  <option>Công nghệ thông tin</option>
                  <option>Kỹ thuật điện</option>
                  <option>Cơ khí</option>
                </select>
                <select className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                  <option value="">{language === 'vi' ? 'Tất cả khóa học' : 'All Courses'}</option>
                  <option>K65</option>
                  <option>K66</option>
                  <option>K67</option>
                </select>
                <input
                  type="text"
                  placeholder={language === 'vi' ? 'Mã sinh viên' : 'Student ID'}
                  className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <input
                  type="text"
                  placeholder={language === 'vi' ? 'Tên sinh viên' : 'Student Name'}
                  className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <select className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                  <option value="">{language === 'vi' ? 'Tất cả lớp' : 'All Classes'}</option>
                  <option>Việt Nhật 01</option>
                  <option>CNTT 01</option>
                  <option>Cơ khí 01</option>
                </select>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse border border-gray-300">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="border border-gray-300 px-4 py-2 text-left">{language === 'vi' ? 'Mã SV' : 'Student ID'}</th>
                    <th className="border border-gray-300 px-4 py-2 text-left">{language === 'vi' ? 'Họ tên' : 'Full Name'}</th>
                    <th className="border border-gray-300 px-4 py-2 text-left">{language === 'vi' ? 'Email' : 'Email'}</th>
                    <th className="border border-gray-300 px-4 py-2 text-left">{language === 'vi' ? 'Lớp' : 'Class'}</th>
                    <th className="border border-gray-300 px-4 py-2 text-left">{language === 'vi' ? 'Thao tác' : 'Actions'}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td className="border border-gray-300 px-4 py-2">SV001</td>
                    <td className="border border-gray-300 px-4 py-2">Nguyễn Văn A</td>
                    <td className="border border-gray-300 px-4 py-2">nguyenvana@email.com</td>
                    <td className="border border-gray-300 px-4 py-2">Việt Nhật 01</td>
                    <td className="border border-gray-300 px-4 py-2">
                      <button className="text-blue-600 hover:text-blue-800 mr-2">{language === 'vi' ? 'Sửa' : 'Edit'}</button>
                      <button className="text-red-600 hover:text-red-800">{language === 'vi' ? 'Xóa' : 'Delete'}</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Schedule Update Page */}
        <div className={`page ${currentPage === 'schedule-update' ? '' : 'hidden'}`}>
          <h2 className="text-2xl font-bold mb-6">{t.updateSchedule}</h2>
          <div className="bg-white rounded-lg shadow-md p-6">
            <p className="text-gray-600">{language === 'vi' ? 'Tính năng cập nhật thời khóa biểu...' : 'Schedule update feature...'}</p>
          </div>
        </div>

        {/* Subjects Upload Page */}
        <div className={`page ${currentPage === 'subjects-upload' ? '' : 'hidden'}`}>
          <h2 className="text-2xl font-bold mb-6">{t.updateSubjects}</h2>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <div className="mt-4">
                <label htmlFor="file-upload" className="cursor-pointer">
                  <span className="mt-2 block text-sm font-medium text-gray-900">
                    {language === 'vi' ? 'Tải lên file Excel danh sách học phần' : 'Upload Excel file with subject list'}
                  </span>
                  <input id="file-upload" name="file-upload" type="file" className="sr-only" accept=".xlsx,.xls" />
                </label>
                <p className="mt-2 text-xs text-gray-500">
                  {language === 'vi' ? 'Chỉ hỗ trợ file .xlsx, .xls' : 'Only .xlsx, .xls files supported'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Scholarship Management Page */}
        <div className={`page ${currentPage === 'scholarship-management' ? '' : 'hidden'}`}>
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-2xl font-bold mb-4">Quản lý học bổng</h2>
            <p className="text-gray-600">Tính năng đang phát triển...</p>
          </div>
        </div>

        {/* Internship Management Page (Placeholder) */}
        <div className={`page ${currentPage === 'internship-management' ? '' : 'hidden'}`}>
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-2xl font-bold mb-4">Quản lý thực tập</h2>
            <p className="text-gray-600">Tính năng đang phát triển...</p>
          </div>
        </div>

        {/* Project Management Page (Placeholder) */}
        <div className={`page ${currentPage === 'project-management' ? '' : 'hidden'}`}>
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-2xl font-bold mb-4">Quản lý đồ án</h2>
            <p className="text-gray-600">Tính năng đang phát triển...</p>
          </div>
        </div>
      </main>

      {/* Chatbot */}
      <div className={`fixed bottom-0 right-6 w-80 bg-white rounded-t-xl shadow-lg transition-all duration-300 transform z-50 ${chatbotOpen ? 'translate-y-0' : 'translate-y-full'}`}>
        <div className="gradient-bg rounded-t-xl p-4 cursor-pointer" onClick={toggleChatbot}>
          <div className="flex justify-between items-center text-white">
            <div className="flex items-center space-x-2">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
              <h3 className="font-medium">Trợ lý quản trị</h3>
            </div>
            <button>
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          </div>
        </div>
        <div className="p-4">
          <div className="chatbot-container mb-4 max-h-64 overflow-y-auto">
            {chatMessages.map((message, index) => (
              <div key={index} className={`mb-3 p-3 ${message.type === 'user' ? 'user-message ml-auto max-w-[80%]' : 'bot-message'}`}>
                <p className="text-sm whitespace-pre-line">{message.content}</p>
              </div>
            ))}
          </div>
          <div className="flex">
            <input 
              type="text" 
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Nhập tin nhắn..." 
              className="flex-grow border border-gray-300 rounded-l-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button 
              className="bg-blue-600 text-white px-4 py-2 rounded-r-md hover:bg-blue-700 transition" 
              onClick={sendChatMessage}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-gray-800 text-white py-6">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <h3 className="text-lg font-semibold mb-3">Hệ thống quản lý học tập</h3>
              <p className="text-sm text-gray-400">Cung cấp giải pháp quản lý học tập toàn diện cho nhà trường.</p>
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-3">Liên hệ</h3>
              <div className="text-sm text-gray-400 space-y-2">
                <p>Email: admin@university.edu.vn</p>
                <p>Điện thoại: (024) 3869 2345</p>
                <p>Địa chỉ: Số 1 Đại Cồ Việt, Hai Bà Trưng, Hà Nội</p>
              </div>
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-3">Hỗ trợ</h3>
              <ul className="text-sm text-gray-400 space-y-2">
                <li><a href="#" className="hover:text-white transition">Hướng dẫn sử dụng</a></li>
                <li><a href="#" className="hover:text-white transition">Báo cáo lỗi</a></li>
                <li><a href="#" className="hover:text-white transition">Cập nhật hệ thống</a></li>
              </ul>
            </div>
          </div>
          <div className="mt-6 pt-4 border-t border-gray-700 text-center text-sm text-gray-400">
            <p>© 2023 Hệ thống quản lý học tập. Bản quyền thuộc về Trường Đại học.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default AppAdmin
