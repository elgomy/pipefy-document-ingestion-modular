# Manejo de Cold Starts en Render

## Problema Identificado

Los servicios en Render (plan gratuito) se "duermen" después de 15 minutos de inactividad, causando:

- **Cold starts** que pueden tardar 30-60 segundos
- **Errores 502 Bad Gateway** durante el despertar
- **Timeouts** en llamadas HTTP entre servicios
- **Fallos en webhooks** de Pipefy

## Soluciones Implementadas

### 1. **Timeout Extendido**
- **Antes**: 10 minutos (600s)
- **Ahora**: 15 minutos (900s)
- **Razón**: Permite manejar cold starts + análisis completo

### 2. **Retry Automático para 502**
```python
elif response.status_code == 502:
    logger.error(f"🛌 Servicio CrewAI está dormido (502 Bad Gateway) - Reintentando en 30 segundos...")
    await asyncio.sleep(30)
    # Reintenta la llamada automáticamente
```

### 3. **Health Check Mejorado**
- Verifica estado del servicio CrewAI
- Mide tiempo de respuesta
- Detecta cold starts automáticamente

### 4. **Endpoint de Utilidad**
- `/utils/wake-crewai`: Despierta el servicio CrewAI manualmente
- Útil antes de procesar webhooks importantes

### 5. **Script de Monitoreo**
- `wake_services.py`: Script para despertar ambos servicios
- Monitoreo automático de estado

## Nuevo: Manejo Automático de Fases en Pipefy

### Problema de Fases Identificado

El campo "Informe CrewAI" solo existe en la **fase de destino** (ID: 1131156124) pero no en la **fase de origen** (ID: 1130856059), causando:

- **Errores al actualizar campo**: Campo no encontrado en fase origen
- **Webhooks fallidos**: No se puede actualizar el informe
- **Flujo interrumpido**: El proceso se detiene sin completar la actualización

### Solución Implementada: Movimiento Automático de Cards

#### 1. **Detección Automática de Fase**
```python
async def get_card_current_phase_and_move_if_needed(card_id: str) -> Dict[str, Any]:
    # Detecta la fase actual del card
    # Mueve automáticamente a la fase de destino si es necesario
    # Retorna información completa del proceso
```

#### 2. **Movimiento Inteligente**
- **Fase Origen (1130856059)** → **Fase Destino (1131156124)** automáticamente
- **Ya en destino**: No hace nada, procede directamente
- **Otra fase**: Registra pero no mueve automáticamente

#### 3. **Actualización Robusta**
```python
async def update_pipefy_informe_crewai_field(card_id: str, informe_content: str) -> bool:
    # PASO 1: Verificar fase y mover si es necesario
    # PASO 2: Buscar campo "Informe CrewAI"
    # PASO 3: Actualizar campo con el informe
```

#### 4. **Endpoints de Prueba**
- `/test/check-and-move-card`: Verifica fase y movimiento
- `/test/update-pipefy-with-phase-handling`: Prueba completa con manejo de fases

### Beneficios del Manejo de Fases

1. **Automatización Completa**: No requiere intervención manual
2. **Robustez**: Maneja cualquier fase de origen automáticamente
3. **Logs Detallados**: Seguimiento completo del proceso
4. **Modularidad**: Mantiene separación de responsabilidades
5. **Escalabilidad**: Fácil agregar nuevas fases en el futuro

## 🔧 Creación Automática de Campos en Pipefy

### Problema Resuelto
El campo "Informe CrewAI" puede no existir en todas las fases del proceso de Pipefy. Para evitar errores al intentar actualizar campos inexistentes, el sistema ahora crea automáticamente el campo si no existe.

### Funcionalidad Implementada

#### 1. Verificación y Creación Automática
```python
def create_informe_crewai_field_if_not_exists(phase_id):
    # Verifica si el campo existe
    # Si no existe, lo crea automáticamente
    # Retorna el field_id para uso posterior
```

#### 2. Actualización con Auto-Creación
```python
def update_pipefy_informe_crewai_field_with_auto_creation(card_id, informe_content):
    # PASO 1: Verificar/mover fase si es necesario
    # PASO 2: Crear campo si no existe
    # PASO 3: Actualizar campo con contenido
```

### Características del Campo Creado

- **Nombre**: "Informe CrewAI"
- **Tipo**: `long_text` (texto largo)
- **Descripción**: "Informe generado automáticamente por CrewAI con análisis de documentos"
- **Requerido**: No
- **Editable**: Sí

### Flujo de Trabajo Actualizado

```
📄 Webhook Pipefy → Módulo Ingestión
                        ↓
🤖 CrewAI ← Llamada HTTP ← Módulo Ingestión
    ↓
💾 CrewAI guarda en informe_cadastro
    ↓
🔔 Supabase detecta INSERT → Webhook automático
    ↓
📍 Módulo Ingestión verifica fase del card
    ↓
🚀 Si está en fase origen → Mueve a fase destino
    ↓
🔧 Verifica si campo "Informe CrewAI" existe
    ↓
🆕 Si no existe → Crea campo automáticamente
    ↓
📝 Actualiza campo con informe generado
```

### Endpoints de Prueba

#### Prueba de Creación Automática
```bash
curl -X POST https://tu-servicio.onrender.com/test/create-field-auto \
  -H "Content-Type: application/json" \
  -d '{
    "card_id": "123456789",
    "test_content": "Contenido de prueba para verificar creación automática"
  }'
```

### Logs de Ejemplo

