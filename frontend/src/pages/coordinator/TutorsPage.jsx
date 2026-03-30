import { useEffect, useState } from 'react'
import api from '../../services/api'
import Spinner from '../../components/ui/Spinner'
import { AlertError } from '../../components/ui/Alert'
import EmptyState from '../../components/ui/EmptyState'
import { UserCheck, Plus, Pencil, Check, X } from 'lucide-react'

const EMPTY_CREATE = { email: '', full_name: '', password: '' }

export default function TutorsPage() {
  const [tutors, setTutors] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [createForm, setCreateForm] = useState(EMPTY_CREATE)
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [editForm, setEditForm] = useState({ full_name: '', is_active: true })
  const [editError, setEditError] = useState(null)

  const load = () => {
    setLoading(true)
    api.get('/dashboard/tutors')
      .then(({ data }) => setTutors(data))
      .catch(() => setError('Error al cargar los tutores'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    setCreateError(null)
    setCreating(true)
    try {
      await api.post('/dashboard/tutors', createForm)
      setCreateForm(EMPTY_CREATE)
      setShowForm(false)
      load()
    } catch (err) {
      setCreateError(err.response?.data?.detail || 'Error al crear el tutor')
    } finally {
      setCreating(false)
    }
  }

  const startEdit = (tutor) => {
    setEditingId(tutor.id)
    setEditForm({ full_name: tutor.full_name, is_active: tutor.is_active })
    setEditError(null)
  }

  const handleEditSave = async (id) => {
    setEditError(null)
    try {
      await api.patch(`/dashboard/tutors/${id}`, editForm)
      setEditingId(null)
      load()
    } catch (err) {
      setEditError(err.response?.data?.detail || 'Error al actualizar')
    }
  }

  const active = tutors.filter((t) => t.is_active).length

  return (
    <div className="page-enter">
      <div className="section-header">
        <div>
          <h2 className="section-title">Tutores</h2>
          <p className="section-subtitle">Gestiona los tutores clínicos del internado</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="btn btn-primary">
          <Plus size={15} /> Nuevo tutor
        </button>
      </div>

      {/* Create form */}
      {showForm && (
        <div className="card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.125rem', fontWeight: 500, margin: 0 }}>Nuevo tutor</h3>
            <button onClick={() => setShowForm(false)} className="btn btn-ghost btn-sm"><X size={15} /></button>
          </div>
          <form onSubmit={handleCreate} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="field">
              <label className="label">Email</label>
              <input type="email" value={createForm.email}
                onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
                required className="input" placeholder="tutor@uv.cl" />
            </div>
            <div className="field">
              <label className="label">Nombre completo</label>
              <input type="text" value={createForm.full_name}
                onChange={(e) => setCreateForm({ ...createForm, full_name: e.target.value })}
                required className="input" placeholder="Dr. Nombre Apellido" />
            </div>
            <div className="field">
              <label className="label">Contraseña</label>
              <input type="password" value={createForm.password}
                onChange={(e) => setCreateForm({ ...createForm, password: e.target.value })}
                required className="input" />
            </div>
            <div style={{ gridColumn: '1 / -1' }}>
              <AlertError>{createError}</AlertError>
              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem' }}>
                <button type="submit" disabled={creating} className="btn btn-primary">
                  {creating ? 'Guardando...' : 'Crear tutor'}
                </button>
                <button type="button" onClick={() => setShowForm(false)} className="btn btn-secondary">Cancelar</button>
              </div>
            </div>
          </form>
        </div>
      )}

      {loading && <Spinner />}
      <AlertError>{error}</AlertError>

      {!loading && !error && (
        tutors.length === 0 ? (
          <div className="card">
            <EmptyState icon={UserCheck} title="Sin tutores" description="No hay tutores registrados." />
          </div>
        ) : (
          <div className="card" style={{ overflow: 'hidden' }}>
            <div style={{
              padding: '0.875rem 1.5rem',
              borderBottom: '1px solid var(--color-ink-100)',
              display: 'flex', alignItems: 'center', gap: '0.5rem',
            }}>
              <UserCheck size={14} style={{ color: 'var(--color-uv-500)' }} />
              <span style={{ fontSize: '0.8125rem', color: 'var(--color-ink-500)' }}>
                {active} tutor{active !== 1 ? 'es' : ''} activo{active !== 1 ? 's' : ''} de {tutors.length} total
              </span>
            </div>
            <table className="table">
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Email</th>
                  <th>Estado</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody className="stagger">
                {tutors.map((tutor) => (
                  <tr key={tutor.id}>
                    <td>
                      {editingId === tutor.id ? (
                        <input
                          value={editForm.full_name}
                          onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })}
                          className="input"
                          style={{ maxWidth: 220 }}
                        />
                      ) : (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
                          <div style={{
                            width: 32, height: 32, borderRadius: '50%',
                            background: 'var(--color-uv-100)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            flexShrink: 0,
                          }}>
                            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-uv-700)' }}>
                              {tutor.full_name?.charAt(0)?.toUpperCase() || '?'}
                            </span>
                          </div>
                          <span style={{ fontWeight: 500 }}>{tutor.full_name}</span>
                        </div>
                      )}
                    </td>
                    <td style={{ color: 'var(--color-ink-500)', fontSize: '0.875rem' }}>{tutor.email}</td>
                    <td>
                      {editingId === tutor.id ? (
                        <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                          <input
                            type="checkbox"
                            checked={editForm.is_active}
                            onChange={(e) => setEditForm({ ...editForm, is_active: e.target.checked })}
                          />
                          <span style={{ fontSize: '0.875rem' }}>Activo</span>
                        </label>
                      ) : (
                        <span className={`badge ${tutor.is_active ? 'badge-green' : 'badge-gray'}`}>
                          {tutor.is_active ? 'Activo' : 'Inactivo'}
                        </span>
                      )}
                    </td>
                    <td>
                      {editingId === tutor.id ? (
                        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                          <button onClick={() => handleEditSave(tutor.id)} className="btn btn-primary btn-sm">
                            <Check size={13} /> Guardar
                          </button>
                          <button onClick={() => setEditingId(null)} className="btn btn-secondary btn-sm">
                            <X size={13} />
                          </button>
                          {editError && <span style={{ fontSize: '0.75rem', color: 'var(--color-err-text)' }}>{editError}</span>}
                        </div>
                      ) : (
                        <button onClick={() => startEdit(tutor)} className="btn btn-secondary btn-sm">
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
