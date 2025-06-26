# Solución de Problemas: CNPJ y WhatsApp

## 📋 Resumen de Problemas Identificados

### 1. ❌ Cartão CNPJ no se genera
**Problema:** El agente de CrewAI no puede extraer CNPJ de los documentos porque no puede acceder a ellos.

### 2. ❌ WhatsApp se envía pero no llega
**Problema:** Twilio confirma envío exitoso pero el mensaje no llega al dispositivo.

---

## 🔧 Soluciones Implementadas

### ✅ Problema A: Normalización de CNPJ
**Estado:** SOLUCIONADO
- Función `normalize_cnpj()` implementada
- Transforma `51.441.685/0001-41` → `51441685000141`
- Aplicada en todas las funciones relevantes
- Logs adicionales para debug

### ✅ Problema B: Número WhatsApp
**Estado:** SOLUCIONADO 
- Cambiado de `+5531999999999` a `+5531999034444`
- Número actualizado en función `get_manager_phone_for_card()`

### ✅ Problema C: URLs de servicios
**Estado:** SOLUCIONADO
- Corregida URL en CrewAI: `pipefy-document-ingestion-modular.onrender.com`
- Endpoints ahora accesibles entre servicios

### ✅ Problema D: Formato de respuesta
**Estado:** SOLUCIONADO
- Agregado campo `success` a endpoint `/api/v1/documentos/{case_id}`
- Herramientas CrewAI ahora pueden procesar respuestas correctamente

---

## 🔍 Problemas Pendientes

### 🚨 1. Extracción de CNPJ de Documentos

**Problema:** El agente no puede extraer CNPJ del contenido de los PDFs porque:
- Las herramientas de CrewAI no pueden leer el contenido de los PDFs directamente
- Solo tienen acceso a metadatos (nombre, URL, tag)

**Soluciones Posibles:**

#### Opción A: OCR en el Backend ⭐ (RECOMENDADA)
```python
# Implementar en el servicio de ingestión
def extract_cnpj_from_pdf_content(pdf_url: str) -> Optional[str]:
    """
    Descargar PDF, extraer texto con OCR, buscar CNPJ
    """
    # 1. Descargar PDF desde URL
    # 2. Usar PyPDF2 o pdfplumber para extraer texto
    # 3. Aplicar regex para encontrar CNPJ
    # 4. Normalizar con normalize_cnpj()
    pass
```

#### Opción B: Análisis en el Procesamiento
```python
# Durante el procesamiento de documentos en handle_pipefy_webhook
async def process_document_and_extract_cnpj(case_id: str, pdf_path: str):
    """
    Extraer CNPJ durante el procesamiento inicial
    """
    # 1. Extraer texto del PDF
    # 2. Buscar CNPJ con regex
    # 3. Guardar en tabla documents con campo cnpj_extraido
    # 4. Usar en análisis posterior
    pass
```

### 🚨 2. WhatsApp No Llega al Dispositivo

**Problema:** Twilio confirma envío (Status 201) pero mensaje no llega.

**Diagnóstico:** Ejecutar script de debug:
```bash
cd pipefy-document-ingestion-v2
python test_whatsapp_debug.py
```

**Causas Probables:**

#### A. Número no verificado en Twilio Sandbox
- **Solución:** Agregar `+5531999034444` a números verificados en Twilio Console
- **URL:** https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn

#### B. Número no registrado en WhatsApp
- **Solución:** Verificar que el número tenga WhatsApp activo
- **Test:** Enviar mensaje manual al número

#### C. Políticas de WhatsApp Business
- **Problema:** Mensajes automatizados pueden ser bloqueados
- **Solución:** Usar templates pre-aprobados o cuenta verificada

#### D. Configuración de Sandbox
```bash
# Verificar configuración en .env
TWILIO_ACCOUNT_SID=AC2adada...
TWILIO_AUTH_TOKEN=7372b2d2...
TWILIO_WHATSAPP_NUMBER=+14155238886
```

---

## 🛠️ Acciones Inmediatas Requeridas

### 1. Para Solucionar CNPJ
```bash
# Opción A: Implementar OCR en backend
# Agregar dependencias
pip install PyPDF2 pdfplumber

# Implementar función extract_cnpj_from_pdf_content()
# Llamar durante procesamiento de documentos
```

### 2. Para Solucionar WhatsApp
```bash
# Ejecutar diagnóstico
cd pipefy-document-ingestion-v2
python test_whatsapp_debug.py

# Verificar en Twilio Console:
# 1. Agregar +5531999034444 a números verificados
# 2. Verificar status de mensajes enviados
# 3. Revisar logs de entrega
```

### 3. Verificar Despliegue
```bash
# Los servicios deben redesplegarse automáticamente
# Verificar que estén usando las nuevas versiones:

curl https://pipefy-document-ingestion-modular.onrender.com/health
curl https://pipefy-crewai-analysis-v2.onrender.com/health
```

---

## 📊 Estado Actual del Flujo

### ✅ Funcionando Correctamente:
1. Webhook Pipefy → Procesamiento documentos
2. Análisis CrewAI → Generación de informes
3. Guardado en Supabase → Campo Pipefy actualizado
4. Movimiento de cards → Fase correcta
5. Normalización CNPJ → Formato API correcto

### ⚠️ Necesita Atención:
1. **Extracción CNPJ de PDFs** → Implementar OCR
2. **Entrega WhatsApp** → Verificar configuración Twilio
3. **Generación Cartão CNPJ** → Depende de extracción CNPJ

---

## 🔄 Próximos Pasos

1. **Implementar extracción CNPJ con OCR** (Prioridad Alta)
2. **Verificar configuración WhatsApp en Twilio** (Prioridad Alta)
3. **Probar flujo completo** con documento que contenga CNPJ visible
4. **Monitorear logs** para confirmar funcionamiento

---

## 📞 Contacto y Soporte

Si necesitas ayuda adicional:
1. Revisar logs de Render para ambos servicios
2. Ejecutar script `test_whatsapp_debug.py`
3. Verificar configuración en Twilio Console
4. Comprobar que variables de entorno estén correctas

**Todos los cambios han sido desplegados automáticamente en Render.**

---

## 🚨 **CORRECCIÓN IMPORTANTE**

**URLs Correctas:**
- ✅ CrewAI: `https://pipefy-crewai-analysis-modular.onrender.com`
- ✅ Ingestión: `https://pipefy-document-ingestion-modular.onrender.com`

**Error Anterior:** Se había cambiado incorrectamente a URLs con sufijo `-v2`. 
**Estado:** Corregido a las URLs correctas con sufijo `-modular`. 🚀 