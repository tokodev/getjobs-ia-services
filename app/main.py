import asyncio
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from app.grpc_server.server import serve as start_grpc_server
from app.worker.worker import start_worker
from app.worker.queue_monitor import monitor_queue_size

app = FastAPI(title="GetJobs IA Service", version="1.0.0")

# Instrumentação do Prometheus
Instrumentator().instrument(app).bootstrap()

@app.on_event("startup")
async def startup_event():
    # Inicia o servidor gRPC em background
    app.state.grpc_server = start_grpc_server()
    # Inicia o Worker do BullMQ e armazena no estado
    app.state.worker = await start_worker()
    # Inicia o monitor de fila
    asyncio.create_task(monitor_queue_size())

@app.on_event("shutdown")
async def shutdown_event():
    # Fecha o worker se necessário
    if hasattr(app.state, "worker"):
        await app.state.worker.close()

@app.get("/")
async def root():
    return {"message": "GetJobs IA Service is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
