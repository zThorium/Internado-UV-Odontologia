const variants = {
  draft:        'badge-gray',
  submitted:    'badge-blue',
  approved:     'badge-green',
  rejected:     'badge-red',
  pending:      'badge-yellow',
  under_review: 'badge-blue',
  resolved:     'badge-green',
  present:      'badge-green',
  absent:       'badge-red',
  justified:    'badge-yellow',
}

const labels = {
  draft:        'Borrador',
  submitted:    'Enviada',
  approved:     'Aprobada',
  rejected:     'Rechazada',
  pending:      'Pendiente',
  under_review: 'En revisión',
  resolved:     'Resuelto',
  present:      'Presente',
  absent:       'Ausente',
  justified:    'Justificado',
}

export default function Badge({ status, label, variant }) {
  const cls = variant || variants[status] || 'badge-gray'
  const text = label || labels[status] || status
  return <span className={`badge ${cls}`}>{text}</span>
}
