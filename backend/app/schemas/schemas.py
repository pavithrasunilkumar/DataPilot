from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr


# ---------- Auth ----------

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: str | None

    model_config = ConfigDict(from_attributes=True)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Projects ----------

class ProjectCreate(BaseModel):
    name: str


class ProjectOut(BaseModel):
    id: str
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- Datasets ----------

class ColumnProfile(BaseModel):
    column: str
    dtype: str
    missing_pct: float
    duplicate_flagged: bool = False
    outlier_pct: float | None = None
    unique_count: int


class QualityReport(BaseModel):
    row_count: int
    column_count: int
    duplicate_row_pct: float
    quality_score: float
    columns: list[ColumnProfile]
    warnings: list[str] = []


class DatasetOut(BaseModel):
    id: str
    filename: str
    domain: str | None
    row_count: int | None
    column_count: int | None
    quality_score: float | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- AI Analyst ----------

class AskRequest(BaseModel):
    question: str


class SkepticFlag(BaseModel):
    type: str
    severity: str
    message: str


class Critique(BaseModel):
    flags: list[SkepticFlag]
    trust_level: str


class AskResponse(BaseModel):
    question: str
    sql: str
    result: list[dict]
    stat_test: dict | None
    explanation: str
    critique: Critique
    diff_summary: str | None
    compared_insight_id: str | None
    confidence_score: float


class InsightOut(BaseModel):
    id: str
    question: str
    explanation: str | None
    confidence_score: float | None
    diff_summary: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
