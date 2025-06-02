<<<<<<< HEAD
# 📄 Document Ingestion Service

Servicio modular para ingestión de documentos desde Pipefy hacia Supabase con comunicación HTTP directa.

## 🏗️ Arquitectura

- **Responsabilidad**: Procesar webhooks de Pipefy, descargar documentos y almacenarlos en Supabase
- **Comunicación**: HTTP directa con el servicio CrewAI
- **Puerto**: 8003
- **Modularidad**: Servicio independiente y desacoplado

## 🚀 Despliegue en Render

### Variables de Entorno Requeridas:
- `SUPABASE_URL`: URL de tu proyecto Supabase
- `SUPABASE_SERVICE_KEY`: Service key de Supabase
- `PIPEFY_TOKEN`: Token de API de Pipefy
- `PIPEFY_WEBHOOK_SECRET`: Secret para validar webhooks (opcional)
- `SUPABASE_STORAGE_BUCKET_NAME`: Nombre del bucket (default: documents)
- `CREWAI_SERVICE_URL`: URL del servicio CrewAI en Render

### Comando de Inicio:
```bash
uvicorn fastAPI_modular_http:app --host 0.0.0.0 --port $PORT
```

## 📋 Endpoints

- `POST /webhook/pipefy` - Recibe webhooks de Pipefy
- `GET /health` - Health check
- `GET /` - Información del servicio

## 🔗 Comunicación

Este servicio se comunica con:
- **Pipefy**: Recibe webhooks y consulta API GraphQL
- **Supabase**: Almacena documentos y metadatos
- **CrewAI Service**: Envía documentos para análisis via HTTP

## 📦 Dependencias

Ver `requirements.txt` para la lista completa de dependencias. 
=======
# pipefy-document-ingestion-modular
 Servicio modular de ingestión de documentos Pipefy-Supabase con comunicación HTTP directa
>>>>>>> 7f9eb48a7ab55d3b3ddf935a6d974519d33014d4
