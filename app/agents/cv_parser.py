import json
import logging
import re
from typing import Dict, Any, List, Set
from pydantic import BaseModel, Field
from langsmith import traceable
from litellm import completion
from app.core.logging_setup import setup_json_logging
from app.core.settings import get_settings
from app.prompts.cv_analysis import CV_ANALYSIS_PROMPT

logger = setup_json_logging("cv_parser")
settings = get_settings()

# --- Schemas ---

class Location(BaseModel):
    city: str | None = None
    state: str | None = None
    country: str | None = None
    workRegime: str | None = None
    availability: str | None = None

class Links(BaseModel):
    linkedin: str | None = None
    github: str | None = None
    portfolio: str | None = None
    website: str | None = None

class PersonalData(BaseModel):
    fullName: str | None = None
    email: str | None = None
    phone: str | None = None
    location: Location = Field(default_factory=Location)
    links: Links = Field(default_factory=Links)

class Experience(BaseModel):
    company: str
    role: str
    location: str | None = None
    startDate: str | None = None
    endDate: str | None = None
    isCurrentRole: bool = False
    originalDescription: str

class Education(BaseModel):
    institution: str
    degree: str
    field: str | None = None
    startDate: str | None = None
    endDate: str | None = None

class Certification(BaseModel):
    name: str
    issuer: str
    credentialId: str | None = None
    credentialUrl: str | None = None
    issueDate: str | None = None
    expiryDate: str | None = None

class Course(BaseModel):
    name: str
    institution: str
    description: str | None = None
    year: str | None = None

class Project(BaseModel):
    name: str
    description: str | None = None
    url: str | None = None
    technologies: List[str] = []

class Award(BaseModel):
    title: str
    issuer: str | None = None
    date: str | None = None
    description: str | None = None

class Language(BaseModel):
    language: str
    level: str

class TechStack(BaseModel):
    frontend: List[str] = []
    backend: List[str] = []
    mobile: List[str] = []
    cloud: List[str] = []
    databases: List[str] = []
    devops: List[str] = []
    other: List[str] = []

class ParsedCV(BaseModel):
    personalData: PersonalData
    summary: str | None = None
    hardSkills: List[str] = []
    softSkills: List[str] = []
    techStack: TechStack = Field(default_factory=TechStack)
    experience: List[Experience] = []
    education: List[Education] = []
    certifications: List[Certification] = []
    courses: List[Course] = []
    projects: List[Project] = []
    awards: List[Award] = []
    languages: List[Language] = []
    aiConfidence: float = 0.0

# --- Agent ---

