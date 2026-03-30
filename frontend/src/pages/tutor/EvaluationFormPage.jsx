import { useState } from 'react'
import { useParams, useSearchParams, useNavigate } from 'react-router-dom'
import api from '../../services/api'
import { AlertError } from '../../components/ui/Alert'
import { ArrowLeft, Send, CheckCircle } from 'lucide-react'

const DIMENSIONS = [
  'Actitud profesional',
  'Habilidades clínicas',
  'Comunicación con pacientes',
  'Puntualidad y asistencia',
  'Trabajo en equipo',
]

const SCALE = [
  { value: 'achieved',     label: 'Logrado',      cls: 'selected-green' },
  { value: 'in_progress',  label: 'En progreso',  cls: 'selected-yellow' },
  { value: 'not_achieved', label: 'No logrado',   cls: 'selected-red' },
]

export default function EvaluationFormPage() {
  const { assignment_id } = useParams()
  const [searchParams] = useSearchParams()
  const student_id = searchParams.get('student_id')
  const navigate = useNavigate()

  const [ratings, setRatings] = useState({})
  const [periodLabel, setPeriodLabel] = useState('')
  const [overallComment, setOverallComment] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const allRated = DIMENSIONS.every((d) => ratings[d])
  const ratedCount = Object.keys(ratings).length

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!allRated || !periodLabel.trim()) return
    setSubmitting(true)
    setError(null)
    const payload = {
      assignment_id,
      student_id,
      period_label: periodLabel.trim(),
      overall_comment: overallComment.trim() || null,
      items: DIMENSIONS.map((d) => ({ dimension: d, score: ratings[d], comment: null })),
    }
    try {
      await api.post('/evaluations', payload)
      navigate('/tutor/confirmation')
    } catch {
      setError('Error al enviar la evaluación. Intenta nuevamente.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="page-enter" style={{ maxWidth: 640 }}>
      <button onClick={() => navigate('/tutor')} className="btn btn-ghost btn-sm"
        style={{ marginBottom: '1rem', marginLeft: '-0.5rem' }}>
        <ArrowLeft size={15} /> Volver
      </button>

      <div style={{ marginBottom: '1.75rem' }}>
        <h2 className="section-title">Formulario de evaluación</h2>
        <p className="section-subtitle">Completa todos los criterios para enviar la evaluación</p>
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {/* Periodo */}
        <div className="card" style={{ padding: '1.5rem' }}>
          <div className="field">
            <label className="label">Periodo <span style={{ color: 'var(--color-err-text)' }}>*</span></label>
            <input
              type="text"
              value={periodLabel}
              onChange={(e) => setPeriodLabel(e.target.value)}
              placeholder="Ej: Semestre 1 - 2025"
              required
              className="input"
            />
          </div>
        </div>

        {/* Criterios */}
        <div className="card" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1rem', fontWeight: 500, color: 'var(--color-ink-700)', margin: 0 }}>
              Criterios de evaluación
            </h3>
            <span style={{ fontSize: '0.8125rem', color: 'var(--color-ink-500)' }}>
              {ratedCount} / {DIMENSIONS.length} evaluados
            </span>
          </div>

          {/* Progress mini */}
          <div className="progress-track" style={{ marginBottom: '1.25rem' }}>
            <div className="progress-fill" style={{
              width: `${(ratedCount / DIMENSIONS.length) * 100}%`,
              background: 'var(--color-uv-500)',
            }} />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {DIMENSIONS.map((dim) => (
              <div key={dim}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.625rem' }}>
                  {ratings[dim] && <CheckCircle size={14} style={{ color: 'var(--color-ok-text)', flexShrink: 0 }} />}
                  <p style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--color-ink-700)', margin: 0 }}>{dim}</p>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                  {SCALE.map(({ value, label, cls }) => (
                    <label key={value} className={`radio-card ${ratings[dim] === value ? cls : ''}`}>
                      <input
                        type="radio"
                        name={dim}
                        value={value}
                        checked={ratings[dim] === value}
                        onChange={() => setRatings((prev) => ({ ...prev, [dim]: value }))}
                        style={{ display: 'none' }}
                      />
                      {label}
                    </label>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Comentario */}
        <div className="card" style={{ padding: '1.5rem' }}>
          <div className="field">
            <label className="label">
              Comentario general
              <span style={{ color: 'var(--color-ink-300)', fontWeight: 400, marginLeft: '0.25rem' }}>(opcional)</span>
            </label>
            <textarea
              value={overallComment}
              onChange={(e) => setOverallComment(e.target.value)}
              rows={4}
              className="input"
              style={{ resize: 'none' }}
              placeholder="Observaciones adicionales sobre el desempeño del estudiante..."
            />
          </div>
        </div>

        <AlertError>{error}</AlertError>

        <button
          type="submit"
          disabled={submitting || !allRated || !periodLabel.trim()}
          className="btn btn-primary btn-lg"
        >
          <Send size={16} />
          {submitting ? 'Enviando...' : 'Enviar evaluación'}
        </button>
      </form>
    </div>
  )
}
