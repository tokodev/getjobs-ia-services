# CV Extraction & Analysis Service

Este documento descreve como o serviço de IA (`ia-services` em Python) processa currículos e como ele se comunica com a API principal (NestJS).

## Arquitetura de Comunicação

O `ia-services` atua como um worker e um servidor gRPC simultaneamente.

### 1. Extração em Lote (Background) via BullMQ
Usado quando o usuário faz upload de um arquivo PDF/Docx.
- **Fluxo**: NestJS (API) -> Redis (BullMQ) -> Python (Worker).
- **Fila**: `cv-extraction`.
- **Payload**: `{ "userId": "...", "cvText": "..." }`.
- **Resultado**: O Python processa o texto, normaliza os dados e o BullMQ salva o JSON no campo `returnvalue` do job no Redis. O NestJS monitora o evento `completed` e atualiza o banco de dados PostgreSQL.

### 2. Extração em Tempo Real via gRPC
Usado para pré-visualização ou integrações síncronas.
- **Protocolo**: gRPC na porta `50051`.
- **Método**: `ParseCV(CVRequest) returns (CVResponse)`.
- **Vantagem**: Baixa latência e tipagem forte via Protobuf.

---

## Motor de Inteligência (CVParserAgent)

O `CVParserAgent` implementa uma estratégia rigorosa de extração baseada na lógica de ETL para dados não estruturados.

### Estratégia de Extração
1. **Prompt de Alta Fidelidade**: Instruções estritas para manter a veracidade do texto original (especialmente no sumário e experiências).
2. **Normalização de Datas**: Conversão inteligente de "Presente/Atual" para `null` com a flag `isCurrentRole`.
3. **Filtragem de Habilidades**: Separação automática entre Hard Skills e Soft Skills usando dicionários de palavras-chave.
4. **Auto-Categorização de Tech Stack**: Mapeamento de habilidades para categorias como `frontend`, `backend`, `cloud`, etc.
5. **Validação de Contexto**: Campos como `workRegime` e `languages` são validados contra o texto original para evitar alucinações da IA.

### Fallback e Resiliência
- **Primary Model**: Utiliza o LiteLLM para rotear para modelos de alta performance (ex: GPT-4o, Gemini 1.5 Pro).
- **Fallback**: Caso o provedor principal falhe (429, 503), o agente tenta automaticamente o **Ollama** (Llama 3) rodando localmente na infraestrutura.
- **Retentativas**: Implementado com backoff exponencial (3 tentativas).

---

## Schemas de Saída (JSON)

O serviço retorna um objeto estruturado seguindo rigorosamente o schema `ParsedCV`.

```json
{
  "personalData": {
    "fullName": "...",
    "email": "...",
    "location": { "city": "...", "workRegime": "Remoto" },
    "links": { "linkedin": "...", "github": "..." }
  },
  "summary": "...",
  "hardSkills": ["Python", "React"],
  "techStack": { "backend": ["Python"], "frontend": ["React"] },
  "experience": [...],
  "education": [...],
  "aiConfidence": 0.95
}
```
