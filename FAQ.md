

# **FAQ - Guia de Análise de Documentos (Versão 2.0 - com Automação IA)**

Esta seção de Perguntas Frequentes (FAQ) foi atualizada para auxiliar as equipes a compreender e aplicar corretamente os requisitos do **CHECKLIST CEDENTE - PESSOA JURÍDICA**, agora integrado com o nosso novo **Sistema de Análise por Inteligência Artificial (IA)**.

**Objetivo:** Fornecer um guia prático, reduzir erros, e explicar como a nova automação classifica as pendências para agilizar o processo como um todo.

### **Tabela 1: Checklist Simplificado e Classificação de Pendências pela IA**

Esta tabela resume os documentos e, mais importante, como o sistema de IA classifica cada tipo de pendência.

| Item do Checklist | Documento Principal Requerido | Prazo/Validade Chave | Classificação da Pendência (se houver) | Ação Automática do Sistema |
| :--- | :--- | :--- | :--- | :--- |
| **1. Cartão CNPJ** | Cópia simples do Cartão CNPJ. | Emitido há no máximo 90 dias. | **Não Bloqueante** | A IA notifica a equipe de Cadastro. O sistema tentará gerar o documento automaticamente via API. O card irá para a fase **"Emitir documentos"**. |
| **2. Contrato/Estatuto Social Consolidado** | Cópia do último consolidado com nº de registro. | Emitido há no máx. 3 anos. | **Não Bloqueante** (se pendência for apenas a data > 3 anos) | A IA move o card para **"Emitir documentos"** para que a equipe de Cadastro emita a `Certidão Simplificada`. |
| **3. Falta de Nº de Registro** | Contrato/Estatuto/Ata sem o nº do órgão competente. | N/A | **Bloqueante** | A IA move o card para **"Pendências Documentais"** e notifica o gestor comercial via WhatsApp. |
| **4. Ata de Eleição da Diretoria** | Cópia da ata vigente com nº de registro (para S/A). | Deve ser da diretoria vigente. | **Bloqueante** (se faltar registro) | A IA move o card para **"Pendências Documentais"** e notifica o gestor comercial. |
| **5. Procuração** | Cópia com reconhecimento de firma ou assinatura digital. | Vigente. | **Bloqueante** (se a validação da assinatura falhar) | A IA move o card para **"Pendências Documentais"** e notifica o gestor. |
| **6. Docs Sócios (Identificação)** | RG/CPF ou CNH legíveis e vigentes. | Vigentes. | **Bloqueante** (se ilegível ou inválido) | A IA move o card para **"Pendências Documentais"** e notifica o gestor. |
| **7. Docs Sócios (Residência)** | Conta de consumo (máx. 90 dias) ou Declaração. | Máx. 90 dias e titularidade correta. | **Bloqueante** | A IA move o card para **"Pendências Documentais"** e notifica o gestor. |
| **8. Docs Financeiros (Balanço/Fat.)** | Balanço, DRE ou Relação de Faturamento. | Datado, assinado (contador/representante). | **Bloqueante** (se faltar assinatura) | A IA move o card para **"Pendências Documentais"** e notifica o gestor. |
| **9. Relatório de Visita** | Relatório de visita do gestor. | Datado e assinado pelo gestor. | **Bloqueante** (se ausente ou incompleto) | A IA move o card para **"Pendências Documentais"** e notifica o gestor. |

---

### **Perguntas Frequentes Detalhadas (com Lógica de IA)**

#### **1. Cartão CNPJ**

* **O que é exigido?** Cópia simples do Cartão CNPJ da empresa cedente.
* **Qual a validade?** Deve ter sido emitido dentro dos últimos 90 dias.

