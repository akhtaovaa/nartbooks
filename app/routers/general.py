"""General purpose routes."""

from fastapi import APIRouter

router = APIRouter(tags=["Общие"])


@router.get("/")
def home():
    return {"message": "Добро пожаловать в NartBooks!"}

