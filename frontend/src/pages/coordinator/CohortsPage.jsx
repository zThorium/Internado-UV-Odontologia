import { useEffect, useState } from 'react'
import api from '../../services/api'
import Spinner from '../../components/ui/Spinner'
import { AlertError } from '../../components/ui/Alert'
import EmptyState from '../../components/ui/EmptyState'
import { Layers3, Plus, X, Calendar, Power } from 'lucide-react'

const EMPTY_FORM = {
  name: '',
  year: new Date().getFullYear(),
  semester: 1,
  is_active: true,
}

export default function CohortsPage() {
  const [cohorts, setCohorts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(EMPTY_FORM)
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await api.get('/dashboard/cohorts')
      setCohorts(data)
    } catch {
      setError('Error al cargar las cohortes')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setForm((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }))
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    setFormError(null)
    setSubmitting(true)
    try {
      await api.post('/dashboard/cohorts', {
        ...form,
        year: Number(form.year),
        semester: Number(form.semester),
      })
      setForm(EMPTY_FORM)
      setShowForm(false)
      await load()
    } catch (err) {
      setFormError(err.response?.data?.detail || 'No se pudo crear la cohorte')
    } finally {
      setSubmitting(false)
    }
  }

  const toggleStatus = async (cohort) => {
    setError(null)
    try {
      await api.patch(`/dashboard/cohorts/${cohort.id}`, {
        is_active: !cohort.is_active,
      })
      await load()
    } catch (err) {
      setError(err.response?.data?.detail || 'No se pudo actualizar el estado de la cohorte')
    }
  }

  const activeCount = cohorts.filter((c) => c.is_active).length

  return (
    <div className="page-enter">
      <div className="section-header">
        <div>
          <h2 className="section-title">Cohortes</h2>
          <p className="section-subtitle">Crea y administra periodos académicos del internado</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="btn btn-primary">
          <Plus size={15} /> Nueva cohorte
        </button>
      </div>

      {showForm && (
        <div className="card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.125rem', fontWeight: 500, margin: 0 }}>
              Crear cohorte
            </h3>
            <button onClick={() => setShowForm(false)} className="btn btn-ghost btn-sm"><X size={15} /></button>
          </div>

          <form onSubmit={handleCreate} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="field">
              <label className="label">Año</label>
              <input
                type="number"
                name="year"
                value={form.year}
                min={2020}
                max={2100}
                onChange={handleChange}
                required
                className="input"
              />
            </div>

            <div className="field">
              <label className="label">Semestre</label>
              <select name="semester" value={form.semester} onChange={handleChange} required className="input">
                <option value={1}>Semestre 1</option>
                <option value={2}>Semestre 2</option>
              </select>
            </div>

            <div className="field" style={{ gridColumn: '1 / -1' }}>
              <label className="label">Nombre (opcional)</label>
              <input
                type="text"
                name="name"
                value={form.name}
                onChange={handleChange}
                className="input"
                placeholder={`Internado ${form.year}-${form.semester}`}
              />
            </div>

            <div style={{ gridColumn: '1 / -1', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                id="cohort-active"
                type="checkbox"
                name="is_active"
                checked={form.is_active}
                onChange={handleChange}
              />
              <label htmlFor="cohort-active" style={{ fontSize: '0.875rem', color: 'var(--color-ink-600)' }}>
                Crear como cohorte activa
              </label>
            </div>

            <div style={{ gridColumn: '1 / -1' }}>
              <AlertError>{formError}</AlertError>
              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem' }}>
                <button type="submit" disabled={submitting} className="btn btn-primary">
                  {submitting ? 'Creando...' : 'Crear cohorte'}
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
        cohorts.length === 0 ? (
          <div className="card">
            <EmptyState icon={Layers3} title="Sin cohortes" description="Aún no hay cohortes registradas." />
          </div>
        ) : (
          <div className="card" style={{ overflow: 'hidden' }}>
            <div style={{
              padding: '0.875rem 1.5rem',
              borderBottom: '1px solid var(--color-ink-100)',
              display: 'flex', alignItems: 'center', gap: '0.5rem',
            }}>
              <Calendar size={14} style={{ color: 'var(--color-uv-500)' }} />
              <span style={{ fontSize: '0.8125rem', color: 'var(--color-ink-500)' }}>
                {activeCount} cohorte{activeCount !== 1 ? 's' : ''} activa{activeCount !== 1 ? 's' : ''} de {cohorts.length}
              </span>
            </div>

            <table className="table">
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Año</th>
                  <th>Semestre</th>
                  <th>Estado</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody className="stagger">
                {cohorts.map((cohort) => (
                  <tr key={cohort.id}>
                    <td style={{ fontWeight: 500 }}>{cohort.name}</td>
                    <td>{cohort.year}</td>
                    <td>{cohort.semester}</td>
                    <td>
                      <span className={`badge ${cohort.is_active ? 'badge-green' : 'badge-gray'}`}>
                        {cohort.is_active ? 'Activa' : 'Inactiva'}
                      </span>
                    </td>
                    <td>
                      <button
                        onClick={() => toggleStatus(cohort)}
                        className="btn btn-secondary btn-sm"
                      >
                        <Power size={13} /> {cohort.is_active ? 'Desactivar' : 'Activar'}
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
