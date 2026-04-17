# Documentação Técnica: Comunicação gRPC e Observabilidade

Esta documentação detalha a implementação da camada de comunicação de alta performance e os mecanismos de monitoramento do microserviço `ia-services`.

---

## 🏎️ Comunicação gRPC (Síncrona)

O gRPC foi implementado para lidar com requisições que exigem baixa latência e contratos de dados rígidos entre a API Core (NestJS) e o serviço de IA (Python).

### 1. O Contrato (`.proto`)
Localizado em `app/grpc_server/ia_service.proto`, o contrato define os serviços disponíveis:
- `ParseCV`: Recebe texto bruto e retorna JSON estruturado do currículo.
- `GetInstantMatch`: Calcula a compatibilidade em tempo real entre um perfil e uma vaga.

### 2. O Servidor
O servidor gRPC roda na **porta 50051** e é iniciado automaticamente junto com o FastAPI.
- **Arquivo:** `app/grpc_server/server.py`
- **Integração:** Consome diretamente os `Agents` (ex: `CVParserAgent`), garantindo que a lógica de IA seja a mesma, independente do protocolo (HTTP ou gRPC).

### 3. Como Funciona a Chamada
1. O cliente (NestJS) envia uma mensagem binária (Protobuf).
2. O servidor Python decodifica, processa a IA (via LiteLLM/LangSmith).
3. O servidor retorna a resposta estruturada, reduzindo o overhead de serialização JSON e latência HTTP/1.1.

---

## 📊 Observabilidade de Infraestrutura (Prometheus/Grafana)

Além do LangSmith (focado em IA), implementamos a coleta de métricas de sistema e performance.

### 1. Coleta de Métricas (`/metrics`)
O FastAPI foi instrumentado com o `prometheus-fastapi-instrumentator`.
- **Endpoint:** `http://localhost:8000/metrics`
- **Dados Coletados:** 
  - Latência de requisições (Histogramas).
  - Contagem de erros (4xx, 5xx).
  - Número de requisições ativas.
  - Uso de recursos do Python (Memória/CPU).

### 2. Fluxo de Monitoramento
1. **Instrumentação:** O código Python gera as métricas em tempo real.
2. **Exposição:** O endpoint `/metrics` disponibiliza os dados no formato padrão do Prometheus.
3. **Agregação:** O Prometheus (container) coleta esses dados.
4. **Visualização:** O Grafana exibe os gráficos de saúde do serviço.

---

## 📂 Arquivos Gerados/Modificados

| Arquivo | Função |
| :--- | :--- |
| `app/grpc_server/ia_service.proto` | Definição da interface do serviço. |
| `app/grpc_server/server.py` | Implementação do servidor gRPC. |
| `app/main.py` | Orquestração do início do gRPC e Instrumentação Prometheus. |
| `app/grpc_server/*_pb2*.py` | Arquivos gerados pelo compilador gRPC (não editar manualmente). |
| `requirements.txt` | Adição de `grpcio`, `grpcio-tools` e `prometheus-fastapi-instrumentator`. |

---

## 🚀 Como Validar
Para verificar se o servidor gRPC e as métricas estão ativos:
1. Suba os containers: `docker-compose up`.
2. Acesse `http://localhost:8000/metrics` no navegador para ver as métricas brutas.
3. Use uma ferramenta como **Postman** (com suporte a gRPC) ou **grpcurl** para testar a porta `50051`.
