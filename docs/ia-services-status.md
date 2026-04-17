# Status do Serviço: `ia-services` (Abril 2026)

## 🎯 Visão Geral
O microserviço `ia-services` foi inicializado como o motor de inteligência do ecossistema GetJobs. Ele segue uma arquitetura moderna em **Python**, focada em alta performance, resiliência de modelos de IA e observabilidade total.

---

## 🏗️ Arquitetura Atual

### 1. Stack Tecnológica
- **Linguagem:** Python 3.11+
- **Framework Web:** FastAPI (Entrypoint e Health Checks)
- **Gateway de LLM:** LiteLLM (Proxy para Load Balancing entre Gemini, OpenAI e Ollama)
- **Observabilidade:** LangSmith (Rastreamento de traces e latência)
- **Comunicação:**
  - **Síncrona (Previsão):** gRPC para baixa latência.
  - **Assíncrona (Previsão):** Redis/BullMQ para processamento em massa.
- **Containerização:** Docker + Docker Compose.

### 2. Componentes Implementados
- **Agente de Extração de CV (`app/agents/cv_parser.py`):** 
  - Utiliza o modelo `cv-parser-delegate` via LiteLLM.
  - Implementa schemas **Pydantic** para garantir que a saída seja um JSON estruturado e válido.
  - Decorado com `@traceable` para integração nativa com LangSmith.
- **Configuração de Roteamento (`config.yaml`):**
  - Define modelos virtuais para separar a lógica de negócio do provedor específico.
  - Configurado para retry automático em erros 429 (Rate Limit).
- **Core Settings:** Gerenciamento de variáveis de ambiente via `pydantic-settings`.

---

## 🚦 Como Rodar o Serviço

### Pré-requisitos
- Docker e Docker Compose instalados.
- Chaves de API (Gemini/OpenAI) no arquivo `.env`.

### Comandos
1. **Configurar o ambiente:**
   ```bash
   cp .env.example .env
   # Edite o .env com suas chaves
   ```
2. **Subir a stack:**
   ```bash
   docker-compose up --build
   ```
3. **Verificar integridade:**
   - API Health Check: `http://localhost:8000/health`
   - LiteLLM Dashboard: `http://localhost:4000` (se configurado)

---

## 🛡️ Segurança e Resiliência
- **LiteLLM Proxy:** Atua como um buffer. Se o Gemini falhar, o sistema está pronto para chavear para o backup sem alteração no código Python.
- **Isolamento:** O serviço de IA não acessa o banco de dados principal diretamente; ele processa dados e retorna contratos estruturados.
