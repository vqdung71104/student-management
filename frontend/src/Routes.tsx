import { Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import AdminDashboard from './pages/admin/AdminDashboard'
import StudentsManagement from './pages/admin/StudentsManagement'
import SubjectsManagement from './pages/admin/SubjectsManagement'
import ClassesManagement from './pages/admin/ClassesManagement'
import ScheduleManagement from './pages/admin/ScheduleManagement'
import StudentDashboard from './pages/student/StudentDashboard'
import Schedule from './pages/student/Schedule'
import Grades from './pages/student/Grades'
import Curriculum from './pages/student/Curriculum'
import Projects from './pages/student/Projects'
import Forms from './pages/student/Forms'
import Scholarships from './pages/student/Scholarships'
import ProtectedRoute from './components/ProtectedRoute'
import { useAuth } from './contexts/AuthContext'

function AppRoutes() {
  const { isAuthenticated, userRole } = useAuth()

  return (
    <Routes>
      {/* Public Routes */}
      <Route 
        path="/login" 
        element={
          isAuthenticated ? (
            <Navigate to={userRole === 'admin' ? '/admin' : '/student'} replace />
          ) : (
            <Login />
          )
        } 
      />
      
      {/* Admin Routes */}
      <Route path="/admin" element={<ProtectedRoute allowedRoles={['admin']} />}>
        <Route index element={<AdminDashboard />} />
        <Route path="students" element={<StudentsManagement />} />
        <Route path="schedule" element={<ClassesManagement />} />
        <Route path="schedule-update" element={<ScheduleManagement />} />
        <Route path="subjects" element={<SubjectsManagement />} />
        <Route path="settings" element={<AdminDashboard />} />
      </Route>

      {/* Student Routes */}
      <Route path="/student" element={<ProtectedRoute allowedRoles={['student']} />}>
        <Route index element={<StudentDashboard />} />
        <Route path="schedule" element={<Schedule />} />
        <Route path="grades" element={<Grades />} />
        <Route path="curriculum" element={<Curriculum />} />
        <Route path="projects" element={<Projects />} />
        <Route path="forms" element={<Forms />} />
        <Route path="scholarships" element={<Scholarships />} />
        <Route path="profile" element={<StudentDashboard />} />
      </Route>

      {/* Default Redirects */}
      <Route 
        path="/" 
        element={
          isAuthenticated 
            ? <Navigate to={userRole === 'admin' ? '/admin' : '/student'} /> 
            : <Navigate to="/login" />
        } 
      />
      
      {/* 404 Page */}
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  )
}

export default AppRoutes
