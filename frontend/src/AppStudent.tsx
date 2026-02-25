import { useState, useEffect } from 'react'
import { UserGuide, FAQ, Feedback } from './components/SupportPages'
import './assets/css/main.css'
import './assets/css/component.css'
import './assets/css/chatbot.css'
import { Menu, Dropdown } from 'antd'
import { DownOutlined } from '@ant-design/icons'

// Define interfaces for type safety
interface Student {
  id: number
  student_name: string
  email: string
  course_id: number
  department_id: number
  cpa?: number
  credits_accumulated?: number
  credits_registered?: number
  credits_passed?: number
}

interface Course {
  id: number
  course_name: string
  course_id: string
  department_id: number
  total_credits: number
}

interface ScheduleItem {
  id: number
  class_id: number
  student_id: number  // This is integer ID now
  registration_date: string
}

interface GradesData {
  id: number
  student_id: number  // This is integer ID now
  subject_id: string
  semester: string
  letter_grade: string
  subject_name: string
  credits: number
}

interface ChatMessage {
  type: 'user' | 'bot'
  content: string
}

interface Notification {
  id: number
  title: string
  content: string
  isRead: boolean
  time: string
}

interface AppStudentProps {
  onLogout: () => void
  studentInfo?: {
    id: number
    role: string
  }
}

