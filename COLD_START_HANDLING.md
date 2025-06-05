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

### 3. **Health Check Previo**
```python
# Verificar que el servicio esté despierto antes de llamadas importantes
async with httpx.AsyncClient(timeout=30.0) as health_client:
    health_response = await health_client.get(f"{CREWAI_SERVICE_URL}/health")
```

### 4. **Endpoint de Utilidad**
```bash
# Despertar manualmente el servicio CrewAI
curl -X POST https://pipefy-document-ingestion-modular.onrender.com/utils/wake-crewai
```

### 5. **Script de Utilidad**
```bash
# Despertar ambos servicios y verificar estado
python3 wake_services.py
```

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

## Troubleshooting

### Error 502 Bad Gateway
**Causa**: Servicio dormido
**Solución**: El sistema reintenta automáticamente después de 30 segundos

### Timeout en Análisis
**Causa**: Cold start + análisis largo
**Solución**: Timeout extendido a 15 minutos

### Webhook Falla
**Causa**: Ambos servicios dormidos
**Solución**: 
1. Despertar servicios manualmente
2. Reenviar webhook desde Pipefy
3. O procesar manualmente el card

## Logs de Debugging

### Logs Normales (Servicio Activo)
```
🏥 Verificando estado del servicio CrewAI...
✅ Servicio CrewAI está activo
🚀 Iniciando análisis CrewAI...
✅ Análisis CrewAI completado exitosamente
```

### Logs de Cold Start
```
🛌 Servicio CrewAI está dormido (502 Bad Gateway) - Reintentando en 30 segundos...
🔄 Reintentando llamada a CrewAI después de cold start...
✅ Análisis CrewAI completado exitosamente en reintento
```

### Logs de Error
```
⏰ Timeout al llamar al servicio CrewAI
💡 Esto puede indicar que el servicio está en cold start
```

## Arquitectura Mejorada

```
📥 Webhook Pipefy
    ↓
🏥 Health Check CrewAI (30s timeout)
    ↓
🚀 Llamada CrewAI (900s timeout)
    ↓ (si 502)
⏳ Esperar 30s + Retry automático
    ↓
✅ Análisis completado
    ↓
📝 Actualizar Pipefy
```

## Beneficios

1. **Robustez**: Maneja automáticamente cold starts
2. **Transparencia**: Logs claros sobre el estado
3. **Flexibilidad**: Endpoints de utilidad para control manual
4. **Monitoreo**: Health checks mejorados
5. **Modularidad**: Mantiene separación de responsabilidades

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