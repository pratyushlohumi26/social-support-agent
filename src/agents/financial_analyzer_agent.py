"""
Financial Analyzer Agent
"""

import logging
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentError

logger = logging.getLogger(__name__)

class FinancialAnalyzerAgent(BaseAgent):
    """UAE financial analysis agent"""

    def __init__(self):
        super().__init__("financial_analyzer")

        # UAE income thresholds
        self.uae_thresholds = {
            "dubai": {"low": 5000, "medium": 15000, "high": 25000},
            "abu_dhabi": {"low": 4500, "medium": 14000, "high": 23000},
            "sharjah": {"low": 4000, "medium": 12000, "high": 20000},
        }

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze financial eligibility"""
        try:
            personal_info = input_data.get("personal_info", {})
            employment_info = input_data.get("employment_info", {})
            support_request = input_data.get("support_request", {})

            emirate = personal_info.get("emirate", "dubai")
            monthly_salary = employment_info.get("monthly_salary", 0)
            family_size = personal_info.get("family_size", 1)

            baseline = self._rule_based_assessment(
                emirate, monthly_salary, family_size, employment_info, support_request
            )

            if self.llm_client and getattr(self.llm_client, "available", False):
                llm_result = await self._analyze_with_llm(personal_info, employment_info, support_request)
                if llm_result:
                    baseline = self._merge_llm_assessment(baseline, llm_result)

            await self.log_processing(input_data, baseline, success=True)
            return baseline

        except Exception as e:
            error_msg = f"Financial analysis failed: {str(e)}"
            await self.log_processing(input_data, {}, success=False, error_message=error_msg)
            raise AgentError(error_msg)

    def _rule_based_assessment(
        self,
        emirate: str,
        monthly_salary: float,
        family_size: int,
        employment_info: Dict[str, Any],
        support_request: Dict[str, Any],
    ) -> Dict[str, Any]:
        eligibility_score = self._calculate_eligibility_score(
            emirate, monthly_salary, family_size, employment_info
        )

        if eligibility_score >= 80:
            recommendation = "approve"
            risk_level = "low"
        elif eligibility_score >= 60:
            recommendation = "conditional_approve"
            risk_level = "medium"
        elif eligibility_score >= 40:
            recommendation = "review_required"
            risk_level = "medium"
        else:
            recommendation = "soft_decline"
            risk_level = "high"

        requested_amount = support_request.get("amount_requested", 0)
        recommended_amount = (
            min(requested_amount, monthly_salary * 6)
            if recommendation != "soft_decline"
            else 0
        )

        return {
            "success": True,
            "eligibility_score": eligibility_score,
            "decision_recommendation": recommendation,
            "recommended_support_amount": recommended_amount,
            "risk_level": risk_level,
            "risk_factors": self._identify_risk_factors(monthly_salary, family_size),
            "uae_assessment": {
                "emirate": emirate,
                "income_category": self._categorize_income(emirate, monthly_salary),
            },
            "analysis_source": "rule_based",
        }

    def _calculate_eligibility_score(self, emirate: str, monthly_salary: float, 
                                   family_size: int, employment_info: Dict) -> int:
        """Calculate UAE eligibility score"""
        score = 0

        # Income assessment (40 points)
        thresholds = self.uae_thresholds.get(emirate, self.uae_thresholds["dubai"])
        if monthly_salary <= thresholds["low"]:
            score += 40  # Higher need
        elif monthly_salary <= thresholds["medium"]:
            score += 30
        else:
            score += 20

        # Family size (30 points)
        if family_size >= 5:
            score += 30
        elif family_size >= 3:
            score += 20
        else:
            score += 10

        # Employment status (30 points)
        employment_status = employment_info.get("employment_status", "")
        if employment_status == "employed":
            score += 30
        elif employment_status == "self_employed":
            score += 20
        else:
            score += 30  # Higher need for unemployed

        return min(score, 100)

    def _categorize_income(self, emirate: str, monthly_salary: float) -> str:
        """Categorize income level"""
        thresholds = self.uae_thresholds.get(emirate, self.uae_thresholds["dubai"])

        if monthly_salary <= thresholds["low"]:
            return "low_income"
        elif monthly_salary <= thresholds["medium"]:
            return "medium_income"
        else:
            return "high_income"

    def _identify_risk_factors(self, monthly_salary: float, family_size: int) -> List[str]:
        """Identify risk factors"""
        risk_factors = []

        if monthly_salary == 0:
            risk_factors.append("No current income")
        elif monthly_salary < 3000:
            risk_factors.append("Very low income level")

        if family_size > 5:
            risk_factors.append("Large family size")

        return risk_factors

    async def _analyze_with_llm(
        self,
        personal_info: Dict[str, Any],
        employment_info: Dict[str, Any],
        support_request: Dict[str, Any],
    ) -> Dict[str, Any] | None:
        context = """
