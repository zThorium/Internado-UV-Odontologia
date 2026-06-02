import { useEffect, useState } from 'react'
import api from '../../services/api'
import Spinner from '../../components/ui/Spinner'
import { AlertError, AlertSuccess } from '../../components/ui/Alert'
import EmptyState from '../../components/ui/EmptyState'
import { CalendarCheck, Plus, Pencil, Check, X } from 'lucide-react'

const STATUS_OPTIONS = [
  { value: 'present',   label: 'Presente',    cls: 'badge-green' },
  { value: 'absent',    label: 'Ausente',     cls: 'badge-red' },
  { value: 'justified', label: 'Justificado', cls: 'badge-yellow' },
]

const today = () => new Date().toISOString().split('T')[0]

function AttendanceBadge({ status }) {
  const map = { present: 'badge-green', absent: 'badge-red', justified: 'badge-yellow' }
  const labels = { present: 'Presente', absent: 'Ausente', justified: 'Justificado' }
  return <span className={`badge ${map[status] || 'badge-gray'}`}>{labels[status] || status}</span>
}

export default function AttendancePage() {
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(true)
  const [fetchError, setFetchError] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ date: today(), status: 'present', observation: '' })
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState(null)
  const [success, setSuccess] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [editForm, setEditForm] = useState({ status: 'present', observation: '' })
  const [editError, setEditError] = useState(null)

  const load = () => {
    setLoading(true)
    api.get('/attendance/me')
      .then(({ data }) => setRecords(data))
      .catch(() => setFetchError('Error al cargar la asistencia'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitError(null)
    setSuccess(false)
    setSubmitting(true)
    try {
      await api.post('/attendance', form)
      setForm({ date: today(), status: 'present', observation: '' })
      setShowForm(false)
      setSuccess(true)
      load()
    } catch (err) {
      setSubmitError(err.response?.data?.detail || 'Error al registrar asistencia')
    } finally {
      setSubmitting(false)
    }
  }

  const startEdit = (rec) => {
    setEditingId(rec.id)
    setEditForm({ status: rec.status, observation: rec.observation || '' })
    setEditError(null)
  }

  const handleEditSave = async (id) => {
    setEditError(null)
    try {
      await api.patch(`/attendance/${id}`, editForm)
      setEditingId(null)
      load()
    } catch (err) {
      setEditError(err.response?.data?.detail || 'Error al actualizar')
    }
  }

  const present = records.filter((r) => r.status === 'present').length
  const rate = records.length ? Math.round((present / records.length) * 100) : null

  return (
    <div className="page-enter">
      <div className="section-header">
        <div>
          <h2 className="section-title">Mi Asistencia</h2>
          <p className="section-subtitle">Registro diario de asistencia al campo clínico</p>
        </div>
        <button onClick={() => { setShowForm(!showForm); setSuccess(false) }} className="btn btn-primary">
          {showForm ? <><X size={15} /> Cancelar</> : <><Plus size={15} /> Registrar</>}
        </button>
      </div>

      <AlertSuccess>{success && 'Asistencia registrada correctamente.'}</AlertSuccess>

      {/* Resumen rápido si hay registros */}
      {!loading && records.length > 0 && rate !== null && (
        <div className="card" style={{ padding: '1.25rem 1.5rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--color-ink-700)' }}>Tasa de asistencia</span>
              <span style={{ fontSize: '0.875rem', color: 'var(--color-ink-500)' }}>{present} / {records.length} días</span>
            </div>
            <div className="progress-track">
              <div className="progress-fill" style={{
                width: `${rate}%`,
                background: rate >= 75 ? '#16a34a' : rate >= 50 ? '#d97706' : '#dc2626',
              }} />
            </div>
          </div>
          <div style={{ textAlign: 'right', flexShrink: 0 }}>
            <p style={{
              fontFamily: 'var(--font-display)', fontSize: '1.75rem', fontWeight: 500, margin: 0, lineHeight: 1,
              color: rate >= 75 ? 'var(--color-ok-text)' : rate >= 50 ? 'var(--color-warn-text)' : 'var(--color-err-text)',
            }}>
              {rate}%
            </p>
          </div>
        </div>
      )}

      {/* Form */}
      {showForm && (
        <div className="card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1rem', fontWeight: 500, color: 'var(--color-ink-700)', marginBottom: '1rem' }}>
            Nuevo registro
          </h3>
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxWidth: 480 }}>
            <div className="form-grid-2">
              <div className="field">
                <label className="label">Fecha</label>
                <input type="date" value={form.date}
                  onChange={(e) => setForm({ ...form, date: e.target.value })}
                  required className="input" max={today()} />
              </div>
              <div className="field">
                <label className="label">Estado</label>
                <select value={form.status}
                  onChange={(e) => setForm({ ...form, status: e.target.value })}
                  className="input">
                  {STATUS_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="field">
              <label className="label">
                Observación <span style={{ color: 'var(--color-ink-300)', fontWeight: 400 }}>(opcional)</span>
              </label>
              <input type="text" value={form.observation}
                onChange={(e) => setForm({ ...form, observation: e.target.value })}
                placeholder="Ej: Cita médica, enfermedad..."
                className="input" />
            </div>
            <AlertError>{submitError}</AlertError>
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button type="submit" disabled={submitting} className="btn btn-primary">
                {submitting ? 'Guardando...' : 'Guardar'}
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
        records.length === 0 ? (
          <div className="card">
            <EmptyState icon={CalendarCheck} title="Sin registros" description="Aún no tienes registros de asistencia." />
          </div>
        ) : (
          <div className="card table-scroll">
            <table className="table">
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Estado</th>
                  <th>Observación</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {records.map((rec) => (
                  <tr key={rec.id}>
                    <td style={{ fontWeight: 500 }}>{rec.date}</td>
                    <td>
                      {editingId === rec.id ? (
                        <select value={editForm.status}
                          onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                          className="input" style={{ maxWidth: 140 }}>
                          {STATUS_OPTIONS.map((o) => (
                            <option key={o.value} value={o.value}>{o.label}</option>
                          ))}
                        </select>
                      ) : (
                        <AttendanceBadge status={rec.status} />
                      )}
                    </td>
                    <td style={{ color: 'var(--color-ink-500)' }}>
                      {editingId === rec.id ? (
                        <input value={editForm.observation}
                          onChange={(e) => setEditForm({ ...editForm, observation: e.target.value })}
                          className="input" style={{ maxWidth: 240 }} />
                      ) : (
                        rec.observation || <span style={{ color: 'var(--color-ink-300)' }}>—</span>
                      )}
                    </td>
                    <td>
                      {editingId === rec.id ? (
                        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                          <button onClick={() => handleEditSave(rec.id)} className="btn btn-primary btn-sm">
                            <Check size={13} /> Guardar
                          </button>
                          <button onClick={() => setEditingId(null)} className="btn btn-secondary btn-sm">
                            <X size={13} />
                          </button>
                          {editError && <span style={{ fontSize: '0.75rem', color: 'var(--color-err-text)' }}>{editError}</span>}
                        </div>
                      ) : (
                        <button onClick={() => startEdit(rec)} className="btn btn-secondary btn-sm">
                          <Pencil size={13} /> Editar
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      )}
    </div>
  )
}
