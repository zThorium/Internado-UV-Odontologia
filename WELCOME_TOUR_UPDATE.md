# Welcome Tour - Actualización Completa

## Resumen
Se ha actualizado el tour de bienvenida del coordinador para incluir todas las nuevas funcionalidades agregadas al sistema.

## Cambios Realizados

### AppShell (`frontend/src/components/AppShell.jsx`)
Actualizado el `TOUR_KEY_MAP` para incluir todas las rutas del coordinador:
- ✅ `/coordinator/overview` - Resumen general
- ✅ `/coordinator/alerts` - Sistema de alertas (NUEVO)
- ✅ `/coordinator/logbooks` - Bitácoras (NUEVO)
- ✅ `/coordinator/evaluations` - Evaluaciones (NUEVO)
- ✅ `/coordinator/attendance` - Asistencia (NUEVO)
- ✅ `/coordinator/incidents` - Incidentes confidenciales
- ✅ `/coordinator/wellbeing` - Bienestar (NUEVO)
- ✅ `/coordinator/assignments` - Asignaciones
- ✅ `/coordinator/users` - Gestión de usuarios (NUEVO)

### Tour Hook (`frontend/src/hooks/useTour.js`)
Actualizado el tour del coordinador con 11 pasos (antes 4):

#### Paso 0: Bienvenida
Modal centrado con introducción general al panel de coordinación.

#### Paso 1: Resumen general
Explica la vista principal con métricas clave del internado.

#### Paso 2: Alertas (NUEVO)
Presenta el sistema inteligente de detección de estudiantes en riesgo.

#### Paso 3: Bitácoras (NUEVO)
Muestra cómo revisar y filtrar entradas de bitácora de estudiantes.

#### Paso 4: Evaluaciones (NUEVO)
Explica el monitoreo de evaluaciones de tutores.

#### Paso 5: Asistencia (NUEVO)
Presenta el control completo de asistencia de estudiantes.

#### Paso 6: Incidentes confidenciales
Explica el sistema de reportes confidenciales y seguimiento.

#### Paso 7: Bienestar (NUEVO)
Muestra el monitoreo de estado emocional de estudiantes.

#### Paso 8: Asignaciones
Explica cómo asignar estudiantes a tutores y campos clínicos.

#### Paso 9: Gestión de usuarios (NUEVO)
Presenta la nueva página unificada de gestión de usuarios.

#### Paso 10: Perfil y opciones
Cierre del tour con información sobre cómo volver a verlo.

## Características del Tour

### Navegación
- Botones "Siguiente →" y "← Anterior"
- Botón "Comenzar" en el último paso
- Progreso visible: "X de Y"
- Permite cerrar en cualquier momento

### Diseño
- Overlay oscuro (55% opacidad)
- Popover con clase `uv-tour-popover` (estilos personalizados)
- Padding de 8px alrededor del elemento destacado
- Radio de 10px en el highlight
- Animaciones suaves
- Scroll automático a cada elemento

### Comportamiento
- Se activa automáticamente en el primer login
- Se puede reactivar desde el perfil ("Ver tour de bienvenida")
- Se marca como completado al finalizar o cerrar
- Delay de 400ms para asegurar que el DOM esté listo

## Tours por Rol

### Estudiante (5 pasos)
1. Bienvenida
2. Mi Bitácora
3. Asistencia
4. Reportes confidenciales
5. Perfil

### Tutor (3 pasos)
1. Bienvenida
2. Mis Estudiantes
3. Perfil

### Coordinador (11 pasos)
1. Bienvenida
2. Resumen general
3. Alertas
4. Bitácoras
5. Evaluaciones
6. Asistencia
7. Incidentes
8. Bienestar
9. Asignaciones
10. Usuarios
11. Perfil

## Integración con AuthContext

El tour se gestiona a través del contexto de autenticación:
- `showTour`: Boolean que indica si debe mostrarse
- `completeTour()`: Marca el tour como completado
- `triggerTour()`: Reactiva el tour manualmente

## Estilos Personalizados

Los estilos del tour están definidos en `frontend/src/index.css`:
- Fondo crema suave (`#fdfaf6`)
- Borde tierra cálido (`#d4a574`)
- Tipografía Fraunces para títulos
- Tipografía Plus Jakarta Sans para descripciones
- Botones con colores del design system

## Testing

Para probar el tour:
1. Crear un nuevo usuario coordinador
2. Hacer login por primera vez
3. El tour debe iniciarse automáticamente
4. Navegar por todos los pasos
5. Verificar que cada elemento se destaca correctamente
6. Confirmar que el tour se marca como completado

Para reactivar el tour:
1. Click en el perfil (parte inferior del sidebar)
2. Click en "Ver tour de bienvenida"
3. El tour debe reiniciarse desde el principio

## Notas Técnicas

- El tour usa la librería `driver.js`
- Los elementos deben tener el atributo `data-tour` correspondiente
- El tour espera 400ms antes de iniciarse para asegurar que el DOM esté listo
- Si un elemento no existe, el tour lo omite automáticamente
- El overlay bloquea la interacción con el resto de la página
