#!/usr/bin/env python3
"""
UAE Social Support AI System - Main Entry Point
"""
import asyncio
import inspect
import json
import logging
import os
import socket
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from agents.orchestrator_agent import OrchestratorAgent
from database.models import Application, Base, Document

API_PORT = int(os.getenv("API_PORT", 8005))

_DEMO_ENGINE = None
_DEMO_SESSION_FACTORY = None


def _get_demo_db_url() -> str:
    db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./social_support.db")
    if db_url.startswith("sqlite+aiosqlite"):
        return db_url.replace("sqlite+aiosqlite", "sqlite", 1)
    if db_url.startswith("sqlite://"):
        return db_url
    logger.warning(
        "Demo persistence falling back to local SQLite database (DATABASE_URL=%s)", db_url
    )
    return "sqlite:///./social_support.db"


def _get_demo_session() -> Session:
    global _DEMO_ENGINE, _DEMO_SESSION_FACTORY

    if _DEMO_ENGINE is None:
        db_url = _get_demo_db_url()
        _DEMO_ENGINE = create_engine(db_url, future=True)
        Base.metadata.create_all(_DEMO_ENGINE)
        _DEMO_SESSION_FACTORY = sessionmaker(
            bind=_DEMO_ENGINE,
            expire_on_commit=False,
            future=True,
        )

    return _DEMO_SESSION_FACTORY()


def _run_coroutine_sync(awaitable):
    iterator = awaitable.__await__() if inspect.iscoroutine(awaitable) else awaitable

    try:
        yielded = next(iterator)
    except StopIteration as exc:  # pragma: no cover - immediate completion
        return exc.value

    while True:
        if inspect.isawaitable(yielded):
            result = _run_coroutine_sync(yielded)
        else:
            raise RuntimeError(f"Unsupported awaitable yielded: {type(yielded)!r}")

        try:
            yielded = iterator.send(result)
        except StopIteration as exc:
            return exc.value


def _can_use_async_runner() -> bool:
    try:
        sock1, sock2 = socket.socketpair()
    except (AttributeError, OSError, PermissionError):
        return False

    sock1.close()
    sock2.close()
    return True


def _persist_demo_application_sync(application_data, processing_result):
    session = _get_demo_session()

    try:
        application_id = application_data.get("application_id")
        personal_info = application_data.get("personal_info", {})
        support_request = application_data.get("support_request", {})
        employment_info = application_data.get("employment_info", {})

        final_decision = processing_result.get("final_decision", {})
        status = (
            final_decision.get("status")
            or application_data.get("processing_status")
            or "processed"
        )

        record = session.execute(
            select(Application).where(Application.application_id == application_id)
        ).scalar_one_or_none()

        if record:
            record.applicant_name = personal_info.get("full_name")
            record.phone = personal_info.get("mobile_number")
            record.email = personal_info.get("email")
            record.support_type = support_request.get("support_type")
            record.status = status
            record.priority = support_request.get("urgency_level")
            record.emirates_id = personal_info.get("emirates_id")
            record.emirate = personal_info.get("emirate")
            record.family_size = personal_info.get("family_size")
            record.monthly_income = employment_info.get("monthly_salary")
            record.application_data = application_data
            record.processing_results = processing_result
            record.decision_data = final_decision
        else:
            record = Application(
                application_id=application_id,
                applicant_name=personal_info.get("full_name"),
                phone=personal_info.get("mobile_number"),
                email=personal_info.get("email"),
                support_type=support_request.get("support_type"),
                status=status,
                priority=support_request.get("urgency_level"),
                emirates_id=personal_info.get("emirates_id"),
                emirate=personal_info.get("emirate"),
                family_size=personal_info.get("family_size"),
                monthly_income=employment_info.get("monthly_salary"),
                application_data=application_data,
                processing_results=processing_result,
                decision_data=final_decision,
            )
            session.add(record)

        session.execute(delete(Document).where(Document.application_id == application_id))

        for document in application_data.get("documents", []) or []:
            session.add(
                Document(
                    application_id=application_id,
                    document_type=document.get("document_type"),
                    filename=document.get("filename"),
                    file_path=document.get("file_path", ""),
                    file_size=document.get("file_size", 0),
                    extraction_data=document.get("extraction_data"),
                    confidence_score=document.get("confidence_score"),
                    validation_status=document.get("status", "uploaded"),
                )
            )

        session.commit()

    except SQLAlchemyError as exc:  # pragma: no cover - logging safety
        session.rollback()
        logger.error("Failed to persist demo application %s: %s", application_id, exc)
    finally:
        session.close()


