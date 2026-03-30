import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import api from '../../services/api'
import Spinner from '../../components/ui/Spinner'
import { AlertError } from '../../components/ui/Alert'
import { AlertTriangle, CheckCircle, ChevronDown, ChevronUp, X, BookOpen, Heart, ClipboardList, Calendar, ShieldAlert, AlertCircle, CheckCircle2 } from 'lucide-react'

// ── Configuración visual del semáforo ────────────────────────────────────────
const LIGHT = {
  red:    { label: 'Crítico',      icon: AlertCircle, color: 'var(--color-err-text)',  bg: '#fff0f0', border: '#fca5a5', weight: 0 },
  yellow: { label: 'En atención',  icon: AlertTriangle, color: 'var(--color-warn-text)', bg: '#fffbeb', border: '#fcd34d', weight: 1 },
  green:  { label: 'Sin alertas',  icon: CheckCircle2, color: 'var(--color-ok-text)',   bg: '#f0fdf4', border: '#86efac', weight: 2 },
}

const ALERT_TYPE_CONFIG = {
  no_bitacora:    { icon: BookOpen, color: '#3b82f6' },
  low_wellbeing:  { icon: Heart, color: '#ec4899' },
  no_evaluation:  { icon: ClipboardList, color: '#8b5cf6' },
  absences:       { icon: Calendar, color: '#f59e0b' },
  incident_report: { icon: ShieldAlert, color: '#dc2626' },
}

const FILTERS = [
  { key: 'all',    label: 'Todos', icon: null },
  { key: 'red',    label: 'Críticos', icon: AlertCircle },
  { key: 'yellow', label: 'En atención', icon: AlertTriangle },
  { key: 'green',  label: 'Sin alertas', icon: CheckCircle2 },
]

// ── Componente semáforo ───────────────────────────────────────────────────────
function TrafficBadge({ level }) {
  const cfg = LIGHT[level] ?? LIGHT.green
  const Icon = cfg.icon
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: '0.375rem',
      padding: '0.3rem 0.75rem', borderRadius: 9999,
      background: cfg.bg, border: `1.5px solid ${cfg.border}`,
      fontSize: '0.8125rem', fontWeight: 700, color: cfg.color,
      letterSpacing: '0.01em',
    }}>
      <Icon size={14} /> {cfg.label}
    </span>
  )
}

