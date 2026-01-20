"""
Decision Orchestrator Agent
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from typing import List as _List
try:
    from .base_agent import BaseAgent, AgentError
except ImportError:
    from base_agent import BaseAgent, AgentError
from .document_processor_agent import DocumentProcessorAgent
from .financial_analyzer_agent import FinancialAnalyzerAgent
from .career_counselor_agent import CareerCounselorAgent
from .chat_assistant_agent import ChatAssistantAgent
from config.settings import settings

logger = logging.getLogger(__name__)

class OrchestratorAgent(BaseAgent):
    """Main orchestration agent"""

    def __init__(self):
        super().__init__("decision_orchestrator")

        # Initialize sub-agents
        self.document_agent = DocumentProcessorAgent()
        self.financial_agent = FinancialAnalyzerAgent()
        self.career_agent = CareerCounselorAgent()
        self.chat_agent = ChatAssistantAgent()

    async def process(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate complete processing"""
        try:
            processing_results = {
                "application_id": application_data.get("application_id"),
                "processing_stages": {},
                "final_decision": {},
                "processing_timeline": []
            }

            # Stage 1: Document Processing
            logger.info(f"Processing application {application_data.get('application_id')}")
            doc_results = await self.document_agent.process(application_data)
            processing_results["processing_stages"]["document_processing"] = doc_results

            # Check for missing or invalid documents
            processed_docs = set(doc_results.get("documents_processed", []))
            required_docs = set(settings.REQUIRED_DOCUMENT_TYPES)
            missing_docs = list(required_docs - processed_docs)
            doc_results["missing_documents"] = missing_docs

            if not doc_results.get("success") or not doc_results.get("documents_valid") or missing_docs:
                return await self._handle_document_failure(processing_results, doc_results, missing_docs)

            # Stage 2: Financial Analysis
            enhanced_data = {**application_data, **doc_results}
            financial_results = await self.financial_agent.process(enhanced_data)
            processing_results["processing_stages"]["financial_analysis"] = financial_results

            # Stage 3: Career Assessment
            career_results = await self.career_agent.process(enhanced_data)
            processing_results["processing_stages"]["career_assessment"] = career_results

            # Stage 4: Final Decision
            final_decision = await self._make_final_decision(financial_results, career_results)
            processing_results["final_decision"] = final_decision

            await self.log_processing(application_data, processing_results, success=True)
            return processing_results

        except Exception as e:
            error_msg = f"Orchestration failed: {str(e)}"
            await self.log_processing(application_data, {}, success=False, error_message=error_msg)
            raise AgentError(error_msg)

    async def _analyze_finances_with_llm(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced financial analysis using Ollama LLM"""
        
        # Prepare context for LLM
        context = """You are a financial analyst for UAE social support programs. 
        Analyze applications based on UAE-specific criteria including:
        - Income thresholds by emirate (Dubai: 5000/15000/25000 AED low/med/high)
        - Family size impact on cost of living
        - Employment stability factors
        - UAE residency status considerations
        
        Provide assessment scores (0-100) and recommendations."""
        
        # Extract application details
        personal_info = application_data.get("personal_info", {})
        employment_info = application_data.get("employment_info", {})
        support_request = application_data.get("support_request", {})
        
        prompt = f"""
        Analyze this UAE social support application:
        
        Applicant: {personal_info.get('full_name', 'Unknown')}
        Emirate: {personal_info.get('emirate', 'dubai')}
        Family Size: {personal_info.get('family_size', 1)}
        Dependents: {personal_info.get('dependents', 0)}
        Employment: {employment_info.get('employment_status', 'unknown')}
        Monthly Salary: {employment_info.get('monthly_salary', 0)} AED
        Support Requested: {support_request.get('amount_requested', 0)} AED
        Reason: {support_request.get('reason_for_support', 'Not specified')}
        
        Provide detailed financial eligibility analysis.
        """
        
        # Define expected output format
        output_format = {
            "success": bool,
            "eligibility_score": int,
            "decision_recommendation": str,
            "recommended_support_amount": float,
            "risk_level": str,
            "risk_factors": list,
            "analysis_reasoning": str
        }
        
        try:
            # Get LLM analysis
            llm_result = await self.llm_analyze(prompt, context, output_format)
            
            if isinstance(llm_result, dict) and llm_result.get("success"):
                return llm_result
            else:
                # Fallback to rule-based analysis
                return await self._analyze_finances_rule_based(application_data)
                
        except Exception as e:
            logger.error(f"LLM financial analysis failed: {e}")
            return await self._analyze_finances_rule_based(application_data)

    async def _assess_career_with_llm(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced career assessment using Ollama LLM"""
        
        context = """You are a career counselor for UAE economic enablement programs.
        Assess career development opportunities considering:
        - UAE job market trends and growth sectors
        - Skills gap analysis for digital transformation
        - Training programs available through UAE institutions
        - Career progression pathways in key industries
        
        Focus on practical, achievable recommendations."""
        
        personal_info = application_data.get("personal_info", {})
        employment_info = application_data.get("employment_info", {})
        support_request = application_data.get("support_request", {})
        
        prompt = f"""
        Assess career development opportunities for:
        
        Current Role: {employment_info.get('job_title', 'Not specified')}
        Experience: {employment_info.get('years_of_experience', 0)} years
        Employment Status: {employment_info.get('employment_status', 'unknown')}
        Emirate: {personal_info.get('emirate', 'dubai')}
        Career Goals: {support_request.get('career_goals', 'Not specified')}
        
        Recommend specific training programs and career pathways.
        """
        
        output_format = {
            "success": bool,
            "career_assessment": dict,
            "enablement_plan": dict,
            "growth_potential": str,
            "recommended_timeline": str
        }
        
        try:
            llm_result = await self.llm_analyze(prompt, context, output_format)
            
            if isinstance(llm_result, dict) and llm_result.get("success"):
                return llm_result
            else:
                return await self._assess_career_rule_based(application_data)
                
        except Exception as e:
            logger.error(f"LLM career assessment failed: {e}")
            return await self._assess_career_rule_based(application_data)

    # Add this method to replace the existing _analyze_finances method
    async def _analyze_finances(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """Choose between LLM and rule-based financial analysis"""
        if self.llm_client and getattr(self.llm_client, "available", False):
            return await self._analyze_finances_with_llm(application_data)
        else:
            return await self._analyze_finances_rule_based(application_data)
    
    async def _handle_document_failure(
        self,
        processing_results: Dict[str, Any],
        doc_results: Dict[str, Any],
        missing_docs: _List[str] = None,
    ) -> Dict[str, Any]:
        """Handle document failures or incomplete uploads"""
        missing = missing_docs or []
        processing_results["final_decision"] = {
            "status": "documents_required",
            "decision": "incomplete_application",
            "missing_documents": missing,
            "next_steps": ["Upload missing documents", "Ensure quality", "Resubmit"],
        }
        return processing_results

    async def _make_final_decision(self, financial_results: Dict, career_results: Dict) -> Dict[str, Any]:
        """Make final decision"""

        financial_score = financial_results.get("eligibility_score", 0)
        financial_recommendation = financial_results.get("decision_recommendation", "review")

        if financial_recommendation == "approve" and financial_score >= 75:
            decision_status = "approved"
            support_amount = financial_results.get("recommended_support_amount", 0)
        elif financial_recommendation == "conditional_approve" and financial_score >= 50:
            decision_status = "conditional_approval"
            support_amount = financial_results.get("recommended_support_amount", 0) * 0.7
        else:
            decision_status = "review_required"
            support_amount = 0

        enablement_plan = career_results.get("enablement_plan", {})

        return {
            "status": decision_status,
            "financial_support": {
                "approved_amount": support_amount,
                "duration_months": 6 if support_amount > 0 else 0
            },
            "economic_enablement": {
                "training_programs": enablement_plan.get("training_recommendations", []),
                "job_matching": enablement_plan.get("job_opportunities", [])
            },
            "next_steps": self._generate_next_steps(decision_status)
        }

    def _generate_next_steps(self, decision_status: str) -> List[str]:
        """Generate next steps"""
        if decision_status == "approved":
            return ["Support disbursement", "Training enrollment", "Progress monitoring"]
        elif decision_status == "conditional_approval":
            return ["Complete requirements", "Attend counseling", "Begin training"]
        else:
            return ["Case worker review", "Additional information", "Alternative programs"]
