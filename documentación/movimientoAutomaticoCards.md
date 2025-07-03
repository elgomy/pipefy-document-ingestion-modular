# Sistema de Movimiento Automático de Cards en Pipefy

## 📋 Descripción General

Este documento explica el sistema completo de movimiento automático de cards en Pipefy, que se basa en el análisis de documentos por parte de CrewAI para determinar automáticamente a qué fase debe moverse cada card según su estado de documentación.

## 🔄 Flujo General del Sistema

```
Webhook Pipefy → Análisis CrewAI → Decisión Automática → Movimiento de Card → Notificaciones
```

---

## 🏗️ **ARQUITECTURA DEL SISTEMA**

### **Componentes Principales:**

1. **Análisis de Documentos** - CrewAI evalúa la documentación
2. **Motor de Decisiones** - Determina la fase destino según el análisis
3. **Cliente Pipefy** - Ejecuta el movimiento físico del card
4. **Sistema de Notificaciones** - Informa sobre pendencias críticas

---

## 1️⃣ **FUNCIÓN PRINCIPAL: `handle_crewai_analysis_result()`**

**📍 Ubicación:** Líneas 1449-1835 en `app.py`

**🎯 Propósito:** Orquestador principal que procesa el resultado del análisis CrewAI y ejecuta las acciones correspondientes.

### 📊 **Lógica de Decisión:**

#### **Estados Posibles del Análisis:**
- **`Aprovado`** → Mueve a fase "Aprovado"
- **`Pendencia_Bloqueante`** → Mueve a fase "Pendências Documentais" + Notificación WhatsApp
- **`Pendencia_NaoBloqueante`** → Mueve a fase "Emitir Documentos"

#### **Mapeo de Fases (definido en settings.py):**
```python
PHASE_ID_APROVADO = "338000018"        # Fase: Aprovado
PHASE_ID_PENDENCIAS = "338000019"      # Fase: Pendências Documentais  
PHASE_ID_EMITIR_DOCS = "338000021"     # Fase: Emitir Documentos
```

### 🔍 **Detección Automática de CNPJ:**

El sistema detecta automáticamente si se necesita generar un Cartão CNPJ:

#### **Patrones de Detección:**
```python
cnpj_patterns = [
    r'cartão\s+cnpj', r'carta\s+cnpj', r'documento\s+cnpj', 
    r'comprovante\s+cnpj', r'consulta\s+cnpj', r'certidão\s+cnpj',
    r'documento.*receita.*federal', r'rfb', r'cnpja'
]
```

#### **Formatos de CNPJ Reconocidos:**
```python
cnpj_patterns_flexible = [
    r'\b\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[\/\s]?\d{4}[\-\s]?\d{2}\b',  # 11.222.333/0001-81
    r'\b\d{14}\b',  # 11222333000181
    r'CNPJ[:\s]*\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[\/\s]?\d{4}[\-\s]?\d{2}',  # CNPJ: 11.222.333/0001-81
    r'CNPJ[:\s]*\d{14}',  # CNPJ: 11222333000181
]
```

### 📝 **Proceso Paso a Paso:**

1. **Extraer datos del análisis CrewAI**
2. **Generar relatório detalhado en Markdown**
3. **Detectar necesidad de Cartão CNPJ**
4. **Actualizar campo "Informe CrewAI" en Pipefy**
5. **Ejecutar acciones según el status_geral**
6. **Mover card a la fase correspondiente**
7. **Enviar notificaciones si es necesario**

---

## 2️⃣ **CLIENTE PIPEFY: `PipefyClient`**

**📍 Ubicación:** `src/integrations/pipefy_client.py`

### **Función: `move_card_to_phase()`** (Líneas 30-113)

**🎯 Propósito:** Mueve un card específico a una fase determinada usando GraphQL.

#### **GraphQL Mutation:**
```graphql
mutation MoveCardToPhase($cardId: ID!, $phaseId: ID!) {
  moveCardToPhase(input: {card_id: $cardId, destination_phase_id: $phaseId}) {
    card {
      id
      title
      current_phase {
        id
        name
      }
      updated_at
    }
  }
}
```

#### **Parámetros:**
- `card_id: str` - ID del card a mover
- `phase_id: str` - ID de la fase destino

#### **Manejo de Errores:**
- ✅ **Errores GraphQL:** Captura y reporta errores específicos de la API
- ✅ **Errores HTTP:** Maneja códigos de estado HTTP
- ✅ **Timeouts:** Configurado con timeout de 30 segundos
- ✅ **Restricciones de Fase:** Detecta errores de transición no permitida

#### **Retorna:**
```python
{
    "success": True,
    "card_id": "1131156124",
    "new_phase_id": "338000018",
    "new_phase_name": "Aprovado",
    "updated_at": "2025-01-26T15:30:00Z"
}
```

### **Función: `move_card_by_classification()`** (Líneas 266-302)

