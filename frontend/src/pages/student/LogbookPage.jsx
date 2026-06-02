import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../../services/api'
import Spinner from '../../components/ui/Spinner'
import Badge from '../../components/ui/Badge'
import { AlertError } from '../../components/ui/Alert'
import EmptyState from '../../components/ui/EmptyState'
import ConfirmModal from '../../components/ui/ConfirmModal'
import { BookOpen, Plus, Pencil, Eye, Trash2 } from 'lucide-react'

export default function LogbookPage() {
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [deleteModal, setDeleteModal] = useState({ open: false, entry: null })
  const [deleting, setDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/logbook/entries')
      .then(({ data }) => setEntries(data))
      .catch(() => setError('Error al cargar las entradas'))
      .finally(() => setLoading(false))
  }, [])

  const handleDeleteClick = (entry) => {
    setDeleteModal({ open: true, entry })
    setDeleteError(null)
  }

  const handleDeleteConfirm = async () => {
    if (!deleteModal.entry) return
    
    setDeleting(true)
    setDeleteError(null)
    
    try {
      await api.delete(`/logbook/entries/${deleteModal.entry.id}`)
      setEntries((prev) => prev.filter((e) => e.id !== deleteModal.entry.id))
      setDeleteModal({ open: false, entry: null })
    } catch (err) {
      setDeleteError(err.response?.data?.detail || 'Error al eliminar la entrada')
    } finally {
      setDeleting(false)
    }
  }

  const handleDeleteCancel = () => {
    if (!deleting) {
      setDeleteModal({ open: false, entry: null })
      setDeleteError(null)
    }
  }

  if (loading) return <Spinner />

  const submitted = entries.filter((e) => e.status !== 'draft').length

  return (
    <div className="page-enter">
      <div className="section-header">
        <div>
          <h2 className="section-title">Mi Bitácora</h2>
          <p className="section-subtitle">Registro semanal de procedimientos clínicos</p>
        </div>
        <button onClick={() => navigate('/student/logbook/new')} className="btn btn-primary">
          <Plus size={15} /> Nueva entrada
        </button>
      </div>

      <AlertError>{error}</AlertError>

      {entries.length === 0 ? (
        <div className="card">
          <EmptyState
            icon={BookOpen}
            title="Sin entradas"
            description="Aún no tienes entradas en tu bitácora. Crea la primera."
          />
        </div>
      ) : (
        <>
          {/* Progreso visual — elemento memorable */}
          {entries.length > 0 && (
            <div className="card" style={{ padding: '1.25rem 1.5rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--color-ink-700)' }}>Entradas enviadas</span>
                  <span style={{ fontSize: '0.875rem', color: 'var(--color-ink-500)' }}>{submitted} / {entries.length}</span>
                </div>
                <div className="progress-track">
                  <div className="progress-fill" style={{
                    width: `${entries.length ? (submitted / entries.length) * 100 : 0}%`,
                    background: 'var(--color-uv-500)',
                  }} />
                </div>
              </div>
              <div style={{ textAlign: 'right', flexShrink: 0 }}>
                <p style={{ fontFamily: 'var(--font-display)', fontSize: '1.75rem', fontWeight: 500, color: 'var(--color-uv-600)', margin: 0, lineHeight: 1 }}>
                  {entries.length}
                </p>
                <p style={{ fontSize: '0.75rem', color: 'var(--color-ink-500)', margin: 0 }}>semanas</p>
              </div>
            </div>
          )}

          <div className="card table-scroll">
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
                {entries.map((entry) => (
                  <tr key={entry.id}>
                    <td>
                      <span style={{ fontFamily: 'var(--font-display)', fontWeight: 500, fontSize: '1rem' }}>
                        Semana {entry.week_number}
                      </span>
                    </td>
                    <td style={{ color: 'var(--color-ink-500)' }}>{entry.week_start_date}</td>
                    <td><Badge status={entry.status} /></td>
                    <td>
                      <span className="badge badge-blue">{entry.procedures?.length ?? 0} proc.</span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button
                          onClick={() => navigate(`/student/logbook/${entry.id}`)}
                          className="btn btn-secondary btn-sm"
                        >
                          {entry.status === 'draft'
                            ? <><Pencil size={13} /> Editar</>
                            : <><Eye size={13} /> Ver</>}
                        </button>
                        {entry.status === 'draft' && (
                          <button
                            onClick={() => handleDeleteClick(entry)}
                            className="btn btn-ghost btn-sm"
                            style={{ color: 'var(--color-err-text)' }}
                            title="Eliminar entrada"
                          >
                            <Trash2 size={13} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      <ConfirmModal
        isOpen={deleteModal.open}
        onConfirm={handleDeleteConfirm}
        onCancel={handleDeleteCancel}
        title="¿Eliminar entrada de bitácora?"
        message={`Estás a punto de eliminar permanentemente la entrada de la Semana ${deleteModal.entry?.week_number}. Esta acción no se puede deshacer.`}
        confirmText="Eliminar entrada"
        variant="destructive"
        loading={deleting}
        error={deleteError}
      />
    </div>
  )
}
