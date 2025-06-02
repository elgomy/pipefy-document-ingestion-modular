# 🚀 Guía de Despliegue en Render - Document Ingestion Service

## 📋 Pasos para Desplegar

### 1. Crear Servicio en Render
1. Ve a [Render Dashboard](https://dashboard.render.com/)
2. Haz clic en "New +" → "Web Service"
3. Conecta este repositorio GitHub
4. Configura el servicio:
   - **Name**: `pipefy-document-ingestion-modular`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`

### 2. Configurar Variables de Entorno
En la sección "Environment" de Render, agrega:

```
SUPABASE_URL=tu_url_supabase_aqui
SUPABASE_SERVICE_KEY=tu_service_key_aqui
PIPEFY_TOKEN=tu_token_pipefy_aqui
PIPEFY_WEBHOOK_SECRET=tu_webhook_secret_aqui
SUPABASE_STORAGE_BUCKET_NAME=documents
CREWAI_SERVICE_URL=https://pipefy-crewai-analysis-modular.onrender.com
```

### 3. Configurar Webhook en Pipefy
1. Ve a tu pipe en Pipefy
2. Configuración → Webhooks
3. URL: `https://pipefy-document-ingestion-modular.onrender.com/webhook/pipefy`
4. Eventos: `card.move`

### 4. Verificar Despliegue
- Health Check: `GET https://pipefy-document-ingestion-modular.onrender.com/health`
- Debe responder con status "healthy"

## 🔗 URLs del Servicio
- **Webhook Principal**: `/webhook/pipefy`
- **Health Check**: `/health`
- **Root**: `/`

## 📊 Monitoreo
- Logs disponibles en Render Dashboard
- Comunicación HTTP directa con servicio CrewAI
- Almacenamiento automático en Supabase 