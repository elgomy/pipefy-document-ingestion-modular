#!/usr/bin/env python3
"""
Servicio de Ingestión de Documentos - Versión HTTP Directa
Se enfoca únicamente en procesar documentos de Pipefy y almacenarlos en Supabase.
Usa comunicación HTTP directa con el servicio CrewAI.
MANTIENE LA MODULARIDAD: Cada servicio tiene su responsabilidad específica.
"""

import os
import asyncio
import tempfile
import httpx
import logging
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any, Union
from fastapi import FastAPI, HTTPException, Request, Header, BackgroundTasks
from pydantic import BaseModel, field_validator, model_validator
from supabase import create_client, Client
from dotenv import load_dotenv
import json
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Variables de entorno
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_STORAGE_BUCKET_NAME = os.getenv("SUPABASE_STORAGE_BUCKET_NAME", "documents")
PIPEFY_TOKEN = os.getenv("PIPEFY_TOKEN")
PIPEFY_WEBHOOK_SECRET = os.getenv("PIPEFY_WEBHOOK_SECRET")

# 🔗 COMUNICACIÓN HTTP DIRECTA - URL del servicio CrewAI
CREWAI_SERVICE_URL = os.getenv("CREWAI_SERVICE_URL", "https://pipefy-crewai-analysis-modular.onrender.com")