class CVParserAgent:
    def __init__(self):
        self.model = "cv-parser-delegate"
        self.fallback_model = "ollama/llama3" # Exemplo de fallback

    @traceable(run_type="chain", name="CV Parser")
    def parse(self, cv_text: str) -> ParsedCV:
        """
        Analisa o texto de um CV e o converte em JSON estruturado com normalização.
        """
        try:
            return self._call_llm(cv_text, self.model)
        except Exception as e:
            logger.warning(f"Primary model failed: {str(e)}. Attempting fallback...")
            return self._call_llm(cv_text, self.fallback_model)

    def _call_llm(self, cv_text: str, model: str) -> ParsedCV:
        response = completion(
            model=model,
            messages=[
                {"role": "system", "content": CV_ANALYSIS_PROMPT},
                {"role": "user", "content": f"CV TEXT TO ANALYZE:\n\n{cv_text}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            num_retries=3
        )
        
        content = response.choices[0].message.content
        raw_data = json.loads(content)
        
        normalized_data = self.normalize_cv_data(raw_data, cv_text)
        result = ParsedCV.model_validate(normalized_data)
        
        # Atribui confiança baseada no preenchimento de campos essenciais
        result.aiConfidence = self._calculate_confidence(result)
        
        return result

    def normalize_cv_data(self, raw: Dict[str, Any], raw_text: str) -> Dict[str, Any]:
        """
        Portabilidade da lógica de normalização do NestJS.
        """
        raw_text_lower = raw_text.toLowerCase() if hasattr(raw_text, 'toLowerCase') else raw_text.lower()

        def normalize_date(date_str: str | None) -> str | None:
            if not date_str: return None
            lower = date_str.lower()
            if any(x in lower for x in ["present", "atual", "presente", "atualmente"]):
                return None
            return date_str

        # --- Personal Data & Location ---
        loc = raw.get("personalData", {}).get("location", {})
        if isinstance(loc, str):
            parts = [p.strip() for p in re.split(r'[-–,]', loc)]
            loc = {"city": parts[0] if len(parts) > 0 else None, "state": parts[1] if len(parts) > 1 else None}
        
        # Validação de regime de trabalho e país (lógica NestJS)
        work_regime = loc.get("workRegime")
        if work_regime and work_regime.lower() not in raw_text_lower:
            work_regime = None # Só aceita se estiver no texto original

        # --- Skills Filtering ---
        hard_skills = raw.get("hardSkills", [])
        soft_skills = raw.get("softSkills", [])
        
        education_keywords = ["graduação", "bacharelado", "mestrado", "doutorado", "mba", "universidade", "faculdade"]
        soft_keywords = ["liderança", "comunicação", "trabalho em equipe", "resolução", "gestão", "liderança", "teamwork", "leadership"]

        filtered_hard = []
        seen = set()
        for s in hard_skills:
            if not isinstance(s, str): continue
            s_low = s.lower()
            if any(k in s_low for k in education_keywords): continue
            if any(k in s_low for k in soft_keywords): 
                if s not in soft_skills: soft_skills.append(s)
                continue
            if len(s) > 80: continue
            
            clean_s = s.strip()
            if clean_s.lower() not in seen:
                filtered_hard.append(clean_s)
                seen.add(clean_s.lower())

        # --- Tech Stack Auto-Categorization ---
        tech_stack = raw.get("techStack", {})
        if not any(tech_stack.values()):
            tech_stack = self.auto_categorize_tech_stack(filtered_hard[:25])

        # --- Final Object Assembly ---
        normalized = {
            "personalData": {
                "fullName": raw.get("personalData", {}).get("fullName") or raw.get("fullName"),
                "email": (raw.get("personalData", {}).get("email") or raw.get("email", "")).replace(" ", ""),
                "phone": raw.get("personalData", {}).get("phone") or raw.get("phone"),
                "location": {
                    "city": loc.get("city"),
                    "state": loc.get("state"),
                    "country": loc.get("country") if "brasil" in raw_text_lower or "brazil" in raw_text_lower else None,
                    "workRegime": work_regime,
                    "availability": loc.get("availability")
                },
                "links": raw.get("personalData", {}).get("links") or raw.get("links", {})
            },
            "summary": raw.get("summary"),
            "hardSkills": filtered_hard[:20],
            "softSkills": soft_skills[:15],
            "techStack": tech_stack,
            "experience": [
                {
                    **exp,
                    "startDate": normalize_date(exp.get("startDate")),
                    "endDate": (norm_end := normalize_date(exp.get("endDate"))),
                    "isCurrentRole": exp.get("isCurrentRole") or norm_end is None
                } for exp in raw.get("experience", [])
            ],
            "education": raw.get("education", []),
            "certifications": raw.get("certifications", []),
            "courses": raw.get("courses", []),
            "projects": raw.get("projects", []),
            "awards": raw.get("awards", []),
            "languages": [l for l in raw.get("languages", []) if l.get("language", "").lower() in raw_text_lower]
        }
        
        return normalized

    def auto_categorize_tech_stack(self, skills: List[str]) -> Dict[str, List[str]]:
        ts = {"frontend": [], "backend": [], "mobile": [], "cloud": [], "databases": [], "devops": [], "other": []}
        
        categories = [
            ("frontend", ["react", "vue", "angular", "next.js", "html", "css", "tailwind", "styled-components"]),
            ("backend", ["node.js", "python", "php", "java", "ruby", "golang", "c#", ".net", "nestjs", "fastapi"]),
            ("mobile", ["react native", "flutter", "swift", "kotlin", "ionic"]),
            ("cloud", ["aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "lambda"]),
            ("databases", ["postgresql", "mysql", "mongodb", "redis", "oracle", "sql server", "dynamodb"]),
            ("devops", ["git", "ci/cd", "jenkins", "terraform", "ansible", "github actions"])
        ]

        for skill in skills:
            low = skill.lower()
            categorized = False
            for key, keywords in categories:
                if any(k in low for k in keywords):
                    ts[key].append(skill)
                    categorized = True
                    break
            if not categorized:
                ts["other"].append(skill)
        return ts

    def _calculate_confidence(self, result: ParsedCV) -> float:
        score = 0.0
        if result.personalData.fullName: score += 0.2
        if result.personalData.email: score += 0.1
        if result.experience: score += 0.3
        if result.education: score += 0.2
        if result.hardSkills: score += 0.2
        return min(score, 1.0)
