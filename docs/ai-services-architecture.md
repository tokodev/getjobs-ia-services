# Arquitetura de Microserviços de IA

## 🎯 Visão Geral
Para garantir escalabilidade, isolamento de dependências pesadas (LangChain, LLMs) e modularidade, as funcionalidades de Inteligência Artificial do GetJobs foram movidas para um serviço dedicado em `../ia-services`. A API Core atua como orquestradora, consumindo esses serviços via REST/gRPC.

---

## 🛠️ Serviços de IA Disponibilizados

### 1. Extração de Currículos (CV Parser)
- **Status:** Ativo
- **Objetivo:** Converter PDF/Texto Bruto em JSON estruturado (ParsedCV).
- **IA Utilizada:** LiteLLM (Gemini 2.5 Flash / Groq Llama 3.1).
- **Entrada:** `cv_text` (String).
- **Saída:** Objeto `ParsedCV` (Identity domain).

### 2. AI Copilot: Sugestão de Resumo (Summary Suggestion)
- **Status:** Em migração para `ia-services`
- **Objetivo:** Analisar todo o contexto do perfil do candidato e sugerir um resumo executivo de alto impacto.
- **Prompt:** Focado em Tech Recruiting e Copywriting.
- **Entrada:** `{ currentSummary, experiences, skills }`.
- **Saída:** `{ suggestedSummary, tone, addedKeywords }`.

### 3. AI Copilot: Revisão de Experiência (Experience Review)
- **Status:** Em migração para `ia-services`
- **Objetivo:** Aplicar o método STAR/XYZ em descrições de cargo e fornecer análise técnica.
- **Entrada:** `{ jobTitle, description, skillsContext }`.
- **Saída:** `{ suggestedDescription, technicalAnalysis, pros, cons, actionableFeedback }`.

### 4. Match Engine (Futuro)
- **Status:** Planejado
- **Objetivo:** Calcular a porcentagem de compatibilidade entre um Candidato e uma Vaga Freelance/CLT usando embeddings.

---

## 🔄 Fluxo de Integração e Cache
A API Core (`getjobs-api`) mantém a responsabilidade do **Cache** para evitar chamadas redundantes e custos desnecessários:

1. **API Core** recebe request GraphQL.
2. **API Core** gera `MD5(content + prompt_version)`.
3. **API Core** consulta **Redis** local.
4. Se *Cache Miss*:
   - Chama o endpoint em `ia-services`.
   - Salva o resultado estruturado no **Redis** (TTL: 7 dias).
5. Retorna o JSON ao Front-end.

---

## 🚀 Próximos Passos (ia-services)
1. Inicializar projeto Python (FastAPI) ou Node.js (NestJS) em `../ia-services`.
2. Implementar endpoints para `summary-review` e `experience-review`.
3. Configurar LangChain com suporte a `withStructuredOutput`.
