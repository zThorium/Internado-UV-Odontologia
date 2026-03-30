import { createContext, useContext, useState, useEffect } from 'react'
import { useKeycloak } from '@react-keycloak/web'
import api, { setAuthToken } from '../services/api'
import { 
  isTokenExpired, 
  clearAuthData, 
  logSecurityEvent,
  preventClickjacking,
  setupCSPReporting,
  isSecureConnection
} from '../utils/security'

const AuthContext = createContext(null)
const ACCESS_TOKEN_KEY = 'kc_access_token'
const REFRESH_TOKEN_KEY = 'kc_refresh_token'
const MAX_REFRESH_ATTEMPTS = 3
const REFRESH_ATTEMPT_KEY = 'refresh_attempts'

function decodeJwt(token) {
  try {
    const payloadPart = token.split('.')[1]
    if (!payloadPart) return null
    const normalized = payloadPart.replace(/-/g, '+').replace(/_/g, '/')
    const payload = JSON.parse(atob(normalized))
    if (payload.exp && payload.exp * 1000 < Date.now()) return null
    return payload
  } catch {
    return null
  }
}

function extractUserFromClaims(claims) {
  if (!claims) return null
  const roles = claims.realm_access?.roles || []
  const appRoles = ['student', 'tutor', 'coordinator']
  const role = roles.find(r => appRoles.includes(r))
  return { id: claims.sub, role: role || null }
}

