import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, LineChart, Line, CartesianGrid } from 'recharts'
import api from '../../services/api'
import Spinner from '../../components/ui/Spinner'
import { AlertError } from '../../components/ui/Alert'
import EmptyState from '../../components/ui/EmptyState'
import { Search, NotebookPen, Eye, TrendingUp, ChartColumnBig, ClipboardList } from 'lucide-react'

const STATUS_META = {
  draft:     { label: 'Borrador',  cls: 'badge-gray' },
  submitted: { label: 'Enviada',   cls: 'badge-blue' },
  reviewed:  { label: 'Revisada',  cls: 'badge-green' },
}

function buildIndividualStats(entries) {
  const totalEntries = entries.length
  const procedureTotals = new Map()
  const weekly = []
  let totalQuantity = 0

  const sortedEntries = [...entries].sort((a, b) => a.week_number - b.week_number)

  sortedEntries.forEach((entry) => {
    const procedures = entry.procedures || []
    const weekQty = procedures.reduce((sum, proc) => sum + (proc.quantity || 0), 0)
    totalQuantity += weekQty

    weekly.push({
      week: `S${entry.week_number}`,
      week_number: entry.week_number,
      quantity: weekQty,
      cumulative: totalQuantity,
    })

    procedures.forEach((proc) => {
      const current = procedureTotals.get(proc.name) || 0
      procedureTotals.set(proc.name, current + (proc.quantity || 0))
    })
  })

  const proceduresByType = Array.from(procedureTotals.entries())
    .map(([name, quantity]) => ({ name, quantity }))
    .sort((a, b) => b.quantity - a.quantity)

  const topProcedures = proceduresByType.slice(0, 8)
  const avgPerEntry = totalEntries > 0 ? (totalQuantity / totalEntries) : 0

  return {
    totalEntries,
    totalQuantity,
    uniqueTypes: proceduresByType.length,
    avgPerEntry,
    topProcedures,
    weekly,
  }
}

function StatsCard({ icon: Icon, label, value, hint, color }) {
  return (
    <div className="card" style={{ padding: '1rem 1.1rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.6rem' }}>
        <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--color-ink-500)' }}>{label}</p>
        <div style={{
          width: 28,
          height: 28,
          borderRadius: 8,
          display: 'grid',
          placeItems: 'center',
          background: color,
          color: 'white',
        }}>
          <Icon size={14} />
        </div>
      </div>
      <p style={{ margin: 0, fontSize: '1.35rem', color: 'var(--color-ink-900)', fontWeight: 600 }}>{value}</p>
      <p style={{ margin: '0.2rem 0 0', fontSize: '0.75rem', color: 'var(--color-ink-400)' }}>{hint}</p>
    </div>
  )
}