function AppStudent({ onLogout, studentInfo }: AppStudentProps) {
  const [currentPage, setCurrentPage] = useState('home')
  const [chatbotOpen, setChatbotOpen] = useState(false)
  const [studentData, setStudentData] = useState<Student | null>(null)
  const [scheduleData, setScheduleData] = useState<ScheduleItem[]>([])
  const [_gradesData, setGradesData] = useState<GradesData[] | null>(null)
  const [courseData, setCourseData] = useState<Course | null>(null)
  const [notifications, setNotifications] = useState<Notification[]>([
    { id: 1, title: 'Thông báo đăng ký học kỳ 2024.1', content: 'Thời gian đăng ký từ 15/01 đến 30/01/2024', isRead: false, time: '2 giờ trước' },
    { id: 2, title: 'Kết quả học tập kỳ 2023.2', content: 'Kết quả đã được cập nhật', isRead: true, time: '1 ngày trước' },
    { id: 3, title: 'Học bổng khuyến khích học tập', content: 'Mở đăng ký học bổng cho sinh viên xuất sắc', isRead: false, time: '3 ngày trước' }
  ])
  const [notificationOpen, setNotificationOpen] = useState(false)
  const [_studyMenuOpen, setStudyMenuOpen] = useState(false)
  const [projectMenuOpen, setProjectMenuOpen] = useState(false)
  const [_formMenuOpen, setFormMenuOpen] = useState(false)
  const [scholarshipMenuOpen, setScholarshipMenuOpen] = useState(false)
  const [integratedStudyMenuOpen, setIntegratedStudyMenuOpen] = useState(false)
  const [_researchMenuOpen, setResearchMenuOpen] = useState(false)
  const [_exchangeMenuOpen, setExchangeMenuOpen] = useState(false)
  const [supportMenuOpen, setSupportMenuOpen] = useState(false)
  const [registrationMenuOpen, setRegistrationMenuOpen] = useState(false)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      type: 'bot',
      content: 'Xin chào! Tôi là trợ lý ảo của hệ thống. Tôi có thể giúp gì cho bạn hôm nay?'
    },
    {
      type: 'bot',
      content: 'Tôi có thể hỗ trợ bạn:\n• Hướng dẫn sử dụng hệ thống\n• Tra cứu thông tin học tập\n• Giải đáp thắc mắc về quy định\n• Hỗ trợ kỹ thuật'
    }
  ])
  const [chatInput, setChatInput] = useState('')

  const unreadCount = notifications.filter(n => !n.isRead).length

  const toggleChatbot = () => {
    setChatbotOpen(!chatbotOpen)
  }

  // Fetch student data when component mounts
  useEffect(() => {
    if (studentInfo?.id) {
      fetchStudentData()
      fetchScheduleData()
    }
  }, [studentInfo])

  useEffect(() => {
    if (studentData?.id) {
      fetchGradesData()
    }
  }, [studentData])

  useEffect(() => {
    if (studentData?.course_id) {
      fetchCourseData()
    }
  }, [studentData])

  const fetchStudentData = async () => {
    try {
      if (studentInfo?.id) {
        const response = await fetch(`http://localhost:8000/students/${studentInfo.id}`)
        if (response.ok) {
          const student: Student = await response.json()
          setStudentData(student)
        }
      }
    } catch (error) {
      console.error('Error fetching student data:', error)
    }
  }

  const fetchScheduleData = async () => {
    try {
      if (studentInfo?.id) {
        const response = await fetch(`http://localhost:8000/class-registers/student/${studentInfo.id}`)
        if (response.ok) {
          const data: ScheduleItem[] = await response.json()
          setScheduleData(data)
        }
      }
    } catch (error) {
      console.error('Error fetching schedule data:', error)
      setScheduleData([])
    }
  }

  const fetchGradesData = async () => {
    try {
      if (studentData?.id) {
        const response = await fetch(`http://localhost:8000/learned-subjects/student/${studentData.id}`)
        if (response.ok) {
          const data: GradesData[] = await response.json()
          setGradesData(data)
        }
      }
    } catch (error) {
      console.error('Error fetching grades data:', error)
      setGradesData([])
    }
  }

  const fetchCourseData = async () => {
    try {
      if (studentData?.course_id) {
        const response = await fetch(`http://localhost:8000/courses/${studentData.course_id}`)
        if (response.ok) {
          const data: Course = await response.json()
          setCourseData(data)
        }
      }
    } catch (error) {
      console.error('Error fetching course data:', error)
    }
  }

  const sendChatMessage = () => {
    if (chatInput.trim()) {
      const newMessage: ChatMessage = { type: 'user', content: chatInput }
      setChatMessages([...chatMessages, newMessage])
      setChatInput('')
      // Simulate bot response
      setTimeout(() => {
        const botMessage: ChatMessage = {
          type: 'bot',
          content: 'Cảm ơn bạn đã gửi tin nhắn. Tôi sẽ phản hồi sớm nhất có thể!'
        }
        setChatMessages(prev => [...prev, botMessage])
      }, 1000)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      sendChatMessage()
    }
  }

  const showStudentPage = (page: string) => {
    setCurrentPage(page)
    setStudyMenuOpen(false)
    setProjectMenuOpen(false)
    setFormMenuOpen(false)
    setScholarshipMenuOpen(false)
    setIntegratedStudyMenuOpen(false)
    setResearchMenuOpen(false)
    setExchangeMenuOpen(false)
    setSupportMenuOpen(false)
    setRegistrationMenuOpen(false)
    setNotificationOpen(false)
  }

  const markAsRead = (id: number) => {
    setNotifications(notifications.map(n =>
      n.id === id ? { ...n, isRead: true } : n
    ))
  }

  const markAllAsRead = () => {
    setNotifications(notifications.map(n => ({ ...n, isRead: true })))
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-lg border-b border-gray-200">
        <div className="container mx-auto px-4 py-3">
          <div className="flex justify-between items-center">
            {/* Logo và Title */}
            <button
              onClick={() => window.location.href = 'http://localhost:5173/student'}
              className="flex items-center space-x-3 hover:opacity-80 transition-opacity duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-lg"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              <h1 className="text-xl font-bold text-gray-800">STUDENT PORTAL</h1>
            </button>

            {/* Navigation Menu */}
            <div className="hidden md:flex items-center space-x-2">
              {/* Học tập */}
              <Dropdown
                trigger={['click']}
                overlay={
                  <Menu className="section-nav-item">
                    <Menu.Item
                      key="schedule"
                      onClick={() => showStudentPage('schedule')}
                      className={currentPage.includes('schedule') ? 'bg-blue-50 font-semibold' : ''}
                    >
                      Thời khóa biểu
                    </Menu.Item>
                    <Menu.Item
                      key="grades"
                      onClick={() => showStudentPage('grades')}
                      className={currentPage.includes('grades') ? 'bg-blue-50 font-semibold' : ''}
                    >
                      Xem điểm
                    </Menu.Item>
                    <Menu.Item
                      key="curriculum"
                      onClick={() => showStudentPage('curriculum')}
                      className={currentPage.includes('curriculum') ? 'bg-blue-50 font-semibold' : ''}
                    >
                      Chương trình đào tạo
                    </Menu.Item>
                  </Menu>
                }
              >
                <button
                  className={`ant-dropdown-trigger section-nav-item px-4 py-2 rounded-lg font-medium transition-all duration-200 flex items-center space-x-2 ${currentPage.includes('study') ||
                      currentPage.includes('schedule') ||
                      currentPage.includes('grades') ||
                      currentPage.includes('curriculum')
                      ? 'bg-blue-600 text-white shadow-lg'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                >
                  <span> Học tập</span>
                  <span className="span-icon-narrow">
                    <DownOutlined />
                  </span>
                </button>
              </Dropdown>

              {/* Đăng ký học tập */}
              <div className="relative">
                <button
                  className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 flex items-center space-x-2 ${currentPage.includes('registration')
                      ? 'bg-blue-600 text-white shadow-lg'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  onClick={() => setRegistrationMenuOpen(!registrationMenuOpen)}
                >
                  <span> Đăng ký học tập</span>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {registrationMenuOpen && (
                  <div className="absolute top-full left-0 mt-2 w-64 bg-white rounded-lg shadow-xl border border-gray-200 py-2 z-50">
                    <button onClick={() => window.location.href = '/student/subject-registration'} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      Đăng ký học phần
                    </button>
                    <button onClick={() => window.location.href = '/student/class-registration'} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      Đăng ký lớp
                    </button>
                  </div>
                )}
              </div>

              {/* Đồ án */}
              <div className="relative">
                <button
                  className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 flex items-center space-x-2 ${currentPage.includes('project')
                      ? 'bg-blue-600 text-white shadow-lg'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  onClick={() => setProjectMenuOpen(!projectMenuOpen)}
                >
                  <span> Đồ án</span>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {projectMenuOpen && (
                  <div className="absolute top-full left-0 mt-2 w-64 bg-white rounded-lg shadow-xl border border-gray-200 py-2 z-50">
                    <button onClick={() => showStudentPage('project-list')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      Danh sách đồ án
                    </button>
                    <button onClick={() => showStudentPage('project-register')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      Đăng ký nguyện vọng
                    </button>
                    <button onClick={() => showStudentPage('project-guidance')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      Định hướng đề tài
                    </button>
                    <button onClick={() => showStudentPage('company-list')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      DS Doanh nghiệp
                    </button>
                    <button onClick={() => showStudentPage('plagiarism-check')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      Kiểm tra trùng lặp
                    </button>
                  </div>
                )}
              </div>

              {/* Biểu mẫu */}
              <button
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${currentPage.includes('form')
                    ? 'bg-blue-600 text-white shadow-lg'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                onClick={() => showStudentPage('forms')}
              >
                Biểu mẫu
              </button>

              {/* Học bổng */}
              <div className="relative">
                <button
                  className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 flex items-center space-x-2 ${currentPage.includes('scholarship')
                      ? 'bg-blue-600 text-white shadow-lg'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  onClick={() => setScholarshipMenuOpen(!scholarshipMenuOpen)}
                >
                  <span>💰 Học bổng</span>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {scholarshipMenuOpen && (
                  <div className="absolute top-full left-0 mt-2 w-64 bg-white rounded-lg shadow-xl border border-gray-200 py-2 z-50">
                    <button onClick={() => showStudentPage('scholarship-register')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      Đăng ký học bổng
                    </button>
                    <button onClick={() => showStudentPage('scholarship-criteria')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      Điều kiện xét học bổng
                    </button>
                  </div>
                )}
              </div>

              {/* Học tích hợp */}
              <div className="relative">
                <button
                  className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 flex items-center space-x-2 ${currentPage.includes('integrated')
                      ? 'bg-blue-600 text-white shadow-lg'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  onClick={() => setIntegratedStudyMenuOpen(!integratedStudyMenuOpen)}
                >
                  <span> Học tích hợp</span>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {integratedStudyMenuOpen && (
                  <div className="absolute top-full left-0 mt-2 w-64 bg-white rounded-lg shadow-xl border border-gray-200 py-2 z-50">
                    <button onClick={() => showStudentPage('engineer-advanced')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      Kỹ sư chuyên sâu
                    </button>
                    <button onClick={() => showStudentPage('master-degree')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      Thạc sỹ
                    </button>
                  </div>
                )}
              </div>

              {/* NCKH */}
              <button
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${currentPage.includes('research')
                    ? 'bg-blue-600 text-white shadow-lg'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                onClick={() => showStudentPage('research')}
              >
                NCKH
              </button>

              {/* CT Trao đổi */}
              <button
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${currentPage.includes('exchange')
                    ? 'bg-blue-600 text-white shadow-lg'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                onClick={() => showStudentPage('exchange')}
              >
                CT Trao đổi
              </button>

              {/* Hỗ trợ */}
              <div className="relative">
                <button
                  className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 flex items-center space-x-2 ${currentPage.includes('support')
                      ? 'bg-blue-600 text-white shadow-lg'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  onClick={() => setSupportMenuOpen(!supportMenuOpen)}
                >
                  <span> Hỗ trợ</span>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {supportMenuOpen && (
                  <div className="absolute top-full left-0 mt-2 w-64 bg-white rounded-lg shadow-xl border border-gray-200 py-2 z-50">
                    <button onClick={() => showStudentPage('user-guide')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      Hướng dẫn sử dụng
                    </button>
                    <button onClick={() => showStudentPage('faq')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      Những câu hỏi thường gặp
                    </button>
                    <button onClick={() => showStudentPage('feedback')} className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 text-left">
                      Phản hồi và góp ý
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Right side - Notification và Logout */}
            <div className="flex items-center space-x-4">
              {/* Notification Bell */}
              <div className="relative">
                <button
                  className="relative p-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition-all duration-200"
                  onClick={() => setNotificationOpen(!notificationOpen)}
                >
                  <svg className="w-6 h-6 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                  </svg>
                  {unreadCount > 0 && (
                    <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                      {unreadCount}
                    </span>
                  )}
                </button>

                {/* Notification Dropdown */}
                {notificationOpen && (
                  <div className="absolute top-full right-0 mt-2 w-80 bg-white rounded-lg shadow-xl border border-gray-200 z-50 max-h-96 overflow-y-auto">
                    <div className="p-4 border-b border-gray-200 flex justify-between items-center">
                      <h3 className="font-semibold text-gray-800">Thông báo</h3>
                      {unreadCount > 0 && (
                        <button
                          onClick={markAllAsRead}
                          className="text-blue-600 text-xs hover:text-blue-800"
                        >
                          Đánh dấu tất cả đã đọc
                        </button>
                      )}
                    </div>
                    <div className="max-h-64 overflow-y-auto">
                      {notifications.map(notification => (
                        <div
                          key={notification.id}
                          className={`p-4 border-b border-gray-100 hover:bg-gray-50 cursor-pointer ${!notification.isRead ? 'bg-blue-50' : ''
                            }`}
                          onClick={() => markAsRead(notification.id)}
                        >
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <h4 className={`text-sm font-medium ${!notification.isRead ? 'text-blue-800' : 'text-gray-800'}`}>
                                {notification.title}
                              </h4>
                              <p className="text-xs text-gray-600 mt-1">{notification.content}</p>
                              <p className="text-xs text-gray-400 mt-2">{notification.time}</p>
                            </div>
                            {!notification.isRead && (
                              <div className="w-2 h-2 bg-red-500 rounded-full ml-2 mt-1"></div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Logout Button */}
              <button
                onClick={onLogout}
                className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-all duration-200 font-medium"
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
                  <p className="text-2xl font-semibold text-gray-900">
                    {courseData?.total_credits || 120}
                  </p>
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
                  <p className="text-2xl font-semibold text-gray-900">{scheduleData.length}</p>
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

        {/* User Guide Page */}
        <div className={`page ${currentPage === 'user-guide' ? '' : 'hidden'}`}>
          <UserGuide />
        </div>

        {/* FAQ Page */}
        <div className={`page ${currentPage === 'faq' ? '' : 'hidden'}`}>
          <FAQ />
        </div>

        {/* Feedback Page */}
        <div className={`page ${currentPage === 'feedback' ? '' : 'hidden'}`}>
          <Feedback />
        </div>

        {/* Các trang khác sẽ được render ở đây dựa trên currentPage */}
        {/* Thêm các trang khác tương tự... */}
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