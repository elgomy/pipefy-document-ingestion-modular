#!/usr/bin/env python3
"""
Script Maestro - Tests End-to-End
Document Triaging Agent v2.0 - Arquitectura Modular Híbrida

Este script ejecuta todos los tests de integración E2E para validar
la comunicación entre los dos servicios independientes.

Estructura de Tests:
1. Tests E2E Generales (test_e2e_integration.py)
2. Tests Backend Específicos (pipefy-document-ingestion-v2/test_backend_integration.py)
3. Tests CrewAI Específicos (pipefy-crewai-analysis-v2/test_crewai_integration.py)
"""

import asyncio
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

# Configuración de colores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(title: str, char: str = "=", length: int = 60):
    """Imprimir encabezado formateado"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{char * length}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.WHITE}{title.center(length)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{char * length}{Colors.END}")

def print_section(title: str):
    """Imprimir sección"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}📋 {title}{Colors.END}")
    print(f"{Colors.BLUE}{'-' * 50}{Colors.END}")

def print_success(message: str):
    """Imprimir mensaje de éxito"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message: str):
    """Imprimir mensaje de error"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message: str):
    """Imprimir mensaje de advertencia"""
    print(f"{Colors.YELLOW}⚠️ {message}{Colors.END}")

def print_info(message: str):
    """Imprimir mensaje informativo"""
    print(f"{Colors.CYAN}ℹ️ {message}{Colors.END}")

