import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

interface PasswordFormData {
  currentPassword: string
  newPassword: string
  confirmPassword: string
}

interface OTPFormData {
  email: string
  otp: string
  newPassword: string
  confirmPassword: string
}

const ChangePassword = () => {
  const navigate = useNavigate()
  const [mode, setMode] = useState<'password' | 'forgot' | 'otp'>('password')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [countdown, setCountdown] = useState(0)
  
  const [passwordForm, setPasswordForm] = useState<PasswordFormData>({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  })
  
  const [otpForm, setOTPForm] = useState<OTPFormData>({
    email: 'vuquangdung71104@gmail.com',
    otp: '',
    newPassword: '',
    confirmPassword: ''
  })

  // Countdown timer for OTP resend
  useEffect(() => {
    let timer: number | null = null
    if (countdown > 0) {
      timer = window.setTimeout(() => setCountdown(countdown - 1), 1000)
    }
    return () => {
      if (timer) clearTimeout(timer)
    }
  }, [countdown])

  const validatePassword = (password: string): string[] => {
    const errors: string[] = []
    if (password.length < 8) {
      errors.push('Mật khẩu phải có ít nhất 8 ký tự')
    }
    if (!/[A-Z]/.test(password)) {
      errors.push('Mật khẩu phải có ít nhất 1 chữ cái viết hoa')
    }
    if (!/[a-z]/.test(password)) {
      errors.push('Mật khẩu phải có ít nhất 1 chữ cái viết thường')
    }
    if (!/\d/.test(password)) {
      errors.push('Mật khẩu phải có ít nhất 1 chữ số')
    }
    if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>?]/.test(password)) {
      errors.push('Mật khẩu phải có ít nhất 1 ký tự đặc biệt')
    }
    return errors
  }

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setMessage('')

    // Validate form
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      setError('Mật khẩu xác nhận không khớp')
      return
    }

    const passwordErrors = validatePassword(passwordForm.newPassword)
    if (passwordErrors.length > 0) {
      setError(passwordErrors.join(', '))
      return
    }

    setLoading(true)
    try {
      const response = await fetch('http://127.0.0.1:8000/admin/change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          current_password: passwordForm.currentPassword,
          new_password: passwordForm.newPassword
        }),
      })

      const result = await response.json()

      if (response.ok) {
        setMessage('Đổi mật khẩu thành công!')
        setTimeout(() => navigate('/admin'), 2000)
      } else {
        setError(result.detail || 'Có lỗi xảy ra')
      }
    } catch (error) {
      setError('Không thể kết nối đến server')
    } finally {
      setLoading(false)
    }
  }

  const handleForgotPassword = async () => {
    setError('')
    setMessage('')
    setLoading(true)

    try {
      const response = await fetch('http://127.0.0.1:8000/admin/request-password-reset', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: otpForm.email
        }),
      })

      const result = await response.json()

      if (response.ok) {
        setMessage('Mã OTP đã được gửi đến email của bạn')
        setMode('otp')
        setCountdown(600) // 10 minutes
      } else {
        setError(result.detail || 'Có lỗi xảy ra khi gửi OTP')
      }
    } catch (error) {
      setError('Không thể kết nối đến server')
    } finally {
      setLoading(false)
    }
  }

  const handleOTPSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setMessage('')

    // Validate form
    if (otpForm.newPassword !== otpForm.confirmPassword) {
      setError('Mật khẩu xác nhận không khớp')
      return
    }

    const passwordErrors = validatePassword(otpForm.newPassword)
    if (passwordErrors.length > 0) {
      setError(passwordErrors.join(', '))
      return
    }

    if (!otpForm.otp || otpForm.otp.length !== 6) {
      setError('Vui lòng nhập mã OTP 6 chữ số')
      return
    }

    setLoading(true)
    try {
      const response = await fetch('http://127.0.0.1:8000/admin/verify-otp-and-change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: otpForm.email,
          otp: otpForm.otp,
          new_password: otpForm.newPassword
        }),
      })

      const result = await response.json()

      if (response.ok) {
        setMessage('Đổi mật khẩu thành công!')
        setTimeout(() => navigate('/admin'), 2000)
      } else {
        setError(result.detail || 'Có lỗi xảy ra')
      }
    } catch (error) {
      setError('Không thể kết nối đến server')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Đổi mật khẩu Admin
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Để đảm bảo bảo mật, vui lòng sử dụng mật khẩu mạnh
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          {/* Tab Navigation */}
          <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg mb-6">
            <button
              onClick={() => setMode('password')}
              className={`flex-1 py-2 px-3 rounded-md text-sm font-medium transition-colors ${
                mode === 'password' 
                  ? 'bg-white text-blue-700 shadow-sm' 
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Đổi mật khẩu
            </button>
            <button
              onClick={() => setMode('forgot')}
              className={`flex-1 py-2 px-3 rounded-md text-sm font-medium transition-colors ${
                mode === 'forgot' || mode === 'otp'
                  ? 'bg-white text-blue-700 shadow-sm' 
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Quên mật khẩu
            </button>
          </div>

          {/* Success/Error Messages */}
          {message && (
            <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-md">
              <p className="text-green-800 text-sm">{message}</p>
            </div>
          )}

          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}

          {/* Change Password Form */}
          {mode === 'password' && (
            <form onSubmit={handlePasswordSubmit} className="space-y-6">
              <div>
                <label htmlFor="currentPassword" className="block text-sm font-medium text-gray-700">
                  Mật khẩu hiện tại
                </label>
                <input
                  id="currentPassword"
                  type="password"
                  required
                  value={passwordForm.currentPassword}
                  onChange={(e) => setPasswordForm({...passwordForm, currentPassword: e.target.value})}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label htmlFor="newPassword" className="block text-sm font-medium text-gray-700">
                  Mật khẩu mới
                </label>
                <input
                  id="newPassword"
                  type="password"
                  required
                  value={passwordForm.newPassword}
                  onChange={(e) => setPasswordForm({...passwordForm, newPassword: e.target.value})}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                  Xác nhận mật khẩu mới
                </label>
                <input
                  id="confirmPassword"
                  type="password"
                  required
                  value={passwordForm.confirmPassword}
                  onChange={(e) => setPasswordForm({...passwordForm, confirmPassword: e.target.value})}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                >
                  {loading ? 'Đang xử lý...' : 'Đổi mật khẩu'}
                </button>
              </div>
            </form>
          )}

          {/* Forgot Password Form */}
          {mode === 'forgot' && (
            <div className="space-y-6">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                  Email Admin
                </label>
                <input
                  id="email"
                  type="email"
                  value={otpForm.email}
                  onChange={(e) => setOTPForm({...otpForm, email: e.target.value})}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  disabled
                />
              </div>

              <div>
                <button
                  onClick={handleForgotPassword}
                  disabled={loading || countdown > 0}
                  className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                >
                  {loading ? 'Đang gửi...' : countdown > 0 ? `Gửi lại sau ${Math.floor(countdown/60)}:${String(countdown%60).padStart(2, '0')}` : 'Gửi mã OTP'}
                </button>
              </div>
            </div>
          )}

          {/* OTP Verification Form */}
          {mode === 'otp' && (
            <form onSubmit={handleOTPSubmit} className="space-y-6">
              <div>
                <label htmlFor="otp" className="block text-sm font-medium text-gray-700">
                  Mã OTP (6 chữ số)
                </label>
                <input
                  id="otp"
                  type="text"
                  maxLength={6}
                  required
                  value={otpForm.otp}
                  onChange={(e) => setOTPForm({...otpForm, otp: e.target.value.replace(/\\D/g, '')})}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-center text-lg tracking-widest"
                  placeholder="000000"
                />
                {countdown > 0 && (
                  <p className="mt-1 text-xs text-gray-500">
                    Mã OTP hết hạn sau: {Math.floor(countdown/60)}:{String(countdown%60).padStart(2, '0')}
                  </p>
                )}
              </div>

              <div>
                <label htmlFor="otpNewPassword" className="block text-sm font-medium text-gray-700">
                  Mật khẩu mới
                </label>
                <input
                  id="otpNewPassword"
                  type="password"
                  required
                  value={otpForm.newPassword}
                  onChange={(e) => setOTPForm({...otpForm, newPassword: e.target.value})}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label htmlFor="otpConfirmPassword" className="block text-sm font-medium text-gray-700">
                  Xác nhận mật khẩu mới
                </label>
                <input
                  id="otpConfirmPassword"
                  type="password"
                  required
                  value={otpForm.confirmPassword}
                  onChange={(e) => setOTPForm({...otpForm, confirmPassword: e.target.value})}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div className="flex space-x-3">
                <button
                  type="button"
                  onClick={() => setMode('forgot')}
                  className="flex-1 py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Quay lại
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                >
                  {loading ? 'Xác thực...' : 'Xác thực & Đổi mật khẩu'}
                </button>
              </div>
            </form>
          )}

          {/* Password Requirements */}
          <div className="mt-6 p-4 bg-gray-50 rounded-md">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Yêu cầu mật khẩu:</h4>
            <ul className="text-xs text-gray-600 space-y-1">
              <li>• Ít nhất 8 ký tự</li>
              <li>• Có chữ cái viết hoa (A-Z)</li>
              <li>• Có chữ cái viết thường (a-z)</li>
              <li>• Có chữ số (0-9)</li>
              <li>• Có ký tự đặc biệt (!@#$%^&*)</li>
              <li className="text-orange-600">• Mật khẩu cần được đổi mỗi 3 tháng</li>
            </ul>
          </div>

          {/* Back to Admin */}
          <div className="mt-6">
            <button
              onClick={() => navigate('/admin')}
              className="w-full text-center py-2 px-4 text-sm text-blue-600 hover:text-blue-500"
            >
              ← Quay lại trang Admin
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChangePassword