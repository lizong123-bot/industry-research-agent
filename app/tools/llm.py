# app/tools/llm.py
import json
import logging
import random
import re
import time

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ValidationError
from openai import (
    RateLimitError, APITimeoutError, APIConnectionError, InternalServerError,
)

from app.config import LLM_API_KEY, LLM_MODEL_ID, LLM_BASE_URL, LLM_MAX_RETRIES

logger = logging.getLogger(__name__)


class LLMCallError(Exception):
    """LLM 调用失败（重试耗尽 / 永久错误）。调用方必须显式处理。"""


_llm = ChatOpenAI(
    model=LLM_MODEL_ID,
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL,
    temperature=0,
)

_RETRYABLE = (
    RateLimitError, APITimeoutError, APIConnectionError, InternalServerError,
)


def _call_with_retry(fn, *args, **kwargs):
    last_exc = None
    for attempt in range(LLM_MAX_RETRIES):
        try:
            return fn(*args, **kwargs)
        except _RETRYABLE as e:
            last_exc = e
            if attempt == LLM_MAX_RETRIES - 1:
                break
            delay = min(2 ** attempt + random.uniform(0, 1), 30)
            logger.warning(
                "LLM call failed (%s), retry %d/%d in %.2fs",
                type(e).__name__, attempt + 1, LLM_MAX_RETRIES, delay,
            )
            time.sleep(delay)
        except Exception as e:
            # 永久错误（4xx 等）→ 不重试，包成 LLMCallError
            raise LLMCallError(
                f"LLM call failed (permanent): {type(e).__name__}: {e}"
            ) from e
    raise LLMCallError(
        f"LLM call failed after {LLM_MAX_RETRIES} attempts: "
        f"{type(last_exc).__name__}: {last_exc}"
    ) from last_exc


def call_llm_text(prompt: str) -> str:
    """自由文本输出。Writer 用。失败 → raise LLMCallError。"""
    return _call_with_retry(_llm.invoke, prompt).content


def call_llm_json(prompt: str, output_schema: type[BaseModel]) -> BaseModel:
    """结构化输出。手动 JSON 解析 + Pydantic 校验（兼容任意 OpenAI 兼容端点）。"""
    schema_json = json.dumps(
        output_schema.model_json_schema(), ensure_ascii=False, indent=2
    )
    full_prompt = (
        f"{prompt}\n\n"
        f"请严格输出符合以下 JSON Schema 的 JSON，不要任何其他文字：\n{schema_json}"
    )

    last_exc = None
    for attempt in range(LLM_MAX_RETRIES):
        try:
            raw = _call_with_retry(_llm.invoke, full_prompt).content
        except LLMCallError:
            raise

        data = _extract_json(raw)
        if data is None:
            last_exc = ValueError(f"无法从 LLM 输出解析 JSON: {raw[:200]}")
            if attempt == LLM_MAX_RETRIES - 1:
                break
            continue

        try:
            return output_schema.model_validate(data)
        except ValidationError as e:
            last_exc = e
            if attempt == LLM_MAX_RETRIES - 1:
                break
            full_prompt = (
                f"{prompt}\n\n"
                f"你上次输出的 JSON 不符合 schema，错误：{e}\n"
                f"请重新输出符合以下 schema 的 JSON：\n{schema_json}"
            )

    raise LLMCallError(f"结构化输出失败: {last_exc}")


def _extract_json(text: str) -> dict | None:
    """从 LLM 输出里抠出 JSON。兼容纯 JSON 和 markdown 代码块。"""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None