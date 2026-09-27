"""一周食谱计划：AI 生成、查询、按天写入记录"""
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import MealLog, Recipe, SessionLocal, WeeklyPlan, WeeklyPlanItem
from ..llm import LLMError, chat_json
from ..schemas import PlanApplyDayIn, PlanCreateIn, PlanGenerateIn, PlanItemIn
from ..utils import recipe_to_dict
from ..workcalendar import is_workday

router = APIRouter(prefix="/api/plans", tags=["plans"])

VALID_MEALS = ("breakfast", "lunch", "dinner", "snack")
MEAL_ZH = {"breakfast": "早餐", "lunch": "午餐", "dinner": "晚餐", "snack": "加餐"}
WEEKDAY_ZH = ("周一", "周二", "周三", "周四", "周五", "周六", "周日")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def next_monday(today: date) -> date:
    """返回下一个周一（若今天是周一则用下周一，计划面向未来）"""
    days_ahead = 7 - today.isoweekday()  # isoweekday: 周一=1...周日=7
    if days_ahead == 0:
        days_ahead = 7
    return today + timedelta(days=days_ahead)


def _plan_to_dict(db: Session, plan: WeeklyPlan) -> dict:
    items = []
    for it in plan.items:
        items.append({
            "id": it.id,
            "date": it.date.isoformat(),
            "meal_type": it.meal_type,
            "recipe": recipe_to_dict(it.recipe) if it.recipe else None,
        })
    return {
        "id": plan.id,
        "start_date": plan.start_date.isoformat(),
        "end_date": plan.end_date.isoformat(),
        "mode": plan.mode or "manual",
        "note": plan.note,
        "created_at": plan.created_at.isoformat() if plan.created_at else "",
        "items": sorted(items, key=lambda x: (x["date"], VALID_MEALS.index(x["meal_type"]) if x["meal_type"] in VALID_MEALS else 9)),
    }


@router.get("")
def list_plans(db: Session = Depends(get_db)):
    plans = db.query(WeeklyPlan).order_by(WeeklyPlan.start_date.desc()).limit(10).all()
    return [_plan_to_dict(db, p) for p in plans]


@router.get("/current")
def current_plan(db: Session = Depends(get_db)):
    """返回覆盖今天的最新计划；没有则返回最近一个未来的计划，都没有返回 null"""
    today = date.today()
    plan = (
        db.query(WeeklyPlan)
        .filter(WeeklyPlan.start_date <= today, WeeklyPlan.end_date >= today)
        .order_by(WeeklyPlan.created_at.desc())
        .first()
    )
    if not plan:
        plan = (
            db.query(WeeklyPlan)
            .filter(WeeklyPlan.start_date > today)
            .order_by(WeeklyPlan.start_date.asc())
            .first()
        )
    return _plan_to_dict(db, plan) if plan else None


