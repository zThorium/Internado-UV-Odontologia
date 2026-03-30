import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { useAuth } from './AuthContext'

const ThemeContext = createContext(null)
const THEME_KEY_PREFIX = 'ui_theme'

function themeKeyForUser(userId) {
  return `${THEME_KEY_PREFIX}:${userId || 'guest'}`
}

/**
 * Limpia claves de tema antiguas o con valores inválidos.
 * Previene que valores corruptos de sesiones anteriores afecten el tema.
 */
function cleanStaleThemeKeys() {
  try {
    Object.keys(localStorage)
      .filter((k) => k.startsWith(THEME_KEY_PREFIX))
      .forEach((k) => {
        const v = localStorage.getItem(k)
        if (v !== 'dark' && v !== 'light') localStorage.removeItem(k)
      })
  } catch {
    // silenciar
  }
}

/**
 * Lee la preferencia guardada de forma síncrona.
 * Solo lee preferencia si hay un userId activo (usuario logueado).
 * Sin sesión activa siempre devuelve 'light' — el login nunca es oscuro.
 */
function readSavedTheme(userId) {
  cleanStaleThemeKeys()
  if (!userId) return 'light'
  try {
    const saved = localStorage.getItem(themeKeyForUser(userId))
    if (saved === 'dark' || saved === 'light') return saved
  } catch {
    // localStorage no disponible
  }
  return 'light'
}

/**
 * Creates a smooth circular reveal animation when switching themes
 */
function animateThemeTransition(isDarkMode, callback) {
  // Check if browser supports View Transitions API
  if (!document.startViewTransition) {
    callback()
    return
  }

  // Use View Transitions API for smooth animation
  document.startViewTransition(() => {
    callback()
  })
}

export function ThemeProvider({ children }) {
  const { user } = useAuth()

  // Inicialización síncrona — evita flash al recargar
  const [theme, setTheme] = useState(() => readSavedTheme(user?.id))
  const [isTransitioning, setIsTransitioning] = useState(false)

  // Cuando cambia el usuario (login/logout), migrar preferencia sin pisar
  useEffect(() => {
    const saved = readSavedTheme(user?.id)
    setTheme(saved)
  }, [user?.id])

  // Aplicar al DOM y persistir cada vez que cambia el tema
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    try {
      localStorage.setItem(themeKeyForUser(user?.id), theme)
    } catch {
      // silenciar errores de localStorage
    }
  }, [theme, user?.id])

  const toggleTheme = () => {
    setIsTransitioning(true)
    
    animateThemeTransition(theme === 'light', () => {
      setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))
    })

    // Reset transition state after animation completes
    setTimeout(() => {
      setIsTransitioning(false)
    }, 500)
  }

  const value = useMemo(() => ({
    theme,
    isDark: theme === 'dark',
    isTransitioning,
    toggleTheme,
  }), [theme, isTransitioning])

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme debe usarse dentro de ThemeProvider')
  return ctx
}
