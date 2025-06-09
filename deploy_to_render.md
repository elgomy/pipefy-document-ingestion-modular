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

#### 🗄️ Variables Obligatorias (Supabase)
```
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_SERVICE_KEY=tu_service_key_aqui
SUPABASE_STORAGE_BUCKET_NAME=documents
```

#### 🔗 Variables Obligatorias (Pipefy)
```
PIPEFY_TOKEN=tu_token_pipefy_aqui
PIPEFY_WEBHOOK_SECRET=tu_webhook_secret_opcional
```

#### 🤖 Comunicación con CrewAI
```
CREWAI_SERVICE_URL=https://pipefy-crewai-analysis-modular.onrender.com
```

#### 🆕 Nuevas Integraciones (Opcionales según PRD)

**📱 Twilio - Para notificaciones WhatsApp:**
```
TWILIO_ACCOUNT_SID=tu_twilio_sid_aqui
TWILIO_AUTH_TOKEN=tu_twilio_token_aqui
TWILIO_WHATSAPP_NUMBER=+17245586619
```

**🏭 CNPJá API - Para generación automática de Cartão CNPJ:**
```
CNPJA_API_KEY=tu_cnpja_api_key_aqui
```

### 3. Configurar Webhook en Pipefy
1. Ve a tu pipe en Pipefy
2. Configuración → Webhooks
3. URL: `https://pipefy-document-ingestion-modular.onrender.com/webhook/pipefy`
4. Eventos: `card.create`, `card.update`

### 4. Configurar Webhook en Supabase
1. Ve a tu proyecto Supabase
2. Database → Webhooks
3. URL: `https://pipefy-document-ingestion-modular.onrender.com/webhook/supabase`
4. Tabla: `informe_cadastro`
5. Eventos: `INSERT`

### 5. Verificar Despliegue
- Health Check: `GET https://pipefy-document-ingestion-modular.onrender.com/health`
- Debe responder con status "healthy"

## 🔗 URLs del Servicio
- **Webhook Principal**: `/webhook/pipefy`
- **Webhook Supabase**: `/webhook/supabase`
- **Health Check**: `/health`
- **Root**: `/`

## 🧪 Endpoints de Prueba
- **Orquestador**: `POST /test/orchestrator`
- **Escenarios**: `POST /test/orchestrator-scenarios`
- **Campo Pipefy**: `POST /test/robust-field-handling`

## 📊 Funcionalidades Implementadas
- ✅ Procesamiento de documentos desde Pipefy
- ✅ Almacenamiento en Supabase
- ✅ Comunicación HTTP directa con CrewAI
- ✅ Orquestador de resultados según PRD
- ✅ Movimiento automático de cards entre fases
- ✅ Notificaciones WhatsApp para pendencias críticas
- ✅ Generación automática de Cartão CNPJ
- ✅ Manejo de cold starts de Render

## 📝 Notas Importantes
- Las variables de Twilio y CNPJá son **opcionales**
- Sin estas variables, el sistema funcionará pero sin las funcionalidades avanzadas
- Los IDs de fases están configurados en el código para el pipe específico
- El sistema maneja automáticamente cold starts de servicios en Render 