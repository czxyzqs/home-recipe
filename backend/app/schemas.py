"""API 请求/响应模型"""
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

MealType = Literal["meal", "breakfast", "lunch", "dinner", "snack"]
PlanMealType = Literal["meal", "breakfast", "lunch", "dinner", "snack"]

MEAL_TYPE_NAMES = {"meal": "用餐", "breakfast": "早餐", "lunch": "午餐", "dinner": "晚餐", "snack": "加餐"}


class Ingredient(BaseModel):
    name: str
    amount: str = ""


class RecipeIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: str = "家常菜"
    cuisine: str = "家常"
    description: str = ""
    ingredients: list[Ingredient] = []
    steps: list[str] = []
    servings: float = 1
    calories: float = 0
    protein: float = 0
    fat: float = 0
    carbs: float = 0
    tags: list[str] = []
    is_ai_generated: bool = False


class RecipeOut(RecipeIn):
    id: int
    created_at: str = ""
    updated_at: str = ""

    model_config = {"from_attributes": True}


class RecipeAIGenerateIn(BaseModel):
    prompt: str = Field(min_length=1, max_length=500, description="食材/菜名/想法")
    count: int = Field(default=1, ge=1, le=3)


class MealLogIn(BaseModel):
    date: date
    meal_type: MealType = "meal"
    recipe_id: int | None = None
    custom_name: str = ""
    servings: float = Field(default=1, ge=0.1, le=20)
    note: str = ""


class MealLogOut(BaseModel):
    id: int
    date: date
    meal_type: str
    recipe_id: int | None
    custom_name: str
    servings: float
    note: str
    recipe: RecipeOut | None = None

    model_config = {"from_attributes": True}


class NutritionSummary(BaseModel):
    calories: float = 0
    protein: float = 0
    fat: float = 0
    carbs: float = 0


class DailyNutrition(BaseModel):
    date: date
    meals: int = 0
    calories: float = 0
    protein: float = 0
    fat: float = 0
    carbs: float = 0


class AIAnalyzeIn(BaseModel):
    start_date: date
    days: int = Field(default=7, ge=1, le=31)


class PlanGenerateIn(BaseModel):
    start_date: date | None = None  # 默认今天（工作日）或下一个工作日
    force: bool = False  # 同周期已有计划时是否直接覆盖（False 时返回 409 由前端确认）


class PlanCreateIn(BaseModel):
    start_date: date


class PlanItemIn(BaseModel):
    date: date
    meal_type: PlanMealType
    recipe_id: int


class LLMSettingIn(BaseModel):
    base_url: str | None = None
    api_key: str | None = None
    model: str | None = None
    temperature: float | None = None


class PlanApplyDayIn(BaseModel):
    date: date
