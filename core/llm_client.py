import time
import logging
from openai import OpenAI
import config

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self):
        self._client = None
        self._model = None
        self._total_calls = 0
        self._total_tokens = 0

    def _ensure_client(self):
        """延迟初始化 OpenAI 客户端，首次调用时才创建"""
        if self._client is None:
            if not config.LLM_API_KEY:
                raise ValueError("LLM_API_KEY 未设置，请检查 .env 文件")
            self._client = OpenAI(
                api_key=config.LLM_API_KEY,
                base_url=config.LLM_BASE_URL
            )
            self._model = config.LLM_MODEL

    def chat(self, prompt: str, system_prompt: str = None, max_retries: int = 3) -> str:
        """发送聊天请求，返回响应文本。内置指数退避重试。"""
        self._ensure_client()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        last_error = None
        for attempt in range(max_retries):
            try:
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    temperature=0.3
                )
                self._total_calls += 1
                if response.usage:
                    self._total_tokens += response.usage.total_tokens
                return response.choices[0].message.content
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    logger.warning(f"LLM API 调用失败 (第 {attempt + 1}/{max_retries} 次): {e}，{wait}秒后重试...")
                    time.sleep(wait)

        raise RuntimeError(f"LLM API 调用失败，已重试 {max_retries} 次: {last_error}")

    @property
    def usage_stats(self) -> dict:
        """获取 API 调用统计"""
        return {
            "total_calls": self._total_calls,
            "total_tokens": self._total_tokens
        }


# 全局客户端实例（延迟初始化，import 时不会创建 OpenAI 连接）
llm_client = LLMClient()
