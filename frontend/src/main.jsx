import { createRoot } from 'react-dom/client'
import { ReactKeycloakProvider } from '@react-keycloak/web'
import keycloak from './keycloak.js'
import './index.css'
import App from './App.jsx'

// Configuración de inicialización de Keycloak
// NO intentar autenticación automática - la app usa login por formulario
const keycloakProviderInitConfig = {
  onLoad: undefined,  // No cargar automáticamente
  pkceMethod: 'S256',  // PKCE para seguridad en clientes públicos
  checkLoginIframe: false, // Desactivar iframe
  flow: 'standard' // Authorization Code Flow con PKCE
}

// Event handlers para logging (útil para debugging)
const keycloakEventHandlers = {
  onReady: () => {
    console.log(`[Keycloak] Inicializado. Autenticado: ${Boolean(keycloak.authenticated)}`)
  },
  onAuthSuccess: () => {
    console.log('[Keycloak] Autenticación exitosa')
  },
  onAuthError: (error) => {
    console.error('[Keycloak] Error de autenticación:', error)
  },
  onAuthRefreshSuccess: () => {
    console.log('[Keycloak] Token refrescado exitosamente')
  },
  onAuthRefreshError: () => {
    console.warn('[Keycloak] Error refrescando token')
  },
  onTokenExpired: () => {
    console.log('[Keycloak] Token expirado, refrescando...')
    keycloak.updateToken(30).catch(() => {
      console.error('[Keycloak] Error al refrescar token expirado')
    })
  },
  onAuthLogout: () => {
    console.log('[Keycloak] Usuario deslogueado')
  }
}

createRoot(document.getElementById('root')).render(
  <ReactKeycloakProvider
    authClient={keycloak}
    initOptions={keycloakProviderInitConfig}
    onEvent={(event, error) => {
      const handler = keycloakEventHandlers[event]
      if (handler) handler(error)
    }}
    LoadingComponent={
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        fontFamily: 'Plus Jakarta Sans, sans-serif',
        color: '#1e4d8c'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: '48px',
            height: '48px',
            border: '4px solid #e0e7ff',
            borderTop: '4px solid #1e4d8c',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 16px'
          }}></div>
          <p>Inicializando autenticación...</p>
        </div>
      </div>
    }
  >
    <App />
  </ReactKeycloakProvider>
)

// Agregar keyframes para el spinner
const style = document.createElement('style')
style.textContent = `
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
`
document.head.appendChild(style)

