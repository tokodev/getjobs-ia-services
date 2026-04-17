import asyncio
import logging
import redis.asyncio as redis
from prometheus_client import Gauge
from app.core.settings import get_settings

settings = get_settings()
logger = logging.getLogger("queue_monitor")

# Métrica Prometheus
BULLMQ_QUEUE_SIZE = Gauge(
    "bullmq_queue_waiting_jobs",
    "Number of jobs waiting in the BullMQ queue",
    ["queue_name"]
)

async def monitor_queue_size():
    """
    Tarefa periódica que lê o tamanho da fila do BullMQ no Redis.
    BullMQ armazena jobs em espera no set/list '{queue_name}:wait'.
    """
    queue_name = settings.BULLMQ_QUEUE_NAME
    # Tenta conectar ao Redis usando a URL do settings
    r = redis.from_url(settings.REDIS_URL)
    
    logger.info(f"Starting queue monitor for: {queue_name}")
    
    while True:
        try:
            # BullMQ 5+ usa listas para o estado 'wait'
            # Chave: bullmq.{queue_name}.wait ou apenas {queue_name}:wait dependendo da versão/config
            # No NestJS/BullMQ padrão a chave costuma ser {queue_name}:wait (tipo list)
            
            wait_key = f"bullmq:{queue_name}:wait" # Padrão BullMQ
            # No BullMQ do NestJS pode ser apenas {queue_name}:wait
            
            # Vamos tentar as duas variações comuns
            size = await r.llen(wait_key)
            if size == 0:
                size = await r.llen(f"{queue_name}:wait")
            
            BULLMQ_QUEUE_SIZE.labels(queue_name=queue_name).set(size)
            
        except Exception as e:
            logger.error(f"Error monitoring queue: {str(e)}")
            
        await asyncio.sleep(15) # Atualiza a cada 15 segundos
