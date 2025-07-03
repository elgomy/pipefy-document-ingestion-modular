# Flujo de Descarga de Archivos Adjuntos: Pipefy → Supabase

## 📋 Descripción General

Este documento explica el proceso completo de descarga de archivos adjuntos desde cards de Pipefy hacia el almacenamiento de Supabase, incluyendo el registro en la base de datos.

## 🔄 Flujo General

```
Pipefy Card → Obtener URLs → Descargar → Subir a Supabase → Registrar en DB
```

---

## 1️⃣ **FUNCIÓN: `get_pipefy_card_attachments()`**

**📍 Ubicación:** Líneas 564-645 en `app.py`

**🎯 Propósito:** Obtiene las URLs de los archivos adjuntos desde Pipefy usando GraphQL.

### 📊 Proceso paso a paso:

#### **Query GraphQL:**
```graphql
query GetCardAttachments($cardId: ID!) {
    card(id: $cardId) {
        id
        title
        attachments {
            id
            name
            url
            downloadUrl
        }
    }
}
```

#### **Parámetros de entrada:**
- `card_id: str` - ID del card de Pipefy

#### **Retorna:**
- `List[PipefyAttachment]` - Lista de objetos con información de archivos adjuntos

#### **Estructura del objeto PipefyAttachment:**
```python
@dataclass
class PipefyAttachment:
    id: str           # ID único del archivo en Pipefy
    name: str         # Nombre del archivo (ej: "documento.pdf")
    url: str          # URL de visualización
    download_url: str # URL de descarga directa
```

#### **Manejo de errores:**
- ✅ **Sin archivos adjuntos:** Retorna lista vacía
- ❌ **Error de API:** Lanza excepción con detalles del error
- ⚠️ **Timeout:** Configurado con timeout de 30 segundos

---

## 2️⃣ **FUNCIÓN: `download_file_from_url()`**

**📍 Ubicación:** Líneas 646-670 en `app.py`

**🎯 Propósito:** Descarga un archivo desde una URL y lo guarda temporalmente.

### 📊 Proceso paso a paso:

#### **Parámetros de entrada:**
- `url: str` - URL de descarga del archivo
- `filename: str` - Nombre del archivo para guardar

#### **Proceso interno:**
1. **Crear archivo temporal:** Usa `tempfile.NamedTemporaryFile(delete=False)`
2. **Descarga streaming:** Descarga por chunks para archivos grandes
3. **Validación:** Verifica que el archivo se descargó correctamente
4. **Logging:** Registra el progreso y ubicación del archivo

#### **Retorna:**
- `str` - Ruta del archivo temporal descargado

#### **Ejemplo de uso:**
```python
temp_file_path = await download_file_from_url(
    url="https://app.pipefy.com/storage/...",
    filename="documento.pdf"
)
```

---

## 3️⃣ **FUNCIÓN: `process_attachments()`**

**📍 Ubicación:** Líneas 1940-1980 en `app.py`

**🎯 Propósito:** Coordina todo el proceso de descarga y almacenamiento.

### 📊 Proceso completo:

#### **1. Obtener archivos adjuntos:**
```python
attachments = await get_pipefy_card_attachments(card_id)
logger.info(f"📄 {len(attachments)} anexos encontrados para o card {card_id}.")
```

#### **2. Procesar cada archivo:**
```python
for attachment in attachments:
    logger.info(f"⬇️ Processando anexo: {attachment.name}...")
    
    # Descargar archivo
    temp_file_path = await download_file_from_url(
        attachment.download_url, 
        attachment.name
    )
    
    # Subir a Supabase Storage
    public_url = await upload_to_supabase_storage(
        temp_file_path, 
        card_id, 
        attachment.name
    )
    
    # Registrar en base de datos
    await register_document_in_db(
        card_id, 
        attachment.name, 
        public_url
    )
```

#### **3. Limpieza:**
- Elimina archivos temporales
- Libera memoria
- Registra estadísticas finales

---

## 4️⃣ **FUNCIÓN: `upload_to_supabase_storage()`**

**🎯 Propósito:** Sube el archivo descargado al almacenamiento de Supabase.

### 📊 Proceso:

#### **Estructura de carpetas en Supabase:**
```
bucket: documents/
├── {card_id}/
│   ├── archivo1.pdf
│   ├── archivo2.jpg
│   └── archivo3.docx
```

