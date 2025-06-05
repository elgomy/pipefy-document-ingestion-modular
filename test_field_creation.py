#!/usr/bin/env python3
"""
Script de prueba para verificar la creación automática de campos en Pipefy.
"""

import requests
import json
import os
from datetime import datetime

# Configuración
BASE_URL = os.getenv('INGESTION_SERVICE_URL', 'http://localhost:8000')

def test_field_creation(card_id, test_content=None):
    """
    Prueba la creación automática de campos.
    
    Args:
        card_id (str): ID del card para probar
        test_content (str): Contenido de prueba opcional
    """
    if not test_content:
        test_content = f"🧪 Prueba de creación automática - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    print(f"🚀 Iniciando prueba de creación automática de campo")
    print(f"   - Card ID: {card_id}")
    print(f"   - Contenido: {test_content[:50]}...")
    print(f"   - URL: {BASE_URL}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/test/create-field-auto",
            json={
                "card_id": card_id,
                "test_content": test_content
            },
            timeout=30
        )
        
        print(f"\n📊 Respuesta HTTP: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            result = data.get('test_result', {})
            
            print("✅ Prueba exitosa!")
            print(f"   - Campo creado: {'Sí' if result.get('field_created') else 'No'}")
            print(f"   - Field ID: {result.get('field_id')}")
            print(f"   - Fase: {result.get('phase_id')}")
            print(f"   - Mensaje: {result.get('message')}")
            
            return True
        else:
            print(f"❌ Error en la prueba: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   - Error: {error_data.get('error', 'Error desconocido')}")
            except:
                print(f"   - Respuesta: {response.text}")
            
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Timeout - El servicio puede estar en cold start")
        return False
    except requests.exceptions.ConnectionError:
        print("🔌 Error de conexión - Verificar que el servicio esté ejecutándose")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return False

def main():
    """Función principal del script."""
    print("🔧 Script de Prueba - Creación Automática de Campos")
    print("=" * 60)
    
    # Solicitar card_id al usuario
    card_id = input("Ingresa el Card ID para probar: ").strip()
    
    if not card_id:
        print("❌ Card ID es requerido")
        return
    
    # Contenido de prueba opcional
    custom_content = input("Contenido personalizado (Enter para usar por defecto): ").strip()
    
    # Ejecutar prueba
    success = test_field_creation(card_id, custom_content if custom_content else None)
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Prueba completada exitosamente!")
    else:
        print("💥 Prueba falló - Revisar logs del servicio")

if __name__ == "__main__":
    main() 