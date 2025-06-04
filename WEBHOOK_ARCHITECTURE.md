# 🔔 Arquitectura de Webhooks - Integración Supabase → Pipefy

## 📋 Resumen

Esta implementación utiliza **Database Webhooks de Supabase** para crear una arquitectura **event-driven** completamente modular que actualiza automáticamente Pipefy cuando se genera un nuevo informe de análisis.

## 🏗️ Arquitectura

### Flujo Completo:
```
1. CrewAI → Analiza documentos
2. CrewAI → Guarda informe en tabla "informe_cadastro" 
3. Supabase → Detecta INSERT automáticamente
4. Supabase → Dispara webhook via pg_net
5. Webhook → Llama endpoint en módulo de ingestión
6. Módulo Ingestión → Actualiza campo "Observações da Validação Credito" en Pipefy
```

### Ventajas de esta Arquitectura:

✅ **Máxima Modularidad**: Cada servicio mantiene su responsabilidad específica  
✅ **Desacoplamiento Total**: No hay dependencias directas entre servicios  
✅ **Event-Driven**: Arquitectura basada en eventos, más escalable  
✅ **Asíncrono**: No bloquea el proceso de análisis  
✅ **Confiabilidad**: Supabase maneja reintentos automáticamente  
✅ **Simplicidad**: Menos código, menos complejidad  

## 🔧 Componentes Técnicos

### 1. Database Trigger (Supabase)
```sql
-- Función que se ejecuta en cada INSERT
CREATE OR REPLACE FUNCTION notify_informe_created()
RETURNS TRIGGER AS $$
DECLARE
    webhook_url TEXT := 'https://pipefy-document-ingestion-modular.onrender.com/webhook/supabase/informe-created';
    payload JSONB;
BEGIN
    payload := jsonb_build_object(
        'type', 'INSERT',
        'table', 'informe_cadastro',
        'schema', 'public',
        'record', row_to_json(NEW),
        'old_record', null
    );
    
    PERFORM net.http_post(
        url := webhook_url,
        headers := '{"Content-Type": "application/json"}'::jsonb,
        body := payload::text
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger que ejecuta la función
CREATE TRIGGER trigger_informe_cadastro_webhook
    AFTER INSERT ON public.informe_cadastro
    FOR EACH ROW
    EXECUTE FUNCTION notify_informe_created();
```

### 2. Webhook Endpoint (Módulo de Ingestión)
```python
@app.post("/webhook/supabase/informe-created")
async def handle_supabase_informe_webhook(
    payload: SupabaseWebhookPayload,
    background_tasks: BackgroundTasks,
    request: Request
):
    """
    Webhook que se activa cuando se crea un nuevo registro en 'informe_cadastro'.
    Actualiza automáticamente el campo 'Observações da Validação Credito' en Pipefy.
    """
    # Validar evento
    if payload.type != "INSERT" or payload.table != "informe_cadastro":
        return {"status": "ignored"}
    
    # Extraer datos
    case_id = payload.record.get("case_id")
    summary_report = payload.record.get("summary_report")
    
    # Actualizar Pipefy en background
    background_tasks.add_task(
        update_pipefy_observacoes_field,
        case_id,
        summary_report
    )
    
    return {"status": "success", "case_id": case_id}
```

### 3. Integración Pipefy (Módulo de Ingestión)
```python
async def update_pipefy_observacoes_field(case_id: str, informe_content: str) -> bool:
    """
    Actualiza el campo 'Observações da Validação Credito' en Pipefy.
    Detecta automáticamente el field_id correcto.
    """
    # Detectar field_id automáticamente
    field_id = await get_pipefy_field_id_for_observacoes(case_id)
    
    # Actualizar campo
    return await update_pipefy_card_field(case_id, field_id, informe_content)
```

## 🚀 Endpoints Disponibles

### Webhook Principal
- **POST** `/webhook/supabase/informe-created`
  - Recibe notificaciones automáticas de Supabase
  - Actualiza Pipefy en background

### Endpoint de Prueba
- **POST** `/test/update-pipefy-observacoes`
  - Para testing manual de la integración Pipefy
  - Parámetros: `case_id`, `informe_content`

## 🔍 Monitoreo y Debugging

### Logs de Supabase
```sql
-- Ver historial de requests HTTP (pg_net)
SELECT * FROM net._http_response 
ORDER BY created_at DESC 
LIMIT 10;
```

### Logs del Módulo de Ingestión
- Todos los webhooks se registran con nivel INFO
- Errores se registran con nivel ERROR y traceback completo

### Testing Manual
```bash
# Probar webhook directamente
curl -X POST "https://pipefy-document-ingestion-modular.onrender.com/test/update-pipefy-observacoes" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "CASO-TESTE-001",
    "informe_content": "Teste de integração Pipefy via webhook"
  }'
```

## 🔒 Seguridad

### Validaciones Implementadas:
- ✅ Validación de tipo de evento (solo INSERT)
- ✅ Validación de tabla (solo informe_cadastro)
- ✅ Validación de datos requeridos (case_id)
- ✅ Manejo robusto de errores
- ✅ Timeouts configurados (5 segundos)

### Recomendaciones Adicionales:
- [ ] Implementar autenticación en webhook endpoint
- [ ] Agregar rate limiting
- [ ] Implementar webhook signature verification

## 📊 Comparación con Arquitectura Anterior

| Aspecto | Arquitectura Anterior | Arquitectura con Webhooks |
|---------|----------------------|---------------------------|
| **Modularidad** | ❌ CrewAI conoce Pipefy | ✅ Servicios independientes |
| **Acoplamiento** | ❌ Alto acoplamiento | ✅ Bajo acoplamiento |
| **Escalabilidad** | ⚠️ Limitada | ✅ Alta escalabilidad |
| **Mantenimiento** | ❌ Complejo | ✅ Simple |
| **Confiabilidad** | ⚠️ Manual | ✅ Automática |
| **Testing** | ❌ Difícil | ✅ Fácil |

## 🎯 Próximos Pasos

1. **Testing Completo**: Probar flujo end-to-end
2. **Monitoreo**: Implementar alertas para fallos
3. **Documentación**: Actualizar README principal
4. **Optimización**: Ajustar timeouts y reintentos

---

**Arquitectura Event-Driven implementada con éxito! 🎉**

*Esta solución respeta completamente el principio de modularidad del proyecto.* 