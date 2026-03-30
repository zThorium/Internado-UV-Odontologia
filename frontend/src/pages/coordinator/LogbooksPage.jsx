import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../../services/api'
import Spinner from '../../components/ui/Spinner'
import { AlertError } from '../../components/ui/Alert'
import EmptyState from '../../components/ui/EmptyState'
import { Search, NotebookPen, Eye } from 'lucide-react'

const STATUS_META = {
  draft:     { label: 'Borrador',  cls: 'badge-gray' },
  submitted: { label: 'Enviada',   cls: 'badge-blue' },
  reviewed:  { label: 'Revisada',  cls: 'badge-green' },
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
      .then(({ data }) => setEntries(data))
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
          <div className="card" style={{ overflow: 'hidden' }}>
            <div style={{
              padding: '0.875rem 1.5rem',
              borderBottom: '1px solid var(--color-ink-100)',
              display: 'flex', alignItems: 'center', gap: '0.5rem',
            }}>
              <NotebookPen size={14} style={{ color: 'var(--color-uv-500)' }} />
              <span style={{ fontSize: '0.8125rem', color: 'var(--color-ink-500)' }}>
                {entries.length} entrada{entries.length !== 1 ? 's' : ''} de {selectedName}
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
                {entries.map((entry) => {
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
        )
      )}
    </div>
  )
}
