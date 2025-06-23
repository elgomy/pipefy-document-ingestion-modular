# Document Triaging Agent v2.0 - Arquitectura Modular

## 🏗️ Arquitectura Híbrida Inteligente

Este proyecto implementa un **enfoque híbrido inteligente** con dos servicios independientes desplegados en Render:

### 🔧 Backend API Completo (`pipefy-document-ingestion-v2`)
**Responsabilidad:** Contiene TODA la lógica de negocio
- ✅ Procesamiento de webhooks de Pipefy
- ✅ Integración con APIs externas (CNPJá, Twilio, BrasilAPI)
- ✅ Gestión completa de Supabase (Storage + Database)
- ✅ Orquestación de flujos de trabajo
- ✅ Sistema de métricas y error handling
- ✅ Endpoints HTTP simples para el agente

### 🤖 Agente CrewAI Enfocado (`pipefy-crewai-analysis-v2`)
**Responsabilidad:** Solo análisis con IA usando herramientas simples
- ✅ Análisis de documentos con IA
- ✅ Herramientas súper simples que llaman al backend
- ✅ NO contiene lógica de APIs externas
- ✅ Enfocado únicamente en razonamiento y análisis

## 🚀 Despliegue en Render

### Servicio 1: Backend API
```bash
# En pipefy-document-ingestion-v2/
# URL: https://pipefy-document-ingestion-v2.onrender.com
# Puerto: 8000
# Endpoints principales:
# - POST /webhook/pipefy (punto de entrada principal)
# - POST /api/v1/cliente/enriquecer
# - GET /api/v1/documentos/{case_id}
# - POST /api/v1/whatsapp/enviar
```

### Servicio 2: Agente CrewAI
```bash
# En pipefy-crewai-analysis-v2/
# URL: https://pipefy-crewai-analysis-v2.onrender.com
# Puerto: 8001
# Endpoints principales:
# - POST /analyze (análisis de documentos)
# - GET /health
```

## 🔄 Flujo de Trabajo

1. **Webhook de Pipefy** → `pipefy-document-ingestion-v2` (puerto 8000)
2. **Backend procesa** documentos y datos de negocio
3. **Backend llama** al agente CrewAI cuando necesita análisis
4. **Agente usa herramientas simples** que llaman de vuelta al backend
5. **Backend actualiza** Pipefy y envía notificaciones

## 🛠️ Configuración de Variables de Entorno

### Para pipefy-document-ingestion-v2:
```bash
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_key
PIPEFY_TOKEN=your_pipefy_token
PIPEFY_WEBHOOK_SECRET=your_webhook_secret
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
CNPJA_API_KEY=your_cnpja_key
CREWAI_SERVICE_URL=https://pipefy-crewai-analysis-v2.onrender.com
```

### Para pipefy-crewai-analysis-v2:
```bash
OPENAI_API_KEY=your_openai_key
DOCUMENT_INGESTION_URL=https://pipefy-document-ingestion-v2.onrender.com
```

## 📁 Estructura del Proyecto

```
Pipefy-Render-Supabase-CrewAI_cadastro/
├── pipefy-document-ingestion-v2/     # 🔧 Backend API Completo
│   ├── app.py                        # FastAPI con toda la lógica
│   ├── src/                          # Servicios y utilidades
│   ├── render.yaml                   # Configuración Render
│   └── requirements.txt              # Dependencias
├── pipefy-crewai-analysis-v2/        # 🤖 Agente CrewAI Enfocado
│   ├── app.py                        # FastAPI para análisis
│   ├── src/tools/                    # Herramientas simples
│   ├── render.yaml                   # Configuración Render
│   └── requirements.txt              # Dependencias
└── scripts/                          # Scripts de desarrollo
```

## 🎯 Ventajas de esta Arquitectura

1. **Modularidad Máxima**: Cada servicio tiene responsabilidades claras
2. **Escalabilidad**: Servicios independientes pueden escalar por separado
3. **Flexibilidad**: Cambios en APIs externas solo afectan el backend
4. **Mantenibilidad**: Código más limpio y fácil de debuggear
5. **Testabilidad**: Cada componente se puede probar independientemente

## 🔧 Desarrollo Local

### Backend API:
```bash
cd pipefy-document-ingestion-v2
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Agente CrewAI:
```bash
cd pipefy-crewai-analysis-v2
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8001 --reload
```

## 📊 Monitoreo

Cada servicio expone su propio endpoint `/health` para monitoreo independiente:
- Backend API: `https://pipefy-document-ingestion-v2.onrender.com/health`
- Agente CrewAI: `https://pipefy-crewai-analysis-v2.onrender.com/health`

## 🚀 Estado del Proyecto

- ✅ **Task 12**: Arquitectura Modular - **COMPLETADA**
- ⏳ **Próxima**: Integration and End-to-End Tests

La arquitectura híbrida está lista para validación con tests de integración entre servicios.