* **P: O cliente enviou um Cartão CNPJ com mais de 90 dias. O que acontece agora com a IA?**
    * **R:** Esta é uma pendência **NÃO BLOQUEANTE**. O agente de IA identificará o problema, classificará o caso como `Pendencia_NaoBloqueante` e o sistema automaticamente:
        1.  Tentará gerar um novo Cartão CNPJ via API da Receita Federal.
        2.  Moverá o card para a fase **"Emitir documentos"** em Pipefy.
        3.  Deixará um relatório no card para a equipe de Cadastro, informando que o documento foi gerado ou que precisa ser verificado.
    * **Atenção Comercial:** O processo não para mais por isso, mas é sempre bom orientar o cliente a enviar a documentação correta para agilizar o trabalho da equipe interna.

#### **2. Contrato Social / Estatuto Social e Certidão Simplificada**

* **O que é exigido?** Cópia simples do último Contrato/Estatuto Social **consolidado** e com **número de registro** no órgão competente.
* **Qual a validade?** O documento deve ter sido registrado há no máximo 3 anos. Se for mais antigo, é **obrigatório** apresentar uma `Certidão Simplificada` atualizada (emitida há no máximo 90 dias).

* **P: O Contrato Social consolidado do cliente tem 4 anos e ele não enviou a Certidão Simplificada. O processo para?**
    * **R:** Não mais. Esta é uma pendência **NÃO BLOQUEANTE**. O agente de IA identificará a necessidade da certidão, classificará o caso como `Pendencia_NaoBloqueante` e o sistema moverá o card para a fase **"Emitir documentos"**. A equipe de Cadastro será responsável por emitir este documento.
* **P: O cliente enviou um Contrato Social sem o número de registro da Junta Comercial. O que acontece?**
    * **R:** Este é um problema **BLOQUEANTE**. A falta do registro é uma falha crítica que a equipe interna não pode corrigir. O agente de IA classificará o caso como `Pendencia_Bloqueante`. O sistema automaticamente:
        1.  Moverá o card para a fase **"Pendências Documentais"**.
        2.  Adicionará um comentário no card com o relatório detalhado do erro.
        3.  **Enviará uma notificação via WhatsApp** para o gestor comercial responsável, informando sobre a pendência crítica.

#### **3. Documentos dos Sócios (Comprovante de Residência)**

* **P: O comprovante de residência do sócio está em nome da esposa e não foi enviada a Certidão de Casamento. Isso é bloqueante?**
    * **R:** Sim, é **BLOQUEANTE**. O agente de IA é treinado para seguir a regra à risca: comprovante em nome de cônjuge exige a certidão para validar o vínculo. Sem ela, a pendência é crítica. O card será movido para **"Pendências Documentais"** e o gestor será notificado.
    * **Atenção Comercial:** Este continua sendo um ponto crítico. Para evitar bloqueios, sempre coletem a Certidão de Casamento proativamente se o comprovante estiver em nome do cônjuge.

#### **4. Processo Geral com a IA**

* **P: O que significa quando um card meu é movido para "Pendências Documentais" pela IA?**
    * **R:** Significa que o agente de IA encontrou uma ou mais **pendências bloqueantes**. Você recebeu (ou receberá em breve) uma notificação por WhatsApp com um resumo. Sua ação é necessária e urgente. Verifique o relatório deixado no card, contate o cliente para obter a documentação correta e anexe-a ao card para uma nova análise.
* **P: E se o card for para "Emitir documentos"?**
    * **R:** Boas notícias! Significa que o agente encontrou pendências, mas nenhuma delas bloqueia o processo. São itens que a equipe de Cadastro pode resolver internamente, como emitir um `Cartão CNPJ` atualizado ou uma `Certidão Simplificada`. Você não precisa fazer nada, mas o processo de cadastro pode demorar um pouco mais enquanto a equipe interna atua.
* **P: E se o card for para "Aprovado"?**
    * **R:** Excelente! Significa que a IA analisou todos os documentos e não encontrou **nenhuma pendência**. O card avançou automaticamente no fluxo e está pronto para a próxima etapa de análise de risco, sem necessidade de nenhuma ação manual na triagem.

---