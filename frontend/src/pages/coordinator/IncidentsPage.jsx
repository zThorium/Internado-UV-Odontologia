import { useEffect, useState } from 'react'
import api from '../../services/api'
import Spinner from '../../components/ui/Spinner'
import Badge from '../../components/ui/Badge'
import { AlertError, AlertSuccess } from '../../components/ui/Alert'
import EmptyState from '../../components/ui/EmptyState'
import { AlertTriangle, ShieldCheck, Eye, Send, User } from 'lucide-react'

const TYPE_LABELS = {
  abuse:          'Abuso',
  harassment:     'Acoso',
  discrimination: 'Discriminación',
  other:          'Otro',
}

const TYPE_ICON_COLOR = {
  abuse:          '#c62828',
  harassment:     '#e65100',
  discrimination: '#6a1b9a',
  other:          'var(--color-earth-500)',
}

const URGENCY_LABELS = {
  low: 'Baja',
  medium: 'Media',
  high: 'Alta',
  critical: 'Crítica',
}

const URGENCY_CLS = {
  low: 'badge-blue',
  medium: 'badge-yellow',
  high: 'badge-red',
  critical: 'badge-red',
}

const REPORTER_LABELS = {
  student: 'Estudiante',
  tutor: 'Tutor',
}

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [updating, setUpdating] = useState(null)
  const [expanded, setExpanded] = useState(null)
  const [responseText, setResponseText] = useState({})
  const [sendingResponse, setSendingResponse] = useState(null)
  const [responseError, setResponseError] = useState(null)
  const [responseSuccess, setResponseSuccess] = useState(null)

  const load = () => {
    setLoading(true)
    setError(null)
    api.get('/incidents')
      .then(({ data }) => setIncidents(data))
      .catch(() => setError('Error al cargar los incidentes'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const updateStatus = (id, status) => {
    setUpdating(id)
    api.patch(`/incidents/${id}/status`, { status })
      .then(() => load())
      .catch(() => alert('Error al actualizar el estado'))
      .finally(() => setUpdating(null))
  }

  const sendResponse = async (incidentId) => {
    const response = responseText[incidentId]
    if (!response || !response.trim()) return

    setSendingResponse(incidentId)
    setResponseError(null)
    setResponseSuccess(null)

    try {
      await api.patch(`/incidents/${incidentId}/response`, {
        coordinator_response: response,
      })
      setResponseSuccess('Respuesta enviada correctamente')
      setResponseText((prev) => ({ ...prev, [incidentId]: '' }))
      load()
    } catch (err) {
      setResponseError(err.response?.data?.detail || 'Error al enviar la respuesta')
    } finally {
      setSendingResponse(null)
    }
  }

  const open = incidents.filter((i) => i.status === 'submitted').length
  const underReview = incidents.filter((i) => i.status === 'under_review').length

  return (
    <div className="page-enter">
      <div className="section-header">
        <div>
          <h2 className="section-title">Incidentes</h2>
          <p className="section-subtitle">Gestiona y da seguimiento a los incidentes reportados</p>
        </div>
      </div>

      {/* Resumen */}
      {!loading && incidents.length > 0 && (
        <div className="stagger stats-grid-3" style={{ marginBottom: '1.5rem' }}>
          <div className="card-stat" style={{ display: 'flex', alignItems: 'center', gap: '0.875rem' }}>
            <div style={{ width: 40, height: 40, borderRadius: 'var(--radius-md)', background: 'var(--color-ink-50)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <AlertTriangle size={18} style={{ color: 'var(--color-ink-500)' }} />
            </div>
            <div>
              <p style={{ fontSize: '0.75rem', color: 'var(--color-ink-500)', margin: 0 }}>Total</p>
              <p style={{ fontFamily: 'var(--font-display)', fontSize: '1.5rem', fontWeight: 500, margin: 0, lineHeight: 1.1 }}>{incidents.length}</p>
            </div>
          </div>
          <div className="card-stat" style={{ display: 'flex', alignItems: 'center', gap: '0.875rem' }}>
            <div style={{ width: 40, height: 40, borderRadius: 'var(--radius-md)', background: 'var(--color-err-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <AlertTriangle size={18} style={{ color: 'var(--color-err-text)' }} />
            </div>
            <div>
              <p style={{ fontSize: '0.75rem', color: 'var(--color-ink-500)', margin: 0 }}>Abiertos</p>
              <p style={{ fontFamily: 'var(--font-display)', fontSize: '1.5rem', fontWeight: 500, margin: 0, lineHeight: 1.1, color: 'var(--color-err-text)' }}>{open}</p>
            </div>
          </div>
          <div className="card-stat" style={{ display: 'flex', alignItems: 'center', gap: '0.875rem' }}>
            <div style={{ width: 40, height: 40, borderRadius: 'var(--radius-md)', background: 'var(--color-warn-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Eye size={18} style={{ color: 'var(--color-warn-text)' }} />
            </div>
            <div>
              <p style={{ fontSize: '0.75rem', color: 'var(--color-ink-500)', margin: 0 }}>En revisión</p>
              <p style={{ fontFamily: 'var(--font-display)', fontSize: '1.5rem', fontWeight: 500, margin: 0, lineHeight: 1.1, color: 'var(--color-warn-text)' }}>{underReview}</p>
            </div>
          </div>
        </div>
      )}

      {loading && <Spinner />}
      <AlertError>{error}</AlertError>
      <AlertSuccess>{responseSuccess}</AlertSuccess>

      {!loading && !error && (
        incidents.length === 0 ? (
          <div className="card">
            <EmptyState icon={ShieldCheck} title="Sin incidentes" description="No hay incidentes registrados en el sistema." />
          </div>
        ) : (
          <div className="stagger" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {incidents.map((inc) => (
              <div key={inc.id} className="card" style={{ overflow: 'hidden' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '1rem 1.25rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.875rem', flex: 1, minWidth: 0 }}>
                    <div style={{
                      width: 36, height: 36, borderRadius: 'var(--radius-md)', flexShrink: 0,
                      background: 'var(--color-earth-50)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                      <AlertTriangle size={16} style={{ color: TYPE_ICON_COLOR[inc.incident_type] || 'var(--color-earth-500)' }} />
                    </div>
                    <div style={{ minWidth: 0, flex: 1 }}>
                      <p style={{ fontWeight: 600, color: 'var(--color-ink-900)', margin: 0 }}>
                        {inc.title || TYPE_LABELS[inc.incident_type] || inc.incident_type}
                      </p>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8125rem', color: 'var(--color-ink-500)' }}>
                        <span>{inc.event_date}</span>
                        {inc.reporter_role && (
                          <>
                            <span>•</span>
                            <span>Reporta: {REPORTER_LABELS[inc.reporter_role] || inc.reporter_role}</span>
                          </>
                        )}
                        {inc.student_name && (
                          <>
                            <span>•</span>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                              <User size={12} />
                              <span>{inc.student_name}</span>
                            </div>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexShrink: 0 }}>
                    {inc.urgency_level && (
                      <span className={`badge ${URGENCY_CLS[inc.urgency_level] || 'badge-gray'}`}>
                        Urgencia {URGENCY_LABELS[inc.urgency_level] || inc.urgency_level}
                      </span>
                    )}
                    <Badge status={inc.status} />
                    <button
                      onClick={() => setExpanded(expanded === inc.id ? null : inc.id)}
                      className="btn btn-ghost btn-sm"
                    >
                      <Eye size={13} /> Ver
                    </button>
                  </div>
                </div>

                {expanded === inc.id && (
                  <div style={{
                    borderTop: '1px solid var(--color-earth-100)',
                    padding: '1rem 1.25rem',
                    background: 'var(--color-earth-50)',
                  }}>
                    {/* Student info */}
                    {inc.student_email && (
                      <div style={{
                        background: 'var(--color-bg-surface)',
                        borderRadius: 'var(--radius-md)',
                        padding: '0.75rem 1rem',
                        marginBottom: '1rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                      }}>
                        <User size={14} style={{ color: 'var(--color-ink-500)' }} />
                        <div>
                          <p style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--color-ink-700)', margin: 0 }}>
                            {inc.student_name}
                          </p>
                          <p style={{ fontSize: '0.75rem', color: 'var(--color-ink-500)', margin: 0 }}>
                            {inc.student_email}
                          </p>
                        </div>
                      </div>
                    )}

                    {/* Description */}
                    {inc.description && (
                      <div style={{ marginBottom: '1rem' }}>
                        <p style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-ink-500)', margin: '0 0 0.375rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                          Descripción
                        </p>
                        <p style={{ fontSize: '0.9rem', color: 'var(--color-ink-700)', margin: 0, lineHeight: 1.6 }}>
                          {inc.description}
                        </p>
                        <p style={{ fontSize: '0.8rem', color: 'var(--color-ink-500)', margin: '0.5rem 0 0' }}>
                          Tipo: {TYPE_LABELS[inc.incident_type] || inc.incident_type}
                        </p>
                      </div>
                    )}

                    {/* Existing response */}
                    {inc.coordinator_response && (
                      <div style={{
                        background: 'var(--color-uv-50)',
                        border: '1px solid var(--color-uv-100)',
                        borderRadius: 'var(--radius-md)',
                        padding: '0.75rem 1rem',
                        marginBottom: '1rem',
                      }}>
                        <p style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-uv-600)', margin: '0 0 0.375rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                          Tu respuesta
                        </p>
                        <p style={{ fontSize: '0.875rem', color: 'var(--color-ink-700)', margin: 0, lineHeight: 1.6 }}>
                          {inc.coordinator_response}
                        </p>
                      </div>
                    )}

                    {/* Response form */}
                    <div style={{ marginBottom: '1rem' }}>
                      <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-ink-500)', display: 'block', margin: '0 0 0.375rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                        {inc.coordinator_response ? 'Actualizar respuesta' : 'Enviar respuesta al estudiante'}
                      </label>
                      <textarea
                        value={responseText[inc.id] || ''}
                        onChange={(e) => setResponseText((prev) => ({ ...prev, [inc.id]: e.target.value }))}
                        placeholder="Escribe tu respuesta aquí..."
                        rows={3}
                        className="input"
                        style={{ resize: 'none', marginBottom: '0.5rem' }}
                      />
                      <button
                        onClick={() => sendResponse(inc.id)}
                        disabled={sendingResponse === inc.id || !responseText[inc.id]?.trim()}
                        className="btn btn-primary btn-sm"
                      >
                        <Send size={13} /> {sendingResponse === inc.id ? 'Enviando...' : 'Enviar respuesta'}
                      </button>
                      {responseError && <p style={{ fontSize: '0.8125rem', color: 'var(--color-err-text)', marginTop: '0.5rem' }}>{responseError}</p>}
                    </div>

                    {/* Status actions */}
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button
                        onClick={() => updateStatus(inc.id, 'under_review')}
                        disabled={updating === inc.id || inc.status === 'under_review' || inc.status === 'resolved'}
                        className="btn btn-secondary btn-sm"
                      >
                        <Eye size={13} /> En revisión
                      </button>
                      <button
                        onClick={() => updateStatus(inc.id, 'resolved')}
                        disabled={updating === inc.id || inc.status === 'resolved'}
                        className="btn btn-sm"
                        style={{ background: 'var(--color-ok-bg)', color: 'var(--color-ok-text)', border: '1.5px solid #c8e6c9' }}
                      >
                        <ShieldCheck size={13} /> Marcar resuelto
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )
      )}
    </div>
  )
}