**🎯 Propósito:** Mueve un card según la clasificación de la IA automáticamente.

#### **Mapeo de Clasificaciones:**
```python
phase_mapping = {
    "Aprovado": settings.PHASE_ID_APROVADO,           # "338000018"
    "Pendencia_Bloqueante": settings.PHASE_ID_PENDENCIAS,    # "338000019"
    "Pendencia_NaoBloqueante": settings.PHASE_ID_EMITIR_DOCS # "338000021"
}
```

#### **Proceso:**
1. **Validar clasificación** - Verifica que sea una clasificación válida
2. **Mapear a fase** - Obtiene el ID de fase correspondiente
3. **Ejecutar movimiento** - Llama a `move_card_to_phase()`
4. **Retornar resultado** - Incluye la clasificación en la respuesta

---

## 3️⃣ **FUNCIÓN DE MOVIMIENTO DIRECTO: `move_pipefy_card_to_phase()`**

**📍 Ubicación:** Líneas 1061-1160 en `app.py`

**🎯 Propósito:** Función de nivel de aplicación que maneja el movimiento con diagnóstico completo.

### 📊 **Características Especiales:**

#### **Diagnóstico Pre-Movimiento:**
```python
# Obtener información de la fase actual
current_phase_info = await get_card_current_phase_info(card_id)
logger.info(f"📍 Fase ACTUAL: {current_phase_info.get('name')} (ID: {current_phase_info.get('id')})")
logger.info(f"📍 Fase DESTINO: {phase_id}")

# Verificar si ya está en la fase destino
if current_phase_info.get('id') == phase_id:
    logger.info(f"✅ Card ya está en la fase destino {phase_id}")
    return True
```

#### **GraphQL Mutation Simplificada:**
```python
mutation = f"""
mutation {{
    moveCardToPhase(input: {{
        card_id: {card_id}
        destination_phase_id: {phase_id}
    }}) {{
        card {{
            id
            current_phase {{
                id
                name
            }}
        }}
    }}
}}
"""
```

#### **Manejo de Errores Específicos:**
- **Restricciones de Fase:** Detecta cuando una fase no permite el movimiento
- **Errores de Autenticación:** Verifica token de Pipefy
- **Errores de Configuración:** Valida variables de entorno

---

## 4️⃣ **SERVICIO PIPEFY: `PipefyService`**

**📍 Ubicación:** `src/services/pipefy_service.py`

### **Función: `process_card_classification()`** (Líneas 40-60)

**🎯 Propósito:** Procesa la clasificación de un card y ejecuta las acciones correspondientes.

#### **Proceso:**
```python
# 1. Mover card a la fase correspondiente
move_result = await self.client.move_card_by_classification(card_id, classification)

# 2. Registrar operación
operation = {
    "type": "move_card",
    "classification": classification,
    "result": move_result,
    "timestamp": datetime.now().isoformat()
}
```

### **Función: `move_card_to_phase()`** (Líneas 103-120)

**🎯 Propósito:** Wrapper del servicio para movimiento directo de cards.

---

## 5️⃣ **FLUJO COMPLETO DE MOVIMIENTO AUTOMÁTICO**

### **Ejemplo Práctico: Card con Pendencia Bloqueante**

```python
# 1. Webhook recibe movimiento a fase "Triagem Documentos AI"
card_id = "1131156124"
phase_id = "338000020"  # Triagem Documentos AI

# 2. Sistema descarga archivos adjuntos
attachments = await get_pipefy_card_attachments(card_id)
# Resultado: ["ContratoSocial.pdf"]

# 3. CrewAI analiza documentos
crew_response = await call_crewai_analysis_service(card_id, documents, checklist_url)
# Resultado: {"status_geral": "Pendencia_Bloqueante", "pendencias": [...]}

# 4. Sistema determina acciones automáticas
if crew_response["status_geral"] == "Pendencia_Bloqueante":
    # 4a. Detectar necesidad de Cartão CNPJ
    cnpj = extract_cnpj_from_analysis(crew_response)
    if cnpj:
        await gerar_e_armazenar_cartao_cnpj(card_id, cnpj)
    
    # 4b. Mover a fase "Pendências Documentais"
    await move_pipefy_card_to_phase(card_id, "338000019")
    
    # 4c. Enviar notificação WhatsApp
    await send_whatsapp_notification(card_id, relatorio_detalhado)

# 5. Actualizar campo "Informe CrewAI"
await update_pipefy_informe_crewai_field(card_id, relatorio_detalhado)
```

---

## 6️⃣ **CONFIGURACIÓN DE FASES**

### **IDs de Fases del Sistema:**
```python
# Definidos en src/config/settings.py
PHASE_ID_TRIAGEM = "338000020"      # Triagem Documentos AI (entrada)
PHASE_ID_APROVADO = "338000018"     # Aprovado (éxito)
PHASE_ID_PENDENCIAS = "338000019"   # Pendências Documentais (bloqueante)
PHASE_ID_EMITIR_DOCS = "338000021"  # Emitir Documentos (no bloqueante)
```