# Cliente Supabase global
supabase_client: Optional[Client] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação FastAPI."""
    global supabase_client
    
    # Startup
    logger.info("🚀 Iniciando Servicio de Ingestión de Documentos (HTTP Directo)...")
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        logger.error("ERRO: Variáveis SUPABASE_URL e SUPABASE_SERVICE_KEY são obrigatórias.")
        raise RuntimeError("Configuração Supabase incompleta.")
    
    if not PIPEFY_TOKEN:
        logger.error("ERRO: Variável PIPEFY_TOKEN é obrigatória.")
        raise RuntimeError("Token Pipefy não configurado.")
    
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        logger.info("✅ Cliente Supabase inicializado com sucesso.")
    except Exception as e:
        logger.error(f"ERRO ao inicializar cliente Supabase: {e}")
        raise RuntimeError(f"Falha na inicialização do Supabase: {e}")
    
    logger.info(f"🔗 Servicio CrewAI configurado en: {CREWAI_SERVICE_URL}")
    
    yield
    
    # Shutdown
    logger.info("INFO: Encerrando Servicio de Ingestión de Documentos...")

app = FastAPI(
    lifespan=lifespan, 
    title="Document Ingestion Service - HTTP Direct",
    description="Servicio modular para ingestión de documentos con comunicación HTTP directa"
)

# Modelos Pydantic
class PipefyCard(BaseModel):
    model_config = {"extra": "allow"}
    
    id: str
    title: Optional[str] = None
    current_phase: Optional[Dict[str, Any]] = None
    pipe: Optional[Dict[str, Any]] = None
    fields: Optional[List[Dict[str, Any]]] = None
    
    @model_validator(mode='before')
    @classmethod
    def convert_id_to_string(cls, data):
        if isinstance(data, dict) and 'id' in data:
            data['id'] = str(data['id'])
        return data

class PipefyEventData(BaseModel):
    model_config = {"extra": "allow"}
    card: PipefyCard
    action: Optional[str] = None

class PipefyWebhookPayload(BaseModel):
    model_config = {"extra": "allow"}
    data: PipefyEventData

class PipefyAttachment(BaseModel):
    name: str
    path: str

# 🔗 Modelo para comunicación HTTP directa con CrewAI
class CrewAIAnalysisRequest(BaseModel):
    case_id: str
    documents: List[Dict[str, Any]]
    checklist_url: str
    current_date: str
    pipe_id: Optional[str] = None

# 📋 Modelos para Webhook de Supabase
class SupabaseWebhookPayload(BaseModel):
    """Modelo para el payload del webhook de Supabase"""
    type: str  # INSERT, UPDATE, DELETE
    table: str
    schema: str
    record: Optional[Dict[str, Any]] = None
    old_record: Optional[Dict[str, Any]] = None

# 🔍 Función para detectar automáticamente el field_id de Pipefy
async def get_pipefy_field_id_for_informe_crewai(card_id: str) -> Optional[str]:
    """
    Detecta automáticamente el field_id del campo 'Informe CrewAI' en Pipefy.
    OPTIMIZADO: Funciona con campos creados directamente en el formulario del card.
    
    Args:
        card_id: ID del card de Pipefy
    
    Returns:
        str: field_id si se encuentra, None en caso contrario
    """
    if not PIPEFY_TOKEN:
        logger.error("ERRO: Token Pipefy não configurado.")
        return None
    
    query = """
    query GetCardFields($cardId: ID!) {
        card(id: $cardId) {
            id
            fields {
                field {
                    id
                    label
                    type
                }
                name
                value
            }
        }
    }
    """
    
    variables = {"cardId": card_id}
    headers = {
        "Authorization": f"Bearer {PIPEFY_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": query,
        "variables": variables
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("https://api.pipefy.com/graphql", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data:
                logger.error(f"ERRO GraphQL ao buscar campos: {data['errors']}")
                return None
            
            card_data = data.get("data", {}).get("card")
            if not card_data:
                logger.warning(f"Card {card_id} não encontrado.")
                return None
            
            fields = card_data.get("fields", [])
            
            # Buscar por nome exato "Informe CrewAI"
            for field in fields:
                field_info = field.get("field", {})
                field_label = field_info.get("label", "").strip()
                field_name = field.get("name", "").strip()
                
                # Verificar coincidencia exacta con "Informe CrewAI"
                if field_label == "Informe CrewAI" or field_name == "Informe CrewAI":
                    field_id = field_info.get("id")
                    logger.info(f"✅ Campo 'Informe CrewAI' encontrado: ID {field_id}")
                    logger.info(f"   - Label: '{field_label}'")
                    logger.info(f"   - Name: '{field_name}'")
                    logger.info(f"   - Type: {field_info.get('type')}")
                    return field_id
            
            # Si no se encuentra con nombre exacto, buscar por palabras clave
            target_keywords = [
                "informe crewai",
                "informe crew ai", 
                "crewai informe",
                "crew ai informe"
            ]
            
            for field in fields:
                field_info = field.get("field", {})
                field_label = field_info.get("label", "").lower()
                field_name = field.get("name", "").lower()
                
                for keyword in target_keywords:
                    if keyword in field_label or keyword in field_name:
                        field_id = field_info.get("id")
                        logger.info(f"✅ Campo encontrado por keyword '{keyword}': ID {field_id}")
                        logger.info(f"   - Label: '{field_info.get('label')}'")
                        logger.info(f"   - Name: '{field.get('name')}'")
                        return field_id
            
            logger.warning(f"⚠️ Campo 'Informe CrewAI' não encontrado no card {card_id}")
            logger.info("📋 Campos disponibles en el card:")
            for field in fields:
                field_info = field.get("field", {})
                logger.info(f"   - '{field.get('name')}' (Label: '{field_info.get('label')}', ID: {field_info.get('id')})")
            
            return None
            
    except Exception as e:
        logger.error(f"ERRO ao buscar field_id para card {card_id}: {e}")
        return None

# 📝 Función para actualizar campo específico en Pipefy
async def update_pipefy_informe_crewai_field(card_id: str, informe_content: str) -> bool:
    """
    Actualiza el campo 'Informe CrewAI' en Pipefy.
    CORREGIDO: Usa la sintaxis correcta de updateCardField según documentación oficial.
    
    Args:
        card_id: ID del card de Pipefy
        informe_content: Contenido del informe a actualizar
    
    Returns:
        bool: True si la actualización fue exitosa, False en caso contrario
    """
    try:
        logger.info(f"🔄 Iniciando actualización del campo 'Informe CrewAI' para card: {card_id}")
        
        # PASO 1: Buscar el field_id del campo 'Informe CrewAI'
        field_id = await get_pipefy_field_id_for_informe_crewai(card_id)
        
        if not field_id:
            logger.error(f"❌ No se pudo encontrar el campo 'Informe CrewAI' en el card {card_id}")
            return False
        
        # PASO 2: Actualizar el campo con la sintaxis CORRECTA de Pipefy
        logger.info(f"📝 Actualizando campo ID {field_id} con el informe...")
        
        # SINTAXIS CORREGIDA según documentación oficial de Pipefy
        mutation = """
        mutation {
            updateCardField(input: {card_id: %s, field_id: "%s", new_value: "%s"}) {
                card {
                    id
                    title
                }
            }
        }
        """ % (card_id, field_id, informe_content.replace('"', '\\"').replace('\n', '\\n'))
        
        headers = {
            "Authorization": f"Bearer {PIPEFY_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": mutation
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post("https://api.pipefy.com/graphql", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data:
                logger.error(f"❌ Erro GraphQL ao atualizar campo: {data['errors']}")
                return False
            
            result = data.get("data", {}).get("updateCardField", {})
            card_info = result.get("card", {})
            
            if card_info and card_info.get("id"):
                logger.info(f"✅ Campo 'Informe CrewAI' atualizado com sucesso!")
                logger.info(f"   - Card ID: {card_info.get('id')}")
                logger.info(f"   - Card Title: {card_info.get('title')}")
                logger.info(f"   - Field ID: {field_id}")
                logger.info(f"   - Conteúdo: {informe_content[:100]}...")
                return True
            else:
                logger.error(f"❌ Resposta inesperada da mutação: {result}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar campo 'Informe CrewAI': {e}")
        return False

# Funciones auxiliares (iguales al original)
async def get_pipefy_card_attachments(card_id: str) -> List[PipefyAttachment]:
    """Obtém anexos de um card do Pipefy via GraphQL."""
    if not PIPEFY_TOKEN:
        logger.error("ERRO: Token Pipefy não configurado.")
        return []
    
    query = """
    query GetCardAttachments($cardId: ID!) {
        card(id: $cardId) {
            id
            title
            fields {
                name
                value
            }
        }
    }
    """
    
    variables = {"cardId": card_id}
    headers = {
        "Authorization": f"Bearer {PIPEFY_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": query,
        "variables": variables
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("https://api.pipefy.com/graphql", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data:
                logger.error(f"ERRO GraphQL Pipefy: {data['errors']}")
                return []
            
            card_data = data.get("data", {}).get("card")
            if not card_data:
                logger.warning(f"ALERTA: Card {card_id} não encontrado ou sem dados.")
                return []
            
            attachments = []
            fields = card_data.get("fields", [])
            
            for field in fields:
                field_value = field.get("value", "")
                if field_value and isinstance(field_value, str):
                    try:
                        import json
                        urls = json.loads(field_value)
                        if isinstance(urls, list):
                            for url in urls:
                                if isinstance(url, str) and url.startswith("http"):
                                    filename = url.split("/")[-1].split("?")[0]
                                    if not filename or filename == "":
                                        filename = f"{field.get('name', 'documento')}.pdf"
                                    
                                    attachments.append(PipefyAttachment(
                                        name=filename,
                                        path=url
                                    ))
                    except (json.JSONDecodeError, TypeError):
                        if field_value.startswith("http"):
                            filename = field_value.split("/")[-1].split("?")[0]
                            if not filename or filename == "":
                                filename = f"{field.get('name', 'documento')}.pdf"
                            
                            attachments.append(PipefyAttachment(
                                name=filename,
                                path=field_value
                            ))
            
            logger.info(f"INFO: {len(attachments)} anexos encontrados para card {card_id}.")
            return attachments
            
    except Exception as e:
        logger.error(f"ERRO ao buscar anexos do card {card_id}: {e}")
        return []

async def download_file_to_temp(url: str, original_filename: str) -> Optional[str]:
    """Baixa um arquivo de uma URL para um arquivo temporário."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{original_filename}") as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name
            
            logger.info(f"INFO: Arquivo '{original_filename}' baixado para: {temp_file_path}")
            return temp_file_path
            
    except Exception as e:
        logger.error(f"ERRO ao baixar arquivo '{original_filename}' de {url}: {e}")
        return None

