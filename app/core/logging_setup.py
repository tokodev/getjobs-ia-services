import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_json_logging(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Previne duplicação se chamado múltiplas vezes
    if not logger.handlers:
        logHandler = logging.StreamHandler(sys.stdout)
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(levelname)s %(name)s %(message)s'
        )
        logHandler.setFormatter(formatter)
        logger.addHandler(logHandler)
    
    return logger
