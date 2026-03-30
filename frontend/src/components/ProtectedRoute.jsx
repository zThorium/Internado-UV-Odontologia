import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useEffect } from 'react'
import { hasRequiredRole, logSecurityEvent, clearAuthData } from '../utils/security'

const ROLE_DASHBOARDS = {
  student: '/student',
  tutor: '/tutor',
  coordinator: '/coordinator',
}

// Loading spinner component
function LoadingSpinner() {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      background: '#f5f5f7',
    }}>
      <div style={{
        textAlign: 'center',
      }}>
        <div className="spinner" style={{
          width: '3rem',
          height: '3rem',
          borderWidth: '4px',
          margin: '0 auto 1rem',
        }} />
        <p style={{
          color: '#3d6480',
          fontSize: '0.875rem',
          margin: 0,
        }}>
          Verificando sesión...
        </p>
      </div>
    </div>
  )
}

export default function ProtectedRoute({ children, allowedRoles }) {
  const { user, isLoading, logout } = useAuth()
  const location = useLocation()

  // Log unauthorized access attempts
  useEffect(() => {
    if (!isLoading && user && allowedRoles && !hasRequiredRole(user, allowedRoles)) {
      logSecurityEvent('unauthorized_access_attempt', {
        userId: user.id,
        userRole: user.role,
        attemptedPath: location.pathname,
        allowedRoles,
      })
    }
  }, [user, isLoading, allowedRoles, location.pathname])

  // Show loading spinner while checking authentication
  if (isLoading) {
    return <LoadingSpinner />
  }

  // Redirect to login if not authenticated
  if (!user) {
    logSecurityEvent('unauthenticated_access_attempt', {
      attemptedPath: location.pathname,
    })
    
    // Clear any stale auth data
    clearAuthData()
    
    // Redirect to login with return URL
    return <Navigate to="/login" state={{ from: location.pathname }} replace />
  }

  // Redirect to correct dashboard if user doesn't have required role
  if (allowedRoles && !hasRequiredRole(user, allowedRoles)) {
    const userDashboard = ROLE_DASHBOARDS[user.role]
    
    if (!userDashboard) {
      // Invalid role, logout user
      logSecurityEvent('invalid_user_role', {
        userId: user.id,
        role: user.role,
      })
      logout()
      return <Navigate to="/login" replace />
    }
    
    // Redirect to user's correct dashboard
    return <Navigate to={userDashboard} replace />
  }

  return children
}
