import { useNavigate } from 'react-router-dom'
import { CheckCircle, ArrowLeft } from 'lucide-react'

export default function ConfirmationPage() {
  const navigate = useNavigate()

  return (
    <div className="page-enter" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
      <div className="card" style={{ padding: '3rem 2.5rem', textAlign: 'center', maxWidth: 380, width: '100%' }}>
        {/* Icono con animación */}
        <div style={{
          width: 64, height: 64, borderRadius: '50%',
          background: 'var(--color-ok-bg)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          margin: '0 auto 1.25rem',
          animation: 'pageEnter 0.4s var(--ease-out) both',
        }}>
          <CheckCircle size={32} style={{ color: 'var(--color-ok-text)' }} />
        </div>

        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.375rem', fontWeight: 500, color: 'var(--color-ink-900)', marginBottom: '0.5rem' }}>
          Evaluación enviada
        </h2>
        <p style={{ fontSize: '0.9rem', color: 'var(--color-ink-500)', marginBottom: '1.75rem', lineHeight: 1.6 }}>
          La evaluación ha sido registrada exitosamente y está disponible para el coordinador.
        </p>

        <button
          onClick={() => navigate('/tutor')}
          className="btn btn-secondary"
          style={{ width: '100%', justifyContent: 'center' }}
        >
          <ArrowLeft size={15} /> Volver a mis estudiantes
        </button>
      </div>
    </div>
  )
}