@router.post("/generate")
async def generate_plan(data: PlanGenerateIn | None = None, db: Session = Depends(get_db)):
    """AI 根据历史用餐记录 + 食谱库生成一周计划"""
    data = data or PlanGenerateIn()
    start = data.start_date or next_monday(date.today())
    end = start + timedelta(days=6)

    # 最近 14 天吃过什么（用于避免重复）
    since = date.today() - timedelta(days=14)
    logs = db.query(MealLog).filter(MealLog.date >= since).order_by(MealLog.date.desc()).all()
    history_lines = []
    for log in logs[:60]:
        name = log.recipe.name if log.recipe else (log.custom_name or "未命名")
        meal = MEAL_ZH.get(log.meal_type, "")
        suffix = f"({meal})" if meal else ""
        history_lines.append(f"{log.date.isoformat()}{suffix}: {name}")

    # 食谱库摘要
    recipes = db.query(Recipe).order_by(Recipe.id).all()
    if len(recipes) < 3:
        raise HTTPException(400, "食谱库太少（至少 3 道），请先在「食谱库」添加或用 AI 生成一些菜品")
    recipe_lines = [
        f"- {r.name} [{r.category}] {r.calories:.0f}千卡/份 蛋白{r.protein:.0f}g" for r in recipes[:120]
    ]

    # 周期内的工作日（跳过周末与法定节假日，保留调休补班日）
    all_days = [start + timedelta(days=i) for i in range(7)]
    workdays = [d for d in all_days if is_workday(d)]
    restdays = [d for d in all_days if not is_workday(d)]
    if not workdays:
        raise HTTPException(400, "所选周期内没有工作日（整周都是节假日/周末），无需生成计划")
    workdays_str = "、".join(f"{d.isoformat()}({WEEKDAY_ZH[d.weekday()]})" for d in workdays)
    rest_str = "、".join(f"{d.isoformat()}({WEEKDAY_ZH[d.weekday()]})" for d in restdays) or "无"

    prompt = f"""你是家庭营养规划师。请为家庭的工作日安排一日三餐计划。

需要安排的工作日（已考虑法定节假日与周末调休补班）：
{workdays_str}

休息日（不要安排）：{rest_str}

家庭最近的饮食记录（越靠上越新，请避免近期频繁重复）：
{chr(10).join(history_lines) if history_lines else "（暂无记录）"}

现有食谱库（优先从中选择，也可以新创菜品）：
{chr(10).join(recipe_lines)}

要求：
1. 只为上面列出的工作日安排，每个工作日 早餐 breakfast、午餐 lunch、晚餐 dinner 各一道，晚餐可额外加一道汤 snack 可选
2. 荤素搭配、营养均衡，早餐清淡（粥/蛋/奶/面点），午晚餐有荤有素
3. 一周内菜品尽量不重复，与最近吃过的错开
4. 从食谱库选择的菜直接用原名；新菜要给出合理食材步骤与营养估算（1人份）
5. 只返回 JSON，不要多余文字，格式：
[
  {{"date": "{start.isoformat()}", "meals": [
    {{"meal_type": "breakfast", "name": "菜名", "source": "existing", "calories": 0, "protein": 0, "fat": 0, "carbs": 0, "ingredients": [{{"name": "", "amount": ""}}], "steps": [""], "reason": "一句话理由"}}
  ]}}
]
source 填 existing（食谱库已有）或 new（新菜）。新菜必须带 ingredients/steps/营养字段。"""

    try:
        result = await chat_json([{"role": "user", "content": prompt}])
    except LLMError as e:
        raise HTTPException(502, f"生成计划失败：{e}")

    days = result if isinstance(result, list) else result.get("days", [])
    if not days:
        raise HTTPException(502, "大模型未返回有效的计划数据")

    # 解析并落库：同名菜关联已有食谱，否则创建新食谱
    existing_by_name = {r.name: r for r in recipes}
    created_recipes = []
    items = []
    for day in days:
        if not isinstance(day, dict):
            continue
        try:
            d = date.fromisoformat(str(day.get("date", "")))
        except ValueError:
            continue
        if not (start <= d <= end) or not is_workday(d):
            continue
        for meal in day.get("meals", []):
            if not isinstance(meal, dict):
                continue
            mt = str(meal.get("meal_type", "")).strip()
            if mt not in VALID_MEALS:
                continue
            name = str(meal.get("name", "")).strip()
            if not name:
                continue
            recipe = existing_by_name.get(name)
            if not recipe:
                recipe = Recipe(
                    name=name,
                    category=str(meal.get("category") or "家常菜"),
                    cuisine="家常",
                    description=str(meal.get("reason") or ""),
                    servings=1,
                    calories=_num(meal.get("calories")),
                    protein=_num(meal.get("protein")),
                    fat=_num(meal.get("fat")),
                    carbs=_num(meal.get("carbs")),
                    is_ai_generated=True,
                )
                recipe.ingredients = [
                    {"name": str(x.get("name", "")), "amount": str(x.get("amount", ""))}
                    for x in meal.get("ingredients", []) if isinstance(x, dict)
                ]
                recipe.steps = [str(s) for s in meal.get("steps", []) if s]
                db.add(recipe)
                db.flush()  # 拿到 id
                existing_by_name[name] = recipe
                created_recipes.append(name)
            items.append(WeeklyPlanItem(date=d, meal_type=mt, recipe_id=recipe.id))

    if not items:
        raise HTTPException(502, "未能从大模型输出中解析出有效的计划条目")

    # 同周期旧计划删除，保持一周一份
    db.query(WeeklyPlan).filter(WeeklyPlan.start_date == start).delete()

    plan = WeeklyPlan(
        start_date=start, end_date=end, mode="ai",
        note=f"AI 生成于 {date.today().isoformat()}（仅工作日）· 休息日不安排：{rest_str} · 新增菜品：{'、'.join(created_recipes) if created_recipes else '无'}",
    )
    plan.items = items
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return _plan_to_dict(db, plan)


