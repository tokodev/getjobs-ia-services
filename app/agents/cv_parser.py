from langsmith import traceable
from litellm import completion
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from app.core.logging_setup import setup_json_logging

logger = setup_json_logging("cv_parser")

class PersonalData(BaseModel):
    fullName: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    links: List[str] = []

class Experience(BaseModel):
    company: str
    role: str
    location: str | None = None
    startDate: str | None = None
    endDate: str | None = None
    isCurrentRole: bool = False
    originalDescription: str

class ParsedCV(BaseModel):
    personalData: PersonalData
    summary: str | None = None
    hardSkills: List[str] = []
    softSkills: List[str] = []
    experience: List[Experience] = []
    education: List[Dict[str, Any]] = []
    certifications: List[Dict[str, Any]] = []
    languages: List[Dict[str, str]] = []
    aiConfidence: float = 0.0

class CVParserAgent:
    def __init__(self):
        self.model = "cv-parser-delegate" # Nome definido no config.yaml do LiteLLM

    @traceable(run_type="chain", name="CV Parser")
    def parse(self, cv_text: str) -> ParsedCV:
        """
        Analisa o texto de um CV e o converte em JSON estruturado seguindo o schema ParsedCV.
        """
        prompt = (
            "Analyze the following CV text and extract all information into a JSON object strictly following the schema. "
            "Return 'aiConfidence' as a float between 0 and 1 representing your confidence in the extraction.\n\n"
            f"CV Text:\n{cv_text}"
        )
        
        response = completion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        # O LiteLLM retorna a resposta em JSON
        content = response.choices[0].message.content
        result = ParsedCV.model_validate_json(content)
        
        # Log de decisão estruturado (Loki)
        logger.info(
            "CV Decision Log",
            extra={
                "model_used": response.get("model", self.model),
                "ai_confidence": result.aiConfidence,
                "usage": response.get("usage", {}),
                "agent": "CVParserAgent"
            }
        )
        
        return result