```
🔧 Verificando si campo 'Informe CrewAI' existe en fase 1130856059
🚀 Creando campo 'Informe CrewAI' en fase 1130856059
✅ Campo 'Informe CrewAI' creado exitosamente!
   - ID: 987654321
   - Label: Informe CrewAI
   - Type: long_text
🆕 Campo 'Informe CrewAI' fue creado automáticamente en fase 1130856059
📝 Actualizando campo 987654321 con informe...
✅ Campo 'Informe CrewAI' actualizado exitosamente!
```

### Ventajas de Esta Solución

1. **Automatización Completa**: No requiere intervención manual
2. **Escalabilidad**: Funciona en cualquier fase del proceso
3. **Robustez**: Maneja automáticamente campos faltantes
4. **Modularidad**: Mantiene la separación de responsabilidades
5. **Flexibilidad**: Se adapta a cambios en el proceso de Pipefy
6. **Trazabilidad**: Logs detallados de todas las operaciones

### Troubleshooting

#### Error: "Field type not found"
```bash
# Verificar tipos de campo disponibles en Pipefy
curl -X POST https://api.pipefy.com/graphql \
  -H "Authorization: Bearer $PIPEFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "query { fieldTypes { id name } }"}'
```

#### Error: "Permission denied to create field"
- Verificar que el token de Pipefy tenga permisos de administración
- Confirmar que el usuario tiene permisos para modificar la fase

#### Campo creado pero no visible
- El campo se crea como no requerido y editable
- Verificar la configuración de la fase en Pipefy
- Puede requerir actualización de la interfaz de usuario

## Comandos Útiles

### Despertar Servicios
```bash
# Despertar ambos servicios automáticamente
python3 wake_services.py

# Despertar solo CrewAI desde el servicio de ingestión
curl -X POST https://pipefy-document-ingestion-modular.onrender.com/utils/wake-crewai
```

### Verificar Estado
```bash
# Health check del servicio de ingestión
curl https://pipefy-document-ingestion-modular.onrender.com/health | python3 -m json.tool

# Health check del servicio CrewAI
curl https://pipefy-crewai-analysis-modular.onrender.com/health | python3 -m json.tool
```

### Probar Manejo de Fases
```bash
# Verificar fase actual y mover si es necesario
curl -X POST "https://pipefy-document-ingestion-modular.onrender.com/test/check-and-move-card?card_id=YOUR_CARD_ID"

# Prueba completa con manejo de fases
curl -X POST "https://pipefy-document-ingestion-modular.onrender.com/test/update-pipefy-with-phase-handling?case_id=YOUR_CARD_ID&informe_content=Test%20informe"
```

## Troubleshooting

### Error 502 Bad Gateway
1. **Causa**: Servicio dormido (cold start)
2. **Solución Automática**: Retry después de 30 segundos
3. **Solución Manual**: Usar `wake_services.py`

### Campo "Informe CrewAI" No Encontrado
1. **Causa**: Card en fase incorrecta
2. **Solución Automática**: Movimiento automático a fase destino
3. **Verificación**: Usar endpoint `/test/check-and-move-card`

### Timeout en Análisis CrewAI
1. **Causa**: Análisis muy largo + cold start
2. **Solución**: Timeout extendido a 15 minutos
3. **Prevención**: Despertar servicio antes de webhooks importantes

### Logs para Debugging
```bash
# Ver logs en tiempo real (si tienes acceso a Render)
# O usar los endpoints de health check para verificar estado

# Verificar último informe guardado
curl https://pipefy-crewai-analysis-modular.onrender.com/informes

# Verificar informe específico
curl https://pipefy-crewai-analysis-modular.onrender.com/informe/YOUR_CASE_ID
```

## Arquitectura Final Optimizada

```
📄 Webhook Pipefy (Fase Origen) → Módulo Ingestión
                                      ↓
🤖 CrewAI ← Llamada HTTP ← Módulo Ingestión
    ↓
💾 CrewAI guarda en informe_cadastro
    ↓
🔔 Supabase detecta INSERT → Webhook automático
    ↓
📍 Módulo Ingestión verifica fase del card
    ↓
🚀 Si está en fase origen → Mueve a fase destino automáticamente
    ↓
📝 Actualiza campo "Informe CrewAI" en Pipefy
```

**Resultado**: Sistema completamente automatizado que maneja cold starts, fases de Pipefy y actualizaciones de campos sin intervención manual.

## Uso Práctico

### Antes de Pruebas Importantes
1. Ejecutar script de despertar:
   ```bash
   python3 wake_services.py
   ```

2. O despertar manualmente:
   ```bash
   curl https://pipefy-document-ingestion-modular.onrender.com/health
   curl https://pipefy-crewai-analysis-modular.onrender.com/health
   ```

### Monitoreo de Estado
```bash
# Health check mejorado con estado de CrewAI
curl https://pipefy-document-ingestion-modular.onrender.com/health | jq
```

Respuesta incluye:
```json
{
  "crewai_status": "healthy",
  "crewai_response_time_seconds": 0.85,
  "cold_start_handling": "enabled"
}
```

## Próximos Pasos

Para eliminar completamente los cold starts:
1. **Upgrade a plan pago** en Render
2. **Implementar keep-alive** con cron jobs
3. **Migrar a servicios serverless** (Vercel, Netlify)
4. **Usar contenedores** siempre activos

## Comandos Útiles

```bash
# Despertar servicios
python3 wake_services.py

# Verificar estado
curl https://pipefy-document-ingestion-modular.onrender.com/health | jq

# Despertar solo CrewAI
curl -X POST https://pipefy-document-ingestion-modular.onrender.com/utils/wake-crewai

# Probar webhook manualmente
curl -X POST https://pipefy-document-ingestion-modular.onrender.com/test/update-pipefy-observacoes \
  -H "Content-Type: application/json" \
  -d '{"case_id": "test123", "informe_content": "Test informe"}'
``` 