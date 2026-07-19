import os
import uuid

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import User, Project, Dataset
from app.data.profiling import profile_dataframe
from app.data.cleaning import auto_clean
from app.rag.auto_context import detect_domain, build_schema_descriptions, build_starter_glossary
from app.rag.store import index_schema_docs, index_glossary_terms
from app.data.auto_analysis import generate_autonomous_summary
from app.dashboard.generator import generate_dashboard
from app.export.report_generator import generate_pdf_report
from app.schemas.schemas import DatasetOut, QualityReport

router = APIRouter(prefix="/datasets", tags=["datasets"])

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json"}


def _read_dataframe(file_path: str) -> pd.DataFrame:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".csv":
        return pd.read_csv(file_path)
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(file_path)
    if ext == ".json":
        return pd.read_json(file_path)
    raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")


@router.post("/upload", response_model=DatasetOut, status_code=201)
async def upload_dataset(
    project_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.owner_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file is missing a filename.")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: {sorted(SUPPORTED_EXTENSIONS)}",
        )

    os.makedirs(settings.upload_dir, exist_ok=True)
    stored_filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(settings.upload_dir, stored_filename)

    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.max_upload_mb:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f}MB). Max is {settings.max_upload_mb}MB.",
        )

    with open(file_path, "wb") as f:
        f.write(contents)

    try:
        df = _read_dataframe(file_path)
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"Could not parse file: {e}")

    report = profile_dataframe(df)
    domain = detect_domain(df)

    dataset = Dataset(
        project_id=project.id,
        filename=file.filename,
        file_path=file_path,
        domain=domain,
        quality_report=report,
        quality_score=report["quality_score"],
        row_count=report["row_count"],
        column_count=report["column_count"],
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    # Seed the RAG store immediately so the AI Analyst has dataset-specific
    # grounding from the very first question, not just after a few insights
    # have accumulated.
    index_schema_docs(dataset.id, build_schema_descriptions(df))
    index_glossary_terms(dataset.id, build_starter_glossary(domain))

    return dataset


@router.get("", response_model=list[DatasetOut])
def list_datasets(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.owner_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return (
        db.query(Dataset)
        .filter(Dataset.project_id == project.id)
        .order_by(Dataset.created_at.desc())
        .all()
    )


@router.get("/{dataset_id}/quality-report", response_model=QualityReport)
def get_quality_report(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = (
        db.query(Dataset)
        .join(Project, Dataset.project_id == Project.id)
        .filter(Dataset.id == dataset_id, Project.owner_id == current_user.id)
        .first()
    )
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    return dataset.quality_report


def _get_owned_dataset(dataset_id: str, db: Session, current_user: User) -> Dataset:
    dataset = (
        db.query(Dataset)
        .join(Project, Dataset.project_id == Project.id)
        .filter(Dataset.id == dataset_id, Project.owner_id == current_user.id)
        .first()
    )
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.post("/{dataset_id}/clean")
def clean_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = _get_owned_dataset(dataset_id, db, current_user)
    df = _read_dataframe(dataset.file_path)

    cleaned_df, cleaning_report = auto_clean(df)

    cleaned_filename = f"{uuid.uuid4()}_cleaned.csv"
    cleaned_path = os.path.join(settings.upload_dir, cleaned_filename)
    cleaned_df.to_csv(cleaned_path, index=False)

    dataset.cleaned_file_path = cleaned_path
    dataset.cleaning_report = cleaning_report
    db.commit()

    # Re-profile the cleaned version so the user can see the before/after
    # quality score improvement directly.
    new_report = profile_dataframe(cleaned_df)

    return {
        "cleaning_report": cleaning_report,
        "quality_score_before": dataset.quality_score,
        "quality_score_after": new_report["quality_score"],
        "new_quality_report": new_report,
    }


@router.get("/{dataset_id}/export/cleaned")
def export_cleaned_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = _get_owned_dataset(dataset_id, db, current_user)
    if not dataset.cleaned_file_path or not os.path.exists(dataset.cleaned_file_path):
        raise HTTPException(status_code=404, detail="No cleaned version exists yet — run /clean first.")

    return FileResponse(
        dataset.cleaned_file_path,
        media_type="text/csv",
        filename=f"cleaned_{dataset.filename}",
    )


@router.get("/{dataset_id}/analysis")
def get_autonomous_analysis(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = _get_owned_dataset(dataset_id, db, current_user)
    file_path = dataset.cleaned_file_path or dataset.file_path
    df = _read_dataframe(file_path)
    return generate_autonomous_summary(df, dataset.domain)


@router.get("/{dataset_id}/dashboard")
def get_dashboard(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = _get_owned_dataset(dataset_id, db, current_user)
    file_path = dataset.cleaned_file_path or dataset.file_path
    df = _read_dataframe(file_path)
    return generate_dashboard(df, dataset.quality_score, dataset.domain, dataset.trained_model_info)


@router.post("/{dataset_id}/export/report")
def export_pdf_report(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = _get_owned_dataset(dataset_id, db, current_user)
    file_path = dataset.cleaned_file_path or dataset.file_path
    df = _read_dataframe(file_path)

    autonomous_analysis = generate_autonomous_summary(df, dataset.domain)

    pdf_path = generate_pdf_report(
        filename=dataset.filename,
        quality_report=dataset.quality_report or {},
        autonomous_analysis=autonomous_analysis,
        trained_model_info=dataset.trained_model_info,
        domain=dataset.domain,
    )

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"datapilot_report_{dataset.filename.rsplit('.', 1)[0]}.pdf",
    )
