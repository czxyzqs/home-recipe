"""应用配置（LLM 等），持久化在 settings 表"""
from .database import SessionLocal, Setting

LLM_SETTING_KEY = "llm"

DEFAULT_LLM_SETTING = {
    "base_url": "",  # 如 https://open.bigmodel.cn/api/paas/v4
    "api_key": "",
    "model": "",  # 如 glm-4-flash / deepseek-chat / gpt-4o-mini
    "temperature": 0.7,
}


def get_llm_setting() -> dict:
    with SessionLocal() as db:
        row = db.get(Setting, LLM_SETTING_KEY)
        if not row:
            return dict(DEFAULT_LLM_SETTING)
        merged = dict(DEFAULT_LLM_SETTING)
        merged.update(row.value)
        return merged


def save_llm_setting(data: dict) -> dict:
    merged = get_llm_setting()
    for key in ("base_url", "api_key", "model"):
        if key in data and data[key] is not None:
            merged[key] = str(data[key]).strip()
    if "temperature" in data and data["temperature"] is not None:
        try:
            merged["temperature"] = max(0.0, min(2.0, float(data["temperature"])))
        except (TypeError, ValueError):
            pass
    with SessionLocal() as db:
        row = db.get(Setting, LLM_SETTING_KEY)
        if not row:
            row = Setting(key=LLM_SETTING_KEY)
            db.add(row)
        row.value = merged
        db.commit()
    return merged


def llm_configured() -> bool:
    s = get_llm_setting()
    return bool(s.get("base_url") and s.get("api_key") and s.get("model"))


def mask_key(key: str) -> str:
    if not key or len(key) <= 8:
        return "*" * len(key) if key else ""
    return key[:4] + "*" * 6 + key[-4:]
