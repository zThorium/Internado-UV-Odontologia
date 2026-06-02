import { useEffect, useState } from 'react'
import { useParams, useSearchParams, useNavigate } from 'react-router-dom'
import api from '../../services/api'
import Spinner from '../../components/ui/Spinner'
import { AlertError } from '../../components/ui/Alert'
import EmptyState from '../../components/ui/EmptyState'
import { CalendarCheck, ArrowLeft } from 'lucide-react'

const STATUS_LABELS = { present: 'Presente', absent: 'Ausente', justified: 'Justificado' }
const STATUS_CLS    = { present: 'badge-green', absent: 'badge-red', justified: 'badge-yellow' }

export default function TutorAttendancePage() {
  const { student_id } = useParams()
  const [searchParams] = useSearchParams()
  const studentName = searchParams.get('name') || 'Estudiante'
  const navigate = useNavigate()
  const [records, setRecords] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const periodLabel = {
    semester_1: 'Semestre 1',
    semester_2: 'Semestre 2',
  }

  useEffect(() => {
    Promise.all([
      api.get(`/attendance/students/${student_id}`),
      api.get(`/attendance/students/${student_id}/stats`),
    ])
      .then(([recRes, statsRes]) => {
        setRecords(recRes.data)
        setStats(statsRes.data)
      })
      .catch(() => setError('Error al cargar la asistencia'))
      .finally(() => setLoading(false))
  }, [student_id])

  const rateColor = stats
    ? stats.attendance_rate >= 75 ? 'var(--color-ok-text)'
    : stats.attendance_rate >= 50 ? 'var(--color-warn-text)'
    : 'var(--color-err-text)'
    : 'var(--color-ink-500)'

  return (
    <div className="page-enter">
      <button onClick={() => navigate('/tutor')} className="btn btn-ghost btn-sm"
        style={{ marginBottom: '1rem', marginLeft: '-0.5rem' }}>
        <ArrowLeft size={15} /> Volver
      </button>

      <div className="section-header">
        <div>
          <h2 className="section-title">Asistencia</h2>
          <p className="section-subtitle">{studentName} · Solo lectura</p>
        </div>
      </div>

      {loading && <Spinner />}
      <AlertError>{error}</AlertError>

      {!loading && !error && stats && (
        <>
          {/* Stats */}
          <div className="stagger" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
            {[
              { label: 'Total días',   value: stats.total,           color: 'var(--color-ink-700)' },
              { label: 'Presentes',    value: stats.present,         color: 'var(--color-ok-text)' },
              { label: 'Ausentes',     value: stats.absent,          color: 'var(--color-err-text)' },
              { label: 'Justificados', value: stats.justified,       color: 'var(--color-warn-text)' },
              { label: 'Tasa',         value: `${stats.attendance_rate}%`, color: rateColor },
            ].map(({ label, value, color }) => (
              <div key={label} className="card-stat" style={{ textAlign: 'center', padding: '1rem' }}>
                <p style={{ fontSize: '0.75rem', color: 'var(--color-ink-500)', margin: '0 0 0.25rem' }}>{label}</p>
                <p style={{ fontFamily: 'var(--font-display)', fontSize: '1.75rem', fontWeight: 500, color, margin: 0, lineHeight: 1.1 }}>{value}</p>
              </div>
            ))}
          </div>

          {/* Progress bar */}
          <div className="card" style={{ padding: '1rem 1.5rem', marginBottom: '1.5rem' }}>
            <div className="progress-track">
              <div className="progress-fill" style={{
                width: `${stats.attendance_rate}%`,
                background: stats.attendance_rate >= 75 ? '#16a34a' : stats.attendance_rate >= 50 ? '#d97706' : '#dc2626',
              }} />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
            <div className="card table-scroll">
              <div style={{ padding: '0.9rem 1rem', borderBottom: '1px solid var(--color-ink-100)' }}>
                <p style={{ margin: 0, fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-ink-700)' }}>
                  Asistencia por periodo
                </p>
              </div>
              <table className="table">
                <thead>
                  <tr>
                    <th>Periodo</th>
                    <th>Presente</th>
                    <th>Ausente</th>
                    <th>Justificado</th>
                  </tr>
                </thead>
                <tbody>
                  {(stats.by_period || []).map((period) => (
                    <tr key={period.period}>
                      <td>{periodLabel[period.period] || period.period}</td>
                      <td>{period.present}</td>
                      <td>{period.absent}</td>
                      <td>{period.justified}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="card table-scroll">
              <div style={{ padding: '0.9rem 1rem', borderBottom: '1px solid var(--color-ink-100)' }}>
                <p style={{ margin: 0, fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-ink-700)' }}>
                  Registros por semana
                </p>
              </div>
              <table className="table">
                <thead>
                  <tr>
                    <th>Semana</th>
                    <th>Periodo</th>
                    <th>P/A/J</th>
                  </tr>
                </thead>
                <tbody>
                  {(stats.by_week || []).slice(-8).map((week) => (
                    <tr key={week.week_label}>
                      <td>{week.week_label}</td>
                      <td>{periodLabel[week.period] || week.period}</td>
                      <td>{week.present}/{week.absent}/{week.justified}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {records.length === 0 ? (
            <div className="card">
              <EmptyState icon={CalendarCheck} title="Sin registros" description="Este estudiante no tiene registros de asistencia." />
            </div>
          ) : (
            <div className="card table-scroll">
              <table className="table">
                <thead>
                  <tr>
                    <th>Fecha</th>
                    <th>Estado</th>
                    <th>Observación</th>
                  </tr>
                </thead>
                <tbody>
                  {records.map((rec) => (
                    <tr key={rec.id}>
                      <td style={{ fontWeight: 500 }}>{rec.date}</td>
                      <td>
                        <span className={`badge ${STATUS_CLS[rec.status] || 'badge-gray'}`}>
                          {STATUS_LABELS[rec.status] || rec.status}
                        </span>
                      </td>
                      <td style={{ color: 'var(--color-ink-500)' }}>
                        {rec.observation || <span style={{ color: 'var(--color-ink-300)' }}>—</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  )
}
