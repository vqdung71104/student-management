import { useState } from 'react'
import './assets/css/main.css'
import './assets/css/component.css'
import './assets/css/chatbot.css'

interface AppAdminProps {
  onLogout: () => void
}

function AppAdmin({ onLogout }: AppAdminProps) {
  const [currentPage, setCurrentPage] = useState('dashboard')
  const [chatbotOpen, setChatbotOpen] = useState(false)
  const [chatMessages, setChatMessages] = useState([
    {
      type: 'bot',
      content: 'Xin chào Admin! Tôi là trợ lý quản trị hệ thống. Tôi có thể giúp gì cho bạn hôm nay?'
    },
    {
      type: 'bot',
      content: 'Tôi có thể giúp bạn:\n• Quản lý sinh viên và khóa học\n• Xem báo cáo thống kê\n• Cấu hình hệ thống\n• Hỗ trợ kỹ thuật'
    }
  ])
  const [chatInput, setChatInput] = useState('')

  const showAdminPage = (page: string) => {
    setCurrentPage(page)
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
      <header className="gradient-bg text-white shadow-lg">
        <div className="container mx-auto px-4 py-3 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            <h1 className="text-xl font-bold">ADMIN PORTAL</h1>
          </div>
          <div className="hidden md:flex items-center space-x-6">
            <button 
              className={`hover:text-blue-200 transition ${currentPage === 'dashboard' ? 'text-blue-200' : ''}`}
              onClick={() => showAdminPage('dashboard')}
            >
              Dashboard
            </button>
            <button 
              className={`hover:text-blue-200 transition ${currentPage === 'students' ? 'text-blue-200' : ''}`}
              onClick={() => showAdminPage('students')}
            >
              Quản lý sinh viên
            </button>
            <button 
              className={`hover:text-blue-200 transition ${currentPage === 'courses' ? 'text-blue-200' : ''}`}
              onClick={() => showAdminPage('courses')}
            >
              Quản lý khóa học
            </button>
            <button 
              className={`hover:text-blue-200 transition ${currentPage === 'reports' ? 'text-blue-200' : ''}`}
              onClick={() => showAdminPage('reports')}
            >
              Báo cáo
            </button>
            <button 
              className={`hover:text-blue-200 transition ${currentPage === 'settings' ? 'text-blue-200' : ''}`}
              onClick={() => showAdminPage('settings')}
            >
              Cài đặt
            </button>
          </div>
          <div className="flex items-center space-x-4">
            <button className="relative" onClick={toggleChatbot}>
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
              <span className="absolute -top-1 -right-1 bg-red-500 text-xs rounded-full h-4 w-4 flex items-center justify-center">2</span>
            </button>
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-full bg-red-200 flex items-center justify-center text-red-800 font-bold">
                A
              </div>
              <span className="hidden md:inline">Admin</span>
              <button 
                onClick={onLogout}
                className="ml-2 px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-sm transition"
              >
                Đăng xuất
              </button>
            </div>
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
              <button className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition">
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
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Khoa</th>
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
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Mã khóa học</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tên khóa học</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Số tín chỉ</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Giảng viên</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Trạng thái</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Thao tác</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">IT4060</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">Trí tuệ nhân tạo</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">3</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">TS. Nguyễn Văn C</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                        Đang mở
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button className="text-blue-600 hover:text-blue-900 mr-2">Sửa</button>
                      <button className="text-red-600 hover:text-red-900">Xóa</button>
                    </td>
                  </tr>
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">IT3150</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">Cấu trúc dữ liệu và giải thuật</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">4</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">TS. Trần Thị D</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                        Đang mở
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
