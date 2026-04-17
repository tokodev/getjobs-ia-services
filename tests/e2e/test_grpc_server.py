import pytest
from unittest.mock import MagicMock, patch
from app.grpc_server.server import AIServiceServicer
from app.grpc_server import ia_service_pb2

class MockContext:
    def __init__(self):
        self.code = None
        self.details = None

    def set_code(self, code):
        self.code = code

    def set_details(self, details):
        self.details = details

@pytest.fixture
def servicer():
    return AIServiceServicer()

def test_parse_cv_grpc_success(servicer):
    # Mock do CVParserAgent para retornar um objeto que tenha o método model_dump_json
    mock_parsed_cv = MagicMock()
    mock_parsed_cv.model_dump_json.return_value = '{"test": "data"}'
    
    with patch.object(servicer.cv_parser, 'parse', return_value=mock_parsed_cv):
        request = ia_service_pb2.CVRequest(cv_text="Text to parse")
        context = MockContext()
        
        response = servicer.ParseCV(request, context)
        
        assert response.json_data == '{"test": "data"}'
        assert context.code is None

def test_parse_cv_grpc_error(servicer):
    with patch.object(servicer.cv_parser, 'parse', side_effect=Exception("Parsing error")):
        request = ia_service_pb2.CVRequest(cv_text="Text to parse")
        context = MockContext()
        
        response = servicer.ParseCV(request, context)
        
        assert response.json_data == ""
        assert "Parsing error" in context.details

def test_get_instant_match_grpc(servicer):
    request = ia_service_pb2.MatchRequest()
    context = MockContext()
    
    response = servicer.GetInstantMatch(request, context)
    
    assert response.score == pytest.approx(0.85)
    assert "Match simulado" in response.reasoning

def test_grpc_serve():
    with patch("grpc.server") as mock_server,          patch("app.grpc_server.ia_service_pb2_grpc.add_AIServiceServicer_to_server") as mock_add:
        
        from app.grpc_server.server import serve
        server_instance = mock_server.return_value
        
        result = serve()
        
        assert result == server_instance
        assert mock_server.called
        assert mock_add.called
        assert server_instance.add_insecure_port.called
        assert server_instance.start.called
