import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { AlertError } from '../components/ui/Alert'

const RECAPTCHA_SITE_KEY = '6Ldh5pksAAAAAN1daWsi6zKicrHUU8QdzLL9cdPo'

export default function LoginPage() {
  const { login, user, isLoading } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const recaptchaRef = useRef(null)
  const [recaptchaLoaded, setRecaptchaLoaded] = useState(false)

  // Redirect to dashboard if already logged in
  useEffect(() => {
    if (!isLoading && user) {
      const dashboards = {
        student: '/student',
        tutor: '/tutor',
        coordinator: '/coordinator',
      }
      navigate(dashboards[user.role] || '/student', { replace: true })
    }
  }, [user, isLoading, navigate])

  // Load reCAPTCHA script
  useEffect(() => {
    // Callback que se ejecuta cuando reCAPTCHA está listo
    window.onRecaptchaLoad = () => {
      setRecaptchaLoaded(true)
    }

    const loadRecaptcha = () => {
      // Si ya está cargado, marcar como listo
      if (window.grecaptcha && window.grecaptcha.render) {
        setRecaptchaLoaded(true)
        return
      }

      // Si el script ya existe, no agregarlo de nuevo
      if (document.querySelector('script[src*="recaptcha"]')) {
        return
      }

      const script = document.createElement('script')
      script.src = `https://www.google.com/recaptcha/api.js?onload=onRecaptchaLoad&render=explicit`
      script.async = true
      script.defer = true
      document.head.appendChild(script)
    }

    loadRecaptcha()

    return () => {
      delete window.onRecaptchaLoad
    }
  }, [])

  // Render reCAPTCHA widget when loaded
  useEffect(() => {
    if (recaptchaLoaded && recaptchaRef.current && !recaptchaRef.current.hasChildNodes()) {
      try {
        window.grecaptcha.render(recaptchaRef.current, {
          sitekey: RECAPTCHA_SITE_KEY,
          theme: 'light',
          size: 'normal',
        })
      } catch (error) {
        console.error('Error renderizando reCAPTCHA:', error)
      }
    }
  }, [recaptchaLoaded])

  const handleLogin = async (e) => {
    e.preventDefault()
    setError('')
    
    // Obtener token de reCAPTCHA (opcional si está desactivado en backend)
    let recaptchaToken = null
    if (window.grecaptcha && recaptchaRef.current) {
      try {
        recaptchaToken = window.grecaptcha.getResponse()
        // Solo requerir captcha si está cargado y visible
        // Si el backend tiene RECAPTCHA_ENABLED=false, aceptará null
      } catch (err) {
        console.error('Error obteniendo token de reCAPTCHA:', err)
      }
    }
    
    setLoading(true)
    try {
      const role = await login(email, password, recaptchaToken)

      // Navigate to appropriate dashboard based on role
      const dashboards = {
        student: '/student',
        tutor: '/tutor',
        coordinator: '/coordinator',
      }
      navigate(dashboards[role] || '/login')
    } catch (error) {
      // Reset reCAPTCHA en caso de error
      if (window.grecaptcha) {
        window.grecaptcha.reset()
      }
      
      if (error?.response?.status === 429) {
        setError('Demasiados intentos. Espera un momento y vuelve a intentar.')
      } else if (error?.response?.status === 503) {
        setError('Servicio de autenticación no disponible. Intenta en unos segundos.')
      } else if (!error?.response) {
        setError('No se pudo conectar al servidor. Verifica que backend esté activo en http://localhost:8000.')
      } else if (error?.response?.data?.detail?.includes('reCAPTCHA')) {
        setError('Verificación de seguridad fallida. Por favor, intenta nuevamente.')
      } else {
        setError(error?.response?.data?.detail || 'Error al iniciar sesión.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-root">

      {/* ── Panel izquierdo — imagen (solo desktop) ───────────────────── */}
      <div className="login-hero">
        <img
          src="/Component 1.png"
          alt="Facultad de Odontología UV"
          style={{
            position: 'absolute', inset: 0,
            width: '100%', height: '100%',
            objectFit: 'cover', objectPosition: 'center',
          }}
        />
        {/* Overlay azul UV */}
        <div style={{
          position: 'absolute', inset: 0,
          background: 'linear-gradient(160deg, rgb(26 58 107 / 0.72) 0%, rgb(14 32 58 / 0.55) 60%, rgb(10 22 40 / 0.38) 100%)',
        }} />

        <div style={{
          position: 'relative', zIndex: 1,
          height: '100%', display: 'flex', flexDirection: 'column',
          justifyContent: 'space-between', padding: '2.5rem 3rem',
        }}>
          <div />
          <div>
            <h1 style={{
              fontFamily: 'var(--font-display)',
              fontSize: '2.75rem', fontWeight: 600,
              color: '#ffffff', lineHeight: 1.15,
              letterSpacing: '-0.03em',
              margin: '0 0 0.875rem',
              textShadow: '0 2px 12px rgb(0 0 0 / 0.25)',
            }}>
              Internado<br />Odontología UV
            </h1>
            <p style={{
              fontSize: '1rem', color: 'rgb(255 255 255 / 0.75)',
              margin: 0, lineHeight: 1.5,
            }}>
              Acceso a plataforma de gestión<br />Odontológica
            </p>
          </div>

          {/* Logo UV — única aparición */}
          <div style={{
            display: 'inline-flex',
            background: 'rgb(255 255 255 / 0.10)',
            backdropFilter: 'blur(12px)',
            border: '1px solid rgb(255 255 255 / 0.18)',
            borderRadius: '14px',
            padding: '0.75rem 1.25rem',
            alignSelf: 'flex-start',
          }}>
            <img
              src="/uv_logo 1.png"
              alt="Universidad de Valparaíso"
              style={{ height: 44, filter: 'brightness(0) invert(1)', opacity: 0.92 }}
            />
          </div>
        </div>
      </div>

      {/* ── Panel derecho — formulario ─────────────────────────────────── */}
      <div className="login-form-panel">

        {/* Logo UV visible solo en móvil (encima del formulario) */}
        <div className="login-mobile-logo">
          <img
            src="/uv_logo 1.png"
            alt="Universidad de Valparaíso"
            style={{ height: 36, opacity: 0.85 }}
          />
        </div>

        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ width: '100%', maxWidth: 360 }} className="slide-up">

            <div style={{ marginBottom: '2.25rem' }}>
              <h2 style={{
                fontFamily: 'var(--font-display)',
                fontSize: '1.75rem', fontWeight: 500,
                color: '#0f1f2e', letterSpacing: '-0.025em',
                marginBottom: '0.375rem',
              }}>
                Bienvenido
              </h2>
              <p style={{ fontSize: '0.9375rem', color: '#3d6480', margin: 0 }}>
                Ingresa con tu cuenta institucional
              </p>
            </div>

            <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1.125rem' }}>
              <div className="field">
                <label htmlFor="email" className="label">Cuenta</label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  placeholder="tu@uv.cl"
                  className="input"
                  style={{ background: '#f5f5f7', border: '1px solid #e0e0e5' }}
                />
              </div>

              <div className="field">
                <label htmlFor="password" className="label">Contraseña</label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder="••••••••"
                  className="input"
                  style={{ background: '#f5f5f7', border: '1px solid #e0e0e5' }}
                />
              </div>

              <AlertError>{error}</AlertError>

              {/* reCAPTCHA widget */}
              <div style={{ display: 'flex', justifyContent: 'center', marginTop: '0.5rem' }}>
                <div ref={recaptchaRef}></div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn btn-primary btn-lg"
                style={{ marginTop: '0.75rem', width: '100%', background: '#1a3a6b' }}
              >
                {loading
                  ? <><span className="spinner" style={{ width: '1rem', height: '1rem' }} /> Validando...</>
                  : 'Ingresar'}
              </button>
            </form>
          </div>
        </div>

        {/* Footer copyright */}
        <div style={{
          borderTop: '1px solid #e8e8ed',
          paddingTop: '1.25rem',
          textAlign: 'center',
        }}>
          <p style={{ fontSize: '0.75rem', color: '#8a8a9a', margin: 0, lineHeight: 1.6 }}>
            © {new Date().getFullYear()} Universidad de Valparaíso — Facultad de Odontología
          </p>
          <p style={{ fontSize: '0.6875rem', color: '#adadbd', margin: '0.125rem 0 0' }}>
            Plataforma de gestión del Internado Odontológico · Todos los derechos reservados
          </p>
        </div>
      </div>
    </div>
  )
}
