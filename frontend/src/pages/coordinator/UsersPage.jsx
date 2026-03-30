import { useEffect, useState } from 'react'
import api from '../../services/api'
import Spinner from '../../components/ui/Spinner'
import { AlertError } from '../../components/ui/Alert'
import EmptyState from '../../components/ui/EmptyState'
import ConfirmModal from '../../components/ui/ConfirmModal'
import { Users, Plus, Pencil, Check, X, UserCheck, GraduationCap, Shield, Trash2 } from 'lucide-react'

const EMPTY_CREATE = { email: '', full_name: '', password: '', role: 'student' }

export default function UsersPage() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [createForm, setCreateForm] = useState(EMPTY_CREATE)
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [editForm, setEditForm] = useState({ full_name: '', is_active: true })
  const [editError, setEditError] = useState(null)
  const [filterRole, setFilterRole] = useState('all')
  const [deletingId, setDeletingId] = useState(null)
  const [deleteError, setDeleteError] = useState(null)
  const [userToDelete, setUserToDelete] = useState(null)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [modalError, setModalError] = useState(null)

  const load = async () => {
    setLoading(true)
    try {
      // Cargar estudiantes y tutores
      const [studentsRes, tutorsRes] = await Promise.all([
        api.get('/dashboard/students'),
        api.get('/dashboard/tutors'),
      ])
      
      const allUsers = [
        ...studentsRes.data.map(u => ({ ...u, role: 'student' })),
        ...tutorsRes.data.map(u => ({ ...u, role: 'tutor' })),
      ]
      
      setUsers(allUsers)
    } catch (err) {
      setError('Error al cargar los usuarios')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    setCreateError(null)
    setCreating(true)
    try {
      await api.post('/auth/create-user', createForm)
      setCreateForm(EMPTY_CREATE)
      setShowForm(false)
      load()
    } catch (err) {
      setCreateError(err.response?.data?.detail || 'Error al crear el usuario')
    } finally {
      setCreating(false)
    }
  }

  const startEdit = (user) => {
    setEditingId(user.id)
    setEditForm({ full_name: user.full_name, is_active: user.is_active })
    setEditError(null)
  }

  const handleEditSave = async (user) => {
    setEditError(null)
    try {
      const endpoint = user.role === 'tutor' ? '/dashboard/tutors' : '/dashboard/students'
      await api.patch(`${endpoint}/${user.id}`, editForm)
      setEditingId(null)
      load()
    } catch (err) {
      setEditError(err.response?.data?.detail || 'Error al actualizar')
    }
  }

  const handleDelete = async (user) => {
    setUserToDelete(user)
    setShowDeleteModal(true)
    setModalError(null)
  }

  const confirmDelete = async () => {
    if (!userToDelete) return
    
    setModalError(null)
    setDeletingId(userToDelete.id)
    try {
      const endpoint = userToDelete.role === 'tutor' ? '/dashboard/tutors' : '/dashboard/students'
      await api.delete(`${endpoint}/${userToDelete.id}`)
      
      // Solo cerrar el modal y recargar si la eliminación fue exitosa
      setShowDeleteModal(false)
      setUserToDelete(null)
      load()
    } catch (err) {
      // Mostrar error en el modal sin cerrarlo
      const errorMessage = err.response?.data?.detail || 'Error al eliminar usuario. Por favor, intenta nuevamente.'
      setModalError(errorMessage)
    } finally {
      setDeletingId(null)
    }
  }

  const getRoleIcon = (role) => {
    switch (role) {
      case 'student': return <GraduationCap size={14} />
      case 'tutor': return <UserCheck size={14} />
      case 'coordinator': return <Shield size={14} />
      default: return null
    }
  }

  const getRoleLabel = (role) => {
    switch (role) {
      case 'student': return 'Estudiante'
      case 'tutor': return 'Tutor'
      case 'coordinator': return 'Coordinador'
      default: return role
    }
  }

  const getRoleColor = (role) => {
    switch (role) {
      case 'student': return 'var(--color-sky-600)'
      case 'tutor': return 'var(--color-uv-600)'
      case 'coordinator': return 'var(--color-earth-600)'
      default: return 'var(--color-ink-600)'
    }
  }

  const filteredUsers = filterRole === 'all' 
    ? users 
    : users.filter(u => u.role === filterRole)

  const activeCount = filteredUsers.filter(u => u.is_active).length

  return (
    <div className="page-enter">
      <ConfirmModal
        isOpen={showDeleteModal}
        onClose={() => {
          setShowDeleteModal(false)
          setUserToDelete(null)
          setModalError(null)
        }}
        onConfirm={confirmDelete}
        title={`¿Eliminar a ${userToDelete?.full_name}?`}
        message="Esta acción eliminará permanentemente al usuario y todos sus datos asociados. No se puede deshacer."
        confirmLabel="Eliminar usuario"
        cancelLabel="Cancelar"
        isDestructive={true}
        loading={deletingId === userToDelete?.id}
        error={modalError}
      />

      <div className="section-header">
        <div>
          <h2 className="section-title">Usuarios</h2>
          <p className="section-subtitle">Gestiona estudiantes, tutores y coordinadores</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="btn btn-primary">
          <Plus size={15} /> Nuevo usuario
        </button>
      </div>

      {/* Create form */}
      {showForm && (
        <div className="card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.125rem', fontWeight: 500, margin: 0 }}>
              Nuevo usuario
            </h3>
            <button onClick={() => setShowForm(false)} className="btn btn-ghost btn-sm">
              <X size={15} />
            </button>
          </div>
          <form onSubmit={handleCreate} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="field">
              <label className="label">Rol</label>
              <select
                value={createForm.role}
                onChange={(e) => setCreateForm({ ...createForm, role: e.target.value })}
                required
                className="input"
              >
                <option value="student">Estudiante</option>
                <option value="tutor">Tutor</option>
              </select>
            </div>
            <div className="field">
              <label className="label">Email</label>
              <input
                type="email"
                value={createForm.email}
                onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
                required
                className="input"
                placeholder="usuario@uv.cl"
              />
            </div>
            <div className="field">
              <label className="label">Nombre completo</label>
              <input
                type="text"
                value={createForm.full_name}
                onChange={(e) => setCreateForm({ ...createForm, full_name: e.target.value })}
                required
                className="input"
                placeholder="Nombre Apellido"
              />
            </div>
            <div className="field">
              <label className="label">Contraseña</label>
              <input
                type="password"
                value={createForm.password}
                onChange={(e) => setCreateForm({ ...createForm, password: e.target.value })}
                required
                minLength={8}
                className="input"
                placeholder="Mínimo 8 caracteres"
              />
            </div>
            <div style={{ gridColumn: '1 / -1' }}>
              <AlertError>{createError}</AlertError>
              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem' }}>
                <button type="submit" disabled={creating} className="btn btn-primary">
                  {creating ? 'Creando...' : 'Crear usuario'}
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
      <AlertError>{deleteError}</AlertError>

      {!loading && !error && (
        users.length === 0 ? (
          <div className="card">
            <EmptyState icon={Users} title="Sin usuarios" description="No hay usuarios registrados." />
          </div>
        ) : (
          <div className="card" style={{ overflow: 'hidden' }}>
            {/* Filters */}
            <div style={{
              padding: '1rem 1.5rem',
              borderBottom: '1px solid var(--color-ink-100)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '1rem',
            }}>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  onClick={() => setFilterRole('all')}
                  className={`btn btn-sm ${filterRole === 'all' ? 'btn-primary' : 'btn-secondary'}`}
                >
                  Todos ({users.length})
                </button>
                <button
                  onClick={() => setFilterRole('student')}
                  className={`btn btn-sm ${filterRole === 'student' ? 'btn-primary' : 'btn-secondary'}`}
                >
                  <GraduationCap size={13} /> Estudiantes ({users.filter(u => u.role === 'student').length})
                </button>
                <button
                  onClick={() => setFilterRole('tutor')}
                  className={`btn btn-sm ${filterRole === 'tutor' ? 'btn-primary' : 'btn-secondary'}`}
                >
                  <UserCheck size={13} /> Tutores ({users.filter(u => u.role === 'tutor').length})
                </button>
              </div>
              <span style={{ fontSize: '0.8125rem', color: 'var(--color-ink-500)' }}>
                {activeCount} activo{activeCount !== 1 ? 's' : ''} de {filteredUsers.length}
              </span>
            </div>

            {/* Table */}
            <table className="table">
              <thead>
                <tr>
                  <th>Usuario</th>
                  <th>Email</th>
                  <th>Rol</th>
                  <th>Estado</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody className="stagger">
                {filteredUsers.map((user) => (
                  <tr key={user.id}>
                    <td>
                      {editingId === user.id ? (
                        <input
                          value={editForm.full_name}
                          onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })}
                          className="input"
                          style={{ maxWidth: 220 }}
                        />
                      ) : (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
                          <div style={{
                            width: 32,
                            height: 32,
                            borderRadius: '50%',
                            background: 'var(--color-uv-100)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            flexShrink: 0,
                          }}>
                            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-uv-700)' }}>
                              {user.full_name?.charAt(0)?.toUpperCase() || '?'}
                            </span>
                          </div>
                          <span style={{ fontWeight: 500 }}>{user.full_name}</span>
                        </div>
                      )}
                    </td>
                    <td style={{ color: 'var(--color-ink-500)', fontSize: '0.875rem' }}>{user.email}</td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', color: getRoleColor(user.role) }}>
                        {getRoleIcon(user.role)}
                        <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>{getRoleLabel(user.role)}</span>
                      </div>
                    </td>
                    <td>
                      {editingId === user.id ? (
                        <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                          <input
                            type="checkbox"
                            checked={editForm.is_active}
                            onChange={(e) => setEditForm({ ...editForm, is_active: e.target.checked })}
                          />
                          <span style={{ fontSize: '0.875rem' }}>Activo</span>
                        </label>
                      ) : (
                        <span className={`badge ${user.is_active ? 'badge-green' : 'badge-gray'}`}>
                          {user.is_active ? 'Activo' : 'Inactivo'}
                        </span>
                      )}
                    </td>
                    <td>
                      {editingId === user.id ? (
                        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                          <button onClick={() => handleEditSave(user)} className="btn btn-primary btn-sm">
                            <Check size={13} /> Guardar
                          </button>
                          <button onClick={() => setEditingId(null)} className="btn btn-secondary btn-sm">
                            <X size={13} />
                          </button>
                          {editError && (
                            <span style={{ fontSize: '0.75rem', color: 'var(--color-err-text)' }}>{editError}</span>
                          )}
                        </div>
                      ) : (
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                          <button onClick={() => startEdit(user)} className="btn btn-secondary btn-sm">
                            <Pencil size={13} /> Editar
                          </button>
                          <button 
                            onClick={() => handleDelete(user)} 
                            disabled={deletingId === user.id}
                            className="btn btn-sm"
                            style={{ 
                              color: 'var(--color-err-text)', 
                              borderColor: 'var(--color-err-border)',
                              backgroundColor: 'var(--color-err-bg)'
                            }}
                          >
                            <Trash2 size={13} /> {deletingId === user.id ? 'Eliminando...' : 'Eliminar'}
                          </button>
                        </div>
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
