import asyncio
import json
import logging
from bullmq import Worker
from app.agents.cv_parser import CVParserAgent
from app.core.settings import get_settings

settings = get_settings()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_cv_extraction(job, token):
    """
    Processa um job de extração de CV vindo do BullMQ (NestJS).
    O job.data deve conter { "userId": "...", "cvText": "..." }
    """
    job_id = getattr(job, "id", "unknown")
    logger.info(f"Processing job {job_id} for CV Extraction")
    try:
        # No Python BullMQ, job.data pode ser acessado diretamente ou como dicionário
        data = job.data
        cv_text = data.get("cvText")
        user_id = data.get("userId")
        
        if not cv_text:
            raise ValueError("cvText is missing in job data")
            
        agent = CVParserAgent()
        result = agent.parse(cv_text)
        
        logger.info(f"Successfully parsed CV for user {user_id}")
        
        # O retorno é o valor que o BullMQ salvará no campo 'returnvalue' do Redis
        return result.model_dump()
        
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}")
        raise e

async def start_worker():
    """
    Inicia o worker do BullMQ.
    """
    redis_opts = {
        "host": settings.REDIS_HOST,
        "port": settings.REDIS_PORT,
        "password": settings.REDIS_PASSWORD
    }
    
    worker = Worker(
        settings.BULLMQ_QUEUE_NAME,
        process_cv_extraction,
        {
            "connection": redis_opts
        }
    )
    
    logger.info(f"BullMQ Worker started for queue: {settings.BULLMQ_QUEUE_NAME}")
    return worker
