import asyncio
import redis.asyncio as redis
from app.core.settings import get_settings

async def clear_bullmq_queue():
    settings = get_settings()
    queue_name = settings.BULLMQ_QUEUE_NAME
    prefix = f"bullmq:{queue_name}:*"
    
    print(f"Conectando ao Redis em {settings.REDIS_URL}...")
    r = redis.from_url(settings.REDIS_URL)
    
    # Encontra todas as chaves associadas a essa fila
    keys = await r.keys(prefix)
    
    if not keys:
        print(f"A fila '{queue_name}' já está vazia ou não existe.")
        return

    print(f"Encontradas {len(keys)} chaves para a fila '{queue_name}'. Apagando...")
    
    # Deleta todas as chaves
    await r.delete(*keys)
    
    print(f"Fila '{queue_name}' limpa com sucesso!")
    await r.aclose()

if __name__ == "__main__":
    asyncio.run(clear_bullmq_queue())
