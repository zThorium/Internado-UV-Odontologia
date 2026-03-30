import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ResponsiveContainer, Area, AreaChart } from 'recharts'
import api from '../../services/api'
import Spinner from '../../components/ui/Spinner'
import { AlertError } from '../../components/ui/Alert'
import {
  BookOpen,
  ArrowRight,
  Activity,
  ClipboardCheck,
  Bell,
  HeartPulse,
  Search,
  PlusCircle,
  FileText,
} from 'lucide-react'
import AlertStatusPill from '../../components/ui/AlertStatusPill'

const METRIC_CARDS = [
  {
    key: 'total_students',
    label: 'Estudiantes activos',
    lineColor: '#2563a8',
    to: '/coordinator/assignments',
  },
  {
    key: 'total_entries',
    label: 'Entradas de bitácora',
    lineColor: '#2e7d32',
    to: '/coordinator/logbooks',
  },
  {
    key: 'open_incidents',
    label: 'Incidentes abiertos',
    lineColor: '#c62828',
    to: '/coordinator/incidents',
    incidentRule: true,
  },
  {
    key: 'pending_entries',
    label: 'Entradas pendientes',
    lineColor: '#1e4d8c',
    to: '/coordinator/logbooks',
  },
]

const ACTIVITY_META = {
  logbook_created: { icon: BookOpen, label: 'Bitácora', cls: 'badge-blue' },
  evaluation_created: { icon: ClipboardCheck, label: 'Evaluación', cls: 'badge-green' },
  incident_created: { icon: Bell, label: 'Incidente', cls: 'badge-red' },
  incident_status_changed: { icon: Activity, label: 'Estado', cls: 'badge-yellow' },
}

function formatRelative(dateLike) {
  const when = new Date(dateLike)
  const seconds = Math.max(1, Math.floor((Date.now() - when.getTime()) / 1000))
  if (seconds < 60) return 'hace unos segundos'
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `hace ${minutes} min`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `hace ${hours} hora${hours === 1 ? '' : 's'}`
  const days = Math.floor(hours / 24)
  return `hace ${days} día${days === 1 ? '' : 's'}`
}

function metricContext(delta) {
  if (delta === 0) return 'Sin cambios esta semana'
  if (delta > 0) return `↑ ${delta} nuevo${delta === 1 ? '' : 's'} esta semana`
  const abs = Math.abs(delta)
  return `↓ ${abs} menos que la semana pasada`
}

