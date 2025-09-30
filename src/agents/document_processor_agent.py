"""
Document Processor Agent
"""

import logging
from typing import Any, Dict

from .base_agent import AgentError, BaseAgent

logger = logging.getLogger(__name__)

class DocumentProcessorAgent(BaseAgent):
    """UAE document processing agent"""

    def __init__(self):
        super().__init__("document_processor")

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process UAE documents"""
        try:
            baseline = self._rule_based_result(input_data)

            if self.llm_client and getattr(self.llm_client, "available", False):
                llm_result = await self._analyze_with_llm(input_data)
                if llm_result:
                    baseline = self._merge_llm_results(baseline, llm_result)

            await self.log_processing(input_data, baseline, success=True)
            return baseline

        except Exception as e:
            error_msg = f"Document processing failed: {str(e)}"
            await self.log_processing(input_data, {}, success=False, error_message=error_msg)
            raise AgentError(error_msg)

    def _rule_based_result(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        applicant_name = input_data.get("personal_info", {}).get("full_name", "Unknown")

        return {
            "success": True,
            "documents_processed": ["emirates_id", "bank_statement"],
            "documents_valid": True,
            "extracted_data": {
                "emirates_id": {
                    "id_number": input_data.get("personal_info", {}).get("emirates_id", ""),
                    "name": applicant_name,
                    "confidence": 0.9,
                },
                "bank_statement": {
                    "monthly_income": input_data.get("employment_info", {}).get("monthly_salary", 0),
                    "monthly_expenses": None,
                    "stability_score": 80,
                },
            },
            "analysis_source": "rule_based",
        }

    async def _analyze_with_llm(self, input_data: Dict[str, Any]) -> Dict[str, Any] | None:
        personal_info = input_data.get("personal_info", {})
        employment_info = input_data.get("employment_info", {})

        context = """
You are validating documents for UAE social support applications. Assess Emirates ID,
bank statements, and salary certificates for authenticity, data consistency, and
potential concerns. Return scores between 0 and 1.
"""

        prompt = f"""
Review the following application details and summarise document findings:

Applicant: {personal_info.get('full_name', 'Unknown')}
Emirates ID: {personal_info.get('emirates_id', 'N/A')}
Emirate: {personal_info.get('emirate', 'dubai')}
Employment Status: {employment_info.get('employment_status', 'unknown')}
Monthly Salary: {employment_info.get('monthly_salary', 0)}

Required JSON fields:
{{
    "success": bool,
    "documents_processed": list[str],
    "documents_valid": bool,
    "authenticity_scores": {{"emirates_id": float, "financial_documents": float}},
    "issues_found": list[str],
    "extracted_data": dict,
    "overall_confidence": float
}}
"""

        expected_shape = {
            "success": True,
            "documents_processed": ["string"],
            "documents_valid": True,
            "authenticity_scores": {"emirates_id": 0.0, "financial_documents": 0.0},
            "issues_found": ["string"],
            "extracted_data": {},
            "overall_confidence": 0.0,
        }

        try:
            llm_payload = await self.llm_analyze(prompt, context, output_format=expected_shape)
            if isinstance(llm_payload, dict) and llm_payload.get("success") is not False:
                return llm_payload
        except Exception as exc:  # noqa: BLE001
            logger.error("LLM document analysis failed: %s", exc)

        return None

    def _merge_llm_results(self, baseline: Dict[str, Any], llm_result: Dict[str, Any]) -> Dict[str, Any]:
        merged = baseline.copy()

        merged["documents_processed"] = llm_result.get(
            "documents_processed", baseline.get("documents_processed", [])
        )
        merged["documents_valid"] = llm_result.get("documents_valid", baseline.get("documents_valid", True))
        merged["extracted_data"] = llm_result.get("extracted_data", baseline.get("extracted_data", {}))

        if "authenticity_scores" in llm_result:
            merged["authenticity_scores"] = llm_result["authenticity_scores"]
        if "issues_found" in llm_result:
            merged["issues_found"] = llm_result["issues_found"]
        if "overall_confidence" in llm_result:
            merged["overall_confidence"] = llm_result["overall_confidence"]

        merged["analysis_source"] = "llm"
        return merged
