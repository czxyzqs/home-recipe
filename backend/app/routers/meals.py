"""每日用餐记录"""
from datetime import date as date_cls

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import MealLog, SessionLocal
from ..schemas import MealLogIn
from ..utils import recipe_to_dict

router = APIRouter(prefix="/api/meals", tags=["meals"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _log_to_dict(log: MealLog) -> dict:
    return {
        "id": log.id,
        "date": log.date.isoformat(),
        "meal_type": log.meal_type,
        "recipe_id": log.recipe_id,
        "custom_name": log.custom_name,
        "servings": log.servings,
        "note": log.note,
        "recipe": recipe_to_dict(log.recipe) if log.recipe else None,
    }


@router.get("")
def list_meals(date: str, db: Session = Depends(get_db)):
    try:
        d = date_cls.fromisoformat(date)
    except ValueError:
        raise HTTPException(400, "日期格式错误，应为 YYYY-MM-DD")
    logs = (
        db.query(MealLog)
        .filter(MealLog.date == d)
        .order_by(MealLog.id)
        .all()
    )
    return [_log_to_dict(l) for l in logs]


@router.post("", status_code=201)
def add_meal(data: MealLogIn, db: Session = Depends(get_db)):
    if not data.recipe_id and not data.custom_name.strip():
        raise HTTPException(400, "必须选择食谱或填写菜名")
    log = MealLog(
        date=data.date,
        meal_type=data.meal_type,
        recipe_id=data.recipe_id,
        custom_name=data.custom_name.strip(),
        servings=data.servings,
        note=data.note,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return _log_to_dict(log)


@router.put("/{log_id}")
def update_meal(log_id: int, data: MealLogIn, db: Session = Depends(get_db)):
    log = db.get(MealLog, log_id)
    if not log:
        raise HTTPException(404, "记录不存在")
    log.date = data.date
    log.meal_type = data.meal_type
    log.recipe_id = data.recipe_id
    log.custom_name = data.custom_name.strip()
    log.servings = data.servings
    log.note = data.note
    db.commit()
    return _log_to_dict(log)


@router.delete("/{log_id}")
def delete_meal(log_id: int, db: Session = Depends(get_db)):
    log = db.get(MealLog, log_id)
    if not log:
        raise HTTPException(404, "记录不存在")
    db.delete(log)
    db.commit()
    return {"ok": True}
