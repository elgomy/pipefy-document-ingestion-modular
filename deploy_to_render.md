# 🚀 Guía de Despliegue en Render - Arquitectura Modular

## 🏗️ Arquitectura de Dos Servicios Independientes

Este proyecto se despliega como **dos servicios independientes** en Render:

1. **Backend API Completo** (`pipefy-document-ingestion-v2`)
2. **Agente CrewAI Enfocado** (`pipefy-crewai-analysis-v2`)

## 📋 Pre-requisitos

- Cuenta en [Render](https://render.com)
- Repositorio en GitHub con ambos servicios
- Variables de entorno configuradas

## 🔧 Servicio 1: Backend API (pipefy-document-ingestion-v2)

### 1.1 Crear Web Service en Render

1. **Conectar Repositorio**:
   - Ir a Render Dashboard → "New" → "Web Service"
   - Conectar el repositorio GitHub
   - **Root Directory**: `pipefy-document-ingestion-v2`

2. **Configuración Básica**:
   - **Name**: `pipefy-document-ingestion-v2`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`

3. **Variables de Entorno** (Environment Variables):
   ```bash
   # Supabase
   SUPABASE_URL=https://tu-proyecto.supabase.co
   SUPABASE_ANON_KEY=tu_supabase_anon_key
   SUPABASE_STORAGE_BUCKET_NAME=documents
   
   # Pipefy
   PIPEFY_TOKEN=tu_pipefy_token
   PIPEFY_WEBHOOK_SECRET=tu_webhook_secret
   PHASE_ID_PENDENCIAS=338000018
   PHASE_ID_EMITIR_DOCS=338000019
   PHASE_ID_APROVADO=338000021
   
   # Twilio WhatsApp
   TWILIO_ACCOUNT_SID=tu_twilio_sid
   TWILIO_AUTH_TOKEN=tu_twilio_token
   TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
   
   # CNPJá API
   CNPJA_API_KEY=tu_cnpja_key
   
   # Comunicación entre servicios
   CREWAI_SERVICE_URL=https://pipefy-crewai-analysis-v2.onrender.com
   ```

4. **Plan Recomendado**: `Starter` o superior
5. **Auto-Deploy**: Habilitado desde `main` branch

### 1.2 URL del Servicio
```
https://pipefy-document-ingestion-v2.onrender.com
```

## 🤖 Servicio 2: Agente CrewAI (pipefy-crewai-analysis-v2)

### 2.1 Crear Web Service en Render

1. **Conectar Repositorio**:
   - Render Dashboard → "New" → "Web Service"
   - Mismo repositorio GitHub
   - **Root Directory**: `pipefy-crewai-analysis-v2`

2. **Configuración Básica**:
   - **Name**: `pipefy-crewai-analysis-v2`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`

3. **Variables de Entorno**:
   ```bash
   # OpenAI para análisis
   OPENAI_API_KEY=tu_openai_api_key
   
   # Comunicación con backend
   DOCUMENT_INGESTION_URL=https://pipefy-document-ingestion-v2.onrender.com
   
   # Opcional: LlamaParse si se usa
   LLAMACLOUD_API_KEY=tu_llama_api_key
   ```

4. **Plan Recomendado**: `Starter` o superior
5. **Auto-Deploy**: Habilitado desde `main` branch

### 2.2 URL del Servicio
```
https://pipefy-crewai-analysis-v2.onrender.com
```

## 🔗 Configuración de Webhooks

### Webhook de Pipefy
- **URL**: `https://pipefy-document-ingestion-v2.onrender.com/webhook/pipefy`
- **Método**: `POST`
- **Trigger**: Cuando card se mueve a fase `338000020` (Triagem Documentos AI)

### Webhook de Supabase (opcional)
- **URL**: `https://pipefy-document-ingestion-v2.onrender.com/webhook/supabase`
- **Método**: `POST`
- **Trigger**: Cambios en tablas relevantes

## 🔍 Verificación del Despliegue

### 1. Health Checks
```bash
# Backend API
curl https://pipefy-document-ingestion-v2.onrender.com/health

# Agente CrewAI
curl https://pipefy-crewai-analysis-v2.onrender.com/health
```

### 2. Test de Comunicación
```bash
# Verificar que el agente puede comunicarse con el backend
curl -X POST https://pipefy-crewai-analysis-v2.onrender.com/test/backend-connection
```

## 📊 Monitoreo

### Logs en Render
1. **Backend API**: Render Dashboard → `pipefy-document-ingestion-v2` → "Logs"
2. **Agente CrewAI**: Render Dashboard → `pipefy-crewai-analysis-v2` → "Logs"

### Métricas Importantes
- **Tiempo de respuesta** de webhooks
- **Errores de comunicación** entre servicios
- **Uso de memoria** y CPU
- **Tiempo de análisis** del agente CrewAI

## 🚨 Troubleshooting

### Problemas Comunes

1. **Servicio no inicia**:
   - Verificar variables de entorno
   - Revisar logs de build
   - Confirmar que `requirements.txt` esté actualizado

2. **Error de comunicación entre servicios**:
   - Verificar URLs en variables de entorno
   - Confirmar que ambos servicios estén corriendo
   - Revisar timeouts en llamadas HTTP

3. **Webhook de Pipefy falla**:
   - Verificar `PIPEFY_WEBHOOK_SECRET`
   - Confirmar URL del webhook en Pipefy
   - Revisar logs del backend

### Comandos de Diagnóstico
```bash
# Verificar conectividad
curl -I https://pipefy-document-ingestion-v2.onrender.com
curl -I https://pipefy-crewai-analysis-v2.onrender.com

# Test de webhook (desde Pipefy)
# Usar el trigger manual en Pipefy Dashboard
```

## 🔄 Actualización de Servicios

### Deploy Automático
- Ambos servicios se actualizan automáticamente con push a `main`
- Render detecta cambios en sus respectivos directorios

### Deploy Manual
1. Ir a Render Dashboard
2. Seleccionar el servicio
3. Click en "Manual Deploy"
4. Seleccionar branch/commit

## 📝 Configuración de Dominio Personalizado (Opcional)

### Backend API
1. Render Dashboard → `pipefy-document-ingestion-v2` → "Settings" → "Custom Domains"
2. Agregar: `api.tu-dominio.com`
3. Actualizar webhook de Pipefy con nueva URL

### Agente CrewAI
1. Render Dashboard → `pipefy-crewai-analysis-v2` → "Settings" → "Custom Domains"
2. Agregar: `ai.tu-dominio.com`
3. Actualizar `CREWAI_SERVICE_URL` en backend

## ✅ Checklist de Despliegue

- [ ] Backend API desplegado y funcionando
- [ ] Agente CrewAI desplegado y funcionando
- [ ] Variables de entorno configuradas en ambos servicios
- [ ] Health checks pasando
- [ ] Webhook de Pipefy configurado
- [ ] Comunicación entre servicios verificada
- [ ] Logs monitoreando correctamente

---

**¡Arquitectura modular desplegada exitosamente! 🎉**

Cada servicio es independiente, escalable y mantenible por separado. 