def run_api():
    """Start the API server"""
    try:
        import uvicorn
        from src.api.main import app
        uvicorn.run(app, host=os.getenv("API_HOST"), port=API_PORT, reload=False)
    except Exception as e:
        logger.error(f"Failed to start API: {e}")

def run_ui():
    """Start the UI"""
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "src/ui/multimodal_app.py", "--server.port", "8501"])
    except Exception as e:
        logger.error(f"Failed to start UI: {e}")


def run_demo():
    """Run UAE demo and persist results."""

    print("🇦🇪 UAE Social Support AI Demo")
    dataset_path = Path("data/synthetic_applicants.json")

    if not dataset_path.exists():
        logger.error("Synthetic applicant dataset missing at %s", dataset_path)
        return

    try:
        with dataset_path.open("r", encoding="utf-8") as dataset_file:
            applicants = json.load(dataset_file)
    except Exception as exc:  # noqa: BLE001
        logger.error("Unable to load synthetic applicants: %s", exc)
        return

    if not isinstance(applicants, list):
        logger.error("Synthetic applicant dataset must be a list of applications")
        return

    async def _run_demo_async():
        orchestrator = OrchestratorAgent()
        results = []

        for index, application in enumerate(applicants, start=1):
            if not isinstance(application, dict):
                logger.warning("Skipping malformed application entry at index %s", index)
                continue

            application_id = application.get("application_id") or f"UAE-DEMO-{index:03d}"
            application["application_id"] = application_id

            try:
                result = await orchestrator.process(application)
                decision = result.get("final_decision", {}).get("status", "unknown")
                _persist_demo_application_sync(application, result)
                results.append((application_id, decision))
                print(f"• {application_id}: decision = {decision}")
            except Exception as exc:  # noqa: BLE001
                logger.error("Processing failed for %s: %s", application_id, exc)
                results.append((application_id, "error"))

        return results

    def _run_demo_sync():
        orchestrator = OrchestratorAgent()
        results = []

        for index, application in enumerate(applicants, start=1):
            if not isinstance(application, dict):
                logger.warning("Skipping malformed application entry at index %s", index)
                continue

            application_id = application.get("application_id") or f"UAE-DEMO-{index:03d}"
            application["application_id"] = application_id

            try:
                result = _run_coroutine_sync(orchestrator.process(application))
                decision = result.get("final_decision", {}).get("status", "unknown")
                _persist_demo_application_sync(application, result)
                results.append((application_id, decision))
                print(f"• {application_id}: decision = {decision}")
            except Exception as sync_exc:  # noqa: BLE001
                logger.error("Processing failed for %s: %s", application_id, sync_exc)
                results.append((application_id, "error"))

        return results

    processed_results = []
    if _can_use_async_runner():
        try:
            processed_results = asyncio.run(_run_demo_async())
        except (PermissionError, OSError, RuntimeError) as exc:
            logger.warning(
                "Async demo runner unavailable (%s); falling back to synchronous execution",
                exc,
            )
            processed_results = _run_demo_sync()
    else:
        logger.warning("Async demo runner not supported on this platform; using synchronous execution")
        processed_results = _run_demo_sync()
    successes = sum(1 for _, status in processed_results if status != "error")
    print("")
    print(f"✅ Demo completed: {successes} / {len(processed_results)} applications processed successfully")

def print_help():
    print("""
🇦🇪 UAE Social Support AI System

Commands:
  api    - Start API server
  ui     - Start web interface  
  demo   - Run UAE demo
  setup  - Run system setup
    """)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "api":
        run_api()
    elif command == "ui":
        run_ui()
    elif command == "demo":
        run_demo()
    elif command == "setup":
        import setup_uae_system
        setup_uae_system.UAESystemSetup().run_complete_setup()
    else:
        print_help()
