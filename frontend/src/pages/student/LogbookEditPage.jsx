import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import api from '../../services/api'
import Spinner from '../../components/ui/Spinner'
import { AlertError } from '../../components/ui/Alert'
import { Plus, Trash2, ArrowLeft } from 'lucide-react'

const emptyProcedure = () => ({ name: '', description: '', quantity: 1 })

export default function LogbookEditPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [entry, setEntry] = useState(null)
  const [weekNumber, setWeekNumber] = useState('')
  const [weekStartDate, setWeekStartDate] = useState('')
  const [wellbeingStatus, setWellbeingStatus] = useState('')
  const [careLevel, setCareLevel] = useState('primary')
  const [allowedProcedures, setAllowedProcedures] = useState([])
  const [procedures, setProcedures] = useState([emptyProcedure()])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    Promise.all([
      api.get(`/logbook/entries/${id}`),
      api.get('/logbook/my-context'),
    ])
      .then(([entryRes, contextRes]) => {
        const data = entryRes.data
        const context = contextRes.data

        setEntry(data)
        setWeekNumber(String(data.week_number || ''))
        setWeekStartDate(data.week_start_date || '')
        setWellbeingStatus(data.wellbeing_status || '')
        setCareLevel(context.care_level || 'primary')

        const catalog = Array.isArray(context.allowed_procedures) ? context.allowed_procedures : []
        const currentNames = (data.procedures || []).map((p) => p.name).filter(Boolean)
        const mergedCatalog = Array.from(new Set([...catalog, ...currentNames]))
        setAllowedProcedures(mergedCatalog)

        if (data.procedures?.length > 0) {
          setProcedures(data.procedures.map((p) => ({
            name: p.name,
            description: p.description || '',
            quantity: p.quantity,
          })))
        }
      })
      .catch(() => setError('Error al cargar la entrada'))
      .finally(() => setLoading(false))
  }, [id])

  const levelLabel = {
    primary: 'Atención primaria',
    secondary: 'Atención secundaria',
    tertiary: 'Atención terciaria',
  }

  const updateProcedure = (index, field, value) =>
    setProcedures((prev) => prev.map((p, i) => i === index ? { ...p, [field]: value } : p))

  const addProcedure = () => setProcedures((prev) => [...prev, emptyProcedure()])

  const removeProcedure = (index) => {
    if (procedures.length === 1) return
    setProcedures((prev) => prev.filter((_, i) => i !== index))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSaving(true)
    try {
      await api.put(`/logbook/entries/${id}`, {
        week_number: parseInt(weekNumber, 10),
        week_start_date: weekStartDate,
        wellbeing_status: wellbeingStatus,
        procedures,
      })
      navigate('/student/logbook')
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al guardar los cambios')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <Spinner />

  if (entry && entry.status !== 'draft') {
    return (
      <div className="page-enter">
        <div className="card" style={{ padding: '2.5rem', textAlign: 'center', maxWidth: 420, margin: '2rem auto' }}>
          <p style={{ color: 'var(--color-ink-500)', marginBottom: '1.25rem' }}>
            Esta entrada no puede editarse porque ya fue enviada.
          </p>
          <button onClick={() => navigate('/student/logbook')} className="btn btn-secondary">
            <ArrowLeft size={15} /> Volver a la bitácora
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="page-enter" style={{ maxWidth: 680 }}>
      <button onClick={() => navigate('/student/logbook')} className="btn btn-ghost btn-sm"
        style={{ marginBottom: '1rem', marginLeft: '-0.5rem' }}>
        <ArrowLeft size={15} /> Volver
      </button>

      <div style={{ marginBottom: '1.75rem' }}>
        <h2 className="section-title">Editar entrada — Semana {entry?.week_number}</h2>
        <p className="section-subtitle">Modifica los procedimientos registrados</p>
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <div className="card" style={{ padding: '1.5rem' }}>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1rem', fontWeight: 500, color: 'var(--color-ink-700)', margin: '0 0 1rem' }}>
            Información general
          </h3>
          <div className="form-grid-2" style={{ marginBottom: '1rem' }}>
            <div className="field" style={{ gridColumn: '1 / -1' }}>
              <input
                type="text"
                value={levelLabel[careLevel] || 'Atención primaria'}
                readOnly
                className="input"
                style={{ background: 'var(--color-bg-surface)' }}
              />
            </div>
            <div className="field">
              <label className="label">Número de semana</label>
              <input
                type="number"
                value={weekNumber}
                onChange={(e) => setWeekNumber(e.target.value)}
                required
                min={1}
                className="input"
                style={{ background: 'var(--color-bg-surface)' }}
              />
            </div>
            <div className="field">
              <label className="label">Fecha de inicio</label>
              <input
                type="date"
                value={weekStartDate}
                onChange={(e) => setWeekStartDate(e.target.value)}
                required
                className="input"
                style={{ background: 'var(--color-bg-surface)' }}
              />
            </div>
            <div className="field" style={{ gridColumn: '1 / -1' }}>
              <label className="label">Estado de bienestar</label>
              <select
                value={wellbeingStatus}
                onChange={(e) => setWellbeingStatus(e.target.value)}
                required
                className="input"
                style={{ background: 'var(--color-bg-surface)' }}
              >
                <option value="">Selecciona una opción</option>
                <option value="good">Bien</option>
                <option value="regular">Regular</option>
                <option value="difficult">Difícil</option>
              </select>
            </div>
          </div>
        </div>

        <div className="card" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1rem', fontWeight: 500, color: 'var(--color-ink-700)', margin: 0 }}>
              Procedimientos
              <span style={{ color: 'var(--color-ink-300)', fontFamily: 'var(--font-body)', fontSize: '0.875rem', fontWeight: 400, marginLeft: '0.375rem' }}>
                ({procedures.length})
              </span>
            </h3>
            <button type="button" onClick={addProcedure} className="btn btn-secondary btn-sm">
              <Plus size={13} /> Agregar
            </button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {procedures.map((proc, i) => (
              <div key={i} style={{
                border: '1px solid var(--color-ink-100)',
                borderRadius: 'var(--radius-md)',
                padding: '1rem',
                background: 'var(--color-ink-50)',
              }}>
                <div className="form-grid-2">
                  <div className="field">
                    <label className="label">Nombre</label>
                    <select
                      value={proc.name}
                      onChange={(e) => updateProcedure(i, 'name', e.target.value)}
                      required
                      className="input"
                      style={{ background: 'var(--color-bg-surface)' }}
                    >
                      <option value="" disabled>Selecciona un procedimiento</option>
                      {allowedProcedures.map((name) => (
                        <option key={name} value={name}>{name}</option>
                      ))}
                    </select>
                  </div>
                  <div className="field">
                    <label className="label">Cantidad</label>
                    <input type="number" value={proc.quantity}
                      onChange={(e) => updateProcedure(i, 'quantity', parseInt(e.target.value, 10))}
                      required min={1} className="input" style={{ background: 'var(--color-bg-surface)' }} />
                  </div>
                  <div className="field" style={{ gridColumn: '1 / -1' }}>
                    <label className="label">
                      Descripción
                      <span style={{ color: 'var(--color-ink-300)', fontWeight: 400, marginLeft: '0.25rem' }}>
                        {proc.name === 'Otro' ? '(obligatoria para "Otro")' : '(opcional)'}
                      </span>
                    </label>
                    <input type="text" value={proc.description}
                      onChange={(e) => updateProcedure(i, 'description', e.target.value)}
                      required={proc.name === 'Otro'}
                      className="input" style={{ background: 'var(--color-bg-surface)' }} />
                  </div>
                </div>
                {procedures.length > 1 && (
                  <button type="button" onClick={() => removeProcedure(i)}
                    className="btn btn-ghost btn-sm"
                    style={{ color: 'var(--color-err-text)', marginTop: '0.5rem' }}>
                    <Trash2 size={13} /> Eliminar
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>

        <AlertError>{error}</AlertError>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button type="submit" disabled={saving} className="btn btn-primary">
            {saving ? 'Guardando...' : 'Guardar cambios'}
          </button>
          <button type="button" onClick={() => navigate('/student/logbook')} className="btn btn-secondary">
            Cancelar
          </button>
        </div>
      </form>
    </div>
  )
}