async def upload_to_supabase_storage_async(local_file_path: str, case_id: str, original_filename: str) -> Optional[str]:
    """Faz upload de um arquivo local para o Supabase Storage."""
    if not supabase_client:
        logger.error("ERRO: Cliente Supabase não inicializado.")
        return None
    
    try:
        storage_path = f"{case_id}/{original_filename}"
        
        def sync_upload_and_get_url():
            with open(local_file_path, 'rb') as file:
                upload_response = supabase_client.storage.from_(SUPABASE_STORAGE_BUCKET_NAME).upload(
                    storage_path, file, file_options={"upsert": "true"}
                )
                
                if hasattr(upload_response, 'error') and upload_response.error:
                    raise Exception(f"Erro no upload: {upload_response.error}")
                
                public_url_response = supabase_client.storage.from_(SUPABASE_STORAGE_BUCKET_NAME).get_public_url(storage_path)
                return public_url_response
        
        public_url = await asyncio.to_thread(sync_upload_and_get_url)
        
        # Limpar arquivo temporário
        try:
            os.unlink(local_file_path)
        except:
            pass
        
        logger.info(f"INFO: Upload concluído para '{original_filename}'. URL: {public_url}")
        return public_url
        
    except Exception as e:
        logger.error(f"ERRO no upload de '{original_filename}': {e}")
        try:
            os.unlink(local_file_path)
        except:
            pass
        return None

