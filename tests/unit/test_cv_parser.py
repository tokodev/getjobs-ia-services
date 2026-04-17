import pytest
from unittest.mock import patch, MagicMock
from app.agents.cv_parser import CVParserAgent, ParsedCV, PersonalData, Experience

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
                        "location": "São Paulo, Brazil",
                        "links": ["https://linkedin.com/in/johndoe"]
                    },
                    "summary": "Experienced software engineer with a focus on Python and Cloud.",
                    "hardSkills": ["Python", "AWS", "Kubernetes"],
                    "softSkills": ["Leadership", "Teamwork"],
                    "experience": [
                        {
                            "company": "Tech Corp",
                            "role": "Senior Engineer",
                            "location": "New York, USA",
                            "startDate": "2020-01-01",
                            "endDate": "2023-12-31",
                            "isCurrentRole": false,
                            "originalDescription": "Developed complex cloud systems."
                        }
                    ],
                    "education": [{"institution": "MIT", "degree": "BS in CS"}],
                    "certifications": [{"name": "AWS Certified Architect"}],
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
        "phone": None,
        "location": "Remote",
        "links": []
    }
    pd = PersonalData(**data)
    assert pd.fullName == "Jane Doe"
    assert pd.links == []

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
        result = cv_parser.parse("Sample CV Text")
        
        assert isinstance(result, ParsedCV)
        assert result.personalData.fullName == "John Doe"
        assert result.aiConfidence == 0.95
        assert len(result.experience) == 1
        assert result.experience[0].company == "Tech Corp"

def test_cv_parser_agent_error_handling(cv_parser):
    # Test with invalid JSON response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='''{"invalid": "json"}'''))
    ]
    
    with patch("app.agents.cv_parser.completion", return_value=mock_response):
        with pytest.raises(Exception): # PydanticValidationError
            cv_parser.parse("Sample CV Text")
