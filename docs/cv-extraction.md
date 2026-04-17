# CV Extraction — Documentação Completa

## 🎯 Visão Geral

O módulo de extração de CV converte currículos em **PDF** para um **JSON estruturado** seguindo um schema agnóstico de ETL. O pipeline combina extração de texto local (`pdftotext`) com análise inteligente via IA (**LiteLLM/Gemini** com fallback **Ollama**).

---

## 🔄 Arquitetura do Pipeline

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────────────┐
│  Upload PDF │────►│  pdftotext   │────►│ LiteLLM/     │────►│  Salva no   │
│  (REST)     │     │  (extrai     │     │ Gemini 2.5   │     │  PostgreSQL │
│             │     │   texto)     │     │ + fallback   │     │             │
└─────────────┘     └──────────────┘     └──────────────┘     └─────────────┘
```

### Camadas DDD

| Camada             | Arquivo                                 | Responsabilidade                                     |
| ------------------ | --------------------------------------- | ---------------------------------------------------- |
| **Domain**         | `parsed-cv.entity.ts`                   | Entity com tipos tipados e métodos de estado         |
| **Domain**         | `cv-extraction.repository.interface.ts` | Interface do repositório                             |
| **Application**    | `extract-cv.use-case.ts`                | Orquestração do pipeline                             |
| **Infrastructure** | `stirling-pdf.service.ts`               | Extração de texto (pdftotext + fallback StirlingPDF) |
| **Infrastructure** | `cv-analysis.service.ts`                | Análise IA via LiteLLM/Gemini + Ollama fallback      |
| **Infrastructure** | `ollama.service.ts`                     | Serviço local Ollama para fallback                   |
| **Infrastructure** | `prisma-cv-extraction.repository.ts`    | Persistência Prisma                                  |
| **Presentation**   | `cv-extraction.controller.ts`           | Endpoints REST                                       |

---

## 📋 Schema JSON de Resposta (Fase 1 — ETL Agnóstico)

A IA retorna um JSON seguindo **rigorosamente** esta estrutura. Os dados são mapeados **sem sumarização, tradução ou melhoria** — fidelidade total ao texto original do CV.

### Schema Completo

```json
{
  "personalData": {
    "fullName": "String ou null",
    "email": "String ou null",
    "phone": "String ou null",
    "location": "Cidade, Estado",
    "links": ["Array de URLs (LinkedIn, Portfolio, GitHub, etc)"]
  },
  "summary": "Texto bruto do resumo/objetivo",
  "hardSkills": ["Array de termos técnicos/ferramentas identificadas"],
  "softSkills": ["Array de competências comportamentais"],
  "experience": [
    {
      "company": "Nome da Organização",
      "role": "Cargo ocupado",
      "location": "Cidade/Estado ou Remoto",
      "startDate": "YYYY-MM",
      "endDate": "YYYY-MM ou null",
      "isCurrentRole": true,
      "originalDescription": "Texto completo das atividades sem alterações"
    }
  ],
  "education": [
    {
      "institution": "Nome da Instituição",
      "degree": "Nível (Graduação, MBA, etc)",
      "field": "Área de estudo",
      "startDate": "YYYY",
      "endDate": "YYYY"
    }
  ],
  "certifications": [
    {
      "name": "Nome do curso ou certificação",
      "institution": "Instituição emissora",
      "description": "Breve descrição ou null",
      "year": "YYYY ou null"
    }
  ],
  "languages": [{ "language": "Nome", "level": "Nível" }]
}
```

### Descrição dos Campos

#### `personalData` — Dados Pessoais

| Campo      | Tipo           | Obrigatório | Descrição                                 |
| ---------- | -------------- | ----------- | ----------------------------------------- |
| `fullName` | `string\|null` | Sim         | Nome completo do candidato                |
| `email`    | `string\|null` | Sim         | Endereço de e-mail                        |
| `phone`    | `string\|null` | Sim         | Telefone/celular                          |
| `location` | `string\|null` | Sim         | Cidade, Estado                            |
| `links`    | `string[]`     | Sim         | URLs de LinkedIn, Portfolio, GitHub, etc. |

#### `summary` — Resumo Profissional

| Campo | Tipo           | Descrição                                                      |
| ----- | -------------- | -------------------------------------------------------------- |
|       | `string\|null` | Texto **bruto** do resumo/objetivo. Não resumir, não traduzir. |

#### `hardSkills` — Habilidades Técnicas

| Campo | Tipo       | Descrição                                                  |
| ----- | ---------- | ---------------------------------------------------------- |
|       | `string[]` | Lista de ferramentas, frameworks, linguagens, tecnologias. |

**Exemplo:**

```json
[
  "ReactJS",
  "Next.js",
  "TypeScript",
  "Node.js",
  "NestJS",
  "PostgreSQL",
  "AWS",
  "Docker",
  "n8n",
  "LangChain"
]
```

#### `softSkills` — Competências Comportamentais

| Campo | Tipo       | Descrição                                        |
| ----- | ---------- | ------------------------------------------------ |
|       | `string[]` | Liderança, comunicação, trabalho em equipe, etc. |

**Exemplo:**

```json
["Liderança", "Inovação técnica", "Transformação Digital", "Hands-on"]
```

#### `experience[]` — Experiências Profissionais

| Campo                 | Tipo           | Descrição                                         |
| --------------------- | -------------- | ------------------------------------------------- |
| `company`             | `string`       | Nome da empresa/organização                       |
| `role`                | `string`       | Cargo/função exercida                             |
| `location`            | `string\|null` | Cidade, Estado ou "Remoto"                        |
| `startDate`           | `string\|null` | Data início no formato `YYYY-MM`                  |
| `endDate`             | `string\|null` | Data término `YYYY-MM` ou `null` se atual         |
| `isCurrentRole`       | `boolean`      | `true` se é o emprego atual                       |
| `originalDescription` | `string`       | **Texto integral** das atividades. Não sumarizar. |

**Exemplo:**

```json
{
  "company": "SmartPace",
  "role": "Arquiteto de Soluções & Product Manager (Founder)",
  "location": "São Paulo - SP",
  "startDate": "2026-01",
  "endDate": null,
  "isCurrentRole": true,
  "originalDescription": "Motor Anti-Fraude: Sistema inviolável com geolocalização (Geofence), sincronização NTP, Liveness Detection (Google ML Kit) e fila offline (SQLite/Hive). UX/UI com IA: Design System com comandos de IA na tela inicial..."
}
```

#### `education[]` — Formação Acadêmica

| Campo         | Tipo           | Descrição                           |
| ------------- | -------------- | ----------------------------------- |
| `institution` | `string`       | Nome da universidade/instituição    |
| `degree`      | `string`       | Nível (Graduação, MBA, Mestrado...) |
| `field`       | `string\|null` | Área de estudo                      |
| `startDate`   | `string\|null` | Ano de início `YYYY`                |
| `endDate`     | `string\|null` | Ano de conclusão `YYYY`             |

**Exemplo:**

```json
{
  "institution": "Instituto Vianna Júnior",
  "degree": "Graduação",
  "field": "Análise e Desenvolvimento de Sistemas",
  "startDate": "1999",
  "endDate": "2004"
}
```

#### `certifications[]` — Cursos e Certificações

| Campo         | Tipo           | Descrição                                   |
| ------------- | -------------- | ------------------------------------------- |
| `name`        | `string`       | Nome do curso ou certificação               |
| `institution` | `string`       | Instituição emissora (Rocketseat, Udemy...) |
| `description` | `string\|null` | Breve descrição do conteúdo                 |
| `year`        | `string\|null` | Ano de obtenção `YYYY`                      |

**Exemplo:**

```json
[
  {
    "name": "GoStack",
    "institution": "Rocketseat",
    "description": "React, React Native, Node.js e TypeScript",
    "year": null
  },
  {
    "name": "Fast MBA",
    "institution": "",
    "description": "Empreendedorismo, Negócios e Startups (Foco em produto e ROI)",
    "year": null
  }
]
```

#### `languages[]` — Idiomas

| Campo      | Tipo     | Descrição                  |
| ---------- | -------- | -------------------------- |
| `language` | `string` | Nome do idioma             |
| `level`    | `string` | Nível (Nativo, Fluente...) |

**Exemplo:**

```json
[
  { "language": "Português", "level": "Nativo" },
  { "language": "English", "level": "Intermediário" }
]
```

---

## 📡 Endpoints REST

### 1. Upload de CV

**POST** `/api/v1/cv/upload`

Extrai e analisa um CV em PDF.

#### Request

- **Content-Type:** `multipart/form-data`
- **Body:**

| Campo    | Tipo   | Obrigatório | Descrição                     |
| -------- | ------ | ----------- | ----------------------------- |
| `userId` | string | ✅          | ID do usuário                 |
| `file`   | file   | ✅          | Arquivo PDF do CV (máx. 10MB) |

#### Exemplo cURL

```bash
curl -X POST http://localhost:3000/api/v1/cv/upload \
  -F "userId=ef892439-8b37-434d-b0ed-e5a0d37d6985" \
  -F "file=@/caminho/do/cv.pdf"
```

#### Response (200 OK)

```json
{
  "data": {
    "props": {
      "id": "9637b58d-932a-4722-965a-51926eb23b2f",
      "userId": "ef892439-8b37-434d-b0ed-e5a0d37d6985",
      "fileUrl": "",
      "rawText": "JOSÉ ROBERTO MIGUEL FILHO\nDesenvolvedor FullStack...",
      "personalData": {
        "fullName": "José Roberto Miguel Filho",
        "email": "joseroberto.toko@gmail.com",
        "phone": "+55 11 97085-9171",
        "location": "São Paulo - SP",
        "links": ["https://linkedin.com/in/tokodev"]
      },
      "summary": "Desenvolvedor Full Stack Sênior com 22+ anos de experiência...",
      "hardSkills": [
        "ReactJS",
        "Next.js",
        "TypeScript",
        "Node.js",
        "NestJS",
        "Flutter",
        "PostgreSQL",
        "AWS",
        "Docker",
        "n8n",
        "LangChain"
      ],
      "softSkills": ["Liderança", "Inovação técnica", "Transformação Digital"],
      "languages": [],
      "experience": [
        {
          "company": "Village",
          "role": "Líder de Transformação Digital (PJ)",
          "location": "São Paulo - SP (Híbrido)",
          "startDate": "2025-05",
          "endDate": "2026-03",
          "isCurrentRole": false,
          "originalDescription": "Logística Inteligente: Sistema de abastecimento dinâmico..."
        },
        {
          "company": "SmartPace",
          "role": "Arquiteto de Soluções & Product Manager (Founder)",
          "location": "São Paulo - SP",
          "startDate": "2026-01",
          "endDate": null,
          "isCurrentRole": true,
          "originalDescription": "Motor Anti-Fraude: Sistema inviolável com geolocalização..."
        }
      ],
      "education": [
        {
          "institution": "Instituto Vianna Júnior",
          "degree": "Graduação",
          "field": "Análise e Desenvolvimento de Sistemas",
          "startDate": "1999",
          "endDate": "2004"
        }
      ],
      "certifications": [
        {
          "name": "GoStack",
          "institution": "Rocketseat",
          "description": "React, React Native, Node.js e TypeScript",
          "year": null
        },
        {
          "name": "AWS Cloud",
          "institution": "",
          "description": "Arquitetura e implementação de infraestrutura Cloud",
          "year": null
        },
        {
          "name": "Fast MBA",
          "institution": "",
          "description": "Empreendedorismo, Negócios e Startups",
          "year": null
        }
      ],
      "processingTimeMs": 28416,
      "status": "completed",
      "createdAt": "2026-04-06T08:31:54.345Z",
      "updatedAt": "2026-04-06T08:31:54.345Z"
    }
  }
}
```

### 2. Listar CVs de um Usuário

**GET** `/api/v1/cv/user/:userId`

#### Response (200 OK)

```json
{
  "data": [
    {
      "id": "9637b58d-932a-4722-965a-51926eb23b2f",
      "userId": "ef892439-8b37-434d-b0ed-e5a0d37d6985",
      "personalData": {
        "fullName": "José Roberto Miguel Filho",
        "email": "joseroberto.toko@gmail.com"
      },
      "status": "completed",
      "createdAt": "2026-04-06T08:31:54.345Z"
    }
  ]
}
```

### 3. Buscar CV por ID

**GET** `/api/v1/cv/:id`

Retorna os detalhes completos de um CV processado.

---

## ⚙️ Configuração

### Variáveis de Ambiente

```env
# --- IA & LLM (via LiteLLM) ---
LITELLM_URL="http://localhost:4000"
LITELLM_API_KEY="sk-litellm-getjobs-2026-master-key"