async def determine_document_tag(filename: str, card_fields: Optional[List[Dict]] = None) -> str:
    """Determina a tag do documento baseada no nome do arquivo."""
    filename_lower = filename.lower()
    
    tag_keywords = {
        "contrato_social": ["contrato", "social", "estatuto"],
        "comprovante_residencia": ["comprovante", "residencia", "endereco"],
        "documento_identidade": ["rg", "identidade", "cnh"],
        "declaracao_impostos": ["declaracao", "imposto", "ir"],
        "certificado_registro": ["certificado", "registro"],
        "procuracao": ["procuracao"],
        "balanco_patrimonial": ["balanco", "patrimonial", "demonstracao"],
        "faturamento": ["faturamento", "receita"]
    }
    
    for tag, keywords in tag_keywords.items():
        if any(keyword in filename_lower for keyword in keywords):
            return tag
    
    return "outro_documento"

async def register_document_in_db(case_id: str, document_name: str, document_tag: str, file_url: str, pipe_id: Optional[str] = None):
    """Registra um documento na tabela 'documents' do Supabase."""
    if not supabase_client:
        logger.error("ERRO: Cliente Supabase não inicializado.")
        return False
    
    try:
        data_to_insert = {
            "case_id": case_id,
            "name": document_name,
            "document_tag": document_tag,
            "file_url": file_url,
            "status": "uploaded"
        }
        
        if pipe_id:
            data_to_insert["pipe_id"] = pipe_id
            logger.info(f"INFO: Registrando documento con pipe_id: {pipe_id}")
        
        response = await asyncio.to_thread(
            supabase_client.table("documents").upsert(data_to_insert, on_conflict="case_id, name").execute
        )
        
        if hasattr(response, 'error') and response.error:
            logger.error(f"ERRO Supabase DB (upsert) para {document_name}: {response.error.message}")
            return False
        if response.data:
            logger.info(f"INFO: Documento '{document_name}' registrado/atualizado no DB para case_id '{case_id}'.")
            return True
        logger.warning(f"AVISO: Upsert do documento '{document_name}' no DB não retornou dados nem erro explícito.")
        return False
    except Exception as e:
        logger.error(f"ERRO ao registrar documento '{document_name}' no Supabase DB: {e}")
        return False

async def get_checklist_url_from_supabase(config_name: str = "checklist_cadastro_pj") -> str:
    """Obtém a URL do checklist da tabela checklist_config."""
    if not supabase_client:
        logger.warning("AVISO: Cliente Supabase não inicializado para buscar checklist. Usando URL padrão.")
        return "https://aguoqgqbdbyipztgrmbd.supabase.co/storage/v1/object/public/checklist/checklist.pdf"
    
    try:
        logger.info(f"INFO: Buscando URL do checklist '{config_name}' de checklist_config...")
        
        def sync_get_checklist_url():
            return supabase_client.table("checklist_config").select("checklist_url").eq("config_name", config_name).single().execute()
        
        response = await asyncio.to_thread(sync_get_checklist_url)

        if response.data and response.data.get("checklist_url"):
            checklist_url = response.data["checklist_url"]
            logger.info(f"INFO: URL do checklist obtida: {checklist_url}")
            return checklist_url
        else:
            logger.warning(f"AVISO: URL do checklist '{config_name}' não encontrada. Usando URL padrão.")
            return "https://aguoqgqbdbyipztgrmbd.supabase.co/storage/v1/object/public/checklist/checklist.pdf"
            
    except Exception as e:
        logger.warning(f"AVISO: Erro ao buscar URL do checklist '{config_name}': {e}. Usando URL padrão.")
        return "https://aguoqgqbdbyipztgrmbd.supabase.co/storage/v1/object/public/checklist/checklist.pdf"

