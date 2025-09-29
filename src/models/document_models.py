"""
Document processing models
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class EmiratesIdData(BaseModel):
    """Emirates ID extracted data"""
    id_number: str
    full_name_en: str
    full_name_ar: Optional[str] = None
    nationality: str
    date_of_birth: Optional[str] = None
    expiry_date: Optional[str] = None
    confidence_score: float = Field(ge=0, le=1)

class BankStatementData(BaseModel):
    """Bank statement analysis"""
    account_holder: Optional[str] = None
    bank_name: Optional[str] = None
    monthly_income: float = Field(default=0, ge=0)
    monthly_expenses: float = Field(default=0, ge=0)
    financial_stability_score: int = Field(default=0, ge=0, le=100)
    red_flags: List[str] = Field(default_factory=list)

class ProcessedDocument(BaseModel):
    """Processed document container"""
    document_type: str
    extracted_data: Dict[str, Any]
    confidence_score: float = Field(ge=0, le=1)
    processing_timestamp: datetime = Field(default_factory=datetime.now)

class ValidationResult(BaseModel):
    """Document validation result"""
    is_valid: bool
    confidence_score: float
    inconsistencies: List[str] = Field(default_factory=list)
    missing_fields: List[str] = Field(default_factory=list)
