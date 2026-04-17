import logging
from app.core.logging_setup import setup_json_logging

def test_setup_json_logging():
    logger = setup_json_logging("test_logger")
    
    assert logger.name == "test_logger"
    assert logger.level == logging.INFO
    assert len(logger.handlers) >= 1
    
    # Testa se ao chamar novamente ele não duplica handlers
    handler_count = len(logger.handlers)
    setup_json_logging("test_logger")
    assert len(logger.handlers) == handler_count
