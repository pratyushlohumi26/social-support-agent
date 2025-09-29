"""
Career Counselor Agent
"""

import logging
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentError

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

            # Identify sector
            sector = self._identify_sector(current_job, career_goals)

            # Generate recommendations
            training_programs = self._recommend_training(sector)
            job_matches = self._find_job_opportunities(emirate, sector)

            enablement_plan = {
                "training_recommendations": training_programs,
                "job_opportunities": job_matches,
                "career_progression_path": self._create_progression_path(current_job, career_goals),
                "timeline": "6-12 months",
                "success_metrics": ["Skill certification", "Job placement", "Income improvement"]
            }

            result = {
                "success": True,
                "enablement_plan": enablement_plan,
                "career_assessment": {
                    "current_sector": sector,
                    "growth_potential": "high" if sector in ["technology", "healthcare"] else "medium",
                    "skill_gaps": self._identify_skill_gaps(current_job, career_goals)
                }
            }

            await self.log_processing(input_data, result, success=True)
            return result

        except Exception as e:
            error_msg = f"Career counseling failed: {str(e)}"
            await self.log_processing(input_data, {}, success=False, error_message=error_msg)
            raise AgentError(error_msg)

    def _identify_sector(self, current_job: str, career_goals: str) -> str:
        """Identify career sector"""
        text = (current_job + " " + career_goals).lower()

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
        if "digital" in career_goals.lower():
            return ["Digital marketing", "Data analysis"]
        elif "management" in career_goals.lower():
            return ["Leadership skills", "Project management"]
        else:
            return ["Professional development", "Communication skills"]