# --- Fallback Ollama ---
CV_ANALYSIS_FALLBACK=enabled
OLLAMA_HOST="http://localhost:11434"
OLLAMA_MODEL="qwen2.5:7b"

# --- Webhook Supabase (sync de usuários) ---
SUPABASE_WEBHOOK_SECRET="whsec_..."
```

### Dependências do Sistema

| Dependência       | Instalação                       | Uso                             |
| ----------------- | -------------------------------- | ------------------------------- |
| **poppler-utils** | `sudo apt install poppler-utils` | `pdftotext` (extração primária) |
| **LiteLLM**       | Docker container                 | Proxy de modelos IA             |
| **Ollama**        | `ollama pull qwen2.5:7b`         | Fallback local                  |

---

## 🔧 Regras de Extração

O prompt de análise segue **4 regras críticas**:

| #   | Regra                      | Descrição                                                                                        |
| --- | -------------------------- | ------------------------------------------------------------------------------------------------ |
| 1   | **Fidelidade ao Texto**    | Não melhorar, não resumir e não traduz descrições. Manter texto **exatamente** como no original. |
| 2   | **Independência de Cargo** | Identificar blocos de experiência e educação independentemente da profissão.                     |
| 3   | **Tratamento de Datas**    | Converter para `YYYY-MM`. "Presente"/"Atualmente"/"Present" → `null` + `isCurrentRole: true`.    |
| 4   | **Campos Obrigatórios**    | Se informação não existir → `null` ou `[]`. **Nunca inventar dados.**                            |

---

## 🛡️ Retry e Fallback

O serviço `CVAnalysisService` implementa:

1. **3 retries** com backoff exponencial (1s → 2s → 4s, máx 10s)
2. **Detecção inteligente** de erros retryable (503, timeout, UNAVAILABLE)
3. **Falha imediata** para erros não-retryable (400 bad request)
4. **Fallback Ollama** se todos os retries do LiteLLM falharem
5. **Agregação de erros** — mensagem inclui falhas de ambos Gemini e Ollama

---

## 📊 Modelo de Dados (Prisma)

### Tabela: `CandidateResume`

| Coluna             | Tipo       | Descrição                                         |
| ------------------ | ---------- | ------------------------------------------------- |
| `id`               | `String`   | UUID primário                                     |
| `userId`           | `String`   | FK → User                                         |
| `fileUrl`          | `String`   | URL do arquivo                                    |
| `rawText`          | `Text`     | Texto bruto extraído do PDF                       |
| `fullName`         | `String`   | Nome completo (de `personalData.fullName`)        |
| `email`            | `String`   | Email (de `personalData.email`)                   |
| `phone`            | `String`   | Telefone (de `personalData.phone`)                |
| `location`         | `String`   | Localização (de `personalData.location`)          |
| `links`            | `Json`     | Array de URLs de perfis                           |
| `summary`          | `Text`     | Resumo profissional bruto                         |
| `hardSkills`       | `String[]` | Lista de skills técnicos                          |
| `softSkills`       | `String[]` | Lista de competências comportamentais             |
| `languages`        | `Json`     | Array de `{language, level}`                      |
| `experience`       | `Json`     | Array de experiências completas                   |
| `education`        | `Json`     | Array de formações acadêmicas                     |
| `certifications`   | `Json`     | Array de `{name, institution, description, year}` |
| `processingTimeMs` | `Int`      | Tempo de processamento em ms                      |
| `status`           | `String`   | `pending`, `processing`, `completed`, `failed`    |
| `createdAt`        | `DateTime` | Data de criação                                   |
| `updatedAt`        | `DateTime` | Última atualização                                |

---

## 🧪 Testes

### Testes Unitários

```bash
npm run test -- --run src/domain/cv-extraction
```

### Teste Manual com CV Real

```bash
curl -X POST http://localhost:3000/api/v1/cv/upload \
  -F "userId=SEU_USER_ID" \
  -F "file=@/caminho/do/cv.pdf" | python3 -m json.tool
```

---

## 🚀 Próximos Passos (Fase 2)

1. **Análise de Match** — Comparar CV extraído com vagas disponíveis
2. **Enriquecimento de Dados** — IA analisa e estrutura informações para melhor matching
3. **Sugestões de Melhoria** — Feedback automático no CV
4. **Suporte a múltiplos formatos** — DOCX, TXT, RTF
5. **Versionamento de CVs** — Histórico de uploads e evolução do perfil
