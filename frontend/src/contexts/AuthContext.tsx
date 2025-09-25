import { createContext, useContext, useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import type { ReactNode } from 'react'

interface User {
  id?: string
  student_id?: string
  student_name?: string
  email?: string
  username?: string
  role?: string
}

interface AuthContextType {
  isAuthenticated: boolean
  userRole: 'admin' | 'student' | null
  userInfo: User | null
  login: (email: string, password: string) => Promise<boolean>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [userRole, setUserRole] = useState<'admin' | 'student' | null>(null)
  const [userInfo, setUserInfo] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  // Khôi phục trạng thái đăng nhập khi load trang
  useEffect(() => {
    const savedAuth = localStorage.getItem('authState')
    if (savedAuth) {
      try {
        const authData = JSON.parse(savedAuth)
        setIsAuthenticated(authData.isAuthenticated)
        setUserRole(authData.userRole)
        setUserInfo(authData.userInfo)
      } catch (error) {
        console.error('Error parsing saved auth state:', error)
        localStorage.removeItem('authState')
      }
    }
    setLoading(false)
  }, [])

  // Lưu trạng thái đăng nhập vào localStorage mỗi khi thay đổi
  useEffect(() => {
    if (!loading) {
      const authState = {
        isAuthenticated,
        userRole,
        userInfo
      }
      localStorage.setItem('authState', JSON.stringify(authState))
    }
  }, [isAuthenticated, userRole, userInfo, loading])

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      // Thử đăng nhập qua API backend
      const response = await fetch('http://localhost:8000/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email,
          password: password
        })
      })

      if (response.ok) {
        const data = await response.json()
        if (data.user_type === 'student') {
          setUserRole('student')
          setUserInfo(data.user_info)
          setIsAuthenticated(true)
          return true
        } else if (data.user_type === 'admin') {
          setUserRole('admin')
          setUserInfo(data.user_info)
          setIsAuthenticated(true)
          return true
        }
      } else {
        // Fallback cho demo - sử dụng student_id thật từ database
        if (email === 'student' && password === 'student123') {
          setUserRole('student')
          setUserInfo({ 
            student_id: '20225818', // Sử dụng student_id thật từ database
            student_name: 'Vũ Quang Dũng',
            email: 'dung.vq225818@sis.hust.edu.vn'
          })
          setIsAuthenticated(true)
          return true
        }
      }
      return false
    } catch (error) {
      console.error('Login error:', error)
      // Fallback for demo - sử dụng student_id thật
      if (email === 'student' && password === 'student123') {
        setUserRole('student')
        setUserInfo({ 
          student_id: '20225818',
          student_name: 'Vũ Quang Dũng',
          email: 'dung.vq225818@sis.hust.edu.vn'
        })
        setIsAuthenticated(true)
        return true
      }
      return false
    }
  }

  const logout = () => {
    setIsAuthenticated(false)
    setUserRole(null)
    setUserInfo(null)
    localStorage.removeItem('authState')
  }

  const value = {
    isAuthenticated,
    userRole,
    userInfo,
    login,
    logout
  }

  // Hiển thị loading trong khi khôi phục trạng thái
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
