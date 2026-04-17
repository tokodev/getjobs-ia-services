# Dify Workflow — Análise de CV

## 🎯 Objetivo

Extrair informações estruturadas de um CV em texto bruto (extraído via StirlingPDF) e retornar JSON padronizado.

---

## 📋 Criar o Workflow no Dify

### 1. Acessar o Dify

```
URL: http://localhost:5001
Login: sua conta admin
```

### 2. Criar Novo Workflow

1. **Studio** → **Create** → **Workflow**
2. Nome: `CV Analysis`
3. Descrição: `Extracts structured data from CV text for GetJobs`

### 3. Configurar os Nós

#### Nó 1: Start (Input)

| Campo             | Valor     |
| ----------------- | --------- |
| **Variable Name** | `cv_text` |
| **Type**          | Paragraph |
| **Required**      | ✅ Sim    |
| **Max Length**    | 50000     |

#### Nó 2: LLM (Análise IA)

| Campo               | Valor                        |
| ------------------- | ---------------------------- |
| **Model**           | `LiteLLM / gemini-2.5-flash` |
| **Temperature**     | `0.3`                        |
| **Response Format** | JSON                         |
| **Max Tokens**      | `4096`                       |

**System Prompt:**

```
You are an expert CV parser. Your task is to extract structured information from CV text and return it as a JSON object.

Rules:
- Return ONLY valid JSON, no markdown, no additional text
- If a field is not found, use null or empty array []
- Dates should be in YYYY-MM format when possible
- Extract ALL skills mentioned (both technical and soft skills)
- aiConfidence should be 0.0 to 1.0 based on data completeness and clarity
- Languages: include level as Native, Fluent, Intermediate, or Basic
- For experience endDate, use "Present" if currently employed
```

**User Prompt:**

```
Analyze the following CV text and extract all information into a JSON object:

{{#cv_text#}}

Return ONLY this JSON structure:
{
  "fullName": "Full name of the candidate",
  "email": "email@example.com",
  "phone": "+55 11 99999-9999",
  "location": "City, State, Country",
  "summary": "Professional summary in 2-3 sentences",
  "hardSkills": ["React", "Node.js", "TypeScript"],
  "softSkills": ["Leadership", "Communication"],
  "languages": [
    {"language": "Portuguese", "level": "Native"},
    {"language": "English", "level": "Fluent"}
  ],
  "experience": [
    {
      "company": "Company Name",
      "role": "Job Title",
      "startDate": "2020-01",
      "endDate": "2024-06",
      "description": "Brief description of responsibilities and achievements"
    }
  ],
  "education": [
    {
      "institution": "University Name",
      "degree": "Bachelor/Master/PhD in Field",
      "year": "2019"
    }
  ],
  "certifications": ["AWS Certified Developer", "Scrum Master"],
  "aiConfidence": 0.92
}
```

#### Nó 3: End (Output)

| Campo               | Valor            |
| ------------------- | ---------------- |
| **Output Variable** | `result`         |
| **Type**            | String           |
| **Value**           | Output do nó LLM |

### 4. Publicar e Obter Credenciais

1. Clique em **Publish**
2. Vá em **API Access** (menu lateral ou botão Publish → API)
3. Copie:
   - **API Key**: `app-xxxxxxxxxxxxxxxxxxxxxxxx`
   - **Workflow ID**: aparece na URL ou na seção API

---

## 🔧 Configurar na API

### .env da API

```env
# --- Dify ---
DIFY_API_URL=http://localhost:5001/v1
DIFY_API_KEY=app-xxxxx
DIFY_WORKFLOW_CV_ANALYSIS=seu-workflow-id
```

---

## 🧪 Testar o Workflow

```bash
curl http://localhost:5001/v1/workflows/run \
  -H "Authorization: Bearer app-xxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {
      "cv_text": "João Silva\njoao@email.com\n+55 11 99999-9999\nSão Paulo, SP\n\nDesenvolvedor Senior com 5 anos de experiência em React, Node.js e TypeScript.\n\nExperiência:\nTechCorp - Senior Developer (2020-01 até 2024-06)\n- Desenvolvimento de aplicações web\n- Liderança técnica de equipe de 5 devs\n\nFormação:\nUSP - Bacharelado em Ciência da Computação (2019)\n\nCertificações:\nAWS Certified Developer\nScrum Master"
    },
    "response_mode": "blocking",
    "user": "getjobs-worker"
  }'
```

### Resposta Esperada

```json
{
  "data": {
    "outputs": {
      "result": "{\"fullName\":\"João Silva\",\"email\":\"joao@email.com\",\"phone\":\"+55 11 99999-9999\",\"location\":\"São Paulo, SP\",\"summary\":\"Desenvolvedor Senior com 5 anos de experiência...\",\"hardSkills\":[\"React\",\"Node.js\",\"TypeScript\"],\"softSkills\":[\"Liderança\"],\"languages\":[],\"experience\":[{\"company\":\"TechCorp\",\"role\":\"Senior Developer\",\"startDate\":\"2020-01\",\"endDate\":\"2024-06\",\"description\":\"Desenvolvimento de aplicações web...\"}],\"education\":[{\"institution\":\"USP\",\"degree\":\"Bacharelado em Ciência da Computação\",\"year\":\"2019\"}],\"certifications\":[\"AWS Certified Developer\",\"Scrum Master\"],\"aiConfidence\":0.85}"
    }
  }
}
```
