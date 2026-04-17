# Documentação Técnica: Integração de Infraestrutura e Filas (BullMQ)

Esta documentação descreve como o microserviço `ia-services` foi integrado ao ecossistema global do GetJobs, utilizando a rede de infraestrutura existente e implementando o processamento assíncrono via BullMQ.

---

## 🌐 Integração de Rede e Banco de Dados

O `ia-services` não roda mais de forma isolada; ele agora faz parte da rede externa **`infra`** (definida no Podman/Docker principal).

### 1. Conectividade de Containers
- **Rede:** `external: true` para a rede `infra`.
- **Hosts de Serviço:**
  - **Redis:** `getjobs-redis` (Porta 6379)
  - **Postgres:** `getjobs-postgres` (Porta 5432)
  - **LiteLLM:** `getjobs-litellm` (Porta 4000)

### 2. Sincronização de Credenciais (`.env`)
As chaves de API e senhas foram extraídas e sincronizadas com os serviços da infraestrutura:
- **Redis Password:** `Redis@2025` (conforme `infra/.env`).
- **IA Keys:** Gemini e Groq Keys sincronizadas para garantir que o LiteLLM funcione corretamente.
- **Database URL:** Apontando para o banco de dados `getjobs` no container Postgres da infra.

---

## 📥 Processamento Assíncrono (BullMQ)

Para lidar com grandes volumes de dados (como extração de múltiplos CVs simultâneos), implementamos um **Worker** compatível com o ecossistema Node.js (BullMQ).

### 1. O Worker (`app/worker/worker.py`)
Um processo Python dedicado que:
1. Conecta-se ao Redis da infraestrutura usando a senha configurada.
2. Escuta a fila definida em `BULLMQ_QUEUE_NAME` (Padrão: `cv-extraction`).
3. Recebe o payload enviado pelo NestJS (ex: `{ "userId": "...", "cvText": "..." }`).
4. Invoca o `CVParserAgent` para processar a inteligência.
5. Retorna o resultado estruturado para o Redis, onde o NestJS pode consumi-lo.

### 2. Lifecycle e Orquestração
O Worker é iniciado de forma assíncrona no `startup` do FastAPI (`app/main.py`):
- **Startup:** O worker começa a ouvir a fila.
- **Shutdown:** O worker fecha as conexões de forma graciosa para evitar perda de dados.

---

## 📂 Arquivos Gerados/Modificados

| Arquivo | Função |
| :--- | :--- |
| `app/worker/worker.py` | Implementação do consumidor BullMQ em Python. |
| `app/core/settings.py` | Configurações estendidas para Redis Auth e Database. |
| `app/main.py` | Integração do ciclo de vida do Worker no servidor. |
| `.env` | Credenciais oficiais e hosts da rede `infra`. |
| `docker-compose.yaml` | Configuração para rodar dentro da rede global do GetJobs. |

---

## 🚦 Como Testar a Fila
1. Certifique-se de que a infraestrutura principal (Redis/Postgres) está rodando.
2. Suba o `ia-services`: `docker-compose up`.
3. O log exibirá: `INFO:app.worker.worker:BullMQ Worker started for queue: cv-extraction`.
4. Qualquer job inserido nesta fila via NestJS ou Redis Insight (porta 8001) será processado automaticamente pelo Python.
