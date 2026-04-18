import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator
from app.grpc_server.server import serve as start_grpc_server
from app.worker.worker import start_worker
from app.worker.queue_monitor import monitor_queue_size
from app.agents.cv_parser import CVParserAgent
from app.agents.summary_analyzer import SummaryAnalyzerAgent
from app.agents.experience_analyzer import ExperienceAnalyzerAgent
from contextlib import asynccontextmanager

# Schema para requisição via API
class CVRequest(BaseModel):
    cvText: str
    userId: str | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.grpc_server = start_grpc_server()
    # Mantemos o monitor de fila apenas se você ainda for usar BullMQ para outras tarefas
    # Caso contrário, pode ser removido
    asyncio.create_task(monitor_queue_size())
    yield
    # Shutdown
    # Se houver worker ativo, fechamos aqui
    if hasattr(app.state, "worker"):
        await app.state.worker.close()

app = FastAPI(title="GetJobs IA Service", version="1.0.0", lifespan=lifespan)

# Instrumentação do Prometheus
Instrumentator().instrument(app).expose(app)

@app.get("/")
async def root():
    return {"message": "GetJobs IA Service is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/extract")
@app.post("/v1/cv/parse")
async def extract_cv(request: CVRequest):
    """
    Endpoint síncrono para extração de dados de currículo.
    Suporta tanto a rota antiga quanto a nova exigida pela API.
    """
    if not request.cvText:
        raise HTTPException(status_code=400, detail="cvText is required")
    
    try:
        agent = CVParserAgent()
        result = agent.parse(request.cvText)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na extração: {str(e)}")


@app.post("/v1/ai/analyze-summary")
async def analyze_summary(request: dict):
    """
    Endpoint para análise de resumo profissional.
    Retorna Prós, Contras e uma sugestão em Markdown.
    """
    try:
        agent = SummaryAnalyzerAgent()
        result = agent.analyze(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise: {str(e)}")


@app.post("/v1/ai/analyze-experience")
async def analyze_experience(request: dict):
    """
    Endpoint para análise de experiência profissional específica.
    """
    try:
        agent = ExperienceAnalyzerAgent()
        result = agent.analyze(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
