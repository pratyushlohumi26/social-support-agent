import pytest

from src.agents.orchestrator_agent import OrchestratorAgent


@pytest.mark.asyncio
async def test_handle_document_failure_with_missing_docs():
    orchestrator = OrchestratorAgent()
    proc_results = {"processing_stages": {}}
    doc_results = {"documents_processed": ["emirates_id"], "documents_valid": True}
    missing = ["bank_statement", "cv"]
    result = await orchestrator._handle_document_failure(proc_results, doc_results, missing)
    assert result["final_decision"]["status"] == "documents_required"
    assert result["final_decision"]["missing_documents"] == missing
    assert "next_steps" in result["final_decision"]


@pytest.mark.asyncio
async def test_handle_document_failure_no_missing_docs():
    orchestrator = OrchestratorAgent()
    proc_results = {"processing_stages": {}}
    doc_results = {}
    result = await orchestrator._handle_document_failure(proc_results, doc_results)
    assert result["final_decision"]["missing_documents"] == []
    assert result["final_decision"]["status"] == "documents_required"
