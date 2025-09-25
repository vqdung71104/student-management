import { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'

const StudentChangePassword = () => {
  const { userInfo } = useAuth()
  const [currentStep, setCurrentStep] = useState<'current' | 'otp' | 'success'>('current')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  
  // Form data for current password method
  const [currentPasswordData, setCurrentPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  })
  
  // Form data for OTP method
  const [otpData, setOtpData] = useState({
    otp: '',
    newPassword: '',
    confirmPassword: ''
  })
  
  const [useOtpMethod, setUseOtpMethod] = useState(false)
  const [otpSent, setOtpSent] = useState(false)

  const validatePassword = (password: string): string | null => {
    if (password.length < 8) {
      return 'Mật khẩu phải có ít nhất 8 ký tự'
    }
    if (!/[A-Z]/.test(password)) {
      return 'Mật khẩu phải có ít nhất 1 chữ cái viết hoa'
    }
    if (!/[a-z]/.test(password)) {
      return 'Mật khẩu phải có ít nhất 1 chữ cái viết thường'
    }
    if (!/\d/.test(password)) {
      return 'Mật khẩu phải có ít nhất 1 chữ số'
    }
    if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>?]/.test(password)) {
      return 'Mật khẩu phải có ít nhất 1 ký tự đặc biệt'
    }
    return null
  }

  const handleCurrentPasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccessMessage('')
    
    // Validate passwords
    const passwordError = validatePassword(currentPasswordData.newPassword)
    if (passwordError) {
      setError(passwordError)
      return
    }
    
    if (currentPasswordData.newPassword !== currentPasswordData.confirmPassword) {
      setError('Mật khẩu xác nhận không khớp')
      return
    }
    
    if (currentPasswordData.currentPassword === currentPasswordData.newPassword) {
      setError('Mật khẩu mới phải khác mật khẩu hiện tại')
      return
    }
    
    setIsLoading(true)
    
    try {
      const response = await fetch('http://127.0.0.1:8000/student/change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          student_email: userInfo?.email,
          current_password: currentPasswordData.currentPassword,
          new_password: currentPasswordData.newPassword
        }),
      })
      
      const data = await response.json()
      
      if (response.ok) {
        setCurrentStep('success')
        setSuccessMessage('Đổi mật khẩu thành công!')
        setCurrentPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' })
      } else {
        setError(data.detail || 'Có lỗi xảy ra khi đổi mật khẩu')
      }
    } catch (error) {
      setError('Có lỗi xảy ra khi đổi mật khẩu')
    } finally {
      setIsLoading(false)
    }
  }

  const handleRequestOtp = async () => {
    setError('')
    setIsLoading(true)
    
    try {
      const response = await fetch('http://127.0.0.1:8000/student/request-password-reset', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: userInfo?.email
        }),
      })
      
      const data = await response.json()
      
      if (response.ok) {
        setOtpSent(true)
        setSuccessMessage('Mã OTP đã được gửi đến email của bạn')
      } else {
        setError(data.detail || 'Có lỗi xảy ra khi gửi OTP')
      }
    } catch (error) {
      setError('Có lỗi xảy ra khi gửi OTP')
    } finally {
      setIsLoading(false)
    }
  }

  const handleOtpSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccessMessage('')
    
    // Validate passwords
    const passwordError = validatePassword(otpData.newPassword)
    if (passwordError) {
      setError(passwordError)
      return
    }
    
    if (otpData.newPassword !== otpData.confirmPassword) {
      setError('Mật khẩu xác nhận không khớp')
      return
    }
    
    setIsLoading(true)
    
    try {
      const response = await fetch('http://127.0.0.1:8000/student/verify-otp-and-change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: userInfo?.email,
          otp: otpData.otp,
          new_password: otpData.newPassword
        }),
      })
      
      const data = await response.json()
      
      if (response.ok) {
        setCurrentStep('success')
        setSuccessMessage('Đổi mật khẩu thành công!')
        setOtpData({ otp: '', newPassword: '', confirmPassword: '' })
      } else {
        setError(data.detail || 'Có lỗi xảy ra khi xác thực OTP')
      }
    } catch (error) {
      setError('Có lỗi xảy ra khi xác thực OTP')
    } finally {
      setIsLoading(false)
    }
  }

  const resetForm = () => {
    setCurrentStep('current')
    setError('')
    setSuccessMessage('')
    setUseOtpMethod(false)
    setOtpSent(false)
    setCurrentPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' })
    setOtpData({ otp: '', newPassword: '', confirmPassword: '' })
  }

  if (currentStep === 'success') {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-md mx-auto">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-gray-900 mb-2">Thành công!</h2>
              <p className="text-gray-600 mb-6">{successMessage}</p>
              <button
                onClick={resetForm}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Đổi mật khẩu lần nữa
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-md mx-auto">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-6 text-center">Đổi mật khẩu</h1>
          
          <div className="mb-6">
            <p className="text-sm text-gray-600 mb-4">Email của bạn: <span className="font-medium">{userInfo?.email}</span></p>
            
            <div className="flex space-x-4 mb-4">
              <button
                onClick={() => setUseOtpMethod(false)}
                className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
                  !useOtpMethod
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Dùng mật khẩu hiện tại
              </button>
              <button
                onClick={() => setUseOtpMethod(true)}
                className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
                  useOtpMethod
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Dùng OTP email
              </button>
            </div>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          )}

          {successMessage && !currentStep.includes('success') && (
            <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-green-600 text-sm">{successMessage}</p>
            </div>
          )}

          {!useOtpMethod ? (
            <form onSubmit={handleCurrentPasswordSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Mật khẩu hiện tại
                </label>
                <input
                  type="password"
                  value={currentPasswordData.currentPassword}
                  onChange={(e) => setCurrentPasswordData({...currentPasswordData, currentPassword: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Mật khẩu mới
                </label>
                <input
                  type="password"
                  value={currentPasswordData.newPassword}
                  onChange={(e) => setCurrentPasswordData({...currentPasswordData, newPassword: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
                <div className="mt-2 text-xs text-gray-500">
                  <p>• Ít nhất 8 ký tự</p>
                  <p>• Có chữ hoa, chữ thường, số và ký tự đặc biệt</p>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Xác nhận mật khẩu mới
                </label>
                <input
                  type="password"
                  value={currentPasswordData.confirmPassword}
                  onChange={(e) => setCurrentPasswordData({...currentPasswordData, confirmPassword: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Đang xử lý...' : 'Đổi mật khẩu'}
              </button>
            </form>
          ) : (
            <div className="space-y-4">
              {!otpSent ? (
                <div className="text-center">
                  <p className="text-gray-600 mb-4">
                    Chúng tôi sẽ gửi mã OTP đến email: <span className="font-medium">{userInfo?.email}</span>
                  </p>
                  <button
                    onClick={handleRequestOtp}
                    disabled={isLoading}
                    className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isLoading ? 'Đang gửi...' : 'Gửi mã OTP'}
                  </button>
                </div>
              ) : (
                <form onSubmit={handleOtpSubmit} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Mã OTP (6 chữ số)
                    </label>
                    <input
                      type="text"
                      value={otpData.otp}
                      onChange={(e) => setOtpData({...otpData, otp: e.target.value.replace(/\D/g, '').slice(0, 6)})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-center text-lg tracking-widest"
                      placeholder="000000"
                      maxLength={6}
                      required
                    />
                    <p className="text-xs text-gray-500 mt-1">Mã OTP có hiệu lực trong 10 phút</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Mật khẩu mới
                    </label>
                    <input
                      type="password"
                      value={otpData.newPassword}
                      onChange={(e) => setOtpData({...otpData, newPassword: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      required
                    />
                    <div className="mt-2 text-xs text-gray-500">
                      <p>• Ít nhất 8 ký tự</p>
                      <p>• Có chữ hoa, chữ thường, số và ký tự đặc biệt</p>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Xác nhận mật khẩu mới
                    </label>
                    <input
                      type="password"
                      value={otpData.confirmPassword}
                      onChange={(e) => setOtpData({...otpData, confirmPassword: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      required
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isLoading ? 'Đang xử lý...' : 'Xác thực và đổi mật khẩu'}
                  </button>

                  <button
                    type="button"
                    onClick={handleRequestOtp}
                    disabled={isLoading}
                    className="w-full text-blue-600 py-2 px-4 rounded-lg hover:bg-blue-50 transition-colors text-sm"
                  >
                    Gửi lại mã OTP
                  </button>
                </form>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default StudentChangePassword