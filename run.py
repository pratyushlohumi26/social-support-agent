#!/usr/bin/env python3
"""
UAE Social Support AI System - Main Entry Point
"""
import asyncio
import logging
from pathlib import Path
import subprocess
import sys
import os
from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    from agents.orchestrator_agent import OrchestratorAgent
    from models.uae_specific_models import UAEPersonalInfo, UAEEmploymentInfo, UAESupportRequest
except ImportError as e:
    logger.error(f"Module import failed: {e}")

API_PORT = int(os.getenv("API_PORT", 8005))

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

async def run_demo():
    """Run UAE demo"""
    print("🇦🇪 UAE Social Support AI Demo")
    try:
        from src.agents.orchestrator_agent import OrchestratorAgent
        orchestrator = OrchestratorAgent()

        sample_data = {
            "application_id": "UAE-2024-001",
            "personal_info": {
                "full_name": "Ahmed Al Mansouri",
                "emirates_id": "784-2024-1234567-1",
                "emirate": "dubai",
                "family_size": 4
            },
            "employment_info": {
                "employment_status": "employed",
                "monthly_salary": 8000
            },
            "support_request": {
                "support_type": "both",
                "amount_requested": 15000,
                "reason_for_support": "Medical expenses and career development"
            }
        }

        result = await orchestrator.process(sample_data)
        print("✅ Demo completed successfully!")
        print(f"Decision: {result['final_decision']['status']}")

    except Exception as e:
        logger.error(f"Demo failed: {e}")

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
        asyncio.run(run_demo())
    elif command == "setup":
        import setup_uae_system
        setup_uae_system.UAESystemSetup().run_complete_setup()
    else:
        print_help()
