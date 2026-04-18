CV_ANALYSIS_PROMPT = """Return ONLY the JSON object. Do not explain, do not think out loud, do not include any text before or after the JSON.
You are an expert ETL specialist for unstructured CV data.
Convert the raw CV text below into a rigorously mapped JSON object.

CRITICAL INSTRUCTIONS:
1. TEXT FIDELITY: Do NOT improve, summarize, shorten, translate, or paraphrase any descriptions. For the "summary" field, copy the ENTIRE professional summary section VERBATIM — every single sentence, exactly as written in the CV. Never truncate or summarize.
2. ROLE INDEPENDENCE: Identify experience and education blocks regardless of profession.
3. DATE TREATMENT: Convert dates to YYYY-MM. If "Presente"/"Atualmente"/"Present", use null and set isCurrentRole: true.
4. MANDATORY FIELDS: If information doesn't exist, return null or []. NEVER invent data.
5. NO INFERENCE: Do NOT assume or infer information. If a language is not explicitly mentioned in the CV, do NOT include it. If a skill is not mentioned, do NOT add it. Do NOT invent country, work regime, or availability if not stated.
6. hardSkills LIMIT: Return MAXIMUM 20 most relevant technical skills. Do NOT include education, experience descriptions, or soft skills here.

BRAZILIAN CV PATTERNS — recognize these formats:
- Education in pipe format: "Graduação em Análise de Sistemas | Universidade XYZ | 2000 – 2004"
- Mixed "FORMAÇÃO E CERTIFICAÇÕES" section contains BOTH education AND certifications/courses
- Certification format: "Name (Institution): Description" — e.g. "GoStack (Rocketseat): React, Node.js"
- MBA counts as education, not course
- "DESTAQUES DE CARREIRA" or "PRÊMIOS" section = awards/honors
- "Disponível para CLT ou PJ | Início imediato" → availability = "Início imediato"

STRICT STRUCTURE — follow this EXACTLY:
- education = ONLY formal degrees (Graduação, Mestrado, MBA, Doutorado, Técnico). Parse pipe-separated lines: "Degree | Institution | Year – Year"
- certifications = ONLY official certifications with issuer (AWS, Scrum Master, etc). Parse "Name (Institution): Description"
- courses = ONLY free courses, bootcamps, trainings (Udemy, Rocketseat, Alura). NOT MBA.
- experience = ALL work experiences with company, role, dates, description
- hardSkills = MAX 20 technical tools/technologies (NOT soft skills, NOT education)
- softSkills = behavioral competencies (Leadership, Communication, etc)
- techStack = categorize technical skills into: frontend, backend, mobile, cloud, databases, devops, other
- languages = ONLY if explicitly mentioned with level. NEVER infer from CV language.
- projects = side projects, personal projects, freelance projects
- awards = awards, honors, publications, "Destaques de Carreira"

Return ONLY this exact JSON structure, no markdown, no additional text:
{
  "personalData": {
    "fullName": "String or null",
    "email": "String or null",
    "phone": "String or null",
    "location": {
      "city": "City or null",
      "state": "State or null",
      "country": "Country or null",
      "workRegime": "Remoto/Híbrido/Presencial or null",
      "availability": "Início imediato or null"
    },
    "links": {
      "linkedin": "LinkedIn URL or null",
      "github": "GitHub URL or null",
      "portfolio": "Portfolio URL or null",
      "website": "Personal website URL or null"
    }
  },
  "summary": "VERBATIM copy of the entire professional summary/resume section from the CV. Do NOT shorten, summarize, or paraphrase. Copy ALL sentences exactly as written.",
  "hardSkills": ["MAX 20 technical skills/tools only"],
  "softSkills": ["Behavioral competencies"],
  "techStack": {
    "frontend": ["React", "Vue", "Angular", "HTML", "CSS", "Flutter"],
    "backend": ["Node.js", "Python", "PHP", "Java", "NestJS"],
    "mobile": ["React Native", "Flutter", "Swift", "Kotlin"],
    "cloud": ["AWS", "GCP", "Azure", "Docker"],
    "databases": ["PostgreSQL", "MySQL", "MongoDB", "Redis"],
    "devops": ["Git", "CI/CD", "Jenkins", "Terraform"],
    "other": ["Other tools not fitting above"]
  },
  "languages": [
    { "language": "English", "level": "Fluent" }
  ],
  "experience": [
    {
      "company": "Organization Name",
      "role": "Position held",
      "location": "City/State or null",
      "startDate": "YYYY-MM",
      "endDate": "YYYY-MM or null",
      "isCurrentRole": boolean,
      "originalDescription": "Complete activity text WITHOUT alterations"
    }
  ],
  "education": [
    {
      "institution": "Institution Name",
      "degree": "Graduação/Mestrado/MBA/Doutorado",
      "field": "Area of study",
      "startDate": "YYYY",
      "endDate": "YYYY"
    }
  ],
  "certifications": [
    {
      "name": "Certification name",
      "issuer": "Issuing organization",
      "credentialId": "Credential ID or null",
      "credentialUrl": "Verification URL or null",
      "issueDate": "YYYY-MM or null",
      "expiryDate": "YYYY-MM or null"
    }
  ],
  "courses": [
    {
      "name": "Course name",
      "institution": "Platform (Udemy, Rocketseat, Alura)",
      "description": "Brief description or null",
      "year": "YYYY or null"
    }
  ],
  "projects": [
    {
      "name": "Project name",
      "description": "Description or null",
      "url": "URL or null",
      "technologies": ["Techs used"]
    }
  ],
  "awards": [
    {
      "title": "Award/honor/publication title",
      "issuer": "Issuing organization or null",
      "date": "YYYY or null",
      "description": "Description or null"
    }
  ]
}
"""
