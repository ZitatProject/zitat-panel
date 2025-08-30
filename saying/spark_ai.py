import json
import os
from typing import Dict, Any, Optional

import openai
"""
这本来是给讯飞的大模型用的，但是讯飞的太纸张了
FK U 讯飞星火
awa
"""

# -------------------------------------------------
# 1. 读取配置
# -------------------------------------------------
def _load_config() -> Dict[str, Any]:
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)

_cfg = _load_config()
API_KEY = _cfg.get("ai_key")
BASE_URL = _cfg.get("base_url")
SYSTEM_PROMPT: Optional[str] = _cfg.get("prompt") or None   # 允许为空

if not API_KEY:
    raise RuntimeError("请在 config.json 中填写 gpt_api_key")

# -------------------------------------------------
# 2. 初始化 openai 客户端
# -------------------------------------------------
openai.api_key = API_KEY
openai.base_url = BASE_URL

# -------------------------------------------------
# 3. 对外暴露的函数
# -------------------------------------------------
def call_spark(user_content: str,
               max_tokens: int = 512,
               temperature: float = 0.5) -> str:
    """
    调用 OpenAI 兼容接口，返回模型回复文本。
    如 config.json 中提供了 prompt 字段，则作为系统提示词传入。
    """
    messages = []
    if SYSTEM_PROMPT:
        messages.append({"role": "system", "content": SYSTEM_PROMPT})
    messages.append({"role": "user", "content": user_content})

    try:
        resp = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"[call_spark Error] {e}"

# -------------------------------------------------
# 4. 简单自测
# -------------------------------------------------
if __name__ == "__main__":
    print(call_spark("用一句话介绍你自己"))