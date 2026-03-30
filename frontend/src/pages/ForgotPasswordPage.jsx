import { useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'
import { AlertError, AlertSuccess } from '../components/ui/Alert'
import { ArrowLeft } from 'lucide-react'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setMessage('')
    setError('')
    setLoading(true)
    try {
      await api.post('/auth/forgot-password', { email })
      setMessage('Si el correo existe, recibirás un enlace de recuperación en breve.')
    } catch {
      setError('Ocurrió un error. Intenta nuevamente.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--color-bg-base)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem',
    }}>
      <div style={{ width: '100%', maxWidth: 400 }} className="slide-up">
        <Link
          to="/login"
          style={{ display: 'inline-flex', alignItems: 'center', gap: '0.375rem', fontSize: '0.875rem', color: 'var(--color-ink-500)', marginBottom: '2rem', fontWeight: 500 }}
        >
          <ArrowLeft size={14} /> Volver al inicio de sesión
        </Link>

        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '1.75rem', fontWeight: 500, letterSpacing: '-0.02em', marginBottom: '0.5rem' }}>
          Recuperar contraseña
        </h1>
        <p style={{ fontSize: '0.9375rem', color: 'var(--color-ink-500)', marginBottom: '2rem' }}>
          Te enviaremos un enlace a tu correo institucional.
        </p>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="field">
            <label htmlFor="email" className="label">Correo electrónico</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="tu@uv.cl"
              className="input"
            />
          </div>

          <AlertError>{error}</AlertError>
          <AlertSuccess>{message}</AlertSuccess>

          <button type="submit" disabled={loading} className="btn btn-primary btn-lg" style={{ width: '100%' }}>
            {loading ? <><span className="spinner" style={{ width: '1rem', height: '1rem' }} /> Enviando...</> : 'Enviar enlace'}
          </button>
        </form>
      </div>
    </div>
  )
}
