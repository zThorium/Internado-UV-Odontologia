import { useEffect, useState } from 'react'
import api from '../../services/api'
import Spinner from '../../components/ui/Spinner'
import { AlertError } from '../../components/ui/Alert'
import EmptyState from '../../components/ui/EmptyState'
import { Users, Plus, X, MapPin } from 'lucide-react'

const EMPTY_FORM = {
  student_id: '', tutor_id: '', cohort_id: '',
  care_level: 'primary',
  clinical_site: '', start_date: '', end_date: '',
}

const CARE_LEVEL_LABEL = {
  primary: 'Atención primaria',
  secondary: 'Atención secundaria',
  tertiary: 'Atención terciaria',
}

export default function AssignmentsPage() {
  const [assignments, setAssignments] = useState([])
  const [students, setStudents] = useState([])
  const [tutors, setTutors] = useState([])
  const [cohorts, setCohorts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [form, setForm] = useState(EMPTY_FORM)
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState(null)
  const [showForm, setShowForm] = useState(false)

  const load = () => {
    setLoading(true)
    api.get('/dashboard/assignments')
      .then(({ data }) => setAssignments(data))
      .catch(() => setError('Error al cargar las asignaciones'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
    api.get('/dashboard/students').then(({ data }) => setStudents(data)).catch(() => {})
    api.get('/dashboard/tutors').then(({ data }) => setTutors(data)).catch(() => {})
    api.get('/dashboard/cohorts').then(({ data }) => setCohorts(data)).catch(() => {})
  }, [])

  const handleDeactivate = (id) => {
    api.patch(`/dashboard/assignments/${id}/deactivate`)
      .then(() => load())
      .catch(() => alert('Error al desactivar la asignación'))
  }

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setFormError(null)
    setSubmitting(true)
    try {
      await api.post('/dashboard/assignments', form)
      setForm(EMPTY_FORM)
      setShowForm(false)
      load()
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Error al crear la asignación')
    } finally {
      setSubmitting(false)
    }
  }

  const active = assignments.filter((a) => a.is_active).length

  return (
    <div className="page-enter">
      <div className="section-header">
        <div>
          <h2 className="section-title">Asignaciones</h2>
          <p className="section-subtitle">Gestiona las asignaciones tutor-estudiante por sede clínica</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="btn btn-primary">
          <Plus size={15} /> Nueva asignación
        </button>
      </div>

      {showForm && (
        <div className="card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.125rem', fontWeight: 500, margin: 0 }}>
              Nueva asignación
            </h3>
            <button onClick={() => setShowForm(false)} className="btn btn-ghost btn-sm"><X size={15} /></button>
          </div>
          <form onSubmit={handleSubmit} className="form-grid-2">
            {/* Estudiante */}
            <div className="field">
              <label className="label">Estudiante</label>
              <select name="student_id" value={form.student_id} onChange={handleChange} required className="input">
                <option value="">Seleccionar estudiante...</option>
                {students.map((s) => (
                  <option key={s.id} value={s.id}>{s.full_name}</option>
                ))}
              </select>
            </div>

            {/* Tutor */}
            <div className="field">
              <label className="label">Tutor</label>
              <select name="tutor_id" value={form.tutor_id} onChange={handleChange} required className="input">
                <option value="">Seleccionar tutor...</option>
                {tutors.map((t) => (
                  <option key={t.id} value={t.id}>{t.full_name}</option>
                ))}
              </select>
            </div>

            {/* Cohorte */}
            <div className="field">
              <label className="label">Cohorte</label>
              <select name="cohort_id" value={form.cohort_id} onChange={handleChange} required className="input">
                <option value="">Seleccionar cohorte...</option>
                {cohorts.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} {!c.is_active && '(Inactivo)'}
                  </option>
                ))}
              </select>
            </div>

            {/* Sede */}
            <div className="field">
              <label className="label">Sede clínica</label>
              <input
                name="clinical_site"
                value={form.clinical_site}
                onChange={handleChange}
                required
                className="input"
                placeholder="Ej: Hospital Regional Valparaíso"
              />
            </div>

            <div className="field">
              <label className="label">Nivel de atención</label>
              <select name="care_level" value={form.care_level} onChange={handleChange} required className="input">
                <option value="primary">Atención primaria</option>
                <option value="secondary">Atención secundaria</option>
                <option value="tertiary">Atención terciaria</option>
              </select>
            </div>

            <div className="field">
              <label className="label">Fecha inicio</label>
              <input type="date" name="start_date" value={form.start_date} onChange={handleChange} required className="input" />
            </div>
            <div className="field">
              <label className="label">
                Fecha fin
                <span style={{ color: 'var(--color-ink-300)', fontWeight: 400, marginLeft: '0.25rem', fontSize: '0.8125rem' }}>
                  (opcional)
                </span>
              </label>
              <input type="date" name="end_date" value={form.end_date} onChange={handleChange} className="input" />
            </div>

            <div style={{ gridColumn: '1 / -1' }}>
              <AlertError>{formError}</AlertError>
              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem' }}>
                <button type="submit" disabled={submitting} className="btn btn-primary">
                  {submitting ? 'Guardando...' : 'Crear asignación'}
                </button>
                <button type="button" onClick={() => setShowForm(false)} className="btn btn-secondary">
                  Cancelar
                </button>
              </div>
            </div>
          </form>
        </div>
      )}

      {loading && <Spinner />}
      <AlertError>{error}</AlertError>

      {!loading && !error && (
        assignments.length === 0 ? (
          <div className="card">
            <EmptyState icon={Users} title="Sin asignaciones" description="No hay asignaciones registradas." />
          </div>
        ) : (
          <div className="card table-scroll">
            <div style={{
              padding: '0.875rem 1.5rem',
              borderBottom: '1px solid var(--color-ink-100)',
              display: 'flex', alignItems: 'center', gap: '0.5rem',
            }}>
              <MapPin size={14} style={{ color: 'var(--color-uv-500)' }} />
              <span style={{ fontSize: '0.8125rem', color: 'var(--color-ink-500)' }}>
                {active} asignación{active !== 1 ? 'es' : ''} activa{active !== 1 ? 's' : ''} de {assignments.length} total
              </span>
            </div>
            <table className="table">
              <thead>
                <tr>
                  <th>Estudiante</th>
                  <th>Tutor</th>
                  <th>Sede</th>
                  <th>Nivel</th>
                  <th>Estado</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody className="stagger">
                {assignments.map((a) => (
                  <tr key={a.id}>
                    <td style={{ fontWeight: 500 }}>{a.student_name ?? '—'}</td>
                    <td style={{ color: 'var(--color-ink-600)' }}>{a.tutor_name ?? '—'}</td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                        <MapPin size={13} style={{ color: 'var(--color-earth-500)', flexShrink: 0 }} />
                        <span style={{ fontWeight: 500 }}>{a.clinical_site}</span>
                      </div>
                    </td>
                    <td>
                      <span className="badge badge-blue">
                        {CARE_LEVEL_LABEL[a.care_level] || 'Atención primaria'}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${a.is_active ? 'badge-green' : 'badge-gray'}`}>
                        {a.is_active ? 'Activo' : 'Inactivo'}
                      </span>
                    </td>
                    <td>
                      <button
                        onClick={() => handleDeactivate(a.id)}
                        disabled={!a.is_active}
                        className="btn btn-secondary btn-sm"
                      >
                        Desactivar
                      </button>
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
