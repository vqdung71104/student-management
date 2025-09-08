import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import AdminLayout from '../layouts/AdminLayout'
import StudentLayout from '../layouts/StudentLayout'

interface ProtectedRouteProps {
  allowedRoles: ('admin' | 'student')[]
}

const ProtectedRoute = ({ allowedRoles }: ProtectedRouteProps) => {
  const { isAuthenticated, userRole } = useAuth()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (!userRole || !allowedRoles.includes(userRole)) {
    return <Navigate to="/login" replace />
  }

  // Wrap with appropriate layout
  if (userRole === 'admin') {
    return (
      <AdminLayout>
        <Outlet />
      </AdminLayout>
    )
  } else {
    return (
      <StudentLayout>
        <Outlet />
      </StudentLayout>
    )
  }
}

export default ProtectedRoute
