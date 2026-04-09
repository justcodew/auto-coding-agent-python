"""测试 core/llm_client.py"""
import pytest
from unittest.mock import patch, MagicMock
from core.llm_client import LLMClient
import config


class TestLLMClientInit:
    """测试 LLM 客户端初始化"""

    def test_lazy_init_no_key(self):
        """没有 API Key 时延迟初始化应抛出 ValueError"""
        client = LLMClient()
        with patch.object(config, "LLM_API_KEY", ""):
            with pytest.raises(ValueError, match="LLM_API_KEY 未设置"):
                client.chat("test")

    def test_lazy_init_with_key(self, monkeypatch):
        """有 API Key 时正常初始化"""
        monkeypatch.setattr(config, "LLM_API_KEY", "test-key")
        client = LLMClient()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "test response"
        mock_response.usage.total_tokens = 50

        with patch("core.llm_client.OpenAI") as MockOpenAI:
            mock_instance = MagicMock()
            mock_instance.chat.completions.create.return_value = mock_response
            MockOpenAI.return_value = mock_instance

            result = client.chat("hello")
            assert result == "test response"
            assert client.usage_stats["total_calls"] == 1
            assert client.usage_stats["total_tokens"] == 50


class TestLLMClientChat:
    """测试聊天请求"""

    def test_chat_with_system_prompt(self, monkeypatch):
        """带 system prompt 的请求"""
        monkeypatch.setattr(config, "LLM_API_KEY", "test-key")
        client = LLMClient()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "response"
        mock_response.usage = None

        with patch("core.llm_client.OpenAI") as MockOpenAI:
            mock_instance = MagicMock()
            mock_instance.chat.completions.create.return_value = mock_response
            MockOpenAI.return_value = mock_instance

            client.chat("user msg", system_prompt="sys msg")

            # 验证 messages 参数
            call_args = mock_instance.chat.completions.create.call_args
            messages = call_args.kwargs.get("messages", call_args[1].get("messages"))
            assert len(messages) == 2
            assert messages[0]["role"] == "system"
            assert messages[1]["role"] == "user"

    def test_chat_without_system_prompt(self, monkeypatch):
        """不带 system prompt 的请求"""
        monkeypatch.setattr(config, "LLM_API_KEY", "test-key")
        client = LLMClient()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "response"
        mock_response.usage = None

        with patch("core.llm_client.OpenAI") as MockOpenAI:
            mock_instance = MagicMock()
            mock_instance.chat.completions.create.return_value = mock_response
            MockOpenAI.return_value = mock_instance

            client.chat("user msg")

            call_args = mock_instance.chat.completions.create.call_args
            messages = call_args.kwargs.get("messages", call_args[1].get("messages"))
            assert len(messages) == 1
            assert messages[0]["role"] == "user"


class TestLLMClientRetry:
    """测试重试逻辑"""

    def test_retry_on_failure(self, monkeypatch):
        """API 失败时重试"""
        monkeypatch.setattr(config, "LLM_API_KEY", "test-key")
        client = LLMClient()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "success"
        mock_response.usage = None

        with patch("core.llm_client.OpenAI") as MockOpenAI:
            mock_instance = MagicMock()
            # 前2次失败，第3次成功
            mock_instance.chat.completions.create.side_effect = [
                Exception("timeout"),
                Exception("timeout"),
                mock_response
            ]
            MockOpenAI.return_value = mock_instance

            result = client.chat("test", max_retries=3)
            assert result == "success"
            assert client.usage_stats["total_calls"] == 1

    def test_all_retries_fail(self, monkeypatch):
        """所有重试都失败时抛出 RuntimeError"""
        monkeypatch.setattr(config, "LLM_API_KEY", "test-key")
        client = LLMClient()

        with patch("core.llm_client.OpenAI") as MockOpenAI:
            mock_instance = MagicMock()
            mock_instance.chat.completions.create.side_effect = Exception("down")
            MockOpenAI.return_value = mock_instance

            with pytest.raises(RuntimeError, match="LLM API 调用失败"):
                client.chat("test", max_retries=2)


class TestUsageStats:
    """测试使用统计"""

    def test_initial_stats(self):
        """初始统计为 0"""
        client = LLMClient()
        stats = client.usage_stats
        assert stats["total_calls"] == 0
        assert stats["total_tokens"] == 0
