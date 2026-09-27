"""通用序列化工具"""
from .database import Recipe


def recipe_to_dict(r: Recipe) -> dict:
    return {
        "id": r.id,
        "name": r.name,
        "category": r.category,
        "cuisine": r.cuisine,
        "description": r.description,
        "ingredients": r.ingredients,
        "steps": r.steps,
        "servings": r.servings,
        "calories": r.calories,
        "protein": r.protein,
        "fat": r.fat,
        "carbs": r.carbs,
        "tags": r.tags,
        "is_ai_generated": r.is_ai_generated,
        "created_at": r.created_at.isoformat() if r.created_at else "",
        "updated_at": r.updated_at.isoformat() if r.updated_at else "",
    }
