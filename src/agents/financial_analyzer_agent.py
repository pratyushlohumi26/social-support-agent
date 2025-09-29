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

            # Calculate eligibility score
            eligibility_score = self._calculate_eligibility_score(
                emirate, monthly_salary, family_size, employment_info
            )

            # Determine recommendation
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

            # Calculate support amount
            requested_amount = support_request.get("amount_requested", 0)
            recommended_amount = min(requested_amount, monthly_salary * 6) if recommendation != "soft_decline" else 0

            result = {
                "success": True,
                "eligibility_score": eligibility_score,
                "decision_recommendation": recommendation,
                "recommended_support_amount": recommended_amount,
                "risk_level": risk_level,
                "risk_factors": self._identify_risk_factors(monthly_salary, family_size),
                "uae_assessment": {
                    "emirate": emirate,
                    "income_category": self._categorize_income(emirate, monthly_salary)
                }
            }

            await self.log_processing(input_data, result, success=True)
            return result

        except Exception as e:
            error_msg = f"Financial analysis failed: {str(e)}"
            await self.log_processing(input_data, {}, success=False, error_message=error_msg)
            raise AgentError(error_msg)

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
