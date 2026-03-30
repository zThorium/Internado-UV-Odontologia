import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import ForgotPasswordPage from './pages/ForgotPasswordPage'
import StudentDashboard from './pages/StudentDashboard'
import TutorDashboard from './pages/TutorDashboard'
import CoordinatorDashboard from './pages/CoordinatorDashboard'
import LogbookPage from './pages/student/LogbookPage'
import LogbookNewPage from './pages/student/LogbookNewPage'
import LogbookEditPage from './pages/student/LogbookEditPage'
import IncidentsPage from './pages/student/IncidentsPage'
import AttendancePage from './pages/student/AttendancePage'
import StudentsListPage from './pages/tutor/StudentsListPage'
import EvaluationFormPage from './pages/tutor/EvaluationFormPage'
import ConfirmationPage from './pages/tutor/ConfirmationPage'
import TutorAttendancePage from './pages/tutor/AttendancePage'
import OverviewPage from './pages/coordinator/OverviewPage'
import LogbooksPage from './pages/coordinator/LogbooksPage'
import LogbookDetailPage from './pages/coordinator/LogbookDetailPage'
import EvaluationsPage from './pages/coordinator/EvaluationsPage'
import CoordinatorIncidentsPage from './pages/coordinator/IncidentsPage'
import AssignmentsPage from './pages/coordinator/AssignmentsPage'
import CohortsPage from './pages/coordinator/CohortsPage'
import UsersPage from './pages/coordinator/UsersPage'
import CoordinatorAttendancePage from './pages/coordinator/AttendancePage'
import WellbeingPage from './pages/coordinator/WellbeingPage'
import AlertsPage from './pages/coordinator/AlertsPage'

export default function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />

          {/* Vista Estudiante */}
          <Route
            path="/student"
            element={
              <ProtectedRoute allowedRoles={['student']}>
                <StudentDashboard />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/student/logbook" replace />} />
            <Route path="logbook" element={<LogbookPage />} />
            <Route path="logbook/new" element={<LogbookNewPage />} />
            <Route path="logbook/:id" element={<LogbookEditPage />} />
            <Route path="incidents" element={<IncidentsPage />} />
            <Route path="attendance" element={<AttendancePage />} />
          </Route>

          {/* Vista Tutor */}
          <Route
            path="/tutor"
            element={
              <ProtectedRoute allowedRoles={['tutor']}>
                <TutorDashboard />
              </ProtectedRoute>
            }
          >
            <Route index element={<StudentsListPage />} />
            <Route path="evaluate/:assignment_id" element={<EvaluationFormPage />} />
            <Route path="confirmation" element={<ConfirmationPage />} />
            <Route path="attendance/:student_id" element={<TutorAttendancePage />} />
          </Route>

          {/* Vista Coordinador */}
          <Route
            path="/coordinator"
            element={
              <ProtectedRoute allowedRoles={['coordinator']}>
                <CoordinatorDashboard />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/coordinator/overview" replace />} />
            <Route path="overview" element={<OverviewPage />} />
            <Route path="logbooks" element={<LogbooksPage />} />
            <Route path="logbooks/:entryId" element={<LogbookDetailPage />} />
            <Route path="evaluations" element={<EvaluationsPage />} />
            <Route path="incidents" element={<CoordinatorIncidentsPage />} />
            <Route path="assignments" element={<AssignmentsPage />} />
            <Route path="cohorts" element={<CohortsPage />} />
            <Route path="users" element={<UsersPage />} />
            <Route path="attendance" element={<CoordinatorAttendancePage />} />
            <Route path="wellbeing" element={<WellbeingPage />} />
            <Route path="alerts" element={<AlertsPage />} />
          </Route>

            <Route path="/" element={<Navigate to="/login" replace />} />
          </Routes>
        </BrowserRouter>
      </ThemeProvider>
    </AuthProvider>
  )
}
