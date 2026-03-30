import Keycloak from 'keycloak-js'

// Singleton de Keycloak para evitar múltiples instancias en desarrollo.
const keycloak = new Keycloak({
  url: import.meta.env.VITE_KEYCLOAK_URL || 'http://localhost:8080',
  realm: import.meta.env.VITE_KEYCLOAK_REALM || 'internado-uv',
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'internado-frontend'
})

export default keycloak