function MetricSparkline({ points, color }) {
  const hasData = Array.isArray(points) && points.length > 0
  const chartData = hasData ? points : [
    { label: 'S-3', value: 0 },
    { label: 'S-2', value: 0 },
    { label: 'S-1', value: 0 },
    { label: 'Actual', value: 0 },
  ]

  return (
    <div style={{ width: 130, height: 62 }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 8, right: 2, left: 2, bottom: 2 }}>
          <defs>
            <linearGradient id={`spark-${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.24} />
              <stop offset="100%" stopColor={color} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <Area
            type="monotone"
            dataKey="value"
            stroke={color}
            fill={`url(#spark-${color.replace('#', '')})`}
            strokeWidth={2.5}
            dot={false}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

function MetricDeltaBadge({ delta, incidentRule = false }) {
  if (delta === 0) {
    return <span className="badge badge-gray">0%</span>
  }

  const up = delta > 0
  const isPositive = incidentRule ? !up : up
  const cls = isPositive ? 'badge-green' : 'badge-red'
  const arrow = up ? '↑' : '↓'

  return <span className={`badge ${cls}`}>{arrow} {Math.abs(delta)}</span>
}

export default function OverviewPage() {
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [trends, setTrends] = useState(null)
  const [alertSummary, setAlertSummary] = useState(null)
  const [recentActivity, setRecentActivity] = useState([])
  const [wellbeingQuick, setWellbeingQuick] = useState({ total_active: 0, items: [] })
  const [metricSeries, setMetricSeries] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activityQuery, setActivityQuery] = useState('')

  const loadAll = () => {
    Promise.all([
      api.get('/dashboard/overview'),
      api.get('/dashboard/overview-trends'),
      api.get('/alerts/summary'),
      api.get('/dashboard/metric-series'),
      api.get('/dashboard/recent-activity', { params: { limit: 5 } }),
      api.get('/dashboard/wellbeing-quick', { params: { limit: 3 } }),
    ])
      .then(([overviewRes, trendsRes, alertsRes, seriesRes, recentRes, wellbeingRes]) => {
        setData(overviewRes.data)
        setTrends(trendsRes.data)
        setAlertSummary(alertsRes.data)
        const mappedSeries = Object.fromEntries((seriesRes.data?.series || []).map((s) => [s.key, s.points]))
        setMetricSeries(mappedSeries)
        setRecentActivity(recentRes.data?.items || [])
        setWellbeingQuick(wellbeingRes.data || { total_active: 0, items: [] })
      })
      .catch(() => setError('Error al cargar el resumen'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadAll()
    const intervalId = setInterval(() => {
      loadAll()
    }, 30000)

    return () => clearInterval(intervalId)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  if (loading) return <Spinner />
  if (error) return <AlertError>{error}</AlertError>

  const pendingEntries = data?.pending_entries ?? 0
  const totalEntries = data?.total_entries ?? 0
  const reviewedEntries = Math.max(0, totalEntries - pendingEntries)
  const reviewRate = totalEntries > 0 ? Math.round((reviewedEntries / totalEntries) * 100) : 0

  const openIncidents = data?.open_incidents ?? 0
  const totalIncidents = data?.total_incidents ?? 0
  const incidentOpenRate = totalIncidents > 0 ? Math.round((openIncidents / totalIncidents) * 100) : 0

  const normalizedQuery = activityQuery.trim().toLowerCase()
  const visibleActivity = normalizedQuery
    ? recentActivity.filter((item) => (
      item.description.toLowerCase().includes(normalizedQuery)
      || item.student_name.toLowerCase().includes(normalizedQuery)
    ))
    : recentActivity

  return (
    <div className="page-enter">
      <div className="section-header">
        <div>
          <h2 className="section-title">Resumen general</h2>
          <p className="section-subtitle">Estado actual del internado clínico</p>
        </div>
      </div>

      <div className="card" style={{
        padding: '1rem 1.25rem',
        marginBottom: '1rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '0.75rem',
        flexWrap: 'wrap',
      }}>
        <div style={{ position: 'relative', minWidth: 260, flex: 1 }}>
          <Search size={14} style={{ position: 'absolute', left: '0.75rem', top: '0.72rem', color: 'var(--color-ink-300)' }} />
          <input
            value={activityQuery}
            onChange={(e) => setActivityQuery(e.target.value)}
            placeholder="Buscar en actividad reciente..."
            className="input"
            style={{ paddingLeft: '2.1rem' }}
          />
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => navigate('/coordinator/assignments')}>
            <PlusCircle size={13} /> Nueva asignación
          </button>
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => navigate('/coordinator/logbooks')}>
            <FileText size={13} /> Revisar bitácoras
          </button>
          <button type="button" className="btn btn-primary btn-sm" onClick={() => navigate('/coordinator/alerts')}>
            <Bell size={13} /> Alertas
          </button>
        </div>
      </div>

      {/* Indicador de estado de alertas */}
      {alertSummary && (
        <AlertStatusPill
          red={alertSummary.red ?? 0}
          yellow={alertSummary.yellow ?? 0}
          green={alertSummary.green ?? 0}
          onViewCritical={() => navigate('/coordinator/alerts?filter=red')}
        />
      )}

      <div className="stagger dashboard-metric-row" style={{ display: 'grid', gap: '0.75rem' }}>
        {METRIC_CARDS.map(({ key, label, lineColor, to, incidentRule }) => {
          const value = data?.[key] ?? 0
          const delta = trends?.[key] ?? 0
          const points = metricSeries[key] || []

          return (
            <button
              key={key}
              type="button"
              className="coordinator-metric-card"
              onClick={() => navigate(to)}
            >
              <p className="coordinator-metric-title">{label}</p>
              <div className="coordinator-metric-mainline">
                <p className="coordinator-metric-value">{value}</p>
                <MetricDeltaBadge delta={delta} incidentRule={incidentRule} />
              </div>
              <p className="coordinator-metric-subtitle">respecto a la semana anterior</p>

              <div className="coordinator-sparkline-wrap">
                <MetricSparkline points={points} color={lineColor} />
            </div>
              <span className="coordinator-metric-hover">Ver detalle <ArrowRight size={12} /></span>
            </button>
          )
        })}
      </div>

      <div className="dashboard-bottom-grid" style={{
        marginTop: '1rem',
        display: 'grid',
        gap: '1rem',
      }}>
        <div className="card" style={{ padding: '1.25rem 1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <h3 className="text-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Activity size={17} style={{ color: 'var(--color-uv-600)' }} /> Actividad reciente
            </h3>
            <span className="text-small">Actualiza cada 30s</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
            {visibleActivity.length === 0 && (
              <p className="text-small" style={{ padding: '0.25rem 0.125rem' }}>Sin actividad reciente para este filtro.</p>
            )}

            {visibleActivity.map((item) => {
              const meta = ACTIVITY_META[item.kind] || { icon: Activity, label: 'Actividad', cls: 'badge-gray' }
              const Icon = meta.icon
              return (
                <div key={item.id} className="activity-item-row">
                  <div className="activity-icon-wrap">
                    <Icon size={14} style={{ color: item.level === 'critical' ? 'var(--color-err-text)' : 'var(--color-uv-600)' }} />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--color-ink-700)' }}>
                      {item.description} · <strong>{item.student_name}</strong>
                    </p>
                    <p style={{ margin: '0.125rem 0 0', fontSize: '0.75rem', color: 'var(--color-ink-500)' }}>
                      {formatRelative(item.occurred_at)}
                    </p>
                  </div>
                  <span className={`badge ${item.kind === 'incident_created' ? 'badge-red' : meta.cls}`}>
                    {meta.label}
                  </span>
                </div>
              )
            })}
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="card" style={{ padding: '1.25rem 1.5rem' }}>
            <h3 className="text-title" style={{ marginBottom: '0.75rem' }}>Resumen operacional</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8125rem', color: 'var(--color-ink-500)' }}>
                  <span>Bitácoras revisadas</span>
                  <strong style={{ color: 'var(--color-ink-700)' }}>{reviewRate}%</strong>
                </div>
                <div className="progress-track" style={{ marginTop: '0.3rem' }}>
                  <div className="progress-fill" style={{ width: `${reviewRate}%`, background: 'var(--color-ok-text)' }} />
                </div>
              </div>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8125rem', color: 'var(--color-ink-500)' }}>
                  <span>Incidentes aún abiertos</span>
                  <strong style={{ color: 'var(--color-ink-700)' }}>{incidentOpenRate}%</strong>
                </div>
                <div className="progress-track" style={{ marginTop: '0.3rem' }}>
                  <div className="progress-fill" style={{ width: `${incidentOpenRate}%`, background: 'var(--color-err-text)' }} />
                </div>
              </div>
            </div>
          </div>

          <div className="card" style={{ padding: '1.25rem 1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <h3 className="text-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <HeartPulse size={17} style={{ color: 'var(--color-err-text)' }} /> Semáforo de bienestar
              </h3>
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => navigate('/coordinator/alerts')}
              >
                Ver todos <ArrowRight size={13} />
              </button>
            </div>

            {wellbeingQuick.items.length === 0 ? (
              <p className="text-small">No hay alertas activas recientes.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {wellbeingQuick.items.map((row, idx) => (
                  <div key={`${row.student_id}-${idx}`} className="activity-item-row" style={{ borderColor: row.alert_level === 'red' ? '#fca5a5' : '#fde68a' }}>
                    <div className="activity-icon-wrap" style={{
                      background: row.alert_level === 'red' ? '#fff0f0' : '#fff9db',
                      borderColor: row.alert_level === 'red' ? '#fecaca' : '#fde68a',
                    }}>
                      <HeartPulse size={14} style={{ color: row.alert_level === 'red' ? 'var(--color-err-text)' : 'var(--color-warn-text)' }} />
                    </div>
                    <div style={{ flex: 1 }}>
                      <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--color-ink-700)' }}>
                        <strong>{row.student_name}</strong>
                      </p>
                      <p style={{ margin: '0.125rem 0 0', fontSize: '0.75rem', color: 'var(--color-ink-500)' }}>
                        {formatRelative(row.triggered_at)}
                      </p>
                    </div>
                    <span className={`badge ${row.alert_level === 'red' ? 'badge-red' : 'badge-yellow'}`}>
                      {row.alert_level === 'red' ? 'Crítica' : 'Seguimiento'}
                    </span>
                  </div>
                ))}
                <p className="text-small" style={{ marginTop: '0.25rem' }}>
                  {wellbeingQuick.total_active} alerta{wellbeingQuick.total_active === 1 ? '' : 's'} activa{wellbeingQuick.total_active === 1 ? '' : 's'} en total.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
