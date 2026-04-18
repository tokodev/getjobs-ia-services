import asyncio
import json
import logging
from bullmq import Worker
from app.agents.cv_parser import CVParserAgent
from app.core.settings import get_settings

settings = get_settings()
from app.agents.cv_parser import CVParserAgent
from app.core.settings import get_settings
from app.core.logging_setup import setup_json_logging

settings = get_settings()
logger = setup_json_logging("worker")

async def process_cv_extraction(job, token):
    """
    Processa um job de extração de CV vindo do BullMQ (NestJS).
    """
    job_id = getattr(job, "id", "unknown")
    logger.info(f"Processing job {job_id} for CV Extraction")
    print(f"\n[DEBUG] Iniciando Job {job_id}...") 

    try:
        data = job.data
        cv_text = data.get("cvText")
        user_id = data.get("userId")

        print(f"[DEBUG] Job {job_id} - Dados recebidos:")
        print(f"        User ID: {user_id}")
        print(f"        Tamanho do texto: {len(cv_text) if cv_text else 0} caracteres")
        if cv_text:
            print(f"        Preview do texto: {cv_text[:100]}...")

        if not cv_text:

            raise ValueError("cvText is missing in job data")

        agent = CVParserAgent()
        result = agent.parse(cv_text)

        logger.info(f"Successfully parsed CV for user {user_id}")

        # Converte para dict para retorno ao BullMQ
        parsed_dict = result.model_dump()

        print(f"[DEBUG] Sucesso no Job {job_id}. Enviando JSON de volta para o Redis.")
        logger.info(f"Returning data for job {job_id}. Fields: {list(parsed_dict.keys())}")

        return parsed_dict

        logger.info(f"Returning data for job {job_id}. Fields: {list(parsed_dict.keys())}")
        
        return parsed_dict
        
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