You are a financial analyst for UAE social support programmes. Consider emirate-specific
income thresholds, family size pressure, employment stability, and urgency when assessing
applications. Always provide numeric scores between 0 and 100.
"""

        prompt = f"""
Evaluate this application:

Emirate: {personal_info.get('emirate', 'dubai')}
Family Size: {personal_info.get('family_size', 1)}
Dependents: {personal_info.get('dependents', 0)}
Nationality: {personal_info.get('nationality', 'unknown')}
Residency Status: {personal_info.get('residency_status', 'unknown')}

Employment Status: {employment_info.get('employment_status', 'unknown')}
Monthly Salary: {employment_info.get('monthly_salary', 0)}
Job Title: {employment_info.get('job_title', 'unknown')}

Support Type: {support_request.get('support_type', 'financial_assistance')}
Amount Requested: {support_request.get('amount_requested', 0)}
Reason: {support_request.get('reason_for_support', 'not specified')}
Urgency: {support_request.get('urgency_level', 'medium')}

Return JSON with:
{{
    "success": bool,
    "eligibility_score": int,
    "decision_recommendation": "approve" | "conditional_approve" | "review_required" | "soft_decline",
    "recommended_support_amount": float,
    "support_duration_months": int,
    "risk_level": "low" | "medium" | "high",
    "risk_factors": list[str],
    "analysis_reasoning": str
}}
"""

        expected_format = {
            "success": True,
            "eligibility_score": 0,
            "decision_recommendation": "approve",
            "recommended_support_amount": 0.0,
            "support_duration_months": 0,
            "risk_level": "medium",
            "risk_factors": ["string"],
            "analysis_reasoning": "text",
        }

        try:
            llm_payload = await self.llm_analyze(prompt, context, output_format=expected_format)
            if isinstance(llm_payload, dict) and llm_payload.get("success"):
                return llm_payload
        except Exception as exc:  # noqa: BLE001
            logger.error("LLM financial analysis failed: %s", exc)

        return None

    def _merge_llm_assessment(
        self, baseline: Dict[str, Any], llm_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        merged = baseline.copy()

        merged.update({
            "eligibility_score": llm_result.get("eligibility_score", baseline["eligibility_score"]),
            "decision_recommendation": llm_result.get(
                "decision_recommendation", baseline["decision_recommendation"]
            ),
            "recommended_support_amount": llm_result.get(
                "recommended_support_amount", baseline["recommended_support_amount"]
            ),
            "risk_level": llm_result.get("risk_level", baseline["risk_level"]),
            "risk_factors": llm_result.get("risk_factors", baseline["risk_factors"]),
        })

        if "support_duration_months" in llm_result:
            merged["support_duration_months"] = llm_result["support_duration_months"]
        if "analysis_reasoning" in llm_result:
            merged["analysis_reasoning"] = llm_result["analysis_reasoning"]

        merged["analysis_source"] = "llm"
        return merged
