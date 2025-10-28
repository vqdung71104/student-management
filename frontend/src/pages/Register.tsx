import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useNavigate, Link } from 'react-router-dom'

interface Course {
  id: number
  course_id: string
  course_name: string
}

interface Department {
  id: string
  department_name: string
}

const Register = () => {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [registerForm, setRegisterForm] = useState({
    student_name: '',
    email: '',
    password: '',
    confirmPassword: '',
    course_id: '',
    department_id: ''
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [courses, setCourses] = useState<Course[]>([])
  const [departments, setDepartments] = useState<Department[]>([])

  // Fetch courses and departments
  useEffect(() => {
    fetchCourses()
    fetchDepartments()
  }, [])

  const fetchCourses = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/courses/')
      if (response.ok) {
        const data = await response.json()
        setCourses(data)
      }
    } catch (error) {
      console.error('Error fetching courses:', error)
    }
  }

  const fetchDepartments = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/departments/')
      if (response.ok) {
        const data = await response.json()
        setDepartments(data)
      }
    } catch (error) {
      console.error('Error fetching departments:', error)
    }
  }

  const validateForm = () => {
    if (!registerForm.student_name.trim()) {
      setError('Vui lòng nhập họ tên')
      return false
    }
    
    if (!registerForm.email.trim()) {
      setError('Vui lòng nhập email')
      return false
    }
    
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(registerForm.email)) {
      setError('Email không hợp lệ')
      return false
    }
    
    if (registerForm.password.length < 6) {
      setError('Mật khẩu phải có ít nhất 6 ký tự')
      return false
    }
    
    if (registerForm.password !== registerForm.confirmPassword) {
      setError('Mật khẩu xác nhận không khớp')
      return false
    }
    
    if (!registerForm.department_id) {
      setError('Vui lòng chọn Khoa/Viện')
      return false
    }
    
    if (!registerForm.course_id) {
      setError('Vui lòng chọn ngành học')
      return false
    }
    
    return true
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    
    if (!validateForm()) {
      return
    }
    
    setLoading(true)
    
    try {
      const result = await register(
        registerForm.student_name,
        registerForm.email,
        registerForm.password,
        parseInt(registerForm.course_id),
        registerForm.department_id
      )
      
      if (result.success) {
        // Auto redirect to student dashboard after successful registration
        navigate('/student')
      } else {
        setError(result.message)
      }
    } catch (error) {
      console.error('Registration error:', error)
      setError('Đăng ký thất bại. Vui lòng thử lại.')
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    
    setRegisterForm({
      ...registerForm,
      [name]: value
    })
    
    // Reset course selection when department changes
    if (name === 'department_id') {
      setRegisterForm(prev => ({
        ...prev,
        department_id: value,
        course_id: '' // Reset course when department changes
      }))
    }
    
    // Clear error when user starts typing
    if (error) {
      setError('')
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-900 via-green-700 to-green-500 flex items-center justify-center py-8">
      <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md mx-4">
        <div className="text-center mb-6">
          <div className="flex justify-center mb-3">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-14 w-14 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-1">ĐĂNG KÝ TÀI KHOẢN</h1>
          <p className="text-gray-600 text-sm">Hệ thống quản lý học tập</p>
        </div>

        <form onSubmit={handleRegister} className="space-y-4">
          <div>
            <label htmlFor="student_name" className="block text-sm font-medium text-gray-700 mb-1">
              Họ và tên <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="student_name"
              name="student_name"
              value={registerForm.student_name}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
              placeholder="Nguyễn Văn A"
              required
            />
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Email <span className="text-red-500">*</span>
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={registerForm.email}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
              placeholder="example@email.com"
              required
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              Mật khẩu <span className="text-red-500">*</span>
            </label>
            <input
              type="password"
              id="password"
              name="password"
              value={registerForm.password}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
              placeholder="Tối thiểu 6 ký tự"
              required
            />
          </div>

          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-1">
              Xác nhận mật khẩu <span className="text-red-500">*</span>
            </label>
            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              value={registerForm.confirmPassword}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
              placeholder="Nhập lại mật khẩu"
              required
            />
          </div>

          <div>
            <label htmlFor="department_id" className="block text-sm font-medium text-gray-700 mb-1">
              Khoa/Viện <span className="text-red-500">*</span>
            </label>
            <select
              id="department_id"
              name="department_id"
              value={registerForm.department_id}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
              required
            >
              <option value="">-- Chọn Khoa/Viện --</option>
              {departments.map((dept) => (
                <option key={dept.id} value={dept.id}>
                  {dept.id} - {dept.department_name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="course_id" className="block text-sm font-medium text-gray-700 mb-1">
              Ngành học <span className="text-red-500">*</span>
            </label>
            <select
              id="course_id"
              name="course_id"
              value={registerForm.course_id}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
              required
              disabled={!registerForm.department_id}
            >
              <option value="">
                {registerForm.department_id 
                  ? "-- Chọn ngành học --" 
                  : "-- Vui lòng chọn Khoa/Viện trước --"}
              </option>
              {registerForm.department_id && courses.map((course) => (
                <option key={course.id} value={course.id}>
                  {course.course_id} - {course.course_name}
                </option>
              ))}
            </select>
          </div>

          {/* Error message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-800 font-medium">
                    {error}
                  </p>
                </div>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {loading ? 'Đang đăng ký...' : 'Đăng ký'}
          </button>
        </form>

        <div className="mt-4 text-center">
          <p className="text-sm text-gray-600">
            Đã có tài khoản?{' '}
            <Link to="/login" className="text-green-600 hover:text-green-700 font-medium">
              Đăng nhập ngay
            </Link>
          </p>
        </div>

        <div className="mt-4 text-center">
          <p className="text-xs text-gray-500">
            © 2023 Hệ thống hỗ trợ đăng ký học tập. Bản quyền thuộc về Trường Đại học.
          </p>
        </div>
      </div>
    </div>
  )
}

export default Register