async def run_python_script(script_path: str, description: str) -> bool:
    """Ejecutar un script Python y retornar si fue exitoso"""
    print_info(f"Ejecutando: {description}")
    print_info(f"Script: {script_path}")
    
    if not os.path.exists(script_path):
        print_error(f"Script no encontrado: {script_path}")
        return False
    
    try:
        # Ejecutar el script
        process = await asyncio.create_subprocess_exec(
            sys.executable, script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        # Mostrar output
        if stdout:
            print(stdout.decode())
        
        if stderr and process.returncode != 0:
            print_error(f"Error en {description}:")
            print(stderr.decode())
        
        success = process.returncode == 0
        
        if success:
            print_success(f"{description} - COMPLETADO")
        else:
            print_error(f"{description} - FALLÓ (código: {process.returncode})")
        
        return success
        
    except Exception as e:
        print_error(f"Error ejecutando {description}: {str(e)}")
        return False

async def check_dependencies():
    """Verificar que las dependencias necesarias estén instaladas"""
    print_section("Verificando Dependencias")
    
    required_packages = [
        "pytest",
        "httpx",
        "asyncio"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print_success(f"Paquete {package} - OK")
        except ImportError:
            missing_packages.append(package)
            print_error(f"Paquete {package} - FALTANTE")
    
    if missing_packages:
        print_warning(f"Instalar paquetes faltantes: pip install {' '.join(missing_packages)}")
        return False
    
    print_success("Todas las dependencias están instaladas")
    return True

async def check_services_availability():
    """Verificar disponibilidad de servicios"""
    print_section("Verificando Disponibilidad de Servicios")
    
    # URLs a verificar
    services = {
        "Backend Local": "http://localhost:8000/health",
        "CrewAI Local": "http://localhost:8001/health",
        "Backend Prod": "https://pipefy-document-ingestion-v2.onrender.com/health",
        "CrewAI Prod": "https://pipefy-crewai-analysis-v2.onrender.com/health"
    }
    
    import httpx
    
    for service_name, url in services.items():
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    print_success(f"{service_name} - DISPONIBLE")
                else:
                    print_warning(f"{service_name} - RESPONDE ({response.status_code})")
        except Exception as e:
            print_warning(f"{service_name} - NO DISPONIBLE ({str(e)[:50]}...)")

async def run_all_e2e_tests():
    """Ejecutar todos los tests E2E"""
    print_header("🚀 TESTS END-TO-END - ARQUITECTURA MODULAR HÍBRIDA")
    print_info(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info("Proyecto: Document Triaging Agent v2.0")
    
    # Verificar dependencias
    if not await check_dependencies():
        print_error("No se pueden ejecutar los tests sin las dependencias necesarias")
        return False
    
    # Verificar servicios
    await check_services_availability()
    
    # Definir tests a ejecutar
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    tests_to_run = [
        {
            "script": os.path.join(project_root, "test_e2e_integration.py"),
            "description": "Tests E2E Generales - Arquitectura Híbrida"
        },
        {
            "script": os.path.join(project_root, "pipefy-document-ingestion-v2", "test_backend_integration.py"),
            "description": "Tests Backend API - Servicio de Ingestión"
        },
        {
            "script": os.path.join(project_root, "pipefy-crewai-analysis-v2", "test_crewai_integration.py"),
            "description": "Tests CrewAI Service - Servicio de Análisis"
        }
    ]
    
    # Ejecutar tests
    results = []
    
    for i, test_config in enumerate(tests_to_run, 1):
        print_section(f"Test Suite {i}/{len(tests_to_run)}: {test_config['description']}")
        
        success = await run_python_script(
            test_config["script"],
            test_config["description"]
        )
        
        results.append({
            "name": test_config["description"],
            "success": success
        })
    
    # Mostrar resultados finales
    print_header("🎯 RESULTADOS FINALES", "=", 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r["success"])
    failed_tests = total_tests - passed_tests
    
    print(f"\n{Colors.BOLD}📊 RESUMEN DE EJECUCIÓN:{Colors.END}")
    print(f"   Total Test Suites: {total_tests}")
    print(f"   {Colors.GREEN}✅ Pasaron: {passed_tests}{Colors.END}")
    print(f"   {Colors.RED}❌ Fallaron: {failed_tests}{Colors.END}")
    print(f"   {Colors.CYAN}📈 Tasa de Éxito: {(passed_tests/total_tests)*100:.1f}%{Colors.END}")
    
    print(f"\n{Colors.BOLD}📋 DETALLE POR TEST SUITE:{Colors.END}")
    for result in results:
        status = f"{Colors.GREEN}✅ PASÓ{Colors.END}" if result["success"] else f"{Colors.RED}❌ FALLÓ{Colors.END}"
        print(f"   {result['name']}: {status}")
    
    # Mensaje final
    if passed_tests == total_tests:
        print(f"\n{Colors.BOLD}{Colors.GREEN}🎉 TODOS LOS TEST SUITES PASARON EXITOSAMENTE!{Colors.END}")
        print(f"{Colors.GREEN}✅ La arquitectura modular híbrida está funcionando correctamente{Colors.END}")
        print(f"{Colors.GREEN}✅ Los dos servicios se comunican adecuadamente{Colors.END}")
        print(f"{Colors.GREEN}✅ Sistema listo para despliegue en producción{Colors.END}")
    else:
        print(f"\n{Colors.BOLD}{Colors.RED}⚠️ ALGUNOS TEST SUITES FALLARON{Colors.END}")
        print(f"{Colors.YELLOW}🔍 Revisar logs arriba para identificar problemas{Colors.END}")
        print(f"{Colors.YELLOW}🛠️ Corregir issues antes del despliegue{Colors.END}")
    
    # Recomendaciones
    print_header("💡 RECOMENDACIONES POST-TESTS", "-", 60)
    
    if passed_tests == total_tests:
        print(f"{Colors.GREEN}✅ Proceder con despliegue en Render{Colors.END}")
        print(f"{Colors.GREEN}✅ Configurar variables de entorno en producción{Colors.END}")
        print(f"{Colors.GREEN}✅ Monitorear health checks post-despliegue{Colors.END}")
    else:
        print(f"{Colors.YELLOW}🔧 Revisar configuración de servicios{Colors.END}")
        print(f"{Colors.YELLOW}🔧 Verificar variables de entorno{Colors.END}")
        print(f"{Colors.YELLOW}🔧 Validar conectividad entre servicios{Colors.END}")
    
    return passed_tests == total_tests

def main():
    """Función principal"""
    try:
        success = asyncio.run(run_all_e2e_tests())
        exit_code = 0 if success else 1
        
        print(f"\n{Colors.BOLD}🏁 FINALIZADO - Código de salida: {exit_code}{Colors.END}")
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Tests interrumpidos por el usuario{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Error inesperado: {str(e)}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()