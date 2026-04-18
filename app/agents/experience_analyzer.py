import json
import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from app.core.settings import get_settings

logger = logging.getLogger("experience_analyzer")
settings = get_settings()

class ExperienceInsight(BaseModel):
    suggestedDescription: str = Field(description="Nova descrição sugerida em Markdown usando STAR/XYZ")
    technicalAnalysis: str = Field(description="Análise técnica profunda da descrição original")
    pros: List[str] = Field(description="Pontos fortes destacados")
    cons: List[str] = Field(description="Oportunidades de melhoria")
    actionableFeedback: str = Field(description="Conselho prático para o candidato")

class ExperienceAnalyzerAgent:
    def __init__(self):
        self.chat = ChatOpenAI(
            base_url=settings.LITELLM_URL,
            api_key=settings.LITELLM_API_KEY,
            model=settings.CV_ANALYSIS_MODEL,
            temperature=0.3,
            max_tokens=4000
        )

    def analyze(self, data: Dict[str, Any]) -> ExperienceInsight:
        logger.info(f"Analisando experiência profissional para o usuário {data.get('userId')}")
        
        role = data.get("role", "Não informado")
        company = data.get("company", "Não informado")
        description = data.get("description", "")
        skills_context = ", ".join(data.get("hardSkills", []))

        system_prompt = """
        Você é um Especialista em Currículos de Tecnologia (Senior Tech Recruiter).
        Sua missão é analisar uma EXPERIÊNCIA PROFISSIONAL específica e fornecer um feedback técnico.

        Regras de Otimização:
        - Use o método STAR (Situação, Tarefa, Ação, Resultado) ou XYZ (Fez X, medido por Y, resultando em Z).
        - Foque em tecnologias e IMPACTO no negócio.
        - Sugira uma descrição formatada em Markdown (lista com bullets).
        - Identifique tecnologias que o candidato usou mas descreveu mal.

        Retorne ESTRITAMENTE um JSON seguindo este esquema:
        {
          "suggestedDescription": "Lista em markdown...",
          "technicalAnalysis": "O candidato demonstra domínio em X, mas...",
          "pros": ["uso de stack moderna", "papel de liderança"],
          "cons": ["falta de métricas", "descrição genérica"],
          "actionableFeedback": "Adicione quantos usuários o sistema atendia..."
        }
        """

        user_content = f\"\"\"
        Empresa: {company}
        Cargo: {role}
        Descrição Atual: {description}
        Skills do Candidato: {skills_context}
        \"\"\"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_content)
        ]

        try:
            response = self.chat.invoke(messages)
            content = response.content
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            raw_json = json.loads(content.strip())
            return ExperienceInsight.model_validate(raw_json)
        except Exception as e:
            logger.error(f"Erro ao analisar experiência: {str(e)}")
            raise e
