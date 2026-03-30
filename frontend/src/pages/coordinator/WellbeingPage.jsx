import { useEffect, useState } from 'react'
import api from '../../services/api'
import Spinner from '../../components/ui/Spinner'
import { AlertError } from '../../components/ui/Alert'

const ALERT_CONFIG = {
  null:     { emoji: '🟢', label: 'Sin alertas',      color: 'var(--color-ok-text)',   bg: 'var(--color-ok-bg)',   border: '#81c784' },
  yellow:   { emoji: '🟡', label: 'Alerta moderada',  color: 'var(--color-warn-text)', bg: 'var(--color-warn-bg)', border: '#ffb74d' },
  red:      { emoji: '🔴', label: 'Alerta crítica',   color: 'var(--color-err-text)',  bg: 'var(--color-err-bg)',  border: '#e57373' },
}

const WELLBEING_CONFIG = {
  good:      { emoji: '😊', label: 'Bien',    color: 'var(--color-ok-text)',   bg: 'var(--color-ok-bg)',   border: '#81c784' },
  regular:   { emoji: '😐', label: 'Regular', color: 'var(--color-warn-text)', bg: 'var(--color-warn-bg)', border: '#ffb74d' },
  difficult: { emoji: '😔', label: 'Difícil', color: 'var(--color-err-text)',  bg: 'var(--color-err-bg)',  border: '#e57373' },
}

function AlertBadge({ level }) {
  const cfg = ALERT_CONFIG[level] ?? ALERT_CONFIG['null']
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: '0.375rem',
      padding: '0.25rem 0.625rem', borderRadius: 9999,
      background: cfg.bg, border: `1px solid ${cfg.border}`,
      fontSize: '0.75rem', fontWeight: 600, color: cfg.color,
    }}>
      {cfg.emoji} {cfg.label}
    </span>
  )
}

function WellbeingMiniTimeline({ history }) {
  if (!history.length) return <span style={{ fontSize: '0.8125rem', color: 'var(--color-ink-300)' }}>Sin registros</span>
  return (
    <div style={{ display: 'flex', gap: '0.25rem', flexWrap: 'wrap' }}>
      {history.map((item) => {
        const cfg = WELLBEING_CONFIG[item.wellbeing_status]
        if (!cfg) return null
        return (
          <span key={item.week_number} title={`S${item.week_number}: ${cfg.label}`}
            style={{ fontSize: '1rem', lineHeight: 1, cursor: 'default' }}>
            {cfg.emoji}
          </span>
        )
      })}
    </div>
  )
}

export default function WellbeingPage() {
  const [summary, setSummary] = useState(null)
  const [students, setStudents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [expanded, setExpanded] = useState(null)

  useEffect(() => {
    Promise.all([
      api.get('/logbook/wellbeing/coordinator-summary'),
      api.get('/logbook/wellbeing/students'),
    ])
      .then(([summaryRes, studentsRes]) => {
        setSummary(summaryRes.data)
        setStudents(studentsRes.data)
      })
      .catch(() => setError('Error al cargar el panel de bienestar'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner />

  return (
    <div className="page-enter">
      <div className="section-header">
        <div>
          <h2 className="section-title">Bienestar estudiantil</h2>
          <p className="section-subtitle">Monitoreo confidencial del estado emocional del internado</p>
        </div>
      </div>

      <AlertError>{error}</AlertError>

      {/* Resumen global */}
      {summary && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
          {[
            { key: 'green',  label: 'Sin alertas',     emoji: '🟢', color: 'var(--color-ok-text)',   bg: 'var(--color-ok-bg)',   border: '#81c784' },
            { key: 'yellow', label: 'Alerta moderada', emoji: '🟡', color: 'var(--color-warn-text)', bg: 'var(--color-warn-bg)', border: '#ffb74d' },
            { key: 'red',    label: 'Alerta crítica',  emoji: '🔴', color: 'var(--color-err-text)',  bg: 'var(--color-err-bg)',  border: '#e57373' },
          ].map(({ key, label, emoji, color, bg, border }) => (
            <div key={key} className="card-stat" style={{ background: bg, border: `1px solid ${border}` }}>
              <p style={{ fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color, marginBottom: '0.5rem' }}>
                {emoji} {label}
              </p>
              <p style={{ fontFamily: 'var(--font-display)', fontSize: '2.5rem', fontWeight: 400, color, margin: 0, lineHeight: 1 }}>
                {summary[key]}
              </p>
              <p style={{ fontSize: '0.8125rem', color, opacity: 0.7, margin: 0, marginTop: '0.25rem' }}>estudiantes</p>
            </div>
          ))}
        </div>
      )}

      {/* Lista de estudiantes */}
      <div className="card" style={{ overflow: 'hidden' }}>
        <table className="table">
          <thead>
            <tr>
              <th>Estudiante</th>
              <th>Estado</th>
              <th>Historial (últimas semanas)</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {students.length === 0 ? (
              <tr>
                <td colSpan={4} style={{ textAlign: 'center', padding: '2rem', color: 'var(--color-ink-300)' }}>
                  No hay estudiantes activos
                </td>
              </tr>
            ) : students.map((s) => (
              <>
                <tr key={s.student_id}>
                  <td>
                    <span style={{ fontWeight: 500, color: 'var(--color-ink-900)' }}>{s.student_name}</span>
                  </td>
                  <td><AlertBadge level={s.alert_level} /></td>
                  <td><WellbeingMiniTimeline history={s.history} /></td>
                  <td>
                    <button
                      className="btn btn-ghost btn-sm"
                      onClick={() => setExpanded(expanded === s.student_id ? null : s.student_id)}
                    >
                      {expanded === s.student_id ? 'Ocultar' : 'Ver detalle'}
                    </button>
                  </td>
                </tr>
                {expanded === s.student_id && (
                  <tr key={`${s.student_id}-detail`}>
                    <td colSpan={4} style={{ padding: '0.75rem 1.25rem', background: 'var(--color-ink-50)' }}>
                      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                        {s.history.length === 0
                          ? <span style={{ fontSize: '0.875rem', color: 'var(--color-ink-300)' }}>Sin registros de bienestar aún.</span>
                          : s.history.map((item) => {
                              const cfg = WELLBEING_CONFIG[item.wellbeing_status]
                              if (!cfg) return null
                              return (
                                <div key={item.week_number} style={{
                                  display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.25rem',
                                  padding: '0.625rem 0.75rem', borderRadius: 'var(--radius-md)',
                                  background: cfg.bg, border: `1.5px solid ${cfg.border}`, minWidth: 56,
                                }}>
                                  <span style={{ fontSize: '1.375rem', lineHeight: 1 }}>{cfg.emoji}</span>
                                  <span style={{ fontSize: '0.6875rem', fontWeight: 600, color: cfg.color }}>S{item.week_number}</span>
                                  <span style={{ fontSize: '0.625rem', color: cfg.color, opacity: 0.75 }}>{item.week_start_date}</span>
                                </div>
                              )
                            })}
                      </div>
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>

      {/* Nota de confidencialidad */}
      <p style={{ fontSize: '0.8125rem', color: 'var(--color-ink-300)', marginTop: '1.5rem', textAlign: 'center' }}>
        Los indicadores de bienestar son confidenciales. Los estudiantes no saben que se generaron alertas.
      </p>
    </div>
  )
}
