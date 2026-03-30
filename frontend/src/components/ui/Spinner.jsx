export default function Spinner({ className = '' }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '3rem 0' }} className={className}>
      <div className="spinner" style={{ color: 'var(--color-uv-500)' }} />
    </div>
  )
}
