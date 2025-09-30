"""FastAPI application for the UAE Social Support AI System."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import Body, Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from dotenv import load_dotenv

load_dotenv()

from ..agents.orchestrator_agent import OrchestratorAgent
from ..agents.chat_assistant_agent import ChatAssistantAgent
from ..config.settings import get_settings
from ..database.database import get_database_session, init_database
from ..database.models import Application, ChatSession, Document
from ..models.uae_specific_models import UAEApplicationData
from pydantic import ValidationError

logger = logging.getLogger(__name__)


# Optional integrations -----------------------------------------------------
try:  # LangGraph workflow orchestration
    from ..orchestration.langgraph_workflow import workflow_orchestrator

    LANGGRAPH_AVAILABLE = workflow_orchestrator is not None
except Exception as exc:  # noqa: BLE001
    logger.warning("LangGraph workflow not available: %s", exc)
    workflow_orchestrator = None
    LANGGRAPH_AVAILABLE = False

# Core application state -----------------------------------------------------
settings = get_settings()
app = FastAPI(
    title="UAE Social Support AI System",
    description="Multimodal social-support processing pipeline for the UAE",
    version="3.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=getattr(settings, "API_CORS_ORIGINS", ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = OrchestratorAgent()
chat_agent = ChatAssistantAgent()
UPLOAD_ROOT = Path(getattr(settings, "UPLOAD_DIR", "uploads"))


# Utility helpers -----------------------------------------------------------
def _generate_application_id() -> str:
    return f"UAE-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"


async def _store_chat_exchange(
    db: AsyncSession,
    session_id: str,
    user_message: str,
    agent_response: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """Persist chat history in the database."""

    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "user": user_message,
        "agent": agent_response.get("response"),
        "intent": agent_response.get("intent"),
    }

    result = await db.execute(
        select(ChatSession).where(ChatSession.session_id == session_id)
    )
    chat_session = result.scalar_one_or_none()

    if chat_session:
        messages = chat_session.messages or []
        messages.append(entry)
        chat_session.messages = messages
        chat_session.context = context or {}
        chat_session.last_activity = datetime.utcnow()
    else:
        chat_session = ChatSession(
            session_id=session_id,
            application_id=agent_response.get("application_id"),
            messages=[entry],
            context=context or {},
            is_active=True,
            last_activity=datetime.utcnow(),
        )
        db.add(chat_session)

    await db.commit()


# FastAPI lifecycle ---------------------------------------------------------
@app.on_event("startup")
async def startup_event() -> None:
    """Ensure required resources are available on startup."""

    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    await init_database()


# Routes --------------------------------------------------------------------
@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint showing build information."""

    return {
        "message": "UAE Social Support AI System",
        "version": app.version,
        "features": [
            "Agent-based orchestration",
            "LangGraph workflow" if LANGGRAPH_AVAILABLE else "Rule-based workflow",
            "LLM-assisted financial analysis",
            "Interactive chat assistant",
            "UAE-specific eligibility criteria",
        ],
        "database_connected": True,
        "langgraph_available": LANGGRAPH_AVAILABLE,
    }


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Return service health details."""

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "system": "UAE Social Support AI",
        "langgraph_available": LANGGRAPH_AVAILABLE,
    }


@app.post("/applications/submit")
async def submit_application(
    application_payload: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_database_session),
) -> Dict[str, Any]:
    """Submit an application for processing and persist the results."""
    try:
        application = UAEApplicationData(**application_payload)
        application_data = application.dict()
    except ValidationError as exc:
        logger.warning("Application validation failed: %s", exc)
        error_details = exc.errors()
        readable_errors = [
            {
                "field": " -> ".join(str(part) for part in error.get("loc", [])),
                "message": error.get("msg", "Invalid value"),
            }
            for error in error_details
        ]
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Application validation failed. Please review the highlighted fields.",
                "errors": readable_errors,
            },
        ) from exc

    application_id = application_data.get("application_id") or _generate_application_id()
    application_data["application_id"] = application_id

    try:
        if LANGGRAPH_AVAILABLE and workflow_orchestrator:
            processing_result = await workflow_orchestrator.process_application(
                application_data
            )
        else:
            processing_result = await orchestrator.process(application_data)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Application processing failed")
        raise HTTPException(status_code=500, detail=f"Processing failed: {exc}") from exc

    processing_result.setdefault("success", True)
    processing_result.setdefault("application_id", application_id)

    final_decision = processing_result.get("final_decision", {})
    status = final_decision.get("status") or application.processing_status or "processed"

    result = await db.execute(
        select(Application).where(Application.application_id == application_id)
    )
    application_record = result.scalar_one_or_none()

    if application_record:
        application_record.applicant_name = application.personal_info.full_name
        application_record.phone = application.personal_info.mobile_number
        application_record.email = application.personal_info.email
        application_record.support_type = application.support_request.support_type
        application_record.status = status
        application_record.priority = application.support_request.urgency_level
        application_record.emirates_id = application.personal_info.emirates_id
        application_record.emirate = application.personal_info.emirate
        application_record.family_size = application.personal_info.family_size
        application_record.monthly_income = application.employment_info.monthly_salary
        application_record.application_data = application_data
        application_record.processing_results = processing_result
        application_record.decision_data = final_decision
    else:
        application_record = Application(
            application_id=application_id,
            applicant_name=application.personal_info.full_name,
            phone=application.personal_info.mobile_number,
            email=application.personal_info.email,
            support_type=application.support_request.support_type,
            status=status,
            priority=application.support_request.urgency_level,
            emirates_id=application.personal_info.emirates_id,
            emirate=application.personal_info.emirate,
            family_size=application.personal_info.family_size,
            monthly_income=application.employment_info.monthly_salary,
            application_data=application_data,
            processing_results=processing_result,
            decision_data=final_decision,
        )
        db.add(application_record)

    await db.commit()
    await db.refresh(application_record)

    return {
        "success": processing_result.get("success", True),
        "application_id": application_record.application_id,
        "processing_result": processing_result,
        "message": "Application processed and stored successfully",
    }


@app.get("/applications/{application_id}")
async def get_application(
    application_id: str,
    db: AsyncSession = Depends(get_database_session),
) -> Dict[str, Any]:
    """Retrieve an application and its processing outcome."""

    result = await db.execute(
        select(Application).where(Application.application_id == application_id)
    )
    application_record = result.scalar_one_or_none()

    if not application_record:
        raise HTTPException(status_code=404, detail="Application not found")

    return {
        "application_id": application_record.application_id,
        "applicant_name": application_record.applicant_name,
        "phone": application_record.phone,
        "email": application_record.email,
        "support_type": application_record.support_type,
        "status": application_record.status,
        "priority": application_record.priority,
        "emirates_id": application_record.emirates_id,
        "emirate": application_record.emirate,
        "family_size": application_record.family_size,
        "monthly_income": application_record.monthly_income,
        "application_data": application_record.application_data,
        "processing_results": application_record.processing_results,
        "decision_data": application_record.decision_data,
        "created_at": application_record.created_at.isoformat()
        if application_record.created_at
        else None,
        "updated_at": application_record.updated_at.isoformat()
        if application_record.updated_at
        else None,
    }


@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = "general",
    application_id: Optional[str] = None,
    db: AsyncSession = Depends(get_database_session),
) -> Dict[str, Any]:
    """Persist uploaded documents and register them in the database."""

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    stored_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}_{file.filename}"
    file_path = UPLOAD_ROOT / stored_name

    with open(file_path, "wb") as destination:
        destination.write(contents)

    document_record = Document(
        application_id=application_id,
        document_type=document_type,
        filename=file.filename,
        file_path=str(file_path),
        file_size=len(contents),
        extraction_data=None,
        confidence_score=None,
        validation_status="uploaded",
    )
    db.add(document_record)
    await db.commit()
    await db.refresh(document_record)

    return {
        "success": True,
        "document_id": document_record.id,
        "filename": file.filename,
        "stored_path": str(file_path),
        "size": len(contents),
        "document_type": document_type,
    }


@app.post("/chat")
async def chat_interaction(
    data: Dict[str, Any],
    db: AsyncSession = Depends(get_database_session),
) -> Dict[str, Any]:
    """Handle chat interactions with optional LLM assistance."""

    message = data.get("message", "").strip()
    context = data.get("context", {})
    session_id = data.get("session_id") or str(uuid4())

    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    try:
        agent_payload = await chat_agent.process({"message": message, "context": context})
        if not agent_payload or agent_payload.get("success") is False:
            raise RuntimeError("Chat agent returned unsuccessful result")

        response_text = agent_payload.get("response", "")
        if isinstance(response_text, dict):
            response_text = json.dumps(response_text)

        response_payload = {
            "success": True,
            "response": response_text,
            "intent": agent_payload.get("intent", "general_help"),
            "suggested_actions": agent_payload.get("suggested_actions", []),
            "llm_powered": agent_payload.get(
                "llm_powered", bool(getattr(chat_agent.llm_client, "available", False))
            ),
        }

        for key, value in agent_payload.items():
            if key not in response_payload:
                response_payload[key] = value

    except Exception as exc:  # noqa: BLE001
        logger.error("Chat processing failed: %s", exc)
        message_lower = message.lower()

        if any(word in message_lower for word in ["document", "paper", "file"]):
            intent = "document_help"
            response_text = (
                "Required documents typically include Emirates ID, bank statements, "
                "salary certificate, and any family book documentation. Ensure copies "
                "are recent and clearly legible."
            )
            actions = [
                "What documents are required?",
                "How do I prepare my bank statements?",
                "Can I upload documents in Arabic?",
            ]
        elif any(word in message_lower for word in ["eligible", "qualify"]):
            intent = "eligibility_question"
            response_text = (
                "Eligibility depends on emirate-specific income thresholds, "
                "family size, and employment stability. Citizens and long-term "
                "residents share similar criteria across emirates."
            )
            actions = [
                "Am I eligible for financial support?",
                "What is the income limit in Dubai?",
                "How does family size affect eligibility?",
            ]
        elif any(word in message_lower for word in ["amount", "money", "support"]):
            intent = "support_amounts"
            response_text = (
                "Support bands range from emergency grants (~2k-8k AED) to "
                "comprehensive programs (~50k AED). Final amounts depend on the "
                "financial assessment and recommended program."
            )
            actions = [
                "How much assistance can I expect?",
                "When will payments be issued?",
                "What influences the support amount?",
            ]
        else:
            intent = "general_help"
            response_text = (
                "I can help with eligibility, documentation, support amounts, and "
                "training programs related to UAE social support applications."
            )
            actions = [
                "Ask about eligibility requirements",
                "Ask about required documents",
                "Ask about training programs",
            ]

        response_payload = {
            "success": True,
            "response": response_text,
            "intent": intent,
            "suggested_actions": actions,
            "llm_powered": False,
            "fallback_used": True,
        }

    response_payload["timestamp"] = datetime.utcnow().isoformat()
    response_payload["session_id"] = session_id

    await _store_chat_exchange(db, session_id, message, response_payload, context)

    return response_payload


@app.get("/chat/health")
async def chat_health_check() -> Dict[str, Any]:
    """Report health for chat-related integrations."""

    status = {
        "timestamp": datetime.utcnow().isoformat(),
        "langgraph_available": LANGGRAPH_AVAILABLE,
        "chat_llm_available": bool(getattr(chat_agent.llm_client, "available", False)),
    }

    try:
        from ..llm.ollama_client import ollama_llm

        status["ollama"] = {
            "available": ollama_llm.available,
            "model": ollama_llm.model,
            "api_key_configured": bool(ollama_llm.api_key),
        }
    except Exception as exc:  # noqa: BLE001
        status["ollama"] = {"error": str(exc)}

    status["overall_status"] = "healthy" if status["chat_llm_available"] else "degraded"
    return status


@app.get("/assessment/criteria/uae")
async def get_uae_criteria() -> Dict[str, Any]:
    """Return UAE-specific assessment criteria."""

    return {
        "income_thresholds": getattr(settings, "UAE_INCOME_THRESHOLDS", {}),
        "supported_emirates": list(getattr(settings, "UAE_INCOME_THRESHOLDS", {}).keys()),
        "assessment_factors": [
            "Income level by emirate",
            "Family size and dependents",
            "Employment stability",
            "Cost of living adjustment",
        ],
    }


@app.get("/stats")
async def get_system_stats(
    db: AsyncSession = Depends(get_database_session),
) -> Dict[str, Any]:
    """Aggregate system statistics from the database."""

    applications_result = await db.execute(select(Application))
    applications = applications_result.scalars().all()
    total_applications = len(applications)

    approved = sum(
        1
        for app_record in applications
        if (app_record.decision_data or {}).get("status", "").lower() == "approved"
    )
    documents_result = await db.execute(select(func.count(Document.id)))
    total_documents = documents_result.scalar() or 0

    success_rate = (approved / total_applications * 100) if total_applications else 0.0

    return {
        "total_applications": total_applications,
        "approved_applications": approved,
        "success_rate": f"{success_rate:.1f}%",
        "active_agents": 4,
        "processing_average_time": "N/A",
        "supported_document_types": len(getattr(settings, "SUPPORTED_DOC_FORMATS", []))
        or 0,
        "documents_uploaded": total_documents,
        "last_updated": datetime.utcnow().isoformat(),
    }


@app.get("/debug/system")
async def debug_system() -> Dict[str, Any]:
    """Verbose system diagnostics for debugging."""

    try:
        agents_status = {
            "document_processor": "operational",
            "financial_analyzer": "operational",
            "career_counselor": "operational",
            "chat_assistant": "operational",
            "orchestrator": "operational",
        }
        try:
            from ..llm.ollama_client import ollama_llm

            ollama_configured = bool(getattr(ollama_llm, "available", False))
            has_api_key = bool(getattr(ollama_llm, "api_key", ""))
        except Exception:  # pragma: no cover - defensive import
            ollama_configured = False
            has_api_key = False

        llm_integration = {
            "ollama_cloud": "configured" if ollama_configured or has_api_key else "not_configured",
            "langgraph_workflow": "operational" if LANGGRAPH_AVAILABLE else "unavailable",
            "processing_mode": "llm_enabled"
            if bool(getattr(chat_agent.llm_client, "available", False))
            else "rule_based",
            "agents_count": len(agents_status),
        }

        return {
            "system_status": "healthy",
            "agents_status": agents_status,
            "langgraph_available": LANGGRAPH_AVAILABLE,
            "chat_llm_available": bool(getattr(chat_agent.llm_client, "available", False)),
            "llm_integration": llm_integration,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as exc:  # noqa: BLE001
        logger.error("System debug failed: %s", exc)
        return {"error": str(exc)}


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(app, host=os.getenv("API_HOST", "0.0.0.0"), port=int(os.getenv("API_PORT", 8005)))
