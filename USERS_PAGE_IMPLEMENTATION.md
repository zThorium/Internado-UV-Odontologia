# Página de Usuarios - Implementación Completa

## Resumen
Se ha creado una página unificada de gestión de usuarios que reemplaza las vistas separadas de "Tutores" y "Crear Usuario", con un modal de confirmación moderno para eliminar usuarios.

## Cambios Realizados

### Frontend

1. **Nueva página**: `frontend/src/pages/coordinator/UsersPage.jsx`
   - Vista unificada para gestionar estudiantes y tutores
   - Filtros por rol (todos/estudiantes/tutores)
   - Crear nuevos usuarios (estudiantes o tutores)
   - Editar usuarios inline (nombre y estado activo)
   - Eliminar usuarios con modal de confirmación moderno
   - Interfaz moderna con iconos y badges de estado

2. **Nuevo componente**: `frontend/src/components/ui/ConfirmModal.jsx`
   - Modal de confirmación reutilizable
   - Diseño integrado con el design system
   - Full-page overlay (100vw × 100vh) con backdrop oscurecido
   - Blur de 4px aplicado al contenido detrás del modal
   - Modal content permanece nítido (sin blur)
   - Renderizado con React Portal en document.body
   - Animaciones suaves (fade in + slide up)
   - Soporte para acciones destructivas (rojo) y normales (azul)
   - Estado de carga en botones
   - Cierre con Escape o click fuera
   - Icono de advertencia contextual
   - Totalmente responsive

3. **Rutas actualizadas**: `frontend/src/App.jsx`
   - Agregada ruta `/coordinator/users` → `UsersPage`

4. **Navegación actualizada**: `frontend/src/pages/CoordinatorDashboard.jsx`
   - Reemplazado "Tutores" y "Crear Usuario" por "Usuarios"
   - Ruta: `/coordinator/users`

### Backend

5. **Nuevos endpoints**: `backend/app/routers/dashboard.py`
   - `PATCH /dashboard/students/{student_id}` - Actualizar estudiante
   - `DELETE /dashboard/students/{student_id}` - Eliminar estudiante y datos relacionados
   - `DELETE /dashboard/tutors/{tutor_id}` - Eliminar tutor (desactiva asignaciones)
   - Permite modificar `full_name` y `is_active`
   - Simétrico al endpoint existente para tutores

## Comportamiento de Eliminación

### Flujo de Eliminación Completo
Cuando un coordinador elimina un usuario, el sistema ejecuta los siguientes pasos en orden:

1. **Eliminación en Keycloak** (primero)
   - Se elimina el usuario del sistema de autenticación
   - Si falla, se detiene el proceso y se muestra error en el modal
   
2. **Eliminación de datos relacionados** (solo si paso 1 fue exitoso)
   - Se eliminan todos los registros asociados en la base de datos
   
3. **Eliminación del usuario local** (solo si pasos anteriores fueron exitosos)
   - Se elimina el registro del usuario de la base de datos local
   
4. **Actualización de UI** (solo si todo fue exitoso)
   - El modal se cierra
   - La lista de usuarios se recarga
   - El usuario desaparece de la interfaz

### Manejo de Errores
- Si cualquier paso falla, el proceso se detiene
- El error se muestra dentro del modal (no se cierra)
- El usuario permanece en la lista hasta que la eliminación sea exitosa
- El coordinador puede reintentar o cancelar

### Estudiantes
Al eliminar un estudiante exitosamente, se eliminan en cascada:
- Usuario en Keycloak
- Alertas del estudiante
- Entradas de bienestar
- Incidentes
- Registros de asistencia
- Entradas de bitácora
- Asignaciones

### Tutores
Al eliminar un tutor exitosamente:
- Usuario en Keycloak
- Las asignaciones se desactivan (no se eliminan)
- Esto preserva el historial de asignaciones

## Modal de Confirmación

### Características
- Backdrop oscurecido con blur sutil
- Animación de entrada suave (fade + slide up)
- Icono de advertencia en círculo coloreado
- Tipografía del design system (Fraunces + Plus Jakarta Sans)
- Botones alineados a la derecha
- Botón ghost para cancelar
- Botón destructivo rojo para eliminar
- Estado de carga durante la operación
- Cierre con Escape, X, o click fuera del modal
- Bloqueo de scroll del body cuando está abierto

### Props del ConfirmModal
```jsx
<ConfirmModal
  isOpen={boolean}           // Controla visibilidad
  onClose={function}         // Callback al cerrar
  onConfirm={function}       // Callback al confirmar
  title={string}             // Título del modal
  message={string}           // Mensaje descriptivo
  confirmLabel={string}      // Texto botón confirmar
  cancelLabel={string}       // Texto botón cancelar
  isDestructive={boolean}    // true = rojo, false = azul
  loading={boolean}          // Estado de carga
  error={string}             // Mensaje de error (opcional)
/>
```

### Ejemplo de Uso con Manejo de Errores
```jsx
const [showModal, setShowModal] = useState(false)
const [loading, setLoading] = useState(false)
const [error, setError] = useState(null)

<ConfirmModal
  isOpen={showModal}
  onClose={() => {
    setShowModal(false)
    setError(null)
  }}
  onConfirm={async () => {
    setLoading(true)
    setError(null)
    try {
      await deleteUser()
      setShowModal(false) // Solo cerrar si fue exitoso
    } catch (err) {
      setError(err.message) // Mostrar error en el modal
    } finally {
      setLoading(false)
    }
  }}
  title="¿Eliminar a Juan Pérez?"
  message="Esta acción eliminará permanentemente al usuario de todos los sistemas."
  confirmLabel="Eliminar usuario"
  cancelLabel="Cancelar"
  isDestructive={true}
  loading={loading}
  error={error}
/>
```

## Funcionalidades

- ✅ Listar todos los usuarios (estudiantes y tutores)
- ✅ Filtrar por rol
- ✅ Crear nuevos usuarios con rol, email, nombre y contraseña
- ✅ Editar nombre completo de usuarios
- ✅ Activar/desactivar usuarios
- ✅ Eliminar usuarios con confirmación modal
- ✅ Eliminación sincronizada en BD local y Keycloak
- ✅ Manejo de errores en el modal (no cierra hasta éxito)
- ✅ Contador de usuarios activos
- ✅ Iconos diferenciados por rol
- ✅ Badges de estado (activo/inactivo)

## Endpoints Utilizados

- `GET /dashboard/students` - Listar estudiantes
- `GET /dashboard/tutors` - Listar tutores
- `POST /auth/create-user` - Crear usuario
- `PATCH /dashboard/tutors/{id}` - Actualizar tutor
- `PATCH /dashboard/students/{id}` - Actualizar estudiante
- `DELETE /dashboard/tutors/{id}` - Eliminar tutor (BD + Keycloak)
- `DELETE /dashboard/students/{id}` - Eliminar estudiante (BD + Keycloak)

## Próximos Pasos

El usuario debe:
1. Iniciar el backend y frontend
2. Navegar a `/coordinator/users`
3. Probar las funcionalidades de crear, editar y filtrar usuarios
