"""
Career Counselor Agent
"""

import logging
from typing import Any, Dict, List

from .base_agent import AgentError, BaseAgent

logger = logging.getLogger(__name__)

class CareerCounselorAgent(BaseAgent):
    """Career guidance agent"""

    def __init__(self):
        super().__init__("career_counselor")

        # UAE training programs
        self.uae_programs = {
            "technology": [
                {"name": "Digital Marketing Certificate", "provider": "Dubai Future Academy", "duration": "3 months"},
                {"name": "Data Analysis Bootcamp", "provider": "ADEK Training", "duration": "4 months"}
            ],
            "healthcare": [
                {"name": "Healthcare Administration", "provider": "UAE Health Authority", "duration": "6 months"}
            ],
            "finance": [
                {"name": "Banking Excellence Program", "provider": "Emirates Institute", "duration": "5 months"}
            ]
        }

        self.job_opportunities = {
            "dubai": ["Digital Marketing Specialist", "Customer Service Manager", "Healthcare Administrator"],
            "abu_dhabi": ["Government Affairs Officer", "Banking Specialist", "Project Coordinator"]
        }

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate career enablement recommendations"""
        try:
            personal_info = input_data.get("personal_info", {})
            employment_info = input_data.get("employment_info", {})
            support_request = input_data.get("support_request", {})

            current_job = employment_info.get("job_title", "")
            emirate = personal_info.get("emirate", "dubai")
            career_goals = support_request.get("career_goals", "")

            sector = self._identify_sector(current_job, career_goals)

            baseline = self._rule_based_plan(
                emirate, sector, current_job, career_goals
            )

            if self.llm_client and getattr(self.llm_client, "available", False):
                llm_result = await self._assess_with_llm(personal_info, employment_info, support_request, sector)
                if llm_result:
                    baseline = self._merge_llm_plan(baseline, llm_result)

            await self.log_processing(input_data, baseline, success=True)
            return baseline

        except Exception as e:
            error_msg = f"Career counseling failed: {str(e)}"
            await self.log_processing(input_data, {}, success=False, error_message=error_msg)
            raise AgentError(error_msg)

    def _rule_based_plan(
        self,
        emirate: str,
        sector: str,
        current_job: str,
        career_goals: str,
    ) -> Dict[str, Any]:
        training_programs = self._recommend_training(sector)
        job_matches = self._find_job_opportunities(emirate, sector)

        enablement_plan = {
            "training_recommendations": training_programs,
            "job_opportunities": job_matches,
            "career_progression_path": self._create_progression_path(current_job, career_goals),
            "timeline": "6-12 months",
            "success_metrics": ["Skill certification", "Job placement", "Income improvement"],
        }

        return {
            "success": True,
            "enablement_plan": enablement_plan,
            "career_assessment": {
                "current_sector": sector,
                "growth_potential": "high" if sector in ["technology", "healthcare"] else "medium",
                "skill_gaps": self._identify_skill_gaps(current_job, career_goals),
            },
            "analysis_source": "rule_based",
        }

    def _identify_sector(self, current_job: str, career_goals: str) -> str:
        """Identify career sector"""
        job_fragment = current_job or ""
        goal_fragment = career_goals or ""
        text = f"{job_fragment} {goal_fragment}".strip().lower()

        if any(keyword in text for keyword in ["technology", "digital", "data"]):
            return "technology"
        elif any(keyword in text for keyword in ["healthcare", "medical"]):
            return "healthcare"
        elif any(keyword in text for keyword in ["bank", "finance"]):
            return "finance"
        else:
            return "general"

    def _recommend_training(self, sector: str) -> List[Dict[str, Any]]:
        """Recommend training programs"""
        return self.uae_programs.get(sector, self.uae_programs["technology"])

    def _find_job_opportunities(self, emirate: str, sector: str) -> List[str]:
        """Find job opportunities"""
        return self.job_opportunities.get(emirate, self.job_opportunities["dubai"])[:3]

    def _create_progression_path(self, current_job: str, career_goals: str) -> List[str]:
        """Create career path"""
        return [
            "Complete skills assessment",
            "Enroll in training program",
            "Gain certifications",
            "Apply for positions",
            "Achieve career advancement"
        ]

    def _identify_skill_gaps(self, current_job: str, career_goals: str) -> List[str]:
        """Identify skill gaps"""
        goals_text = (career_goals or "").lower()
        if "digital" in goals_text:
            return ["Digital marketing", "Data analysis"]
        elif "management" in goals_text:
            return ["Leadership skills", "Project management"]
        else:
            return ["Professional development", "Communication skills"]

    async def _assess_with_llm(
        self,
        personal_info: Dict[str, Any],
        employment_info: Dict[str, Any],
        support_request: Dict[str, Any],
        sector: str,
    ) -> Dict[str, Any] | None:
        context = """
Provide tailored career enablement advice for UAE residents. Recommend programmes,
timelines, and next steps, considering local training providers and labour market trends.
Return structured JSON responses.
"""

        prompt = f"""
Applicant information:
Emirate: {personal_info.get('emirate', 'dubai')}
Current job title: {employment_info.get('job_title', 'N/A')}
Employment status: {employment_info.get('employment_status', 'unknown')}
Years of experience: {employment_info.get('years_of_experience', 0)}
Career goals: {support_request.get('career_goals', 'Not provided')}
Support type: {support_request.get('support_type', 'economic_enablement')}

Produce JSON with:
{{
    "success": bool,
    "career_assessment": {{
        "current_sector": "{sector}",
        "growth_potential": "high" | "medium" | "emerging",
        "skill_gaps": list[str]
    }},
    "enablement_plan": {{
        "training_recommendations": list[dict],
        "job_opportunities": list[str],
        "timeline": str,
        "career_progression_path": list[str]
    }},
    "recommended_timeline": str
}}
"""

        expected_format = {
            "success": True,
            "career_assessment": {
                "current_sector": sector,
                "growth_potential": "medium",
                "skill_gaps": ["string"],
            },
            "enablement_plan": {
                "training_recommendations": ["items"],
                "job_opportunities": ["string"],
                "timeline": "string",
                "career_progression_path": ["string"],
            },
            "recommended_timeline": "string",
        }

        try:
            llm_payload = await self.llm_analyze(prompt, context, output_format=expected_format)
            if isinstance(llm_payload, dict) and llm_payload.get("success"):
                return llm_payload
        except Exception as exc:  # noqa: BLE001
            logger.error("LLM career assessment failed: %s", exc)

        return None

    def _merge_llm_plan(self, baseline: Dict[str, Any], llm_result: Dict[str, Any]) -> Dict[str, Any]:
        merged = baseline.copy()

        merged["career_assessment"] = llm_result.get(
            "career_assessment", baseline.get("career_assessment", {})
        )
        merged["enablement_plan"] = llm_result.get(
            "enablement_plan", baseline.get("enablement_plan", {})
        )
        if "recommended_timeline" in llm_result:
            merged["recommended_timeline"] = llm_result["recommended_timeline"]

        merged["analysis_source"] = "llm"
        return merged
