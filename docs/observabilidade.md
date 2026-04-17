# Observabilidade: Infraestrutura e IA

O microserviço `ia-services` utiliza uma estratégia de observabilidade em duas camadas para garantir que tanto o "cérebro" (IA) quanto os "músculos" (Infraestrutura) funcionem perfeitamente.

## 1. Camada de Inteligência (LangSmith)
Focada no ciclo de vida das chamadas às LLMs.
- **Traceability:** Rastreamento completo de cada prompt enviado e resposta recebida.
- **Custo e Performance:** Monitoramento de tokens gastos e latência por requisição.
- **Debugging:** Identificação rápida de onde a IA está falhando no raciocínio.
- **Integração:** Realizada via decorators `@traceable` e metadados injetados pelo LiteLLM.

## 2. Camada de Infraestrutura (Grafana + Prometheus)
Focada na saúde do servidor e dos serviços de apoio.
- **Dashboard (Grafana):** Visualização em tempo real de métricas.
- **Métricas (Prometheus):**
  - **FastAPI:** Requisições por segundo (RPS), erros 4xx/5xx, tempo de resposta HTTP.
  - **gRPC:** Latência das chamadas binárias e volume de tráfego.
  - **Redis/BullMQ:** Tamanho das filas e throughput do worker.
  - **Container:** Uso de CPU, memória e volume de disco.

## 💡 Fluxo de Dados de Observabilidade
1. O **FastAPI** expõe métricas no endpoint `/metrics`.
2. O **Prometheus** lê essas métricas periodicamente.
3. O **Grafana** consulta o Prometheus e exibe dashboards formatados.
4. O **LangSmith** recebe traces diretamente via SDK durante o processamento da IA.