export default function LogbooksPage() {
  const navigate = useNavigate()
  const [students, setStudents] = useState([])
  const [studentQuery, setStudentQuery] = useState('')
  const [selectedName, setSelectedName] = useState('')
  const [loadingStudents, setLoadingStudents] = useState(false)
  const [showOptions, setShowOptions] = useState(false)
  const [studentId, setStudentId] = useState('')
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [searched, setSearched] = useState(false)
  const [statusFilter, setStatusFilter] = useState('all')
  const [procedureFilter, setProcedureFilter] = useState('all')
  const [periodFilter, setPeriodFilter] = useState('all')
  const [weekFrom, setWeekFrom] = useState('')
  const [weekTo, setWeekTo] = useState('')

  const availableProcedures = Array.from(
    new Set(
      entries.flatMap((entry) => (entry.procedures || []).map((proc) => proc.name)).filter(Boolean)
    )
  ).sort((a, b) => a.localeCompare(b))

  const matchesPeriod = (week) => {
    if (periodFilter === 'all') return true
    if (periodFilter === 'first') return week >= 1 && week <= 13
    if (periodFilter === 'second') return week >= 14 && week <= 26

    const from = Number(weekFrom)
    const to = Number(weekTo)
    if (!Number.isFinite(from) || !Number.isFinite(to) || from <= 0 || to <= 0) {
      return true
    }
    return week >= Math.min(from, to) && week <= Math.max(from, to)
  }

  const filteredEntries = entries.filter((entry) => {
    const matchesStatus = statusFilter === 'all' || entry.status === statusFilter
    const matchesProcedure = procedureFilter === 'all'
      || (entry.procedures || []).some((proc) => proc.name === procedureFilter)
    return matchesStatus && matchesProcedure && matchesPeriod(entry.week_number)
  })

  const stats = buildIndividualStats(filteredEntries)

  useEffect(() => {
    const timeout = setTimeout(() => {
      setLoadingStudents(true)
      api.get('/dashboard/students', {
        params: { q: studentQuery || undefined, limit: 20 },
      })
        .then(({ data }) => setStudents(data))
        .catch(() => setStudents([]))
        .finally(() => setLoadingStudents(false))
    }, 300)
    return () => clearTimeout(timeout)
  }, [studentQuery])

  const pickStudent = (student) => {
    setStudentId(student.id)
    setSelectedName(student.full_name)
    setStudentQuery(student.full_name)
    setShowOptions(false)
  }

  const handleSearch = (e) => {
    e.preventDefault()
    if (!studentId) return
    setLoading(true)
    setError(null)
    setSearched(true)
    api.get('/logbook/students/' + studentId + '/entries')
      .then(({ data }) => {
        setEntries(data)
        setStatusFilter('all')
        setProcedureFilter('all')
        setPeriodFilter('all')
        setWeekFrom('')
        setWeekTo('')
      })
      .catch(() => setError('Error al cargar las entradas'))
      .finally(() => setLoading(false))
  }

  return (
    <div className="page-enter">
      <div className="section-header">
        <div>
          <h2 className="section-title">Bitacoras</h2>
          <p className="section-subtitle">Consulta las entradas por estudiante</p>
        </div>
      </div>

      <div className="card" style={{ padding: '1.25rem 1.5rem', marginBottom: '1.5rem' }}>
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.75rem' }}>
          <div style={{ flex: 1, position: 'relative' }}>
            <input
              type="text"
              value={studentQuery}
              onChange={(e) => {
                const value = e.target.value
                setStudentQuery(value)
                setShowOptions(true)
                if (value !== selectedName) setStudentId('')
              }}
              onFocus={() => setShowOptions(true)}
              placeholder="Buscar estudiante por nombre o correo..."
              className="input"
            />
            {showOptions && (
              <div className="card" style={{
                position: 'absolute', top: 'calc(100% + 0.35rem)',
                left: 0, right: 0, zIndex: 30, maxHeight: '15rem', overflowY: 'auto',
              }}>
                {loadingStudents && (
                  <div style={{ padding: '0.625rem 0.75rem', fontSize: '0.8125rem', color: 'var(--color-ink-500)' }}>
                    Buscando estudiantes...
                  </div>
                )}
                {!loadingStudents && students.length === 0 && (
                  <div style={{ padding: '0.625rem 0.75rem', fontSize: '0.8125rem', color: 'var(--color-ink-500)' }}>
                    Sin resultados
                  </div>
                )}
                {!loadingStudents && students.map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={() => pickStudent(s)}
                    style={{
                      width: '100%', border: 'none', background: 'transparent',
                      textAlign: 'left', padding: '0.625rem 0.75rem', cursor: 'pointer',
                      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    }}
                  >
                    <span style={{ color: 'var(--color-ink-700)', fontSize: '0.875rem' }}>{s.full_name}</span>
                    <span style={{ color: 'var(--color-ink-400)', fontSize: '0.75rem' }}>{s.email}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
          <button type="submit" className="btn btn-primary" disabled={loading || !studentId}>
            <Search size={15} /> Buscar
          </button>
        </form>
        <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: 'var(--color-ink-500)' }}>
          {studentId
            ? 'Seleccionado: ' + selectedName
            : 'Selecciona un estudiante de la lista para consultar bitacoras.'}
        </div>
      </div>

      {loading && <Spinner />}
      <AlertError>{error}</AlertError>

      {!loading && searched && !error && (
        entries.length === 0 ? (
          <div className="card">
            <EmptyState
              icon={NotebookPen}
              title="Sin bitacoras"
              description={`No se encontraron entradas para ${selectedName || 'este estudiante'}.`}
            />
          </div>
        ) : (
          <>
            <div className="card" style={{ padding: '1rem 1.25rem', marginBottom: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.75rem', flexWrap: 'wrap' }}>
                <div>
                  <p style={{ margin: 0, fontSize: '0.76rem', color: 'var(--color-ink-400)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    Estadistica individual
                  </p>
                  <h3 style={{ margin: '0.25rem 0 0', fontSize: '1.05rem', color: 'var(--color-ink-900)' }}>
                    Resumen clinico de {selectedName}
                  </h3>
                </div>
                <span className="badge badge-blue">
                  {stats.totalEntries} semana{stats.totalEntries !== 1 ? 's' : ''} registrada{stats.totalEntries !== 1 ? 's' : ''}
                </span>
              </div>
            </div>

            <div className="card" style={{ padding: '1rem 1.25rem', marginBottom: '1rem' }}>
              <div style={{
                display: 'grid',
                gap: '0.75rem',
                gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))',
                alignItems: 'end',
              }}>
                <div className="field" style={{ marginBottom: 0 }}>
                  <label className="label">Periodo</label>
                  <select className="input" value={periodFilter} onChange={(e) => setPeriodFilter(e.target.value)}>
                    <option value="all">Todo el internado</option>
                    <option value="first">Primer periodo (sem. 1-13)</option>
                    <option value="second">Segundo periodo (sem. 14-26)</option>
                    <option value="custom">Rango de semanas</option>
                  </select>
                </div>

                {periodFilter === 'custom' && (
                  <>
                    <div className="field" style={{ marginBottom: 0 }}>
                      <label className="label">Semana desde</label>
                      <input
                        type="number"
                        min="1"
                        className="input"
                        value={weekFrom}
                        onChange={(e) => setWeekFrom(e.target.value)}
                        placeholder="Ej: 1"
                      />
                    </div>
                    <div className="field" style={{ marginBottom: 0 }}>
                      <label className="label">Semana hasta</label>
                      <input
                        type="number"
                        min="1"
                        className="input"
                        value={weekTo}
                        onChange={(e) => setWeekTo(e.target.value)}
                        placeholder="Ej: 8"
                      />
                    </div>
                  </>
                )}

                <div className="field" style={{ marginBottom: 0 }}>
                  <label className="label">Estado de bitácora</label>
                  <select className="input" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
                    <option value="all">Todos los estados</option>
                    <option value="draft">Borrador</option>
                    <option value="submitted">Enviada</option>
                    <option value="reviewed">Revisada</option>
                  </select>
                </div>

                <div className="field" style={{ marginBottom: 0 }}>
                  <label className="label">Tipo de procedimiento</label>
                  <select className="input" value={procedureFilter} onChange={(e) => setProcedureFilter(e.target.value)}>
                    <option value="all">Todos los procedimientos</option>
                    {availableProcedures.map((name) => (
                      <option key={name} value={name}>{name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div style={{ marginTop: '0.6rem', fontSize: '0.78rem', color: 'var(--color-ink-500)' }}>
                Mostrando {filteredEntries.length} de {entries.length} entrada{entries.length !== 1 ? 's' : ''}.
              </div>
            </div>

            {filteredEntries.length === 0 && (
              <div className="card" style={{ marginBottom: '1rem' }}>
                <EmptyState
                  icon={NotebookPen}
                  title="Sin resultados con estos filtros"
                  description="Ajusta el periodo, estado o procedimiento para ver estadísticas y entradas."
                />
              </div>
            )}

            {filteredEntries.length > 0 && (
              <>
                <div style={{
                  display: 'grid',
                  gap: '0.75rem',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))',
                  marginBottom: '1rem',
                }}>
                  <StatsCard
                    icon={ClipboardList}
                    label="Entradas en bitacora"
                    value={stats.totalEntries}
                    hint="Semanas registradas"
                    color="var(--color-uv-500)"
                  />
                  <StatsCard
                    icon={ChartColumnBig}
                    label="Procedimientos totales"
                    value={stats.totalQuantity}
                    hint="Suma de cantidades"
                    color="var(--color-ok-text)"
                  />
                  <StatsCard
                    icon={TrendingUp}
                    label="Promedio por semana"
                    value={stats.avgPerEntry.toFixed(1)}
                    hint="Cantidad promedio"
                    color="var(--color-warn-text)"
                  />
                  <StatsCard
                    icon={NotebookPen}
                    label="Tipos distintos"
                    value={stats.uniqueTypes}
                    hint="Variedad de casuistica"
                    color="var(--color-earth-500)"
                  />
                </div>

                <div style={{
                  display: 'grid',
                  gap: '1rem',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(290px, 1fr))',
                  marginBottom: '1rem',
                }}>
                  <div className="card" style={{ padding: '1rem 1.1rem' }}>
                    <h4 style={{ margin: '0 0 0.25rem', color: 'var(--color-ink-800)', fontSize: '0.95rem' }}>
                      Top procedimientos
                    </h4>
                    <p style={{ margin: '0 0 0.75rem', color: 'var(--color-ink-500)', fontSize: '0.78rem' }}>
                      Cantidad acumulada por tipo
                    </p>
                    <div style={{ width: '100%', height: 260 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={stats.topProcedures} layout="vertical" margin={{ top: 8, right: 20, left: 8, bottom: 8 }}>
                          <XAxis type="number" tick={{ fontSize: 11 }} />
                          <YAxis dataKey="name" type="category" width={140} tick={{ fontSize: 11 }} />
                          <Tooltip formatter={(value) => [`${value}`, 'Cantidad']} />
                          <Bar dataKey="quantity" fill="var(--color-uv-500)" radius={[0, 6, 6, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  <div className="card" style={{ padding: '1rem 1.1rem' }}>
                    <h4 style={{ margin: '0 0 0.25rem', color: 'var(--color-ink-800)', fontSize: '0.95rem' }}>
                      Evolucion semanal
                    </h4>
                    <p style={{ margin: '0 0 0.75rem', color: 'var(--color-ink-500)', fontSize: '0.78rem' }}>
                      Progresion acumulada de procedimientos
                    </p>
                    <div style={{ width: '100%', height: 260 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={stats.weekly} margin={{ top: 8, right: 20, left: 4, bottom: 8 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-ink-100)" />
                          <XAxis dataKey="week" tick={{ fontSize: 11 }} />
                          <YAxis tick={{ fontSize: 11 }} />
                          <Tooltip formatter={(value) => [`${value}`, 'Acumulado']} />
                          <Line
                            type="monotone"
                            dataKey="cumulative"
                            stroke="var(--color-ok-text)"
                            strokeWidth={2.5}
                            dot={{ r: 3, fill: 'var(--color-ok-text)' }}
                            activeDot={{ r: 5 }}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>

                <div className="card" style={{ overflow: 'hidden' }}>
                  <div style={{
                    padding: '0.875rem 1.5rem',
                    borderBottom: '1px solid var(--color-ink-100)',
                    display: 'flex', alignItems: 'center', gap: '0.5rem',
                  }}>
                    <NotebookPen size={14} style={{ color: 'var(--color-uv-500)' }} />
                    <span style={{ fontSize: '0.8125rem', color: 'var(--color-ink-500)' }}>
                      {filteredEntries.length} entrada{filteredEntries.length !== 1 ? 's' : ''} de {selectedName}
                    </span>
                  </div>
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Semana</th>
                        <th>Fecha inicio</th>
                        <th>Estado</th>
                        <th>Procedimientos</th>
                        <th>Acciones</th>
                      </tr>
                    </thead>
                    <tbody className="stagger">
                      {filteredEntries.map((entry) => {
                        const meta = STATUS_META[entry.status] || { label: entry.status, cls: 'badge-gray' }
                        return (
                          <tr key={entry.id}>
                            <td style={{ fontWeight: 600 }}>Semana {entry.week_number}</td>
                            <td style={{ color: 'var(--color-ink-500)' }}>{entry.week_start_date}</td>
                            <td><span className={'badge ' + meta.cls}>{meta.label}</span></td>
                            <td>
                              <span className="badge badge-blue">
                                {entry.procedures ? entry.procedures.length : 0} proc.
                              </span>
                            </td>
                            <td>
                              <button
                                onClick={() => navigate('/coordinator/logbooks/' + entry.id, {
                                  state: { studentName: selectedName },
                                })}
                                className="btn btn-secondary btn-sm"
                              >
                                <Eye size={13} /> Ver detalle
                              </button>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </>
        )
      )}
    </div>
  )
}
