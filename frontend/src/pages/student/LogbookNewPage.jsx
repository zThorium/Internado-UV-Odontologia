import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../../services/api'
import { AlertError } from '../../components/ui/Alert'
import { Plus, Trash2, ArrowLeft } from 'lucide-react'

const emptyProcedure = () => ({ name: '', description: '', quantity: 1 })

export default function LogbookNewPage() {
  const navigate = useNavigate()
  const [weekNumber, setWeekNumber] = useState('')
  const [weekStartDate, setWeekStartDate] = useState('')
  const [wellbeingStatus, setWellbeingStatus] = useState('')
  const [careLevel, setCareLevel] = useState('primary')
  const [allowedProcedures, setAllowedProcedures] = useState([])
  const [loadingContext, setLoadingContext] = useState(true)
  const [procedures, setProcedures] = useState([emptyProcedure()])
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    api.get('/logbook/my-context')
      .then(({ data }) => {
        setWeekNumber(String(data.week_number || ''))
        setWeekStartDate(data.week_start_date || '')
        setCareLevel(data.care_level || 'primary')
        setAllowedProcedures(Array.isArray(data.allowed_procedures) ? data.allowed_procedures : [])
      })
      .catch((err) => {
        setError(err.response?.data?.detail || 'No se pudo cargar el contexto de bitacora')
      })
      .finally(() => setLoadingContext(false))
  }, [])

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
      await api.post('/logbook/entries', {
        week_number: parseInt(weekNumber, 10),
        week_start_date: weekStartDate,
        wellbeing_status: wellbeingStatus,
        procedures,
      })
      navigate('/student/logbook')
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al guardar la entrada')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="page-enter max-w-2xl">
      <button onClick={() => navigate('/student/logbook')} className="btn btn-ghost btn-sm mb-4 -ml-2">
        <ArrowLeft size={15} /> Volver
      </button>
      <h2 className="text-xl font-semibold text-slate-800 mb-6">Nueva entrada de bitacora</h2>

      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        <div className="card p-6">
          <h3 className="font-medium text-slate-700 mb-4">Informacion general</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="field sm:col-span-2">
              <label className="label">Nivel de atención asignado</label>
              <input type="text" value={levelLabel[careLevel] || 'Atención primaria'} readOnly className="input" />
            </div>
            <div className="field">
              <label className="label">Numero de semana</label>
              <input type="number" value={weekNumber} onChange={(e) => setWeekNumber(e.target.value)}
                required min={1} className="input" placeholder="1" disabled={loadingContext} />
            </div>
            <div className="field">
              <label className="label">Fecha de inicio</label>
              <input type="date" value={weekStartDate} onChange={(e) => setWeekStartDate(e.target.value)}
                required className="input" disabled={loadingContext} />
            </div>
            <div className="field sm:col-span-2">
              <label className="label">Estado de bienestar</label>
              <select
                value={wellbeingStatus}
                onChange={(e) => setWellbeingStatus(e.target.value)}
                required
                className="input"
              >
                <option value="" disabled>Selecciona una opcion</option>
                <option value="good">Bien</option>
                <option value="regular">Regular</option>
                <option value="difficult">Dificil</option>
              </select>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium text-slate-700">Procedimientos</h3>
            <button type="button" onClick={addProcedure} className="btn btn-secondary btn-sm">
              <Plus size={13} /> Agregar
            </button>
          </div>
          <div className="flex flex-col gap-3">
            {procedures.map((proc, i) => (
              <div key={i} className="border border-slate-200 rounded-lg p-4 bg-slate-50">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="field sm:col-span-2">
                    <label className="label">Nombre</label>
                    <select
                      value={proc.name}
                      onChange={(e) => updateProcedure(i, 'name', e.target.value)}
                      required
                      className="input bg-white"
                      disabled={allowedProcedures.length === 0}
                    >
                      <option value="" disabled>
                        {allowedProcedures.length === 0 ? 'Cargando catálogo...' : 'Selecciona un procedimiento'}
                      </option>
                      {allowedProcedures.map((name) => (
                        <option key={name} value={name}>{name}</option>
                      ))}
                    </select>
                  </div>
                  <div className="field">
                    <label className="label">Cantidad</label>
                    <input type="number" value={proc.quantity}
                      onChange={(e) => updateProcedure(i, 'quantity', parseInt(e.target.value, 10))}
                      required min={1} className="input bg-white" />
                  </div>
                  <div className="field sm:col-span-3">
                    <label className="label">
                      Descripcion {proc.name === 'Otro' ? '(obligatoria para "Otro")' : '(opcional)'}
                    </label>
                    <input type="text" value={proc.description}
                      onChange={(e) => updateProcedure(i, 'description', e.target.value)}
                      required={proc.name === 'Otro'}
                      className="input bg-white" />
                  </div>
                </div>
                {procedures.length > 1 && (
                  <button type="button" onClick={() => removeProcedure(i)}
                    className="btn btn-ghost btn-sm text-red-500 hover:bg-red-50 mt-2">
                    <Trash2 size={13} /> Eliminar
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>

        <AlertError>{error}</AlertError>

        <div className="flex gap-3">
          <button type="submit" disabled={saving || loadingContext} className="btn btn-primary">
            {saving ? 'Guardando...' : 'Guardar entrada'}
          </button>
          <button type="button" onClick={() => navigate('/student/logbook')} className="btn btn-secondary">
            Cancelar
          </button>
        </div>
      </form>
    </div>
  )
}