### **Flujo de Fases:**
```
┌─────────────────────┐
│ Triagem Documentos  │ ← Entrada (webhook trigger)
│ AI (338000020)      │
└─────────┬───────────┘
          │
          ▼ (Análisis CrewAI)
          │
    ┌─────┴──────┐
    │  Decisión  │
    │ Automática │
    └─────┬──────┘
          │
     ┌────┴────┬────────────┬──────────────┐
     │         │            │              │
     ▼         ▼            ▼              ▼
┌─────────┐ ┌──────────┐ ┌──────────────┐ ┌────────────┐
│Aprovado │ │Pendências│ │Emitir        │ │   Error    │
│(338018) │ │(338019)  │ │Documentos    │ │ (manual)   │
│         │ │+ WhatsApp│ │(338021)      │ │            │
└─────────┘ └──────────┘ └──────────────┘ └────────────┘
```

---

## 7️⃣ **LOGS TÍPICOS DEL SISTEMA**

### **Movimiento Exitoso:**
```
INFO:app:🎯 Processando resultado CrewAI para card 1131156124
INFO:app:📊 Status Geral: Pendencia_Bloqueante
INFO:app:🔍 Buscando CNPJ no texto: Necessário apresentar cartão CNPJ...
INFO:app:🎯 CNPJ encontrado automaticamente: 11222333000181
INFO:app:➕ Adicionando ação de Cartão CNPJ para CNPJ: 11222333000181
INFO:app:🏢 Gerando Cartão CNPJ para CNPJ: 11222333000181
INFO:app:✅ Cartão CNPJ gerado e armazenado automaticamente
INFO:app:🔄 Movendo card 1131156124 para fase Pendências Documentais (338000019)
INFO:app:✅ Card 1131156124 movido exitosamente!
INFO:app:📞 Enviando notificação WhatsApp para gestor
INFO:app:✅ Notificação WhatsApp enviada com sucesso
```

### **Error de Movimiento:**
```
ERROR:app:❌ Erro GraphQL ao mover card 1131156124: [{'message': 'Cannot move card to this phase', 'extensions': {'code': 'PHASE_TRANSITION_ERROR'}}]
ERROR:app:🚨 FASE RESTRICTION ERROR: La fase destino 338000019 no permite el movimiento desde la fase actual
ERROR:app:💡 SOLUCIÓN: Verificar 'Move card settings' en la UI de Pipefy para esta fase
```

---

## 8️⃣ **CARACTERÍSTICAS TÉCNICAS**

### **Robustez:**
- ✅ **Verificación previa** - Comprueba si el card ya está en la fase destino
- ✅ **Manejo de errores** - Captura y reporta errores específicos
- ✅ **Logs detallados** - Información completa para debugging
- ✅ **Timeouts configurados** - Evita bloqueos indefinidos
- ✅ **Validación de permisos** - Verifica restricciones de fase

### **Inteligencia:**
- ✅ **Detección automática de CNPJ** - Múltiples patrones de reconocimiento
- ✅ **Clasificación inteligente** - Basada en análisis de IA
- ✅ **Acciones contextuales** - Genera documentos según necesidad
- ✅ **Notificaciones selectivas** - Solo para pendencias críticas

### **Escalabilidad:**
- ✅ **Procesamiento asíncrono** - No bloquea otros procesos
- ✅ **Cliente reutilizable** - Instancia global del cliente Pipefy
- ✅ **Configuración centralizada** - IDs de fase en settings
- ✅ **Arquitectura modular** - Separación clara de responsabilidades

---

## 9️⃣ **ENDPOINTS DE TESTING**

### **Test de Movimiento Manual:**
```
POST /debug/test-move-card
{
    "card_id": "1131156124",
    "phase_id": "338000018"
}
```

### **Test de Clasificación:**
```
POST /test/check-and-move-card?card_id=1131156124
```

### **Test de Orquestador:**
```
POST /test/orchestrator
{
    "card_id": "1131156124",
    "crew_response": {
        "status_geral": "Pendencia_Bloqueante",
        "pendencias": [...]
    }
}
```

---

## 🎯 **PUNTOS CLAVE DEL SISTEMA**

1. **Completamente Automático** - No requiere intervención manual
2. **Inteligente** - Basado en análisis de IA de documentos
3. **Robusto** - Manejo completo de errores y edge cases
4. **Trazable** - Logs detallados de cada operación
5. **Configurable** - Fases y comportamientos ajustables
6. **Escalable** - Arquitectura preparada para crecimiento
7. **Integrado** - Funciona seamlessly with webhook of Pipefy

El sistema garantiza que cada card se mueva automáticamente a la fase correcta según el estado real de su documentación, optimizando el flujo de trabajo y reduciendo la intervención manual. 