import { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import AuthService from '../../services/authService'

const StudentChangePassword = () => {
  const { userInfo } = useAuth()
  const [currentStep, setCurrentStep] = useState<'current' | 'otp' | 'success'>('current')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false,
    otpNew: false,
    otpConfirm: false,
  })
  
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
      return 'Mật khẩu mới phải có ít nhất 8 ký tự'
    }

    return null
  }

  const readApiError = async (response: Response, fallbackMessage: string) => {
    const rawBody = await response.text()
    if (!rawBody) {
      return fallbackMessage
    }

    try {
      const parsed = JSON.parse(rawBody)
      return parsed.detail || parsed.message || fallbackMessage
    } catch {
      return rawBody || fallbackMessage
    }
  }

  const togglePasswordVisibility = (field: keyof typeof showPasswords) => {
    setShowPasswords((previous) => ({
      ...previous,
      [field]: !previous[field],
    }))
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
      const response = await fetch('/api/student/change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...AuthService.getAuthHeaders(),
        },
        body: JSON.stringify({
          student_email: userInfo?.email,
          current_password: currentPasswordData.currentPassword,
          new_password: currentPasswordData.newPassword
        }),
      })

      if (response.ok) {
        setCurrentStep('success')
        setSuccessMessage('Đổi mật khẩu thành công!')
        setShowPasswords({ current: false, new: false, confirm: false, otpNew: false, otpConfirm: false })
        setCurrentPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' })
      } else {
        const detail = await readApiError(response, 'Không thể đổi mật khẩu lúc này. Vui lòng thử lại.')
        console.error('[ChangePassword][student] change-password failed', {
          status: response.status,
          detail,
        })
        setError(detail)
      }
    } catch (error) {
      console.error('[ChangePassword][student] change-password network error', error)
      setError('Không thể kết nối đến server. Vui lòng kiểm tra lại mạng hoặc đăng nhập lại.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleRequestOtp = async () => {
    setError('')
    setIsLoading(true)
    
    try {
      const response = await fetch('/api/student/request-password-reset', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...AuthService.getAuthHeaders(),
        },
        body: JSON.stringify({
          email: userInfo?.email
        }),
      })

      if (response.ok) {
        setOtpSent(true)
        setSuccessMessage('Mã OTP đã được gửi đến email của bạn')
      } else {
        const detail = await readApiError(response, 'Không thể gửi OTP lúc này. Vui lòng thử lại.')
        console.error('[ChangePassword][student] request-password-reset failed', {
          status: response.status,
          detail,
        })
        setError(detail)
      }
    } catch (error) {
      console.error('[ChangePassword][student] request-password-reset network error', error)
      setError('Không thể kết nối đến server. Vui lòng kiểm tra lại mạng hoặc đăng nhập lại.')
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
      const response = await fetch('/api/student/verify-otp-and-change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...AuthService.getAuthHeaders(),
        },
        body: JSON.stringify({
          email: userInfo?.email,
          otp: otpData.otp,
          new_password: otpData.newPassword
        }),
      })

      if (response.ok) {
        setCurrentStep('success')
        setSuccessMessage('Đổi mật khẩu thành công!')
        setShowPasswords({ current: false, new: false, confirm: false, otpNew: false, otpConfirm: false })
        setOtpData({ otp: '', newPassword: '', confirmPassword: '' })
      } else {
        const detail = await readApiError(response, 'Không thể xác thực OTP lúc này. Vui lòng thử lại.')
        console.error('[ChangePassword][student] verify-otp-and-change-password failed', {
          status: response.status,
          detail,
        })
        setError(detail)
      }
    } catch (error) {
      console.error('[ChangePassword][student] verify-otp-and-change-password network error', error)
      setError('Không thể kết nối đến server. Vui lòng kiểm tra lại mạng hoặc đăng nhập lại.')
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
    setShowPasswords({ current: false, new: false, confirm: false, otpNew: false, otpConfirm: false })
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
          
          {/* <div className="mb-6">
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
          )}*/}

          {successMessage && !currentStep.includes('success') && (
            <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-green-600 text-sm">{successMessage}</p>
            </div>
          )}

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          )}

          {!useOtpMethod ? (
            <form onSubmit={handleCurrentPasswordSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Mật khẩu hiện tại
                </label>
                <div className="relative">
                  <input
                    type={showPasswords.current ? 'text' : 'password'}
                    value={currentPasswordData.currentPassword}
                    onChange={(e) => setCurrentPasswordData({...currentPasswordData, currentPassword: e.target.value})}
                    className="w-full px-3 py-2 pr-11 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    autoComplete="current-password"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => togglePasswordVisibility('current')}
                    className="absolute inset-y-0 right-0 flex items-center px-3 text-gray-500 hover:text-gray-700"
                    aria-label={showPasswords.current ? 'Ẩn mật khẩu hiện tại' : 'Hiện mật khẩu hiện tại'}
                  >
                    {showPasswords.current ? (
                      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-5 0-9.27-3.11-11-7 1.3-2.92 3.6-5.26 6.5-6.47M17.94 17.94A9.96 9.96 0 0023 12c-1.73-3.89-6-7-11-7-.83 0-1.64.08-2.42.24M9.88 9.88A3 3 0 0012 15a3 3 0 002.12-.88M3 3l18 18" />
                      </svg>
                    ) : (
                      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Mật khẩu mới
                </label>
                <div className="relative">
                  <input
                    type={showPasswords.new ? 'text' : 'password'}
                    value={currentPasswordData.newPassword}
                    onChange={(e) => setCurrentPasswordData({...currentPasswordData, newPassword: e.target.value})}
                    className="w-full px-3 py-2 pr-11 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    autoComplete="new-password"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => togglePasswordVisibility('new')}
                    className="absolute inset-y-0 right-0 flex items-center px-3 text-gray-500 hover:text-gray-700"
                    aria-label={showPasswords.new ? 'Ẩn mật khẩu mới' : 'Hiện mật khẩu mới'}
                  >
                    {showPasswords.new ? (
                      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-5 0-9.27-3.11-11-7 1.3-2.92 3.6-5.26 6.5-6.47M17.94 17.94A9.96 9.96 0 0023 12c-1.73-3.89-6-7-11-7-.83 0-1.64.08-2.42.24M9.88 9.88A3 3 0 0012 15a3 3 0 002.12-.88M3 3l18 18" />
                      </svg>
                    ) : (
                      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    )}
                  </button>
                </div>
                <div className="mt-2 text-xs text-gray-500">
                  <p>• Ít nhất 8 ký tự</p>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Xác nhận mật khẩu mới
                </label>
                <div className="relative">
                  <input
                    type={showPasswords.confirm ? 'text' : 'password'}
                    value={currentPasswordData.confirmPassword}
                    onChange={(e) => setCurrentPasswordData({...currentPasswordData, confirmPassword: e.target.value})}
                    className="w-full px-3 py-2 pr-11 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    autoComplete="new-password"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => togglePasswordVisibility('confirm')}
                    className="absolute inset-y-0 right-0 flex items-center px-3 text-gray-500 hover:text-gray-700"
                    aria-label={showPasswords.confirm ? 'Ẩn xác nhận mật khẩu' : 'Hiện xác nhận mật khẩu'}
                  >
                    {showPasswords.confirm ? (
                      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-5 0-9.27-3.11-11-7 1.3-2.92 3.6-5.26 6.5-6.47M17.94 17.94A9.96 9.96 0 0023 12c-1.73-3.89-6-7-11-7-.83 0-1.64.08-2.42.24M9.88 9.88A3 3 0 0012 15a3 3 0 002.12-.88M3 3l18 18" />
                      </svg>
                    ) : (
                      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    )}
                  </button>
                </div>
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
                    <div className="relative">
                      <input
                        type={showPasswords.otpNew ? 'text' : 'password'}
                        value={otpData.newPassword}
                        onChange={(e) => setOtpData({...otpData, newPassword: e.target.value})}
                        className="w-full px-3 py-2 pr-11 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        autoComplete="new-password"
                        required
                      />
                      <button
                        type="button"
                        onClick={() => togglePasswordVisibility('otpNew')}
                        className="absolute inset-y-0 right-0 flex items-center px-3 text-gray-500 hover:text-gray-700"
                        aria-label={showPasswords.otpNew ? 'Ẩn mật khẩu mới' : 'Hiện mật khẩu mới'}
                      >
                        {showPasswords.otpNew ? (
                          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-5 0-9.27-3.11-11-7 1.3-2.92 3.6-5.26 6.5-6.47M17.94 17.94A9.96 9.96 0 0023 12c-1.73-3.89-6-7-11-7-.83 0-1.64.08-2.42.24M9.88 9.88A3 3 0 0012 15a3 3 0 002.12-.88M3 3l18 18" />
                          </svg>
                        ) : (
                          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                          </svg>
                        )}
                      </button>
                    </div>
                    <div className="mt-2 text-xs text-gray-500">
                      <p>• Ít nhất 8 ký tự</p>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Xác nhận mật khẩu mới
                    </label>
                    <div className="relative">
                      <input
                        type={showPasswords.otpConfirm ? 'text' : 'password'}
                        value={otpData.confirmPassword}
                        onChange={(e) => setOtpData({...otpData, confirmPassword: e.target.value})}
                        className="w-full px-3 py-2 pr-11 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        autoComplete="new-password"
                        required
                      />
                      <button
                        type="button"
                        onClick={() => togglePasswordVisibility('otpConfirm')}
                        className="absolute inset-y-0 right-0 flex items-center px-3 text-gray-500 hover:text-gray-700"
                        aria-label={showPasswords.otpConfirm ? 'Ẩn xác nhận mật khẩu' : 'Hiện xác nhận mật khẩu'}
                      >
                        {showPasswords.otpConfirm ? (
                          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-5 0-9.27-3.11-11-7 1.3-2.92 3.6-5.26 6.5-6.47M17.94 17.94A9.96 9.96 0 0023 12c-1.73-3.89-6-7-11-7-.83 0-1.64.08-2.42.24M9.88 9.88A3 3 0 0012 15a3 3 0 002.12-.88M3 3l18 18" />
                          </svg>
                        ) : (
                          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                          </svg>
                        )}
                      </button>
                    </div>
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