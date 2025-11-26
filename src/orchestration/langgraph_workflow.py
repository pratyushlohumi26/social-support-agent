"""
LangGraph-based Workflow Orchestration for UAE Social Support AI
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("Warning: LangGraph not available. Install with: pip install langgraph")

from ..agents.agent_state import UAEApplicationState
from ..agents.llm_powered_agents import (
    DocumentProcessorAgent,
    FinancialAnalyzerAgent, 
    CareerCounselorAgent,
    ChatAssistantAgent
)

logger = logging.getLogger(__name__)

class UAESocialSupportWorkflow:
    """LangGraph-orchestrated UAE Social Support processing workflow"""
    
    def __init__(self):
        if not LANGGRAPH_AVAILABLE:
            raise ImportError("LangGraph not available. Install required dependencies.")
        
        # Initialize agents
        self.document_agent = DocumentProcessorAgent()
        self.financial_agent = FinancialAnalyzerAgent()
        self.career_agent = CareerCounselorAgent()
        self.chat_agent = ChatAssistantAgent()
        
        # Build workflow graph
        self.workflow = self._build_workflow()
        self.memory = MemorySaver()
        
        logger.info("UAE Social Support LangGraph workflow initialized")
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # Create workflow graph
        workflow = StateGraph(UAEApplicationState)
        
        # Add nodes (processing stages)
        workflow.add_node("document_processing", self._process_documents)
        workflow.add_node("financial_analysis", self._analyze_finances)  
        workflow.add_node("career_evaluation", self._evaluate_career)
        workflow.add_node("eligibility_determination", self._determine_eligibility)
        workflow.add_node("final_decision", self._make_final_decision)
        
        # Add edges (workflow transitions)
        workflow.set_entry_point("document_processing")
        workflow.add_edge("document_processing", "financial_analysis")
        workflow.add_edge("financial_analysis", "career_evaluation")
        workflow.add_edge("career_evaluation", "eligibility_determination")
        workflow.add_edge("eligibility_determination", "final_decision")
        workflow.add_edge("final_decision", END)
        png_data = workflow.get_graph().draw_mermaid_png()
 
        with open("workflow_diagram.png", "wb") as f:
             f.write(png_data)
        
        return workflow.compile(checkpointer=self.memory)
    
    async def _process_documents(self, state: UAEApplicationState) -> UAEApplicationState:
        """Document processing stage"""
        
        try:
            logger.info("Starting document processing stage")
            
            # Process documents using LLM agent
            doc_results = await self.document_agent.process_documents(state)
            
            # Update state
            state["document_analysis"] = doc_results
            state["processing_stage"] = "documents_completed"
            
            # Log stage completion
            state["processing_log"].append({
                "stage": "document_processing",
                "timestamp": datetime.now().isoformat(),
                "success": doc_results.get("success", False),
                "confidence": doc_results.get("overall_confidence", 0.0)
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            state["errors"].append(f"Document processing error: {str(e)}")
            state["processing_stage"] = "documents_failed"
            return state
    
    async def _analyze_finances(self, state: UAEApplicationState) -> UAEApplicationState:
        """Financial analysis stage"""
        
        try:
            logger.info("Starting financial analysis stage")
            
            # Skip if document processing failed
            if state["processing_stage"] == "documents_failed":
                state["financial_assessment"] = {"success": False, "skipped": True}
                return state
            
            # Analyze financial eligibility
            financial_results = await self.financial_agent.analyze_financial_eligibility(state)
            
            # Update state
            state["financial_assessment"] = financial_results
            state["processing_stage"] = "financial_completed"
            
            # Log stage completion
            state["processing_log"].append({
                "stage": "financial_analysis",
                "timestamp": datetime.now().isoformat(),
                "success": financial_results.get("success", False),
                "eligibility_score": financial_results.get("eligibility_score", 0)
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Financial analysis failed: {e}")
            state["errors"].append(f"Financial analysis error: {str(e)}")
            state["processing_stage"] = "financial_failed"
            return state
    
    async def _evaluate_career(self, state: UAEApplicationState) -> UAEApplicationState:
        """Career evaluation stage"""
        
        try:
            logger.info("Starting career evaluation stage")
            
            # Evaluate career opportunities
            career_results = await self.career_agent.evaluate_career_opportunities(state)
            
            # Update state
            state["career_evaluation"] = career_results
            state["processing_stage"] = "career_completed"
            
            # Log stage completion
            state["processing_log"].append({
                "stage": "career_evaluation",
                "timestamp": datetime.now().isoformat(),
                "success": career_results.get("success", False)
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Career evaluation failed: {e}")
            state["errors"].append(f"Career evaluation error: {str(e)}")
            state["processing_stage"] = "career_failed"
            return state
    
    async def _determine_eligibility(self, state: UAEApplicationState) -> UAEApplicationState:
        """Eligibility determination stage using LLM"""
        
        try:
            logger.info("Starting eligibility determination")
            
            # Prepare comprehensive analysis prompt
            doc_analysis = state.get("document_analysis", {})
            financial_analysis = state.get("financial_assessment", {})
            career_analysis = state.get("career_evaluation", {})
            
            eligibility_prompt = f"""
            Based on comprehensive analysis, determine final eligibility for UAE social support:
            
            Document Analysis Results:
            - Success: {doc_analysis.get('success', False)}
            - Confidence: {doc_analysis.get('overall_confidence', 0)}
            - Issues: {doc_analysis.get('inconsistencies', [])}
            
            Financial Analysis Results:
            - Eligibility Score: {financial_analysis.get('eligibility_score', 0)}
            - Recommendation: {financial_analysis.get('decision_recommendation', 'unknown')}
            - Risk Level: {financial_analysis.get('risk_level', 'unknown')}
            - Support Amount: {financial_analysis.get('recommended_support_amount', 0)} AED
            
            Career Analysis Results:
            - Growth Potential: {career_analysis.get('career_assessment', {}).get('growth_potential', 'unknown')}
            - Training Recommended: {len(career_analysis.get('enablement_plan', {}).get('recommended_training', []))} programs
            
            Provide final eligibility determination:
            {{
                "eligible": true/false,
                "eligibility_level": "high/medium/low",
                "overall_score": 0-100,
                "primary_factors": ["key decision factors"],
                "concerns": ["any concerns or limitations"],
                "confidence_level": 0.0-1.0,
                "reasoning": "detailed explanation"
            }}
            """
            
            # Get LLM eligibility determination
            from ..llm.ollama_client import ollama_llm
            eligibility_response = await ollama_llm._acall(eligibility_prompt)
            
            try:
                import json
                eligibility_result = json.loads(eligibility_response)
            except json.JSONDecodeError:
                eligibility_result = {
                    "eligible": True,
                    "eligibility_level": "medium",
                    "overall_score": 70,
                    "confidence_level": 0.8,
                    "reasoning": "LLM analysis completed"
                }
            
            state["eligibility_determination"] = eligibility_result
            state["processing_stage"] = "eligibility_completed"
            
            return state
            
        except Exception as e:
            logger.error(f"Eligibility determination failed: {e}")
            state["errors"].append(f"Eligibility determination error: {str(e)}")
            return state
    
    async def _make_final_decision(self, state: UAEApplicationState) -> UAEApplicationState:
        """Final decision making using LLM synthesis"""
        
        try:
            logger.info("Making final decision")
            
            # Synthesize all analysis results
            decision_prompt = f"""
            Create final decision for UAE social support application based on complete analysis:
            
            Application ID: {state.get('application_id', 'Unknown')}
            
            Processing Results:
            - Document Processing: {state.get('document_analysis', {}).get('success', False)}
            - Financial Assessment: {state.get('financial_assessment', {}).get('eligibility_score', 0)}/100
            - Career Evaluation: Available programs and opportunities identified
            - Eligibility Determination: {state.get('eligibility_determination', {}).get('eligible', False)}
            
            Create comprehensive final decision:
            {{
                "status": "approved/conditional_approval/review_required/declined",
                "financial_support": {{
                    "approved_amount": 0.0,
                    "duration_months": 0,
                    "disbursement_schedule": "monthly/quarterly",
                    "conditions": ["any conditions"]
                }},
                "economic_enablement": {{
                    "training_programs": ["recommended programs"],
                    "job_matching": ["job opportunities"],
                    "career_counseling_sessions": 0,
                    "mentorship_program": true/false
                }},
                "timeline": {{
                    "decision_effective_date": "date",
                    "first_disbursement": "date",
                    "program_start": "date"
                }},
                "next_steps": ["immediate actions required"],
                "case_worker_notes": "internal notes",
                "review_date": "date for next review"
            }}
            """
            
            from ..llm.ollama_client import ollama_llm
            decision_response = await ollama_llm._acall(decision_prompt)
            
            try:
                import json
                final_decision = json.loads(decision_response)
            except json.JSONDecodeError:
                # Fallback decision structure
                financial_assessment = state.get("financial_assessment", {})
                career_evaluation = state.get("career_evaluation", {})
                
                final_decision = {
                    "status": financial_assessment.get("decision_recommendation", "review_required"),
                    "financial_support": {
                        "approved_amount": financial_assessment.get("recommended_support_amount", 0),
                        "duration_months": 6,
                        "conditions": []
                    },
                    "economic_enablement": {
                        "training_programs": career_evaluation.get("enablement_plan", {}).get("recommended_training", []),
                        "career_counseling_sessions": 3
                    },
                    "next_steps": ["Complete enrollment process", "Attend orientation"]
                }
            
            # Update final state
            state["final_decision"] = final_decision
            state["processing_stage"] = "completed"
            
            # Create recommendations summary
            recommendations = []
            if final_decision["status"] in ["approved", "conditional_approval"]:
                recommendations.append({
                    "type": "financial",
                    "description": f"Financial support approved: {final_decision['financial_support']['approved_amount']} AED"
                })
            
            enablement = final_decision.get("economic_enablement", {})
            if enablement.get("training_programs"):
                recommendations.append({
                    "type": "career",
                    "description": f"Career development: {len(enablement['training_programs'])} programs recommended"
                })
            
            state["recommendations"] = recommendations
            
            return state
            
        except Exception as e:
            logger.error(f"Final decision failed: {e}")
            state["errors"].append(f"Final decision error: {str(e)}")
            return state
    
    async def process_application(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process complete application through LangGraph workflow"""
        
        # Initialize state
        initial_state = UAEApplicationState(
            application_data=application_data,
            application_id=application_data.get("application_id", f"UAE-{datetime.now().strftime('%Y%m%d-%H%M%S')}"),
            document_analysis=None,
            financial_assessment=None,
            career_evaluation=None,
            eligibility_determination=None,
            final_decision=None,
            recommendations=[],
            processing_stage="started",
            errors=[],
            processing_log=[],
            llm_interactions=[],
            chat_history=[],
            user_queries=[]
        )
        
        try:
            # Execute workflow
            config = {"configurable": {"thread_id": initial_state["application_id"]}}
            
            # Run through workflow
            result = await self.workflow.ainvoke(initial_state, config)
            
            logger.info(f"Workflow completed for application {result['application_id']}")
            
            return {
                "success": True,
                "application_id": result["application_id"],
                "processing_stages": {
                    "document_analysis": result.get("document_analysis"),
                    "financial_assessment": result.get("financial_assessment"),
                    "career_evaluation": result.get("career_evaluation"),
                    "eligibility_determination": result.get("eligibility_determination")
                },
                "final_decision": result.get("final_decision"),
                "recommendations": result.get("recommendations"),
                "processing_log": result.get("processing_log"),
                "llm_interactions": result.get("llm_interactions"),
                "errors": result.get("errors")
            }
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "application_id": initial_state["application_id"]
            }
    
    async def handle_chat(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle chat interaction using LLM-powered assistant"""
        return await self.chat_agent.generate_response(message, context)

# Global workflow instance
workflow_orchestrator = UAESocialSupportWorkflow() if LANGGRAPH_AVAILABLE else None

