import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch
from app.main import app

@pytest.mark.asyncio
async def test_read_root():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "GetJobs IA Service is running"}

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@pytest.mark.asyncio
async def test_startup_shutdown():
    # Mocks para as funções iniciadas no startup
    with patch("app.main.start_grpc_server") as mock_grpc, \
         patch("app.main.start_worker", new_callable=AsyncMock) as mock_worker, \
         patch("app.main.monitor_queue_size", new_callable=AsyncMock) as mock_monitor:
        
        mock_worker.return_value = AsyncMock()
        
        # Chama manualmente os handlers de evento pois o AsyncClient não os dispara sozinho em on_event
        from app.main import startup_event, shutdown_event
        await startup_event()
        
        assert mock_grpc.called
        assert mock_worker.called
        assert mock_monitor.called
        
        await shutdown_event()
        assert app.state.worker.close.called
