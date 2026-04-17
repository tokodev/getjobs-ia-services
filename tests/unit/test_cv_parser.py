import pytest
from unittest.mock import patch, MagicMock
from app.agents.cv_parser import CVParserAgent, ParsedCV, PersonalData, Experience, Location, Links

@pytest.fixture
def cv_parser():
    return CVParserAgent()

@pytest.fixture
def mock_completion_response():
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content='''{
                    "personalData": {
                        "fullName": "John Doe",
                        "email": "john.doe@example.com",
                        "phone": "+55 11 99999-9999",
                        "location": {
                            "city": "São Paulo",
                            "state": "SP",
                            "country": "Brazil",
                            "workRegime": "Remoto",
                            "availability": "Início imediato"
                        },
                        "links": {
                            "linkedin": "https://linkedin.com/in/johndoe",
                            "github": "https://github.com/johndoe",
                            "portfolio": null,
                            "website": null
                        }
                    },
                    "summary": "Experienced software engineer with a focus on Python and Cloud.",
                    "hardSkills": ["Python", "AWS", "Kubernetes"],
                    "softSkills": ["Leadership", "Teamwork"],
                    "techStack": {
                        "backend": ["Python"],
                        "cloud": ["AWS", "Kubernetes"]
                    },
                    "experience": [
                        {
                            "company": "Tech Corp",
                            "role": "Senior Engineer",
                            "location": "New York, USA",
                            "startDate": "2020-01",
                            "endDate": "2023-12",
                            "isCurrentRole": false,
                            "originalDescription": "Developed complex cloud systems."
                        }
                    ],
                    "education": [{"institution": "MIT", "degree": "BS in CS", "field": "Computer Science", "startDate": "2016", "endDate": "2020"}],
                    "certifications": [],
                    "courses": [],
                    "projects": [],
                    "awards": [],
                    "languages": [{"language": "English", "level": "Fluent"}],
                    "aiConfidence": 0.95
                }'''
            )
        )
    ]
    mock_response.get.side_effect = lambda key, default=None: {"model": "gpt-4o", "usage": {"prompt_tokens": 100, "completion_tokens": 50}}.get(key, default)
    return mock_response

def test_personal_data_schema():
    data = {
        "fullName": "Jane Doe",
        "email": "jane@example.com",
        "location": {"city": "Remote"},
        "links": {"linkedin": "url"}
    }
    pd = PersonalData(**data)
    assert pd.fullName == "Jane Doe"
    assert pd.location.city == "Remote"
    assert pd.links.linkedin == "url"

def test_experience_schema():
    data = {
        "company": "Company",
        "role": "Manager",
        "originalDescription": "Managed people."
    }
    exp = Experience(**data)
    assert exp.company == "Company"
    assert exp.isCurrentRole is False

def test_cv_parser_agent_parse(cv_parser, mock_completion_response):
    with patch("app.agents.cv_parser.completion", return_value=mock_completion_response):
        # O texto do CV deve conter "brazil" para o validador de country passar no normalize_cv_data
        result = cv_parser.parse("Sample CV Text from Brazil")
        
        assert isinstance(result, ParsedCV)
        assert result.personalData.fullName == "John Doe"
        assert result.personalData.location.country == "Brazil"
        assert result.aiConfidence >= 0.8
        assert len(result.experience) == 1
        assert result.experience[0].company == "Tech Corp"

def test_cv_parser_agent_normalization_logic(cv_parser):
    raw_data = {
        "personalData": {
            "fullName": "Normal User",
            "email": "user @ email.com", # Espaços que devem ser removidos
            "location": "São Paulo - SP", # String que deve ser parseada
        },
        "hardSkills": ["Python", "Leadership", "MBA in Data"], # Habilidades que devem ser filtradas
        "experience": [
            {"company": "A", "role": "B", "startDate": "2020", "endDate": "Present", "originalDescription": "D"}
        ]
    }
    
    # Testando o método interno de normalização
    normalized = cv_parser.normalize_cv_data(raw_data, "CV text from Brazil with Python and Leadership")
    
    assert normalized["personalData"]["email"] == "user@email.com"
    assert normalized["personalData"]["location"]["city"] == "São Paulo"
    assert normalized["personalData"]["location"]["state"] == "SP"
    # "Leadership" deve ir para softSkills e "MBA" deve ser removido de hardSkills
    assert "Python" in normalized["hardSkills"]
    assert "Leadership" in normalized["softSkills"]
    assert "MBA in Data" not in normalized["hardSkills"]
    # Data "Present" deve virar None
    assert normalized["experience"][0]["endDate"] is None
    assert normalized["experience"][0]["isCurrentRole"] is True
