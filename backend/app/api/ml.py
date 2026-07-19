from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import User, Project, Dataset
from app.ai_analyst.query_executor import load_dataframe
from app.ml.classifier import train_classifier, UnsupportedTargetError

router = APIRouter(prefix="/ml", tags=["machine-learning"])


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


@router.post("/{dataset_id}/train")
def train(
    dataset_id: str,
    target_column: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = _get_owned_dataset(dataset_id, db, current_user)

    # Train on the cleaned file if it exists, otherwise the raw upload.
    file_path = dataset.cleaned_file_path or dataset.file_path
    df = load_dataframe(file_path)

    try:
        result = train_classifier(df, target_column)
    except UnsupportedTargetError as e:
        raise HTTPException(status_code=400, detail=str(e))

    dataset.trained_model_info = result
    db.commit()

    return result


@router.get("/{dataset_id}/model-info")
def get_model_info(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = _get_owned_dataset(dataset_id, db, current_user)
    if not dataset.trained_model_info:
        raise HTTPException(status_code=404, detail="No model has been trained for this dataset yet.")
    return dataset.trained_model_info
