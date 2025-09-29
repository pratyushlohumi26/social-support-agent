"""
UAE-specific data models
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from enum import Enum

class EmirateEnum(str, Enum):
    ABU_DHABI = "abu_dhabi"
    DUBAI = "dubai"
    SHARJAH = "sharjah"
    AJMAN = "ajman"
    FUJAIRAH = "fujairah"
    RAS_AL_KHAIMAH = "ras_al_khaimah"
    UMM_AL_QUWAIN = "umm_al_quwain"

class UAEPersonalInfo(BaseModel):
    """UAE-specific personal information"""
    
    full_name: str = Field(..., min_length=2, max_length=100)
    emirates_id: str = Field(..., pattern=r"^784-\d{4}-\d{7}-\d$")
    nationality: str
    residency_status: str
    emirate: EmirateEnum
    family_size: int = Field(..., ge=1, le=20)
    dependents: int = Field(..., ge=0, le=15)
    mobile_number: str = Field(..., pattern=r"^(\+971|00971|971)?[0-9]{8,9}$")
    marital_status: str
    email: Optional[str] = None

    @validator('dependents')
    def dependents_not_exceed_family(cls, v, values):
        if 'family_size' in values and v >= values['family_size']:
            raise ValueError('Dependents must be less than family size')
        return v

class UAEEmploymentInfo(BaseModel):
    """UAE-specific employment information"""
    
    employment_status: str
    employer_name: Optional[str] = None
    job_title: Optional[str] = None
    monthly_salary: Optional[float] = Field(None, ge=0)
    employment_start_date: Optional[date] = None
    years_of_experience: Optional[int] = Field(None, ge=0, le=50)

class UAESupportRequest(BaseModel):
    """UAE-specific support request"""
    
    support_type: str
    urgency_level: str
    amount_requested: Optional[float] = Field(None, ge=0, le=100000)
    reason_for_support: str = Field(..., min_length=10, max_length=500)
    career_goals: Optional[str] = None

class UAEApplicationData(BaseModel):
    """Complete UAE application data"""
    
    application_id: Optional[str] = None
    submission_date: datetime = Field(default_factory=datetime.now)
    personal_info: UAEPersonalInfo
    employment_info: UAEEmploymentInfo
    support_request: UAESupportRequest
    processing_status: str = Field(default="submitted")
    
    class Config:
        use_enum_values = True