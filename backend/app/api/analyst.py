from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import User, Project, Dataset, Insight
from app.schemas.schemas import AskRequest, AskResponse, InsightOut
from app.ai_analyst.graph import run_agentic_analysis
from app.rag.store import index_insight

router = APIRouter(prefix="/analyst", tags=["ai-analyst"])


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


@router.post("/{dataset_id}/ask", response_model=AskResponse)
def ask(
    dataset_id: str,
    payload: AskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = _get_owned_dataset(dataset_id, db, current_user)

    past_insights = (
        db.query(Insight)
        .filter(Insight.dataset_id == dataset.id)
        .order_by(Insight.created_at.desc())
        .limit(50)
        .all()
    )

    result = run_agentic_analysis(dataset.id, payload.question, dataset.file_path, past_insights)

    insight = Insight(
        dataset_id=dataset.id,
        question=payload.question,
        generated_sql=result["sql"],
        result_summary={"rows": result["result"][:20], "stat_test": result.get("stat_test")},
        explanation=result["explanation"],
        confidence_score=result["confidence_score"],
        critique=result["critique"],
        diff_summary=result["diff_summary"],
        compared_insight_id=result["compared_insight_id"],
    )
    db.add(insight)
    db.commit()
    db.refresh(insight)

    # Index this Q&A into the RAG store so future questions on this dataset
    # can retrieve it as prior context / for insight diffing.
    index_insight(dataset.id, insight.id, payload.question, result["explanation"])

    return AskResponse(
        question=payload.question,
        sql=result["sql"],
        result=result["result"],
        stat_test=result["stat_test"],
        explanation=result["explanation"],
        critique=result["critique"],
        diff_summary=result["diff_summary"],
        compared_insight_id=result["compared_insight_id"],
        confidence_score=result["confidence_score"],
    )


@router.get("/{dataset_id}/history", response_model=list[InsightOut])
def history(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = _get_owned_dataset(dataset_id, db, current_user)
    return (
        db.query(Insight)
        .filter(Insight.dataset_id == dataset.id)
        .order_by(Insight.created_at.desc())
        .all()
    )