// ── Componente alerta individual ──────────────────────────────────────────────
function AlertRow({ alert, onResolve }) {
  const [note, setNote] = useState('')
  const [showNote, setShowNote] = useState(false)
  const [resolving, setResolving] = useState(false)

  const isRed = alert.alert_level === 'red'
  const typeConfig = ALERT_TYPE_CONFIG[alert.alert_type] || { icon: AlertTriangle, color: 'var(--color-ink-500)' }
  const TypeIcon = typeConfig.icon
  const LevelIcon = isRed ? AlertCircle : AlertTriangle

  const handleResolve = async () => {
    setResolving(true)
    try {
      await onResolve(alert.id, note)
    } finally {
      setResolving(false)
      setShowNote(false)
    }
  }

  return (
    <div style={{
      padding: '1rem 1.25rem',
      borderRadius: 'var(--radius-md)',
      border: `1.5px solid ${isRed ? '#fca5a5' : '#fcd34d'}`,
      background: isRed ? '#fff5f5' : '#fffdf0',
      display: 'flex', flexDirection: 'column', gap: '0.625rem',
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.625rem' }}>
          <div style={{
            width: 32, height: 32, borderRadius: 'var(--radius-md)', flexShrink: 0,
            background: 'var(--color-bg-surface)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <TypeIcon size={16} style={{ color: typeConfig.color }} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
              <span style={{
                fontSize: '0.6875rem', fontWeight: 700, letterSpacing: '0.07em',
                textTransform: 'uppercase',
                color: isRed ? 'var(--color-err-text)' : 'var(--color-warn-text)',
                display: 'flex', alignItems: 'center', gap: '0.25rem',
              }}>
                <LevelIcon size={12} /> {alert.alert_type_label}
              </span>
            </div>
            <p style={{ fontSize: '0.9375rem', color: 'var(--color-ink-900)', margin: 0, lineHeight: 1.5 }}>
              {alert.description}
            </p>
            <p style={{ fontSize: '0.75rem', color: 'var(--color-ink-500)', margin: '0.25rem 0 0' }}>
              Desde {new Date(alert.triggered_at).toLocaleDateString('es-CL', { day: 'numeric', month: 'long' })}
            </p>
          </div>
        </div>
        <button
          onClick={() => setShowNote(!showNote)}
          className="btn btn-secondary btn-sm"
          style={{ flexShrink: 0 }}
        >
          <CheckCircle size={13} /> Marcar atendida
        </button>
      </div>

      {showNote && (
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-end', paddingTop: '0.25rem' }}>
          <div className="field" style={{ flex: 1 }}>
            <label className="label">Nota interna (opcional)</label>
            <input
              type="text"
              className="input"
              placeholder="Ej: Se contactó al estudiante por teléfono"
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </div>
          <button onClick={handleResolve} disabled={resolving} className="btn btn-primary btn-sm">
            {resolving ? 'Guardando…' : 'Confirmar'}
          </button>
          <button onClick={() => setShowNote(false)} className="btn btn-ghost btn-sm">
            <X size={13} />
          </button>
        </div>
      )}
    </div>
  )
}

// ── Componente fila de estudiante ─────────────────────────────────────────────
function StudentRow({ student, onResolve }) {
  const [expanded, setExpanded] = useState(false)
  const cfg = LIGHT[student.traffic_light] ?? LIGHT.green
  const isRed = student.traffic_light === 'red'

  return (
    <div style={{
      border: `1.5px solid ${isRed ? '#fca5a5' : student.traffic_light === 'yellow' ? '#fcd34d' : 'var(--color-ink-100)'}`,
      borderRadius: 'var(--radius-lg)',
      background: isRed ? '#fff8f8' : student.traffic_light === 'yellow' ? '#fffef5' : 'var(--color-bg-surface)',
      overflow: 'hidden',
      transition: 'box-shadow 0.15s',
    }}>
      {/* Cabecera del estudiante */}
      <button
        onClick={() => setExpanded(!expanded)}
        style={{
          width: '100%', display: 'flex', alignItems: 'center',
          justifyContent: 'space-between', padding: '1rem 1.25rem',
          background: 'transparent', border: 'none', cursor: 'pointer',
          gap: '1rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {/* Indicador visual de peso — rojo tiene borde izquierdo grueso */}
          {isRed && (
            <div style={{ width: 4, height: 36, borderRadius: 2, background: 'var(--color-err-text)', flexShrink: 0 }} />
          )}
          <div style={{ textAlign: 'left' }}>
            <p style={{ fontWeight: 600, fontSize: '0.9375rem', color: 'var(--color-ink-900)', margin: 0 }}>
              {student.student_name}
            </p>
            {student.active_alerts.length > 0 && (
              <p style={{ fontSize: '0.8125rem', color: 'var(--color-ink-500)', margin: 0, marginTop: '0.125rem' }}>
                {student.active_alerts.length} alerta{student.active_alerts.length > 1 ? 's' : ''} activa{student.active_alerts.length > 1 ? 's' : ''}
              </p>
            )}
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <TrafficBadge level={student.traffic_light} />
          {expanded ? <ChevronUp size={16} style={{ color: 'var(--color-ink-300)', flexShrink: 0 }} />
                    : <ChevronDown size={16} style={{ color: 'var(--color-ink-300)', flexShrink: 0 }} />}
        </div>
      </button>

      {/* Detalle expandido */}
      {expanded && (
        <div style={{ padding: '0 1.25rem 1.25rem', display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
          {student.active_alerts.length === 0 ? (
            <p style={{ fontSize: '0.875rem', color: 'var(--color-ink-300)', textAlign: 'center', padding: '1rem 0' }}>
              Sin alertas activas
            </p>
          ) : (
            student.active_alerts.map((alert) => (
              <AlertRow key={alert.id} alert={alert} onResolve={onResolve} />
            ))
          )}
        </div>
      )}
    </div>
  )
}

// ── Página principal ──────────────────────────────────────────────────────────
export default function AlertsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [students, setStudents] = useState([])
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState(null)

  const filter = searchParams.get('filter') || 'all'

  const load = () => {
    setLoading(true)
    // Primero ejecutar la evaluación automática
    api.post('/alerts/run')
      .catch(() => {}) // No mostrar error si falla la evaluación
      .finally(() => {
        // Luego cargar los datos actualizados
        Promise.all([
          api.get('/alerts/students'),
          api.get('/alerts/summary'),
        ])
          .then(([studentsRes, summaryRes]) => {
            setStudents(studentsRes.data)
            setSummary(summaryRes.data)
          })
          .catch(() => setError('Error al cargar las alertas'))
          .finally(() => setLoading(false))
      })
  }

  useEffect(() => { load() }, [])

  const handleRunEvaluation = async () => {
    setRunning(true)
    try {
      await api.post('/alerts/run')
      load()
    } catch {
      setError('Error al ejecutar la evaluación')
    } finally {
      setRunning(false)
    }
  }

  const handleResolve = async (alertId, note) => {
    await api.post(`/alerts/resolve/${alertId}`, { coordinator_note: note || null })
    load()
  }

  const filtered = filter === 'all'
    ? students
    : students.filter((s) => s.traffic_light === filter)

  if (loading) return <Spinner />

  return (
    <div className="page-enter">
      <div className="section-header">
        <div>
          <h2 className="section-title">Panel de alertas</h2>
          <p className="section-subtitle">Detección automática de patrones preocupantes</p>
        </div>
      </div>

      <AlertError>{error}</AlertError>

      {/* Widget resumen */}
      {summary && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
          {[
            { key: 'red',    label: 'Requieren atención inmediata', icon: AlertCircle, color: 'var(--color-err-text)',  bg: '#fff0f0', border: '#fca5a5' },
            { key: 'yellow', label: 'En seguimiento',               icon: AlertTriangle, color: 'var(--color-warn-text)', bg: '#fffbeb', border: '#fcd34d' },
            { key: 'green',  label: 'Sin novedades',                icon: CheckCircle2, color: 'var(--color-ok-text)',   bg: '#f0fdf4', border: '#86efac' },
          ].map(({ key, label, icon: Icon, color, bg, border }) => (
            <button
              key={key}
              onClick={() => setSearchParams({ filter: key === filter ? 'all' : key })}
              style={{
                background: bg,
                border: `1.5px solid ${filter === key ? color : border}`,
                borderRadius: 'var(--radius-lg)',
                padding: '1.25rem 1.5rem',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'box-shadow 0.15s, transform 0.15s',
                boxShadow: filter === key ? `0 0 0 3px ${border}` : 'none',
              }}
            >
              <p style={{ fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color, margin: '0 0 0.5rem', display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                <Icon size={14} /> {label}
              </p>
              <p style={{ fontFamily: 'var(--font-display)', fontSize: '2.5rem', fontWeight: 400, color, margin: 0, lineHeight: 1 }}>
                {summary[key]}
              </p>
              <p style={{ fontSize: '0.8125rem', color, opacity: 0.7, margin: '0.25rem 0 0' }}>estudiantes</p>
            </button>
          ))}
        </div>
      )}

      {/* Filtros rápidos */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.25rem', flexWrap: 'wrap' }}>
        {FILTERS.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setSearchParams(key === 'all' ? {} : { filter: key })}
            className={`btn btn-sm ${filter === key || (key === 'all' && filter === 'all') ? 'btn-primary' : 'btn-secondary'}`}
          >
            {Icon && <Icon size={13} />} {label}
          </button>
        ))}
      </div>

      {/* Lista de estudiantes */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {filtered.length === 0 ? (
          <div className="card" style={{ padding: '3rem', textAlign: 'center' }}>
            <div style={{
              width: 48, height: 48, borderRadius: '50%',
              background: 'var(--color-ok-bg)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              margin: '0 auto 0.875rem',
            }}>
              <CheckCircle2 size={24} style={{ color: 'var(--color-ok-text)' }} />
            </div>
            <p style={{ fontFamily: 'var(--font-display)', fontSize: '1.125rem', color: 'var(--color-ink-700)' }}>
              Sin estudiantes en esta categoría
            </p>
          </div>
        ) : (
          filtered.map((student) => (
            <StudentRow key={student.student_id} student={student} onResolve={handleResolve} />
          ))
        )}
      </div>
    </div>
  )
}
