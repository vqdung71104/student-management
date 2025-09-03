import { useState } from 'react'
import './assets/css/main.css'
import './assets/css/component.css'
import './assets/css/chatbot.css'
import AppAdmin from './AppAdmin'
import AppStudent from './AppStudent'

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [userRole, setUserRole] = useState<'admin' | 'student' | null>(null)
  const [loginForm, setLoginForm] = useState({
    username: '',
    password: ''
  })

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault()
    
    // Simulate login logic - in real app, this would be an API call
    if (loginForm.username === 'admin' && loginForm.password === 'admin123') {
      setUserRole('admin')
      setIsLoggedIn(true)
    } else if (loginForm.username === 'student' && loginForm.password === 'student123') {
      setUserRole('student')
      setIsLoggedIn(true)
    } else {
      alert('Thông tin đăng nhập không chính xác!')
    }
  }

  const handleLogout = () => {
    setIsLoggedIn(false)
    setUserRole(null)
    setLoginForm({ username: '', password: '' })
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setLoginForm({
      ...loginForm,
      [e.target.name]: e.target.value
    })
  }

  // If logged in, render appropriate component based on role
  if (isLoggedIn) {
    if (userRole === 'admin') {
      return <AppAdmin onLogout={handleLogout} />
    } else if (userRole === 'student') {
      return <AppStudent onLogout={handleLogout} />
    }
  }

  // Login page
  return (
    <div className="min-h-screen gradient-bg flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">STUDENT PORTAL</h1>
          <p className="text-gray-600">Hệ thống quản lý học tập</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
              Tên đăng nhập
            </label>
            <input
              type="text"
              id="username"
              name="username"
              value={loginForm.username}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Nhập tên đăng nhập"
              required
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
              Mật khẩu
            </label>
            <input
              type="password"
              id="password"
              name="password"
              value={loginForm.password}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Nhập mật khẩu"
              required
            />
          </div>

          <button
            type="submit"
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition duration-200"
          >
            Đăng nhập
          </button>
        </form>

        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <h3 className="text-sm font-medium text-blue-800 mb-2">Tài khoản demo:</h3>
          <div className="text-xs text-blue-700 space-y-1">
            <p><strong>Admin:</strong> username: admin, password: admin123</p>
            <p><strong>Student:</strong> username: student, password: student123</p>
          </div>
        </div>

        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600">
            © 2023 Hệ thống đăng ký học tập. Bản quyền thuộc về Trường Đại học.
          </p>
        </div>
      </div>
    </div>
  )
}

export default App
