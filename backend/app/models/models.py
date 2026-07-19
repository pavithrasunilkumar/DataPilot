import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, JSON, Float, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    projects: Mapped[list["Project"]] = relationship(back_populates="owner")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner: Mapped["User"] = relationship(back_populates="projects")
    datasets: Mapped[list["Dataset"]] = relationship(back_populates="project")


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    domain: Mapped[str] = mapped_column(String, nullable=True)  # e.g. "retail", "finance"

    # Raw profiling results, stored as JSON so the schema doesn't need to
    # change every time we add a new profiling metric.
    quality_report: Mapped[dict] = mapped_column(JSON, nullable=True)
    quality_score: Mapped[float] = mapped_column(Float, nullable=True)

    row_count: Mapped[int] = mapped_column(nullable=True)
    column_count: Mapped[int] = mapped_column(nullable=True)

    # Populated once /datasets/{id}/clean has been run. The raw upload is
    # never overwritten — cleaning produces a separate file so the original
    # is always recoverable.
    cleaned_file_path: Mapped[str] = mapped_column(String, nullable=True)
    cleaning_report: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Populated once a model has been trained for this dataset (app/ml).
    trained_model_path: Mapped[str] = mapped_column(String, nullable=True)
    trained_model_info: Mapped[dict] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    project: Mapped["Project"] = relationship(back_populates="datasets")
    insights: Mapped[list["Insight"]] = relationship(back_populates="dataset")


class Insight(Base):
    """
    Every AI Analyst question + answer gets stored here.
    This doubles as the RAG memory source for Phase 4 — past insights
    get embedded and retrieved as context for future questions.
    """

    __tablename__ = "insights"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id"), nullable=False)

    question: Mapped[str] = mapped_column(Text, nullable=False)
    generated_sql: Mapped[str] = mapped_column(Text, nullable=True)
    result_summary: Mapped[dict] = mapped_column(JSON, nullable=True)
    explanation: Mapped[str] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=True)

    # Skeptic Agent — a second pass that critiques the explanation above
    # rather than presenting it as unquestionable fact.
    critique: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Insight Diffing — if a similar past question exists for this dataset,
    # this stores a comparison between the old and new conclusion.
    diff_summary: Mapped[str] = mapped_column(Text, nullable=True)
    compared_insight_id: Mapped[str] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    dataset: Mapped["Dataset"] = relationship(back_populates="insights")