# 🔗 COMUNICACIÓN HTTP DIRECTA CON CREWAI
async def call_crewai_analysis_service(case_id: str, documents: List[Dict], checklist_url: str, pipe_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Llama directamente al servicio CrewAI para análisis de documentos.
    MANTIENE LA MODULARIDAD: Solo llama al servicio, no guarda en Supabase.
    El módulo CrewAI se encarga de guardar el informe en la tabla informe_cadastro.
    
    MEJORADO: Maneja cold starts y timeouts de Render.
    """
    try:
        # Preparar payload para CrewAI
        analysis_request = CrewAIAnalysisRequest(
            case_id=case_id,
            documents=documents,
            checklist_url=checklist_url,
            current_date=datetime.now().strftime('%Y-%m-%d'),
            pipe_id=pipe_id
        )
        
        logger.info(f"🔗 Llamando al servicio CrewAI para case_id: {case_id}")
        logger.info(f"📄 Documentos a analizar: {len(documents)}")
        logger.info(f"🎯 URL CrewAI: {CREWAI_SERVICE_URL}/analyze/sync")
        
        # MEJORADO: Primero verificar que el servicio esté despierto
        logger.info("🏥 Verificando estado del servicio CrewAI...")
        try:
            async with httpx.AsyncClient(timeout=30.0) as health_client:
                health_response = await health_client.get(f"{CREWAI_SERVICE_URL}/health")
                if health_response.status_code == 200:
                    logger.info("✅ Servicio CrewAI está activo")
                else:
                    logger.warning(f"⚠️ Servicio CrewAI respondió con status: {health_response.status_code}")
        except Exception as health_error:
            logger.warning(f"⚠️ No se pudo verificar estado del servicio: {health_error}")
        
        # Llamada HTTP directa al servicio CrewAI con timeout extendido para cold starts
        logger.info("🚀 Iniciando análisis CrewAI (puede tardar si el servicio estaba dormido)...")
        
        # TIMEOUT AUMENTADO: 15 minutos para manejar cold starts + análisis completo
        async with httpx.AsyncClient(timeout=900.0) as client:  
            response = await client.post(
                f"{CREWAI_SERVICE_URL}/analyze/sync",
                json=analysis_request.model_dump()
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Análisis CrewAI completado exitosamente para case_id: {case_id}")
                
                # Procesar resultado completo
                if result.get("status") == "completed" and "analysis_result" in result:
                    analysis_result = result["analysis_result"]
                    summary_report = analysis_result.get("summary_report", "")
                    
                    # MODULARIDAD: Solo el módulo CrewAI guarda en Supabase
                    # Este módulo solo se encarga de la comunicación con Pipefy
                    logger.info(f"💾 Informe guardado por módulo CrewAI en tabla informe_cadastro")
                    
                    # Actualizar campo en Pipefy con el resumen del análisis
                    pipefy_updated = False
                    if summary_report:
                        logger.info(f"📝 Actualizando campo 'Informe CrewAI' en Pipefy para case_id: {case_id}")
                        pipefy_updated = await update_pipefy_informe_crewai_field(case_id, summary_report)
                        
                        if pipefy_updated:
                            logger.info(f"✅ Campo 'Informe CrewAI' actualizado exitosamente para case_id: {case_id}")
                        else:
                            logger.warning(f"⚠️ No se pudo actualizar campo 'Informe CrewAI' para case_id: {case_id}")
                    
                    return {
                        "status": "success",
                        "crewai_response": result,
                        "supabase_saved_by_crewai": True,  # Guardado por el módulo CrewAI
                        "pipefy_updated": pipefy_updated,
                        "communication": "http_direct_sync",
                        "risk_score": analysis_result.get("risk_score"),
                        "summary_report": summary_report,
                        "architecture": "modular_separation"
                    }
                else:
                    logger.warning(f"⚠️ Respuesta CrewAI incompleta para case_id: {case_id}")
                    return {
                        "status": "partial_success",
                        "crewai_response": result,
                        "communication": "http_direct_sync"
                    }
            elif response.status_code == 502:
                logger.error(f"🛌 Servicio CrewAI está dormido (502 Bad Gateway) - Reintentando en 30 segundos...")
                
                # RETRY PARA COLD STARTS: Esperar y reintentar una vez
                await asyncio.sleep(30)
                logger.info("🔄 Reintentando llamada a CrewAI después de cold start...")
                
                async with httpx.AsyncClient(timeout=900.0) as retry_client:
                    retry_response = await retry_client.post(
                        f"{CREWAI_SERVICE_URL}/analyze/sync",
                        json=analysis_request.model_dump()
                    )
                    
                    if retry_response.status_code == 200:
                        result = retry_response.json()
                        logger.info(f"✅ Análisis CrewAI completado exitosamente en reintento para case_id: {case_id}")
                        
                        if result.get("status") == "completed" and "analysis_result" in result:
                            analysis_result = result["analysis_result"]
                            summary_report = analysis_result.get("summary_report", "")
                            
                            logger.info(f"💾 Informe guardado por módulo CrewAI en tabla informe_cadastro")
                            
                            pipefy_updated = False
                            if summary_report:
                                logger.info(f"📝 Actualizando campo 'Informe CrewAI' en Pipefy para case_id: {case_id}")
                                pipefy_updated = await update_pipefy_informe_crewai_field(case_id, summary_report)
                            
                            return {
                                "status": "success_after_retry",
                                "crewai_response": result,
                                "supabase_saved_by_crewai": True,
                                "pipefy_updated": pipefy_updated,
                                "communication": "http_direct_sync_retry",
                                "risk_score": analysis_result.get("risk_score"),
                                "summary_report": summary_report,
                                "architecture": "modular_separation",
                                "cold_start_handled": True
                            }
                    
                    logger.error(f"❌ Reintento falló: {retry_response.status_code} - {retry_response.text}")
                    return {
                        "status": "error_after_retry",
                        "error": f"CrewAI service error after retry: {retry_response.status_code}",
                        "details": retry_response.text,
                        "communication": "http_direct_sync_retry_failed"
                    }
            else:
                logger.error(f"❌ Error en servicio CrewAI: {response.status_code} - {response.text}")
                return {
                    "status": "error",
                    "error": f"CrewAI service error: {response.status_code}",
                    "details": response.text,
                    "communication": "http_direct_sync"
                }
                
    except httpx.TimeoutException:
        logger.error(f"⏰ Timeout al llamar al servicio CrewAI para case_id: {case_id}")
        logger.error("💡 Esto puede indicar que el servicio está en cold start. Considera usar el endpoint asíncrono.")
        return {
            "status": "timeout",
            "error": "CrewAI service timeout - posible cold start",
            "communication": "http_direct_sync",
            "suggestion": "El servicio puede estar dormido. Reintenta en unos minutos."
        }
    except Exception as e:
        logger.error(f"❌ Error al llamar al servicio CrewAI: {e}")
        return {
            "status": "error",
            "error": str(e),
            "communication": "http_direct_sync"
        }

# --- Endpoint Principal ---
@app.post("/webhook/pipefy")
async def handle_pipefy_webhook(request: Request, background_tasks: BackgroundTasks, x_pipefy_signature: Optional[str] = Header(None)):
    """
    Recebe webhooks do Pipefy, processa anexos, armazena no Supabase e chama CrewAI diretamente.
    VERSIÓN HTTP DIRECTA: Mantiene modularidad pero usa comunicación HTTP directa.
    """
    try:
        # Capturar el cuerpo raw sin Pydantic
        raw_body = await request.body()
        raw_body_str = raw_body.decode('utf-8', errors='ignore')
        
        # Parsear JSON manualmente
        try:
            payload_data = json.loads(raw_body_str)
        except json.JSONDecodeError as e:
            logger.error(f"ERRO: JSON inválido recebido: {e}")
            raise HTTPException(status_code=400, detail="JSON inválido")
        
        logger.info(f"📥 Webhook Pipefy recebido. Payload length: {len(raw_body_str)}")
        
        # Validar estructura básica manualmente
        if not isinstance(payload_data, dict):
            logger.error("ERRO: Payload não é um objeto JSON válido")
            raise HTTPException(status_code=400, detail="Payload deve ser um objeto JSON")
        
        data = payload_data.get('data')
        if not data or not isinstance(data, dict):
            logger.error("ERRO: Campo 'data' ausente ou inválido")
            raise HTTPException(status_code=400, detail="Campo 'data' obrigatório")
        
        card = data.get('card')
        if not card or not isinstance(card, dict):
            logger.error("ERRO: Campo 'card' ausente ou inválido")
            raise HTTPException(status_code=400, detail="Campo 'card' obrigatório")
        
        # Extrair e convertir card_id
        card_id_raw = card.get('id')
        if card_id_raw is None:
            logger.error("ERRO: Campo 'card.id' ausente")
            raise HTTPException(status_code=400, detail="Campo 'card.id' obrigatório")
        
        card_id_str = str(card_id_raw)
        logger.info(f"📋 Processando card_id: {card_id_str}")
        
        # Extraer pipe_id si está disponible
        pipe_id = None
        if 'pipe' in card and isinstance(card['pipe'], dict):
            pipe_id = card['pipe'].get('id')
            if pipe_id:
                pipe_id = str(pipe_id)
                logger.info(f"🔗 Pipe ID encontrado: {pipe_id}")
        
        # Extraer action si existe
        action = data.get('action', 'unknown')
        logger.info(f"⚡ Ação: {action}")

        # Procesar documentos anexos del card
        attachments_from_pipefy = await get_pipefy_card_attachments(card_id_str)
        processed_documents: List[Dict[str, Any]] = []

        if not attachments_from_pipefy:
            logger.info(f"📄 Nenhum anexo encontrado para o card {card_id_str}.")
        else:
            logger.info(f"📄 {len(attachments_from_pipefy)} anexos encontrados para o card {card_id_str}.")
            for att in attachments_from_pipefy:
                logger.info(f"⬇️ Processando anexo: {att.name}...")
                
                temp_file = await download_file_to_temp(att.path, att.name)
                if temp_file:
                    storage_url = await upload_to_supabase_storage_async(temp_file, card_id_str, att.name)
                    if storage_url:
                        document_tag = await determine_document_tag(att.name)
                        success_db = await register_document_in_db(card_id_str, att.name, document_tag, storage_url, pipe_id)
                        if success_db:
                            processed_documents.append({
                                "name": att.name,
                                "file_url": storage_url,
                                "document_tag": document_tag
                            })
                        else:
                            logger.warning(f"⚠️ Falha ao fazer upload do anexo '{att.name}' para Supabase Storage.")
                else:
                    logger.warning(f"⚠️ Falha ao baixar o anexo '{att.name}' do Pipefy.")
        
        logger.info(f"✅ {len(processed_documents)} documentos processados com sucesso.")

        # Obtener URL del checklist
        logger.info("🔍 Buscando URL do checklist...")
        checklist_url = await get_checklist_url_from_supabase()
        logger.info(f"📋 URL do checklist: {checklist_url}")
        
        # 🔗 LLAMADA HTTP DIRECTA A CREWAI (en background para no bloquear respuesta)
        background_tasks.add_task(
            call_crewai_analysis_service,
            card_id_str,
            processed_documents,
            checklist_url,
            pipe_id
        )

        logger.info(f"🚀 Tarea CrewAI programada en background para case_id: {card_id_str}")
        logger.info(f"📊 Resumen del procesamiento:")
        logger.info(f"   - Card ID: {card_id_str}")
        logger.info(f"   - Pipe ID: {pipe_id}")
        logger.info(f"   - Documentos procesados: {len(processed_documents)}")
        logger.info(f"   - Checklist URL: {checklist_url}")
        logger.info(f"   - Servicio CrewAI: {CREWAI_SERVICE_URL}")

        return {
            "status": "success",
            "message": f"Webhook para card {card_id_str} processado. {len(processed_documents)} documentos processados.",
            "service": "document_ingestion_service",
            "card_id": card_id_str,
            "pipe_id": pipe_id,
            "documents_processed": len(processed_documents),
            "crewai_analysis": "initiated_in_background",
            "architecture": "modular_http_direct",
            "communication": "http_direct",
            "cold_start_handling": "enabled"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ ERRO inesperado no webhook: {e}")
        import traceback
        logger.error(f"TRACEBACK: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# 🔔 WEBHOOK SUPABASE - Endpoint para recibir notificaciones de nuevos informes
@app.post('/webhook/supabase')
async def supabase_webhook(request: Request):
    """
    Webhook que recibe notificaciones de Supabase cuando se inserta un nuevo informe.
    CORREGIDO: Usa FastAPI y sintaxis correcta de updateCardField.
    """
    try:
        data = await request.json()
        logger.info(f"📨 Webhook Supabase recebido: {json.dumps(data, indent=2)}")
        
        # Verificar que es un INSERT en la tabla informe_cadastro
        if data.get('type') != 'INSERT' or data.get('table') != 'informe_cadastro':
            logger.info(f"⏭️ Webhook ignorado - Tipo: {data.get('type')}, Tabla: {data.get('table')}")
            return {"status": "ignored", "reason": "not_informe_insert"}
        
        record = data.get('record', {})
        case_id = record.get('case_id')
        informe = record.get('informe')
        status = record.get('status')
        
        if not case_id or not informe:
            logger.warning(f"⚠️ Webhook com dados incompletos - case_id: {case_id}, informe presente: {bool(informe)}")
            raise HTTPException(status_code=400, detail="case_id ou informe ausente")
        
        logger.info(f"🎯 Processando informe para case_id: {case_id}")
        logger.info(f"   - Status: {status}")
        logger.info(f"   - Tamanho do informe: {len(informe)} caracteres")
        
        # Ejecutar actualización del Pipefy de forma asíncrona
        async def update_pipefy():
            try:
                logger.info(f"🚀 Iniciando atualização do Pipefy para case_id: {case_id}")
                
                # Usar la función corregida con sintaxis oficial de Pipefy
                success = await update_pipefy_informe_crewai_field(case_id, informe)
                
                if success:
                    logger.info(f"✅ Pipefy atualizado com sucesso para case_id: {case_id}")
                else:
                    logger.error(f"❌ Falha ao atualizar Pipefy para case_id: {case_id}")
                    
            except Exception as e:
                logger.error(f"❌ Erro na atualização assíncrona do Pipefy: {e}")
        
        # Ejecutar en background
        asyncio.create_task(update_pipefy())
        
        return {
            "status": "success", 
            "message": "Webhook processado com sucesso",
            "case_id": case_id,
            "strategy": "corrected_updateCardField_syntax"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro no webhook Supabase: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 🧪 ENDPOINT DE PRUEBA - Para verificar fase del card y movimiento
@app.post("/test/check-and-move-card")
async def test_check_and_move_card(card_id: str):
    """
    Endpoint de prueba para verificar la fase actual del card y moverlo si es necesario.
    Útil para testing del nuevo sistema de manejo de fases.
    """
    try:
        logger.info(f"🧪 Test: Verificando fase y movimiento para card {card_id}")
        
        # Verificar fase actual y mover si es necesario
        phase_info = await get_card_current_phase_and_move_if_needed(card_id)
        
        if "error" in phase_info:
            raise HTTPException(
                status_code=500, 
                detail=f"Error al verificar fase del card: {phase_info}"
            )
        
        return {
            "status": "success",
            "message": f"Verificación de fase completada para card {card_id}",
            "phase_info": phase_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ ERRO en test endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# 🧪 ENDPOINT DE PRUEBA - Para probar la integración completa con movimiento de fase
@app.post("/test/update-pipefy-with-phase-handling")
async def test_update_pipefy_with_phase_handling(
    case_id: str,
    informe_content: str
):
    """
    Endpoint de prueba para actualizar el campo Informe CrewAI con manejo automático de fases.
    Incluye verificación de fase, movimiento si es necesario, y actualización del campo.
    """
    try:
        logger.info(f"🧪 Test: Actualización completa con manejo de fases para case_id {case_id}")
        
        success = await update_pipefy_informe_crewai_field(case_id, informe_content)
        
        if success:
            return {
                "status": "success",
                "message": f"Campo actualizado exitosamente con manejo de fases para case_id {case_id}",
                "case_id": case_id,
                "feature": "automatic_phase_handling"
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Error al actualizar campo con manejo de fases para case_id {case_id}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ ERRO en test endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.post("/test/update-form-field")
async def test_update_form_field(request: Request):
    """
    Endpoint de prueba para verificar la actualización de campos en formulario.
    CORREGIDO: Usa la sintaxis correcta de updateCardField de Pipefy.
    """
    try:
        data = await request.json()
        card_id = data.get('card_id')
        test_content = data.get('test_content', f'🧪 Prueba de campo en formulario - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        
        if not card_id:
            raise HTTPException(status_code=400, detail="card_id es requerido")
        
        logger.info(f"🧪 Prueba de actualización de campo en formulario para card: {card_id}")
        
        # Ejecutar actualización usando la función corregida
        success = await update_pipefy_informe_crewai_field(card_id, test_content)
        
        if success:
            return {
                "success": True,
                "card_id": card_id,
                "test_content": test_content,
                "strategy": "form_field_direct_corrected",
                "message": "Campo actualizado exitosamente con sintaxis corregida"
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail="Error al actualizar campo con sintaxis corregida"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en prueba de campo en formulario: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/")
async def root():
    return {
        "service": "Document Ingestion Service - HTTP Direct",
        "description": "Servicio modular para ingestión de documentos con comunicación HTTP directa",
        "architecture": "modular",
        "communication": "http_direct",
        "crewai_service": CREWAI_SERVICE_URL
    }

@app.get("/health")
async def health_check():
    """Endpoint de verificação de saúde con estado del servicio CrewAI."""
    
    # Verificar estado del servicio CrewAI
    crewai_status = "unknown"
    crewai_response_time = None
    
    try:
        start_time = datetime.now()
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{CREWAI_SERVICE_URL}/health")
            end_time = datetime.now()
            crewai_response_time = (end_time - start_time).total_seconds()
            
            if response.status_code == 200:
                crewai_status = "healthy"
            else:
                crewai_status = f"unhealthy_status_{response.status_code}"
    except httpx.TimeoutException:
        crewai_status = "timeout"
    except Exception as e:
        crewai_status = f"error_{str(e)[:50]}"
    
    return {
        "status": "healthy",
        "service": "document_ingestion_service",
        "supabase_configured": bool(SUPABASE_URL and SUPABASE_SERVICE_KEY),
        "pipefy_configured": bool(PIPEFY_TOKEN),
        "storage_bucket": SUPABASE_STORAGE_BUCKET_NAME,
        "crewai_service": CREWAI_SERVICE_URL,
        "crewai_status": crewai_status,
        "crewai_response_time_seconds": crewai_response_time,
        "architecture": "modular_http_direct",
        "communication": "http_direct",
        "cold_start_handling": "enabled"
    }

# 🧪 Función para detectar la fase actual del card y moverlo si es necesario
# NOTA: Mantenida para compatibilidad, pero no necesaria con la nueva estrategia
async def get_card_current_phase_and_move_if_needed(card_id: str) -> Dict[str, Any]:
    """
    Detecta la fase actual del card y lo mueve a la fase de destino si es necesario.
    OBSOLETA: No necesaria con campos en formulario, pero mantenida para compatibilidad.
    """
    # Función mantenida para compatibilidad pero no usada en la nueva estrategia
    return {"status": "not_needed", "message": "Campo en formulario - no requiere movimiento de fase"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)