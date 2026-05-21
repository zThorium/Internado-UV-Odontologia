import { useEffect, useMemo, useState } from 'react'
import api from '../../services/api'
import Spinner from '../../components/ui/Spinner'
import { AlertError } from '../../components/ui/Alert'
import EmptyState from '../../components/ui/EmptyState'
import { HeartPulse, Search, ShieldCheck, TriangleAlert, Siren, Filter, ChevronDown, ChevronUp } from 'lucide-react'

const ALERT_CONFIG = {
  null: {
    label: 'Sin alertas',
    color: 'var(--color-ok-text)',
    bg: 'var(--color-ok-bg)',
    border: '#81c784',
  },
  yellow: {
    label: 'Alerta moderada',
    color: 'var(--color-warn-text)',
    bg: 'var(--color-warn-bg)',
    border: '#ffb74d',
  },
  red: {
    label: 'Alerta crítica',
    color: 'var(--color-err-text)',
    bg: 'var(--color-err-bg)',
    border: '#e57373',
  },
}

const WELLBEING_CONFIG = {
  good: {
    label: 'Bien',
    color: 'var(--color-ok-text)',
    bg: 'var(--color-ok-bg)',
    border: '#81c784',
  },
  regular: {
    label: 'Regular',
    color: 'var(--color-warn-text)',
    bg: 'var(--color-warn-bg)',
    border: '#ffb74d',
  },
  difficult: {
    label: 'Difícil',
    color: 'var(--color-err-text)',
    bg: 'var(--color-err-bg)',
    border: '#e57373',
  },
}

const SCORE_BY_STATUS = {
  good: 0,
  regular: 50,
  difficult: 100,
}

function AlertBadge({ level }) {
  const cfg = ALERT_CONFIG[level] ?? ALERT_CONFIG.null
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.375rem',
        padding: '0.25rem 0.625rem',
        borderRadius: 9999,
        background: cfg.bg,
        border: `1px solid ${cfg.border}`,
        fontSize: '0.75rem',
        fontWeight: 600,
        color: cfg.color,
      }}
    >
      {cfg.label}
    </span>
  )
}

function WellbeingStrip({ history }) {
  if (!history.length) {
    return <span style={{ fontSize: '0.8125rem', color: 'var(--color-ink-300)' }}>Sin registros</span>
  }

  return (
    <div style={{ display: 'flex', gap: '0.25rem', flexWrap: 'wrap' }}>
      {history.map((item) => {
        const cfg = WELLBEING_CONFIG[item.wellbeing_status]
        if (!cfg) return null

        return (
          <span
            key={item.week_number}
            title={`Semana ${item.week_number}: ${cfg.label}`}
            style={{
              width: 14,
              height: 14,
              borderRadius: 9999,
              background: cfg.border,
              border: `1px solid ${cfg.border}`,
              display: 'inline-block',
            }}
          />
        )
      })}
    </div>
  )
}

