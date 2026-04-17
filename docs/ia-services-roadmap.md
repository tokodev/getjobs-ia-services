# Próximos Passos (Roadmap): `ia-services`

## 📅 Curto Prazo (Fase 2 & 3)

### 1. Comunicação via gRPC (Síncrono)
- **Definir `.proto`:** Criar o contrato de serviço `ia_service.proto` contendo as chamadas para extração de CV e otimização de perfil.
- **Implementar Servidor gRPC:** Rodar um processo paralelo (ou dentro do FastAPI) que escuta requisições do NestJS via protocolo binário Protobuf.
- **Geração de Tipos:** Compilar os arquivos `.proto` para Python e TypeScript (para a API Core).

### 2. Consumo de Filas (Assíncrono)
- **Integração BullMQ:** Configurar o consumidor Redis no Python para ler jobs enviados pelo NestJS na fila `cv-extraction`.
- **Estratégia de Retry:** Configurar o LiteLLM para sinalizar ao BullMQ quando um job deve ser tentado novamente em caso de falha de API.

---

## 📅 Médio Prazo (Fase 4 & Migração)

### 3. Migração do AI Copilot
- **Agente `summary_review`:** Implementar a lógica de análise de contexto (experiências + skills) para sugerir resumos executivos.
- **Agente `experience_review`:** Aplicar o método STAR/XYZ via IA em descrições de cargo.

### 4. Observabilidade Avançada
- **Dataset LangSmith:** Criar um conjunto de dados para "Golden Testing" (testar novos modelos contra exemplos reais de sucesso).
- **Custo e Auditoria:** Integrar metadados de `cost` e `usage` do LiteLLM nos logs de cada requisição.

---

## 📅 Longo Prazo (Fase 5+)

### 5. Match Engine (Proprietário)
- **Implementação de Embeddings:** Criar o agente para gerar vetores a partir de currículos e descrições de vagas.
- **Cálculo de Cosine Similarity:** Integrar uma engine (ex: PGVector ou FAISS) para ranqueamento rápido de compatibilidade.

### 6. Integração Final com API Core
- Migrar todas as chamadas de IA legadas da API NestJS para chamadas gRPC ao novo `ia-services`.
- Ativar o cache centralizado no Redis para evitar chamadas duplicadas ao LLM.
