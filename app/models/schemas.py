from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ReportInfo(BaseModel):
    id: int
    company_id: int
    filename: str
    report_type: Optional[str]
    report_period: Optional[str]
    report_year: Optional[int]
    report_quarter: Optional[int]
    upload_date: datetime
    file_size: int
    status: str

    class Config:
        from_attributes = True


# ============================================================================
# COMPANY SCHEMAS
# ============================================================================

class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    ticker: Optional[str] = Field(None, max_length=10)
    description: Optional[str] = None
    industry: Optional[str] = Field(None, max_length=100)


class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    ticker: Optional[str] = Field(None, max_length=10)
    description: Optional[str] = None
    industry: Optional[str] = Field(None, max_length=100)


class CompanyResponse(BaseModel):
    id: int
    name: str
    ticker: Optional[str]
    description: Optional[str]
    industry: Optional[str]
    created_at: datetime
    updated_at: datetime
    reports_count: int = 0

    class Config:
        from_attributes = True


class CompanyDetail(CompanyResponse):
    reports: List['ReportInfo'] = []


# ============================================================================
# REPORT SCHEMAS
# ============================================================================

class ReportUploadResponse(BaseModel):
    id: int
    company_id: int
    company_name: str
    filename: str
    report_type: Optional[str]
    report_period: Optional[str]
    upload_date: datetime
    file_size: int
    status: str


class ReportInfo(BaseModel):
    id: int
    company_id: int
    filename: str
    report_type: Optional[str]
    report_period: Optional[str]
    report_year: Optional[int]
    report_quarter: Optional[int]
    upload_date: datetime
    file_size: int
    status: str

    class Config:
        from_attributes = True


class ReportDetail(ReportInfo):
    key_metrics: Optional[dict] = None
    summary: Optional[str] = None
    extracted_text_length: Optional[int] = None


# ============================================================================
# CHAT SCHEMAS
# ============================================================================

class ChatMessage(BaseModel):
    role: MessageRole
    content: str
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    message: str
    company_id: int  # ZMIANA: Teraz wymagane company_id zamiast report_id
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    company_name: str
    reports_used: int  # Liczba raportów użytych w kontekście
    suggestions: Optional[List[str]] = None


class SessionInfo(BaseModel):
    session_id: str
    company_id: int
    company_name: str
    created_at: datetime
    updated_at: datetime
    messages_count: int = 0


# ============================================================================
# ANALYSIS SCHEMAS
# ============================================================================

class AnalysisRequest(BaseModel):
    company_id: int
    analysis_type: str = Field(..., description="Type: summary, metrics, trends, comparison")
    period_filter: Optional[str] = None  # np. "2024", "Q3 2024"


class AnalysisResponse(BaseModel):
    company_id: int
    company_name: str
    analysis_type: str
    result: dict
    reports_analyzed: int
    generated_at: datetime


class FinancialMetrics(BaseModel):
    revenue: Optional[float] = None
    net_income: Optional[float] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    equity: Optional[float] = None
    operating_income: Optional[float] = None

class SessionInfo(BaseModel):
    session_id: str
    report_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime