import pytest
from unittest.mock import MagicMock, patch
from app.worker.worker import process_cv_extraction

@pytest.mark.asyncio
async def test_process_cv_extraction_success():
    # Mock do Job do BullMQ
    mock_job = MagicMock()
    mock_job.id = "job-123"
    mock_job.data = {"userId": "user-456", "cvText": "Experienced developer"}
    
    # Mock do CVParserAgent
    mock_result = MagicMock()
    mock_result.model_dump.return_value = {"parsed": "data"}
    
    with patch("app.worker.worker.CVParserAgent") as MockAgent:
        instance = MockAgent.return_value
        instance.parse.return_value = mock_result
        
        result = await process_cv_extraction(mock_job, "token")
        
        assert result == {"parsed": "data"}
        instance.parse.assert_called_once_with("Experienced developer")

@pytest.mark.asyncio
async def test_process_cv_extraction_missing_cv_text():
    mock_job = MagicMock()
    mock_job.data = {"userId": "user-456"} # Faltando cvText
    
    with pytest.raises(ValueError, match="cvText is missing"):
        await process_cv_extraction(mock_job, "token")

@pytest.mark.asyncio
async def test_process_cv_extraction_agent_failure():
    mock_job = MagicMock()
    mock_job.data = {"userId": "user-456", "cvText": "Text"}
    
    with patch("app.worker.worker.CVParserAgent") as MockAgent:
        instance = MockAgent.return_value
        instance.parse.side_effect = Exception("Agent error")
        
        with pytest.raises(Exception, match="Agent error"):
            await process_cv_extraction(mock_job, "token")

@pytest.mark.asyncio
async def test_start_worker():
    with patch("app.worker.worker.Worker") as MockWorker:
        from app.worker.worker import start_worker
        
        worker = await start_worker()
        
        assert MockWorker.called
        assert worker == MockWorker.return_value
        # Verifica se passou os argumentos corretos para o Worker
        # No código: Worker(settings.BULLMQ_QUEUE_NAME, process_cv_extraction, {"connection": redis_opts})
        MockWorker.assert_called_once()
        args, kwargs = MockWorker.call_args
        assert args[0] == "cv-extraction"
        assert args[1] == process_cv_extraction
        # O terceiro argumento é o dicionário de opções
        assert "host" in args[2]["connection"]
        assert "port" in args[2]["connection"]