function ScoreBar({ value }) {
  return (
    <div style={{ width: '100%' }}>
      <div
        style={{
          width: '100%',
          height: 8,
          borderRadius: 999,
          background: 'var(--color-ink-100)',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${value}%`,
            height: '100%',
            background: value >= 70
              ? 'var(--color-err-text)'
              : value >= 35
                ? 'var(--color-warn-text)'
                : 'var(--color-ok-text)',
          }}
        />
      </div>
      <p style={{ marginTop: '0.25rem', fontSize: '0.72rem', color: 'var(--color-ink-500)' }}>
        Riesgo estimado: {Math.round(value)}%
      </p>
    </div>
  )
}

function computeRiskScore(history) {
  if (!history.length) return 0
  const total = history.reduce((acc, item) => acc + (SCORE_BY_STATUS[item.wellbeing_status] ?? 0), 0)
  return total / history.length
}

export default function WellbeingPage() {
  const [summary, setSummary] = useState(null)
  const [students, setStudents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [expanded, setExpanded] = useState(null)
  const [search, setSearch] = useState('')
  const [alertFilter, setAlertFilter] = useState('all')

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

  const studentsWithScore = useMemo(
    () => students.map((student) => ({
      ...student,
      riskScore: computeRiskScore(student.history || []),
    })),
    [students]
  )

  const filteredStudents = useMemo(() => {
    const normalized = search.trim().toLowerCase()

    return studentsWithScore
      .filter((student) => {
        const bySearch = !normalized || student.student_name.toLowerCase().includes(normalized)
        const byAlert = alertFilter === 'all'
          || (alertFilter === 'none' && !student.alert_level)
          || student.alert_level === alertFilter
        return bySearch && byAlert
      })
      .sort((a, b) => {
        if ((b.riskScore || 0) !== (a.riskScore || 0)) return (b.riskScore || 0) - (a.riskScore || 0)
        return a.student_name.localeCompare(b.student_name)
      })
  }, [studentsWithScore, search, alertFilter])

  if (loading) return <Spinner />

  const totalStudents = students.length
  const redCount = summary?.red ?? 0
  const yellowCount = summary?.yellow ?? 0
  const greenCount = summary?.green ?? 0
  const attentionCount = redCount + yellowCount

  return (
    <div className="page-enter">
      <div className="section-header">
        <div>
          <h2 className="section-title">Bienestar estudiantil</h2>
          <p className="section-subtitle">Monitoreo confidencial con foco en detección temprana</p>
        </div>
      </div>

      <AlertError>{error}</AlertError>

      <div
        className="card"
        style={{
          padding: '1rem 1.25rem',
          marginBottom: '1rem',
          background: 'linear-gradient(135deg, var(--color-uv-50), var(--color-bg-surface))',
          border: '1px solid var(--color-ink-100)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.6rem' }}>
          <HeartPulse size={16} style={{ color: 'var(--color-uv-600)' }} />
          <h3 style={{ margin: 0, fontSize: '1rem', color: 'var(--color-ink-800)' }}>Panel ejecutivo de bienestar</h3>
        </div>
        <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--color-ink-500)' }}>
          Priorización automática de estudiantes para seguimiento coordinador.
        </p>
      </div>

      {summary && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '0.75rem',
            marginBottom: '1rem',
          }}
        >
          <div className="card-stat">
            <p className="text-label" style={{ marginBottom: '0.4rem' }}>Total estudiantes</p>
            <p className="text-heading" style={{ marginBottom: '0.15rem' }}>{totalStudents}</p>
            <p className="text-small">Con historial de bienestar</p>
          </div>

          <div className="card-stat" style={{ background: 'var(--color-ok-bg)', border: '1px solid #81c784' }}>
            <p className="text-label" style={{ marginBottom: '0.4rem', color: 'var(--color-ok-text)' }}>Sin alertas</p>
            <p className="text-heading" style={{ marginBottom: '0.15rem', color: 'var(--color-ok-text)' }}>{greenCount}</p>
            <p className="text-small" style={{ color: 'var(--color-ok-text)' }}>
              {totalStudents ? Math.round((greenCount / totalStudents) * 100) : 0}% del total
            </p>
          </div>

          <div className="card-stat" style={{ background: 'var(--color-warn-bg)', border: '1px solid #ffb74d' }}>
            <p className="text-label" style={{ marginBottom: '0.4rem', color: 'var(--color-warn-text)' }}>Alerta moderada</p>
            <p className="text-heading" style={{ marginBottom: '0.15rem', color: 'var(--color-warn-text)' }}>{yellowCount}</p>
            <p className="text-small" style={{ color: 'var(--color-warn-text)' }}>Requieren monitoreo semanal</p>
          </div>

          <div className="card-stat" style={{ background: 'var(--color-err-bg)', border: '1px solid #e57373' }}>
            <p className="text-label" style={{ marginBottom: '0.4rem', color: 'var(--color-err-text)' }}>Alerta crítica</p>
            <p className="text-heading" style={{ marginBottom: '0.15rem', color: 'var(--color-err-text)' }}>{redCount}</p>
            <p className="text-small" style={{ color: 'var(--color-err-text)' }}>Priorización inmediata</p>
          </div>
        </div>
      )}

      <div className="card" style={{ padding: '1rem 1.25rem', marginBottom: '1rem' }}>
        <div className="form-grid-2">
          <div style={{ position: 'relative' }}>
            <Search size={14} style={{ position: 'absolute', top: 12, left: 10, color: 'var(--color-ink-300)' }} />
            <input
              className="input"
              style={{ paddingLeft: '2rem' }}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Buscar estudiante..."
            />
          </div>

          <select className="input" value={alertFilter} onChange={(e) => setAlertFilter(e.target.value)}>
            <option value="all">Todas las alertas</option>
            <option value="none">Sin alertas</option>
            <option value="yellow">Alerta moderada</option>
            <option value="red">Alerta crítica</option>
          </select>
        </div>

        <div style={{ marginTop: '0.6rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Filter size={13} style={{ color: 'var(--color-ink-400)' }} />
          <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--color-ink-500)' }}>
            Mostrando {filteredStudents.length} de {students.length} estudiantes.
          </p>
        </div>
      </div>

      {filteredStudents.length === 0 ? (
        <div className="card">
          <EmptyState
            icon={HeartPulse}
            title="Sin resultados"
            description="No hay estudiantes para los filtros seleccionados."
          />
        </div>
      ) : (
        <div style={{ display: 'grid', gap: '0.75rem' }}>
          {filteredStudents.map((student) => {
            const latest = (student.history || [])[0]
            const latestCfg = latest ? WELLBEING_CONFIG[latest.wellbeing_status] : null

            return (
              <div key={student.student_id} className="card" style={{ padding: '0.95rem 1rem' }}>
                <div
                  style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: '0.75rem',
                    alignItems: 'flex-start',
                  }}
                >
                  <div style={{ flex: '1 1 160px', minWidth: 0 }}>
                    <p style={{ margin: 0, fontWeight: 600, color: 'var(--color-ink-900)' }}>{student.student_name}</p>
                    <div style={{ marginTop: '0.35rem', display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
                      <AlertBadge level={student.alert_level} />
                      {latestCfg && (
                        <span
                          style={{
                            fontSize: '0.72rem',
                            fontWeight: 600,
                            padding: '0.2rem 0.45rem',
                            borderRadius: 999,
                            color: latestCfg.color,
                            background: latestCfg.bg,
                            border: `1px solid ${latestCfg.border}`,
                          }}
                        >
                          Último estado: {latestCfg.label}
                        </span>
                      )}
                    </div>
                  </div>

                  <div style={{ flex: '1 1 120px', minWidth: 0 }}>
                    <p style={{ margin: '0 0 0.35rem', fontSize: '0.76rem', color: 'var(--color-ink-500)' }}>Historial reciente</p>
                    <WellbeingStrip history={student.history || []} />
                  </div>

                  <div style={{ flex: '1 1 140px', minWidth: 0 }}>
                    <p style={{ margin: '0 0 0.35rem', fontSize: '0.76rem', color: 'var(--color-ink-500)' }}>Índice de riesgo</p>
                    <ScoreBar value={student.riskScore || 0} />
                  </div>

                  <div style={{ flexShrink: 0 }}>
                    <button
                      className="btn btn-ghost btn-sm"
                      onClick={() => setExpanded(expanded === student.student_id ? null : student.student_id)}
                    >
                      {expanded === student.student_id ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                      {expanded === student.student_id ? 'Ocultar' : 'Detalle'}
                    </button>
                  </div>
                </div>

                {expanded === student.student_id && (
                  <div
                    style={{
                      marginTop: '0.8rem',
                      paddingTop: '0.8rem',
                      borderTop: '1px solid var(--color-ink-100)',
                    }}
                  >
                    {(student.history || []).length === 0 ? (
                      <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--color-ink-400)' }}>
                        Sin registros de bienestar todavía.
                      </p>
                    ) : (
                      <div style={{ display: 'flex', gap: '0.45rem', flexWrap: 'wrap' }}>
                        {student.history.map((item) => {
                          const cfg = WELLBEING_CONFIG[item.wellbeing_status]
                          if (!cfg) return null

                          return (
                            <div
                              key={`${student.student_id}-${item.week_number}`}
                              style={{
                                padding: '0.45rem 0.6rem',
                                borderRadius: 'var(--radius-md)',
                                border: `1px solid ${cfg.border}`,
                                background: cfg.bg,
                                minWidth: 92,
                              }}
                            >
                              <p style={{ margin: 0, fontSize: '0.68rem', fontWeight: 700, color: cfg.color }}>
                                Semana {item.week_number}
                              </p>
                              <p style={{ margin: '0.15rem 0 0', fontSize: '0.78rem', color: cfg.color }}>
                                {cfg.label}
                              </p>
                              <p style={{ margin: '0.05rem 0 0', fontSize: '0.64rem', color: cfg.color, opacity: 0.85 }}>
                                {item.week_start_date}
                              </p>
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      <div className="card" style={{ marginTop: '1rem', padding: '0.8rem 1rem', background: 'var(--color-ink-50)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.25rem' }}>
          {attentionCount > 0 ? <TriangleAlert size={14} style={{ color: 'var(--color-warn-text)' }} /> : <ShieldCheck size={14} style={{ color: 'var(--color-ok-text)' }} />}
          <p style={{ margin: 0, fontSize: '0.82rem', fontWeight: 600, color: 'var(--color-ink-700)' }}>
            Nota de confidencialidad
          </p>
        </div>
        <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--color-ink-500)' }}>
          Los indicadores de bienestar son confidenciales y orientan apoyo académico temprano. {attentionCount > 0 && (
            <span style={{ fontWeight: 600 }}> Hay {attentionCount} estudiante(s) que requieren seguimiento prioritario.</span>
          )}
        </p>
      </div>

      <div style={{ marginTop: '0.8rem', display: 'flex', justifyContent: 'flex-end' }}>
        <span className="badge badge-red" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
          <Siren size={12} /> Uso interno coordinador
        </span>
      </div>
    </div>
  )
}
