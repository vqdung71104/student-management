import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

const ResetPassword = () => {
  const [searchParams] = useSearchParams()
  const token = useMemo(() => searchParams.get('token') || '', [searchParams])

  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const hasToken = token.trim().length > 0

  useEffect(() => {
    if (!hasToken) {
      setError('Link đặt lại mật khẩu không hợp lệ hoặc thiếu token.')
    } else if (error === 'Link đặt lại mật khẩu không hợp lệ hoặc thiếu token.') {
      setError('')
    }
  }, [hasToken])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setMessage('')

    if (newPassword !== confirmPassword) {
      setError('Mật khẩu xác nhận không khớp')
      return
    }

    if (newPassword.length < 8) {
      setError('Mật khẩu phải có ít nhất 8 ký tự')
      return
    }

    setLoading(true)
    try {
      const response = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: newPassword }),
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Không thể đặt lại mật khẩu')
      }

      setMessage(data.message || 'Đặt lại mật khẩu thành công')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Có lỗi xảy ra')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-700 to-blue-500 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md mx-4">
        <h1 className="text-2xl font-bold text-gray-900 mb-2 text-center">Đặt lại mật khẩu</h1>

        {!hasToken ? (
          <div>
            <p className="text-sm text-red-700 mb-4 text-center">Link đặt lại mật khẩu không hợp lệ hoặc đã hết hạn.</p>
            <div className="text-center">
              <Link to="/forgot-password" className="text-blue-600 hover:text-blue-700 font-medium">Yêu cầu link mới</Link>
            </div>
          </div>
        ) : (
          <>
            {message && <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md text-green-800 text-sm">{message}</div>}
            {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-red-800 text-sm">{error}</div>}

            {!message && (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Mật khẩu mới</label>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Xác nhận mật khẩu mới</label>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition disabled:opacity-50"
                >
                  {loading ? 'Đang cập nhật...' : 'Đặt lại mật khẩu'}
                </button>
              </form>
            )}
          </>
        )}

        <div className="mt-6 text-center">
          <Link to="/login" className="text-sm text-blue-600 hover:text-blue-700 font-medium">
            Quay lại đăng nhập
          </Link>
        </div>
      </div>
    </div>
  )
}

export default ResetPassword
