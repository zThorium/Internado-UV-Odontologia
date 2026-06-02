import { useState } from 'react'
import { useParams, useSearchParams, useNavigate } from 'react-router-dom'
import api from '../../services/api'
import { AlertError } from '../../components/ui/Alert'
import { ArrowLeft, Send, CheckCircle } from 'lucide-react'

const DIMENSIONS = [
  'Diagnóstico y evaluación de riesgo',
  'Solicitud de exámenes e indicaciones',
  'Planificación y diseño del plan de tratamiento',
  'Realización de procedimientos',
  'Manejo de emergencias',
  'Salud pública y administración',
  'Competencias genéricas (trabajo en equipo, comunicación, etc.)',
]

const SCALE = [
  { value: 1, label: '1', cls: 'selected-red' },
  { value: 2, label: '2', cls: 'selected-red' },
  { value: 3, label: '3', cls: 'selected-yellow' },
  { value: 4, label: '4', cls: 'selected-green' },
  { value: 5, label: '5', cls: 'selected-green' },
]

export default function EvaluationFormPage() {
  const { assignment_id } = useParams()
  const [searchParams] = useSearchParams()
  const student_id = searchParams.get('student_id')
  const studentName = searchParams.get('name') || 'Estudiante'
  const tutorName = searchParams.get('tutor') || 'Tutor clínico'
  const clinicalSite = searchParams.get('site') || 'Establecimiento no informado'
  const navigate = useNavigate()

  const [ratings, setRatings] = useState({})
  const [periodLabel, setPeriodLabel] = useState('semester_1')
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
        <p className="section-subtitle">Completa la rúbrica periódica para dejar registro objetivo del desempeño</p>
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <div className="card" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.85rem' }}>
            <div>
              <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--color-ink-500)' }}>Estudiante</p>
              <p style={{ margin: '0.15rem 0 0', fontWeight: 600, color: 'var(--color-ink-800)' }}>{studentName}</p>
            </div>
            <div>
              <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--color-ink-500)' }}>Tutor clínico</p>
              <p style={{ margin: '0.15rem 0 0', fontWeight: 600, color: 'var(--color-ink-800)' }}>{tutorName}</p>
            </div>
            <div style={{ gridColumn: '1 / -1' }}>
              <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--color-ink-500)' }}>Establecimiento de salud</p>
              <p style={{ margin: '0.15rem 0 0', fontWeight: 600, color: 'var(--color-ink-800)' }}>{clinicalSite}</p>
            </div>
          </div>
        </div>

        {/* Periodo */}
        <div className="card" style={{ padding: '1.5rem' }}>
          <div className="field">
            <label className="label">Periodo <span style={{ color: 'var(--color-err-text)' }}>*</span></label>
            <select
              value={periodLabel}
              onChange={(e) => setPeriodLabel(e.target.value)}
              required
              className="input"
            >
              <option value="semester_1">Semestre 1</option>
              <option value="semester_2">Semestre 2</option>
            </select>
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
