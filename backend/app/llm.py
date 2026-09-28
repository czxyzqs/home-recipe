"""大模型客户端：OpenAI 兼容 Chat Completions 协议"""
import json
import re

import httpx

from .config import get_llm_setting


class LLMError(Exception):
    pass


async def chat(messages: list[dict], temperature: float | None = None) -> str:
    """调用配置好的大模型，返回文本内容"""
    cfg = get_llm_setting()
    if not (cfg.get("base_url") and cfg.get("api_key") and cfg.get("model")):
        raise LLMError("大模型未配置，请先在「设置」页填写 Base URL / API Key / 模型名")

    url = cfg["base_url"].rstrip("/") + "/chat/completions"
    payload = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": cfg.get("temperature", 0.7) if temperature is None else temperature,
    }
    headers = {
        "Authorization": f"Bearer {cfg['api_key']}",
        "Content-Type": "application/json",
    }
    # 生成周计划等长输出场景耗时较长，读取超时放宽到 180 秒
    timeout = httpx.Timeout(connect=15, read=180, write=15, pool=15)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
    except httpx.HTTPError as e:
        raise LLMError(f"请求大模型失败：{e}") from e

    if resp.status_code != 200:
        raise LLMError(f"大模型返回错误 {resp.status_code}：{resp.text[:500]}")
    try:
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, ValueError) as e:
        raise LLMError(f"解析大模型响应失败：{e}") from e


async def chat_json(messages: list[dict], temperature: float = 0.4) -> dict | list:
    """要求模型输出 JSON 并做容错解析"""
    text = await chat(messages, temperature=temperature)
    return extract_json(text)


def extract_json(text: str) -> dict | list:
    """从模型输出中提取 JSON（容忍 ```json 代码块、前后缀文本）"""
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(.+?)\s*```", text, re.DOTALL)
    if m:
        text = m.group(1).strip()
    # 去掉 <think>...</think> 推理段（部分推理模型会输出）
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    try:
        return json.loads(text)
    except ValueError:
        pass
    # 取第一个 { 到最后一个 }（或 [ ... ]）
    for left, right in (("{", "}"), ("[", "]")):
        start, end = text.find(left), text.rfind(right)
        if start != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except ValueError:
                continue
    raise LLMError("无法从大模型输出中解析 JSON，请重试或更换模型")
