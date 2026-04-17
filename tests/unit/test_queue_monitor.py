import pytest
from unittest.mock import AsyncMock, patch
from app.worker.queue_monitor import monitor_queue_size

@pytest.mark.asyncio
async def test_monitor_queue_size_iteration():
    # Mock do Redis
    mock_redis = AsyncMock()
    mock_redis.llen.side_effect = [10, 0] # Simula 10 na primeira chave e 0 na segunda
    
    # Mock do Gauge do Prometheus para não dar erro de registro
    with patch("app.worker.queue_monitor.redis.from_url", return_value=mock_redis), \
         patch("app.worker.queue_monitor.BULLMQ_QUEUE_SIZE") as mock_gauge, \
         patch("asyncio.sleep", side_effect=[None, Exception("StopLoop")]): # Para o while após 1 iteração
        
        try:
            await monitor_queue_size()
        except Exception as e:
            if str(e) != "StopLoop":
                raise e
        
        # Verifica se o llen foi chamado
        assert mock_redis.llen.called
        # Verifica se a métrica foi atualizada com labels
        mock_gauge.labels.assert_called_with(queue_name="cv-extraction")
        mock_gauge.labels.return_value.set.assert_called_with(10)
