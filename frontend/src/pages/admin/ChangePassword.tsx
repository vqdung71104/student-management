import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import AuthService from '../../services/authService'

interface PasswordFormData {
  currentPassword: string
  newPassword: string
  confirmPassword: string
}

const ChangePassword = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [passwordForm, setPasswordForm] = useState<PasswordFormData>({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  })

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

  const handlePasswordSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError('')
    setMessage('')

    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      setError('Mật khẩu xác nhận không khớp')
      return
    }

    const passwordError = validatePassword(passwordForm.newPassword)
    if (passwordError) {
      setError(passwordError)
      return
    }

    if (passwordForm.currentPassword === passwordForm.newPassword) {
      setError('Mật khẩu mới phải khác mật khẩu hiện tại')
      return
    }

    setLoading(true)
    try {
      const response = await fetch('/api/admin/change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...AuthService.getAuthHeaders(),
        },
        body: JSON.stringify({
          current_password: passwordForm.currentPassword,
          new_password: passwordForm.newPassword,
        }),
      })

      if (response.ok) {
        setMessage('Đổi mật khẩu thành công!')
        setPasswordForm({ currentPassword: '', newPassword: '', confirmPassword: '' })
        setTimeout(() => navigate('/admin'), 2000)
        return
      }

      const detail = await readApiError(response, 'Không thể đổi mật khẩu lúc này. Vui lòng thử lại.')
      console.error('[ChangePassword][admin] change-password failed', {
        status: response.status,
        detail,
      })
      setError(detail)
    } catch (error) {
      console.error('[ChangePassword][admin] network error', error)
      setError('Không thể kết nối đến server. Vui lòng kiểm tra lại mạng hoặc đăng nhập lại.')
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
          Mật khẩu mới cần tối thiểu 8 ký tự
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
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

          <form onSubmit={handlePasswordSubmit} className="space-y-6">
            <div>
              <label htmlFor="currentPassword" className="block text-sm font-medium text-gray-700">
                Mật khẩu hiện tại
              </label>
              <div className="relative mt-1">
                <input
                  id="currentPassword"
                  type="password"
                  required
                  value={passwordForm.currentPassword}
                  onChange={(event) => setPasswordForm({ ...passwordForm, currentPassword: event.target.value })}
                  className="block w-full px-3 py-2 pr-14 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  autoComplete="current-password"
                />
                <div className="absolute inset-y-0 right-0 w-11 rounded-r-md border-l border-gray-200 bg-gray-50" aria-hidden="true" />
              </div>
            </div>

            <div>
              <label htmlFor="newPassword" className="block text-sm font-medium text-gray-700">
                Mật khẩu mới
              </label>
              <div className="relative mt-1">
                <input
                  id="newPassword"
                  type="password"
                  required
                  value={passwordForm.newPassword}
                  onChange={(event) => setPasswordForm({ ...passwordForm, newPassword: event.target.value })}
                  className="block w-full px-3 py-2 pr-14 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  autoComplete="new-password"
                />
                <div className="absolute inset-y-0 right-0 w-11 rounded-r-md border-l border-gray-200 bg-gray-50" aria-hidden="true" />
              </div>
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                Xác nhận mật khẩu mới
              </label>
              <div className="relative mt-1">
                <input
                  id="confirmPassword"
                  type="password"
                  required
                  value={passwordForm.confirmPassword}
                  onChange={(event) => setPasswordForm({ ...passwordForm, confirmPassword: event.target.value })}
                  className="block w-full px-3 py-2 pr-14 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  autoComplete="new-password"
                />
                <div className="absolute inset-y-0 right-0 w-11 rounded-r-md border-l border-gray-200 bg-gray-50" aria-hidden="true" />
              </div>
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
        </div>
      </div>
    </div>
  )
}

export default ChangePassword