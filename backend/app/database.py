"""数据库模型与会话管理（SQLite）"""
import json
import os
from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data"))
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "recipe.db")

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class JSONText:
    """简单的 JSON 字段 mixin（SQLite 无原生 JSON 类型时的便捷读写）"""

    @staticmethod
    def dump(value) -> str:
        return json.dumps(value, ensure_ascii=False)

    @staticmethod
    def load(text_value: str | None, default=None):
        if not text_value:
            return default if default is not None else []
        try:
            return json.loads(text_value)
        except (TypeError, ValueError):
            return default if default is not None else []


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(50), default="家常菜")  # 家常菜/荤菜/素菜/汤羹/甜点
    cuisine: Mapped[str] = mapped_column(String(50), default="家常")
    description: Mapped[str] = mapped_column(Text, default="")
    ingredients_text: Mapped[str] = mapped_column(Text, default="")  # JSON: [{name, amount}]
    steps_text: Mapped[str] = mapped_column(Text, default="")  # JSON: [str]
    servings: Mapped[float] = mapped_column(Float, default=1)  # 营养数据对应的份数（人份）
    calories: Mapped[float] = mapped_column(Float, default=0)  # 千卡/份
    protein: Mapped[float] = mapped_column(Float, default=0)  # 克/份
    fat: Mapped[float] = mapped_column(Float, default=0)
    carbs: Mapped[float] = mapped_column(Float, default=0)
    tags_text: Mapped[str] = mapped_column(Text, default="")  # JSON: [str]
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    # JSON 便捷属性 -------------------------------------------------
    @property
    def ingredients(self) -> list:
        return JSONText.load(self.ingredients_text)

    @ingredients.setter
    def ingredients(self, value):
        self.ingredients_text = JSONText.dump(value or [])

    @property
    def steps(self) -> list:
        return JSONText.load(self.steps_text)

    @steps.setter
    def steps(self, value):
        self.steps_text = JSONText.dump(value or [])

    @property
    def tags(self) -> list:
        return JSONText.load(self.tags_text)

    @tags.setter
    def tags(self, value):
        self.tags_text = JSONText.dump(value or [])


class MealLog(Base):
    """每日用餐记录（不区分餐段）"""
    __tablename__ = "meal_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    meal_type: Mapped[str] = mapped_column(String(20))  # 固定为 meal
    recipe_id: Mapped[int | None] = mapped_column(ForeignKey("recipes.id"), nullable=True)
    custom_name: Mapped[str] = mapped_column(String(200), default="")  # 临时记录的不在库里的菜
    servings: Mapped[float] = mapped_column(Float, default=1)
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    recipe: Mapped[Recipe | None] = relationship("Recipe")


class WeeklyPlan(Base):
    __tablename__ = "weekly_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    start_date: Mapped[date] = mapped_column(Date, index=True)
    end_date: Mapped[date] = mapped_column(Date)
    mode: Mapped[str] = mapped_column(String(10), default="manual")  # ai=AI生成(仅工作日) / manual=手工
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    items: Mapped[list["WeeklyPlanItem"]] = relationship(
        "WeeklyPlanItem", cascade="all, delete-orphan", order_by="WeeklyPlanItem.date"
    )


class WeeklyPlanItem(Base):
    __tablename__ = "weekly_plan_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("weekly_plans.id"), index=True)
    date: Mapped[date] = mapped_column(Date)
    meal_type: Mapped[str] = mapped_column(String(20))
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"))

    recipe: Mapped[Recipe] = relationship("Recipe")


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(50), primary_key=True)
    value_text: Mapped[str] = mapped_column(Text, default="{}")

    @property
    def value(self) -> dict:
        try:
            return json.loads(self.value_text or "{}")
        except (TypeError, ValueError):
            return {}

    @value.setter
    def value(self, v: dict):
        self.value_text = json.dumps(v, ensure_ascii=False)


def init_db() -> None:
    Base.metadata.create_all(engine)
    # 旧库迁移：weekly_plans 缺 mode 列则补上
    from sqlalchemy import text
    with engine.connect() as conn:
        cols = [row[1] for row in conn.execute(text("PRAGMA table_info(weekly_plans)"))]
        if "mode" not in cols:
            conn.execute(text("ALTER TABLE weekly_plans ADD COLUMN mode VARCHAR(10) DEFAULT 'manual'"))
            conn.commit()
