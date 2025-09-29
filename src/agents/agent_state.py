"""
LangGraph State Management for UAE Social Support AI
"""

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime

class UAEApplicationState(TypedDict):
    """State for UAE social support application processing"""
    
    # Input data
    application_data: Dict[str, Any]
    application_id: str
    
    # Processing stages
    document_analysis: Optional[Dict[str, Any]]
    financial_assessment: Optional[Dict[str, Any]]
    career_evaluation: Optional[Dict[str, Any]]
    eligibility_determination: Optional[Dict[str, Any]]
    
    # Final outputs
    final_decision: Optional[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    
    # Metadata
    processing_stage: str
    errors: List[str]
    processing_log: List[Dict[str, Any]]
    llm_interactions: List[Dict[str, Any]]
    
    # Chat context
    chat_history: List[Dict[str, str]]
    user_queries: List[str]
