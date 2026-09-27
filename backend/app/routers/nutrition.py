"""营养统计与 AI 膳食分析"""
from datetime import date as date_cls, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import MealLog, SessionLocal
from ..llm import LLMError, chat
from ..schemas import AIAnalyzeIn, MEAL_TYPE_NAMES
from ..utils import recipe_to_dict

router = APIRouter(prefix="/api/nutrition", tags=["nutrition"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _summarize_range(db: Session, start: date_cls, end: date_cls) -> list[dict]:
    logs = (
        db.query(MealLog)
        .filter(MealLog.date >= start, MealLog.date <= end)
        .order_by(MealLog.date)
        .all()
    )
    by_date: dict[date, dict] = {}
    for log in logs:
        rec = log.recipe
        factor = log.servings
        calories = (rec.calories if rec else 0) * factor
        protein = (rec.protein if rec else 0) * factor
        fat = (rec.fat if rec else 0) * factor
        carbs = (rec.carbs if rec else 0) * factor
        entry = by_date.setdefault(
            log.date, {"date": log.date.isoformat(), "meals": 0, "calories": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0}
        )
        entry["meals"] += 1
        entry["calories"] += calories
        entry["protein"] += protein
        entry["fat"] += fat
        entry["carbs"] += carbs
    # 补齐空白天
    result = []
    d = start
    while d <= end:
        result.append(by_date.get(d) or {"date": d.isoformat(), "meals": 0, "calories": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0})
        d += timedelta(days=1)
    return result


@router.get("/daily")
def daily_nutrition(date: str, db: Session = Depends(get_db)):
    try:
        d = date_cls.fromisoformat(date)
    except ValueError:
        raise HTTPException(400, "日期格式错误")
    rows = _summarize_range(db, d, d)
    return rows[0]


@router.get("/range")
def range_nutrition(start: str, end: str, db: Session = Depends(get_db)):
    try:
        s, e = date_cls.fromisoformat(start), date_cls.fromisoformat(end)
    except ValueError:
        raise HTTPException(400, "日期格式错误")
    if s > e:
        raise HTTPException(400, "开始日期不能晚于结束日期")
    if (e - s).days > 62:
        raise HTTPException(400, "时间范围不能超过 62 天")
    return _summarize_range(db, s, e)


@router.post("/ai-analyze")
async def ai_analyze(data: AIAnalyzeIn, db: Session = Depends(get_db)):
    """AI 分析一段时间内的饮食营养并给出建议"""
    end = data.start_date + timedelta(days=data.days - 1)
    daily_rows = _summarize_range(db, data.start_date, end)

    logs = (
        db.query(MealLog)
        .filter(MealLog.date >= data.start_date, MealLog.date <= end)
        .order_by(MealLog.date)
        .all()
    )
    detail_lines = []
    for log in logs:
        name = log.recipe.name if log.recipe else (log.custom_name or "未命名")
        meal = MEAL_TYPE_NAMES.get(log.meal_type, log.meal_type)
        detail_lines.append(f"{log.date.isoformat()} {meal}: {name} x{log.servings}份")

    total = {
        k: round(sum(r[k] for r in daily_rows), 1)
        for k in ("calories", "protein", "fat", "carbs")
    }
    avg = {k: round(v / data.days, 1) for k, v in total.items()}

    prompt = f"""你是专业家庭营养师。请分析以下家庭近 {data.days} 天的饮食数据（{data.start_date} 至 {end}）：

每日营养摄入：
{chr(10).join(f"{r['date']}: {r['calories']:.0f}千卡, 蛋白{r['protein']:.0f}g, 脂肪{r['fat']:.0f}g, 碳水{r['carbs']:.0f}g" for r in daily_rows)}

期间总计：{total['calories']:.0f}千卡 / 蛋白{total['protein']}g / 脂肪{total['fat']}g / 碳水{total['carbs']}g
日均：{avg['calories']}千卡 / 蛋白{avg['protein']}g / 脂肪{avg['fat']}g / 碳水{avg['carbs']}g

具体吃了什么：
{chr(10).join(detail_lines) if detail_lines else "（无记录）"}

请用中文输出分析报告（纯文本，可用少量表情符号），包含：
1. 总体评价（对照一般成人膳食参考：日热量 1800-2400 千卡、蛋白质 55-65g、脂肪供能 20-30%、碳水供能 50-65%）
2. 做得好的地方
3. 存在的问题（营养失衡、重复单调、蔬果不足等）
4. 具体改进建议（可推荐 2-3 道适合补充的菜）
控制在 400 字以内。"""

    try:
        text = await chat([{"role": "user", "content": prompt}], temperature=0.5)
    except LLMError as e:
        raise HTTPException(502, str(e))

    return {"analysis": text.strip(), "total": total, "average": avg, "days": daily_rows}
