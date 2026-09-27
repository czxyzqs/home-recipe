"""家庭食谱系统 - FastAPI 入口"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import init_db
from .routers import meals, nutrition, plans, recipes, settings
from .seed import seed_if_empty

app = FastAPI(title="家庭食谱系统", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recipes.router)
app.include_router(meals.router)
app.include_router(nutrition.router)
app.include_router(plans.router)
app.include_router(settings.router)


@app.get("/api/health")
def health():
    return {"ok": True, "app": "home-recipe"}


@app.on_event("startup")
def startup():
    init_db()
    seed_if_empty()


# ---- 前端静态资源（Docker/生产模式由后端直接托管 SPA）----
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        # 静态文件存在则返回文件，否则回退 index.html（前端路由）
        candidate = os.path.join(STATIC_DIR, full_path)
        if full_path and os.path.isfile(candidate) and ".." not in full_path:
            return FileResponse(candidate)
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
