#!/usr/bin/env python3
"""
Script de prueba para verificar la sintaxis correcta de updateCardField de Pipefy.
Usa la sintaxis oficial según la documentación de Pipefy.
"""

import os
import asyncio
import httpx
import json
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

PIPEFY_TOKEN = os.getenv("PIPEFY_TOKEN")

async def test_get_card_fields(card_id: str):
    """Obtiene todos los campos de un card para verificar estructura."""
    
    query = """
    query GetCardFields($cardId: ID!) {
        card(id: $cardId) {
            id
            title
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
                print(f"❌ Error GraphQL: {data['errors']}")
                return None
            
            card_data = data.get("data", {}).get("card")
            if not card_data:
                print(f"❌ Card {card_id} no encontrado")
                return None
            
            print(f"✅ Card encontrado: {card_data.get('title')}")
            print(f"📋 Campos disponibles:")
            
            fields = card_data.get("fields", [])
            informe_field = None
            
            for field in fields:
                field_info = field.get("field", {})
                field_label = field_info.get("label", "")
                field_name = field.get("name", "")
                field_id = field_info.get("id")
                field_type = field_info.get("type")
                
                print(f"   - '{field_name}' (Label: '{field_label}', ID: {field_id}, Type: {field_type})")
                
                # Buscar campo "Informe CrewAI"
                if "informe crewai" in field_label.lower() or "informe crewai" in field_name.lower():
                    informe_field = field_id
                    print(f"   🎯 CAMPO ENCONTRADO: {field_id}")
            
            return informe_field
            
    except Exception as e:
        print(f"❌ Error al obtener campos: {e}")
        return None

async def test_update_card_field_official_syntax(card_id: str, field_id: str, test_content: str):
    """Prueba la sintaxis oficial de updateCardField según documentación de Pipefy."""
    
    # SINTAXIS OFICIAL según documentación de Pipefy
    mutation = """
    mutation {
        updateCardField(input: {card_id: %s, field_id: "%s", new_value: "%s"}) {
            card {
                id
                title
            }
        }
    }
    """ % (card_id, field_id, test_content.replace('"', '\\"').replace('\n', '\\n'))
    
    headers = {
        "Authorization": f"Bearer {PIPEFY_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": mutation
    }
    
    try:
        print(f"🚀 Probando sintaxis oficial de updateCardField...")
        print(f"   - Card ID: {card_id}")
        print(f"   - Field ID: {field_id}")
        print(f"   - Contenido: {test_content[:50]}...")
        
        async with httpx.AsyncClient() as client:
            response = await client.post("https://api.pipefy.com/graphql", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            print(f"📨 Respuesta de Pipefy:")
            print(json.dumps(data, indent=2))
            
            if "errors" in data:
                print(f"❌ Error GraphQL: {data['errors']}")
                return False
            
            result = data.get("data", {}).get("updateCardField", {})
            card_info = result.get("card", {})
            
            if card_info and card_info.get("id"):
                print(f"✅ Campo actualizado exitosamente!")
                print(f"   - Card ID: {card_info.get('id')}")
                print(f"   - Card Title: {card_info.get('title')}")
                return True
            else:
                print(f"❌ Respuesta inesperada: {result}")
                return False
                
    except Exception as e:
        print(f"❌ Error al actualizar campo: {e}")
        return False

async def main():
    """Función principal de prueba."""
    
    if not PIPEFY_TOKEN:
        print("❌ Error: PIPEFY_TOKEN no configurado")
        return
    
    # Solicitar card_id al usuario
    card_id = input("🔢 Ingresa el Card ID para probar: ").strip()
    
    if not card_id:
        print("❌ Card ID es requerido")
        return
    
    print(f"\n🧪 INICIANDO PRUEBA DE SINTAXIS OFICIAL DE PIPEFY")
    print(f"=" * 60)
    
    # PASO 1: Obtener campos del card
    print(f"\n📋 PASO 1: Obteniendo campos del card {card_id}")
    field_id = await test_get_card_fields(card_id)
    
    if not field_id:
        print(f"❌ No se encontró el campo 'Informe CrewAI' en el card {card_id}")
        print(f"💡 Asegúrate de que el campo existe en el formulario del card")
        return
    
    # PASO 2: Probar actualización con sintaxis oficial
    print(f"\n📝 PASO 2: Probando actualización con sintaxis oficial")
    test_content = f"🧪 Prueba de sintaxis oficial - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    success = await test_update_card_field_official_syntax(card_id, field_id, test_content)
    
    # RESULTADO FINAL
    print(f"\n🎯 RESULTADO FINAL")
    print(f"=" * 60)
    
    if success:
        print(f"✅ ÉXITO: La sintaxis oficial de Pipefy funciona correctamente!")
        print(f"✅ Campo 'Informe CrewAI' actualizado exitosamente")
        print(f"✅ El problema estaba en la sintaxis de la mutación GraphQL")
    else:
        print(f"❌ FALLO: Aún hay problemas con la actualización")
        print(f"❌ Revisar logs para más detalles")

if __name__ == "__main__":
    asyncio.run(main()) 