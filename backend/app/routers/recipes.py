"""食谱管理 + AI 生成食谱"""
import math

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import Recipe, SessionLocal
from ..llm import LLMError, chat_json
from ..schemas import RecipeAIGenerateIn, RecipeIn
from ..utils import recipe_to_dict

router = APIRouter(prefix="/api/recipes", tags=["recipes"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _save_recipe(recipe: Recipe, data: RecipeIn) -> Recipe:
    recipe.name = data.name.strip()
    recipe.category = data.category or "家常菜"
    recipe.cuisine = data.cuisine or "家常"
    recipe.description = data.description or ""
    recipe.ingredients = [{"name": i.name, "amount": i.amount} for i in data.ingredients]
    recipe.steps = [s for s in data.steps if s and s.strip()]
    recipe.servings = data.servings or 1
    recipe.calories = data.calories or 0
    recipe.protein = data.protein or 0
    recipe.fat = data.fat or 0
    recipe.carbs = data.carbs or 0
    recipe.tags = data.tags or []
    recipe.is_ai_generated = data.is_ai_generated
    return recipe


@router.get("")
def list_recipes(q: str = "", category: str = "", db: Session = Depends(get_db)):
    query = db.query(Recipe)
    if q:
        query = query.filter(
            or_(
                Recipe.name.contains(q),
                Recipe.description.contains(q),
                Recipe.ingredients_text.contains(q),
            )
        )
    if category:
        query = query.filter(Recipe.category == category)
    rows = query.order_by(Recipe.updated_at.desc()).all()
    return [recipe_to_dict(r) for r in rows]


@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    rows = db.query(Recipe.category).distinct().all()
    return [r[0] for r in rows if r[0]]


@router.post("", status_code=201)
def create_recipe(data: RecipeIn, db: Session = Depends(get_db)):
    if db.query(Recipe).filter(Recipe.name == data.name.strip()).first():
        raise HTTPException(400, f"食谱「{data.name}」已存在")
    recipe = _save_recipe(Recipe(), data)
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    return recipe_to_dict(recipe)


@router.get("/{recipe_id}")
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(404, "食谱不存在")
    return recipe_to_dict(recipe)


@router.put("/{recipe_id}")
def update_recipe(recipe_id: int, data: RecipeIn, db: Session = Depends(get_db)):
    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(404, "食谱不存在")
    dup = db.query(Recipe).filter(Recipe.name == data.name.strip(), Recipe.id != recipe_id).first()
    if dup:
        raise HTTPException(400, f"食谱「{data.name}」已存在")
    _save_recipe(recipe, data)
    db.commit()
    return recipe_to_dict(recipe)


@router.delete("/{recipe_id}")
def delete_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(404, "食谱不存在")
    db.delete(recipe)
    db.commit()
    return {"ok": True}


@router.post("/ai-generate")
async def ai_generate_recipe(data: RecipeAIGenerateIn, db: Session = Depends(get_db)):
    """根据食材/想法用大模型生成食谱并入库"""
    prompt = f"""你是家庭菜谱专家。请根据以下需求设计 {data.count} 道家常菜谱：
「{data.prompt}」

要求：
1. 菜品适合家庭制作，食材易得，步骤清晰（3-6 步）
2. 营养数据按 1 人份估算（千卡、蛋白质/脂肪/碳水克数），数值合理
3. 只返回 JSON，不要多余文字，格式：
[
  {{
    "name": "菜名",
    "category": "荤菜/素菜/汤羹/家常菜 之一",
    "cuisine": "菜系",
    "description": "一句话介绍",
    "ingredients": [{{"name": "食材", "amount": "用量"}}],
    "steps": ["步骤1", "步骤2"],
    "calories": 0, "protein": 0, "fat": 0, "carbs": 0,
    "tags": ["标签"]
  }}
]"""
    try:
        result = await chat_json([{"role": "user", "content": prompt}])
    except LLMError as e:
        raise HTTPException(502, str(e))

    items = result if isinstance(result, list) else result.get("recipes", [])
    created = []
    for item in items[: data.count]:
        if not isinstance(item, dict) or not item.get("name"):
            continue
        name = str(item["name"]).strip()
        if db.query(Recipe).filter(Recipe.name == name).first():
            continue
        recipe = Recipe(
            name=name,
            category=str(item.get("category") or "家常菜"),
            cuisine=str(item.get("cuisine") or "家常"),
            description=str(item.get("description") or ""),
            servings=1,
            calories=_num(item.get("calories")),
            protein=_num(item.get("protein")),
            fat=_num(item.get("fat")),
            carbs=_num(item.get("carbs")),
            is_ai_generated=True,
        )
        recipe.ingredients = [
            {"name": str(x.get("name", "")), "amount": str(x.get("amount", ""))}
            for x in item.get("ingredients", []) if isinstance(x, dict)
        ]
        recipe.steps = [str(s) for s in item.get("steps", []) if s]
        recipe.tags = [str(t) for t in item.get("tags", [])]
        db.add(recipe)
        created.append(recipe)
    db.commit()
    for r in created:
        db.refresh(r)
    if not created:
        raise HTTPException(502, "大模型未能生成有效的新食谱（可能菜名与已有食谱重复）")
    return [recipe_to_dict(r) for r in created]


def _num(v) -> float:
    try:
        n = float(v)
        return 0 if math.isnan(n) else n
    except (TypeError, ValueError):
        return 0