@router.post("")
def create_plan(data: PlanCreateIn, db: Session = Depends(get_db)):
    """手工创建一个空周计划，之后可逐天挑选菜品"""
    start = data.start_date
    end = start + timedelta(days=6)
    db.query(WeeklyPlan).filter(WeeklyPlan.start_date == start).delete()
    plan = WeeklyPlan(start_date=start, end_date=end, mode="manual", note="手工创建")
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return _plan_to_dict(db, plan)


@router.post("/{plan_id}/items", status_code=201)
def add_plan_item(plan_id: int, data: PlanItemIn, db: Session = Depends(get_db)):
    """往计划里添加一道菜（同一天同一道菜已存在则幂等返回）"""
    plan = db.get(WeeklyPlan, plan_id)
    if not plan:
        raise HTTPException(404, "计划不存在")
    if not (plan.start_date <= data.date <= plan.end_date):
        raise HTTPException(400, "日期不在计划周期内")
    if data.meal_type not in VALID_MEALS:
        raise HTTPException(400, "餐段不合法")
    recipe = db.get(Recipe, data.recipe_id)
    if not recipe:
        raise HTTPException(404, "食谱不存在")
    dup = (
        db.query(WeeklyPlanItem)
        .filter(
            WeeklyPlanItem.plan_id == plan_id,
            WeeklyPlanItem.date == data.date,
            WeeklyPlanItem.recipe_id == data.recipe_id,
        )
        .first()
    )
    if dup:
        return {"ok": True, "duplicate": True, "item": {"id": dup.id}}
    item = WeeklyPlanItem(date=data.date, meal_type=data.meal_type, recipe_id=data.recipe_id)
    plan.items.append(item)
    db.commit()
    return {"ok": True, "duplicate": False, "item": {"id": item.id}}


@router.delete("/items/{item_id}")
def delete_plan_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(WeeklyPlanItem, item_id)
    if not item:
        raise HTTPException(404, "计划项不存在")
    db.delete(item)
    db.commit()
    return {"ok": True}


@router.post("/{plan_id}/apply-day")
def apply_plan_day(plan_id: int, data: PlanApplyDayIn, db: Session = Depends(get_db)):
    """把计划中某一天的菜品一键写入当日用餐记录"""
    plan = db.get(WeeklyPlan, plan_id)
    if not plan:
        raise HTTPException(404, "计划不存在")
    items = [it for it in plan.items if it.date == data.date]
    if not items:
        raise HTTPException(400, f"计划中 {data.date} 没有菜品")
    added = []
    for it in items:
        log = MealLog(date=data.date, meal_type=it.meal_type, recipe_id=it.recipe_id, servings=1)
        db.add(log)
        added.append(it.recipe.name if it.recipe else str(it.recipe_id))
    db.commit()
    return {"ok": True, "added": added}


@router.delete("/{plan_id}")
def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.get(WeeklyPlan, plan_id)
    if not plan:
        raise HTTPException(404, "计划不存在")
    db.delete(plan)
    db.commit()
    return {"ok": True}


def _num(v) -> float:
    try:
        return float(v) or 0
    except (TypeError, ValueError):
        return 0
