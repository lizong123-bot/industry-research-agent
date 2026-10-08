# app/config.py
import os
from dotenv import load_dotenv

# 开发场景本地 .env 优先，改了立即生效
load_dotenv(override=True)

# ---------- LLM ----------
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL_ID = os.getenv("LLM_MODEL_ID")
LLM_BASE_URL = os.getenv("LLM_BASE_URL")

# ---------- 搜索 ----------
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
SEARCH_MAX_RETRIES = int(os.getenv("SEARCH_MAX_RETRIES", "3"))
SCRAPE_TIMEOUT = int(os.getenv("SCRAPE_TIMEOUT", "10"))

# ---------- 流程上限 ----------
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "35"))
MAX_TOOL_CALLS = int(os.getenv("MAX_TOOL_CALLS", "20"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))

# ---------- 启动校验（fail fast + 直接引用 + 分步报错） ----------
if not LLM_API_KEY:
    raise ValueError("缺少环境变量: LLM_API_KEY")
if not LLM_MODEL_ID:
    raise ValueError("缺少环境变量: LLM_MODEL_ID")
if not LLM_BASE_URL:
    raise ValueError("缺少环境变量: LLM_BASE_URL")
if not SERPAPI_KEY:
    raise ValueError("缺少环境变量: SERPAPI_KEY")