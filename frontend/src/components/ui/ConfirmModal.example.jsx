import { useState } from 'react'
import ConfirmModal from './ConfirmModal'

/**
 * Ejemplos de uso del ConfirmModal
 */
export default function ConfirmModalExamples() {
  const [showDestructive, setShowDestructive] = useState(false)
  const [showNormal, setShowNormal] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleDestructiveConfirm = async () => {
    setLoading(true)
    // Simular operación async
    await new Promise((resolve) => setTimeout(resolve, 1500))
    setLoading(false)
    setShowDestructive(false)
    alert('Usuario eliminado')
  }

  const handleNormalConfirm = () => {
    setShowNormal(false)
    alert('Acción confirmada')
  }

  return (
    <div style={{ padding: '3rem', maxWidth: '800px', margin: '0 auto' }}>
      <h1 style={{ fontFamily: 'var(--font-display)', marginBottom: '2rem' }}>
        ConfirmModal Examples
      </h1>

      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
        <button onClick={() => setShowDestructive(true)} className="btn btn-danger">
          Acción destructiva (eliminar)
        </button>

        <button onClick={() => setShowNormal(true)} className="btn btn-primary">
          Acción normal (confirmar)
        </button>
      </div>

      {/* Modal destructivo */}
      <ConfirmModal
        isOpen={showDestructive}
        onClose={() => setShowDestructive(false)}
        onConfirm={handleDestructiveConfirm}
        title="¿Eliminar usuario?"
        message="Estás a punto de eliminar permanentemente a Juan Pérez. Esta acción no se puede deshacer."
        confirmLabel="Eliminar usuario"
        cancelLabel="Cancelar"
        isDestructive={true}
        loading={loading}
      />

      {/* Modal normal */}
      <ConfirmModal
        isOpen={showNormal}
        onClose={() => setShowNormal(false)}
        onConfirm={handleNormalConfirm}
        title="¿Confirmar acción?"
        message="¿Estás seguro de que deseas continuar con esta operación?"
        confirmLabel="Confirmar"
        cancelLabel="Cancelar"
        isDestructive={false}
      />

      <div style={{ marginTop: '3rem', padding: '1.5rem', background: 'var(--color-ink-50)', borderRadius: 'var(--radius-lg)' }}>
        <h3 style={{ fontFamily: 'var(--font-display)', marginBottom: '1rem' }}>Props</h3>
        <ul style={{ fontSize: '0.875rem', lineHeight: 1.8, color: 'var(--color-ink-700)' }}>
          <li><code>isOpen</code> - boolean: Controla visibilidad</li>
          <li><code>onClose</code> - function: Callback al cerrar</li>
          <li><code>onConfirm</code> - function: Callback al confirmar</li>
          <li><code>title</code> - string: Título del modal</li>
          <li><code>message</code> - string: Mensaje descriptivo</li>
          <li><code>confirmLabel</code> - string: Texto botón confirmar</li>
          <li><code>cancelLabel</code> - string: Texto botón cancelar</li>
          <li><code>isDestructive</code> - boolean: Estilo rojo para acciones destructivas</li>
          <li><code>loading</code> - boolean: Estado de carga</li>
        </ul>
      </div>
    </div>
  )
}
