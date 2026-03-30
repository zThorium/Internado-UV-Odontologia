import { AlertTriangle, X } from 'lucide-react'
import { useEffect } from 'react'
import { createPortal } from 'react-dom'

/**
 * ConfirmModal - Modal de confirmación moderno integrado con el design system
 * 
 * @param {boolean} isOpen - Controla la visibilidad del modal
 * @param {function} onClose - Callback cuando se cierra el modal
 * @param {function} onConfirm - Callback cuando se confirma la acción
 * @param {string} title - Título del modal
 * @param {string} message - Mensaje descriptivo
 * @param {string} confirmLabel - Texto del botón de confirmación (default: "Confirmar")
 * @param {string} cancelLabel - Texto del botón de cancelar (default: "Cancelar")
 * @param {boolean} isDestructive - Si true, usa estilo rojo para acción destructiva
 * @param {boolean} loading - Si true, muestra estado de carga en el botón
 * @param {string} error - Mensaje de error a mostrar (opcional)
 */
export default function ConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  title = 'Confirmar acción',
  message,
  confirmLabel = 'Confirmar',
  cancelLabel = 'Cancelar',
  isDestructive = false,
  loading = false,
  error = null,
}) {
  // Bloquear scroll del body cuando el modal está abierto
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => {
      document.body.style.overflow = ''
    }
  }, [isOpen])

  // Cerrar con tecla Escape
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }
    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [isOpen, onClose])

  if (!isOpen) return null

  const modalContent = (
    <div
      className="modal-backdrop"
      onClick={onClose}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        width: '100vw',
        height: '100vh',
        background: 'rgba(15, 31, 46, 0.6)',
        backdropFilter: 'blur(4px)',
        WebkitBackdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        padding: '1rem',
        animation: 'fadeIn 150ms cubic-bezier(0.16, 1, 0.3, 1)',
        overflow: 'auto',
      }}
    >
      <div
        className="modal-content"
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'var(--color-bg-surface)',
          borderRadius: 'var(--radius-xl)',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.25), 0 4px 12px rgba(0, 0, 0, 0.15)',
          maxWidth: '420px',
          width: '100%',
          position: 'relative',
          animation: 'modalSlideUp 200ms cubic-bezier(0.16, 1, 0.3, 1)',
          margin: 'auto',
          filter: 'none',
          backdropFilter: 'none',
          WebkitBackdropFilter: 'none',
          isolation: 'isolate',
          willChange: 'transform',
        }}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="btn-ghost"
          style={{
            position: 'absolute',
            top: '1rem',
            right: '1rem',
            padding: '0.375rem',
            borderRadius: 'var(--radius-md)',
            color: 'var(--color-ink-300)',
            transition: 'color var(--duration-fast) var(--ease-out)',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--color-ink-500)')}
          onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--color-ink-300)')}
        >
          <X size={18} />
        </button>

        {/* Content */}
        <div style={{ padding: '2rem 2rem 1.5rem' }}>
          {/* Icon */}
          <div
            style={{
              width: '48px',
              height: '48px',
              borderRadius: '50%',
              background: isDestructive ? 'var(--color-err-bg)' : 'var(--color-warn-bg)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '1.25rem',
            }}
          >
            <AlertTriangle
              size={24}
              style={{
                color: isDestructive ? 'var(--color-err-text)' : 'var(--color-warn-text)',
              }}
            />
          </div>

          {/* Title */}
          <h3
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: '1.375rem',
              fontWeight: 500,
              color: 'var(--color-ink-900)',
              letterSpacing: '-0.02em',
              lineHeight: 1.2,
              margin: '0 0 0.75rem 0',
            }}
          >
            {title}
          </h3>

          {/* Message */}
          <p
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: '0.9375rem',
              color: 'var(--color-ink-500)',
              lineHeight: 1.6,
              margin: 0,
            }}
          >
            {message}
          </p>

          {/* Error message */}
          {error && (
            <div
              style={{
                marginTop: '1rem',
                padding: '0.75rem 1rem',
                borderRadius: 'var(--radius-md)',
                background: 'var(--color-err-bg)',
                border: '1px solid var(--color-err-text)',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '0.5rem',
              }}
            >
              <AlertTriangle size={16} style={{ color: 'var(--color-err-text)', flexShrink: 0, marginTop: '0.125rem' }} />
              <span
                style={{
                  fontFamily: 'var(--font-body)',
                  fontSize: '0.875rem',
                  color: 'var(--color-err-text)',
                  lineHeight: 1.5,
                }}
              >
                {error}
              </span>
            </div>
          )}
        </div>

        {/* Actions */}
        <div
          style={{
            padding: '1rem 2rem 2rem',
            display: 'flex',
            gap: '0.75rem',
            justifyContent: 'flex-end',
          }}
        >
          <button onClick={onClose} disabled={loading} className="btn btn-ghost">
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            disabled={loading}
            className="btn"
            style={{
              background: isDestructive ? '#dc2626' : 'var(--color-uv-600)',
              color: '#fff',
              boxShadow: isDestructive
                ? '0 1px 3px rgba(220, 38, 38, 0.3)'
                : '0 1px 3px rgba(30, 77, 140, 0.25)',
            }}
            onMouseEnter={(e) => {
              if (!loading) {
                e.currentTarget.style.background = isDestructive ? '#b91c1c' : 'var(--color-uv-700)'
                e.currentTarget.style.boxShadow = isDestructive
                  ? '0 2px 8px rgba(220, 38, 38, 0.35)'
                  : '0 2px 8px rgba(30, 77, 140, 0.30)'
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = isDestructive ? '#dc2626' : 'var(--color-uv-600)'
              e.currentTarget.style.boxShadow = isDestructive
                ? '0 1px 3px rgba(220, 38, 38, 0.3)'
                : '0 1px 3px rgba(30, 77, 140, 0.25)'
            }}
          >
            {loading ? 'Procesando...' : confirmLabel}
          </button>
        </div>
      </div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        
        @keyframes modalSlideUp {
          from {
            opacity: 0;
            transform: translateY(16px) scale(0.96);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }
      `}</style>
    </div>
  )

  // Render modal using portal to ensure it's at the root level
  return createPortal(modalContent, document.body)
}