// ==========================================
// AuthProvider Keycloak-only
// ==========================================
export function AuthProvider({ children }) {
  const { keycloak, initialized } = useKeycloak()
  const [directAccessToken, setDirectAccessToken] = useState(null)
  const [directRefreshToken, setDirectRefreshToken] = useState(null)
  const [directUser, setDirectUser] = useState(null)
  const [isRestoringSession, setIsRestoringSession] = useState(true)

  // Estado para tour de bienvenida
  const [showTour, setShowTour] = useState(false)

  // Security: Setup protections on mount
  useEffect(() => {
    // Prevent clickjacking
    preventClickjacking()
    
    // Setup CSP reporting
    setupCSPReporting()
    
    // Warn if not on secure connection in production
    if (import.meta.env.PROD && !isSecureConnection()) {
      console.warn('[Security] Application is not running on HTTPS')
      logSecurityEvent('insecure_connection', {
        protocol: window.location.protocol,
        hostname: window.location.hostname,
      })
    }
  }, [])

  // Restore session from localStorage on mount
  useEffect(() => {
    const restoreSession = async () => {
      const savedAccess = localStorage.getItem(ACCESS_TOKEN_KEY)
      const savedRefresh = localStorage.getItem(REFRESH_TOKEN_KEY)

      if (!savedAccess || !savedRefresh) {
        setIsRestoringSession(false)
        return
      }

      // Check if token is expired
      if (isTokenExpired(savedAccess)) {
        // Token expired, try to refresh it
        const refreshAttempts = parseInt(sessionStorage.getItem(REFRESH_ATTEMPT_KEY) || '0')
        
        if (refreshAttempts >= MAX_REFRESH_ATTEMPTS) {
          logSecurityEvent('max_refresh_attempts_exceeded', {
            attempts: refreshAttempts,
          })
          clearAuthData()
          sessionStorage.removeItem(REFRESH_ATTEMPT_KEY)
          setIsRestoringSession(false)
          return
        }

        try {
          sessionStorage.setItem(REFRESH_ATTEMPT_KEY, String(refreshAttempts + 1))
          
          const { data } = await api.post('/auth/refresh', null, {
            params: { refresh_token: savedRefresh },
          })

          const nextAccessToken = data.access_token
          const nextRefreshToken = data.refresh_token || savedRefresh
          const newClaims = decodeJwt(nextAccessToken)

          if (!newClaims) {
            throw new Error('Invalid token after refresh')
          }

          setDirectAccessToken(nextAccessToken)
          setDirectRefreshToken(nextRefreshToken)
          setDirectUser(extractUserFromClaims(newClaims))
          localStorage.setItem(ACCESS_TOKEN_KEY, nextAccessToken)
          localStorage.setItem(REFRESH_TOKEN_KEY, nextRefreshToken)
          sessionStorage.removeItem(REFRESH_ATTEMPT_KEY)
          
          logSecurityEvent('session_restored', {
            userId: newClaims.sub,
          })
        } catch (error) {
          console.error('[Auth] Failed to restore session:', error)
          logSecurityEvent('session_restore_failed', {
            error: error.message,
          })
          clearAuthData()
          sessionStorage.removeItem(REFRESH_ATTEMPT_KEY)
        } finally {
          setIsRestoringSession(false)
        }
      } else {
        // Token is still valid
        const claims = decodeJwt(savedAccess)
        setDirectAccessToken(savedAccess)
        setDirectRefreshToken(savedRefresh)
        setDirectUser(extractUserFromClaims(claims))
        sessionStorage.removeItem(REFRESH_ATTEMPT_KEY)
        setIsRestoringSession(false)
      }
    }

    restoreSession()
  }, [])

  // Auto-refresh de tokens Keycloak
  useEffect(() => {
    if (!keycloak.authenticated) return

    const interval = setInterval(() => {
      keycloak.updateToken(30).then((refreshed) => {
        if (refreshed) {
          console.log('[Keycloak] Token refrescado automáticamente')
        }
      }).catch(() => {
        console.error('[Keycloak] Error al refrescar token, sesión expirada')
        logout()
      })
    }, 10000) // Verificar cada 10 segundos

    return () => clearInterval(interval)
  }, [keycloak.authenticated])

  useEffect(() => {
    if (keycloak.authenticated || !directRefreshToken) return

    const interval = setInterval(async () => {
      try {
        const { data } = await api.post('/auth/refresh', null, {
          params: { refresh_token: directRefreshToken },
        })

        const nextAccessToken = data.access_token
        const nextRefreshToken = data.refresh_token || directRefreshToken
        const claims = decodeJwt(nextAccessToken)

        if (!claims) throw new Error('Token inválido después de refresh')

        setDirectAccessToken(nextAccessToken)
        setDirectRefreshToken(nextRefreshToken)
        setDirectUser(extractUserFromClaims(claims))
        localStorage.setItem(ACCESS_TOKEN_KEY, nextAccessToken)
        localStorage.setItem(REFRESH_TOKEN_KEY, nextRefreshToken)
      } catch {
        setDirectAccessToken(null)
        setDirectRefreshToken(null)
        setDirectUser(null)
        localStorage.removeItem(ACCESS_TOKEN_KEY)
        localStorage.removeItem(REFRESH_TOKEN_KEY)
      }
    }, 60000)

    return () => clearInterval(interval)
  }, [keycloak.authenticated, directRefreshToken])

  // ==========================================
  // Computed values (usuario y token actuales)
  // ==========================================
  const user = keycloak.authenticated ? extractUserFromKeycloak(keycloak) : directUser
  const token = keycloak.authenticated ? keycloak.token : directAccessToken

  // Inyectar token en axios cuando cambie
  useEffect(() => {
    if (token) {
      setAuthToken(token)
    } else {
      setAuthToken(null)
    }
  }, [token])

  // ==========================================
  // Métodos de autenticación
  // ==========================================

  // Login por formulario sin redirección usando Password Grant contra Keycloak
  const login = async (email, password, recaptchaToken = null) => {
    try {
      const { data } = await api.post('/auth/login', { 
        email, 
        password,
        recaptcha_token: recaptchaToken 
      })
      const accessToken = data.access_token
      const refreshToken = data.refresh_token
      const claims = decodeJwt(accessToken)

      if (!accessToken || !refreshToken || !claims) {
        throw new Error('Respuesta de autenticación inválida')
      }

      setDirectAccessToken(accessToken)
      setDirectRefreshToken(refreshToken)
      setDirectUser(extractUserFromClaims(claims))
      localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
      localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
      sessionStorage.removeItem(REFRESH_ATTEMPT_KEY)

      if (data.has_completed_onboarding === false) {
        setShowTour(true)
      }

      logSecurityEvent('login_success', {
        userId: claims.sub,
        role: extractUserFromClaims(claims)?.role,
      })

      return extractUserFromClaims(claims)?.role
    } catch (error) {
      logSecurityEvent('login_failed', {
        email,
        error: error.response?.data?.detail || error.message,
      })
      throw error
    }
  }

  // Logout siempre con Keycloak
  const logout = async () => {
    const userId = user?.id
    
    if (keycloak.authenticated) {
      console.log('[Auth] Logout de Keycloak')
      keycloak.logout()
    }

    if (directRefreshToken) {
      try {
        await api.post('/auth/logout', null, {
          params: { refresh_token: directRefreshToken },
        })
      } catch {
        // Si falla logout remoto, limpiamos estado local igualmente.
      }
    }

    setDirectAccessToken(null)
    setDirectRefreshToken(null)
    setDirectUser(null)
    clearAuthData()
    sessionStorage.removeItem(REFRESH_ATTEMPT_KEY)
    setShowTour(false)
    
    logSecurityEvent('logout', {
      userId,
    })
  }

  /**
   * Completar tour de bienvenida
   */
  const completeTour = async () => {
    setShowTour(false)
    try {
      await api.post('/auth/complete-onboarding')
    } catch {
      // silencioso — no crítico
    }
  }

  /**
   * Activar tour manualmente
   */
  const triggerTour = () => setShowTour(true)

  // No renderizar nada hasta que Keycloak se inicialice
  if (!initialized) {
    return null // El LoadingComponent de ReactKeycloakProvider se muestra
  }

  // Show loading while restoring session
  const isLoading = isRestoringSession

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        login,
        logout,
        showTour,
        completeTour,
        triggerTour,
        // Exponer métodos de Keycloak para uso avanzado
        keycloak: keycloak.authenticated ? keycloak : null,
        isKeycloakAuth: keycloak.authenticated,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

/**
 * Hook para acceder al contexto de autenticación
 */
export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth debe usarse dentro de un AuthProvider')
  }
  return context
}

// ==========================================
// Helpers
// ==========================================

/**
 * Extrae información del usuario desde el token de Keycloak
 */
function extractUserFromKeycloak(keycloak) {
  if (!keycloak.tokenParsed) return null

  const { sub, realm_access } = keycloak.tokenParsed

  // Extraer rol principal (student, tutor, coordinator)
  const roles = realm_access?.roles || []
  const appRoles = ['student', 'tutor', 'coordinator']
  const role = roles.find(r => appRoles.includes(r))

  return {
    id: sub,
    role: role || null
  }
}
