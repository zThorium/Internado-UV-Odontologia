import { useEffect, useState } from 'react'
import api from '../../services/api'
import Spinner from '../../components/ui/Spinner'
import Badge from '../../components/ui/Badge'
import { AlertError, AlertSuccess } from '../../components/ui/Alert'
import { AlertTriangle, Plus, ShieldCheck, X } from 'lucide-react'

const INCIDENT_TYPES = [
  { value: 'abuse',          label: 'Abuso',           desc: 'Maltrato físico o verbal' },
  { value: 'harassment',     label: 'Acoso',            desc: 'Acoso laboral o sexual' },
  { value: 'discrimination', label: 'Discriminación',   desc: 'Trato diferenciado injusto' },
  { value: 'other',          label: 'Otro',             desc: 'Otro tipo de incidente' },
]

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState([])
  const [loading, setLoading] = useState(true)
  const [fetchError, setFetchError] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [incidentType, setIncidentType] = useState('abuse')
  const [description, setDescription] = useState('')
  const [eventDate, setEventDate] = useState('')
  const [submitError, setSubmitError] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [success, setSuccess] = useState(false)

  const load = () => {
    setLoading(true)
    api.get('/incidents')
      .then(({ data }) => setIncidents(data))
      .catch(() => setFetchError('Error al cargar los incidentes'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitError(null)
    setSuccess(false)
    setSubmitting(true)
    try {
      await api.post('/incidents', { incident_type: incidentType, description, event_date: eventDate })
      setDescription('')
      setEventDate('')
      setIncidentType('abuse')
      setSuccess(true)
      setShowForm(false)
      load()
    } catch (err) {
      setSubmitError(err.response?.data?.detail || 'Error al reportar el incidente')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="page-enter">
      {/* Header con tono cálido y humano */}
      <div style={{ marginBottom: '1.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem' }}>
          <div>
            <h2 className="section-title">Reportar incidente</h2>
            <p className="section-subtitle" style={{ maxWidth: '42ch' }}>
              Este espacio es confidencial. Tu bienestar durante el internado es una prioridad.
            </p>
          </div>
          <button
            onClick={() => { setShowForm(!showForm); setSuccess(false) }}
            className={showForm ? 'btn btn-secondary' : 'btn btn-warm'}
          >
            {showForm ? <><X size={15} /> Cancelar</> : <><Plus size={15} /> Reportar</>}
          </button>
        </div>
      </div>

      {/* Aviso de confidencialidad — elemento memorable */}
      {!showForm && (
        <div style={{
          background: 'var(--color-earth-50)',
          border: '1px solid var(--color-earth-100)',
          borderLeft: '3px solid var(--color-earth-300)',
          borderRadius: 'var(--radius-lg)',
          padding: '1rem 1.25rem',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '0.75rem',
        }}>
          <ShieldCheck size={18} style={{ color: 'var(--color-earth-500)', flexShrink: 0, marginTop: 2 }} />
          <div>
            <p style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--color-earth-700)', margin: '0 0 0.25rem' }}>
              Espacio seguro y confidencial
            </p>
            <p style={{ fontSize: '0.8125rem', color: 'var(--color-earth-700)', margin: 0, lineHeight: 1.5 }}>
              Los reportes son gestionados exclusivamente por el coordinador UV. Tu identidad está protegida durante el proceso de revisión.
            </p>
          </div>
        </div>
      )}

      <AlertSuccess>{success && 'Tu reporte fue enviado correctamente. El coordinador lo revisará pronto.'}</AlertSuccess>

      {/* Formulario cálido */}
      {showForm && (
        <div className="card-warm" style={{ padding: '1.75rem', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', marginBottom: '1.25rem' }}>
            <AlertTriangle size={16} style={{ color: 'var(--color-earth-500)' }} />
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.0625rem', fontWeight: 500, color: 'var(--color-earth-900)', margin: 0 }}>
              Nuevo reporte
            </h3>
          </div>
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxWidth: 520 }}>
            {/* Tipo de incidente — radio cards */}
            <div className="field">
              <label className="label" style={{ color: 'var(--color-earth-700)' }}>Tipo de incidente</label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                {INCIDENT_TYPES.map((t) => (
                  <label key={t.value} style={{
                    display: 'flex', flexDirection: 'column', gap: '0.125rem',
                    padding: '0.625rem 0.875rem',
                    borderRadius: 'var(--radius-md)',
                    border: `1.5px solid ${incidentType === t.value ? 'var(--color-earth-500)' : 'var(--color-earth-100)'}`,
                    background: incidentType === t.value ? 'var(--color-earth-100)' : 'var(--color-bg-surface)',
                    cursor: 'pointer',
                    transition: 'all 120ms',
                  }}>
                    <input type="radio" name="incident_type" value={t.value}
                      checked={incidentType === t.value}
                      onChange={() => setIncidentType(t.value)}
                      style={{ display: 'none' }} />
                    <span style={{ fontSize: '0.875rem', fontWeight: 600, color: incidentType === t.value ? 'var(--color-earth-700)' : 'var(--color-ink-700)' }}>
                      {t.label}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--color-ink-500)' }}>{t.desc}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="field">
              <label className="label" style={{ color: 'var(--color-earth-700)' }}>Descripción del incidente</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                required rows={4}
                className="input input-warm"
                style={{ resize: 'none' }}
                placeholder="Describe lo ocurrido con el mayor detalle posible..."
              />
            </div>

            <div className="field">
              <label className="label" style={{ color: 'var(--color-earth-700)' }}>Fecha del evento</label>
              <input type="date" value={eventDate} onChange={(e) => setEventDate(e.target.value)}
                required className="input input-warm" />
            </div>

            <AlertError>{submitError}</AlertError>

            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button type="submit" disabled={submitting} className="btn btn-warm">
                {submitting ? 'Enviando...' : 'Enviar reporte'}
              </button>
              <button type="button" onClick={() => setShowForm(false)} className="btn btn-secondary">
                Cancelar
              </button>
            </div>
          </form>
        </div>
      )}

      {loading && <Spinner />}
      <AlertError>{fetchError}</AlertError>

      {!loading && !fetchError && (
        incidents.length === 0 ? (
          <div className="card" style={{ padding: '3rem 2rem', textAlign: 'center' }}>
            <div style={{
              width: 48, height: 48, borderRadius: '50%',
              background: 'var(--color-earth-50)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              margin: '0 auto 0.875rem',
            }}>
              <ShieldCheck size={22} style={{ color: 'var(--color-earth-300)' }} />
            </div>
            <p style={{ fontFamily: 'var(--font-display)', fontSize: '1.0625rem', color: 'var(--color-ink-700)', margin: '0 0 0.375rem' }}>
              Sin reportes
            </p>
            <p style={{ fontSize: '0.875rem', color: 'var(--color-ink-500)' }}>
              No has reportado incidentes. Si algo ocurre, este espacio está disponible.
            </p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem' }} className="stagger">
            {incidents.map((inc) => {
              const typeLabel = INCIDENT_TYPES.find((t) => t.value === inc.incident_type)?.label || inc.incident_type
              return (
                <div key={inc.id} style={{
                  background: 'var(--color-bg-surface)',
                  border: '1px solid var(--color-earth-100)',
                  borderLeft: '3px solid var(--color-earth-300)',
                  borderRadius: 'var(--radius-lg)',
                  overflow: 'hidden',
                }}>
                  <div style={{
                    padding: '1rem 1.25rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: '1rem',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <AlertTriangle size={15} style={{ color: 'var(--color-earth-500)', flexShrink: 0 }} />
                      <div>
                        <p style={{ fontWeight: 600, color: 'var(--color-ink-900)', margin: 0 }}>{typeLabel}</p>
                        <p style={{ fontSize: '0.8125rem', color: 'var(--color-ink-500)', margin: 0 }}>{inc.event_date}</p>
                      </div>
                    </div>
                    <Badge status={inc.status} />
                  </div>
                  
                  {/* Coordinator response */}
                  {inc.coordinator_response && (
                    <div style={{
                      background: 'var(--color-uv-50)',
                      borderTop: '1px solid var(--color-uv-100)',
                      padding: '1rem 1.25rem',
                    }}>
                      <p style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-uv-600)', margin: '0 0 0.5rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                        Respuesta del coordinador
                      </p>
                      <p style={{ fontSize: '0.875rem', color: 'var(--color-ink-700)', margin: 0, lineHeight: 1.6 }}>
                        {inc.coordinator_response}
                      </p>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )
      )}
    </div>
  )
}
