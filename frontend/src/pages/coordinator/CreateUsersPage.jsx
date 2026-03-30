import { useState } from 'react'
import api from '../../services/api'
import { AlertError, AlertSuccess } from '../../components/ui/Alert'
import Spinner from '../../components/ui/Spinner'
import { UserPlus, Plus, X } from 'lucide-react'

const EMPTY_FORM = { email: '', password: '', full_name: '', role: 'student' }

export default function CreateUsersPage() {
  const [form, setForm] = useState(EMPTY_FORM)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [createdCount, setCreatedCount] = useState(0)

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setSubmitting(true)

    try {
      const response = await api.post('/auth/create-user', form)
      
      setSuccess(`${form.role === 'student' ? 'Estudiante' : 'Tutor'} creado: ${response.data.email}`)
      setCreatedCount(prev => prev + 1)
      setForm(EMPTY_FORM)
      
    } catch (err) {
      const message = err.response?.data?.detail || err.message
      setError(`Error creando usuario: ${message}`)
    } finally {
      setSubmitting(false)
    }
  }

  const handleCreateAnother = () => {
    setSuccess('')
    setShowForm(true)
    setForm(EMPTY_FORM)
  }

  return (
    <div className="page-enter">
      <div className="section-header">
        <div>
          <h2 className="section-title">Crear Usuario</h2>
          <p className="section-subtitle">Crea nuevas cuentas para estudiantes y tutores clínicos</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="btn btn-primary">
          <Plus size={15} /> {showForm ? 'Cerrar' : 'Nuevo usuario'}
        </button>
      </div>

      {/* Formulario */}
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

          {error && <div className="alert alert-error" style={{ marginBottom: '1rem' }}>{error}</div>}

          <form onSubmit={handleSubmit} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            {/* Email */}
            <div className="field">
              <label className="label">Email</label>
              <input
                type="email"
                name="email"
                value={form.email}
                onChange={handleChange}
                placeholder="usuario@uv.cl"
                className="input"
                disabled={submitting}
                required
              />
            </div>

            {/* Nombre Completo */}
            <div className="field">
              <label className="label">Nombre completo</label>
              <input
                type="text"
                name="full_name"
                value={form.full_name}
                onChange={handleChange}
                placeholder="Juan Pérez García"
                className="input"
                disabled={submitting}
                required
              />
            </div>

            {/* Contraseña */}
            <div className="field">
              <label className="label">Contraseña</label>
              <input
                type="password"
                name="password"
                value={form.password}
                onChange={handleChange}
                placeholder="Mínimo 8 caracteres"
                className="input"
                disabled={submitting}
                required
                minLength="8"
              />
            </div>

            {/* Rol */}
            <div className="field">
              <label className="label">Rol</label>
              <select
                name="role"
                value={form.role}
                onChange={handleChange}
                className="input"
                disabled={submitting}
                required
              >
                <option value="student">Estudiante</option>
                <option value="tutor">Tutor Clínico</option>
              </select>
            </div>

            {/* Botones */}
            <div style={{ gridColumn: '1 / -1', display: 'flex', gap: '0.75rem', marginTop: '0.5rem' }}>
              <button
                type="submit"
                disabled={submitting}
                className="btn btn-primary"
              >
                {submitting ? <>
                  <span className="spinner" style={{ width: '1rem', height: '1rem' }} /> Creando...
                </> : <>
                  <UserPlus size={15} /> Crear usuario
                </>}
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="btn btn-secondary"
              >
                Cancelar
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Resumen de éxito */}
      {success && (
        <div className="card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
          <div className="alert alert-success" style={{ marginBottom: '1rem' }}>{success}</div>
          {createdCount > 0 && (
            <p style={{ fontSize: '0.875rem', color: 'var(--color-ink-500)', margin: '0 0 1rem' }}>
              {createdCount} usuario{createdCount !== 1 ? 's' : ''} creado{createdCount !== 1 ? 's' : ''} exitosamente
            </p>
          )}
          <button
            onClick={handleCreateAnother}
            className="btn btn-primary"
          >
            <Plus size={15} /> Crear otro usuario
          </button>
        </div>
      )}

      {/* Información */}
      <div className="card" style={{ padding: '1.5rem' }}>
        <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1rem', fontWeight: 500, margin: '0 0 0.75rem', color: 'var(--color-ink-900)' }}>
          Información importante
        </h3>
        <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.875rem', color: 'var(--color-ink-500)', lineHeight: '1.6' }}>
          <li>El email debe ser único en el sistema</li>
          <li>La contraseña debe tener mínimo 8 caracteres</li>
          <li>Puedes crear estudiantes y tutores clínicos</li>
          <li>El usuario podrá cambiar su contraseña después</li>
          <li>Se recomienda usar emails institucionales (@uv.cl)</li>
        </ul>
      </div>
    </div>
  )
}
