import { useState } from 'react'
import './assets/css/main.css'
import './assets/css/component.css'
import './assets/css/chatbot.css'

interface AppStudentProps {
  onLogout: () => void
}

function AppStudent({ onLogout }: AppStudentProps) {
  const [currentPage, setCurrentPage] = useState('home')
  const [chatbotOpen, setChatbotOpen] = useState(false)
  const [chatMessages, setChatMessages] = useState([
    {
      type: 'bot',
      content: 'Xin chào Nguyễn Thành! Tôi là trợ lý học tập của bạn. Tôi có thể giúp gì cho bạn hôm nay?'
    },
    {
      type: 'bot',
      content: 'Tôi có thể giúp bạn:\n• Tư vấn về các học phần phù hợp\n• Giải đáp thắc mắc về đăng ký học phần\n• Thông tin về giảng viên và lớp học\n• Gợi ý lịch học tối ưu'
    },
    {
      type: 'user',
      content: 'Tôi muốn đăng ký học phần Trí tuệ nhân tạo. Tôi có đủ điều kiện không?'
    },
    {
      type: 'bot',
      content: 'Dựa trên kết quả học tập của bạn, bạn đã hoàn thành các môn tiên quyết cho học phần Trí tuệ nhân tạo (IT4060), bao gồm:\n• Cấu trúc dữ liệu và giải thuật (IT3150) - Điểm B+\n• Xác suất thống kê (MI1110) - Điểm A\n\nBạn hoàn toàn đủ điều kiện đăng ký học phần này. Học phần này có 2 lớp, bạn có muốn xem thông tin chi tiết không?'
    }
  ])
  const [chatInput, setChatInput] = useState('')

  const showStudentPage = (page: string) => {
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
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            <h1 className="text-xl font-bold">STUDENT PORTAL</h1>
          </div>
          <div className="hidden md:flex items-center space-x-6">
            <button 
              className={`hover:text-blue-200 transition ${currentPage === 'home' ? 'text-blue-200' : ''}`}
              onClick={() => showStudentPage('home')}
            >
              Trang chủ
            </button>
            <button 
              className={`hover:text-blue-200 transition ${currentPage === 'registration' ? 'text-blue-200' : ''}`}
              onClick={() => showStudentPage('registration')}
            >
              Đăng ký học phần
            </button>
            <button 
              className={`hover:text-blue-200 transition ${currentPage === 'profile' ? 'text-blue-200' : ''}`}
              onClick={() => showStudentPage('profile')}
            >
              Thông tin cá nhân
            </button>
            <button 
              className={`hover:text-blue-200 transition ${currentPage === 'schedule' ? 'text-blue-200' : ''}`}
              onClick={() => showStudentPage('schedule')}
            >
              Thời khóa biểu
            </button>
          </div>
          <div className="flex items-center space-x-4">
            <button className="relative" onClick={toggleChatbot}>
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
              <span className="absolute -top-1 -right-1 bg-red-500 text-xs rounded-full h-4 w-4 flex items-center justify-center">1</span>
            </button>
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-full bg-blue-200 flex items-center justify-center text-blue-800 font-bold">
                NT
              </div>
              <span className="hidden md:inline">Nguyễn Thành</span>
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
        {/* Home Page */}
        <div className={`page ${currentPage === 'home' ? '' : 'hidden'}`}>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center">
                <div className="p-3 rounded-full bg-blue-100 text-blue-600">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Tổng số tín chỉ</p>
                  <p className="text-2xl font-semibold text-gray-900">120</p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center">
                <div className="p-3 rounded-full bg-green-100 text-green-600">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Điểm TB tích lũy</p>
                  <p className="text-2xl font-semibold text-gray-900">3.45</p>
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
                  <p className="text-sm font-medium text-gray-600">Học kỳ hiện tại</p>
                  <p className="text-2xl font-semibold text-gray-900">2024.1</p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center">
                <div className="p-3 rounded-full bg-purple-100 text-purple-600">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Lớp học đã đăng ký</p>
                  <p className="text-2xl font-semibold text-gray-900">5</p>
                </div>
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold mb-4">Thông báo mới</h3>
              <div className="space-y-3">
                <div className="flex items-start space-x-3 p-3 bg-blue-50 rounded-lg">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                  <div>
                    <p className="text-sm font-medium">Đăng ký học phần học kỳ 2024.1</p>
                    <p className="text-xs text-gray-600">Thời gian đăng ký: 15/01/2024 - 30/01/2024</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3 p-3 bg-yellow-50 rounded-lg">
                  <div className="w-2 h-2 bg-yellow-500 rounded-full mt-2"></div>
                  <div>
                    <p className="text-sm font-medium">Lịch thi cuối kỳ</p>
                    <p className="text-xs text-gray-600">Xem lịch thi tại trang thông báo</p>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold mb-4">Lịch học hôm nay</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="text-sm font-medium">Cơ sở dữ liệu</p>
                    <p className="text-xs text-gray-600">Phòng A101 - 08:00 - 11:00</p>
                  </div>
                  <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">Đang diễn ra</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="text-sm font-medium">Lập trình Web</p>
                    <p className="text-xs text-gray-600">Phòng B203 - 14:00 - 17:00</p>
                  </div>
                  <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">Sắp tới</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Registration Page */}
        <div className={`page ${currentPage === 'registration' ? '' : 'hidden'}`}>
          <h2 className="text-2xl font-bold mb-6">Đăng ký học phần</h2>
          <div className="bg-white rounded-lg shadow-md p-6">
            <p className="text-gray-600">Nội dung đăng ký học phần sẽ được hiển thị ở đây...</p>
          </div>
        </div>

        {/* Profile Page */}
        <div className={`page ${currentPage === 'profile' ? '' : 'hidden'}`}>
          <h2 className="text-2xl font-bold mb-6">Thông tin cá nhân</h2>
          <div className="bg-white rounded-lg shadow-md p-6">
            <p className="text-gray-600">Thông tin cá nhân sẽ được hiển thị ở đây...</p>
          </div>
        </div>

        {/* Schedule Page */}
        <div className={`page ${currentPage === 'schedule' ? '' : 'hidden'}`}>
          <h2 className="text-2xl font-bold mb-6">Thời khóa biểu</h2>
          <div className="bg-white rounded-lg shadow-md p-6">
            <p className="text-gray-600">Thời khóa biểu sẽ được hiển thị ở đây...</p>
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
              <h3 className="font-medium">Trợ lý học tập</h3>
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
              <h3 className="text-lg font-semibold mb-3">Hệ thống đăng ký học tập</h3>
              <p className="text-sm text-gray-400">Cung cấp giải pháp đăng ký học tập thông minh và tiện lợi cho sinh viên.</p>
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-3">Liên hệ</h3>
              <div className="text-sm text-gray-400 space-y-2">
                <p>Email: support@university.edu.vn</p>
                <p>Điện thoại: (024) 3869 2345</p>
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

export default AppStudent
