import json
import logging
import re
from typing import Dict, Any, List, Set
from pydantic import BaseModel, Field
from langsmith import traceable
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
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
        model_name = settings.CV_ANALYSIS_MODEL
        
        if "gemini" in model_name.lower():
            logger.info(f"Usando motor GOOGLE nativo para modelo: {model_name}")
            self.chat = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.1,
                max_output_tokens=8192,
                convert_system_message_to_human=True
            )
        else:
            logger.info(f"Usando motor OPENAI (LiteLLM) para modelo: {model_name}")
            self.chat = ChatOpenAI(
                base_url=settings.LITELLM_URL,
                api_key=settings.LITELLM_API_KEY,
                model=model_name,
                temperature=0.1,
                max_tokens=8000,
                model_kwargs={"response_format": {"type": "json_object"}}
            )

    @traceable(run_type="chain", name="CV Parser")
    def parse(self, cv_text: str) -> ParsedCV:
        logger.info(f"Iniciando extração. Texto: {len(cv_text)} chars.")
        
        messages = [
            SystemMessage(content=CV_ANALYSIS_PROMPT),
            HumanMessage(content=f"CV TEXT TO ANALYZE:\n\n{cv_text}")
        ]
        
        try:
            response = self.chat.invoke(messages)
            content = response.content
            
            # Limpeza robusta de blocos de código
            content = re.sub(r"```json\s*", "", content)
            content = re.sub(r"```\s*", "", content)
            content = content.strip()
            
            # Se for Gemini e não estiver em JSON mode, pode vir texto extra. 
            # Tentamos encontrar o primeiro { e o último }
            if not content.startswith("{"):
                match = re.search(r"({.*})", content, re.DOTALL)
                if match:
                    content = match.group(1)

            raw_data = json.loads(content)
            normalized_data = self.normalize_cv_data(raw_data, cv_text or "")
            
            result = ParsedCV.model_validate(normalized_data)
            result.aiConfidence = self._calculate_confidence(result)
            
            return result
        except Exception as e:
            logger.error(f"Erro no CVParserAgent: {str(e)}")
            raise e

    def normalize_cv_data(self, raw: Dict[str, Any], raw_text: str) -> Dict[str, Any]:
        raw_text_lower = (raw_text or "").lower()

        def normalize_date(date_str: Any) -> str | None:
            if not date_str: return None
            lower = str(date_str).lower()
            if any(x in lower for x in ["present", "atual", "presente", "atualmente"]):
                return None
            return str(date_str)

        # --- Personal Data ---
        p_raw = raw.get("personalData") or raw or {}
        
        # Links
        l_raw = p_raw.get("links") or raw.get("links") or {}
        links = {
            "linkedin": l_raw.get("linkedin") or l_raw.get("LinkedIn"),
            "github": l_raw.get("github") or l_raw.get("GitHub"),
            "portfolio": l_raw.get("portfolio"),
            "website": l_raw.get("website") or l_raw.get("personalWebsite")
        }

        # Location
        loc_raw = p_raw.get("location") or raw.get("location") or {}
        if isinstance(loc_raw, str):
            parts = [p.strip() for p in re.split(r'[-–,]', loc_raw)]
            loc = {"city": parts[0] if len(parts) > 0 else None, "state": parts[1] if len(parts) > 1 else None}
        else:
            loc = loc_raw

        # --- Skills ---
        hard_skills = raw.get("hardSkills") or raw.get("skills") or []
        soft_skills = raw.get("softSkills") or []
        
        edu_keywords = ["graduação", "bacharelado", "licenciatura", "tecnólogo", "mestrado", "doutorado", "mba", "pós-graduação", "técnico"]
        soft_keywords = ["liderança", "leadership", "comunicação", "communication", "trabalho em equipe", "teamwork", "resolução", "gestão", "planning"]

        filtered_hard = []
        seen = set()
        for s in (hard_skills if isinstance(hard_skills, list) else []):
            if not s or not isinstance(s, str) or len(s) > 80: continue
            s_low = s.lower()
            if any(k in s_low for k in edu_keywords): continue
            if any(k in s_low for k in soft_keywords):
                if s not in soft_skills: soft_skills.append(s)
                continue
            if s_low not in seen:
                filtered_hard.append(s.strip())
                seen.add(s_low)

        # --- Tech Stack ---
        tech_stack = raw.get("techStack") or raw.get("technologyStack") or {}
        if not isinstance(tech_stack, dict) or not any(tech_stack.values()):
            tech_stack = self.auto_categorize_tech_stack(filtered_hard[:25])

        # --- Normalização das Listas ---
        def get_v(obj, *keys, default=None):
            for k in keys:
                if k in obj: return obj[k]
            return default

        experience = []
        for exp in (raw.get("experience") or raw.get("experiences") or []):
            end_date = normalize_date(get_v(exp, "endDate", "end_date", "fim"))
            experience.append({
                "company": get_v(exp, "company", "organization", "empresa", default=""),
                "role": get_v(exp, "role", "position", "cargo", "title", default=""),
                "location": get_v(exp, "location", "local"),
                "startDate": normalize_date(get_v(exp, "startDate", "start_date", "inicio")),
                "endDate": end_date,
                "isCurrentRole": bool(get_v(exp, "isCurrentRole", "is_current") or end_date is None),
                "originalDescription": get_v(exp, "originalDescription", "description", "atividades", default="")
            })

        education = []
        raw_edu_list = raw.get("education") or raw.get("educations") or []
        if not raw_edu_list:
            education = self._extract_education_fallback(raw_text)
        else:
            for edu in raw_edu_list:
                education.append({
                    "institution": get_v(edu, "institution", "university", "school", "faculdade", default=""),
                    "degree": get_v(edu, "degree", "course", "formacao", default=""),
                    "field": get_v(edu, "field", "area"),
                    "startDate": normalize_date(get_v(edu, "startDate", "start_date")),
                    "endDate": normalize_date(get_v(edu, "endDate", "end_date", "year"))
                })

        languages = []
        for l in (raw.get("languages") or raw.get("language") or []):
            lang_name = get_v(l, "language", "name", "idioma", default="")
            if lang_name.lower() in raw_text_lower:
                languages.append({
                    "language": lang_name,
                    "level": get_v(l, "level", "proficiency", "nivel", default="")
                })

        # --- Objeto Final ---
        normalized = {
            "personalData": {
                "fullName": get_v(p_raw, "fullName", "fullName", "name", "nome"),
                "email": str(get_v(p_raw, "email", "email", default="")).replace(" ", ""),
                "phone": get_v(p_raw, "phone", "phone", "telefone"),
                "location": {
                    "city": loc.get("city"),
                    "state": loc.get("state"),
                    "country": loc.get("country") if any(x in raw_text_lower for x in ["brasil", "brazil"]) else None,
                    "workRegime": loc.get("workRegime") if str(loc.get("workRegime", "")).lower() in raw_text_lower else None,
                    "availability": loc.get("availability")
                },
                "links": links
            },
            "summary": raw.get("summary") or raw.get("resume"),
            "hardSkills": filtered_hard[:20],
            "softSkills": soft_skills[:15],
            "techStack": tech_stack,
            "experience": experience,
            "education": education,
            "certifications": raw.get("certifications") or [],
            "courses": raw.get("courses") or [],
            "projects": raw.get("projects") or [],
            "awards": raw.get("awards") or [],
            "languages": languages
        }
        
        return normalized

    def _extract_education_fallback(self, raw_text: str) -> List[Dict[str, Any]]:
        edu_regex = r"(Graduação|Mestrado|MBA|Doutorado|Pós-Graduação|Técnico|Bacharelado|Licenciatura)\s+em\s+([^\|]+)\s*\|\s*([^\|]+)\s*\|\s*(\d{4})\s*[–—-]+\s*(\d{4}|atual|Presente)"
        matches = re.findall(edu_regex, raw_text or "", re.IGNORECASE)
        return [
            {
                "institution": m[2].strip(),
                "degree": m[0].strip(),
                "field": m[1].strip(),
                "startDate": m[3],
                "endDate": m[4] if m[4].isdigit() else None
            } for m in matches
        ]

    def auto_categorize_tech_stack(self, skills: List[str]) -> Dict[str, List[str]]:
        ts = {"frontend": [], "backend": [], "mobile": [], "cloud": [], "databases": [], "devops": [], "other": []}
        categories = [
            ("frontend", ["react", "vue", "angular", "next.js", "html", "css", "tailwind"]),
            ("backend", ["node.js", "python", "php", "java", "ruby", "golang", "nestjs", "fastapi"]),
            ("mobile", ["react native", "flutter", "swift", "kotlin"]),
            ("cloud", ["aws", "azure", "gcp", "docker", "kubernetes"]),
            ("databases", ["postgresql", "mysql", "mongodb", "redis"]),
            ("devops", ["git", "ci/cd", "jenkins", "terraform", "ansible"])
        ]
        for skill in skills:
            low = str(skill).lower()
            cat_found = False
            for key, keywords in categories:
                if any(k in low for k in keywords):
                    ts[key].append(skill)
                    cat_found = True
                    break
            if not cat_found: ts["other"].append(skill)
        return ts

    def _calculate_confidence(self, result: ParsedCV) -> float:
        score = 0.0
        if result.personalData.fullName: score += 0.2
        if result.personalData.email: score += 0.1
        if result.experience: score += 0.3
        if result.education: score += 0.2
        if result.hardSkills: score += 0.2
        return min(score, 1.0)
