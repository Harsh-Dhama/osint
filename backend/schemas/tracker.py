from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SearchType(str, Enum):
    PHONE = "phone"
    EMAIL = "email"


class TrackerModule(str, Enum):
    TRUE_NAME = "truename"
    SOCIAL_MEDIA = "social_media"
    UPI_ID = "upi"
    VEHICLE = "vehicle"
    AADHAAR = "aadhaar"
    DEEP_SEARCH = "deep_search"
    LINKED_EMAILS = "linked_emails"
    ALTERNATE_NUMBERS = "alternate_numbers"
    BANK_DETAILS = "bank_details"


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# Module credit costs
MODULE_CREDITS = {
    TrackerModule.TRUE_NAME: 5,
    TrackerModule.SOCIAL_MEDIA: 3,
    TrackerModule.UPI_ID: 10,
    TrackerModule.VEHICLE: 15,
    TrackerModule.AADHAAR: 20,
    TrackerModule.DEEP_SEARCH: 25,
    TrackerModule.LINKED_EMAILS: 8,
    TrackerModule.ALTERNATE_NUMBERS: 10,
    TrackerModule.BANK_DETAILS: 30,
}


class UsernameSearchBase(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)


class UsernameSearchCreate(UsernameSearchBase):
    case_id: Optional[int] = None
    officer_name: Optional[str] = None


class UsernameResultResponse(BaseModel):
    id: int
    search_id: int
    platform: str
    profile_url: Optional[str] = None
    is_available: bool
    registered_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class UsernameSearchResponse(UsernameSearchBase):
    id: int
    case_id: int
    searched_at: datetime
    results: List[UsernameResultResponse] = []

    class Config:
        from_attributes = True


class NumberEmailSearchBase(BaseModel):
    search_type: SearchType
    search_value: str = Field(..., min_length=3, max_length=200)
    
    @field_validator('search_value')
    @classmethod
    def validate_search_value(cls, v, info):
        search_type = info.data.get('search_type')
        if search_type == SearchType.PHONE:
            # Remove all non-digit characters
            digits = ''.join(filter(str.isdigit, v))
            if len(digits) < 10:
                raise ValueError('Phone number must have at least 10 digits')
        elif search_type == SearchType.EMAIL:
            if '@' not in v or '.' not in v:
                raise ValueError('Invalid email format')
        return v


class NumberEmailSearchCreate(NumberEmailSearchBase):
    case_id: int
    modules: List[TrackerModule] = Field(..., min_length=1)
    
    @field_validator('modules')
    @classmethod
    def validate_modules(cls, v):
        if not v:
            raise ValueError('At least one module must be selected')
        return v


class NumberEmailResultResponse(BaseModel):
    id: int
    search_id: int
    module_name: str
    result_type: str
    result_data: Optional[Dict[str, Any]] = None
    source: Optional[str] = None
    confidence: ConfidenceLevel
    retrieved_at: datetime

    class Config:
        from_attributes = True
        use_enum_values = True


class NumberEmailSearchResponse(NumberEmailSearchBase):
    id: int
    case_id: int
    user_id: int
    searched_at: datetime
    credits_used: int
    status: str
    modules_requested: Optional[str] = None
    results: List[NumberEmailResultResponse] = []

    class Config:
        from_attributes = True
        use_enum_values = True


class TrackerSearchRequest(BaseModel):
    """Request to initiate a tracker search"""
    case_id: int
    search_type: SearchType
    search_value: str
    modules: List[TrackerModule]
    accept_disclaimer: bool = Field(..., description="User must accept disclaimer before Aadhaar/sensitive lookups")
    
    @field_validator('accept_disclaimer')
    @classmethod
    def check_disclaimer(cls, v, info):
        modules = info.data.get('modules', [])
        sensitive_modules = [TrackerModule.AADHAAR, TrackerModule.BANK_DETAILS, TrackerModule.VEHICLE]
        if any(m in sensitive_modules for m in modules) and not v:
            raise ValueError('Disclaimer must be accepted for sensitive data lookups')
        return v


class TrackerSearchResponse(BaseModel):
    """Response after initiating a search"""
    search_id: int
    status: str
    credits_required: int
    credits_available: int
    message: str


class TrackerResultData(BaseModel):
    """Structured result data from bot queries"""
    raw_response: str
    parsed_data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class ModuleResultResponse(BaseModel):
    """Individual module result"""
    module_name: TrackerModule
    status: str  # success, failed, pending
    confidence: ConfidenceLevel
    data: Optional[Dict[str, Any]] = None
    source: Optional[str] = None
    error: Optional[str] = None


class ConsolidatedSearchResponse(BaseModel):
    """Complete search results with all modules"""
    search_id: int
    search_type: SearchType
    search_value: str
    case_id: int
    searched_at: datetime
    credits_used: int
    status: str
    module_results: List[ModuleResultResponse]
    summary: Dict[str, Any]  # Cross-module insights
    

class CreditBalance(BaseModel):
    user_id: int
    username: str
    current_balance: int
    total_earned: int
    total_spent: int


class CreditTransactionResponse(BaseModel):
    id: int
    user_id: int
    transaction_type: str
    amount: int
    balance_before: int
    balance_after: int
    module: Optional[str] = None
    description: Optional[str] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True


class CreditTopUpRequest(BaseModel):
    user_id: int
    credits: int = Field(..., gt=0, description="Amount of credits to add")
    description: Optional[str] = Field(None, max_length=500)


class BulkCreditTopUp(BaseModel):
    user_ids: List[int]
    credits_per_user: int = Field(..., gt=0)
    description: Optional[str] = None


class TrackerStatsResponse(BaseModel):
    """Statistics for tracker module"""
    total_searches: int
    phone_searches: int
    email_searches: int
    total_credits_spent: int
    most_used_module: Optional[str] = None
    success_rate: float
    recent_searches: List[Dict[str, Any]]
