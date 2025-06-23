#!/usr/bin/env python3
"""
Script de teste manual para integração com APIs de CNPJ.

Este script permite testar manualmente as funcionalidades de:
- Consulta de dados de CNPJ
- Geração de cartões CNPJ
- Cache e armazenamento
- Validação para triagem
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.services.cnpj_service import cnpj_service, CNPJServiceError
    from src.integrations.cnpj_client import cnpj_client, CNPJAPIError
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    print("Verifique se todas as dependências estão instaladas")
    sys.exit(1)


class CNPJTestRunner:
    """Classe para executar testes manuais de CNPJ."""
    
    def __init__(self):
        self.test_cnpjs = [
            "11.222.333/0001-81",  # CNPJ de teste (pode não existir)
            "11222333000181",      # Mesmo CNPJ sem formatação
            "00.000.000/0000-00",  # CNPJ inválido
            "123",                 # Formato inválido
        ]
    
    def print_header(self, title: str):
        """Imprime cabeçalho formatado."""
        print("\n" + "="*60)
        print(f" {title}")
        print("="*60)
    
    def print_result(self, result: dict, title: str = "Resultado"):
        """Imprime resultado formatado."""
        print(f"\n{title}:")
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    
    async def test_cnpj_validation(self):
        """Testa validação de CNPJs."""
        self.print_header("TESTE 1: Validação de CNPJs")
        
        for cnpj in self.test_cnpjs:
            print(f"\nTestando CNPJ: {cnpj}")
            
            # Teste de validação básica
            is_valid = cnpj_client._validate_cnpj(cnpj)
            print(f"Validação básica: {'✅ Válido' if is_valid else '❌ Inválido'}")
            
            if is_valid:
                # Teste de formatação
                formatted = cnpj_client._format_cnpj(cnpj)
                cleaned = cnpj_client._clean_cnpj(cnpj)
                print(f"Formatado: {formatted}")
                print(f"Limpo: {cleaned}")
    
    async def test_cnpj_api_query(self):
        """Testa consulta nas APIs de CNPJ."""
        self.print_header("TESTE 2: Consulta nas APIs de CNPJ")
        
        # Usar apenas CNPJs válidos para teste de API
        valid_cnpjs = [cnpj for cnpj in self.test_cnpjs if cnpj_client._validate_cnpj(cnpj)]
        
        for cnpj in valid_cnpjs[:1]:  # Testar apenas o primeiro para não sobrecarregar APIs
            print(f"\nConsultando CNPJ: {cnpj}")
            
            try:
                # Teste direto do cliente
                cnpj_data = await cnpj_client.get_cnpj_data(cnpj)
                
                result = {
                    "cnpj": cnpj_data.cnpj,
                    "razao_social": cnpj_data.razao_social,
                    "situacao_cadastral": cnpj_data.situacao_cadastral,
                    "uf": cnpj_data.uf,
                    "municipio": cnpj_data.municipio,
                    "api_source": cnpj_data.api_source,
                    "consulted_at": cnpj_data.consulted_at.isoformat()
                }
                
                self.print_result(result, "✅ Dados obtidos com sucesso")
                
            except CNPJAPIError as e:
                print(f"❌ Erro na API: {e.message}")
                if e.api_name:
                    print(f"API: {e.api_name}")
                if e.status_code:
                    print(f"Status: {e.status_code}")
            except Exception as e:
                print(f"❌ Erro inesperado: {e}")
    
    async def test_simple_validation(self):
        """Teste simples de validação sem dependências externas."""
        self.print_header("TESTE SIMPLES: Validação Básica")
        
        print("Testando validação de CNPJ sem APIs externas...")
        
        test_cases = [
            ("11.222.333/0001-81", "CNPJ formatado válido"),
            ("11222333000181", "CNPJ sem formatação válido"),
            ("00.000.000/0000-00", "CNPJ inválido"),
            ("123", "Formato inválido"),
            ("", "CNPJ vazio"),
            ("11111111111111", "CNPJ com dígitos iguais")
        ]
        
        for cnpj, description in test_cases:
            try:
                is_valid = cnpj_client._validate_cnpj(cnpj)
                status = "✅ Válido" if is_valid else "❌ Inválido"
                print(f"{description}: {cnpj} -> {status}")
                
                if is_valid:
                    formatted = cnpj_client._format_cnpj(cnpj)
                    cleaned = cnpj_client._clean_cnpj(cnpj)
                    print(f"  Formatado: {formatted}")
                    print(f"  Limpo: {cleaned}")
                    
            except Exception as e:
                print(f"  ❌ Erro: {e}")
    
    async def test_cnpj_service_cache(self):
        """Testa funcionalidades de cache do serviço."""
        self.print_header("TESTE 3: Cache do Serviço de CNPJ")
        
        valid_cnpjs = [cnpj for cnpj in self.test_cnpjs if cnpj_client._validate_cnpj(cnpj)]
        
        if not valid_cnpjs:
            print("❌ Nenhum CNPJ válido para testar cache")
            return
        
        cnpj = valid_cnpjs[0]
        print(f"Testando cache com CNPJ: {cnpj}")
        
        try:
            # 1. Primeira consulta (deve ir para API)
            print("\n1. Primeira consulta (API)...")
            start_time = datetime.now()
            result1 = await cnpj_service.get_cnpj_data(cnpj, use_cache=True)
            time1 = (datetime.now() - start_time).total_seconds()
            print(f"✅ Consulta realizada em {time1:.2f}s")
            print(f"Fonte: {result1.api_source}")
            
            # 2. Segunda consulta (deve usar cache)
            print("\n2. Segunda consulta (cache)...")
            start_time = datetime.now()
            result2 = await cnpj_service.get_cnpj_data(cnpj, use_cache=True)
            time2 = (datetime.now() - start_time).total_seconds()
            print(f"✅ Consulta realizada em {time2:.2f}s")
            print(f"Fonte: {result2.api_source}")
            
            # 3. Verificar se dados são iguais
            if result1.cnpj == result2.cnpj and result1.razao_social == result2.razao_social:
                print("✅ Dados do cache são consistentes")
            else:
                print("❌ Dados do cache são inconsistentes")
            
            # 4. Listar CNPJs em cache
            cached_list = cnpj_service.list_cached_cnpjs()
            print(f"\n✅ CNPJs em cache: {len(cached_list)}")
            
        except Exception as e:
            print(f"❌ Erro no teste de cache: {e}")
    
    async def test_cnpj_card_generation(self):
        """Testa geração de cartões CNPJ."""
        self.print_header("TESTE 4: Geração de Cartões CNPJ")
        
        valid_cnpjs = [cnpj for cnpj in self.test_cnpjs if cnpj_client._validate_cnpj(cnpj)]
        
        if not valid_cnpjs:
            print("❌ Nenhum CNPJ válido para testar geração de cartão")
            return
        
        cnpj = valid_cnpjs[0]
        case_id = f"TEST_CASE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"Gerando cartão para CNPJ: {cnpj}")
        print(f"Case ID: {case_id}")
        
        try:
            # Gerar cartão (sem salvar na base de dados para teste)
            result = await cnpj_service.gerar_e_armazenar_cartao_cnpj(
                cnpj=cnpj,
                case_id=case_id,
                save_to_database=False
            )
            
            if result["success"]:
                print("✅ Cartão gerado com sucesso!")
                self.print_result({
                    "cnpj": result["cnpj"],
                    "razao_social": result["razao_social"],
                    "file_path": result["file_path"],
                    "generated_at": result["generated_at"],
                    "api_source": result["api_source"]
                })
                
                # Verificar se arquivo foi criado
                if os.path.exists(result["file_path"]):
                    print(f"✅ Arquivo criado: {result['file_path']}")
                    
                    # Mostrar conteúdo do arquivo
                    with open(result["file_path"], 'r', encoding='utf-8') as f:
                        card_content = json.load(f)
                    
                    print("\n📄 Conteúdo do cartão:")
                    print(json.dumps(card_content, indent=2, ensure_ascii=False, default=str))
                else:
                    print(f"❌ Arquivo não encontrado: {result['file_path']}")
            else:
                print("❌ Falha na geração do cartão")
                self.print_result(result)
                
        except Exception as e:
            print(f"❌ Erro na geração do cartão: {e}")
    
    async def test_cnpj_validation_for_triagem(self):
        """Testa validação de CNPJ para triagem."""
        self.print_header("TESTE 5: Validação para Triagem")
        
        for cnpj in self.test_cnpjs:
            print(f"\nValidando CNPJ para triagem: {cnpj}")
            
            try:
                result = await cnpj_service.validate_cnpj_for_triagem(cnpj)
                
                if result["valid"]:
                    print("✅ CNPJ válido para triagem")
                    self.print_result({
                        "cnpj": result["cnpj"],
                        "razao_social": result["razao_social"],
                        "situacao_ativa": result["situacao_ativa"],
                        "uf": result["uf"],
                        "warnings": result.get("warnings", [])
                    })
                else:
                    print(f"❌ CNPJ inválido: {result['error']}")
                    
            except Exception as e:
                print(f"❌ Erro na validação: {e}")
    
    async def test_cache_management(self):
        """Testa gerenciamento de cache."""
        self.print_header("TESTE 6: Gerenciamento de Cache")
        
        # Estatísticas do cache
        stats = cnpj_service.get_cnpj_cache_statistics()
        print("📊 Estatísticas do cache:")
        self.print_result(stats)
        
        # Listar CNPJs em cache
        cached_cnpjs = cnpj_service.list_cached_cnpjs()
        print(f"\n📋 CNPJs em cache: {len(cached_cnpjs)}")
        for cached in cached_cnpjs[:3]:  # Mostrar apenas os 3 primeiros
            print(f"  - {cached['cnpj']} | {cached['razao_social']} | Válido: {cached['is_valid']}")
        
        # Listar cartões gerados
        generated_cards = cnpj_service.list_generated_cards()
        print(f"\n🗂️ Cartões gerados: {len(generated_cards)}")
        for card in generated_cards[:3]:  # Mostrar apenas os 3 primeiros
            print(f"  - {card['cnpj']} | {card['razao_social']} | {card['generated_at']}")
        
        # Opção de limpeza de cache (comentada para segurança)
        # print("\n🧹 Limpando cache expirado...")
        # removed = cnpj_service.clear_cache(older_than_hours=24)
        # print(f"✅ {removed} arquivos de cache removidos")
    
    async def run_all_tests(self):
        """Executa todos os testes."""
        print("🚀 Iniciando testes de integração CNPJ")
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        tests = [
            self.test_simple_validation,
            self.test_cnpj_validation,
            self.test_cnpj_api_query,
            self.test_cnpj_service_cache,
            self.test_cnpj_card_generation,
            self.test_cnpj_validation_for_triagem,
            self.test_cache_management
        ]
        
        for i, test in enumerate(tests, 1):
            try:
                await test()
            except Exception as e:
                print(f"\n❌ Erro no teste {i}: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n" + "="*60)
        print(" 🏁 TESTES CONCLUÍDOS")
        print("="*60)


async def main():
    """Função principal."""
    print("🔧 Teste Manual de Integração CNPJ")
    print("Este script testa as funcionalidades de CNPJ do sistema.")
    
    # Verificar configuração
    print("\n📋 Verificando configuração...")
    
    # Verificar se diretórios existem
    data_dir = Path("data")
    if not data_dir.exists():
        print("📁 Criando diretório data/")
        data_dir.mkdir(exist_ok=True)
    
    runner = CNPJTestRunner()
    
    # Menu interativo
    while True:
        print("\n" + "="*50)
        print(" MENU DE TESTES")
        print("="*50)
        print("1. Teste Simples (Validação)")
        print("2. Validação de CNPJs")
        print("3. Consulta nas APIs")
        print("4. Teste de Cache")
        print("5. Geração de Cartões")
        print("6. Validação para Triagem")
        print("7. Gerenciamento de Cache")
        print("8. Executar Todos os Testes")
        print("0. Sair")
        
        choice = input("\nEscolha uma opção: ").strip()
        
        if choice == "0":
            print("👋 Saindo...")
            break
        elif choice == "1":
            await runner.test_simple_validation()
        elif choice == "2":
            await runner.test_cnpj_validation()
        elif choice == "3":
            await runner.test_cnpj_api_query()
        elif choice == "4":
            await runner.test_cnpj_service_cache()
        elif choice == "5":
            await runner.test_cnpj_card_generation()
        elif choice == "6":
            await runner.test_cnpj_validation_for_triagem()
        elif choice == "7":
            await runner.test_cache_management()
        elif choice == "8":
            await runner.run_all_tests()
        else:
            print("❌ Opção inválida!")
        
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc() 