#### **Parámetros:**
- `file_path: str` - Ruta del archivo temporal
- `card_id: str` - ID del card (usado como carpeta)
- `filename: str` - Nombre del archivo

#### **Proceso interno:**
1. **Leer archivo:** Carga el contenido en memoria
2. **Definir ruta:** `{card_id}/{filename}`
3. **Subir archivo:** Usa cliente Supabase Storage
4. **Generar URL pública:** Para acceso posterior

#### **Retorna:**
- `str` - URL pública del archivo en Supabase

---

## 5️⃣ **FUNCIÓN: `register_document_in_db()`**

**🎯 Propósito:** Registra la información del documento en la tabla `documents`.

### 📊 Estructura de la tabla `documents`:

```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    case_id TEXT NOT NULL,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    uploaded_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(case_id, name)  -- Evita duplicados
);
```

#### **Datos registrados:**
- `case_id` - ID del card de Pipefy
- `name` - Nombre original del archivo
- `url` - URL pública en Supabase Storage
- `uploaded_at` - Timestamp automático

#### **Manejo de duplicados:**
- Usa `on_conflict=case_id, name` para actualizar si ya existe
- Evita duplicar archivos del mismo card

---

## 🚀 **Flujo Completo en Acción**

### **Ejemplo práctico:**

```python
# 1. Webhook recibe card_id = "1131156124"
card_id = "1131156124"

# 2. Obtener archivos adjuntos
attachments = await get_pipefy_card_attachments(card_id)
# Resultado: [PipefyAttachment(name="ContratoSocial.pdf", ...)]

# 3. Descargar cada archivo
for attachment in attachments:
    # Descarga: https://app.pipefy.com/storage/.../ContratoSocial.pdf
    temp_path = await download_file_from_url(attachment.download_url, attachment.name)
    # Resultado: /tmp/tmpXXXXXX_ContratoSocial.pdf
    
    # Subir a Supabase: documents/1131156124/ContratoSocial.pdf
    public_url = await upload_to_supabase_storage(temp_path, card_id, attachment.name)
    # Resultado: https://aguoqgqbdbyipztgrmbd.supabase.co/storage/v1/object/public/documents/1131156124/ContratoSocial.pdf
    
    # Registrar en DB
    await register_document_in_db(card_id, attachment.name, public_url)
    
    # Limpiar archivo temporal
    os.unlink(temp_path)
```

---

## 🔍 **Características Técnicas**

### **Seguridad:**
- ✅ URLs firmadas de Pipefy con expiración
- ✅ Validación de tipos de archivo
- ✅ Manejo seguro de archivos temporales

### **Rendimiento:**
- ✅ Descarga por chunks para archivos grandes
- ✅ Procesamiento asíncrono
- ✅ Limpieza automática de archivos temporales

### **Robustez:**
- ✅ Manejo de errores en cada paso
- ✅ Logs detallados para debugging
- ✅ Timeouts configurados
- ✅ Prevención de duplicados

### **Escalabilidad:**
- ✅ Estructura de carpetas organizada por card_id
- ✅ URLs públicas para acceso directo
- ✅ Base de datos normalizada

---

## 📊 **Logs Típicos del Proceso**

```
INFO:app:📄 1 anexos encontrados para o card 1131156124.
INFO:app:⬇️ Processando anexo: ContratoSocial.pdf...
INFO:app:INFO: Arquivo 'ContratoSocial.pdf' baixado para: /tmp/tmpXXXXXX_ContratoSocial.pdf
INFO:app:INFO: Upload concluído para 'ContratoSocial.pdf'. URL: https://aguoqgqbdbyipztgrmbd.supabase.co/storage/v1/object/public/documents/1131156124/ContratoSocial.pdf
INFO:app:INFO: Documento 'ContratoSocial.pdf' registrado/atualizado no DB para case_id '1131156124'.
INFO:app:✅ 1 documentos processados com sucesso.
```

---

## 🎯 **Puntos Clave**

1. **Proceso completamente asíncrono** - No bloquea otros requests
2. **Manejo robusto de errores** - Cada paso está protegido
3. **Organización clara** - Archivos organizados por card_id
4. **Prevención de duplicados** - Constraint único en DB
5. **URLs públicas** - Acceso directo sin autenticación adicional
6. **Limpieza automática** - No deja archivos temporales 