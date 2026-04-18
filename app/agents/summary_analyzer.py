import json
import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from app.core.settings import get_settings

logger = logging.getLogger("summary_analyzer")
settings = get_settings()

class SummaryInsight(BaseModel):
    suggestedSummary: str = Field(description="Novo resumo profissional sugerido em Markdown")
    pros: List[str] = Field(description="Pontos fortes do perfil atual")
    cons: List[str] = Field(description="Pontos de melhoria do perfil atual")
    tone: str = Field(description="Tom de voz da sugestão")

class SummaryAnalyzerAgent:
    def __init__(self):
        self.chat = ChatOpenAI(
            base_url=settings.LITELLM_URL,
            api_key=settings.LITELLM_API_KEY,
            model=settings.CV_ANALYSIS_MODEL,
            temperature=0.7,
            max_tokens=4000
        )

    def analyze(self, data: Dict[str, Any]) -> SummaryInsight:
        logger.info(f"Analisando resumo para o usuário {data.get('userId')}")
        
        full_name = data.get("fullName", "Candidato")
        current_summary = data.get("currentSummary", "")
        skills = ", ".join(data.get("hardSkills", []))
        
        experiences_raw = data.get("experiences", [])
        experiences_text = "\n".join([
            f"- {e.get('role')} na {e.get('company')}: {e.get('description')}" 
            for e in experiences_raw
        ])

        system_prompt = """
        Você é um Tech Recruiter Sênior e especialista em carreira. 
        Sua missão é analisar as competências e experiências de um profissional de tecnologia e fornecer um feedback honesto (Prós e Contras) 
        além de sugerir um NOVO Resumo Profissional de alto impacto formatado em Markdown.

        Regras para o NOVO Resumo (suggestedSummary):
        - Use Markdown (negrito para tecnologias, títulos se necessário).
        - Foque em RESULTADOS e não apenas em responsabilidades.
        - Use verbos de ação poderosos.
        - Seja conciso e direto.
        - Retorne o texto pronto para ser copiado.

        Retorne ESTRITAMENTE um JSON seguindo este esquema:
        {
          "suggestedSummary": "Texto em Markdown...",
          "pros": ["ponto 1", "ponto 2"],
          "cons": ["melhoria 1", "melhoria 2"],
          "tone": "Profissional/Sênior"
        }
        """

        user_content = f"""
        Candidato: {full_name}
        Skills: {skills}
        Resumo Atual: {current_summary}
        
        Experiências Recentes:
        {experiences_text}
        """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_content)
        ]

        try:
            response = self.chat.invoke(messages)
            print(f"[DEBUG] Resposta Bruta da IA: {response.content}")
            content = response.content
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            raw_json = json.loads(content.strip())
            return SummaryInsight.model_validate(raw_json)
        except Exception as e:
            logger.error(f"Erro ao analisar resumo: {str(e)}")
            raise e
