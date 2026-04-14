import { useEffect, useMemo, useState } from 'react'
import api from '../../services/api'
import Spinner from '../../components/ui/Spinner'
import Badge from '../../components/ui/Badge'
import { AlertError, AlertSuccess } from '../../components/ui/Alert'
import EmptyState from '../../components/ui/EmptyState'
import { AlertTriangle, RefreshCw, Send, ShieldAlert } from 'lucide-react'

const URGENCY_OPTIONS = [
  { value: 'low', label: 'Baja' },
  { value: 'medium', label: 'Media' },
  { value: 'high', label: 'Alta' },
  { value: 'critical', label: 'Crítica' },
]

const URGENCY_BADGE = {
  low: 'badge-blue',
  medium: 'badge-yellow',
  high: 'badge-red',
  critical: 'badge-red',
}

export default function TutorIncidentsPage() {
  const [students, setStudents] = useState([])
  const [incidents, setIncidents] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadingSubmit, setLoadingSubmit] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [form, setForm] = useState({
    student_id: '',
    title: '',
    description: '',
    event_date: '',
    urgency_level: 'medium',
  })

  const studentsMap = useMemo(
    () => new Map(students.map((student) => [student.id, student])),
    [students],
  )

  const loadData = () => {
    setLoading(true)
    setError(null)
    Promise.all([
      api.get('/evaluations/my-students'),
      api.get('/incidents'),
    ])
      .then(([studentsRes, incidentsRes]) => {
        setStudents(studentsRes.data)
        setIncidents(incidentsRes.data)
      })
      .catch(() => setError('No se pudo cargar la información de incidentes.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError(null)
    setSuccess(null)
    setLoadingSubmit(true)

    try {
      await api.post('/incidents/tutor', form)
      setForm({
        student_id: '',
        title: '',
        description: '',
        event_date: '',
        urgency_level: 'medium',
      })
      setSuccess('Incidente registrado correctamente y enviado a coordinación.')
      loadData()
    } catch (submitError) {
      setError(submitError.response?.data?.detail || 'No fue posible registrar el incidente.')
    } finally {
      setLoadingSubmit(false)
    }
  }

  if (loading) return <Spinner />

  return (
    <div className="page-enter">
      <div className="section-header">
        <div>
          <h2 className="section-title">Incidentes clínicos</h2>
          <p className="section-subtitle">Registra situaciones del estudiante para seguimiento del coordinador</p>
        </div>
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          onClick={loadData}
          disabled={loading}
        >
          <RefreshCw size={14} />
          Actualizar
        </button>
      </div>

      <div className="card" style={{ padding: '1.25rem 1.5rem', marginBottom: '1.5rem' }}>
        <form onSubmit={handleSubmit} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div className="field">
            <label className="label">Estudiante</label>
            <select
              className="input"
              value={form.student_id}
              onChange={(event) => setForm((prev) => ({ ...prev, student_id: event.target.value }))}
              required
            >
              <option value="">Selecciona un estudiante asignado...</option>
              {students.map((student) => (
                <option key={student.id} value={student.id}>
                  {student.full_name}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label className="label">Fecha</label>
            <input
              type="date"
              className="input"
              value={form.event_date}
              onChange={(event) => setForm((prev) => ({ ...prev, event_date: event.target.value }))}
              required
            />
          </div>

          <div className="field" style={{ gridColumn: '1 / -1' }}>
            <label className="label">Título del incidente</label>
            <input
              type="text"
              className="input"
              placeholder="Ej: Ausencias reiteradas sin justificación"
              value={form.title}
              onChange={(event) => setForm((prev) => ({ ...prev, title: event.target.value }))}
              required
            />
          </div>

          <div className="field" style={{ gridColumn: '1 / -1' }}>
            <label className="label">Descripción</label>
            <textarea
              rows={4}
              className="input"
              style={{ resize: 'none' }}
              placeholder="Describe el contexto y hechos relevantes..."
              value={form.description}
              onChange={(event) => setForm((prev) => ({ ...prev, description: event.target.value }))}
              required
            />
          </div>

          <div className="field">
            <label className="label">Nivel de urgencia</label>
            <select
              className="input"
              value={form.urgency_level}
              onChange={(event) => setForm((prev) => ({ ...prev, urgency_level: event.target.value }))}
            >
              {URGENCY_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'end' }}>
            <button type="submit" className="btn btn-primary" disabled={loadingSubmit || students.length === 0}>
              <Send size={14} />
              {loadingSubmit ? 'Enviando...' : 'Registrar incidente'}
            </button>
          </div>
        </form>
      </div>

      <AlertError>{error}</AlertError>
      <AlertSuccess>{success}</AlertSuccess>

      {incidents.length === 0 ? (
        <div className="card">
          <EmptyState
            icon={ShieldAlert}
            title="Sin incidentes registrados"
            description="Aún no has registrado incidentes de tus estudiantes."
          />
        </div>
      ) : (
        <div className="stagger" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {incidents.map((incident) => {
            const student = studentsMap.get(incident.student_id)
            return (
              <div key={incident.id} className="card" style={{ padding: '1rem 1.25rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.75rem' }}>
                  <div style={{ minWidth: 0 }}>
                    <p style={{ margin: 0, fontWeight: 600, color: 'var(--color-ink-900)' }}>
                      {incident.title || 'Incidente reportado'}
                    </p>
                    <p style={{ margin: '0.2rem 0 0', fontSize: '0.8125rem', color: 'var(--color-ink-500)' }}>
                      {student?.full_name || incident.student_name || 'Estudiante'} · {incident.event_date}
                    </p>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span className={`badge ${URGENCY_BADGE[incident.urgency_level] || 'badge-gray'}`}>
                      Urgencia {URGENCY_OPTIONS.find((item) => item.value === incident.urgency_level)?.label || incident.urgency_level}
                    </span>
                    <Badge status={incident.status} />
                  </div>
                </div>
                <p style={{ margin: '0.65rem 0 0', fontSize: '0.875rem', color: 'var(--color-ink-600)', lineHeight: 1.5 }}>
                  <AlertTriangle size={14} style={{ marginRight: '0.35rem', verticalAlign: 'text-bottom', color: 'var(--color-earth-500)' }} />
                  {incident.description}
                </p>

                <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid var(--color-earth-100)' }}>
                  <p style={{ margin: 0, fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-ink-500)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Respuesta de coordinación
                  </p>
                  {incident.coordinator_response ? (
                    <>
                      <p style={{ margin: '0.35rem 0 0', fontSize: '0.875rem', color: 'var(--color-ink-700)', lineHeight: 1.45 }}>
                        {incident.coordinator_response}
                      </p>
                      <p style={{ margin: '0.35rem 0 0', fontSize: '0.75rem', color: 'var(--color-ink-500)' }}>
                        Actualizado: {new Date(incident.updated_at).toLocaleString('es-CL')}
                      </p>
                    </>
                  ) : (
                    <p style={{ margin: '0.35rem 0 0', fontSize: '0.8125rem', color: 'var(--color-ink-500)' }}>
                      Aún no hay respuesta de coordinación para este incidente.
                    </p>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
