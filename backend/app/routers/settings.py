"""LLM 设置"""
from fastapi import APIRouter, HTTPException

from ..config import get_llm_setting, llm_configured, mask_key, save_llm_setting
from ..llm import LLMError, chat
from ..schemas import LLMSettingIn

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/llm")
def read_llm_setting():
    s = get_llm_setting()
    return {
        "base_url": s.get("base_url", ""),
        "api_key_masked": mask_key(s.get("api_key", "")),
        "api_key_set": bool(s.get("api_key")),
        "model": s.get("model", ""),
        "temperature": s.get("temperature", 0.7),
        "configured": llm_configured(),
    }


@router.put("/llm")
def update_llm_setting(data: LLMSettingIn):
    payload = {k: v for k, v in data.model_dump().items() if v is not None}
    # api_key 传空或掩码字符串时保留原值
    if "api_key" in payload and (not payload["api_key"].strip() or "*" in payload["api_key"]):
        payload.pop("api_key")
    save_llm_setting(payload)
    return read_llm_setting()


@router.post("/llm/test")
async def test_llm_setting(data: LLMSettingIn):
    """先保存再测试，返回模型回复"""
    payload = {k: v for k, v in data.model_dump().items() if v is not None}
    if "api_key" in payload and (not payload["api_key"].strip() or "*" in payload["api_key"]):
        payload.pop("api_key")
    save_llm_setting(payload)
    try:
        reply = await chat(
            [{"role": "user", "content": "请只回复两个字：你好"}],
            temperature=0.1,
        )
    except LLMError as e:
        raise HTTPException(502, f"连接失败：{e}")
    return {"ok": True, "reply": reply.strip()[:200]}
